"""Windows 小工具：任务进行中阻止电脑睡眠、关闭黑色窗口的「快速编辑」、在资源管理器里打开文件。

只用标准库（ctypes），在其它系统上什么都不做；任何函数都不会抛出异常。
"""

from __future__ import annotations

import atexit
import contextlib
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Iterator, Optional, Union

from voicetwin.utils.log import get_logger

log = get_logger("winsys")

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
STD_INPUT_HANDLE = -10
ENABLE_QUICK_EDIT_MODE = 0x0040
ENABLE_EXTENDED_FLAGS = 0x0080

AWAKE_MSG = "已暂时阻止电脑自动睡眠（任务结束后自动恢复；合上笔记本盖子仍然会睡眠）"

_local = threading.local()
_k32: Any = None
_k32_lock = threading.Lock()


def _is_windows() -> bool:
    return sys.platform == "win32"


def _kernel32() -> Any:
    """kernel32.dll（独立的 WinDLL 实例，改 restype 不会影响别的库）。测试里会被替换。"""
    global _k32
    with _k32_lock:
        if _k32 is None:
            import ctypes

            _k32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        return _k32


@contextlib.contextmanager
def keep_awake() -> Iterator[None]:
    """在 with 块里阻止 Windows 自动睡眠。同一线程里可以嵌套（只有最外层真正生效）。

    SetThreadExecutionState 只对调用它的线程有效，所以要在普通函数里用（run_train 等），
    不要包住会在不同线程里继续执行的生成器。
    """
    depth = int(getattr(_local, "depth", 0) or 0)
    _local.depth = depth + 1
    applied = False
    if depth == 0 and _is_windows():
        try:
            _kernel32().SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
            applied = True
            log.info(AWAKE_MSG)
        except Exception:
            applied = False
    try:
        yield
    finally:
        _local.depth = max(0, int(getattr(_local, "depth", 1) or 1) - 1)
        if applied:
            try:
                _kernel32().SetThreadExecutionState(ES_CONTINUOUS)
            except Exception:
                pass


def quick_edit_mask(mode: int) -> int:
    """去掉「快速编辑」位、保留其它设置（必须带上 ENABLE_EXTENDED_FLAGS 才会生效）。"""
    return (int(mode) & ~ENABLE_QUICK_EDIT_MODE) | ENABLE_EXTENDED_FLAGS


_RESTORE_REGISTERED = False


def _restore_console_mode(handle: Any, mode: int) -> None:
    """程序结束时把黑色窗口的设置改回去（atexit 调用，不会抛出异常）。"""
    try:
        _kernel32().SetConsoleMode(handle, int(mode))
    except Exception:
        pass


def disable_quick_edit() -> bool:
    """关闭黑色窗口的「快速编辑模式」：否则用鼠标点一下窗口，程序输出就会被冻结，训练看起来像卡住。

    程序结束时会自动改回原来的设置：在自己打开的「命令提示符」里运行过 voicetwin.bat 之后，
    仍然可以用鼠标选中、复制窗口里的文字。成功返回 True；不是 Windows、没有控制台或调用失败时返回 False。
    """
    global _RESTORE_REGISTERED
    if not _is_windows():
        return False
    try:
        import ctypes

        k32 = _kernel32()
        get_std = k32.GetStdHandle
        try:
            get_std.restype = ctypes.c_void_p
        except Exception:
            pass
        handle = get_std(STD_INPUT_HANDLE)
        if handle in (None, 0, -1) or handle == ctypes.c_void_p(-1).value:
            return False
        mode = ctypes.c_uint32(0)
        if not k32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        new_mode = quick_edit_mask(mode.value)
        if new_mode == mode.value:
            return True
        if not k32.SetConsoleMode(handle, new_mode):
            return False
        if not _RESTORE_REGISTERED:
            atexit.register(_restore_console_mode, handle, mode.value)
            _RESTORE_REGISTERED = True
        return True
    except Exception:
        return False


def open_path(path: Union[str, Path], select: bool = False) -> bool:
    """在资源管理器（访达）里打开文件夹；select=True 时打开所在文件夹并选中这个文件。不会抛出异常。"""
    try:
        p = Path(path)
        if not p.exists():
            return False
        if _is_windows():
            if select and p.is_file():
                # explorer 的 /select 参数要求这样的写法：/select,"C:\带 空格\a.wav"
                subprocess.Popen(f'explorer /select,"{p.resolve()}"')
            else:
                os.startfile(str(p if p.is_dir() else (p.parent if select else p)))  # type: ignore[attr-defined]
            return True
        target: Optional[Path] = p
        if sys.platform == "darwin":
            cmd = ["open", "-R", str(p)] if select and p.is_file() else ["open", str(p)]
        else:
            if select and p.is_file():
                target = p.parent
            cmd = ["xdg-open", str(target)]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False
