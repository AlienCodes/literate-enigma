"""「一模一样」档：实测你本人的说话习惯，存成 twin_profile.json（profile.json 各档都在用，这里另外存一份，不动它）。

只用处理器（CPU）。每段录音量出来的东西按文件（大小 + 修改时间）缓存在 cache/ 里：改文字只要重新对齐标点，
不用重新量声音；素材没变时什么都不做（signature 一样）。

量什么：
- 停顿：逗号、顿号、冒号分号、句号处各停多久，没有标点的停顿算「犹豫」。在整段原始录音 raw/<视频>.wav 上重新量
  （切片时记下的「片段后面的停顿」只在切开的地方有，切开的地方又专挑长的停顿，统计起来系统性地偏长，
  见 research/一模一样/scripts/gap_bias_sim.py）；标点和停顿按位置对齐（动态规划）。
  原始录音找不到时退回只用切好的片段（source = "clips"）。
- 音调：整句往下走多快、句末升还是降、起伏多大（陈述句 / 问句 × 英文多少分组）。
- 语速模型：一句话（汉字、英文音节、数字、句中标点各多少）大约要说多久。
- 音量：同一个视频里句子之间响度差多少；句首起音、句尾收音多长。
- 前后两句之间音调、语速变化多少（音色的变化由参考录音库 data/references.build_reference_bank 填）。
- 频谱（LTAS，只记录、只给打分校准参考，不拿来改声音——永久规定：不加任何处理）。

每个统计都带 n（用了多少个数）；少于 8 个时值是 null：不瞎猜，用的时候退回原来的做法。
"""

from __future__ import annotations

import bisect
import json
import math
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from voicetwin.project import Project
from voicetwin.style.prosody import f0_frames
from voicetwin.utils.audio import (EPS, frame_rms_db, load_audio, mask_runs, resample, silence_threshold_from_db,
                                   silent_runs, speech_activity, trim_silence)
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import (DIGIT_RE, count_cjk, en_syllables, en_words, ends_sentence, sentence_kind,
                                      short_hash, syllable_count)

log = get_logger("twin_profile")

try:  # 停止按钮
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover
    def _check_cancel() -> None:
        return None

TWIN_PROFILE_VERSION = 1
TWIN_PROFILE_FILE = "twin_profile.json"
CLIP_CACHE_FILE = "twin_clips.json"        # 在 cache/ 里：每段录音量出来的声音特征
SOURCE_CACHE_FILE = "twin_sources.json"    # 在 cache/ 里：每个原始录音里的停顿位置
MIN_N = 8                                  # 少于这么多个数：不算统计值（null）
HOP_MS, WIN_MS = 10.0, 40.0                # 和切片量停顿用的一样：10 ms 一帧、40 ms 窗
MIN_GAP_MS = 120.0                         # 至少 120 ms（12 帧）的静音才算停顿
SKIP_COST, MATCH_MAX = 0.08, 0.12          # 对齐：跳过一个标点 / 一个停顿各算 0.08；位置差 ≤ 0.12 才能对上
PAUSE_MIN, PAUSE_MAX = 0.12, 4.0           # 停顿只统计 0.12~4 秒（更长的多半是在写板书、放视频）
DELTA_MAX_GAP = 2.0                        # 前后两句：同一个视频里、中间停顿 < 2 秒才算连着说的
QUANTS = tuple(range(5, 100, 5)) + (97,)   # 分位数 p05 … p95，再加 p97
PAUSE_CLASSES = ("comma", "enum", "colon_semi", "sentence")
MARK_CLASS = {"，": "comma", ",": "comma", "、": "enum", "：": "colon_semi", "；": "colon_semi", ":": "colon_semi",
              ";": "colon_semi", "。": "sentence", "！": "sentence", "？": "sentence", "!": "sentence", "?": "sentence",
              "…": "sentence", ".": "sentence"}
_STRENGTH = {"enum": 0, "comma": 1, "colon_semi": 2, "sentence": 3}
_CLOSERS = "”\"'’）)」』】》"
EN_BINS = (("lt10", 0.0, 0.10), ("10to30", 0.10, 0.30), ("ge30", 0.30, 1.0 + 1e-9))
KINDS = ("statement", "question")
PROSODY_FEATURES = ("f0_med_st", "f0_range_st", "decl_slope", "final_slope", "energy_range_db")
DURATION_TERMS = ("const", "n_cjk", "en_syllables", "n_digits", "n_clause_punct")
LTAS_SR = 32000
LTAS_CENTERS = 1000.0 * 2.0 ** (np.arange(-10, 12) / 3.0)   # 22 个 1/3 倍频程：约 100 Hz … 12.7 kHz
EDGE_HOP_MS, EDGE_WIN_MS = 2.5, 10.0       # 句首起音 / 句尾收音用更细的帧

#: 同一个程序里两个保存同时更新时一个一个来（第二个看到 signature 一样就直接返回）
_LOCK = threading.RLock()

ProgressFn = Callable[[float, str], None]


# ============================================================================ 小工具
def _r(x: Any, nd: int = 4) -> Optional[float]:
    """保留 nd 位小数；NaN / 无穷 / 不是数字 → None（写进 JSON 是 null，不会写出 NaN）。"""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return round(v, nd)


def _finite(values: Iterable[Any]) -> np.ndarray:
    arr = np.asarray([v for v in values if v is not None], dtype=np.float64)
    return arr[np.isfinite(arr)] if arr.size else arr


def _quantiles(values: Iterable[Any], nd: int = 4) -> Dict[str, Any]:
    """{"n": 个数, "q": {"p05": …, "p95": …, "p97": …}}；少于 8 个时 q 是 null。"""
    arr = _finite(values)
    out: Dict[str, Any] = {"n": int(arr.size), "q": None, "median": None}
    if arr.size >= MIN_N:
        out["q"] = {f"p{q:02d}": _r(np.percentile(arr, q), nd) for q in QUANTS}
        out["median"] = _r(np.median(arr), nd)
    return out


def _mean_sd(values: Iterable[Any], nd: int = 4) -> Dict[str, Any]:
    arr = _finite(values)
    if arr.size < MIN_N:
        return {"mean": None, "sd": None, "n": int(arr.size)}
    return {"mean": _r(arr.mean(), nd), "sd": _r(arr.std(ddof=1), nd), "n": int(arr.size)}


