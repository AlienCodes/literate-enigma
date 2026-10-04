"""IndexTTS2.5 引擎（B 站开源，零样本克隆）：不需要训练，给一段老师自己的录音当参考就照着说。

v18.7 起是唯一的引擎（老师 10-04 决定只用 IndexTTS25）。接口照着官方 indextts/infer_v2_5.py（commit d9e41aa）：
- 不需要参考录音的文字；参考录音只用前 15 秒；
- 中英文夹在一起的句子用 lang="ZH"（有一个汉字就是 ZH，不然会按英文读）；
- 语速用 duration_factor（>1 变慢，有效范围 0.5~2.0）在模型里面控制，音高音色不变；
- 采样参数用 IndexTTS 自己的默认（temperature 0.8、top_p 0.8、top_k 30），不用给 GPT-SoVITS 调的那一套。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from voicetwin.backends.base import SynthRequest, resolve_python
from voicetwin.backends.worker import subprocess_env
from voicetwin.backends.worker_backend import WORKERS_DIR, WorkerBackend
from voicetwin.utils.ffmpeg import atempo
from voicetwin.utils.textutil import CJK_RE, short_hash

#: 官方 infer_v2_5 的采样默认值（do_sample=True、num_beams=3、repetition_penalty=10.0 也是它的默认，不用传）
SAMPLING_DEFAULTS = {"temperature": 0.8, "top_p": 0.8, "top_k": 30}
#: duration_factor 的有效范围（官方 README §7）
DURATION_MIN, DURATION_MAX = 0.5, 2.0

#: 2.5 的模型文件夹（ModelScope / Hugging Face 上的 IndexTeam/IndexTTS-2.5）里必须有的文件
MODEL_FILES_25 = ("config.yaml", "gpt.pth", "s2mel.pth", "codec.pth", "wav2vec2bert_stats.pt", "feat1.pt", "feat2.pt")
#: 第一次运行时官方会另外下载到 <模型文件夹>/hf_cache/ 的东西（安装程序先下载好，免得生成时卡住几十分钟）
AUX_FILES = ("hf_cache/campplus_cn_common.bin", "hf_cache/bigvgan/config.json", "hf_cache/bigvgan/bigvgan_generator.pt")
AUX_DIRS = ("hf_cache/w2v-bert-2.0",)

REINSTALL = "重新运行安装程序（双击 install_windows.bat），它会把缺的东西补上"


def send_lang(text: str, lang: str) -> str:
    """IndexTTS 的语言：句子里有一个汉字就是 ZH（中英混合也是 ZH，官方 README 的混合例子就是这样），没有汉字才按英文读。"""
    return "ZH" if CJK_RE.search(text or "") or lang != "en" else "EN"


def label_for(version: str) -> str:
    """「IndexTTS25」（老师定的写法：不放点、不放空格）；IndexTTS 2 是「IndexTTS2」。"""
    return "IndexTTS" + re.sub(r"[^0-9A-Za-z]", "", str(version))


class IndexTTSBackend(WorkerBackend):
    name = "indextts"
    display_name = "IndexTTS25"
    supports_speed = True

    def __init__(self, cfg, project):
        super().__init__(cfg, project)
        self.root = self.resolve("root", "./third_party/index-tts")
        self.python = resolve_python(self.bcfg.get("python", "auto"), self.root, cfg)
        self.version = str(self.bcfg.get("version", "2.5"))
        self.display_name = label_for(self.version)

    @property
    def model_dir(self) -> Path:
        d = Path(str(self.bcfg.get("model_dir", "checkpoints")))
        return d if d.is_absolute() or self.root is None else self.root / d

    def model_id(self) -> str:
        return f"indextts-{self.version}-{short_hash(str(self.bcfg.get('model_dir')), n=6)}"

    def model_name_info(self) -> Dict[str, Any]:
        """文件名里的模型名：IndexTTS 2.5 写成「IndexTTS25」，IndexTTS 2 写成「IndexTTS2」。"""
        return {"name": label_for(self.version), "how": f"设置里的 IndexTTS 版本 {self.version}（不训练，没有模型文件要检测）",
                "files": []}

    def sampling_defaults(self) -> Dict[str, Any]:
        return dict(SAMPLING_DEFAULTS)

    def check(self) -> List[str]:
        """装好没有：程序、它自己的 Python 环境、模型文件、第一次运行要用的辅助模型。每一条都写清楚缺什么、怎么办。"""
        if not self.root or not (self.root / "indextts").is_dir():
            return [f"找不到 IndexTTS 程序（应该在 {self.root}）。{REINSTALL}。"]
        problems: List[str] = []
        if str(self.bcfg.get("python") or "auto") == "auto" and self.python == sys.executable:
            problems.append(f"IndexTTS 自己的 Python 环境没装好（{self.root / '.venv'} 不存在）。{REINSTALL}。")
        md = self.model_dir
        if self.version.startswith("2.5"):
            missing = [f for f in MODEL_FILES_25 if not (md / f).is_file()]
            if not list(md.glob("*.tiktoken")):
                missing.append("*.tiktoken")
            if missing:
                problems.append(f"IndexTTS 2.5 的模型没下载完整（{md} 里缺 {'、'.join(missing)}）。{REINSTALL}。")
        elif not (md / "config.yaml").is_file():
            problems.append(f"IndexTTS 的模型没下载（{md / 'config.yaml'} 不存在）。{REINSTALL}。")
        aux = [f for f in AUX_FILES if not (md / f).is_file()]
        aux += [d for d in AUX_DIRS if not (md / d).is_dir() or not any((md / d).iterdir())]
        if aux:
            problems.append(f"IndexTTS 第一次运行要用的辅助模型没下载（{md} 里缺 {'、'.join(aux)}）。{REINSTALL}。")
        return problems

    def worker_command(self) -> List[str]:
        return [self.python, str(WORKERS_DIR / "indextts_worker.py"), "--root", str(self.root),
                "--model_dir", str(self.model_dir), "--version", self.version,
                "--half", str(bool(self.bcfg.get("half", True))).lower(),
                "--low_vram_split", str(self.bcfg.get("low_vram_split", "oom"))]

    def worker_cwd(self):
        return self.root

    def worker_env(self) -> Dict[str, str]:
        # 缺辅助模型时官方会自己下载：国内连不上 Hugging Face，先用魔搭（ModelScope），魔搭没有的用 hf-mirror
        env = subprocess_env()
        env.setdefault("USE_MODELSCOPE", "true")
        env.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        return env

    def build_payload(self, req: SynthRequest, out_path: Path) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        # 语速：IndexTTS2.5 在模型内部控制时长（duration_factor），音高和音色不变，不对音频做后期变速
        if self.version.startswith("2.5") and req.speed and abs(req.speed - 1.0) > 0.01:
            params["duration_factor"] = round(min(DURATION_MAX, max(DURATION_MIN, 1.0 / float(req.speed))), 4)
        for key, default in SAMPLING_DEFAULTS.items():
            val = getattr(req, key)
            params[key] = default if val is None else val
        if self.bcfg.get("interval_silence") is not None:  # 只有显存不够、一句话被切开时才用到
            params["interval_silence"] = int(self.bcfg["interval_silence"])
        return {"cmd": "tts", "text": req.text, "lang": send_lang(req.text, req.lang),
                "ref_audio": str(Path(req.ref_audio).resolve()), "seed": req.seed, "out": str(out_path),
                "params": params}

    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        out = super().synthesize(req, out_path)
        # IndexTTS2 没有时长控制：用 ffmpeg atempo（WSOLA，变速不变调）；不做重采样
        if not self.version.startswith("2.5") and req.speed and abs(req.speed - 1.0) > 0.02:
            tmp = out.with_suffix(".tempo.wav")
            atempo(out, tmp, req.speed)
            tmp.replace(out)
        return out
