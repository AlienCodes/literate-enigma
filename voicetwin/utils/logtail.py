"""把很长的程序记录（比如 GPT-SoVITS 推理服务的 gptsovits_api.log）整理成人能看的几十行。

为什么需要：v18.2 时老师的 gptsovits_api.log 有 3 万多行，几乎全是同一个报错重复了 867 次，
真正有用的「服务已经开好了」那一行淹没在中间。这里做三件事：
1. 只取最后一次启动之后的部分（每次启动时程序会写一行 RUN_MARKER 开头的分隔线）；
2. 连续重复的内容（包括「请求记录 + 报错 + 一大段 Traceback」这样几行一组的重复）只留一份，注明重复了几次；
3. 太长的行截断（GPT-SoVITS 加载模型时会打印一行几千字的 _IncompatibleKeys，正常现象）。

另外 diagnose_gsv_api() 从记录里认出常见情况，写成中文结论（只写记录里真的有的东西）。
"""

import re
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

#: 每次启动推理服务前，程序在 gptsovits_api.log 里写的分隔线的开头
RUN_MARKER = "===== 声音分身"

_PORT = re.compile(r"(127\.0\.0\.1|localhost|\[::1\]):\d+")
_PID = re.compile(r"\[\d+\]")
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_EXC_LINE = re.compile(r"^([A-Za-z_][\w.]*(?:Error|Exception|Exit|Interrupt|Warning)|[A-Za-z_][\w.]*\.\w+Error)\b.*")


def read_text(path: Union[str, Path], max_bytes: int = 8_000_000) -> str:
    """读文本文件（UTF-8，读不出的字用 � 代替）；太大时只读最后 max_bytes 字节。读不了返回空字符串。"""
    try:
        p = Path(path)
        size = p.stat().st_size
        with open(p, "rb") as fh:
            if size > max_bytes:
                fh.seek(size - max_bytes)
            data = fh.read()
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def last_run(text: str, marker: str = RUN_MARKER) -> str:
    """只要最后一次启动（最后一行分隔线）之后的内容；没有分隔线就返回全部。"""
    idx = text.rfind("\n" + marker)
    if idx >= 0:
        return text[idx + 1:]
    if text.startswith(marker):
        return text
    return text


def _norm(line: str) -> str:
    line = _ANSI.sub("", line)
    line = _PORT.sub(r"\1:*", line)
    return _PID.sub("[*]", line).strip()


def _units(lines: Sequence[str]) -> List[List[str]]:
    """把行分成「单元」：一段完整的 Traceback（到最后的报错那一行为止）算一个单元，其它每行一个单元。"""
    units: List[List[str]] = []
    i, n = 0, len(lines)
    while i < n:
        if lines[i].startswith("Traceback (most recent call last)"):
            j = i + 1
            while j < n:
                ln = lines[j]
                if ln.startswith((" ", "\t")) or not ln.strip():
                    j += 1
                    continue
                if ln.startswith(("During handling of the above exception", "The above exception was the direct cause",
                                  "Traceback (most recent call last)")):
                    j += 1
                    continue
                j += 1  # 报错那一行（AttributeError: ……）
                break
            units.append(list(lines[i:j]))
            i = j
        else:
            units.append([lines[i]])
            i += 1
    return units


def _key(unit: List[str]) -> Tuple[str, ...]:
    return tuple(_norm(ln) for ln in unit)


_LIB_FRAME = re.compile(r"site-packages|dist-packages|[\\/]lib[\\/]python\d|[\\/]runtime[\\/]lib[\\/]|[\\/]Lib[\\/]", re.I)


def _shorten_traceback(unit: List[str]) -> List[str]:
    """Traceback 里 Python 库内部的调用（uvicorn、starlette……）一层一层都打印出来，几十行没用；
    只留程序自己的文件和最后一层，其余合成一行说明。"""
    if len(unit) < 2 or not unit[0].startswith("Traceback"):
        return unit
    frames: List[List[str]] = []
    others: List[Tuple[int, str]] = []
    cur: Optional[List[str]] = None
    for ln in unit[1:-1]:
        if ln.lstrip().startswith("File \""):
            cur = [ln]
            frames.append(cur)
        elif cur is not None and ln.startswith("    "):
            cur.append(ln)
        else:
            cur = None
            others.append((len(frames), ln))
    if others or len(frames) <= 3:  # 连环报错等复杂情况：原样保留
        return unit
    keep = [i for i, f in enumerate(frames) if not _LIB_FRAME.search(f[0])]
    if len(frames) - 1 not in keep:
        keep.append(len(frames) - 1)
    out = [unit[0]]
    skipped = 0
    for i, f in enumerate(frames):
        if i in keep:
            if skipped:
                out.append(f"  ……（{skipped} 层 Python 库内部的调用，省略）")
                skipped = 0
            out.extend(f)
        else:
            skipped += 1
    if skipped:
        out.append(f"  ……（{skipped} 层 Python 库内部的调用，省略）")
    out.append(unit[-1])
    return out


