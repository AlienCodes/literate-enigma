"""测试引擎：不需要显卡和模型，用来验证整条流程。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

from voicetwin.backends.base import SynthRequest
from voicetwin.backends.worker_backend import WORKERS_DIR, WorkerBackend


class DummyBackend(WorkerBackend):
    name = "dummy"
    display_name = "测试引擎(dummy)"
    supports_speed = True
    file_model_name = "dummy"           # 测试引擎生成的文件名最后是「_dummy」

    def worker_command(self) -> List[str]:
        return [sys.executable, str(WORKERS_DIR / "dummy_worker.py"), "--f0", str(self.bcfg.get("f0", 150)),
                "--rate", str(self.bcfg.get("rate", 4.6))]

    def build_payload(self, req: SynthRequest, out_path: Path) -> Dict[str, Any]:
        return {"cmd": "tts", "text": req.text, "lang": req.lang, "seed": req.seed, "out": str(out_path),
                "params": {"speed": req.speed}}

    def model_id(self) -> str:
        return f"dummy-{self.bcfg.get('f0', 150)}"
