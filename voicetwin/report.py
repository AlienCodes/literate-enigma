"""出错时自动生成「问题报告」。

老师的要求（v18.4）：一旦出问题，「详细过程」里直接生成一份问题报告，说清楚到底是什么原因。
所以任何任务出错时（网页 tasks._run，以及训练后「自动挑选」这种不算整个任务失败的步骤）：
1. 在「详细过程」里写一段简短的报告：停在哪一步、原因、怎么办、自动诊断出的线索、完整报告存在哪里；
2. 在这个声音的 logs 文件夹里存一份完整的「问题报告_日期_时间.txt」：再加上技术细节、这次任务的运行记录、
   这次改动过的各个记录文件（整理过，重复的报错只留一份）、电脑情况（只写检测到的，检测不出来就写检测不出来）。
生成报告本身永远不能再出错：每一部分都单独 try，出问题就跳过那一部分。
"""

import os
import platform
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from voicetwin.utils.log import get_logger
from voicetwin.utils.logtail import condense, diagnose_gsv_api, exception_counts, last_run, latest_files, read_text

log = get_logger("report")

REPORT_PREFIX = "问题报告_"
#: logs 文件夹里最多留几份问题报告（多了删最旧的）
KEEP_REPORTS = 30
API_LOG = "gptsovits_api.log"
#: 这些记录文件不在报告里重复（voicetwin.log 就是「运行记录」本身）
SKIP_LOGS = ("voicetwin.log",)
LINE = "=" * 60


def _safe(fn, default=""):
    try:
        return fn()
    except Exception:
        return default


def _friendly(exc: Any, friendly: Any = None) -> Any:
    if friendly is not None:
        return friendly
    from voicetwin.errors import explain

    return explain(exc)


def _technical(exc: Any) -> str:
    if isinstance(exc, BaseException):
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        return condense(tb, max_lines=120, max_line_len=600)
    return str(exc or "")


def _diagnosis(logs_dir: Optional[Path], since: Optional[float], tech: str) -> List[str]:
    """从这次任务期间改动过的记录文件里找线索（只写记录里真的有的东西）。"""
    notes: List[str] = []
    if logs_dir is None:
        return notes
    api = logs_dir / API_LOG
    if api.exists() and (since is None or _safe(lambda: api.stat().st_mtime, 0) >= since - 2):
        notes += diagnose_gsv_api(last_run(read_text(api)))
    for p in latest_files(logs_dir, since or 0, exclude=SKIP_LOGS + (API_LOG,))[:4]:
        counts = exception_counts(read_text(p, max_bytes=2_000_000))
        for exc_line, n in counts[-2:]:
            notes.append(f"{p.name} 里的报错：{exc_line[:200]}" + (f"（共 {n} 次）" if n > 1 else ""))
    if "CUDA out of memory" in tech and not any("显存" in x for x in notes):
        notes.append("报错里有「显卡内存（显存）不够」（CUDA out of memory）。")
    return notes


def _computer(logs_dir: Optional[Path]) -> List[str]:
    out = [f"系统：{_safe(platform.platform, '检测不出来') or '检测不出来'}",
           f"Python：{sys.version.split()[0]}（{sys.executable}）"]

    def gpu() -> str:
        from voicetwin.utils import gpu as g

        st = g.gpu_status()
        if not st.get("name"):
            return "显卡：" + (st.get("message") or "检测不出来")
        mem = ""
        if st.get("total_gb") is not None:
            mem = f"，显存 {st['total_gb']:.1f} GB"
            if st.get("free_gb") is not None:
                mem += f"（现在可用 {st['free_gb']:.1f} GB）"
        drv = f"，驱动 {st['driver']}" if st.get("driver") else ""
        return f"显卡：{st['name']}{mem}{drv}"

    out.append(_safe(gpu, "显卡：检测不出来"))
    if logs_dir is not None:
        def disk() -> str:
            u = shutil.disk_usage(str(logs_dir))
            return f"硬盘（{Path(logs_dir).anchor or '/'}）剩余：{u.free / 1024 ** 3:.1f} GB"

        out.append(_safe(disk, "硬盘剩余：检测不出来"))
    return out


