"""统一日志：终端输出 + 项目日志文件。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

_LOGGER_NAME = "voicetwin"
_configured = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    base = logging.getLogger(_LOGGER_NAME)
    if not _configured:
        setup_logging()
    return base.getChild(name) if name else base


def setup_logging(level: int = logging.INFO, log_file: Optional[Path] = None) -> logging.Logger:
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    if not any(getattr(h, "_voicetwin_console", False) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S"))
        handler._voicetwin_console = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        existing = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        if not any(Path(h.baseFilename) == log_file.resolve() for h in existing):
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
            logger.addHandler(fh)
    _configured = True
    return logger
