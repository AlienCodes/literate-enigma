"""Qwen3-TTS 引擎（阿里通义 2026 年开源，Apache-2.0）。

- 零样本：Base 模型 + 你的参考音频，3 秒就能克隆，不用训练；
- 微调：用你的全部素材做单说话人微调（官方 finetuning 脚本），像度更高。
  注意全量微调显存占用大：0.6B 约需 12GB+，1.7B 建议 32GB+。
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from voicetwin.backends.base import ProgressFn, SynthRequest, resolve_python
from voicetwin.backends.worker import subprocess_env
from voicetwin.backends.worker_backend import WORKERS_DIR, WorkerBackend
from voicetwin.utils.ffmpeg import atempo
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import short_hash

log = get_logger("qwen3tts")
LANG_NAMES = {"zh": "Chinese", "en": "English"}


def _speaker_name(voice: str) -> str:
    ascii_part = re.sub(r"[^a-z0-9_]+", "", voice.lower())[:16]
    return f"vt_{ascii_part + '_' if ascii_part else ''}{short_hash(voice, n=6)}"


class Qwen3TTSBackend(WorkerBackend):
    name = "qwen3tts"
    display_name = "Qwen3-TTS"
    supports_training = True
    supports_speed = False

    def __init__(self, cfg, project):
        super().__init__(cfg, project)
        self.repo = self.resolve("repo", "./third_party/Qwen3-TTS")
        self.python = resolve_python(self.bcfg.get("python", "auto"), self.repo, cfg)
        self.speaker = _speaker_name(project.voice)
        self.models_root = self.resolve("models_dir", "./third_party/models")
        self._active: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------ 模型选择
    def _mode_and_model(self) -> Dict[str, str]:
        if self._active:
            return self._active
        sel = self.selected_checkpoint()
        if sel and Path(sel.get("path", "")).exists():
            return {"mode": "custom", "model": sel["path"], "id": sel.get("id", "ft")}
        return {"mode": "clone", "model": str(self.bcfg.get("model", "Qwen/Qwen3-TTS-12Hz-1.7B-Base")), "id": "base"}

    def model_id(self) -> str:
        m = self._mode_and_model()
        return f"qwen3-{m['mode']}-{short_hash(m['model'], n=8)}"

    def worker_command(self) -> List[str]:
        m = self._mode_and_model()
        return [self.python, str(WORKERS_DIR / "qwen3_worker.py"), "--model", m["model"],
                "--device", str(self.bcfg.get("device", "cuda:0")), "--dtype", str(self.bcfg.get("dtype", "bfloat16")),
                "--attn", str(self.bcfg.get("attn", "auto")), "--mode", m["mode"], "--speaker", self.speaker]

    def worker_env(self) -> Dict[str, str]:
        return subprocess_env()

    def check(self) -> List[str]:
        from voicetwin.backends.base import python_has_module

        if not python_has_module(self.python, "qwen_tts"):
            return [f"Python 环境 {self.python} 里没有安装 qwen-tts（pip install -U qwen-tts），"
                    f"或在 config.yaml 里设置 backends.qwen3tts.python"]
        return []

    # ------------------------------------------------------------------ 合成
    def build_payload(self, req: SynthRequest, out_path: Path) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if req.temperature is not None:
            params["temperature"] = req.temperature
        if req.top_p is not None:
            params["top_p"] = req.top_p
        if req.top_k is not None:
            params["top_k"] = req.top_k
        if self.bcfg.get("instruct"):
            params["instruct"] = self.bcfg["instruct"]
        return {"cmd": "tts", "text": req.text, "language": LANG_NAMES.get(req.lang, "Auto"),
                "ref_audio": str(Path(req.ref_audio).resolve()), "ref_text": req.ref_text,
                "seed": req.seed, "out": str(out_path), "params": params}

    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        out = super().synthesize(req, out_path)
        if req.speed and abs(req.speed - 1.0) > 0.02:  # 引擎不支持调速，用 ffmpeg 高质量变速
            tmp = out.with_suffix(".tempo.wav")
            atempo(out, tmp, req.speed)
            tmp.replace(out)
        return out

    # ------------------------------------------------------------------ 训练
    def _local_model(self, repo_or_path: str) -> Path:
        p = Path(repo_or_path).expanduser()
        if p.exists():
            return p.resolve()
        assert self.models_root is not None
        local = self.models_root / repo_or_path.replace("/", "__")
        if (local / "config.json").exists():
            return local
        log.info(f"下载模型 {repo_or_path}（只需一次）……")
        self.run_logged([self.python, str(WORKERS_DIR / "download_model.py"), repo_or_path, str(local),
                         str(self.bcfg.get("download_source", "auto"))], None, subprocess_env(), "qwen3_download")
        return local

    def train(self, progress: Optional[ProgressFn] = None, **opts: Any) -> Dict[str, Any]:
        from voicetwin.data.exporters import export_qwen3

        problems = self.check()
        finetune_dir = (self.repo / "finetuning") if self.repo else None
        if not finetune_dir or not (finetune_dir / "sft_12hz.py").exists():
            problems.append(f"找不到 Qwen3-TTS 仓库的 finetuning 脚本：{finetune_dir}"
                            "（git clone https://github.com/QwenLM/Qwen3-TTS.git third_party/Qwen3-TTS）")
        if problems:
            raise RuntimeError("Qwen3-TTS 环境有问题：\n- " + "\n- ".join(problems))
        refs = self.project.load_references()
        if not refs:
            raise RuntimeError("没有参考音频，请先运行素材准备")
        main_ref = next((r for r in refs if r["kind"] == "statement"), refs[0])
        exp = export_qwen3(self.project, self.project.abspath(main_ref["path"]))
        tcfg = {**(self.bcfg.get("train", {}) or {}), **{k: v for k, v in opts.items() if v not in (None, "auto")}}
        init_model = self._local_model(str(tcfg.get("init_model", "Qwen/Qwen3-TTS-12Hz-0.6B-Base")))
        tokenizer = self._local_model(str(self.bcfg.get("tokenizer", "Qwen/Qwen3-TTS-Tokenizer-12Hz")))
        coded = self.work_dir / "train_with_codes.jsonl"
        self.step(progress, 0.05, "提取音频编码（Qwen3-TTS Tokenizer）")
        self.run_logged([self.python, "prepare_data.py", "--device", str(self.bcfg.get("device", "cuda:0")),
                         "--tokenizer_model_path", str(tokenizer), "--input_jsonl", str(exp["jsonl"]),
                         "--output_jsonl", str(coded)], finetune_dir, subprocess_env(), "qwen3_prepare")
        out_dir = self.work_dir / "output"
        epochs = int(tcfg.get("epochs", 3))
        self.step(progress, 0.15, f"微调 Qwen3-TTS（{epochs} 轮）")
        epoch_re = re.compile(r"Epoch (\d+)")
        self.run_logged([self.python, str(WORKERS_DIR / "qwen3_sft_launcher.py"), str(finetune_dir / "sft_12hz.py"),
                         "--init_model_path", str(init_model), "--output_model_path", str(out_dir),
                         "--train_jsonl", str(coded), "--batch_size", str(tcfg.get("batch_size", 2)),
                         "--lr", str(tcfg.get("lr", 2e-5)), "--num_epochs", str(epochs), "--speaker_name", self.speaker],
                        finetune_dir, subprocess_env(), "qwen3_sft", progress, (0.15, 0.95),
                        lambda line: (int(m.group(1)) + 1) / epochs if (m := epoch_re.search(line)) else None)
        ckpts = self._list_checkpoints(out_dir)
        if not ckpts:
            raise RuntimeError("微调结束但没有找到 checkpoint，请查看 logs/qwen3_sft.log")
        info = {"speaker": self.speaker, "init_model": str(init_model), "trained_at": time.strftime("%Y-%m-%d %H:%M"),
                "checkpoints": [str(c) for c in ckpts],
                "selected": {"id": ckpts[-1].name, "path": str(ckpts[-1])}}
        self.project.update_models(self.name, info)
        self.stop()
        return info

    @staticmethod
    def _list_checkpoints(out_dir: Path) -> List[Path]:
        if not out_dir.exists():
            return []
        found = [p for p in out_dir.glob("checkpoint-epoch-*") if (p / "model.safetensors").exists()]
        return sorted(found, key=lambda p: int(p.name.rsplit("-", 1)[-1]))

    def checkpoints(self) -> List[Dict[str, Any]]:
        info = self.project.load_models().get(self.name) or {}
        paths = [Path(p) for p in info.get("checkpoints", []) if Path(p).exists()]
        return [{"id": p.name, "path": str(p)} for p in paths]

    def use_checkpoint(self, ckpt: Dict[str, Any]) -> None:
        target = {"mode": "custom", "model": ckpt["path"], "id": ckpt["id"]}
        if self._active != target:
            self._active = target
            self.restart()