def condense(text: str, max_lines: int = 80, max_line_len: int = 300, head: int = 25) -> str:
    """整理记录：合并连续重复的内容、截断太长的行；还是太长时保留开头 head 行和最后的部分。"""
    lines = [_ANSI.sub("", ln.rstrip("\r")) for ln in text.splitlines()]
    units = [_shorten_traceback(u) for u in _units(lines)]
    keys = [_key(u) for u in units]
    out: List[str] = []
    i, n = 0, len(units)
    while i < n:
        best_k, best_p = 1, 1
        for p in (1, 2, 3, 4):
            if i + 2 * p > n:
                break
            k = 1
            while i + (k + 1) * p <= n and keys[i + k * p:i + (k + 1) * p] == keys[i:i + p]:
                k += 1
            if k > 1 and k * p > best_k * best_p:
                best_k, best_p = k, p
        for u in units[i:i + best_p]:
            out.extend(u)
        if best_k > 1:
            what = "上面这一行" if best_p == 1 and len(units[i]) == 1 else "上面这一段"
            out.append(f"……（{what}又重复了 {best_k - 1} 次，已省略）")
        i += best_k * best_p
    clipped = [(ln if len(ln) <= max_line_len else ln[:max_line_len] + f"……（这一行太长，后面省略 {len(ln) - max_line_len} 字）")
               for ln in out]
    if len(clipped) > max_lines:
        tail = max(0, max_lines - head - 1)
        clipped = clipped[:head] + [f"……（中间省略 {len(clipped) - head - tail} 行）"] + (clipped[-tail:] if tail else [])
    return "\n".join(clipped).strip("\n")


def tail_condensed(path: Union[str, Path], max_lines: int = 60, only_last_run: bool = True) -> str:
    text = read_text(path)
    if only_last_run:
        text = last_run(text)
    return condense(text, max_lines=max_lines)


def exception_counts(text: str) -> List[Tuple[str, int]]:
    """记录里每种报错（Traceback 最后一行）出现了几次，按第一次出现的顺序。"""
    counts: dict = {}
    for unit in _units(text.splitlines()):
        if len(unit) > 1 and unit[0].startswith("Traceback"):
            last = unit[-1].strip()
            if last:
                counts[last] = counts.get(last, 0) + 1
    return list(counts.items())


def diagnose_gsv_api(text: str) -> List[str]:
    """从 GPT-SoVITS 推理服务的记录（最后一次启动的部分）里认出常见情况，返回中文结论（可能为空）。"""
    notes: List[str] = []
    if not text.strip():
        return notes
    started = "Uvicorn running on" in text or "Application startup complete" in text
    if started:
        m = re.search(r"Uvicorn running on (\S+)", text)
        notes.append("引擎记录显示：合成引擎已经加载完模型并打开了" + (f"（{m.group(1)}）" if m else "") + "。")
    else:
        loading = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("Loading ")]
        if loading:
            last = loading[-1]
            what = last.split(" from ")[0] if " from " in last else last
            notes.append(f"引擎记录显示：合成引擎还没有打开，最后在做的是「{what[:80]}」（加载模型）。")
    n500 = len(re.findall(r'" 500 Internal Server Error', text))
    if n500:
        notes.append(f"引擎对程序的请求回答了 {n500} 次「内部错误」（HTTP 500）。")
    if re.search(r"CUDA out of memory|OutOfMemoryError", text):
        notes.append("引擎记录里有「显卡内存（显存）不够」（CUDA out of memory）。")
    if re.search(r"Address already in use|error while attempting to bind|10048", text):
        notes.append("引擎记录显示：端口被别的程序占用了（可能是上次没关掉的引擎）。")
    for exc, cnt in exception_counts(text)[:3]:
        notes.append(f"引擎报错：{exc[:200]}" + (f"（共 {cnt} 次）" if cnt > 1 else ""))
    return notes


def latest_files(folder: Union[str, Path], since: float, pattern: str = "*.log",
                 exclude: Sequence[str] = ()) -> List[Path]:
    """folder 里 since（时间戳）之后改过的文件，最近改的在前。"""
    try:
        files = [p for p in Path(folder).glob(pattern) if p.is_file() and p.name not in exclude]
    except OSError:
        return []
    out = []
    for p in files:
        try:
            if p.stat().st_mtime >= since:
                out.append(p)
        except OSError:
            continue
    out.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    return out


def first_line(text: Optional[str]) -> str:
    for ln in (text or "").splitlines():
        if ln.strip():
            return ln.strip()
    return ""
