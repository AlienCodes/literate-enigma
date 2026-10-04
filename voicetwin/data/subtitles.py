"""字幕（.srt / .vtt）读写，以及按字幕切分录音。

如果你的讲课视频本来就有字幕文件，把它和视频放在一起、同名即可（例如 第1课.mp4 + 第1课.srt），
程序会直接用字幕的文字和时间轴切片，比语音识别更准确。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

from voicetwin.utils.audio import frame_rms_db
from voicetwin.utils.textutil import clean_transcript, count_cjk, decode_text_bytes, ends_sentence

TIME_RE = re.compile(
    r"(?:(\d+):)?(\d{1,2}):(\d{1,2})[,.](\d{1,3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{1,2})[,.](\d{1,3})"
)
TAG_RE = re.compile(r"<[^>]+>|\{\\[^}]*\}")


@dataclass
class Cue:
    start: float
    end: float
    text: str


def _to_sec(h: Optional[str], m: str, s: str, ms: str) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000.0


def parse_subtitles(path: Path) -> List[Cue]:
    """读 .srt / .vtt。记事本另存为 ANSI（GBK）、「Unicode」（UTF-16）的字幕也能读（以前只按 UTF-8 读：
    GBK 的中文全变成乱码，UTF-16 的一条都读不出来）。"""
    return parse_subtitle_text(decode_text_bytes(Path(path).read_bytes()))


def parse_subtitle_text(raw: str) -> List[Cue]:
    cues: List[Cue] = []
    blocks = re.split(r"\n\s*\n", raw.replace("\r\n", "\n").replace("\r", "\n"))
    for block in blocks:
        lines = [ln for ln in block.strip().split("\n") if ln.strip()]
        for i, line in enumerate(lines):
            m = TIME_RE.search(line)
            if not m:
                continue
            g = m.groups()
            start = _to_sec(g[0], g[1], g[2], g[3])
            end = _to_sec(g[4], g[5], g[6], g[7])
            text = " ".join(TAG_RE.sub("", ln).strip() for ln in lines[i + 1:])
            text = clean_transcript(text)
            if text and end > start:
                cues.append(Cue(start, end, text))
            break
    cues.sort(key=lambda c: c.start)
    return cues


def _fmt_time(t: float) -> str:
    # 先换成整毫秒再拆：59.9996 秒是 00:01:00,000（以前进位只进到秒，写出 00:00:60,000，剪映等软件不认）
    total = int(round(max(0.0, float(t)) * 1000))
    h, rest = divmod(total, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues: Sequence[Cue], path: Path) -> Path:
    lines = []
    for i, c in enumerate(cues, 1):
        lines += [str(i), f"{_fmt_time(c.start)} --> {_fmt_time(c.end)}", c.text, ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return Path(path)


def join_texts(texts: Sequence[str]) -> str:
    out = ""
    for t in texts:
        if not out:
            out = t
        elif count_cjk(out[-1:]) or count_cjk(t[:1]) or out[-1] in "，。！？；：":
            out += t
        else:
            out += " " + t
    return out


@dataclass
class CueSegment:
    start: float
    end: float
    text: str
    gap_before: Optional[float]
    gap_after: Optional[float]


def group_cues(cues: Sequence[Cue], min_duration: float = 3.0, max_duration: float = 12.0,
               join_gap: float = 0.6) -> List[CueSegment]:
    """把相邻字幕条合并成适合训练的长度（尽量在句末切开）。"""
    groups: List[List[Cue]] = []
    cur: List[Cue] = []
    for cue in cues:
        if not cur:
            cur = [cue]
            continue
        gap = cue.start - cur[-1].end
        cand = cue.end - cur[0].start
        cur_dur = cur[-1].end - cur[0].start
        sentence_done = ends_sentence(cur[-1].text)
        if cand <= max_duration and gap <= join_gap and (cur_dur < min_duration or not sentence_done):
            cur.append(cue)
        else:
            groups.append(cur)
            cur = [cue]
    if cur:
        groups.append(cur)
    out: List[CueSegment] = []
    for i, g in enumerate(groups):
        prev_end = groups[i - 1][-1].end if i > 0 else None
        next_start = groups[i + 1][0].start if i + 1 < len(groups) else None
        out.append(CueSegment(
            start=g[0].start,
            end=g[-1].end,
            text=join_texts([c.text for c in g]),
            gap_before=max(0.0, g[0].start - prev_end) if prev_end is not None else None,
            gap_after=max(0.0, next_start - g[-1].end) if next_start is not None else None,
        ))
    return out


def refine_boundaries(wav: np.ndarray, sr: int, start: float, end: float, search: float = 0.3,
                      pad: float = 0.12) -> "tuple[int, int]":
    """字幕时间轴通常有 0.1~0.3 秒误差：在边界附近找能量最低点，避免把字切掉一半。"""
    hop_ms = 10.0
    db = frame_rms_db(wav, sr, hop_ms=hop_ms)
    n = len(db)
    to_f = lambda t: int(np.clip(round(t * 1000 / hop_ms), 0, max(n - 1, 0)))  # noqa: E731
    s_lo, s_hi = to_f(start - search), to_f(start + 0.05)
    e_lo, e_hi = to_f(end - 0.05), to_f(end + search)
    s_f = s_lo + int(np.argmin(db[s_lo:s_hi + 1])) if s_hi > s_lo else to_f(start)
    e_f = e_lo + int(np.argmin(db[e_lo:e_hi + 1])) if e_hi > e_lo else to_f(end)
    hop = sr * hop_ms / 1000.0
    s_samp = max(0, int(s_f * hop - pad * sr * 0.5))
    e_samp = min(len(wav), int(e_f * hop + pad * sr * 0.5))
    if e_samp <= s_samp:
        s_samp, e_samp = int(start * sr), int(end * sr)
    return s_samp, e_samp


def find_sidecar_subtitle(media: Path) -> Optional[Path]:
    for ext in (".srt", ".vtt", ".SRT", ".VTT"):
        cand = media.with_suffix(ext)
        if cand.exists():
            return cand
    # 常见命名：视频名.zh.srt / 视频名.chs.srt / 视频名.en.srt
    for cand in sorted(media.parent.glob(media.stem + ".*.srt")):
        return cand
    return None
