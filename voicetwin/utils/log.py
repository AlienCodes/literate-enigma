"""统一日志：终端输出 + 项目日志文件。

每个声音（项目）有自己的 logs/ 文件夹。打开另一个声音时，不再把日志同时写进上一个声音的日志文件里：
- 哪个线程打开了哪个声音（setup_logging(log_file=...)），这个线程的日志就只写进那个声音的日志文件；
- 别的声音的日志文件如果已经没有线程在用，就关掉它（网页里后台任务还在跑的声音会保留）。
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import weakref
from pathlib import Path
from typing import Optional

_LOGGER_NAME = "voicetwin"
_configured = False
_lock = threading.RLock()
_tls = threading.local()
# 线程 → 它当前在用的 logs 文件夹（线程结束后自动消失）
_bound: "weakref.WeakKeyDictionary[threading.Thread, str]" = weakref.WeakKeyDictionary()


def _dir_key(path: Path) -> str:
    try:
        path = path.resolve()
    except Exception:
        path = path.absolute()
    return os.path.normcase(str(path))


class _ProjectFilter(logging.Filter):
    """只让「绑定到这个 logs 文件夹的线程」（以及没有绑定任何声音的线程）写进这个文件。"""

    def __init__(self, logs_dir: str):
        super().__init__()
        self.logs_dir = logs_dir

    def filter(self, record: logging.LogRecord) -> bool:  # 在写日志的那个线程里调用
        bound = getattr(_tls, "logs_dir", None)
        return bound is None or bound == self.logs_dir


def get_logger(name: Optional[str] = None) -> logging.Logger:
    base = logging.getLogger(_LOGGER_NAME)
    if not _configured:
        setup_logging()
    return base.getChild(name) if name else base


def _bind_current_thread(logs_dir: str) -> None:
    _tls.logs_dir = logs_dir
    try:
        _bound[threading.current_thread()] = logs_dir
    except TypeError:  # 极少数线程对象不支持弱引用
        pass


def _active_dirs() -> set:
    return {d for t, d in list(_bound.items()) if t.is_alive()}


def setup_logging(level: Optional[int] = None, log_file: Optional[Path] = None) -> logging.Logger:
    """配置终端日志；给出 log_file 时再加一个写入该文件的日志（UTF-8）。

    level 为 None 时：第一次配置用 INFO，之后保持原来的级别（不会把 --verbose 的 DEBUG 改回 INFO）。
    """
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    with _lock:
        if level is not None:
            logger.setLevel(level)
        elif not _configured:
            logger.setLevel(logging.INFO)
        logger.propagate = False
        if not any(getattr(h, "_voicetwin_console", False) for h in logger.handlers):
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S"))
            handler._voicetwin_console = True  # type: ignore[attr-defined]
            logger.addHandler(handler)
        if log_file is not None:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            logs_dir = _dir_key(log_file.parent)
            _bind_current_thread(logs_dir)
            active = _active_dirs() | {logs_dir}
            # 关掉别的声音的、已经没有线程在用的日志文件
            for h in list(logger.handlers):
                owner = getattr(h, "_voicetwin_logs_dir", None)
                if owner is not None and owner not in active:
                    logger.removeHandler(h)
                    try:
                        h.close()
                    except Exception:
                        pass
            target = _dir_key(log_file)
            existing = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            if not any(_dir_key(Path(h.baseFilename)) == target for h in existing):
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
                fh._voicetwin_logs_dir = logs_dir  # type: ignore[attr-defined]
                fh.addFilter(_ProjectFilter(logs_dir))
                logger.addHandler(fh)
        _configured = True
    return logger
