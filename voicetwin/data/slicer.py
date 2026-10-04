"""按停顿切分长录音。

思路：先找出所有足够长的静音段，得到"语音区间"，再把相邻区间合并成 3~10 秒左右的训练片段；
过长的区间在能量最低处强制切开。同时记录每个片段前后的真实停顿长度，用于分析你的说话节奏。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from voicetwin.utils.audio import auto_silence_threshold, frame_rms_db


@dataclass
class Segment:
    start: int                      # 样本位置（含首尾保留静音）
    end: int
    speech_start: int               # 实际语音起止（不含保留静音）
    speech_end: int
    gap_before: Optional[float]     # 片段前的静音长度（秒），None 表示在文件开头
    gap_after: Optional[float]      # 片段后的静音长度（秒），None 表示在文件结尾
    forced_cuts: int = 0            # 在没有停顿处强制切开的次数
    inner_gaps: List[float] = field(default_factory=list)  # 片段内部被合并掉的停顿

    def duration(self, sr: int) -> float:
        return (self.end - self.start) / sr


def _silent_runs_frames(silent: np.ndarray, min_frames: int) -> List[Tuple[int, int]]:
    runs = []
    n = len(silent)
    i = 0
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            if j - i >= min_frames or i == 0 or j == n:
                runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def _split_long(db: np.ndarray, s: int, e: int, max_frames: int, min_frames: int) -> List[Tuple[int, int]]:
    """在 [s, e) 内能量最低处递归切分，直到每段不超过 max_frames。"""
    if e - s <= max_frames:
        return [(s, e)]
    lo, hi = s + min_frames, e - min_frames
    if hi <= lo:
        mid = (s + e) // 2
    else:
        window = db[lo:hi]
        # 平滑一下，避免切在辅音的瞬时低能量点上
        k = 5
        if len(window) > k:
            window = np.convolve(window, np.ones(k) / k, mode="same")
        # 偏向中间位置：加一个很小的抛物线惩罚
        idx = np.arange(len(window))
        center = (len(window) - 1) / 2.0
        penalty = ((idx - center) / max(center, 1.0)) ** 2 * 3.0
        mid = lo + int(np.argmin(window + penalty))
    return _split_long(db, s, mid, max_frames, min_frames) + _split_long(db, mid, e, max_frames, min_frames)


def find_segments(
    wav: np.ndarray,
    sr: int,
    threshold_db: Optional[float] = None,
    min_interval_ms: float = 300.0,
    hop_ms: float = 10.0,
    max_sil_kept_ms: float = 400.0,
    min_duration: float = 2.0,
    max_duration: float = 12.0,
    target_min: float = 3.0,
    target_max: float = 9.0,
    join_gap: float = 0.5,
    max_merge_gap: float = 1.2,
) -> List[Segment]:
    """max_merge_gap：比这更长的停顿两边永远不合并成一段（「好。」说完写板书 7 秒再说下一句：以前合成一段 11 秒、
    中间 7 秒底噪的训练片段，模型会学到句子中间长时间停顿）。太短的那段自己成一段（不到 min_duration 的以后算「太短」）。"""
    if wav.size == 0:
        return []
    if threshold_db is None:
        threshold_db = auto_silence_threshold(wav, sr)
    db = frame_rms_db(wav, sr, hop_ms=hop_ms)
    n = len(db)
    hop = sr * hop_ms / 1000.0
    hop_s = hop_ms / 1000.0
    silent = db < threshold_db
    min_run = max(1, int(round(min_interval_ms / hop_ms)))
    runs = [r for r in _silent_runs_frames(silent, min_run) if r[1] - r[0] >= min_run or r[0] == 0 or r[1] == n]

    # 语音区间：两个静音段之间
    regions: List[Tuple[int, int, Optional[float], Optional[float]]] = []
    cursor = 0
    prev_gap: Optional[float] = None
    for rs, re_ in runs:
        if rs > cursor:
            gap_after = (re_ - rs) * hop_s if re_ < n else None
            regions.append((cursor, rs, prev_gap, gap_after))
        # 文件开头的静音不算停顿
        prev_gap = None if rs == 0 else (re_ - rs) * hop_s
        cursor = re_
    if cursor < n:
        regions.append((cursor, n, prev_gap, None))
    # 丢掉极短的噪声区间（< 0.25 秒）
    min_region = int(0.25 / hop_s)
    regions = [r for r in regions if r[1] - r[0] >= min_region]
    if not regions:
        return []

    # 合并相邻区间
    groups: List[List[Tuple[int, int, Optional[float], Optional[float]]]] = []
    cur = [regions[0]]
    for reg in regions[1:]:
        cur_start = cur[0][0]
        cur_dur = (cur[-1][1] - cur_start) * hop_s
        cand_dur = (reg[1] - cur_start) * hop_s
        gap = reg[2] if reg[2] is not None else 0.0
        if (cur_dur < target_min and cand_dur <= max_duration and gap <= max_merge_gap) or \
                (gap <= join_gap and cand_dur <= target_max):
            cur.append(reg)
        else:
            groups.append(cur)
            cur = [reg]
    groups.append(cur)
    # 太短的尾巴并入前一组（只要合并后不超长、中间的停顿不太长）
    merged: List[List[Tuple[int, int, Optional[float], Optional[float]]]] = []
    for grp in groups:
        dur = (grp[-1][1] - grp[0][0]) * hop_s
        gap_before = grp[0][2] if grp[0][2] is not None else 0.0
        if merged and dur < target_min and gap_before <= max_merge_gap \
                and (grp[-1][1] - merged[-1][0][0]) * hop_s <= max_duration:
            merged[-1].extend(grp)
        else:
            merged.append(grp)
    groups = merged

    max_frames = int(max_duration / hop_s)
    min_frames = int(min_duration / hop_s)
    max_kept = max_sil_kept_ms / 1000.0
    segments: List[Segment] = []
    for grp in groups:
        s, e = grp[0][0], grp[-1][1]
        gap_before, gap_after = grp[0][2], grp[-1][3]
        inner = [r[2] for r in grp[1:] if r[2] is not None]
        pieces = _split_long(db, s, e, max_frames, min_frames)
        for k, (ps, pe) in enumerate(pieces):
            gb = gap_before if k == 0 else 0.0
            ga = gap_after if k == len(pieces) - 1 else 0.0
            pad_l = min((gb or 0.0) / 2.0, max_kept) if gb is not None else min(ps * hop_s, max_kept)
            pad_r = min((ga or 0.0) / 2.0, max_kept) if ga is not None else min((n - pe) * hop_s, max_kept)
            start = max(0, int(ps * hop - pad_l * sr))
            end = min(len(wav), int(pe * hop + pad_r * sr))
            segments.append(Segment(
                start=start,
                end=end,
                speech_start=int(ps * hop),
                speech_end=min(len(wav), int(pe * hop)),
                gap_before=gb,
                gap_after=ga,
                forced_cuts=len(pieces) - 1,
                inner_gaps=inner if len(pieces) == 1 else [],
            ))
    return segments