def build(exc: Any, what: str = "", voice: str = "", where: str = "", elapsed: str = "",
          logs_dir: Optional[Path] = None, task_lines: Sequence[str] = (), since: Optional[float] = None,
          friendly: Any = None, report_path: Optional[Path] = None) -> Tuple[str, str]:
    """返回 (显示在「详细过程」里的简短报告, 存成文件的完整报告)。"""
    from voicetwin import __version__

    f = _safe(lambda: _friendly(exc, friendly), None)
    title = getattr(f, "title", "") or str(exc)[:200] or "出现了意外错误"
    advice = getattr(f, "advice", "") or ""
    tech = _safe(lambda: _technical(exc), str(exc))
    logs_dir = Path(logs_dir) if logs_dir else None
    notes = _safe(lambda: _diagnosis(logs_dir, since, tech), [])

    head = [f"做的事：{what or '（不知道）'}" + (f"（声音：{voice}）" if voice else "")]
    if where:
        head.append(f"停在哪里：{where}")
    if elapsed:
        head.append(f"已用时间：{elapsed}")
    head.append(f"原因：{title}")
    if advice:
        head.append(f"怎么办：{advice}")

    short = ["📋 问题报告（出错时自动生成）"] + head
    if notes:
        short.append("自动诊断出的线索：")
        short += [f"- {x}" for x in notes]
    if report_path is not None:
        short.append(f"完整的问题报告已保存在：{report_path}")
        short.append("需要帮忙时，把这个文件（或者这里的文字）发给帮你的人就行。")

    full = [LINE, "声音分身 VoiceTwin 问题报告", LINE,
            f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"声音分身版本：{__version__}"] + head
    full += ["", "【自动诊断出的线索】"] + ([f"- {x}" for x in notes] or ["（记录里没有找到更多线索）"])
    full += ["", "【技术细节】", tech or "（没有）"]
    if task_lines:
        full += ["", f"【这次任务的运行记录（最后 {len(task_lines)} 行）】"] + list(task_lines)
    if logs_dir is not None:
        api = logs_dir / API_LOG
        if api.exists() and (since is None or _safe(lambda: api.stat().st_mtime, 0) >= since - 2):
            full += ["", f"【合成引擎的记录 {API_LOG}（最后一次启动的部分，重复的报错已合并）】",
                     _safe(lambda: condense(last_run(read_text(api)), max_lines=120), "（读不出来）")]
        for p in _safe(lambda: latest_files(logs_dir, since or 0, exclude=SKIP_LOGS + (API_LOG,)), [])[:4]:
            if p.name.startswith(REPORT_PREFIX):
                continue
            full += ["", f"【记录文件 {p.name}（最后的部分，重复的已合并）】",
                     _safe(lambda: condense(read_text(p, max_bytes=2_000_000), max_lines=60, head=10), "（读不出来）")]
    full += ["", "【电脑情况】"] + _safe(lambda: _computer(logs_dir), ["（检测不出来）"])
    full += [LINE]
    return "\n".join(short), "\n".join(full) + "\n"


def _cleanup(logs_dir: Path) -> None:
    files = sorted(logs_dir.glob(REPORT_PREFIX + "*.txt"))
    for old in files[:-KEEP_REPORTS]:
        try:
            old.unlink()
        except OSError:
            pass


def report_failure(exc: Any, what: str = "", voice: str = "", where: str = "", elapsed: str = "",
                   logs_dir: Optional[Path] = None, task_lines: Iterable[str] = (), since: Optional[float] = None,
                   friendly: Any = None) -> Optional[Path]:
    """生成问题报告：完整的存成文件，简短的写进日志（网页「详细过程」里就能看到）。永远不抛异常。

    返回报告文件的路径（存不了时是 None）。"""
    try:
        lines = [str(x) for x in task_lines][-150:]
        path: Optional[Path] = None
        if logs_dir is not None:
            try:
                Path(logs_dir).mkdir(parents=True, exist_ok=True)
                path = Path(logs_dir) / f"{REPORT_PREFIX}{time.strftime('%Y%m%d_%H%M%S')}.txt"
                n = 1
                while path.exists():
                    n += 1
                    path = Path(logs_dir) / f"{REPORT_PREFIX}{time.strftime('%Y%m%d_%H%M%S')}_{n}.txt"
            except OSError:
                path = None
        short, full = build(exc, what=what, voice=voice, where=where, elapsed=elapsed, logs_dir=logs_dir,
                            task_lines=lines, since=since, friendly=friendly, report_path=path)
        if path is not None:
            try:
                path.write_text(full, encoding="utf-8-sig")  # 带 BOM：Windows 的记事本一定按 UTF-8 打开
                _cleanup(Path(logs_dir))
            except OSError:
                path = None
                short = build(exc, what=what, voice=voice, where=where, elapsed=elapsed, logs_dir=logs_dir,
                              task_lines=lines, since=since, friendly=friendly)[0]
                short += "\n（完整的问题报告没能存成文件，可以直接复制这里的文字。）"
        log.info(short)
        return path
    except Exception:  # pragma: no cover - 报告本身出错也不能影响程序
        try:
            log.debug("生成问题报告时出错", exc_info=True)
        except Exception:
            pass
        return None