def _file_key(path: Path) -> Optional[str]:
    try:
        st = Path(path).stat()
    except OSError:
        return None
    return f"{st.st_size}:{st.st_mtime_ns}"


def _clean(obj: Any) -> Any:
    """写 JSON 前：numpy 数字换成普通数字，NaN / 无穷换成 null。"""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return _r(obj, 6)
    return obj


def dumps(obj: Any) -> str:
    """固定格式的 JSON（键排序、没有时间戳）：素材一样，写出来的文件一个字节都不差。"""
    return json.dumps(_clean(obj), ensure_ascii=False, indent=1, sort_keys=True, allow_nan=False)


def _read_cache(path: Path) -> Dict[str, Any]:
    """缓存读不了（写到一半断电、手动改坏了）：当作没有，重新量（只是慢一点）。"""
    from voicetwin.utils import atomic

    try:
        data = json.loads(atomic.read_text(path))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        log.debug(f"缓存 {path.name} 读不了（{exc}），重新量")
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, obj: Any) -> None:
    from voicetwin.utils import atomic

    path.parent.mkdir(parents=True, exist_ok=True)
    atomic.write_text(path, dumps(obj))


# ============================================================================ 文字：标点和音节
def _mark_class(text: str, i: int) -> Optional[str]:
    """text[i] 是不是一个停顿标点、是哪一类。数字里的「3.14」「1,000」「10:30」、缩写里的「e.g.」不算。"""
    ch = text[i]
    cls = MARK_CLASS.get(ch)
    if cls is None:
        return None
    if ch in ".,:":
        prev = text[i - 1] if i > 0 else ""
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if prev.isdigit() and nxt.isdigit():
            return None
        if ch == "." and nxt.isascii() and nxt.isalpha():
            return None
        if ch == "." and prev.isascii() and prev.isalpha() and i >= 2 and text[i - 2] == ".":  # e.g. / i.e. 的最后一个点
            return None
    return cls


def text_marks(text: str) -> List[Tuple[float, str]]:
    """句子里面的标点（后面还有字的）：[(位置 = 前面的音节数 / 全部音节数, 类别), ...]。
    连在一起的几个标点（「？！」「。”」）算一个，取最强的一类。句末的标点不在这里（它对应片段后面的停顿）。"""
    text = str(text or "")
    total = syllable_count(text)
    if total <= 0:
        return []
    out: List[Tuple[float, str]] = []
    i, n = 0, len(text)
    while i < n:
        cls = _mark_class(text, i)
        if cls is None:
            i += 1
            continue
        best, j = cls, i + 1
        while j < n and (text[j] in _CLOSERS or text[j].isspace() or _mark_class(text, j)):
            c2 = _mark_class(text, j)
            if c2 and _STRENGTH[c2] > _STRENGTH[best]:
                best = c2
            j += 1
        before = syllable_count(text[:i])
        if 0 < before < total:
            out.append((before / total, best))
        i = j
    return out


def final_mark(text: str) -> Optional[str]:
    """句末标点的类别（没有标点时 None）。"""
    t = str(text or "").rstrip()
    while t and t[-1] in _CLOSERS:
        t = t[:-1].rstrip()
    if not t:
        return None
    return _mark_class(t, len(t) - 1)


def latin_syllables(text: str) -> int:
    return sum(en_syllables(w) for w in en_words(str(text or "")))


def en_share(text: str) -> float:
    """英文音节占全部音节的比例（0~1）。"""
    total = syllable_count(str(text or ""))
    return latin_syllables(text) / total if total > 0 else 0.0


def duration_features(text: str) -> List[float]:
    """语速模型的四个数：汉字个数、英文音节数、数字个数、句中标点个数。"""
    text = str(text or "")
    return [float(count_cjk(text)), float(latin_syllables(text)), float(len(DIGIT_RE.findall(text))),
            float(len(text_marks(text)))]


def _en_bin(share: float) -> str:
    for name, lo, hi in EN_BINS:
        if lo <= share < hi:
            return name
    return EN_BINS[-1][0]


def _kind2(text: str) -> str:
    return "question" if sentence_kind(str(text or "")) == "question" else "statement"


# ============================================================================ 对齐标点和停顿
def align_pauses(text: str, clip_pauses: Sequence[Tuple[float, float]]
                 ) -> Tuple[List[Tuple[str, float]], List[float], Dict[str, int]]:
    """把片段里量到的停顿和文字里的标点按位置对上（Needleman–Wunsch 动态规划）。

    clip_pauses：[(位置 0~1, 停顿秒数), ...]，位置 = (停顿中点 − 开口) / (开口到收音的长度)。
    标点的位置 = 前面的音节数 / 全部音节数。跳过一个标点或一个停顿各算 0.08，位置差 ≤ 0.12 才能对上
    （对上的代价 = 位置差，所以对得上时一定比两边都跳过便宜）。

    返回 (对上的 [(标点类别, 秒数)], 没有标点的停顿（犹豫）秒数, 每类标点各有几个)。"""
    marks = text_marks(text)
    pauses = sorted((float(f), float(d)) for f, d in clip_pauses
                    if f is not None and d is not None and math.isfinite(float(f)) and math.isfinite(float(d)))
    counts = {c: 0 for c in PAUSE_CLASSES}
    for _, cls in marks:
        counts[cls] += 1
    m, k = len(marks), len(pauses)
    cost = np.zeros((m + 1, k + 1))
    back = np.zeros((m + 1, k + 1), dtype=np.int8)  # 0 = 对上，1 = 跳过标点，2 = 跳过停顿
    cost[1:, 0] = np.arange(1, m + 1) * SKIP_COST
    back[1:, 0] = 1
    cost[0, 1:] = np.arange(1, k + 1) * SKIP_COST
    back[0, 1:] = 2
    for i in range(1, m + 1):
        for j in range(1, k + 1):
            best, how = cost[i - 1, j] + SKIP_COST, 1
            alt = cost[i, j - 1] + SKIP_COST
            if alt < best:
                best, how = alt, 2
            diff = abs(marks[i - 1][0] - pauses[j - 1][0])
            if diff <= MATCH_MAX and cost[i - 1, j - 1] + diff <= best:
                best, how = cost[i - 1, j - 1] + diff, 0
            cost[i, j], back[i, j] = best, how
    pairs: List[Tuple[str, float]] = []
    hesitations: List[float] = []
    i, j = m, k
    while i > 0 or j > 0:
        how = back[i, j]
        if how == 0:
            pairs.append((marks[i - 1][1], pauses[j - 1][1]))
            i, j = i - 1, j - 1
        elif how == 1:
            i -= 1
        else:
            hesitations.append(pauses[j - 1][1])
            j -= 1
    pairs.reverse()
    hesitations.reverse()
    return pairs, hesitations, counts


