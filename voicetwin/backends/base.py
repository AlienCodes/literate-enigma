"""合成引擎统一接口。"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from voicetwin.backends.worker import subprocess_env
from voicetwin.config import Config, resolve_path
from voicetwin.project import Project
from voicetwin.utils.log import get_logger

log = get_logger("backend")
ProgressFn = Callable[[float, str], None]


@dataclass
class SynthRequest:
    text: str
    lang: str                       # zh（可夹英文）| en
    ref_audio: Path
    ref_text: str
    ref_lang: str
    aux_refs: List[Path] = field(default_factory=list)
    seed: int = 0
    speed: float = 1.0
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class Backend:
    name = "base"
    display_name = "base"
    supports_training = False
    supports_speed = False           # 引擎本身能否调语速（不能的话由 ffmpeg atempo 后处理）
    supports_aux_refs = False

    def __init__(self, cfg: Config, project: Project):
        self.cfg = cfg
        self.project = project
        self.bcfg: Dict[str, Any] = cfg.backend(self.name)
        self.work_dir = project.models_dir / self.name
        self.work_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ 生命周期
    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def __enter__(self) -> "Backend":
        self.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.stop()

    # ------------------------------------------------------------------ 合成
    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        raise NotImplementedError

    def model_id(self) -> str:
        """当前使用的模型标识（参与缓存键，换模型后缓存自动失效）。"""
        return self.name

    # ------------------------------------------------------------------ 训练 / 检查点
    def check(self) -> List[str]:
        """返回安装/配置问题列表（空列表表示一切正常）。"""
        return []

    def train(self, progress: Optional[ProgressFn] = None, **opts: Any) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.display_name} 不支持微调训练（只能零样本克隆）")

    def checkpoints(self) -> List[Dict[str, Any]]:
        """可供自动挑选的模型组合，例如 [{"id": "s8-g15", ...}, ...]。"""
        return []

    def use_checkpoint(self, ckpt: Dict[str, Any]) -> None:
        pass

    def selected_checkpoint(self) -> Optional[Dict[str, Any]]:
        return (self.project.load_models().get(self.name) or {}).get("selected")

    def speed_calibration(self) -> Dict[str, float]:
        return (self.project.load_models().get(self.name) or {}).get("speed", {}) or {}

    # ------------------------------------------------------------------ 工具
    def resolve(self, key: str, default: str = "") -> Optional[Path]:
        return resolve_path(self.cfg, self.bcfg.get(key, default))

    def run_logged(self, cmd: List[str], cwd: Optional[Path], env: Dict[str, str], log_name: str,
                   progress: Optional[ProgressFn] = None, progress_range: tuple = (0.0, 1.0),
                   parse_progress: Optional[Callable[[str], Optional[float]]] = None) -> None:
        """运行训练类子进程，输出同时写入日志文件；失败时抛出带日志尾部的异常。"""
        log_path = self.project.logs_dir / f"{log_name}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log.info(f"▶ {log_name}：{' '.join(str(c) for c in cmd[:4])} …（日志：{log_path}）")
        tail: List[str] = []
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with open(log_path, "a", encoding="utf-8") as fh:
            proc = subprocess.Popen([str(c) for c in cmd], cwd=str(cwd) if cwd else None, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0,
                                    creationflags=creationflags)
            assert proc.stdout is not None
            buf = b""
            while True:
                chunk = proc.stdout.read(1024)
                if not chunk:
                    break
                buf += chunk
                parts = buf.replace(b"\r", b"\n").split(b"\n")
                buf = parts.pop()
                for raw in parts:
                    line = raw.decode("utf-8", errors="replace").rstrip()
                    if not line:
                        continue
                    fh.write(line + "\n")
                    tail.append(line)
                    if len(tail) > 60:
                        tail.pop(0)
                    if parse_progress and progress:
                        frac = parse_progress(line)
                        if frac is not None:
                            lo, hi = progress_range
                            try:
                                progress(lo + (hi - lo) * max(0.0, min(1.0, frac)), line[-120:])
                            except Exception:
                                pass
            fh.flush()
            code = proc.wait()
        if code != 0:
            raise RuntimeError(f"{log_name} 失败（退出码 {code}）。最后的日志：\n" + "\n".join(tail[-30:]))


def resolve_python(configured: Optional[str], root: Optional[Path], cfg: Config) -> str:
    """找到引擎自己的 Python 解释器。"""
    if configured and configured != "auto":
        p = resolve_path(cfg, configured)
        if p and p.exists():
            return str(p)
        return str(configured)  # 可能是 PATH 里的命令，如 "python"
    if root:
        for rel in ("runtime/python.exe", "runtime/python", "runtime/bin/python", ".venv/Scripts/python.exe",
                    ".venv/bin/python", "venv/Scripts/python.exe", "venv/bin/python", "env/python.exe"):
            cand = root / rel
            if cand.exists():
                return str(cand)
    return sys.executable


def python_has_module(python: str, module: str, env: Optional[Dict[str, str]] = None, cwd: Optional[Path] = None) -> bool:
    try:
        proc = subprocess.run([python, "-c", f"import {module}"], env=env or subprocess_env(), cwd=str(cwd) if cwd else None,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        return proc.returncode == 0
    except Exception:
        return False


def gpu_memory_gb(python: str, env: Optional[Dict[str, str]] = None) -> float:
    code = ("import torch;print(torch.cuda.get_device_properties(0).total_memory/1024**3 "
            "if torch.cuda.is_available() else 0)")
    try:
        out = subprocess.run([python, "-c", code], env=env or subprocess_env(), stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, timeout=180).stdout.decode().strip().splitlines()
        return float(out[-1]) if out else 0.0
    except Exception:
        return 0.0


_BACKENDS: Dict[str, str] = {
    "gptsovits": "voicetwin.backends.gptsovits:GPTSoVITSBackend",
    "qwen3tts": "voicetwin.backends.qwen3tts:Qwen3TTSBackend",
    "indextts": "voicetwin.backends.indextts:IndexTTSBackend",
    "dummy": "voicetwin.backends.dummy:DummyBackend",
}


def available_backends() -> List[str]:
    return list(_BACKENDS)


def get_backend(name: str, cfg: Config, project: Project) -> Backend:
    import importlib

    name = (name or cfg.get("backend") or "gptsovits").lower()
    if name not in _BACKENDS:
        raise ValueError(f"未知引擎 {name}，可选：{', '.join(_BACKENDS)}")
    mod_name, cls_name = _BACKENDS[name].split(":")
    cls = getattr(importlib.import_module(mod_name), cls_name)
    return cls(cfg, project)
