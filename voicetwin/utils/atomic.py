"""先写临时文件、再整个换上去（写到一半出错也不会留下半个文件）。

临时文件名每个程序、每个线程各用各的：以前固定叫「xxx.tmp」，两个地方同时写同一个文件时（例如「保存修改」还在写
profile.json，老师就点了「确认训练素材」），一个把临时文件换上去以后，另一个找不到自己的临时文件，报错
「No such file or directory: ...profile.json.tmp」（10-03 浏览器实测发现）。"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path


def tmp_for(path: Path) -> Path:
    """path 旁边的临时文件名（这个程序、这个线程专用）。"""
    path = Path(path)
    return path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")


#: Windows 上正式文件这一刻正被别的线程读 / 换的时候，换文件会被拒绝（PermissionError，一般一眨眼就好）：
#: 等一会儿再试，最多大约 3 秒；还不行（例如正被 Excel 一直打开着）才把错误报出去
RETRY_WAITS = [0.02, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3, 0.5, 0.5, 1.0]


def finish(tmp: Path, path: Path) -> None:
    """把写好的临时文件换成正式文件；换不上（例如正被 Excel 打开）时删掉临时文件，再把错误报出去。"""
    try:
        for wait in RETRY_WAITS + [None]:
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if wait is None:
                    raise
                time.sleep(wait)
    except BaseException:
        try:
            Path(tmp).unlink()
        except OSError:
            pass
        raise


def write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """整个文件一次写好（先写临时文件再换上去）。"""
    path = Path(path)
    tmp = tmp_for(path)
    try:
        tmp.write_text(text, encoding=encoding)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    finish(tmp, path)


def read_text(path: Path, encoding: str = "utf-8") -> str:
    """读整个文件；Windows 上一眨眼的占用（杀毒软件、OneDrive 正在看这个文件）等一会儿再读。
    文件不存在照样抛 FileNotFoundError；一直读不了才把错误报出去（不能当成「没有」，不然下次保存会把里面的东西冲掉）。
    写到一半断电、正好断在一个汉字中间：读不出的那几个字节换成「�」（不报错），交给调用的地方当坏行 / 坏文件处理。"""
    for wait in RETRY_WAITS + [None]:
        try:
            return Path(path).read_text(encoding=encoding, errors="replace")
        except FileNotFoundError:
            raise
        except PermissionError:
            if wait is None:
                raise
            time.sleep(wait)
    raise OSError(f"读不了 {path}")  # pragma: no cover - 上面的循环一定会返回或抛出


def keep_bad_copy(path: Path) -> None:
    """文件坏了（读出来不是完整的内容）：先留一份「.bad」副本（只留第一次的），方便以后找回，再当作没有。"""
    path = Path(path)
    bad = path.with_name(path.name + ".bad")
    try:
        if path.exists() and not bad.exists():
            import shutil

            shutil.copy2(path, bad)
    except OSError:
        pass