# ============================================================================ 原始录音里的停顿
def source_gaps(wav: np.ndarray, sr: int) -> List[Tuple[float, float]]:
    """整段录音里的停顿 [(开始秒, 结束秒), ...]：10 ms 一帧、40 ms 窗、自动静音阈值、至少 120 ms（12 帧）。
    文件开头和结尾的静音不算停顿。"""
    if wav is None or len(wav) == 0 or not sr:
        return []
    wav = np.nan_to_num(np.asarray(wav, dtype=np.float32))
    total = len(wav) / sr
    return [(s, e) for s, e in silent_runs(wav, sr, hop_ms=HOP_MS, min_run_ms=MIN_GAP_MS) if s > 0 and e < total]


def _gaps_from_db(db: np.ndarray, total: float) -> List[Tuple[float, float]]:
    thr = silence_threshold_from_db(db)
    hop_s = HOP_MS / 1000.0
    n = len(db)
    min_frames = int(round(MIN_GAP_MS / HOP_MS))
    return [(i * hop_s, min(j * hop_s, total)) for i, j in mask_runs(db < thr, min_frames) if i > 0 and j < n]


def source_gaps_file(path: Path) -> Tuple[List[Tuple[float, float]], float]:
    """source_gaps 的读文件版：分块读（一次 60 秒），一小时的录音也不用整个读进内存。结果和整个读进来算的一样
    （每 10 ms 的能量先加起来，40 ms 窗 = 前后 4 个 10 ms 的和）。返回 (停顿, 总秒数)。"""
    import soundfile as sf

    info = sf.info(str(path))
    sr, n = int(info.samplerate), int(info.frames)
    if n <= 0 or sr <= 0:
        return [], 0.0
    hop = max(1, int(round(sr * HOP_MS / 1000.0)))
    win = max(hop, int(round(sr * WIN_MS / 1000.0)))
    if win != 4 * hop:  # 不常见的采样率（比如 22050）：整个读进来算
        wav, sr2 = load_audio(path)
        return source_gaps(wav, sr2), len(wav) / sr2
    sums: List[np.ndarray] = []
    for block in sf.blocks(str(path), blocksize=hop * 6000, dtype="float32", always_2d=True):
        x = block.mean(axis=1) if block.shape[1] > 1 else block[:, 0]
        x = np.nan_to_num(x.astype(np.float64))
        if len(x) % hop:
            x = np.concatenate([x, np.zeros(hop - len(x) % hop)])
        sums.append((x * x).reshape(-1, hop).sum(axis=1))
    s = np.concatenate(sums) if sums else np.zeros(0)
    n_frames = 1 + (n - 1) // hop
    s = s[:n_frames]
    padded = np.concatenate([[0.0, 0.0], s, [0.0]])
    energy = np.convolve(padded, np.ones(4), mode="valid")[:n_frames] / win
    db = (10.0 * np.log10(energy + EPS)).astype(np.float32)
    return _gaps_from_db(db, n / sr), n / sr


# ============================================================================ 每段录音的声音特征
def _edges(wav: np.ndarray, sr: int) -> Tuple[Optional[float], Optional[float], Optional[bool]]:
    """句首起音、句尾收音各多少毫秒（从底噪到比最响处低 30 dB 之间），以及开口前有没有像吸气的声音（只记录）。"""
    db = frame_rms_db(wav, sr, hop_ms=EDGE_HOP_MS, win_ms=EDGE_WIN_MS)
    db = db[np.isfinite(db)] if db.size else db
    if db.size < 20:
        return None, None, None
    peak = float(np.percentile(db, 99))
    hi = peak - 30.0
    floor = max(float(np.percentile(db, 3)) + 6.0, peak - 60.0)
    if floor >= hi - 3.0:  # 底噪太高：量不出来
        return None, None, None
    above = np.flatnonzero(db >= hi)
    if above.size == 0:
        return None, None, None
    a, b = int(above[0]), int(above[-1])
    pre = np.flatnonzero(db[:a] <= floor)
    post = np.flatnonzero(db[b + 1:] <= floor)
    onset = (a - int(pre[-1])) * EDGE_HOP_MS if pre.size else None
    offset = (int(post[0]) + 1) * EDGE_HOP_MS if post.size else None
    breath = None
    if pre.size:
        lo = max(0, int(pre[-1]) - int(600 / EDGE_HOP_MS))
        seg = db[lo:int(pre[-1]) + 1]
        breath = bool(mask_runs((seg > floor) & (seg < hi), int(100 / EDGE_HOP_MS)))
    return onset, offset, breath


def _ltas22(wav: np.ndarray, sr: int) -> Optional[List[Optional[float]]]:
    """长时平均频谱：22 个 1/3 倍频程（约 100 Hz … 12.7 kHz），先换成 32 kHz；只看有声音的帧；减去平均值
    （只比形状，不比音量）。原始采样率不够高的频带是 null。"""
    from scipy import signal

    x = resample(wav, sr, LTAS_SR)
    if len(x) < 2048:
        return None
    fr, _, z = signal.stft(x, LTAS_SR, nperseg=1024, noverlap=1024 - 320, boundary=None)
    p = np.abs(z) ** 2
    e = p.sum(axis=0)
    if e.size == 0 or not np.isfinite(e).all():
        return None
    keep = e > np.percentile(e, 30)
    if not keep.any():
        return None
    p = p[:, keep].mean(axis=1)
    out = []
    for c in LTAS_CENTERS:
        lo, hi = c / 2 ** (1 / 6), c * 2 ** (1 / 6)
        m = (fr >= lo) & (fr < hi)
        if hi > 0.45 * sr or not m.any():
            out.append(np.nan)
        else:
            out.append(10.0 * np.log10(p[m].mean() + 1e-12))
    arr = np.asarray(out)
    if not np.isfinite(arr).any():
        return None
    arr = arr - np.nanmean(arr)
    return [_r(v, 2) for v in arr]


