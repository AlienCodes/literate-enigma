"""IndexTTS2.5 / IndexTTS2 引擎（B 站开源）：零样本克隆，情绪表达和时长控制很强。

不需要训练，适合：素材很少、想马上试听，或作为 GPT-SoVITS 之外的第二选择。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from voicetwin.backends.base import SynthRequest, resolve_python
from voicetwin.backends.worker_backend import WORKERS_DIR, WorkerBackend
from voicetwin.utils.ffmpeg import atempo
from voicetwin.utils.textutil import short_hash


class IndexTTSBackend(WorkerBackend):
    name = "indextts"
    display_name = "IndexTTS"
    supports_speed = True

    def __init__(self, cfg, project):
        super().__init__(cfg, project)
        self.root = self.resolve("root", "./third_party/index-tts")
        self.python = resolve_python(self.bcfg.get("python", "auto"), self.root, cfg)
        self.version = str(self.bcfg.get("version", "2.5"))

    def model_id(self) -> str:
        return f"indextts-{self.version}-{short_hash(str(self.bcfg.get('model_dir')), n=6)}"

    def check(self) -> List[str]:
        if not self.root or not (self.root / "indextts").exists():
            return [f"找不到 index-tts 仓库：{self.root}（git clone https://github.com/index-tts/index-tts.git third_party/index-tts）"]
        model_dir = Path(self.bcfg.get("model_dir", "checkpoints"))
        model_dir = model_dir if model_dir.is_absolute() else self.root / model_dir
        if not (model_dir / "config.yaml").exists():
            return [f"缺少 IndexTTS 模型：{model_dir}/config.yaml（modelscope download --model IndexTeam/IndexTTS-2.5 --local_dir {model_dir}）"]
        return []

    def worker_command(self) -> List[str]:
        return [self.python, str(WORKERS_DIR / "indextts_worker.py"), "--root", str(self.root),
                "--model_dir", str(self.bcfg.get("model_dir", "checkpoints")), "--version", self.version,
                "--half", str(bool(self.bcfg.get("half", True))).lower()]

    def worker_cwd(self):
        return self.root

    def build_payload(self, req: SynthRequest, out_path: Path) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        ref = str(Path(req.ref_audio).resolve())
        if float(self.bcfg.get("emo_alpha", 0.6)) > 0:
            params["emo_audio"] = ref  # 用你自己的参考音频作为情绪/语气参考
            params["emo_alpha"] = float(self.bcfg.get("emo_alpha", 0.6))
        # 语速：IndexTTS2.5 在模型内部控制时长（duration_factor），音高和音色不变，不对音频做后期变速
        if self.version.startswith("2.5") and req.speed and abs(req.speed - 1.0) > 0.01:
            params["duration_factor"] = 1.0 / float(req.speed)
        for key in ("temperature", "top_p", "top_k"):
            val = getattr(req, key)
            if val is not None:
                params[key] = val
        return {"cmd": "tts", "text": req.text, "lang": "EN" if req.lang == "en" else "ZH", "ref_audio": ref,
                "seed": req.seed, "out": str(out_path), "params": params}

    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        out = super().synthesize(req, out_path)
        # IndexTTS2 没有时长控制：用 ffmpeg atempo（WSOLA，变速不变调）；不做重采样
        if not self.version.startswith("2.5") and req.speed and abs(req.speed - 1.0) > 0.02:
            tmp = out.with_suffix(".tempo.wav")
            atempo(out, tmp, req.speed)
            tmp.replace(out)
        return out
