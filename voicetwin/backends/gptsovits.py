"""GPT-SoVITS 引擎（推荐）：用你的素材微调，复刻程度最高。

训练流程与官方 WebUI 完全一致（1A 文本 → 1B 特征/声纹 → 1C 语义 → SoVITS 训练 → GPT 训练），
只是全部自动完成；推理通过官方 api_v2.py 服务进行。
训练出来的模型和官方 WebUI 通用，也可以在 GPT-SoVITS 的界面里直接选择使用。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from voicetwin.backends.base import Backend, ProgressFn, SynthRequest, gpu_memory_gb, resolve_python
from voicetwin.backends.worker import subprocess_env
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import short_hash

log = get_logger("gptsovits")

PRETRAINED_SOVITS = {
    "v2": "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth",
    "v2Pro": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2Pro.pth",
    "v2ProPlus": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth",
}
PRETRAINED_GPT = {
    "v2": "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
    "v2Pro": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
    "v2ProPlus": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
}
BERT_DIR = "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large"
HUBERT_DIR = "GPT_SoVITS/pretrained_models/chinese-hubert-base"
SV_PATH = "GPT_SoVITS/pretrained_models/sv/pretrained_eres2netv2w24s4ep4.ckpt"
SUPPORTED_VERSIONS = tuple(PRETRAINED_SOVITS)


def _free_port(preferred: int) -> int:
    for port in [preferred] + list(range(preferred + 1, preferred + 50)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred


def _exp_name(voice: str) -> str:
    ascii_part = re.sub(r"[^A-Za-z0-9_-]+", "", voice)[:20]
    return f"vt_{ascii_part + '_' if ascii_part else ''}{short_hash(voice, n=6)}"


class GPTSoVITSBackend(Backend):
    name = "gptsovits"
    display_name = "GPT-SoVITS"
    supports_training = True
    supports_speed = True
    supports_aux_refs = True

    def __init__(self, cfg, project):
        super().__init__(cfg, project)
        self.root = self.resolve("root", "./third_party/GPT-SoVITS")
        self.version = str(self.bcfg.get("version", "v2ProPlus"))
        if self.version not in SUPPORTED_VERSIONS:
            log.warning(f"暂只自动化支持 {SUPPORTED_VERSIONS}，当前配置 {self.version}，改用 v2ProPlus")
            self.version = "v2ProPlus"
        self.python = resolve_python(self.bcfg.get("python", "auto"), self.root, cfg)
        self.exp_name = _exp_name(project.voice)
        self.external_url = (self.bcfg.get("api_url") or "").rstrip("/")
        self.port = int(self.bcfg.get("port", 9880))
        self.api_url = self.external_url or f"http://127.0.0.1:{self.port}"
        self.proc: Optional[subprocess.Popen] = None
        self._loaded: Dict[str, str] = {}
        self._http = None

    # ================================================================ 路径与检查
    def p(self, rel: str) -> Path:
        assert self.root is not None
        return (self.root / rel).resolve()

    @property
    def is_half(self) -> bool:
        return bool(self.bcfg.get("is_half", True))

    def check(self) -> List[str]:
        problems = []
        if self.external_url:
            return problems
        if not self.root or not self.root.exists():
            return [f"找不到 GPT-SoVITS 目录：{self.root}（请运行安装脚本，或在 config.yaml 里设置 backends.gptsovits.root）"]
        if not (self.root / "api_v2.py").exists():
            problems.append(f"{self.root} 不是完整的 GPT-SoVITS 目录（缺少 api_v2.py）")
        needed = [BERT_DIR, HUBERT_DIR, PRETRAINED_SOVITS[self.version], PRETRAINED_GPT[self.version]]
        if "Pro" in self.version:
            needed.append(SV_PATH)
        for rel in needed:
            if not self.p(rel).exists():
                problems.append(f"缺少预训练模型：{rel}")
        return problems

    def env(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        assert self.root is not None
        root = str(self.root)
        paths = [root, os.path.join(root, "GPT_SoVITS"), os.path.join(root, "GPT_SoVITS", "BigVGAN"),
                 os.path.join(root, "tools"), os.path.join(root, "tools", "asr"), os.path.join(root, "tools", "uvr5")]
        existing = os.environ.get("PYTHONPATH", "")
        env = subprocess_env({
            "PYTHONPATH": os.pathsep.join(paths + ([existing] if existing else [])),
            "version": self.version,
            "is_half": str(self.is_half),
            "no_proxy": "localhost, 127.0.0.1, ::1",
            "KMP_DUPLICATE_LIB_OK": "TRUE",
        })
        env.pop("all_proxy", None)
        env.pop("ALL_PROXY", None)
        if extra:
            env.update({k: str(v) for k, v in extra.items()})
        return env

    # ================================================================ 训练
    def _gpu(self) -> str:
        return str(self.bcfg.get("train", {}).get("gpu", "0"))

    def _prepare_features(self, list_path: Path, wav_dir: Path, progress: Optional[ProgressFn]) -> Path:
        opt_dir = self.p(f"logs/{self.exp_name}")
        opt_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(list_path.read_bytes() + self.version.encode()).hexdigest()
        stamp = opt_dir / "voicetwin_list.sha1"
        if stamp.exists() and stamp.read_text().strip() != digest:
            log.info("训练素材有变化，清理旧的特征文件后重新提取")
            for name in ("2-name2text.txt", "6-name2semantic.tsv", "3-bert", "4-cnhubert", "5-wav32k", "7-sv_cn"):
                target = opt_dir / name
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                elif target.exists():
                    target.unlink()
        stamp.write_text(digest)
        base = {"inp_text": str(list_path), "inp_wav_dir": str(wav_dir), "exp_name": self.exp_name,
                "opt_dir": str(opt_dir), "i_part": "0", "all_parts": "1", "_CUDA_VISIBLE_DEVICES": self._gpu(),
                "is_half": str(self.is_half), "version": self.version}

        # 1A：文本 → 音素 + BERT 特征
        path_text = opt_dir / "2-name2text.txt"
        if not path_text.exists() or len(path_text.read_text(encoding="utf-8").strip().splitlines()) < 2:
            if progress:
                progress(0.05, "1A 文本处理（音素 + BERT 特征）")
            self.run_logged([self.python, "-s", "GPT_SoVITS/prepare_datasets/1-get-text.py"], self.root,
                            self.env({**base, "bert_pretrained_dir": str(self.p(BERT_DIR))}), "gsv_1a_text")
            part = opt_dir / "2-name2text-0.txt"
            lines = part.read_text(encoding="utf-8").strip("\n").split("\n") if part.exists() else []
            if not "".join(lines).strip():
                raise RuntimeError("1A 文本处理没有产出，请查看日志 logs/gsv_1a_text.log")
            path_text.write_text("\n".join(lines) + "\n", encoding="utf-8")
            part.unlink(missing_ok=True)

        # 1B：HuBERT 特征 + 32k 音频（+ v2Pro 声纹）
        if progress:
            progress(0.12, "1B 提取 HuBERT 特征" + ("与说话人声纹" if "Pro" in self.version else ""))
        env_1b = {**base, "cnhubert_base_dir": str(self.p(HUBERT_DIR)), "sv_path": str(self.p(SV_PATH))}
        self.run_logged([self.python, "-s", "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py"], self.root,
                        self.env(env_1b), "gsv_1b_hubert")
        if "Pro" in self.version:
            self.run_logged([self.python, "-s", "GPT_SoVITS/prepare_datasets/2-get-sv.py"], self.root,
                            self.env(env_1b), "gsv_1b_sv")

        # 1C：语义 token
        path_sem = opt_dir / "6-name2semantic.tsv"
        if not path_sem.exists() or path_sem.stat().st_size < 31:
            if progress:
                progress(0.2, "1C 提取语义 token")
            env_1c = {**base, "pretrained_s2G": str(self.p(PRETRAINED_SOVITS[self.version])),
                      "s2config_path": self._s2_config_template()}
            self.run_logged([self.python, "-s", "GPT_SoVITS/prepare_datasets/3-get-semantic.py"], self.root,
                            self.env(env_1c), "gsv_1c_semantic")
            part = opt_dir / "6-name2semantic-0.tsv"
            lines = ["item_name\tsemantic_audio"]
            if part.exists():
                lines += part.read_text(encoding="utf-8").strip("\n").split("\n")
                part.unlink()
            path_sem.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return opt_dir

    def _s2_config_template(self) -> str:
        return "GPT_SoVITS/configs/s2.json" if "Pro" not in self.version else f"GPT_SoVITS/configs/s2{self.version}.json"

    def _auto_params(self, n_clips: int, minutes: float) -> Dict[str, int]:
        tcfg = self.bcfg.get("train", {}) or {}
        mem = gpu_memory_gb(self.python, self.env())
        if mem <= 0:
            log.warning("没有检测到可用的 NVIDIA 显卡，训练会非常慢（CPU 训练可能需要数天）")
        bs = tcfg.get("batch_size", "auto")
        if bs in (None, "auto"):
            bs = int(mem // 2) if mem > 0 else 2
        bs = max(1, min(int(bs), max(1, n_clips // 4)))
        s_ep = tcfg.get("sovits_epochs", "auto")
        if s_ep in (None, "auto"):
            s_ep = 8 if minutes < 30 else 12
        g_ep = tcfg.get("gpt_epochs", "auto")
        if g_ep in (None, "auto"):
            g_ep = 15
        return {"batch_size": bs, "sovits_epochs": min(int(s_ep), 25), "gpt_epochs": int(g_ep), "gpu_mem_gb": round(mem, 1)}

    def train(self, progress: Optional[ProgressFn] = None, **opts: Any) -> Dict[str, Any]:
        from voicetwin.data.exporters import export_gptsovits

        problems = self.check()
        if self.external_url:
            problems.append("配置了外部 api_url 时无法自动训练，请清空 backends.gptsovits.api_url 并设置 root")
        if problems:
            raise RuntimeError("GPT-SoVITS 环境有问题：\n- " + "\n- ".join(problems))
        exp = export_gptsovits(self.project, speaker=self.exp_name)
        log.info(f"训练素材：{exp['count']} 条，{exp['minutes']} 分钟；实验名 {self.exp_name}；版本 {self.version}")
        params = self._auto_params(exp["count"], exp["minutes"])
        params.update({k: v for k, v in opts.items() if v not in (None, "auto")})
        tcfg = self.bcfg.get("train", {}) or {}
        log.info(f"训练参数：batch={params['batch_size']}，SoVITS {params['sovits_epochs']} 轮，GPT {params['gpt_epochs']} 轮"
                 f"（显存 {params['gpu_mem_gb']} GB）")
        opt_dir = self._prepare_features(Path(exp["list"]), Path(exp["wav_dir"]), progress)

        # ---------------- SoVITS
        bs = int(params["batch_size"])
        with open(self.p(self._s2_config_template()), "r", encoding="utf-8") as f:
            s2 = json.load(f)
        if not self.is_half:
            s2["train"]["fp16_run"] = False
            bs = max(1, bs // 2)
        pre_g = str(self.p(PRETRAINED_SOVITS[self.version]))
        s2["train"].update({
            "batch_size": bs, "epochs": int(params["sovits_epochs"]),
            "text_low_lr_rate": float(tcfg.get("text_low_lr_rate", 0.4)),
            "pretrained_s2G": pre_g, "pretrained_s2D": pre_g.replace("s2G", "s2D"),
            "if_save_latest": True, "if_save_every_weights": True,
            "save_every_epoch": int(tcfg.get("sovits_save_every", 4)), "gpu_numbers": self._gpu(),
            "grad_ckpt": False, "lora_rank": 32,
        })
        s2["model"]["version"] = self.version
        s2["data"]["exp_dir"] = s2["s2_ckpt_dir"] = str(opt_dir)
        s2["save_weight_dir"] = f"SoVITS_weights_{self.version}"
        s2["name"] = self.exp_name
        s2["version"] = self.version
        (opt_dir / f"logs_s2_{self.version}").mkdir(parents=True, exist_ok=True)
        s2_path = self.work_dir / "tmp_s2.json"
        s2_path.write_text(json.dumps(s2, ensure_ascii=False), encoding="utf-8")
        total_s = int(params["sovits_epochs"])
        self.run_logged([self.python, "-s", "GPT_SoVITS/s2_train.py", "--config", str(s2_path)], self.root, self.env(),
                        "gsv_s2_train", progress, (0.25, 0.6), _epoch_parser(total_s))

        # ---------------- GPT
        with open(self.p("GPT_SoVITS/configs/s1longer-v2.yaml"), "r", encoding="utf-8") as f:
            s1 = yaml.safe_load(f)
        bs1 = int(params["batch_size"])
        if not self.is_half:
            s1["train"]["precision"] = "32"
            bs1 = max(1, bs1 // 2)
        s1["train"].update({
            "batch_size": bs1, "epochs": int(params["gpt_epochs"]),
            "save_every_n_epoch": int(tcfg.get("gpt_save_every", 5)), "if_save_every_weights": True,
            "if_save_latest": True, "if_dpo": False, "half_weights_save_dir": f"GPT_weights_{self.version}",
            "exp_name": self.exp_name,
        })
        s1["pretrained_s1"] = str(self.p(PRETRAINED_GPT[self.version]))
        s1["train_semantic_path"] = str(opt_dir / "6-name2semantic.tsv")
        s1["train_phoneme_path"] = str(opt_dir / "2-name2text.txt")
        s1["output_dir"] = str(opt_dir / f"logs_s1_{self.version}")
        (opt_dir / "logs_s1").mkdir(parents=True, exist_ok=True)
        s1_path = self.work_dir / "tmp_s1.yaml"
        s1_path.write_text(yaml.dump(s1, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        self.run_logged([self.python, "-s", "GPT_SoVITS/s1_train.py", "--config_file", str(s1_path)], self.root,
                        self.env({"_CUDA_VISIBLE_DEVICES": self._gpu(), "hz": "25hz"}), "gsv_s1_train",
                        progress, (0.6, 0.95), _epoch_parser(int(params["gpt_epochs"])))

        sovits, gpt = self._list_weights()
        if not sovits or not gpt:
            raise RuntimeError("训练结束但没有找到权重文件，请查看 logs/gsv_s2_train.log 与 logs/gsv_s1_train.log")
        info = {
            "version": self.version, "exp_name": self.exp_name, "trained_at": time.strftime("%Y-%m-%d %H:%M"),
            "params": params, "sovits": [str(p) for p in sovits], "gpt": [str(p) for p in gpt],
            "selected": {"id": f"s{_epoch(sovits[-1])}-g{_epoch(gpt[-1])}", "sovits": str(sovits[-1]), "gpt": str(gpt[-1])},
        }
        self.project.update_models(self.name, info)
        if progress:
            progress(1.0, "GPT-SoVITS 训练完成")
        return info

    def _list_weights(self) -> "tuple[List[Path], List[Path]]":
        sov_dir = self.p(f"SoVITS_weights_{self.version}")
        gpt_dir = self.p(f"GPT_weights_{self.version}")
        sovits = sorted(sov_dir.glob(f"{self.exp_name}_e*_s*.pth"), key=_epoch) if sov_dir.exists() else []
        gpt = sorted(gpt_dir.glob(f"{self.exp_name}-e*.ckpt"), key=_epoch) if gpt_dir.exists() else []
        return sovits, gpt

    def checkpoints(self) -> List[Dict[str, Any]]:
        info = self.project.load_models().get(self.name) or {}
        sovits = [Path(p) for p in info.get("sovits", []) if Path(p).exists()]
        gpt = [Path(p) for p in info.get("gpt", []) if Path(p).exists()]
        if not sovits or not gpt:
            sovits, gpt = self._list_weights()
        out = []
        for s in sovits[-3:]:
            for g in gpt[-3:]:
                out.append({"id": f"s{_epoch(s)}-g{_epoch(g)}", "sovits": str(s), "gpt": str(g)})
        return out

    # ================================================================ 推理服务
    def _current_weights(self) -> Dict[str, str]:
        sel = self.selected_checkpoint()
        if sel and Path(sel.get("sovits", "")).exists() and Path(sel.get("gpt", "")).exists():
            return {"sovits": sel["sovits"], "gpt": sel["gpt"], "id": sel.get("id", "custom")}
        if self.root is None:
            return {"sovits": "", "gpt": "", "id": "external"}
        log.warning("还没有训练好的 GPT-SoVITS 模型，暂时使用官方底模做零样本克隆（像度会明显低于训练后）")
        return {"sovits": str(self.p(PRETRAINED_SOVITS[self.version])), "gpt": str(self.p(PRETRAINED_GPT[self.version])),
                "id": "pretrained"}

    def model_id(self) -> str:
        w = self._current_weights()
        return f"gsv-{self.version}-{w['id']}-{short_hash(w['sovits'], w['gpt'], n=6)}"

    def _session(self):
        if self._http is None:
            import requests

            self._http = requests.Session()
            self._http.trust_env = False  # 访问本机服务不走代理
        return self._http

    def _alive(self) -> bool:
        """api_v2 对不带参数的 /tts 请求会返回 400 + {"message": ...}，以此判断服务已就绪。"""
        try:
            r = self._session().get(f"{self.api_url}/tts", timeout=3)
            return r.status_code == 400 and "message" in r.json()
        except Exception:
            return False

    def start(self) -> None:
        if self._alive():
            self._ensure_weights()
            return
        if self.external_url:
            raise RuntimeError(f"连接不上 GPT-SoVITS 服务 {self.external_url}，请先启动 api_v2.py")
        problems = self.check()
        if problems:
            raise RuntimeError("GPT-SoVITS 环境有问题：\n- " + "\n- ".join(problems))
        self.port = _free_port(self.port)
        self.api_url = f"http://127.0.0.1:{self.port}"
        weights = self._current_weights()
        cfg_path = self.work_dir / "tts_infer.yaml"
        cfg_path.write_text(yaml.dump({"custom": {
            "bert_base_path": str(self.p(BERT_DIR)), "cnhuhbert_base_path": str(self.p(HUBERT_DIR)),
            "device": str(self.bcfg.get("device", "cuda")), "is_half": self.is_half, "version": self.version,
            "t2s_weights_path": weights["gpt"], "vits_weights_path": weights["sovits"],
        }}, allow_unicode=True), encoding="utf-8")
        log_path = self.project.logs_dir / "gptsovits_api.log"
        log.info(f"启动 GPT-SoVITS 推理服务（端口 {self.port}，模型 {weights['id']}）……")
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._log_fh = open(log_path, "a", encoding="utf-8")
        self.proc = subprocess.Popen(
            [self.python, "api_v2.py", "-a", "127.0.0.1", "-p", str(self.port), "-c", str(cfg_path)],
            cwd=str(self.root), env=self.env(), stdout=self._log_fh, stderr=subprocess.STDOUT, creationflags=creationflags,
        )
        deadline = time.time() + float(self.bcfg.get("startup_timeout", 600))
        while time.time() < deadline:
            if self.proc.poll() is not None:
                self._log_fh.flush()
                tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]
                raise RuntimeError("GPT-SoVITS 推理服务启动失败：\n" + "\n".join(tail))
            if self._alive():
                self._loaded = {"sovits": weights["sovits"], "gpt": weights["gpt"]}
                log.info("GPT-SoVITS 推理服务已就绪")
                return
            time.sleep(2)
        self.stop()
        raise RuntimeError(f"GPT-SoVITS 推理服务启动超时，请查看 {log_path}")

    def stop(self) -> None:
        if self.proc is not None:
            try:
                self._session().get(f"{self.api_url}/control", params={"command": "exit"}, timeout=3)
            except Exception:
                pass
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
            self.proc = None
            try:
                self._log_fh.close()
            except Exception:
                pass
        self._loaded = {}

    def _set_weights(self, gpt: str, sovits: str) -> None:
        s = self._session()
        if gpt and self._loaded.get("gpt") != gpt:
            r = s.get(f"{self.api_url}/set_gpt_weights", params={"weights_path": gpt}, timeout=600)
            if r.status_code != 200:
                raise RuntimeError(f"切换 GPT 模型失败：{r.text}")
            self._loaded["gpt"] = gpt
        if sovits and self._loaded.get("sovits") != sovits:
            r = s.get(f"{self.api_url}/set_sovits_weights", params={"weights_path": sovits}, timeout=600)
            if r.status_code != 200:
                raise RuntimeError(f"切换 SoVITS 模型失败：{r.text}")
            self._loaded["sovits"] = sovits

    def _ensure_weights(self) -> None:
        w = self._current_weights()
        if w["sovits"] and w["gpt"]:
            self._set_weights(w["gpt"], w["sovits"])

    def use_checkpoint(self, ckpt: Dict[str, Any]) -> None:
        if not self._alive():
            self.start()
        self._set_weights(ckpt["gpt"], ckpt["sovits"])

    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        if not self._alive():
            self.start()
        icfg = self.bcfg.get("infer", {}) or {}
        payload = {
            "text": req.text,
            "text_lang": "en" if req.lang == "en" else "zh",
            "ref_audio_path": str(Path(req.ref_audio).resolve()),
            "aux_ref_audio_paths": [str(Path(p).resolve()) for p in req.aux_refs],
            "prompt_text": req.ref_text,
            "prompt_lang": "en" if req.ref_lang == "en" else "zh",
            "top_k": int(req.top_k if req.top_k is not None else icfg.get("top_k", 15)),
            "top_p": float(req.top_p if req.top_p is not None else icfg.get("top_p", 1.0)),
            "temperature": float(req.temperature if req.temperature is not None else icfg.get("temperature", 1.0)),
            "text_split_method": "cut0",   # 已按句切好，不再二次切分，保留模型自己的句内停顿
            "batch_size": 1,
            "speed_factor": float(req.speed or 1.0),
            "fragment_interval": 0.3,
            "seed": int(req.seed),
            "media_type": "wav",
            "streaming_mode": False,
            "parallel_infer": True,
            "repetition_penalty": float(icfg.get("repetition_penalty", 1.35)),
            "sample_steps": int(icfg.get("sample_steps", 32)),
            "super_sampling": False,
        }
        r = self._session().post(f"{self.api_url}/tts", json=payload, timeout=600)
        if r.status_code != 200:
            try:
                msg = r.json().get("message") or r.text
            except Exception:
                msg = r.text
            raise RuntimeError(f"GPT-SoVITS 合成失败：{msg}")
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        return out_path


def _epoch(path: Path) -> int:
    m = re.search(r"_e(\d+)_s\d+\.pth$", str(path)) or re.search(r"-e(\d+)\.ckpt$", str(path))
    return int(m.group(1)) if m else 0


def _epoch_parser(total: int):
    pats = [re.compile(r"[Ee]poch[:=\s]*(\d+)"), re.compile(r"epoch=(\d+)")]

    def parse(line: str) -> Optional[float]:
        for pat in pats:
            m = pat.search(line)
            if m:
                return min(1.0, int(m.group(1)) / max(total, 1))
        return None

    return parse