def _slope(t: np.ndarray, y: np.ndarray) -> Optional[float]:
    if t.size < 5 or float(np.ptp(t)) <= 0:
        return None
    try:
        return float(np.polyfit(t, y, 1)[0])
    except (ValueError, np.linalg.LinAlgError):
        return None


def acoustic_features(wav: np.ndarray, sr: int) -> Dict[str, Any]:
    """一段录音里只和声音有关的东西（和文字无关，按文件缓存）。量不出来的是 None。"""
    wav = np.nan_to_num(np.asarray(wav, dtype=np.float32))
    dur = len(wav) / sr if sr else 0.0
    out: Dict[str, Any] = {"dur": _r(dur, 4), "voiced": 0.0, "vs": None, "ve": None, "gaps": [], "level_db": None,
                           "energy_range_db": None, "f0_med_hz": None, "f0_range_st": None, "decl_slope": None,
                           "final_slope": None, "n_f0": 0, "onset_ms": None, "offset_ms": None, "breath": None,
                           "ltas": None, "trim": None}
    if len(wav) < int(0.1 * sr):
        return out
    hop_s = HOP_MS / 1000.0
    db = frame_rms_db(wav, sr, hop_ms=HOP_MS, win_ms=WIN_MS)
    thr = silence_threshold_from_db(db)
    speech = db >= thr
    if not speech.any():
        return out
    first, last = np.flatnonzero(speech)[[0, -1]]
    out["vs"] = _r(first * hop_s, 3)
    out["ve"] = _r(min((last + 1) * hop_s, dur), 3)
    out["gaps"] = [[_r(i * hop_s, 3), _r(min(j * hop_s, dur), 3)]
                   for i, j in mask_runs(~speech, int(round(MIN_GAP_MS / HOP_MS))) if i > first and j <= last]
    voiced, _ = speech_activity(wav, sr, threshold_db=thr)
    out["voiced"] = _r(voiced, 3)
    sdb = db[speech].astype(np.float64)
    out["level_db"] = _r(10.0 * np.log10(np.mean(10.0 ** (sdb / 10.0)) + EPS), 2)
    out["energy_range_db"] = _r(np.percentile(sdb, 90) - np.percentile(sdb, 10), 2)
    t, f0 = f0_frames(wav, sr)
    ok = np.isfinite(f0) & (f0 > 0) & np.isfinite(t)
    t, f0 = t[ok].astype(np.float64), f0[ok].astype(np.float64)
    out["n_f0"] = int(f0.size)
    if f0.size >= 10:
        med = float(np.median(f0))
        st = 12.0 * np.log2(f0 / med)
        out["f0_med_hz"] = _r(med, 2)
        out["f0_range_st"] = _r(np.percentile(st, 90) - np.percentile(st, 10), 3)
        if float(np.ptp(t)) >= 0.5:
            out["decl_slope"] = _r(_slope(t, st), 3)
        tail = t >= t[-1] - 0.3
        if int(tail.sum()) >= 5 and float(np.ptp(t[tail])) >= 0.1:
            out["final_slope"] = _r(_slope(t[tail], st[tail]), 3)
    onset, offset, breath = _edges(wav, sr)
    out["onset_ms"], out["offset_ms"], out["breath"] = _r(onset, 1), _r(offset, 1), breath
    out["ltas"] = _ltas22(wav, sr)
    _, a, b = trim_silence(wav, sr, pad_ms=80)
    out["trim"] = [int(a), int(b), int(sr)] if b > a else None
    return out


def clip_features(wav: np.ndarray, sr: int, text: str = "", f0_ref_hz: Optional[float] = None) -> Dict[str, Any]:
    """一段录音的特征：声音的（acoustic_features）+ 文字的（音节、英文比例、句型、语速）。
    f0_med_st：这一段的音高中位数比你整体的中位数（f0_ref_hz）高几个半音；没给 f0_ref_hz 时是 None。"""
    out = acoustic_features(wav, sr)
    return _with_text(out, text, f0_ref_hz)


def _with_text(feat: Dict[str, Any], text: str, f0_ref_hz: Optional[float]) -> Dict[str, Any]:
    out = dict(feat)
    syl = syllable_count(str(text or ""))
    out["syllables"] = syl
    out["en_ratio"] = _r(en_share(text), 4)
    out["kind"] = _kind2(text)
    voiced = out.get("voiced") or 0.0
    out["rate"] = _r(syl / voiced, 4) if syl > 0 and voiced >= 0.3 else None
    med = out.get("f0_med_hz")
    out["f0_med_st"] = _r(12.0 * math.log2(med / f0_ref_hz), 3) if med and f0_ref_hz else None
    return out


# ============================================================================ 量所有片段（带缓存）
class _OverBudget(Exception):
    """要新量的录音太多（这次先不量，留到素材准备 / 生成「一模一样」时再量）。"""


def _sources_of(records: Iterable[Dict[str, Any]]) -> List[str]:
    return sorted({str(r.get("source") or "") for r in records if r.get("source")})


def _raw_path(project: Project, sid: str) -> Path:
    return project.raw_dir / f"{sid}.wav"


def collect_clips(project: Project, records: Sequence[Dict[str, Any]], max_new_clips: Optional[int] = None,
                  max_new_source_mb: Optional[float] = None, progress: Optional[ProgressFn] = None
                  ) -> Dict[str, Dict[str, Any]]:
    """量 records 里每一段（声音特征按文件缓存），再放回整段原始录音里找它前后、里面的停顿。

    返回 {片段 id: {"feat": 声音特征, "mode": "raw" | "clips", "vs"/"ve": 开口和收音（秒，片段里的时间）,
    "inner": [(开始, 结束)] 片段里面的停顿, "gap_before"/"gap_after": 片段前后的停顿秒数（只有 raw 才有）}}。
    读不了的片段跳过。max_new_*：要新量的太多时抛 _OverBudget（什么都不量）。"""
    with _LOCK:  # 缓存文件同一时间只有一个在改（不然后写的会把先写的新结果冲掉）
        return _collect_clips(project, records, max_new_clips, max_new_source_mb, progress)


