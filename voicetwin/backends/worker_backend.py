"""基于 worker 子进程的引擎基类。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from voicetwin.backends.base import Backend, SynthRequest, check_cancel
from voicetwin.backends.worker import WorkerClient, subprocess_env

WORKERS_DIR = Path(__file__).with_name("workers")


class WorkerBackend(Backend):
    worker_script = ""

    def __init__(self, cfg, project):
        super().__init__(cfg, project)
        self.client: Optional[WorkerClient] = None

    # 子类实现
    def worker_command(self) -> List[str]:
        raise NotImplementedError

    def worker_cwd(self) -> Optional[Path]:
        return None

    def worker_env(self) -> Dict[str, str]:
        return subprocess_env()

    def build_payload(self, req: SynthRequest, out_path: Path) -> Dict[str, Any]:
        raise NotImplementedError

    # 通用实现
    def start(self) -> None:
        check_cancel()  # 点了「停止」就不要再花几分钟加载模型
        if self.client is None:
            self.client = WorkerClient(
                self.worker_command(), cwd=self.worker_cwd(), env=self.worker_env(),
                log_path=self.project.logs_dir / f"{self.name}_worker.log",
                startup_timeout=float(self.bcfg.get("startup_timeout", 900)), name=self.display_name,
            )
        self.client.start()

    def stop(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def restart(self) -> None:
        self.stop()
        self.start()

    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        if self.client is None:
            self.start()
        assert self.client is not None
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        resp = self.client.request(self.build_payload(req, out_path))
        return Path(resp.get("out") or out_path)
