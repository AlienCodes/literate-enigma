"""先写临时文件、再整个换上去（写到一半出错也不会留下半个文件）。

临时文件名每个程序、每个线程各用各的：以前固定叫「xxx.tmp」，两个地方同时写同一个文件时（例如「保存修改」还在写
profile.json，老师就点了「确认训练素材」），一个把临时文件换上去以后，另一个找不到自己的临时文件，报错
「No such file or directory: ...profile.json.tmp」（10-03 浏览器实测发现）。

换上去之前先让硬盘真的写好（fsync）：以前只是交给系统，系统过几秒才写到硬盘上。保存以后几秒内断电 / 死机按了电源键，
Windows 记得「换过了」，内容却没写进去，开机以后 manifest.jsonl 变成空的或者一堆 0，整张校对表没了（第四轮找 bug 发现）。"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Optional


def tmp_for(path: Path) -> Path:
    """path 旁边的临时文件名（这个程序、这个线程专用）。"""
    path = Path(path)
    return path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")


#: Windows 上正式文件这一刻正被别的线程读 / 换的时候，换文件会被拒绝（PermissionError，一般一眨眼就好）：
#: 等一会儿再试，最多大约 3 秒；还不行（例如正被 Excel 一直打开着）才把错误报出去
RETRY_WAITS = [0.02, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3, 0.5, 0.5, 1.0]


def sync(path: Path) -> None:
    """让写好的文件真的落到硬盘上（不只是在系统的缓存里）。个别网络盘 / 虚拟盘不支持：照样保存（和以前一样）。"""
    try:
        with open(path, "rb+") as f:
            os.fsync(f.fileno())
    except OSError:
        pass


def finish(tmp: Path, path: Path) -> None:
    """把写好的临时文件换成正式文件（先确认临时文件已经写到硬盘上）；换不上（例如正被 Excel 打开）时删掉临时文件，
    再把错误报出去。"""
    try:
        sync(tmp)
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


def remove(path: Path, fallback_text: Optional[str] = None) -> None:
    """删掉文件（本来就没有也算删掉了）。Windows 上这一刻正被别的线程读着（或杀毒软件、OneDrive 正在看）时删不掉
    （PermissionError）：和 finish 一样等一会儿再试，最多大约 3 秒。还删不掉：给了 fallback_text 就把内容换成它
    （例如 "{}" = 空的，读的地方当作没有），不然把错误报出去——不能悄悄当成删掉了（以前「撤销这一行的修改」说撤销了，
    草稿文件却还在，下次「保存修改」把撤销了的字存了进去）。"""
    path = Path(path)
    for wait in RETRY_WAITS + [None]:
        try:
            path.unlink()
            return
        except FileNotFoundError:
            return
        except PermissionError:
            if wait is None:
                if fallback_text is None:
                    raise
                break
            time.sleep(wait)
    write_text(path, fallback_text)


def _useless(p: Path) -> bool:
    """这份副本里什么都没有（空的，或者全是 0：断电后 Windows 留下的样子）。"""
    try:
        data = p.read_bytes()
    except OSError:
        return False
    return not data.strip(b"\x00 \r\n\t")


def keep_bad_copy(path: Path) -> None:
    """文件坏了（读出来不是完整的内容）：先留一份「.bad」副本（只留第一次的），方便以后找回，再当作没有。
    以前留的那份什么都没有（空的 / 全是 0）时换成这一次的（不然后来真正有内容的坏文件一份都留不下）。"""
    path = Path(path)
    bad = path.with_name(path.name + ".bad")
    try:
        if path.exists() and (not bad.exists() or (_useless(bad) and not _useless(path))):
            import shutil

            shutil.copy2(path, bad)
    except OSError:
        pass