def _collect_clips(project: Project, records: Sequence[Dict[str, Any]], max_new_clips: Optional[int],
                   max_new_source_mb: Optional[float], progress: Optional[ProgressFn]) -> Dict[str, Dict[str, Any]]:
    cache_path = project.cache_dir / CLIP_CACHE_FILE
    src_path = project.cache_dir / SOURCE_CACHE_FILE
    cache = _read_cache(cache_path)
    src_cache = _read_cache(src_path)

    todo: List[Tuple[Dict[str, Any], Path, str]] = []
    keys: Dict[str, str] = {}
    for r in records:
        rid = str(r.get("id") or "")
        if not rid or not r.get("path"):
            continue
        path = project.abspath(r["path"])
        key = _file_key(path)
        if key is None:
            continue
        keys[rid] = key
        ent = cache.get(rid)
        if not (isinstance(ent, dict) and ent.get("key") == key and ent.get("v") == TWIN_PROFILE_VERSION):
            todo.append((r, path, key))
    src_todo: List[Tuple[str, Path, str]] = []
    src_keys: Dict[str, Optional[str]] = {}
    for sid in _sources_of(records):
        path = _raw_path(project, sid)
        key = _file_key(path)
        src_keys[sid] = key
        ent = src_cache.get(sid)
        if key is not None and not (isinstance(ent, dict) and ent.get("key") == key
                                    and ent.get("v") == TWIN_PROFILE_VERSION):
            src_todo.append((sid, path, key))
    if max_new_clips is not None and len(todo) > max_new_clips:
        raise _OverBudget(f"{len(todo)} 段录音还没量过")
    if max_new_source_mb is not None:
        mb = sum(int(k.split(":")[0]) for _, _, k in src_todo) / 1024.0 ** 2
        if mb > max_new_source_mb:
            raise _OverBudget(f"{len(src_todo)} 个原始录音（{mb:.0f} MB）还没量过")

    total_new = len(todo) + len(src_todo)
    done = 0
    changed = False
    for sid, path, key in src_todo:
        _check_cancel()
        try:
            gaps, dur = source_gaps_file(path)
        except Exception as exc:  # noqa: BLE001 - 读不了：这个视频退回只用切好的片段
            log.debug(f"原始录音 {path.name} 读不了（{exc}），这个视频只用切好的片段")
            src_cache.pop(sid, None)
            src_keys[sid] = None
            continue
        src_cache[sid] = {"key": key, "v": TWIN_PROFILE_VERSION, "dur": _r(dur, 3),
                          "gaps": [[_r(s, 3), _r(e, 3)] for s, e in gaps]}
        changed = True
        done += 1
        if progress is not None and total_new:
            progress(done / total_new, f"量原始录音里的停顿 {done}/{total_new}")
    for k, (r, path, key) in enumerate(todo):
        _check_cancel()
        try:
            wav, sr = load_audio(path)
            feat = acoustic_features(wav, sr)
        except Exception as exc:  # noqa: BLE001 - 个别片段读不了不影响别的
            log.debug(f"片段 {r.get('id')} 读不了（{exc}），跳过")
            keys.pop(str(r["id"]), None)
            continue
        feat.update({"key": key, "v": TWIN_PROFILE_VERSION})
        cache[str(r["id"])] = feat
        changed = True
        done += 1
        if progress is not None and total_new and (k % 10 == 0 or k == len(todo) - 1):
            progress(done / total_new, f"测量你的说话习惯 {done}/{total_new}")
        if k % 200 == 199:  # 中途停下也不白量
            _write_json(cache_path, cache)
            _write_json(src_path, src_cache)
    if changed:
        try:
            _write_json(cache_path, cache)
            _write_json(src_path, src_cache)
        except OSError as exc:  # 缓存写不了（硬盘满了）：这次照样算完，只是下次还要重新量
            log.debug(f"缓存写不了（{exc}）")

    by_src: Dict[str, Tuple[List[float], List[float], float]] = {}
    for sid, key in src_keys.items():
        ent = src_cache.get(sid)
        if key is not None and isinstance(ent, dict) and ent.get("key") == key:
            gaps = sorted((float(s), float(e)) for s, e in ent.get("gaps") or [])
            by_src[sid] = ([g[0] for g in gaps], [g[1] for g in gaps], float(ent.get("dur") or 0.0))

    out: Dict[str, Dict[str, Any]] = {}
    for r in records:
        rid = str(r.get("id") or "")
        if rid not in keys:
            continue
        feat = cache.get(rid)
        if not isinstance(feat, dict):
            continue
        info = _place_in_source(r, feat, by_src.get(str(r.get("source") or "")))
        if info is not None:
            out[rid] = info
    return out


def _place_in_source(r: Dict[str, Any], feat: Dict[str, Any],
                     src: Optional[Tuple[List[float], List[float], float]]) -> Optional[Dict[str, Any]]:
    """片段放回整段原始录音（有的话）：开口 / 收音、里面的停顿、前后的停顿都在原始录音上量。"""
    base = {"feat": feat, "mode": "clips", "gap_before": None, "gap_after": None}
    if feat.get("vs") is None or feat.get("ve") is None:
        return None
    try:
        cs, ce = float(r.get("start")), float(r.get("end"))
    except (TypeError, ValueError):
        cs = ce = float("nan")
    if src is not None and math.isfinite(cs) and math.isfinite(ce) and ce > cs and ce <= src[2] + 0.05:
        starts, ends, _ = src
        i = bisect.bisect_right(ends, cs)  # 第一个结束在片段开始之后的停顿
        ov: List[Tuple[float, float]] = []
        while i < len(starts) and starts[i] < ce:
            ov.append((starts[i], ends[i]))
            i += 1
        vs, ve = cs, ce
        before = after = None
        if ov and ov[0][0] <= cs:
            vs, before = ov[0][1], ov[0][1] - ov[0][0]
            ov = ov[1:]
        if ov and ov[-1][1] >= ce:
            ve, after = ov[-1][0], ov[-1][1] - ov[-1][0]
            ov = ov[:-1]
        if ve - vs >= 0.2:
            return {"feat": feat, "mode": "raw", "vs": vs - cs, "ve": ve - cs,
                    "inner": [(s - cs, e - cs) for s, e in ov if s >= vs and e <= ve],
                    "gap_before": before, "gap_after": after}
    vs, ve = float(feat["vs"]), float(feat["ve"])
    if ve - vs < 0.2:
        return None
    base.update({"vs": vs, "ve": ve, "inner": [(float(s), float(e)) for s, e in feat.get("gaps") or []]})
    return base


