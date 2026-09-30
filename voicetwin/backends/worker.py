"""与合成引擎子进程通信（JSON Lines 协议）。

每个引擎（Qwen3-TTS、IndexTTS……）依赖的 PyTorch/transformers 版本互相冲突，
所以各自运行在自己的 Python 环境里，VoiceTwin 通过 stdin/stdout 发送 JSON 请求：
    → {"id": 1, "cmd": "tts", "text": "...", "out": "x.wav", ...}
    ← {"id": 1, "ok": true, "out": "x.wav", "sr": 24000}
worker 启动完成时先发一行 {"event": "ready"}。
"""

from __future__ import annotations

import collections
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from voicetwin.utils.log import get_logger

log = get_logger("worker")


class WorkerError(RuntimeError):
    pass


def subprocess_env(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = dict(os.environ)
    env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"})
    if extra:
        env.update({k: str(v) for k, v in extra.items() if v is not None})
    return env


class WorkerClient:
    def __init__(self, cmd: List[str], cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None,
                 log_path: Optional[Path] = None, startup_timeout: float = 600.0, name: str = "worker"):
        self.cmd = [str(c) for c in cmd]
        self.cwd = str(cwd) if cwd else None
        self.env = env or subprocess_env()
        self.log_path = Path(log_path) if log_path else None
        self.startup_timeout = startup_timeout
        self.name = name
        self.proc: Optional[subprocess.Popen] = None
        self._responses: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._tail: Deque[str] = collections.deque(maxlen=80)
        self._next_id = 0
        self._lock = threading.Lock()
        self.ready_info: Dict[str, Any] = {}

    # ------------------------------------------------------------------ 生命周期
    def start(self) -> Dict[str, Any]:
        if self.proc is not None and self.proc.poll() is None:
            return self.ready_info
        log.info(f"启动 {self.name}：{' '.join(self.cmd[:3])} ……（首次加载模型可能需要几分钟）")
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.proc = subprocess.Popen(
            self.cmd, cwd=self.cwd, env=self.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0, creationflags=creationflags,
        )
        threading.Thread(target=self._pump_stdout, daemon=True).start()
        threading.Thread(target=self._pump_stderr, daemon=True).start()
        deadline = time.time() + self.startup_timeout
        while time.time() < deadline:
            try:
                msg = self._responses.get(timeout=0.5)
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise WorkerError(f"{self.name} 启动失败（退出码 {self.proc.returncode}）：\n{self.tail()}")
                continue
            if msg.get("event") == "ready":
                self.ready_info = msg
                log.info(f"{self.name} 已就绪")
                return msg
            if msg.get("event") == "error":
                raise WorkerError(f"{self.name} 启动失败：{msg.get('error')}\n{self.tail()}")
        self.close()
        raise WorkerError(f"{self.name} 启动超时（{self.startup_timeout:.0f} 秒）：\n{self.tail()}")

    def close(self) -> None:
        if self.proc is None:
            return
        if self.proc.poll() is None:
            try:
                self._send({"id": -1, "cmd": "shutdown"})
                self.proc.wait(timeout=15)
            except Exception:
                self.proc.kill()
        self.proc = None

    def tail(self) -> str:
        return "\n".join(self._tail)

    # ------------------------------------------------------------------ 通信
    def _pump_stdout(self) -> None:
        assert self.proc is not None and self.proc.stdout is not None
        for raw in iter(self.proc.stdout.readline, b""):
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                self._responses.put(json.loads(line))
            except json.JSONDecodeError:
                self._tail.append(line)

    def _pump_stderr(self) -> None:
        assert self.proc is not None and self.proc.stderr is not None
        fh = open(self.log_path, "a", encoding="utf-8") if self.log_path else None
        try:
            for raw in iter(self.proc.stderr.readline, b""):
                line = raw.decode("utf-8", errors="replace").rstrip()
                if not line:
                    continue
                self._tail.append(line)
                if fh:
                    fh.write(line + "\n")
                    fh.flush()
        finally:
            if fh:
                fh.close()

    def _send(self, payload: Dict[str, Any]) -> None:
        assert self.proc is not None and self.proc.stdin is not None
        self.proc.stdin.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
        self.proc.stdin.flush()

    def request(self, payload: Dict[str, Any], timeout: float = 900.0) -> Dict[str, Any]:
        with self._lock:
            if self.proc is None or self.proc.poll() is not None:
                self.start()
            self._next_id += 1
            rid = self._next_id
            self._send({**payload, "id": rid})
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    msg = self._responses.get(timeout=0.5)
                except queue.Empty:
                    if self.proc is None or self.proc.poll() is not None:
                        raise WorkerError(f"{self.name} 意外退出：\n{self.tail()}")
                    continue
                if msg.get("id") != rid:
                    continue
                if not msg.get("ok"):
                    raise WorkerError(f"{self.name} 合成失败：{msg.get('error')}")
                return msg
            raise WorkerError(f"{self.name} 请求超时（{timeout:.0f} 秒）")