def consecutive_pairs(records: Sequence[Dict[str, Any]], use: Iterable[str],
                      gap_after: Optional[Dict[str, Optional[float]]] = None) -> List[Tuple[str, str, str]]:
    """前后连着说的两段：同一个视频里紧挨着（中间没有别的片段，包括删掉 / 没用上的）、中间停顿 < 2 秒。
    返回 [(前一段 id, 后一段 id, "sentence" | "clause")]（前一段以句号类标点结尾 → sentence）。"""
    use = set(use)
    gap_after = gap_after or {}
    by_src: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        if r.get("source") and isinstance(r.get("start"), (int, float)):
            by_src.setdefault(str(r["source"]), []).append(r)
    out: List[Tuple[str, str, str]] = []
    for sid in sorted(by_src):
        items = sorted(by_src[sid], key=lambda x: (float(x["start"]), str(x.get("id"))))
        for a, b in zip(items, items[1:]):
            if a.get("id") not in use or b.get("id") not in use:
                continue
            gap = gap_after.get(str(a["id"]))
            if gap is None:
                try:
                    gap = float(b["start"]) - float(a.get("end", a["start"]))
                except (TypeError, ValueError):
                    continue
            if gap >= DELTA_MAX_GAP:
                continue
            out.append((str(a["id"]), str(b["id"]), "sentence" if final_mark(a.get("text", "")) == "sentence"
                        else "clause"))
    return out


# ============================================================================ 语速模型
def fit_duration_model(features: Sequence[Sequence[float]], voiced: Sequence[float]) -> Dict[str, Any]:
    """voiced_s ≈ e + a·汉字 + b·英文音节 + c·数字 + d·句中标点（系数都不小于 0，NNLS）。
    ok = 至少 50 句而且 r² ≥ 0.3；不 ok 时用整体语速（音节 / 秒）估计。"""
    from scipy.optimize import nnls

    X = np.asarray(features, dtype=np.float64).reshape(-1, 4) if len(features) else np.zeros((0, 4))
    y = np.asarray(voiced, dtype=np.float64).reshape(-1)
    good = np.isfinite(y) & (y > 0) & np.isfinite(X).all(axis=1)
    X, y = X[good], y[good]
    n = int(y.size)
    out: Dict[str, Any] = {"terms": list(DURATION_TERMS), "coef": None, "r2": None, "resid_sd_log": None,
                           "n": n, "ok": False, "global_rate": None}
    syl = X[:, :3].sum(axis=1) if n else np.zeros(0)
    if n >= MIN_N and float(y.sum()) > 0 and float(syl.sum()) > 0:
        out["global_rate"] = _r(float(syl.sum()) / float(y.sum()), 4)
    if n < MIN_N:
        return out
    A = np.column_stack([np.ones(n), X])
    try:
        coef, _ = nnls(A, y)
    except Exception:  # noqa: BLE001 - 解不出来：只用整体语速
        return out
    pred = A @ coef
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - float(np.sum((y - pred) ** 2)) / ss_tot if ss_tot > 0 else None
    pos = pred > 0
    resid = np.log(y[pos] / pred[pos])
    out.update({"coef": {name: _r(c, 5) for name, c in zip(DURATION_TERMS, coef)}, "r2": _r(r2, 4),
                "resid_sd_log": _r(np.std(resid, ddof=1), 4) if resid.size >= MIN_N else None})
    out["ok"] = bool(n >= 50 and r2 is not None and r2 >= 0.3)
    return out


def expected_voiced(model: Optional[Dict[str, Any]], text: str) -> Optional[float]:
    """按语速模型估计这句话要说多少秒（不含停顿）。模型不 ok 时用整体语速；都没有时 None（没测出来）。"""
    if not model:
        return None
    feats = duration_features(text)
    if model.get("ok") and isinstance(model.get("coef"), dict):
        c = model["coef"]
        val = float(c.get("const") or 0.0) + sum(float(c.get(name) or 0.0) * x
                                                  for name, x in zip(DURATION_TERMS[1:], feats))
        return val if val > 0 else None
    rate = model.get("global_rate")
    syl = sum(feats[:3])
    if rate and syl > 0:
        return syl / float(rate)
    return None


# ============================================================================ 汇总成 twin_profile.json
def twin_signature(project: Project, kept: Sequence[Dict[str, Any]]) -> str:
    """素材的指纹：哪些片段（训练 / 验证）、保存了的文字和语言、原始录音文件，再加上版本号。有一样变了就要重算。"""
    from voicetwin.eval.speaker import _manifest_sig

    texts = sorted((str(r.get("id")), str(r.get("text") or ""), str(r.get("lang") or "")) for r in kept)
    raws = {sid: _file_key(_raw_path(project, sid)) or "-" for sid in _sources_of(kept)}
    return short_hash(_manifest_sig(project), texts, sorted(raws.items()), TWIN_PROFILE_VERSION, n=16)


def twin_profile_path(project: Project) -> Path:
    return project.root / TWIN_PROFILE_FILE


def load_twin_profile(project: Project) -> Optional[Dict[str, Any]]:
    data = project.read_json(twin_profile_path(project), None)
    if not isinstance(data, dict) or data.get("version") != TWIN_PROFILE_VERSION:
        return None
    return data


def _kept(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in records if r.get("keep", True) and not r.get("deleted") and r.get("path") and r.get("id")]


def build_twin_profile(project: Project, force: bool = False, max_new_clips: Optional[int] = None,
                       max_new_source_mb: Optional[float] = None,
                       progress: Optional[ProgressFn] = None) -> Optional[Dict[str, Any]]:
    """量你本人的说话习惯，写进 workspace/<声音>/twin_profile.json（先写临时文件再换上去）。

    素材没变（signature 一样）时直接返回上次的结果。max_new_*：要新量的录音太多时这次不做、返回 None
    （校对表保存时用：第一次要把全部录音量一遍，留到素材准备 / 生成「一模一样」时再做，保存不会因此变慢）。"""
    with _LOCK:
        records = project.load_manifest()
        kept = sorted(_kept(records), key=lambda r: str(r["id"]))
        sig = twin_signature(project, kept)
        if not force:
            old = load_twin_profile(project)
            if old is not None and old.get("signature") == sig:
                return old
        try:
            clips = collect_clips(project, kept, max_new_clips=max_new_clips, max_new_source_mb=max_new_source_mb,
                                  progress=progress)
        except _OverBudget as exc:
            log.debug(f"说话习惯这次先不量：{exc}")
            return None
        prof = _aggregate(project, records, kept, clips, sig)
        _write_json(twin_profile_path(project), prof)
        return prof


def _aggregate(project: Project, records: Sequence[Dict[str, Any]], kept: Sequence[Dict[str, Any]],
               clips: Dict[str, Dict[str, Any]], sig: str) -> Dict[str, Any]:
    used = [r for r in kept if str(r["id"]) in clips]
    meds = [clips[str(r["id"])]["feat"].get("f0_med_hz") for r in used]
    f0_arr = _finite(meds)
    f0_ref = float(np.median(f0_arr)) if f0_arr.size >= MIN_N else None

    # ---------------------------------------------------------------- 停顿
    pause_vals: Dict[str, List[float]] = {c: [] for c in PAUSE_CLASSES}
    n_inner = {c: 0 for c in PAUSE_CLASSES}
    n_final = {c: 0 for c in PAUSE_CLASSES}
    n_marks = {c: 0 for c in PAUSE_CLASSES}
    n_matched = {c: 0 for c in PAUSE_CLASSES}
    hes: List[float] = []
    inner_all: List[float] = []
    syl_total = 0
    n_text_clips = 0
    modes = {"raw": set(), "clips": set()}
    for r in used:
        c = clips[str(r["id"])]
        modes[c["mode"]].add(str(r.get("source") or ""))
        text = str(r.get("text") or "")
        syl = syllable_count(text)
        if syl <= 0:
            continue
        n_text_clips += 1
        syl_total += syl
        vs, ve = float(c["vs"]), float(c["ve"])
        span = ve - vs
        cp = [(((s + e) / 2.0 - vs) / span, e - s) for s, e in c["inner"]]
        inner_all += [d for _, d in cp if PAUSE_MIN <= d <= PAUSE_MAX]
        pairs, hesit, counts = align_pauses(text, cp)
        for cls, n in counts.items():
            n_marks[cls] += n
        for cls, d in pairs:
            n_matched[cls] += 1
            if PAUSE_MIN <= d <= PAUSE_MAX:
                pause_vals[cls].append(d)
                n_inner[cls] += 1
        hes += [d for d in hesit if PAUSE_MIN <= d <= PAUSE_MAX]
        fm = final_mark(text)
        ga = c.get("gap_after")
        if fm and ga is not None and PAUSE_MIN <= ga <= PAUSE_MAX:
            pause_vals[fm].append(float(ga))
            n_final[fm] += 1
    pauses: Dict[str, Any] = {}
    for cls in PAUSE_CLASSES:
        st = _quantiles(pause_vals[cls], 3)
        st.update({"n_inner": n_inner[cls], "n_final": n_final[cls], "n_marks": n_marks[cls],
                   "p_pause": _r(n_matched[cls] / n_marks[cls], 3) if n_marks[cls] >= MIN_N else None})
        pauses[cls] = st
    hst = _quantiles(hes, 3)
    per100 = _r(100.0 * len(hes) / syl_total, 3) if n_text_clips >= MIN_N and syl_total else None
    hst.update({"n_syllables": syl_total, "per_100_syllables": per100})
    pauses["hesitation"] = hst
    ip = _finite(inner_all)
    inner_p97 = {"value": _r(np.percentile(ip, 97), 3) if ip.size >= MIN_N else None, "n": int(ip.size)}

    # ---------------------------------------------------------------- 音调（分组）
    rows: List[Tuple[str, str, Dict[str, Optional[float]]]] = []
    for r in used:
        text = str(r.get("text") or "")
        if syllable_count(text) <= 0:
            continue
        f = _with_text(clips[str(r["id"])]["feat"], text, f0_ref)
        vals = {k: f.get(k) for k in PROSODY_FEATURES}
        if not ends_sentence(text):
            vals["final_slope"] = None  # 话还没说完的片段：最后那一下不是句末的升降
        rows.append((_kind2(text), _en_bin(en_share(text)), vals))

    def group_vals(kind: str, bin_: str, feat: str) -> List[Optional[float]]:
        return [v[feat] for k, b, v in rows if k == kind and (bin_ == "all" or b == bin_)]

    groups: Dict[str, Any] = {}
    for kind in KINDS:
        for bin_ in [b[0] for b in EN_BINS] + ["all"]:
            own_n = sum(1 for k, b, _ in rows if k == kind and (bin_ == "all" or b == bin_))
            feats: Dict[str, Any] = {}
            for feat in PROSODY_FEATURES:
                chain = [(kind, bin_), (kind, "all")]
                if kind == "question" and feat != "final_slope":  # 问句太少：借陈述句的（句末升降不借）
                    chain += [("statement", bin_), ("statement", "all")]
                pick: Dict[str, Any] = {"mean": None, "sd": None, "n": len(_finite(group_vals(kind, bin_, feat))),
                                        "from": None}
                for k2, b2 in chain:
                    st = _mean_sd(group_vals(k2, b2, feat), 4)
                    if st["mean"] is not None:
                        pick = dict(st, **{"from": f"{k2}|{b2}"})
                        break
                feats[feat] = pick
            groups[f"{kind}|{bin_}"] = {"n": own_n, "features": feats}
    prosody = {"f0_median_hz": {"value": _r(f0_ref, 2), "n": int(f0_arr.size)}, "features": list(PROSODY_FEATURES),
               "en_bins": {name: [lo, min(hi, 1.0)] for name, lo, hi in EN_BINS}, "groups": groups}

    # ---------------------------------------------------------------- 语速模型
    X, y = [], []
    for r in used:
        text = str(r.get("text") or "")
        voiced = clips[str(r["id"])]["feat"].get("voiced") or 0.0
        if syllable_count(text) > 0 and voiced >= 0.3:
            X.append(duration_features(text))
            y.append(float(voiced))
    duration_model = fit_duration_model(X, y)

    # ---------------------------------------------------------------- 音量、句首句尾
    by_src: Dict[str, List[float]] = {}
    for r in used:
        lv = clips[str(r["id"])]["feat"].get("level_db")
        if lv is not None:
            by_src.setdefault(str(r.get("source") or ""), []).append(float(lv))
    diffs: List[float] = []
    for sid in sorted(by_src):
        vals = by_src[sid]
        if len(vals) >= 3:  # 一个视频只有一两段：和自己的中位数比没有意义
            med = float(np.median(vals))
            diffs += [v - med for v in vals]
    darr = _finite(diffs)
    loudness = {"sd": _r(darr.std(ddof=1), 3) if darr.size >= MIN_N else None,
                "p05": _r(np.percentile(darr, 5), 3) if darr.size >= MIN_N else None,
                "p95": _r(np.percentile(darr, 95), 3) if darr.size >= MIN_N else None, "n": int(darr.size)}
    onsets = _finite(clips[str(r["id"])]["feat"].get("onset_ms") for r in used)
    offsets = _finite(clips[str(r["id"])]["feat"].get("offset_ms") for r in used)
    breaths = [clips[str(r["id"])]["feat"].get("breath") for r in used]
    breaths = [b for b in breaths if b is not None]
    edges = {"onset_ms": {"median": _r(np.median(onsets), 1) if onsets.size >= MIN_N else None,
                          "n": int(onsets.size)},
             "offset_ms": {"median": _r(np.median(offsets), 1) if offsets.size >= MIN_N else None,
                           "n": int(offsets.size)},
             "breath_fraction": {"value": _r(sum(breaths) / len(breaths), 3) if len(breaths) >= MIN_N else None,
                                 "n": len(breaths), "note": "只记录，不拿来做任何处理"}}

    # ---------------------------------------------------------------- 前后两句的变化
    ids = {str(r["id"]) for r in used}
    gap_after = {rid: c.get("gap_after") for rid, c in clips.items() if c.get("mode") == "raw"}
    d_f0: Dict[str, List[float]] = {"sentence": [], "clause": []}
    d_rate: Dict[str, List[float]] = {"sentence": [], "clause": []}
    feats_by_id = {str(r["id"]): _with_text(clips[str(r["id"])]["feat"], str(r.get("text") or ""), f0_ref)
                   for r in used}
    for a, b, typ in consecutive_pairs(records, ids, gap_after):
        fa, fb = feats_by_id[a], feats_by_id[b]
        if fa.get("f0_med_hz") and fb.get("f0_med_hz"):
            d_f0[typ].append(12.0 * math.log2(float(fb["f0_med_hz"]) / float(fa["f0_med_hz"])))
        if fa.get("rate") and fb.get("rate"):
            d_rate[typ].append(math.log(float(fb["rate"]) / float(fa["rate"])))
    deltas: Dict[str, Any] = {typ: {"f0_med_st": _mean_sd(d_f0[typ], 4), "log_rate": _mean_sd(d_rate[typ], 4)}
                              for typ in ("sentence", "clause")}
    deltas["timbre"] = None  # 参考录音库（build_reference_bank）算出声纹以后填

    # ---------------------------------------------------------------- 频谱（只记录）
    ltas_rows = [clips[str(r["id"])]["feat"].get("ltas") for r in used]
    ltas_rows = [x for x in ltas_rows if isinstance(x, list) and len(x) == len(LTAS_CENTERS)]
    mean_b, sd_b, n_b = [], [], []
    for k in range(len(LTAS_CENTERS)):
        st = _mean_sd([row[k] for row in ltas_rows], 2)
        mean_b.append(st["mean"])
        sd_b.append(st["sd"])
        n_b.append(st["n"])
    ltas = {"bands_hz": [_r(c, 1) for c in LTAS_CENTERS], "mean": mean_b, "sd": sd_b, "n": n_b,
            "note": "只记录（给打分校准参考），不拿来改声音"}

    raw_src, clip_src = modes["raw"], modes["clips"] - modes["raw"]
    source = "raw" if raw_src and not clip_src else ("clips" if not raw_src else "mixed")
    return {
        "version": TWIN_PROFILE_VERSION,
        "signature": sig,
        "voice": project.voice,
        "source": source,
        "sources": {"raw": len(raw_src), "clips": len(clip_src)},
        "clips": len(used),
        "clips_skipped": len(kept) - len(used),
        "pauses": pauses,
        "inner_pause_p97": inner_p97,
        "prosody": prosody,
        "duration_model": duration_model,
        "loudness": loudness,
        "edges": edges,
        "deltas": deltas,
        "ltas": ltas,
    }


def fill_timbre_deltas(project: Project, records: Sequence[Dict[str, Any]], embs: Dict[str, Dict[str, np.ndarray]],
                       judge_sig: str = "") -> Optional[Dict[str, Any]]:
    """参考录音库算出声纹以后：前后连着说的两段之间音色差多少（1 − 余弦相似度，几个声纹模型取平均），
    按 sentence / clause 分开，写进 twin_profile.json 的 deltas.timbre（signature 不变）。"""
    from voicetwin.eval.speaker import cosine

    with _LOCK:
        prof = load_twin_profile(project)
        if prof is None:
            return None
        vals: Dict[str, List[float]] = {"sentence": [], "clause": []}
        for a, b, typ in consecutive_pairs(records, set(embs)):
            ea, eb = embs.get(a) or {}, embs.get(b) or {}
            common = sorted(set(ea) & set(eb))
            if common:
                vals[typ].append(float(np.mean([1.0 - cosine(ea[m], eb[m]) for m in common])))
        timbre = {typ: _mean_sd(vals[typ], 5) for typ in vals}
        timbre["judge_sig"] = judge_sig
        prof.setdefault("deltas", {})["timbre"] = timbre
        _write_json(twin_profile_path(project), prof)
        return prof
