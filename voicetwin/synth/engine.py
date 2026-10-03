"""合成引擎：讲稿 → 完整的讲课音频（+ 字幕）。

为了"像你"做的事情：
1. 每句话生成多个候选（不同随机种子），用"像你本人（%）"（几个声纹模型校准后的平均）、
   识别错字率、语速/音高偏差打分；低于 85% 的候选直接淘汰，剩下的里面相似度为主挑最像的；
2. 错字太多（漏字/多字/读错）或者都不够像时自动重做；「完美」档会一批一批地试，直到达到严格标准或试满 20 次；
   「一模一样」档（默认，synth/search.py）每句从参考录音库里换几条参考、试几种生成设置，一次请求同时生成好几个版本
   （引擎自检通过时），先快速打分、挑出来的再完整打分（eval/identical_judge.py），每句至少 / 最多试几个按显卡分档，
   挑出来的那个达到严格标准、并且再试也不更好时才停；每句留下最好的几个版本，重新生成时一起比；
3. 疑问句用你的疑问语气参考音频，陈述句用陈述参考（「完美」档还会挑长短最接近的参考）；
4. 句间/段间停顿按你本人的停顿习惯（含自然波动），停顿和开头结尾都是绝对的数字静音（全是 0），没有任何底噪；
   「一模一样」档：停顿按你本人实测的停顿分布，拼好以后用量你录音的同一个方法再量、再改两遍；整篇再挑一遍
   （Viterbi：前后两句的音调、语速、音色变化和你本人比），每句一个固定的音量系数（按你本人句子之间的音量差）；
5. 每句首尾的非语音会被切掉并淡入淡出，句子边上不留杂音（「一模一样」以底噪为准切，句尾按你本人的收音长度多留一点）；
6. 语速用验证集自动校准，再乘上你选的快慢；快慢由合成模型本身控制（GPT-SoVITS 的 speed_factor 只改时长、
   不改音高和音色），这里从不对波形做重采样或变调式的拉伸；停顿也跟着快慢按比例变化；
7. 响度匹配你原来的录音；
8. 每句结果都缓存：改了讲稿的某一句，重新生成只会重做那一句；
9. 「完美」「一模一样」档同时输出「未去杂音」和「去杂音」两个完整版本，自动比较哪个更像你并标出推荐
   （「一模一样」只给说话部分量得出底噪的句子去杂音，别的句子两个版本一模一样）；
10. 生成的文件名最后是「_实际用的模型名」（例如 第3课_10月05日09点30分_V4.wav），按每一句实际用的模型文件检测，
    写文件那一刻才定；文件里面的注释、报告里也写。文件名只用汉字、英文字母、数字和下划线。
"""

from __future__ import annotations

import json
import math
import random
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np

from voicetwin.backends.base import Backend, SynthRequest
from voicetwin.data.references import aux_references, pick_reference
from voicetwin.eval.metrics import CERChecker, Score, Scorer, engine_is_strong
from voicetwin.eval.speaker import (
    HONEST_NOTE,
    PCT_HELP,
    SimilarityJudge,
    get_speaker_encoder,
    gsv_root_from_cfg,
    status_for_pct,
    voice_centroid,
)
from voicetwin.project import Project
from voicetwin.style.profile import pause_range, pause_seconds
from voicetwin.synth.script import ScriptSegment, parse_script
from voicetwin.utils import atomic
from voicetwin.utils.audio import (
    auto_silence_threshold,
    fade,
    frame_rms_db,
    load_audio,
    measure_lufs,
    normalize_lufs,
    resample,
    save_audio,
    silent_runs,
    speech_level_db,
    speech_noise_db,
)
from voicetwin.utils.ffmpeg import encode
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import count_cjk, en_words, send_lang, short_hash, syllable_count

try:  # U1：停止按钮
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover - 没有 U1 时什么都不做
    def _check_cancel() -> None:
        return None

log = get_logger("synth")
CACHE_VERSION = "v2"
ProgressFn = Callable[[float, str], None]

QUALITY_ORDER = ("fast", "balanced", "best", "max", "perfect", "identical")
#: 默认档位：auto、空、不认识的写法，任何显卡都用它（老师的要求：除非自己换，一直用最高档）
DEFAULT_QUALITY = "identical"
#: 网页「质量」单选框上的字（命令行、报告里也用它）。只有「一模一样」写「最慢」：「极致」「完美」都比它快。
QUALITY_LABELS = {
    "fast": "快速（最快，每句只做 1 遍）",
    "balanced": "均衡（每句做 3 遍，挑最像你的）",
    "best": "最好（每句做 5 遍，并检查漏字错字）",
    "max": "极致（很慢，更稳更像，建议显存 ≥ 8GB）",
    "perfect": "完美：每句最多试 20 次、严格检查漏字错字，同时做「未去杂音 / 去杂音」两个版本让你选，句子之间完全静音（很慢）",
    # 只写现在真的会做的事（不要乱写）：设计方案 §4.1 里「用满显卡」（没有实测）这种说法不写；「每句试几十个」
    # 也不写（没有 N 卡时每句最多 12 个）。tests/test_identical_tier.py 会核对
    "identical": "一模一样（默认）：每句换几条你的录音当参考、试很多个版本，严格检查漏字错字，挑最像你的；"
                 "整篇按你的停顿和音量拼接，同时做「未去杂音 / 去杂音」两个版本，句子之间完全静音（最慢）",
}
QUALITY_SHORT = {"fast": "快速", "balanced": "均衡", "best": "最好", "max": "极致", "perfect": "完美",
                 "identical": "一模一样"}
#: 每个档位一行说明（网页上显示，诚实：只说多试、挑得更准，不保证百分之百一样）
QUALITY_HELP = {
    "fast": "快速：每句只生成 1 次，最快；偶尔会有读错或不太像的句子。",
    "balanced": "均衡：每句生成 3 次，自动挑最像你的；速度和效果兼顾。",
    "best": "最好：每句生成 5 次，并用语音识别检查漏字、错字；更慢，但更稳。",
    "max": "极致：每句生成 8 次并严格检查漏字错字，不够像的自动重做；时间大约是「均衡」的 3～5 倍。",
    "perfect": "完美：每句最多试 20 次、严格检查漏字错字，同时做「未去杂音 / 去杂音」两个版本让你选，句子之间完全静音（很慢）。",
    "identical": "一模一样：每句从你的录音里换几条最合适的当参考，换着用几种生成设置，一共试很多个版本（显卡越好试得越多；"
                 "合成引擎自检通过时，显卡一次同时生成好几个版本）；用声纹打分（精准声纹模型下载了时是三个模型一起）、"
                 "中英文分开的错字检查（有中文识别模型 Paraformer 时）和你本人的语速、音调一起挑最像你的，"
                 "达到严格标准、并且再试也不更好时才停。整篇再挑一遍让前后句子衔接自然，再按你本人的停顿长短和音量拼接"
                 "（拼好以后用量你录音的同一个方法再量一遍停顿），句子之间是完全的数字静音，"
                 "同时给出「未去杂音 / 去杂音」两个版本。最慢。这是努力的方向，不能保证百分之百一样。",
}
QUALITY_NOTE = ("越往下越慢。默认是「一模一样」：它是努力的方向，不是保证——任何声音克隆都做不到百分之百一样，"
                "也不会超过模型训练出来的水平。素材的质量和数量、认真校对文字，对像不像影响最大。")
#: 打开网页时「质量」下面的说明（按显卡；{size} 是检测到的显存，例如「显存 12 GB」，检测不到写「你的显卡」；
#: {cap} 是这种显卡每句最多试几个，和真正生成时一样：自带的值合并 config.yaml 的 synth.tiers.identical，见 identical_limits）。
#: 「新模型第一次先做一次准备」（第 8 步）等设计方案 §4.2 的说法，等那几步做好了再写上；「不会因为显存不够而停下」
#: 不写：同时生成的个数减到 1 个、让出识别模型的显存以后还不够，生成还是会停下（并说明原因）
QUALITY_TIER_NOTES = {
    "high": "已选好「一模一样」（{size}）。每句会试很多个版本，所以很慢；生成时会按实际速度告诉你还要多久。",
    "mid": "已选好「一模一样」（{size}）。每句会试很多个版本，所以很慢；生成时会按实际速度告诉你还要多久。",
    "low": "已选好「一模一样」（{size}，显存偏小）：每句最多试 {cap} 个版本，会很慢；显存不够时会先自动减少同时生成的个数"
           "再接着试。着急的话可以改选「均衡」。",
    "none": "没检测到能用的 N 卡（NVIDIA 显卡），仍然先选好「一模一样」：用处理器生成会非常慢，每句最多试 {cap} 个版本。"
            "着急的话可以改选「均衡」。",
}

#: 各档位的参数。依据见 research_quality.md §6（结构有依据，具体数字是工程取值，最终由识别校验和声纹打分把关）。
QUALITY_PRESETS: Dict[str, Dict[str, Any]] = {
    "fast": {"candidates": 1, "asr": False, "retry_rounds": 0, "retry_candidates": 0, "aux_refs": None},
    "balanced": {"candidates": 3, "asr": False, "retry_rounds": 2, "retry_candidates": 2, "aux_refs": None,
                 "cer_retry_threshold": {"strong": 0.15, "weak": 0.15}},
    "best": {"candidates": 5, "asr": True, "retry_rounds": 2, "retry_candidates": 2, "aux_refs": None,
             "cer_retry_threshold": {"strong": 0.10, "weak": 0.15}},
    "max": {"candidates": 8, "low_tier_candidates": 6, "asr": True, "force_asr": True, "retry_rounds": 3,
            "retry_candidates": 3, "early_after": 4, "early_pct": 99.0, "aux_refs": 3, "low_tier_aux_refs": 2,
            "cer_retry_threshold": {"strong": 0.08, "weak": 0.12}},
    "perfect": {"candidates": 4, "adaptive": True, "max_candidates": 20, "low_tier_max_candidates": 12,
                "asr": True, "force_asr": True, "aux_refs": 3, "low_tier_aux_refs": 2,
                "cer_retry_threshold": {"strong": 0.08, "weak": 0.12}, "cer_target": {"strong": 0.05, "weak": 0.08},
                "target_pct": 99.0, "variants": True, "match_reference": True},
    # 「一模一样」：按显卡分档的值（high / mid / low / none）在 Narrator 里按显卡取出来；怎么找见 synth/search.py。
    # continuity / two_checkpoints / speed_trick 是后面几步才用的（见 research/一模一样/设计方案原文.md）
    "identical": {"search": True, "adaptive": True, "candidates": 4, "asr": True, "force_asr": True,
                  "batch": {"high": 12, "mid": 8, "low": 2, "none": 1},
                  "min_candidates": {"high": 40, "mid": 40, "low": 16, "none": 6},
                  "max_candidates": {"high": 64, "mid": 64, "low": 32, "none": 12},
                  "refs_per_sentence": {"high": 3, "mid": 3, "low": 2, "none": 2},
                  "aux_refs": 3, "low_tier_aux_refs": 2, "aux_options": [3, 0],
                  "presets": [{"temperature": 1.0, "top_k": 15, "top_p": 1.0},
                              {"temperature": 1.0, "top_k": 5, "top_p": 1.0}],
                  "rescue_preset": {"temperature": 0.6, "top_k": 15, "top_p": 0.8},
                  "plateau": 8, "plateau_eps": 0.02, "full_score_top": 12, "full_score_max": 24, "store_top_k": 6,
                  "cer_retry_threshold": {"strong": 0.08, "weak": 0.12}, "cer_target": {"strong": 0.03, "weak": 0.06},
                  "search_target": "p50", "pass_target": "p25", "member_floor": "p10",
                  "refine_tempo": True, "continuity": True, "pipeline": "auto", "speed_trick": "auto",
                  "judge_device": "auto", "two_checkpoints": True, "variants": True, "match_reference": True},
}
#: 重做时用更保守的采样（温度/候选词更少 → 更稳）；GPT-SoVITS 官方温度上限是 1
RETRY_SAMPLING = [{"temperature": 0.7, "top_k": 10, "top_p": 1.0}, {"temperature": 0.6, "top_k": 15, "top_p": 0.8}]
VARIANT_RAW, VARIANT_DENOISED = "未去杂音", "去杂音"
RESULT_HEADERS = ["#", "句子", "像你本人（%）", "状态", "提示"]
LEAD_IN, LEAD_OUT = 0.35, 0.4


def _vram_tier() -> str:
    try:
        from voicetwin.utils.gpu import vram_tier

        return vram_tier()
    except Exception:
        return "none"


def recommended_quality(tier: Optional[str] = None, size: Optional[str] = None,
                        cfg: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
    """默认档位和一句说明：任何显卡都是「一模一样」，说明按显卡写（显存小、没有 N 卡时会很慢，可以改选「均衡」）。
    size 是检测到的显存（例如「显存 12 GB」），网页传进来；不传写「你的显卡」。
    cfg 是读进来的设置：说明里「每句最多试几个」和真正生成时一样（config.yaml 改了 synth.tiers.identical 就跟着变）。"""
    tier = tier if tier in QUALITY_TIER_NOTES else (_vram_tier() if not tier else "none")
    scfg = (cfg.get("synth") if cfg is not None else None) or {}
    cap = identical_limits(tier_preset(DEFAULT_QUALITY, scfg), tier)[2]
    return DEFAULT_QUALITY, QUALITY_TIER_NOTES[tier].format(size=size or "你的显卡", cap=cap)


def quality_choices() -> List[Tuple[str, str]]:
    """给网页单选框用的 (中文标签, 值) 列表，从快到慢。"""
    return [(QUALITY_LABELS[q], q) for q in QUALITY_ORDER]


#: 这些写法都当作「没指定」= 默认的「一模一样」
AUTO_QUALITY = ("", "auto", "自动", "none", "null", "默认")


def match_quality(quality: Any) -> Optional[str]:
    """认得出的档位写法 → fast|balanced|best|max|perfect|identical；auto / 空 → 默认的 identical；认不出 → None。
    英文名、中文名（「一模一样」）、网页上的整段标签或它的开头都认。"""
    q = str(quality if quality is not None else "").strip()
    if isinstance(quality, (list, tuple)):  # gradio 偶尔会把单选值包成列表
        q = str(quality[0]).strip() if quality else ""
    low = q.lower()
    if low in AUTO_QUALITY:
        return DEFAULT_QUALITY
    if low in QUALITY_PRESETS:
        return low
    for key in QUALITY_ORDER:
        if q in (QUALITY_LABELS[key], QUALITY_SHORT[key]) or q.startswith(QUALITY_SHORT[key]):
            return key
    return None


def resolve_quality(quality: Any, tier: Optional[str] = None) -> str:
    """把用户/配置给的档位变成 fast|balanced|best|max|perfect|identical；auto、空、不认识的都用默认的「一模一样」
    （任何显卡都一样，tier 只为兼容旧的调用保留）。"""
    key = match_quality(quality)
    if key is None:
        q = quality[0] if isinstance(quality, (list, tuple)) and quality else quality
        log.warning(f"不认识的质量档位「{str(q).strip()}」，改用默认的「{QUALITY_SHORT[DEFAULT_QUALITY]}」")
        return DEFAULT_QUALITY
    return key


def _per_tier(value: Any, tier: str, default: int) -> int:
    """档位参数可以写一个数，也可以按显卡分档写 {high, mid, low, none}；写错了用 default。"""
    if isinstance(value, dict):
        value = value.get(tier, value.get("mid"))
    try:
        v = int(value)
    except (TypeError, ValueError):
        return int(default)
    return v if v > 0 else int(default)


def tier_preset(quality: str, scfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """档位的参数 = 自带的值，再盖上 config.yaml 的 synth.tiers.<档位>（写 auto / 没写的不算）。
    两边都是表的（按显卡分档的 {high, mid, low, none}、错字门槛的 {strong, weak}）只换写了的那几项：
    只写了一种显卡时，其它显卡还是自带的值，不会掉到兜底的数字。Narrator 和网页上的说明都用它。"""
    preset = dict(QUALITY_PRESETS[quality])
    tiers_cfg = (scfg or {}).get("tiers") or {}
    user = tiers_cfg.get(quality) if isinstance(tiers_cfg, dict) else None
    for key, val in (user.items() if isinstance(user, dict) else ()):
        if val in (None, "auto"):
            continue
        base = preset.get(key)
        if isinstance(base, dict) and isinstance(val, dict):
            val = {**base, **{k: v for k, v in val.items() if v not in (None, "auto", "")}}
        preset[key] = val
    return preset


def identical_limits(preset: Dict[str, Any], tier: str, candidates: Any = None) -> Tuple[int, int, int, int]:
    """「一模一样」按显卡取出来的 (每批几个, 每句至少试几个, 每句最多试几个, 每句几条参考录音)。
    写错的值（不是正数）用这种显卡自带的值；candidates 是命令行明确写的 -n：每句最多试几个（至少试的个数跟着变小）。"""
    base = QUALITY_PRESETS["identical"]

    def get(key: str) -> int:
        return _per_tier(preset.get(key), tier, _per_tier(base[key], tier, 1))

    cap = get("max_candidates")
    if candidates not in (None, "auto", 0, "0", ""):
        try:
            cap = max(1, int(candidates))
        except (TypeError, ValueError):
            pass
    return max(1, min(get("batch"), cap)), max(1, min(get("min_candidates"), cap)), cap, get("refs_per_sentence")


def trim_edges(wav: np.ndarray, sr: int, pad_ms: float = 30.0, drop_db: float = 30.0, floor_db: float = 6.0,
               tail_pad_ms: Optional[float] = None, abs_floor_db: float = -65.0,
               min_range_db: Optional[float] = None) -> np.ndarray:
    """去掉一句话首尾的非语音（按能量判断），首尾各留一点余量，并在余量里平滑淡入淡出：
    第一个和最后一个采样都是 0，句子边上不会留下杂音，也不会有"咔哒"声。

    阈值 = max(语音 − drop_db, 底噪 + floor_db, abs_floor_db)，最高到 语音 − 15 dB（语音 = 95% 分位、底噪 = 3% 分位）。
    不传参数时和以前一模一样（30 / 6 / −65，首尾各留 30 毫秒）。「一模一样」档（Narrator._trim）传 45 / 12 / −70：
    以底噪为准切，句尾自然衰减的尾音多留一些；tail_pad_ms = 你本人句尾收音的中位数（30~120 毫秒），
    min_range_db = 12：整段没有一处比底噪高 12 dB、频谱又像噪声（只有底噪、嘶嘶声）时切成空的。"""
    wav = np.asarray(wav, dtype=np.float32)
    if wav.size == 0:
        return wav
    hop_ms, win_ms = 5.0, 20.0
    if min_range_db is not None:
        levels = speech_noise_db(frame_rms_db(wav, sr))
        if levels is None or (levels[1] - levels[0] < float(min_range_db) and _noise_like(wav, sr)):
            return wav[:0]
    thr = auto_silence_threshold(wav, sr, abs_floor_db, drop_db, floor_db)
    db = frame_rms_db(wav, sr, hop_ms=hop_ms, win_ms=win_ms)
    voiced = np.where(db >= thr)[0]
    if voiced.size == 0:
        return wav[:0]
    hop = sr * hop_ms / 1000.0
    half = sr * win_ms / 2000.0
    pad = int(sr * pad_ms / 1000.0)
    tail_pad = int(sr * (pad_ms if tail_pad_ms is None else float(tail_pad_ms)) / 1000.0)
    v0 = int(voiced[0] * hop - half)
    v1 = int(voiced[-1] * hop + half)
    start = max(0, v0 - pad)
    end = min(len(wav), v1 + tail_pad)
    out = wav[start:end].astype(np.float32, copy=True)
    n = len(out)
    if n < 4:
        return out[:0]
    # 淡入淡出放在语音前后的余量里（再往语音里多 4 / 8 毫秒）。真实的 GPT-SoVITS 输出开头没有空白、
    # 第一个采样就是声音：这时前面没有余量，只淡入 4 毫秒防止「咔哒」声，不能把第一个字的开头淡掉。
    lead = max(0, v0 - start)
    tail = max(0, end - v1)
    n_in = min(n // 2, max(int(sr * 0.002), lead + int(sr * 0.004)))
    n_out = min(n // 2, max(int(sr * 0.002), tail + int(sr * 0.008)))
    if n_in > 1:
        out[:n_in] *= (0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, n_in))).astype(np.float32)
    if n_out > 1:
        out[-n_out:] *= (0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, n_out))).astype(np.float32)
    out[0] = 0.0
    out[-1] = 0.0
    return out


#: 频谱平坦度（几何平均 / 算术平均）不低于这个数算「像噪声」：实测白噪声 0.99，说话、音调都远低于 0.01
NOISE_FLATNESS = 0.3


def _noise_like(wav: np.ndarray, sr: int) -> bool:
    """整段像不像嘶嘶声（宽带噪声）：频谱很平。只靠音量分不出「一直很平稳的声音」是噪声还是音调，所以再看频谱——
    说话、音调的频谱有一个个峰，平坦度远低于 NOISE_FLATNESS。"""
    from scipy import signal

    x = np.asarray(wav, dtype=np.float64)
    x = x[np.abs(x) > 0]
    if x.size < 256:
        return False
    f, pw = signal.welch(x, sr, nperseg=min(1024, x.size))
    pw = pw[(f >= 100.0) & (f <= 0.45 * sr)]
    pw = pw[pw > 0]
    if pw.size < 8:
        return False
    return float(np.exp(np.mean(np.log(pw))) / np.mean(pw)) >= NOISE_FLATNESS


def denoise_light(wav: np.ndarray, sr: int, strength: float = 0.5) -> Optional[np.ndarray]:
    """轻度去杂音（noisereduce 平稳噪声模式，中等强度）。没装 noisereduce 时返回 None。

    噪声样本取这句话里最安静的几段（句内停顿）；样本不够（< 0.15 秒）时不处理，原样返回——宁可不去，也不伤音色。
    """
    try:
        import noisereduce as nr  # type: ignore
    except Exception:
        return None
    wav = np.asarray(wav, dtype=np.float32)
    if wav.size < sr * 0.3:
        return wav.copy()
    try:
        hop = int(sr * 0.01)
        edge = int(sr * 0.045)  # 首尾已经淡入淡出过，不能拿来估计噪声
        inner = wav[edge:len(wav) - edge] if len(wav) > 2 * edge + sr * 0.2 else wav
        db = frame_rms_db(inner, sr, hop_ms=10.0, win_ms=30.0)
        valid = db > -90.0
        if not np.any(valid):
            return wav.copy()
        floor = float(np.percentile(db[valid], 10))
        top = float(np.percentile(db[valid], 95))
        if top - floor < 15.0:  # 没有明显的停顿可以当噪声样本
            return wav.copy()
        quiet = np.where(valid & (db <= floor + 3.0))[0]
        pieces = [inner[i * hop:(i + 1) * hop] for i in quiet if (i + 1) * hop <= len(inner)]
        noise = np.concatenate(pieces) if pieces else np.zeros(0, dtype=np.float32)
        if len(noise) < sr * 0.15 or float(np.max(np.abs(noise))) <= 0.0:
            return wav.copy()
        out = nr.reduce_noise(y=wav, sr=sr, y_noise=noise, stationary=True, prop_decrease=float(strength),
                              n_std_thresh_stationary=1.5)
        out = np.asarray(out, dtype=np.float32).reshape(-1)
        if out.shape != wav.shape or not np.all(np.isfinite(out)):
            return wav.copy()
        n = min(len(out) // 2, int(sr * 0.01))
        if n > 1:  # 保证首尾仍然从 0 开始、到 0 结束
            out[:n] *= np.linspace(0.0, 1.0, n, dtype=np.float32)
            out[-n:] *= np.linspace(1.0, 0.0, n, dtype=np.float32)
        out[0] = 0.0
        out[-1] = 0.0
        return out
    except Exception as exc:
        log.warning(f"去杂音失败（{exc}），这一句用原声")
        return wav.copy()


SHORT_HINT = "这一句很短（人声不到 2 秒），「像你本人」的分数只能粗略参考，请用耳朵听一下"


def _is_short(score: Any) -> bool:
    """这个候选的人声是不是太短（< 2 秒）——这时声纹打分波动大。"""
    from voicetwin.eval.speaker import SHORT_WARN_SECONDS

    sec = getattr(score, "speech_seconds", None)
    return isinstance(sec, (int, float)) and sec < SHORT_WARN_SECONDS


@dataclass
class SegmentResult:
    segment: ScriptSegment
    wav: np.ndarray
    sr: int
    score: Dict[str, Any]
    ref_id: str
    cached: bool
    seed: int
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    start: float = 0.0
    end: float = 0.0
    path: Optional[Path] = None          # 这一句的音频（缓存里的 wav），网页上可以单独试听
    pct: Optional[float] = None          # 像你本人（%）
    status: str = ""                     # ✅ / 🟢 / 🔴 / ⚠️
    hint: str = ""                       # 给老师看的提示
    flagged: bool = False
    tries: int = 0                       # 这一句一共试了几次
    met: Optional[bool] = None           # 「完美」「一模一样」档：有没有达到严格标准
    #: 这一句实际用的模型（生成时按正在用的模型文件检测的）：{"name": "V4" / None, "how", "files"}；
    #: 生成的文件名最后的「_模型名」按每一句的这个定（model_tag）
    model: Dict[str, Any] = field(default_factory=dict)
    #: 「一模一样」才有：用了哪种组合（arm）、每种组合试了几个（arms）、这一句的搜索记录（search）、整篇再挑一遍换没换（dp）
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrationResult:
    audio_path: Path
    srt_path: Optional[Path]
    report_path: Path
    duration: float
    segments: List[Dict[str, Any]]
    warnings: List[str]
    flagged: List[int] = field(default_factory=list)       # 有问题的句子编号（从 1 开始，和结果表的 # 一样）
    variants: List[Dict[str, Any]] = field(default_factory=list)  # 「完美」「一模一样」档的两个版本
    quality: str = ""
    overall_pct: Optional[float] = None                    # 整篇的像你本人（%），按时长加权
    notes: List[str] = field(default_factory=list)         # 中文小结


@dataclass
class _Plan:
    ref: Dict[str, Any]
    aux: List[Dict[str, Any]]
    speed: float
    key: str
    wav_path: Path
    meta_path: Path
    # 下面几项只有「一模一样」才有（synth/search.py）：这句话挑的几条参考录音、每条的辅助参考、第 1 轮的组合、
    # 留下来的版本存在哪（pool_key：和 key 一样，只是不算排序权重——权重变了时不用显卡、按新权重重新排）
    refs: List[Dict[str, Any]] = field(default_factory=list)
    aux_by_ref: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    arms: List[Any] = field(default_factory=list)
    pool_key: str = ""

    @property
    def cached(self) -> bool:
        return self.wav_path.exists() and self.meta_path.exists()


@dataclass
class _Cand:
    score: Score
    seed: int
    wav: np.ndarray
    sr: int
    round: int
    k: int


#: 「一模一样」每句记录里带到结果（SegmentResult.extra）和报告里的几项
EXTRA_KEYS = ("arm", "arms", "search", "dp", "chosen", "profile_sig", "weights_version")
#: 按字幕时间轴配音时，句子之间至少留的绝对静音（秒）：逗号处 / 句子之间
TIMED_MIN_CLAUSE_GAP = 0.08
TIMED_MIN_GAP = 0.15

# ---------------------------------------------------------------- 「一模一样」拼接（设计方案 §1.9）
#: 切首尾：比语音低 45 dB、比底噪高 12 dB、不低于 −70 dBFS（以底噪为准，句尾自然衰减的尾音多留一些）；句首留 30 毫秒，
#: 句尾留你本人句尾收音的中位数（限制在 30~120 毫秒）；整段没有一处比底噪高 12 dB、频谱又像噪声（只有嘶嘶声）时切成空的
ID_TRIM = {"pad_ms": 30.0, "drop_db": 45.0, "floor_db": 12.0, "abs_floor_db": -70.0, "min_range_db": 12.0}
ID_TAIL_PAD = (30.0, 120.0)
#: 打分时两边各补 0.3 秒的数字静音（只用来分析，不进最后的音频）
ANALYSIS_PAD = 0.3
#: 整篇再挑一遍：前后两句音调（半音）、语速（ln）、音色（1 − 余弦）的变化和你本人比，每一项 0.03 × min(z², 9)
DP_WEIGHT = 0.03
DP_ZCAP = 9.0
#: 停顿：你本人停顿分布的 u 分位，u 在 0.2~0.8 之间随机（段落之间 0.85~0.97）；少于 8 个时按以前的方法
PAUSE_U = (0.2, 0.8)
PARA_U = (0.85, 0.97)
#: 停顿量了再改：每次最多改 ±0.15 秒，两句之间的数字静音至少 0.08 秒，量两遍改两遍
FIT_STEP = 0.15
FIT_MIN_GAP = 0.08
FIT_PASSES = 2
#: 一句话里说话部分的底噪（有声音的那一段里逐帧电平的 p10）高于这个才做去杂音；不高于时 B 版本这一句和 A 一模一样
DENOISE_FLOOR_DB = -60.0
#: 每句音量调好以后，哪一句的最高点超过 −1 dBFS 就把这一句单独调低（不用限幅器，不整篇压）
PEAK_CEILING_DB = -1.0


def model_tag(models: Sequence[Dict[str, Any]], weights: Optional[Sequence[float]] = None) -> str:
    """生成的文件名最后的模型名（老师的规定：按实际用的模型，写文件那一刻定）：每一句实际用的模型（SegmentResult.model），
    用了几种就按用得多少（这几句的总时长，一样时按句数）排、用「和」连起来（「V4和v2ProPlus」，不用「+」这类符号）；
    检测不出来的那几句写「模型未知」（绝不猜）。只留汉字、英文字母、数字。"""
    from voicetwin.backends.base import MODEL_UNKNOWN

    use: Dict[str, List[float]] = {}
    for k, m in enumerate(models):
        name = str((m or {}).get("name") or "")
        name = re.sub(r"[^一-鿿A-Za-z0-9]", "", name) or MODEL_UNKNOWN
        w = float(weights[k]) if weights is not None and k < len(weights) else 1.0
        row = use.setdefault(name, [0.0, 0.0])
        row[0] += w
        row[1] += 1
    if not use:
        return MODEL_UNKNOWN
    return "和".join(n for n, _ in sorted(use.items(), key=lambda kv: (-kv[1][0], -kv[1][1], kv[0])))


def models_used(results: Sequence["SegmentResult"]) -> List[Dict[str, Any]]:
    """这一篇用了哪些模型：[{"name", "sentences", "seconds", "files", "how"}]，用得多的在前（报告用）。"""
    from voicetwin.backends.base import MODEL_UNKNOWN

    rows: Dict[str, Dict[str, Any]] = {}
    for r in results:
        m = r.model or {}
        name = re.sub(r"[^一-鿿A-Za-z0-9]", "", str(m.get("name") or "")) or MODEL_UNKNOWN
        row = rows.setdefault(name, {"name": name, "sentences": 0, "seconds": 0.0, "files": [],
                                     "how": m.get("how", "")})
        row["sentences"] += 1
        row["seconds"] = round(row["seconds"] + len(r.wav) / max(r.sr, 1), 2)
        for f in m.get("files") or []:
            if f not in row["files"]:
                row["files"].append(f)
    return sorted(rows.values(), key=lambda d: (-d["seconds"], -d["sentences"], d["name"]))


def out_parts(out_path: Union[str, Path], default_fmt: str = "wav") -> Tuple[Path, str, str]:
    """输出路径 → (文件夹, 名字, 扩展名)。名字按老师的规定只留汉字、英文字母、数字、下划线（file_stem）；
    扩展名只认 .wav / .mp3 / .m4a / .flac：「第1.2课」这种没写扩展名、里面有点的名字，「.2课」不是扩展名
    （不能用 Path.with_suffix 改：会把「.2课」当扩展名换掉），整个都是名字，扩展名按设置。"""
    from voicetwin.utils.textutil import file_stem

    p = Path(out_path)
    name, ext = p.name, p.suffix.lower()
    if ext in (".wav", ".mp3", ".m4a", ".flac"):
        name = name[: -len(p.suffix)]
    else:
        ext = "." + (str(default_fmt or "wav").lower().lstrip(".") or "wav")
        if ext not in (".wav", ".mp3", ".m4a", ".flac"):
            ext = ".wav"
    return p.parent, file_stem(name, 60), ext

class Narrator:
    def __init__(self, cfg: Dict[str, Any], project: Project, backend: Backend, quality: Optional[str] = None,
                 candidates: Optional[int] = None, speed: Union[str, float, None] = None, reference: str = "",
                 asr_check: Optional[bool] = None, progress: Optional[ProgressFn] = None,
                 variants: Optional[bool] = None, tier: Optional[str] = None):
        self.cfg = cfg
        self.scfg: Dict[str, Any] = dict(cfg.get("synth", {}) or {})
        self.project = project
        self.backend = backend
        self._tier = tier
        self.quality = resolve_quality(quality if quality not in (None, "") else self.scfg.get("quality", "auto"),
                                       tier=tier)
        tiers_cfg = self.scfg.get("tiers") or {}
        qcfg = tiers_cfg.get(self.quality) if isinstance(tiers_cfg, dict) else None
        qcfg = qcfg if isinstance(qcfg, dict) else {}
        preset = tier_preset(self.quality, self.scfg)
        if self.quality in ("balanced", "best"):  # 老配置里的全局项只管这两档
            if self.scfg.get("cer_retry_threshold") not in (None, "auto"):
                thr = float(self.scfg["cer_retry_threshold"])
                if self.quality == "balanced" or thr != 0.15:
                    preset["cer_retry_threshold"] = {"strong": thr, "weak": thr}
            if self.scfg.get("max_retries") not in (None, "auto"):
                preset["retry_rounds"] = int(self.scfg["max_retries"])
        self.preset = preset
        self.notes: List[str] = []
        low = preset.get("low_tier_candidates") is not None or preset.get("low_tier_max_candidates") is not None
        is_low = low and self.tier == "low"
        cand_cfg = candidates if candidates is not None else self.scfg.get("candidates", "auto")
        n = preset.get("low_tier_candidates") if (is_low and preset.get("low_tier_candidates")) else preset["candidates"]
        self.n_candidates = max(1, int(n if cand_cfg in (None, "auto", 0, "0") else cand_cfg))
        self.adaptive = bool(preset.get("adaptive"))
        cap = preset.get("low_tier_max_candidates") if (is_low and preset.get("low_tier_max_candidates")) \
            else preset.get("max_candidates", self.n_candidates)
        if isinstance(cap, dict):  # 按显卡分档的写法（「一模一样」）：下面 _init_identical 再按显卡取
            cap = None
        self.max_candidates = max(self.n_candidates, int(cap or self.n_candidates))
        if is_low and self.quality in ("max", "perfect"):
            self.notes.append("显存较小，已减少候选数（每句最多试 "
                              f"{self.max_candidates if self.adaptive else self.n_candidates} 次）")
            log.info(self.notes[-1])
        self.min_candidates = self.n_candidates  # 每句至少试几个（只有「一模一样」和每批的个数不一样）
        self.R = 1                               # 每句用几条参考录音（「一模一样」以后的步骤才用到多条）
        self.search_target: Any = None           # 「一模一样」：继续找的目标 / 算达标的标准（见 _sim_target）
        self.pass_target: Any = None
        self.plateau, self.plateau_eps = 0, 0.0  # 「一模一样」：最近几个版本的最高分涨不到多少就算「再试也不更好」
        if self.quality == "identical":
            self._init_identical(preset, candidates)
        asr_cfg = asr_check if asr_check is not None else self.scfg.get("asr_check", "auto")
        if preset.get("force_asr") and asr_cfg is not False:
            self.use_asr = True
        else:
            self.use_asr = bool(preset["asr"]) if asr_cfg in (None, "auto") else bool(asr_cfg)
        self.min_wrong = int(preset.get("min_wrong_chars", self.scfg.get("min_wrong_chars", 2)) or 0)
        self.want_variants = bool(preset.get("variants")) if variants is None else bool(variants)
        self.speed_opt = speed if speed is not None else self.scfg.get("speed", "auto")
        self.reference = reference
        self.progress = progress
        self.profile = project.load_profile()
        self.refs = project.load_references()
        self.warnings: List[str] = []
        self._scorer: Optional[Scorer] = None
        self._judge: Optional[SimilarityJudge] = None
        self._checker: Optional[CERChecker] = None
        self._started = False
        self._pos: Tuple[int, int] = (0, 1)
        self._gen_range: Tuple[float, float] = (0.03, 0.95)
        self.base_seed = int(self.scfg.get("seed", 20240601))
        #: 「一模一样」：你本人的说话习惯、参考录音库、models.json 里的 identical 设置（_identical_ctx）；
        #: 每次同时生成几个（_batch_tuner）；每段话的第一句是第几句（挑参考时用）
        self._identical: Optional[Dict[str, Any]] = None
        self._tuner: Any = None
        self._search: Any = None
        self._para_first: Optional[set] = None
        self._judge_device_done = False
        #: 不能拿来当参考的录音（片段 id）：盲听测试里当「真人」播放的那几段（「一模一样」从参考录音库挑参考，
        #: 只改 self.refs 管不到库；见 _load_identical）
        self.exclude_refs: set = set()
        sim_cfg = dict(cfg.get("similarity", {}) or {})
        self.min_pct = float(sim_cfg.get("min_pct", 85) or 85)
        self.filter_mode = str(sim_cfg.get("filter", "auto") or "auto").lower()
        # 「完美」档的目标：synth.tiers.<档位>.target_pct 优先，其次 similarity.target_pct（配置文件里写着的那个），
        # 都没写（或写 auto）才用档位自带的 99。
        # 「一模一样」不看 similarity.target_pct（每个人的 config.yaml 里都抄着 99）：它的目标是相对你自己真实录音的水平，
        # 只认 synth.tiers.identical.search_target / pass_target（见 _sim_target）；没有精准声纹打分时和「完美」一样用 99
        tier_target = qcfg.get("target_pct")
        if self.quality == "identical":
            target: Any = 99
        elif tier_target not in (None, "auto", ""):
            target = tier_target
        elif sim_cfg.get("target_pct") not in (None, "auto", ""):
            target = sim_cfg.get("target_pct")
        else:
            target = preset.get("target_pct", 99)
        try:
            self.target_pct = float(target) if float(target) > 0 else 99.0
        except (TypeError, ValueError):
            self.target_pct = 99.0

    def _init_identical(self, preset: Dict[str, Any], candidates: Any) -> None:
        """「一模一样」：每批几个、每句至少 / 最多试几个、几条参考录音都按显卡分档（见 identical_limits）。
        只有命令行明确写的 -n 改每句最多试几个。config.yaml 里的 synth.candidates 是给其它档位的：以前为「均衡」「完美」
        手改过的值不能悄悄把「一模一样」限制成每句只试几个（网页的「生成」从来不传 -n），用不上时说一声。"""
        tier = self.tier
        self.n_candidates, self.min_candidates, self.max_candidates, self.R = identical_limits(preset, tier, candidates)
        cap = self.max_candidates
        self.search_target = preset.get("search_target", "p50")
        self.pass_target = preset.get("pass_target", "p25")
        self.plateau = max(0, int(preset.get("plateau", 0) or 0))
        self.plateau_eps = float(preset.get("plateau_eps", 0.0) or 0.0)
        n0 = len(self.notes)
        if tier == "low":
            self.notes.append(f"显存较小，已减少每句试的版本数（每句至少 {self.min_candidates} 个、最多 {cap} 个）")
        elif tier == "none":
            self.notes.append(f"没有检测到能用的 N 卡（NVIDIA 显卡），用处理器生成：每句至少试 {self.min_candidates} 个、"
                              f"最多 {cap} 个版本，会非常慢；着急的话可以改选「均衡」")
        old = self.scfg.get("candidates", "auto")
        if candidates is None and old not in (None, "auto", 0, "0", ""):
            self.notes.append(f"设置文件 config.yaml 里的「candidates: {old}」不管「一模一样」（这次每句至少试 "
                              f"{self.min_candidates} 个、最多 {cap} 个）；要限制「一模一样」每句最多试几个，"
                              "改 synth.tiers.identical.max_candidates，或者命令行加 -n")
        for line in self.notes[n0:]:
            log.info(line)

    # ------------------------------------------------------------------ 显卡档位
    @property
    def tier(self) -> str:
        if self._tier is None:
            self._tier = _vram_tier()
        return self._tier

    # ------------------------------------------------------------------ 打分器
    @property
    def judge(self) -> Optional[SimilarityJudge]:
        self.scorer  # noqa: B018 - 触发加载
        return self._judge

    @property
    def scorer(self) -> Scorer:
        if self._scorer is None:
            judge = None
            try:
                judge = SimilarityJudge.for_project(self.cfg, self.project)
            except Exception as exc:
                log.warning(f"声纹打分不可用：{exc}")
            encoder, cen = None, None
            if judge is None or not judge.available:
                try:
                    encoder = get_speaker_encoder(self.cfg.get("speaker_encoder", "auto"))
                    cen = voice_centroid(self.project, encoder)
                except Exception as exc:
                    log.warning(f"声纹打分不可用：{exc}")
            self._judge = judge if (judge is not None and judge.available) else None
            if self.use_asr:
                self._checker = CERChecker(self.scfg.get("asr_check_model", "auto"), progress=self.progress,
                                           vram_tier=self.tier, gsv_root=gsv_root_from_cfg(self.cfg),
                                           progress_range=(0.02, 0.03))
            if self.quality == "identical":
                from voicetwin.eval.identical_judge import IdenticalScorer

                ctx = self._identical_ctx()
                self._scorer = IdenticalScorer(self.profile, cen, encoder, self.scfg.get("score"), self._checker,
                                               judge=self._judge, twin=ctx.get("twin"),
                                               rank_weights=ctx.get("weights"))
                release = getattr(self._checker, "release_gpu", None)
                if callable(release):
                    # 一次只生成一个也显存不够时，合成引擎先请识别校验模型让出显卡再试一次（返回有没有真的让出）
                    self.backend.release_gpu_callback = release
            else:
                self._scorer = Scorer(self.profile, cen, encoder, self.scfg.get("score"), self._checker,
                                      judge=self._judge)
            if self._judge is not None:
                log.info("声纹打分模型：" + "、".join(self._judge.info()["labels"]) + f"（{PCT_HELP}）")
        return self._scorer

    @property
    def sim_filter(self) -> bool:
        """要不要按"像你本人"淘汰候选（< 85%）。auto：有正经声纹模型并且校准成功时才淘汰。"""
        judge = self.judge
        if judge is None or not judge.calibrated or self.filter_mode in ("off", "false", "0", "no"):
            return False
        if self.filter_mode in ("on", "true", "1", "yes"):
            return True
        return judge.reliable

    def _cer_strong(self, c: Optional["_Cand"], lang: str, text: str = "") -> bool:
        """这个候选是用"准"的识别模型检查的吗（Paraformer / Whisper large）？准的模型用更严的门槛。"""
        if c is not None and c.score.checker:
            return engine_is_strong(c.score.checker)
        return bool(self._checker is not None and self._checker.strong(lang, text))

    def _thr(self, key: str, lang: str, default: float, c: Optional["_Cand"] = None) -> float:
        val = self.preset.get(key)
        if isinstance(val, dict):
            return float(val.get("strong" if self._cer_strong(c, lang) else "weak", default))
        return float(val) if isinstance(val, (int, float)) else default

    # ------------------------------------------------------------------ 工具
    def _speed_multiplier(self) -> float:
        """用户额外指定的快慢倍数（auto = 1.0，即完全按你本人的语速）。>1 更快，<1 更慢。"""
        opt = self.speed_opt
        if opt in (None, "auto", ""):
            return 1.0
        try:
            val = float(opt)
        except (TypeError, ValueError):
            return 1.0
        return float(min(2.0, max(0.5, val))) if math.isfinite(val) and val > 0 else 1.0

    def _speed_for(self, lang: str) -> float:
        """最终传给引擎的语速 = 自动校准系数 × 用户倍数（由模型自己控制时长，不改音高音色）。
        「一模一样」：挑模型时按「一模一样」的方式校准过（models.json 里的 identical.speed）就用它。"""
        cal = self.backend.speed_calibration()
        if self.quality == "identical":
            own = (self._identical_ctx().get("block") or {}).get("speed")
            if isinstance(own, dict) and own:
                cal = own
        val = float(cal.get(lang, cal.get("zh", 1.0)) or 1.0) * self._speed_multiplier()
        return float(min(2.0, max(0.5, val)))

    def _progress(self, frac: float, msg: str) -> None:
        if self.progress:
            try:
                self.progress(max(0.0, min(1.0, frac)), msg)
            except Exception:
                pass

    def _cache_paths(self, key: str) -> Tuple[Path, Path]:
        d = self.project.cache_dir / "segments" / key[:2]
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{key}.wav", d / f"{key}.json"

    def _n_aux(self) -> int:
        if self.preset.get("aux_refs") is not None:
            if self.tier == "low" and self.preset.get("low_tier_aux_refs") is not None:
                return int(self.preset["low_tier_aux_refs"])
            return int(self.preset["aux_refs"])
        return int((self.backend.bcfg.get("infer") or {}).get("aux_refs", 0) or 0)

    def _ref_for(self, seg: ScriptSegment) -> Dict[str, Any]:
        if self.reference or not self.preset.get("match_reference"):
            return pick_reference(self.refs, seg.lang, seg.kind, self.reference)
        # 「完美」「一模一样」：同语言、同句型里，挑字数和这句话最接近的参考（同样接近时挑分数高的）
        same_lang = [r for r in self.refs if r.get("lang") == seg.lang] or list(self.refs)
        pool = [r for r in same_lang if r.get("kind") == seg.kind] or \
            [r for r in same_lang if r.get("kind") == "statement"] or same_lang
        if not pool:
            return pick_reference(self.refs, seg.lang, seg.kind)
        n = syllable_count(seg.text) + 1
        return min(enumerate(pool), key=lambda p: (round(abs(math.log((syllable_count(p[1].get("text", "")) + 1) / n)), 1),
                                                   p[0]))[1]

    def _tier_sig(self) -> List[Any]:
        sig = [self.quality, self.n_candidates, self.max_candidates, self.use_asr, self.adaptive, self.min_wrong,
               self.min_pct, self.filter_mode, self.target_pct,
               {k: self.preset.get(k) for k in ("cer_retry_threshold", "cer_target", "retry_rounds", "retry_candidates",
                                                "early_after", "early_pct")}]
        if self.quality == "identical":  # 只加在「一模一样」后面：其它档位的缓存键一个字节都不变
            sig.append([self.min_candidates, self.search_target, self.pass_target, self.plateau, self.plateau_eps])
        return sig

    def _plan(self, seg: ScriptSegment) -> _Plan:
        if self.quality == "identical":
            return self._plan_identical(seg)
        ref = self._ref_for(seg)
        aux = aux_references(self.refs, ref, self._n_aux())
        if not self.backend.supports_aux_refs:
            aux = []
        speed = self._speed_for(seg.lang)
        # 参考音频的文字也算进去：老师在校对表里改了这条参考的文字以后，不能再用改之前生成的缓存
        parts: List[Any] = [CACHE_VERSION, self.backend.model_id(), seg.text, seg.lang, ref["id"], ref.get("text", ""),
                            [a["id"] for a in aux], round(speed, 3), self._tier_sig(), self.base_seed]
        lang_eff = send_lang(seg.text, seg.lang)
        if lang_eff != seg.lang:
            # 英文单词多、以前按 en 发给引擎的中文句子（里面的汉字被丢掉了）：现在按 zh 发，旧缓存不能再用。
            # 只有这种句子的缓存键变了，其它句子一个字节都不变，以前生成好的照常直接用
            parts.append(lang_eff)
        ref_lang = ref.get("lang")
        prompt_lang = send_lang(ref.get("text", ""), ref_lang)
        if prompt_lang != ("en" if ref_lang == "en" else "zh"):
            # 参考音频也一样：标成 en、文字里却有汉字时，prompt_lang 以前发 en（参考文字里的汉字被丢掉），现在发 zh，
            # 发给引擎的请求变了，旧缓存不能再用；只有用这种参考的句子缓存键变了
            parts.append(f"prompt_lang={prompt_lang}")
        key = short_hash(*parts, n=16)
        wav_path, meta_path = self._cache_paths(key)
        return _Plan(ref, aux, speed, key, wav_path, meta_path)

    # ------------------------------------------------------------------ 「一模一样」
    def _identical_ctx(self) -> Dict[str, Any]:
        """「一模一样」要用的东西（第一次用到时准备，见 _load_identical）。"""
        if self._identical is None:
            self._identical = self._load_identical()
        return self._identical

    def _load_identical(self, report: bool = False) -> Dict[str, Any]:
        """「一模一样」要用的东西：你本人的说话习惯（twin_profile.json）、参考录音库（refs_bank.json）、
        models.json 里挑模型时按「一模一样」校准过的设置（identical：语速、排序权重、试听参考录音的结果，P8 写）。
        素材没变时几乎不花时间；第一次要把你的录音量一遍。量不出来的项目按以前的方式（没测出来就不用）。
        参考录音库：以前没有、或者是这里（不带声纹）整理的，就重新整理一遍（几毫秒到一两秒）；带声纹的库由
        「准备「一模一样」」（P8）负责更新，这里不动它，只用里面现在还能用的录音。"""
        from voicetwin.data.references import (bank_eligible, bank_signature, build_reference_bank,
                                               load_reference_bank)
        from voicetwin.style.twin_profile import build_twin_profile, load_twin_profile
        from voicetwin.synth import search as S

        twin = None
        lo = self._gen_range[0]
        try:
            if report:
                self._progress(min(0.02, lo), "准备「一模一样」：测量你的说话习惯（停顿、音调、语速）……")
            twin = build_twin_profile(self.project)
        except Exception as exc:  # noqa: BLE001 - 停止按钮不是 Exception，照常传出去
            log.warning(f"你本人的说话习惯这次没量出来（{exc}），语速按以前的方式比")
        if twin is None:
            twin = load_twin_profile(self.project)
        records: List[Dict[str, Any]] = []
        bank = None
        try:
            records = self.project.load_manifest()
            bank = load_reference_bank(self.project)
            if bank is None or not bank.get("judge_models"):
                if report:
                    self._progress(min(0.05, lo), "准备「一模一样」：整理参考录音……")
                build_reference_bank(self.project, records)
                bank = load_reference_bank(self.project)
        except Exception as exc:  # noqa: BLE001
            log.warning(f"参考录音库这次没整理好（{exc}），用以前挑好的参考录音")
        by_id = {str(r.get("id")): r for r in records}
        # 不能当参考的录音（盲听测试的「真人」录音）不进挑参考的范围；指纹按剩下的录音算，缓存键跟着变
        # （以前用它们当参考生成好的不能拿来用）
        skip = {str(x) for x in (self.exclude_refs or ())}
        pool = []
        for e in S.pool_from_bank(bank):  # 库里现在还能用的录音（片段还在、还用来训练、文字没改过）
            r = by_id.get(str(e["id"]))
            if (r is not None and str(e["id"]) not in skip and bank_eligible(r)
                    and str(r.get("text") or "").strip() == e["text"]):
                pool.append(e)
        bank_sig = bank_signature(pool) if pool else ""
        if not pool:
            # 全都不能用时照旧用 references.json（和 build_blind_test 里 refs 的兜底一样）
            pool = S.pool_from_refs([r for r in self.refs if str(r.get("id")) not in skip] or self.refs)
            bank_sig = S.pool_signature(pool)
        block: Dict[str, Any] = {}
        try:
            got = (self.project.load_models().get(self.backend.name) or {}).get("identical")
            block = got if isinstance(got, dict) else {}
        except Exception:  # noqa: BLE001
            block = {}
        audition = block.get("ref_prior") if isinstance(block.get("ref_prior"), dict) else None
        weights = block.get("weights") if isinstance(block.get("weights"), dict) else {}
        n_bank = sum(1 for e in pool if e.get("_bank"))
        if report:
            log.info(f"「一模一样」：参考录音 {len(pool)} 条" + ("（参考录音库）" if n_bank else "（还没有参考录音库，"
                                                              "用以前挑好的参考录音）"))
        return {"twin": twin or {}, "bank": bank, "pool": pool, "bank_sig": bank_sig,
                "prior": S.prior_scores(pool, audition),
                "prior_version": str(block.get("ref_prior_version") or "") if audition else "",
                "weights": weights, "weights_version": str(block.get("weights_version") or "default"),
                "block": block, "profile_sig": str((twin or {}).get("signature") or "")}

    def _para_initial(self, seg: ScriptSegment) -> bool:
        """这句话是不是一段话的开头（挑参考录音时，段落开头的语气用段落开头的录音更像）。"""
        if self._para_first is not None:
            return seg.index in self._para_first
        return seg.index == 0

    def _batch_tuner(self) -> Any:
        """每次同时生成几个（按实测速度选，整个生成过程只选一次；config.yaml 里写了每批几个就照写的）。"""
        if self._tuner is None:
            from voicetwin.synth.search import BatchTuner

            tiers = self.scfg.get("tiers") if isinstance(self.scfg.get("tiers"), dict) else {}
            own = tiers.get("identical") if isinstance(tiers.get("identical"), dict) else {}
            fixed = own.get("batch") not in (None, "auto", "")
            self._tuner = BatchTuner(self.n_candidates,
                                     enabled=bool(getattr(self.backend, "supports_batch", False)) and not fixed)
        return self._tuner

    def _search_obj(self) -> Any:
        if self._search is None:
            from voicetwin.synth.search import IdenticalSearch

            self._search = IdenticalSearch(self)
        return self._search

    def _arm_sig(self, refs: List[Dict[str, Any]], aux_by_ref: Dict[str, List[Dict[str, Any]]], arms: List[Any]) -> str:
        """「一模一样」怎么找的设置（缓存键用）：第 1 轮的组合、参考和辅助参考、生成设置、门槛和目标、打分分几步。
        每次同时生成几个不算在里面（只影响快慢，不影响找出来的结果是什么样的）。"""
        keys = ("presets", "rescue_preset", "aux_options", "cer_retry_threshold", "cer_target", "search_target",
                "pass_target", "member_floor", "full_score_top", "full_score_max", "refine_tempo")
        return short_hash([(a.ref_id, a.preset_idx, a.aux_n, a.speed_mult, a.ckpt) for a in arms],
                          [(r["id"], r.get("text", ""), [a["id"] for a in aux_by_ref.get(str(r["id"])) or []])
                           for r in refs],
                          {k: self.preset.get(k) for k in keys}, self.search_target, self.pass_target, self.R,
                          self.use_asr, self.min_wrong, self.min_pct, self.filter_mode, n=12)

    def _plan_identical(self, seg: ScriptSegment) -> _Plan:
        """「一模一样」：这句话挑哪几条参考录音、每条配哪几条辅助参考、第 1 轮试哪些组合，以及缓存键：
        模型、文字、发给引擎的语言、参考录音库、试听结果的版本、怎么找的设置、排序权重的版本、
        每句至少 / 最多试几个和「再试也不更好」的标准、语速、种子（设计方案 §2 P5）。"""
        from voicetwin.synth import search as S

        ctx = self._identical_ctx()
        pool = ctx["pool"]
        forced = S.find_forced(self.reference, pool, self.refs)
        refs = S.shortlist_refs(seg, pool, ctx["prior"], self.R, forced=forced, para_initial=self._para_initial(seg))
        if not refs:  # 能用的参考录音的文字都和这句话一样：和以前一样从 references.json 挑
            refs = S.pool_from_refs([self._ref_for(seg)])
        n_aux = self._n_aux() if self.backend.supports_aux_refs else 0
        aux_by_ref = {str(r["id"]): S.aux_set(r, pool, ctx["prior"], n_aux) for r in refs}
        presets = [p for p in (self.preset.get("presets") or []) if isinstance(p, dict)]
        arms = S.plan_arms(self.tier, refs, aux_by_ref, n_presets=max(1, len(presets)),
                           aux_options=self.preset.get("aux_options") or (3, 0))
        if not arms:
            arms = [S.Arm(str(refs[0]["id"]), 0, 0)]
        speed = self._speed_for(seg.lang)
        common = ["i1", sorted([self.backend.model_id()]), seg.text, send_lang(seg.text, seg.lang), ctx["bank_sig"],
                  ctx["prior_version"], self._arm_sig(refs, aux_by_ref, arms)]
        tail = [(self.min_candidates, self.max_candidates, self.plateau, self.plateau_eps), round(speed, 3),
                self.base_seed]
        key = short_hash(*common, ctx["weights_version"], *tail, n=16)
        pool_key = short_hash(*common, "pool", *tail, n=16)
        wav_path, meta_path = self._cache_paths(key)
        main = refs[0]
        return _Plan(main, (aux_by_ref.get(str(main["id"])) or [])[:arms[0].aux_n], speed, key, wav_path, meta_path,
                     refs=refs, aux_by_ref=aux_by_ref, arms=arms, pool_key=pool_key)

    def _tail_pad_ms(self) -> Optional[float]:
        """「一模一样」句尾留多少：你本人句尾收音（从比最响处低 30 dB 到底噪）的中位数，限制在 30~120 毫秒；
        没量出来时 None（和句首一样留 30 毫秒）。"""
        twin = (self._identical_ctx() or {}).get("twin") or {}
        try:
            val = float(((twin.get("edges") or {}).get("offset_ms") or {}).get("median"))
        except (TypeError, ValueError):
            return None
        if not math.isfinite(val):
            return None
        return float(min(ID_TAIL_PAD[1], max(ID_TAIL_PAD[0], val)))

    def _trim(self, wav: np.ndarray, sr: int) -> np.ndarray:
        """这一句最后放进音频里的样子（去首尾、淡入淡出，第一个和最后一个采样是 0）。
        「一模一样」按底噪切（ID_TRIM，句尾留你本人的收音长度）；其它档位和以前一样。"""
        if self.quality != "identical":
            return trim_edges(wav, sr)
        return trim_edges(wav, sr, tail_pad_ms=self._tail_pad_ms(), **ID_TRIM)

    def _analysis(self, wav: np.ndarray, sr: int) -> np.ndarray:
        """「一模一样」打分用的声音：就是最后放进音频里的那一段（_trim），两边各补 0.3 秒的数字静音（只用来分析：
        量说话时长、底噪要有静音做参照）。切完是空的（整段只有底噪）时用引擎原样的声音打分——这种版本反正不会被挑中
        （_best_nonempty）。同一段声音每次算出来一模一样，所以重新排名时和当时的分数对得上。"""
        return self._analysis_pair(wav, sr)[0]

    def _analysis_pair(self, wav: np.ndarray, sr: int) -> Tuple[np.ndarray, bool]:
        """(_analysis 的结果, 去首尾以后是不是空的)。"""
        out = self._trim(wav, sr)
        if out.size == 0:
            return np.asarray(wav, dtype=np.float32), True
        pad = np.zeros(int(round(ANALYSIS_PAD * sr)), dtype=np.float32)
        return np.concatenate([pad, out, pad]), False

    def _identical_ok(self, s: Score) -> bool:
        """「一模一样」达标的另外两条：时长在你平时的波动范围里（±2 个标准差），每个声纹模型都不低于它自己给你
        真实录音打的 p10（精准打分时才查）。"""
        if s.dur_z is not None and abs(float(s.dur_z)) > 2.0:
            return False
        if not self.sim_filter:
            return True
        floor = str(self.preset.get("member_floor") or "p10").strip().lower()
        fn = getattr(self.scorer, "member_floor_ok", None)
        return bool(fn(s, "g" + floor[1:])) if callable(fn) and floor.startswith("p") else True

    def _ensure_started(self, frac: Optional[float] = None) -> None:
        if self._started:
            return
        if frac is None:
            i, n = self._pos
            frac = self._gen_range[0] + (self._gen_range[1] - self._gen_range[0]) * i / max(n, 1)
        hint = getattr(self.backend, "start_hint", lambda: "")()
        self._progress(frac, "启动合成引擎" + (f"（{hint}）" if hint else "") + "……")
        self.backend.start()  # 已经在运行的服务也要调用：它会切换到这个声音的模型
        self._started = True

    def _warm_up(self, segments: Iterable[ScriptSegment]) -> None:
        """提前加载打分模型（第一次使用会下载），这样进度条能显示在做什么。"""
        self.scorer  # noqa: B018
        if self._checker is None:
            return
        need = {"paraformer" if self._checker.wants_paraformer(send_lang(s.text, s.lang), s.text) else "whisper"
                for s in segments}
        mixed = getattr(self._checker, "mixed_available", None)
        if self.quality == "identical" and callable(mixed) and any(
                count_cjk(s.text) and en_words(s.text) for s in segments) and mixed():
            need |= {"paraformer", "whisper"}  # 中文里夹着英文：中文用 Paraformer、英文单词用 Whisper 分开查
        for name in sorted(need):
            try:
                if name == "paraformer":
                    self._checker._load_paraformer()
                else:
                    self._checker._load()
            except Exception:
                pass

    # ------------------------------------------------------------------ 挑选
    def _cer_ok(self, c: _Cand, lang: str, thr: Optional[float] = None) -> bool:
        s = c.score
        if s.cer is None:
            return True
        if self.min_wrong > 1 and s.errors is not None and s.errors < self.min_wrong:
            return True  # 短句只错 1 个字（可能是识别误差）不算
        return s.cer <= (thr if thr is not None else self._thr("cer_retry_threshold", lang, 0.15, c))

    def _pct_ok(self, c: _Cand) -> bool:
        return not self.sim_filter or c.score.pct is None or c.score.pct >= self.min_pct

    def _select(self, cands: List[_Cand], lang: str, seg: Optional[ScriptSegment] = None) -> Tuple[_Cand, List[_Cand]]:
        alive = [c for c in cands if "几乎没有声音" not in c.score.issues] or cands
        survivors = [c for c in alive if self._pct_ok(c)]
        pool = survivors or alive
        # 读对的永远排在读错的前面；同一类里按综合分（相似度为主）。
        # 「完美」「一模一样」档（给了 seg）：达到全部严格标准的排在没达到的前面——综合分最高的不一定达标
        # （综合分里语速/音高偏差也要扣分），已经有达标的就要用达标的。
        if self.adaptive and seg is not None:
            best = max(pool, key=lambda c: (self._cer_ok(c, lang), self._meets_targets(c, seg), c.score.total))
        else:
            best = max(pool, key=lambda c: (self._cer_ok(c, lang), c.score.total))
        return best, survivors

    def _meets_targets(self, c: _Cand, seg: ScriptSegment, which: str = "pass") -> bool:
        """有没有达到全部严格标准。which：pass = 算不算达标；search = 「一模一样」继续找的目标（更高）。"""
        s = c.score
        lang = send_lang(seg.text, seg.lang)
        cer_ok = s.cer is None or s.cer <= self._thr("cer_target", lang, 0.05, c) or s.errors == 0
        pct_ok = s.pct is None or not self.sim_filter or self._pct_value(s) >= self._sim_target(which)
        ok = bool(cer_ok and pct_ok and "几乎没有声音" not in s.issues
                  and self.scorer.in_normal_range(s, lang, self._speed_multiplier()))
        if ok and self.quality == "identical":
            ok = self._identical_ok(s)
        return ok

    def _pct_value(self, s: Score) -> float:
        """和目标比的「像你本人」：「一模一样」用没封顶的值（目标可以是你自己录音的中位水平 100% 或更高）。"""
        if self.quality == "identical" and s.pct_raw is not None:
            return float(s.pct_raw)
        return float(s.pct) if s.pct is not None else 0.0

    def _sim_target(self, which: str = "pass") -> float:
        """「像你本人」要达到多少。其它档位：effective_target(target_pct)。
        「一模一样」：继续找到你自己真实录音的中位水平（p50 = 100%），不低于你自己录音的下四分位（p25）才算达标；
        写在 synth.tiers.identical.search_target / pass_target 里（p10 / p25 / p50 / p90，或者直接写百分比）。
        没有精准声纹打分（量不出你自己录音的范围）时，和「完美」一样用 99%。"""
        if self.quality != "identical":
            return self.effective_target(self.target_pct)
        spec = self.search_target if which == "search" else self.pass_target
        natural = getattr(self._judge, "natural_range", None)
        rng = natural() if callable(natural) else None
        text = str(spec if spec is not None else "").strip().lower()
        try:
            val = float(text.rstrip("%"))
        except ValueError:
            if not rng or not isinstance(rng.get(text), (int, float)):
                return float(self.target_pct)
            val = float(rng[text])
        return float(max(self.min_pct, val))

    def effective_target(self, target: float) -> float:
        """「像你本人」要达到多少才算达标：配置的目标（默认 99%），但不要求超过你自己真实录音的正常水平——
        精准打分时，你自己的真实录音本身就在一个范围里波动（例如 90%~110%），落在你自己录音的下四分位以上，
        声纹模型就分不出它和你的真实录音，算达标；无论如何不低于淘汰线（85%）。"""
        natural = getattr(self._judge, "natural_range", None)
        rng = natural() if callable(natural) else None
        if rng and isinstance(rng.get("p25"), (int, float)):
            return float(max(self.min_pct, min(target, float(rng["p25"]))))
        return float(target)

    def _target_miss(self, c: _Cand, seg: ScriptSegment) -> str:
        """「完美」「一模一样」档没达标时，按真正没达到的那一项写提示。"""
        s = c.score
        if self.sim_filter and s.pct is not None and self._pct_value(s) < self._sim_target("pass"):
            return "这一句可能不够像，建议重新生成或改写"
        lang = send_lang(seg.text, seg.lang)
        if s.cer is not None and not (s.cer <= self._thr("cer_target", lang, 0.05, c) or s.errors == 0):
            return "这一句可能有个别字读得不太准，建议重新生成或改写"
        if not self.scorer.in_normal_range(s, lang, self._speed_multiplier()):
            return "这一句的语速或音调和你平时不太一样，建议重新生成或改写"
        if self.quality == "identical" and s.dur_z is not None and abs(float(s.dur_z)) > 2.0:
            return "这一句的语速或音调和你平时不太一样，建议重新生成或改写"
        return "这一句可能不够像，建议重新生成或改写"

    def _clearly_good(self, c: _Cand, seg: ScriptSegment) -> bool:
        s = c.score
        thr = self._thr("cer_retry_threshold", send_lang(seg.text, seg.lang), 0.12, c)
        cer_ok = s.cer is None or s.cer <= thr / 2 or s.errors == 0
        pct_ok = s.pct is None or s.pct >= self.effective_target(float(self.preset.get("early_pct", 99.0)))
        return bool(cer_ok and pct_ok and "几乎没有声音" not in s.issues)

    def _retry_reason(self, cands: List[_Cand], seg: ScriptSegment) -> Optional[str]:
        if not cands:
            return "没生成成功"
        lang = send_lang(seg.text, seg.lang)
        best, survivors = self._select(cands, lang)
        if self.use_asr and not self._cer_ok(best, lang):
            hyp = f"，识别为：{best.score.hyp}" if best.score.hyp else ""
            return f"有字读错了（错字率 {best.score.cer:.0%}{hyp}）"
        if self.sim_filter and not survivors:
            return f"不够像（最好的只有 {best.score.pct:.1f}%，低于 {self.min_pct:.0f}%）"
        return None

    # ------------------------------------------------------------------ 单句
    def _load_cached(self, seg: ScriptSegment, plan: _Plan) -> SegmentResult:
        meta = json.loads(plan.meta_path.read_text(encoding="utf-8"))
        identical = self.quality == "identical"
        if identical and self._identical_stale(meta):
            # 打分标准 / 你的说话习惯 / 排序权重变了：留下来的几个版本按新标准重新排（只用处理器，不再生成）
            res = self._rerank(seg, plan, int(meta.get("tries", 0) or 0))
            if res is not None:
                return res
        wav, sr = load_audio(plan.wav_path)
        meta = self._rescore_cached(meta, wav, sr, plan)
        score = meta.get("score", {}) or {}
        ref_id = meta.get("ref") if identical and meta.get("ref") else plan.ref["id"]
        model = meta.get("model_info")
        if not isinstance(model, dict):
            # 这一版以前生成的句子没记模型名：缓存键里有模型的标识（model_id，含模型文件的大小和修改时间），
            # 能用上这个缓存就说明是现在这个模型生成的——按现在的模型文件检测（不是猜）
            model = self._model_info()
        extra = {k: meta[k] for k in EXTRA_KEYS if k in meta}
        return SegmentResult(seg, wav, sr, score, ref_id, True, meta.get("seed", 0), meta.get("candidates", []),
                             path=plan.wav_path, pct=score.get("pct"), status=meta.get("status", ""),
                             hint=meta.get("hint", ""), flagged=bool(meta.get("flagged")), tries=int(meta.get("tries", 0)),
                             met=meta.get("met"), model=dict(model), extra=extra)

    def _model_info(self) -> Dict[str, Any]:
        """这一刻实际用的模型（每句生成完马上记下：生成的文件名、文件里面的注释、报告都按它定）。
        检测出错时 name 是 None（文件名写「模型未知」，不猜）。"""
        fn = getattr(self.backend, "model_name_info", None)
        try:
            info = fn() if callable(fn) else None
        except Exception as exc:  # noqa: BLE001 - 读不出来就如实写「模型未知」
            info = {"name": None, "how": f"读模型文件出错（{str(exc)[:120]}）", "files": []}
        return dict(info or {"name": None, "how": "这个引擎读不出模型名", "files": []})

    def _judge_sig(self) -> str:
        sig = getattr(self.judge, "signature", None)
        return str(sig()) if callable(sig) else ""

    def _identical_stale(self, meta: Dict[str, Any]) -> bool:
        """「一模一样」以前生成好的这句：打分标准、你的说话习惯、排序权重有没有变（变了就按新标准重新排）。"""
        ctx = self._identical_ctx()
        return (meta.get("profile_sig", "") != ctx["profile_sig"] or meta.get("judge", "") != self._judge_sig()
                or meta.get("weights_version", "") != ctx["weights_version"])

    def _rerank(self, seg: ScriptSegment, plan: _Plan, tries: Optional[int] = None) -> Optional[SegmentResult]:
        """只用这句话留下来的几个版本、按现在的标准重新挑（不用显卡、不调用合成引擎）。没有留下的版本时返回 None。"""
        from voicetwin.synth.search import store_dir, store_info

        if tries is None:
            tries = int(store_info(store_dir(self.project.cache_dir, plan.pool_key)).get("tries", 0) or 0)
        try:
            out = self._search_obj().rerank(seg, plan, tries)
        except Exception as exc:  # noqa: BLE001 - 重新排不了：照旧用以前挑好的那个
            log.debug(f"第 {seg.index + 1} 句留下的版本重新排名失败：{exc}")
            return None
        if out is None:
            return None
        log.info(f"第 {seg.index + 1} 句：打分标准、说话习惯或排序权重变了，按新标准从留下的 {len(out.cands)} 个版本里"
                 "重新挑（不用重新生成）")
        return self._finish_identical(seg, plan, out, cached=True)

    def _finish_identical(self, seg: ScriptSegment, plan: _Plan, out: Any, cached: bool) -> SegmentResult:
        """「一模一样」挑好以后：写这句的声音和记录，再把最好的几个版本存下来（重新生成时一起比、标准变了时重新排）。"""
        from voicetwin.synth.search import store_candidates, store_dir

        ctx = self._identical_ctx()
        best = out.best
        extra = {"profile_sig": ctx["profile_sig"], "weights_version": ctx["weights_version"], "arm": best.arm.to_dict(),
                 "search": out.stats, "arms": out.arms,
                 # 挑出来的是留下来的版本里的哪一个（整篇再挑一遍时认出「现在用的这个」）
                 "chosen": {"seed": int(best.seed), "row": int(best.row), "speed": round(float(best.speed), 6)}}
        res = self._finish_segment(seg, plan, best, out.cands, out.tries, out.met, extra=extra,
                                   wav=self._trim(best.wav, best.sr), ref_id=best.arm.ref_id, cached=cached)
        k = max(1, int(self.preset.get("store_top_k", 6) or 6))
        # 挑出来的那个一定留下（排第一）：只留前 k 个时，差不多一样高按时长、音调挑出来的那个按综合分可能排不进去
        store_candidates(store_dir(self.project.cache_dir, plan.pool_key), out.keep or out.cands, k,
                         judge_sig=self._judge_sig(),
                         extra={"tries": out.tries, "text": seg.text, "model_info": res.model,
                                "scored_on": self._scored_on()})
        return res

    def _scored_on(self) -> str:
        """留下来的版本当时是按什么样的声音打的分（去首尾的设置）：不一样时不沿用存下来的声纹，重新算。"""
        return f"delivered|tail={self._tail_pad_ms()}|" + ",".join(f"{k}={v}" for k, v in sorted(ID_TRIM.items()))

    def _rescore_cached(self, meta: Dict[str, Any], wav: np.ndarray, sr: int, plan: _Plan) -> Dict[str, Any]:
        """以前生成好的句子：打分方式变了（例如升级到精准声纹打分、素材变了）时，只重新打"像你本人"这一项，
        声音不用重新生成。新旧两种百分比的标准不一样，混在一起会误导。"""
        sig = self._judge_sig()
        if not sig or meta.get("judge") == sig:
            return meta
        try:
            res = self.judge.judge(wav, sr)
        except Exception as exc:
            log.debug(f"重新打分失败：{exc}")
            return meta
        score = dict(meta.get("score") or {})
        for key in ("pct", "pct_raw", "pcts", "sims"):
            score[key] = res.get(key)
        if res.get("sim") is not None:
            score["speaker_sim"] = res.get("sim")
        hints = [h for h in str(meta.get("hint") or "").split("；") if h and "不够像" not in h and "低于" not in h]
        score["speech_seconds"] = res.get("seconds")
        pct = score.get("pct")
        filt = self.sim_filter
        short = bool(res.get("short"))
        hints = [h for h in hints if h != SHORT_HINT]
        if filt and pct is not None and pct < self.min_pct:
            hints.insert(0, SHORT_HINT if short else f"低于 {self.min_pct:.0f}%，建议重新生成或改写这一句")
        issues = list(score.get("issues") or [])
        if filt and pct is not None:
            status = status_for_pct(pct, self.min_pct)
            if status == "🔴" and short:
                status = "⚠️"
            if status != "🔴" and (hints or issues):
                status = "⚠️"
        else:
            status = "⚠️" if (hints or issues) else "✅"
        meta = dict(meta, score=score, hint="；".join(hints), status=status, flagged=bool(hints or issues), judge=sig)
        try:
            atomic.write_text(plan.meta_path, json.dumps(meta, ensure_ascii=False, indent=1))
        except OSError:
            pass
        return meta

    def synthesize_segment(self, seg: ScriptSegment, force: bool = False) -> SegmentResult:
        plan = self._plan(seg)
        if plan.cached and not force:
            try:
                return self._load_cached(seg, plan)
            except Exception as exc:  # noqa: BLE001 - 缓存坏了（写到一半关了窗口、断电）：重新生成这一句，不能一直失败
                log.warning(f"第 {seg.index + 1} 句的缓存读不了（{exc}），重新生成")
        if self.quality == "identical":
            return self._synthesize_identical(seg, plan, force)
        self._ensure_started()
        ref, aux, speed, key = plan.ref, plan.aux, plan.speed, plan.key
        seed0 = self.base_seed + seg.index * 7919
        if force:
            seed0 += random.randint(1, 10_000_000)
        tmp_dir = self.project.cache_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        cands: List[_Cand] = []
        state = {"tried": 0, "last_exc": None}
        i, total_n = self._pos
        lo, hi = self._gen_range
        expected = 8 if self.adaptive else self.n_candidates
        mult = self._speed_multiplier()
        lang = send_lang(seg.text, seg.lang)  # 打分、查错字按真正发给引擎的语言（有汉字就是 zh）
        ref_audio = self.project.abspath(ref["path"])
        aux_paths = [self.project.abspath(a["path"]) for a in aux]

        def attempt(r_i: int, k: int, sampling: Optional[Dict[str, Any]], msg: str) -> None:
            _check_cancel()
            seed = seed0 + (r_i * 101 + k) * 104729
            sampling = sampling or {}
            req = SynthRequest(text=seg.text, lang=seg.lang, ref_audio=ref_audio, ref_text=ref["text"],
                               ref_lang=ref["lang"], aux_refs=list(aux_paths), seed=seed, speed=speed,
                               temperature=sampling.get("temperature"), top_k=sampling.get("top_k"),
                               top_p=sampling.get("top_p"))
            out = tmp_dir / f"{key}_{r_i}_{k}.wav"
            wav: Optional[np.ndarray] = None
            sr = 0
            try:
                self.backend.synthesize(req, out)
                wav, sr = load_audio(out)
            except Exception as exc:
                state["last_exc"] = exc
                log.warning(f"  第 {seg.index + 1} 句第 {state['tried'] + 1} 次生成失败：{exc}")
                if _is_fatal(exc):  # 显存不够、服务起不来……换个种子也没用
                    raise RuntimeError(f"第 {seg.index + 1} 句没能生成（原因：{_reason(exc)}）：{seg.text[:30]}") from exc
            finally:
                out.unlink(missing_ok=True)
                state["tried"] += 1
                self._progress(lo + (hi - lo) * (i + min(0.95, state["tried"] / max(expected, 1))) / max(total_n, 1), msg)
            if wav is None or wav.size == 0:
                return
            # 在裁剪前打分（语速测量需要首尾的静音作为底噪参考）
            try:
                score = self.scorer.score(wav, sr, seg.text, lang, speed=mult, use_asr=self.use_asr)
            except Exception as exc:
                if not self.use_asr:
                    raise
                # 识别校验（查错字）只是帮着挑的：它出错（比如识别模型显存不够）时关掉它接着生成，不能让整篇停下
                log.warning(f"⚠️ 识别校验出错了（{str(exc).splitlines()[0] if str(exc) else type(exc).__name__}），"
                            "后面只按声纹、语速和停顿挑选")
                self.use_asr = False
                score = self.scorer.score(wav, sr, seg.text, lang, speed=mult, use_asr=False)
            trimmed = trim_edges(wav, sr)
            if trimmed.size == 0:
                return
            cands.append(_Cand(score, seed, trimmed, sr, r_i, k))

        head = f"[{i + 1}/{total_n}]"
        met: Optional[bool] = None
        if self.adaptive:
            batch, cap, b = self.n_candidates, self.max_candidates, 0
            short = QUALITY_SHORT[self.quality]
            met = False
            while state["tried"] < cap:
                sampling = None if b % 3 == 0 else RETRY_SAMPLING[(b % 3) - 1]
                for k in range(min(batch, cap - state["tried"])):
                    n_try = state["tried"] + 1
                    if b == 0:
                        msg = f"{head} 第 {n_try}/{cap} 次尝试：{seg.display[:20]}"
                    else:
                        msg = f"{head} 还没达到「{short}」标准，继续试（第 {n_try}/{cap} 次）"
                    attempt(b, k, sampling, msg)
                # 任何一个候选达到全部严格标准就停（不只看综合分最高的那个）。「一模一样」不走这里（synth/search.py）
                if any(self._meets_targets(c, seg) for c in cands):
                    met = True
                    break
                if not cands and state["tried"] >= 2 * batch:
                    break  # 一直生成不出来：不再浪费时间
                b += 1
        else:
            retry_n = int(self.preset.get("retry_candidates", 2) or 0)
            rounds: List[Tuple[int, Optional[Dict[str, Any]]]] = [(self.n_candidates, None)]
            for r in range(int(self.preset.get("retry_rounds", 0) or 0)):
                rounds.append((retry_n, RETRY_SAMPLING[min(r, len(RETRY_SAMPLING) - 1)]))
            early_after = int(self.preset.get("early_after", 0) or 0)
            for r_i, (n, sampling) in enumerate(rounds):
                reason = ""
                if r_i > 0:
                    reason = self._retry_reason(cands, seg) or ""
                    if not reason:
                        break
                    log.info(f"  第 {seg.index + 1} 句{reason}，重新生成（第 {r_i} 次）……")
                for k in range(n):
                    if r_i == 0:
                        msg = f"{head} 第 {k + 1}/{n} 个版本：{seg.display[:20]}"
                    elif reason.startswith("有字读错"):
                        msg = f"{head} 有字读错了，重新生成（第 {r_i} 次）"
                    else:
                        msg = f"{head} 不够像，重新生成（第 {r_i} 次）"
                    attempt(r_i, k, sampling, msg)
                    if (r_i == 0 and early_after and k + 1 == early_after and k + 1 < n and cands
                            and self._clearly_good(self._select(cands, lang)[0], seg)):
                        log.info(f"  第 {seg.index + 1} 句前 {early_after} 个版本里已经有很好的，提前结束")
                        break
        if not cands:
            exc = state["last_exc"]
            why = _reason(exc) if exc is not None else "生成的音频是空的"
            raise RuntimeError(f"第 {seg.index + 1} 句没能生成（原因：{why}）：{seg.text[:30]}") from exc

        best, survivors = self._select(cands, lang, seg)
        if self.adaptive:
            met = self._meets_targets(best, seg)
        return self._finish_segment(seg, plan, best, cands, state["tried"], met)

    def _synthesize_identical(self, seg: ScriptSegment, plan: _Plan, force: bool) -> SegmentResult:
        """「一模一样」：每句换几条参考录音、几种生成设置，一次请求同时生成好几个版本，分两步打分挑最像的
        （synth/search.py）。force（重新生成）：以前留下来的几个版本也一起比，最好的不会变差。"""
        if not force:
            # 只是排序权重变了（缓存键跟着变了）：同样的设置以前留下的版本还在，按新权重重新排，不用再生成
            res = self._rerank(seg, plan)
            if res is not None:
                return res
        if not self._started:
            # 整篇开始时以为这句只要从留下的版本里重新挑（没启动合成引擎），结果留下的版本读不了：这时才启动。
            # 和整篇开始时一样的顺序：识别模型先加载好，再看空闲显存够不够把声纹模型放到显卡上
            self._ensure_started()
            self._warm_up([seg])
            self._judge_device()
        out = self._search_obj().run(seg, plan, force)
        return self._finish_identical(seg, plan, out, cached=False)

    def _finish_segment(self, seg: ScriptSegment, plan: _Plan, best: Any, cands: Sequence[Any], tries: int,
                        met: Optional[bool], extra: Optional[Dict[str, Any]] = None, wav: Optional[np.ndarray] = None,
                        ref_id: Optional[str] = None, cached: bool = False,
                        model_info: Optional[Dict[str, Any]] = None) -> SegmentResult:
        """挑好以后：写提示和状态、写这句的缓存（声音 + 记录）。所有档位共用（以前写在 synthesize_segment 里）。
        记录里多了这一句实际用的模型（model_name / model_info：生成完马上按正在用的模型文件检测；model_info 给了就用给的，
        例如整篇再挑一遍换成留下来的另一个版本时用原来记下的）。extra / wav / ref_id 只有「一模一样」才给：记录里多几项、
        存的是去掉首尾的声音（打分用的是同样去掉首尾、两边补了静音的声音）、用的是哪条参考。"""
        ref = plan.ref
        lang = send_lang(seg.text, seg.lang)
        out_wav = best.wav if wav is None else wav
        filt = self.sim_filter
        hints: List[str] = []
        short = _is_short(best.score)
        if filt and best.score.pct is not None and best.score.pct < self.min_pct:
            hints.append(SHORT_HINT if short else f"低于 {self.min_pct:.0f}%，建议重新生成或改写这一句")
        if self.use_asr and not self._cer_ok(best, lang):
            hints.append("可能有读错的字" + (f"（识别为：{best.score.hyp}）" if best.score.hyp else "") + "，建议重新生成或改写这一句")
        if self.adaptive and not met and not hints:
            hints.append(self._target_miss(best, seg))
        issues = list(best.score.issues)
        pct = best.score.pct
        if filt and pct is not None:
            status = status_for_pct(pct, self.min_pct)
            if status == "🔴" and short:  # 很短的句子：分数波动大，不直接判"不像"，提醒用耳朵听
                status = "⚠️"
            if status != "🔴" and (hints or issues):
                status = "⚠️"
        else:
            status = "⚠️" if (hints or issues) else "✅"
        flagged = bool(hints or issues)
        cand_info = []
        for c in cands:
            d = c.score.to_dict()
            info = {"seed": c.seed, "pct": d.get("pct"), "cer": d.get("cer"), "errors": d.get("errors"),
                    "total": d.get("total"), "speaker_sim": d.get("speaker_sim"), "round": c.round,
                    "eliminated": bool(filt and c.score.pct is not None and c.score.pct < self.min_pct),
                    "chosen": c is best}
            if extra is not None and hasattr(c, "arm"):  # 「一模一样」：哪种组合、第几行、是不是以前留下的 / 语速微调的
                info.update({"arm": d.get("arm"), "row": c.row, "stored": bool(c.stored), "refined": bool(c.refined)})
            cand_info.append(info)
        cand_info.sort(key=lambda d: (d["pct"] is None, -(d["pct"] or 0.0), -(d["total"] or 0.0)))
        tmp_wav = atomic.tmp_for(plan.wav_path).with_suffix(".wav")  # 先写临时文件再换上去：不会留下半个缓存
        save_audio(tmp_wav, out_wav, best.sr)
        atomic.finish(tmp_wav, plan.wav_path)
        # 重新生成（--redo / 只重新生成第几句）会写到同一个缓存文件：旁边旧的「去杂音」版本是旧句子做的，必须删掉，
        # 否则长度刚好一样时版本 B 里还是旧的那句
        for old in plan.wav_path.parent.glob(plan.wav_path.stem + ".dn*.wav"):
            old.unlink(missing_ok=True)
        score = best.score.to_dict()
        rid = ref_id if ref_id is not None else ref["id"]
        model = dict(model_info) if model_info is not None else self._model_info()  # 这一句实际用的模型（文件名按它定）
        meta = {"text": seg.text, "lang": seg.lang, "ref": rid, "seed": best.seed, "score": score,
                "candidates": cand_info, "model": self.backend.model_id(), "quality": self.quality,
                "tries": tries, "met": met, "hint": "；".join(hints), "status": status, "flagged": flagged,
                "judge": self._judge_sig(), "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model_name": model.get("name"), "model_info": model}
        if extra:
            meta.update(extra)
        atomic.write_text(plan.meta_path, json.dumps(meta, ensure_ascii=False, indent=1))  # 最后写：有它才算缓存好了
        keep = {k: meta[k] for k in EXTRA_KEYS if k in meta}
        return SegmentResult(seg, out_wav, best.sr, score, rid, cached, best.seed, cand_info, path=plan.wav_path,
                             pct=pct, status=status, hint=meta["hint"], flagged=flagged, tries=tries, met=met,
                             model=model, extra=keep)

    # ------------------------------------------------------------------ 整篇
    def _segments(self, source: Union[str, Path, Sequence[ScriptSegment]]) -> List[ScriptSegment]:
        if isinstance(source, (list, tuple)):
            return list(source)
        return parse_script(
            source, lexicon=self.project.load_lexicon(),
            max_units_zh=int(self.scfg.get("max_units_zh", 50)), max_units_en=int(self.scfg.get("max_units_en", 45)),
            min_units=int(self.scfg.get("min_units", 6)), skip_code_blocks=bool(self.scfg.get("skip_code_blocks", True)),
        )

    def _desc(self) -> str:
        if self.quality == "identical":
            return (f"每句至少试 {self.min_candidates} 个、最多 {self.max_candidates} 个版本，"
                    "达到严格标准并且再试也不更好时才停")
        if self.adaptive:
            return f"每句最多试 {self.max_candidates} 次，达到严格标准就停"
        if self.n_candidates > 1:
            return f"每句做 {self.n_candidates} 遍，挑最像你的"
        return "每句做 1 遍"

    def synthesize_all(self, segments: List[ScriptSegment], redo: Iterable[int] = ()) -> List[SegmentResult]:
        """逐句合成（含缓存）。redo 是从 1 开始的句子编号（和结果表的 # 一样）。"""
        n = len(segments)
        redo_set, bad = set(), []
        for x in redo:
            try:
                v = int(x)
            except (TypeError, ValueError):
                continue
            if 1 <= v <= n:
                redo_set.add(v - 1)  # 用户看到的编号从 1 开始
            else:
                bad.append(v)
        if bad:
            msg = f"讲稿只有 {n} 句，第 {'、'.join(str(b) for b in sorted(set(bad)))} 句不存在，已跳过"
            self.warnings.append(msg)
            log.warning(msg)
        lo, hi = self._gen_range
        identical = self.quality == "identical"
        self._redo_set = set(redo_set)
        if identical:
            # 「一模一样」先准备（素材没变时几乎不花时间）：参考录音库的指纹在缓存键里，要先知道哪些句子已经生成过
            self._para_first = {s.index for k, s in enumerate(segments)
                                if k == 0 or segments[k - 1].paragraph != s.paragraph}
            self._identical = self._load_identical(report=True)
        plans = [self._plan(s) for s in segments]
        self._plans = plans
        # 不用合成引擎的句子：已经生成过的；「一模一样」只是排序权重变了（缓存键变了）、同样设置留下的版本还在的
        # （按新权重从留下的版本里重新挑，只用处理器）。都不用时不启动合成引擎（真的引擎启动要占显卡、几十秒）
        ready = [i not in redo_set and (p.cached or (identical and self._has_stored(p))) for i, p in enumerate(plans)]
        need_engine = not all(ready)
        if need_engine and not self._started:
            # 「一模一样」的进度和阶段表对齐（0.02 准备、0.08 逐句生成）；盲听测试等别的地方用时不超过开始生成的位置
            self._ensure_started(min(0.06, lo) if identical else 0.0)
            self._progress(min(0.07, lo) if identical else 0.02, "加载打分模型（第一次使用会先下载）……")
            self._warm_up(segments)
            if identical:
                self._judge_device()
        self._progress(lo, f"开始生成，共 {n} 句（{self._desc()}）")
        results: List[SegmentResult] = []
        todo = [i for i, ok in enumerate(ready) if not ok]  # 真要生成的（估算还要多久只算这些）
        fresh_s: List[float] = []
        self._fresh_s = fresh_s
        if identical:
            self._start_search_report(need_engine)
        for i, seg in enumerate(segments):
            _check_cancel_or_stop(self)
            self._pos = (i, n)
            t_seg = time.monotonic()
            try:
                res = self.synthesize_segment(seg, force=i in redo_set)
            except BaseException:
                self._stop_gpu_sampler()  # 出错、点了停止：后台量显卡的线程也停下
                raise
            results.append(res)
            tag = "已有，直接用" if res.cached else "生成"
            pct = res.pct
            msg = f"[{i + 1}/{n}] {tag}：{seg.display[:20]}" + (f"（像你本人 {pct:.1f}%）" if pct is not None else "")
            log.info(msg)
            self._progress(lo + (hi - lo) * (i + 1) / max(n, 1), msg)
            if identical and not res.cached:
                fresh_s.append(time.monotonic() - t_seg)
                self._eta(fresh_s, sum(1 for j in todo if j > i), lo + (hi - lo) * (i + 1) / max(n, 1))
            for issue in res.score.get("issues") or []:
                self.warnings.append(f"第 {i + 1} 句：{issue}")
            if res.hint:
                self.warnings.append(f"第 {i + 1} 句：{res.hint}")
        if identical:
            self._search_report = self._finish_search_report(results, fresh_s)
        return results

    def _stop_gpu_sampler(self) -> None:
        if getattr(self, "_gpu", None) is not None:
            try:
                self._gpu.stop()
            except Exception:  # noqa: BLE001
                pass
            self._gpu = None

    def _start_search_report(self, need_engine: bool) -> None:
        """「一模一样」报告里的实测（search 块）：开始前记下合成引擎已有的同时生成记录（只算这一篇的），
        有 nvidia-smi 时后台每 2 秒量一次显卡（没有时什么都不量，报告里写 null，不猜）。"""
        import copy

        stats = getattr(self.backend, "batch_stats", None)
        self._bs0 = copy.deepcopy(stats) if isinstance(stats, dict) else None
        self._gpu = None
        if need_engine:
            try:
                from voicetwin.utils.gpu import GpuSampler

                self._gpu = GpuSampler(interval=2.0).start()
            except Exception:  # noqa: BLE001 - 量不了显卡不影响生成
                self._gpu = None

    def _finish_search_report(self, results: List[SegmentResult], fresh_s: List[float]) -> Dict[str, Any]:
        """search 块（设计方案 §2 P6）：每次同时生成几个、语速 1.0001 自检、显存不够减半几次、切不开改一个一个生成几次、
        每秒几个版本、每句几秒、显卡平均使用率和最高显存——都是这一篇实测的；量不出来的是 null。"""
        from collections import Counter

        gpu = {"util_avg": None, "peak_gb": None, "n": 0}
        if getattr(self, "_gpu", None) is not None:
            try:
                gpu = self._gpu.stop()
            except Exception:  # noqa: BLE001
                pass
            self._gpu = None
        now = getattr(self.backend, "batch_stats", None)
        now = now if isinstance(now, dict) else {}
        before = getattr(self, "_bs0", None) or {}

        def diff(key: str) -> int:
            try:
                return int(now.get(key) or 0) - int(before.get(key) or 0)
            except (TypeError, ValueError):
                return 0

        by: Dict[str, Dict[str, Any]] = {}
        for b, row in (now.get("by_batch") or {}).items():
            old = (before.get("by_batch") or {}).get(b) or {}
            req = int(row.get("requests") or 0) - int(old.get("requests") or 0)
            if req > 0:
                by[str(b)] = {"requests": req, "pieces": int(row.get("pieces") or 0) - int(old.get("pieces") or 0),
                              "seconds": round(float(row.get("seconds") or 0.0) - float(old.get("seconds") or 0.0), 3)}
        reasons = {k: int(v) - int((before.get("single_reasons") or {}).get(k) or 0)
                   for k, v in (now.get("single_reasons") or {}).items()}
        reasons = {k: v for k, v in reasons.items() if v > 0}
        fresh = [r for r in results if not r.cached]
        n_cands = sum(int(((r.extra or {}).get("search") or {}).get("candidates") or 0) for r in fresh)
        seg_secs = sum(float(((r.extra or {}).get("search") or {}).get("seconds") or 0.0) for r in fresh)
        pieces = sum(v["pieces"] for v in by.values())
        secs = sum(v["seconds"] for v in by.values())
        cps, basis = None, ""
        if pieces > 0 and secs > 0:
            cps, basis = pieces / secs, "engine"     # 合成引擎实际用的时间（不算打分）
        elif n_cands > 0 and seg_secs > 0:
            cps, basis = n_cands / seg_secs, "search"  # 引擎没有记录时：整个搜索的时间（含打分）
        used = Counter()
        for b, v in by.items():
            used[int(b)] += int(v["pieces"])
        if not used:
            for r in fresh:
                for b in ((r.extra or {}).get("search") or {}).get("batches") or []:
                    used[int(b)] += int(b)
        tuner = getattr(self, "_tuner", None)
        return {"batch_used": used.most_common(1)[0][0] if used else None, "by_batch": by,
                "batch_tuner": dict(getattr(tuner, "result", {}) or {}),
                "speed_trick": now.get("speed_trick") if now else None,
                "oom_backoffs": diff("oom_backoffs"), "split_fallbacks": diff("split_fallbacks"),
                "split_reason": str(now.get("split_reason") or "") if diff("split_fallbacks") > 0 else "",
                "single_reasons": reasons, "gpu_releases": diff("gpu_releases"),
                "candidates_per_s": round(cps, 3) if cps else None, "candidates_per_s_basis": basis,
                "seconds_per_sentence": round(float(np.mean(fresh_s)), 2) if fresh_s else None,
                "fresh_sentences": len(fresh_s),
                "gpu_util_avg": gpu.get("util_avg") if gpu.get("n") else None,
                "gpu_peak_gb": gpu.get("peak_gb") if gpu.get("n") else None, "gpu_samples": int(gpu.get("n") or 0)}

    def _has_stored(self, plan: _Plan) -> bool:
        """「一模一样」这句话同样的设置（缓存键去掉排序权重的版本）有没有留下来的版本。"""
        from voicetwin.synth.search import has_stored, store_dir

        return bool(plan.pool_key) and has_stored(store_dir(self.project.cache_dir, plan.pool_key))

    def _eta(self, fresh_s: List[float], left: int, frac: float) -> None:
        """「一模一样」：新生成满 3 句以后，按实测的每句用时估算还要多久（之后每 5 句更新一次）。"""
        k = len(fresh_s)
        if k < 3 or left <= 0 or not (k == 3 or k % 5 == 0):
            return
        sec = float(np.mean(fresh_s)) * left
        when = "不到 1 分钟" if sec < 60 else f"大约 {int(round(sec / 60.0))} 分钟"
        line = f"按刚才实测的速度估算，生成还要{when}（还有 {left} 句；刚才平均每句 {np.mean(fresh_s):.0f} 秒）"
        log.info(line)
        self._progress(frac, line)

    def _judge_device(self) -> None:
        """「一模一样」的声纹模型能不能放到显卡上（judge_device: auto）：条件都满足、实测和处理器算出来的一样才用，
        不然照旧用处理器（永远不会因为这个出错）。只查一次。"""
        if getattr(self, "_judge_device_done", False):
            return
        self._judge_device_done = True
        judge = self.judge  # 用到时才建打分器（整篇开始时没启动引擎、到这一句才启动时，打分器可能还没建）
        if judge is None or not getattr(judge, "precise", False):
            return
        from voicetwin.data.references import bank_wav
        from voicetwin.eval.identical_judge import judge_on_gpu

        clips = []
        for e in self._identical_ctx()["pool"][:3]:
            try:
                path = bank_wav(self.project, e) if e.get("_bank") else self.project.abspath(e["path"])
                clips.append(load_audio(path))
            except Exception:  # noqa: BLE001
                continue
        new, note = judge_on_gpu(judge, str(self.preset.get("judge_device", "auto")), clips)
        if note:
            log.info(note)
        if new is not judge:
            self._judge = new
            use = getattr(self._scorer, "use_judge", None)
            if callable(use):
                use(new)

    def synthesize_text(self, text: Union[str, Sequence[ScriptSegment]]) -> Tuple[np.ndarray, int, List[SegmentResult]]:
        """合成一段文字，返回拼好的波形（停顿是绝对静音），不写输出文件（盲听测试、试听语速用）。"""
        segments = self._segments(text)
        if not segments:
            raise ValueError("讲稿里没有可以朗读的内容")
        if not self.refs:
            raise RuntimeError("这个声音还没有参考音频，请先完成素材准备（voicetwin prepare）")
        results = self.synthesize_all(segments)
        layout = self._layout(results)
        sr = max(r.sr for r in results)
        return self._render(layout, [(r.wav, r.sr) for r in results], sr), sr, results

    def narrate(self, source: Union[str, Path, Sequence[ScriptSegment]], out_path: Union[str, Path],
                redo: Iterable[int] = (), subtitles: Optional[bool] = None) -> NarrationResult:
        segments = self._segments(source)
        if not segments:
            raise ValueError("讲稿里没有可以朗读的内容")
        if not self.refs:
            raise RuntimeError("这个声音还没有参考音频，请先完成素材准备（voicetwin prepare）")
        # 文件名（老师的规定）：只留汉字、英文字母、数字、下划线；最后的「_模型名」等写文件那一刻按每一句实际用的模型定
        out_dir, stem, ext = out_parts(out_path, self.scfg.get("output_format", "wav"))
        variants_on = self.want_variants
        identical = self.quality == "identical"
        # 进度和 workflows 的阶段表对齐：「一模一样」见 STAGES_NARRATE_IDENTICAL（0.02 准备、0.08 逐句生成、0.88 拼接……）
        if identical:
            self._gen_range = (0.08, 0.88)
        else:
            self._gen_range = (0.03, 0.90) if variants_on else (0.03, 0.95)
        log.info(f"共 {len(segments)} 句，引擎 {self.backend.display_name}，质量「{QUALITY_SHORT[self.quality]}」"
                 f"（{self._desc()}{'，识别校验' if self.use_asr else ''}）")
        t0 = time.time()
        results = self.synthesize_all(segments, redo)
        sr = max(r.sr for r in results)
        mult = self._speed_multiplier()
        timed = any(r.segment.cue_start is not None for r in results)
        assembly: Dict[str, Any] = {}
        if identical and self.preset.get("continuity", True):
            self._progress(self._gen_range[1] + 0.001, "整篇再挑一遍，让前后句子衔接自然……")
            assembly["continuity"] = self._continuity(results, free=getattr(self, "_redo_set", None) or None)
        if identical:
            self._progress(self._gen_range[1] + 0.005, "按你本人的停顿长短和音量拼接，再量一遍停顿……")
        else:
            self._progress(self._gen_range[1], "拼接音频、调整音量、生成字幕……")
        layout = self._layout(results)
        pieces = [(r.wav, r.sr) for r in results]
        gains: Optional[List[float]] = None
        if identical:
            # 每句一个固定的音量系数（不用限幅器、不整篇压）；停顿量了再改（按字幕时间轴配音时不改）
            gains, assembly["loudness"] = self._levels(results, layout, sr)
            if not timed:
                layout, assembly["fit"] = self._fit_pauses(layout, pieces, sr, gains)
                self._apply_layout(results, layout, sr)
        audio_a = self._render(layout, pieces, sr, gains)

        variants: List[Dict[str, Any]] = []
        final_name = ""
        audio_by_name: Dict[str, np.ndarray] = {VARIANT_RAW: audio_a}
        if variants_on:
            self._progress(0.92 if identical else 0.93, "做「去杂音」版本，并比较哪个版本更像你……")
            variants, audio_by_name = self._make_variants(results, layout, audio_a, sr, mult, gains)
            final_name = next(v for v in variants if v["recommended"])["name"]
        audio_main = audio_by_name[final_name] if final_name else audio_a

        # 文件名最后的模型名：写文件这一刻，按这一篇每一句实际用的模型定（老师的规定：模型名永远在最后；
        # 用了两种写「V4和v2ProPlus」；检测不出来写「模型未知」，绝不猜）。文件里面的注释、报告里也写
        tag = model_tag([r.model for r in results], [len(r.wav) / max(r.sr, 1) for r in results])
        used = models_used(results)
        comment = self._file_comment(tag, used)

        def target(*parts: str, ext_: str = ext) -> Path:
            return out_dir / ("_".join([stem, *parts, tag]) + ext_)

        out_dir.mkdir(parents=True, exist_ok=True)
        loud = not identical  # 「一模一样」每句的音量已经调好（_levels），不再整篇调
        if variants_on:
            for v in variants:
                v["path"] = str(self._write_audio(audio_by_name[v["name"]], sr, target(v["name"]), loudness=loud,
                                                  comment=comment))
            final = target()
            src = Path(next(v["path"] for v in variants if v["recommended"]))
            tmp = atomic.tmp_for(final)
            shutil.copyfile(src, tmp)
            atomic.finish(tmp, final)
            for v in variants:
                v["final"] = v["name"] == final_name
        else:
            final = self._write_audio(audio_a, sr, target(), loudness=loud, comment=comment)
        srt_path = None
        if identical:
            self._progress(0.99, "写字幕和报告……")
        if subtitles if subtitles is not None else self.scfg.get("subtitles", True):
            srt_path = self._write_srt(results, target(ext_=".srt"))

        seg_report = self._seg_report(results)
        sims = [s["speaker_sim"] for s in seg_report if s.get("speaker_sim") is not None]
        overall = _weighted_pct(results)
        if variants:  # 两个版本时，整篇百分比用最终版本的（和版本卡片上的数字一致）
            final_pct = next((v.get("pct") for v in variants if v.get("final")), None)
            overall = final_pct if final_pct is not None else overall
        flagged = sorted(s["index"] for s in seg_report if s.get("flagged"))
        nums: Dict[str, Any] = {}
        if identical:
            nums = self._assembly_numbers(results, layout, audio_main, sr, gains, assembly)
        notes = list(self.notes) + self._summary_lines(results, flagged, overall, nums=nums or None)
        for line in notes:
            log.info(line)
        judge = self.judge
        report = {
            "audio": str(final), "backend": self.backend.name, "model": self.backend.model_id(),
            "model_name": tag, "models_used": used, "file_comment": comment,
            "srt": str(srt_path) if srt_path else None,
            "quality": self.quality, "quality_label": QUALITY_LABELS[self.quality],
            "duration": round(len(audio_main) / sr, 2), "speed": round(mult, 3),
            "mean_speaker_sim": round(float(np.mean(sims)), 4) if sims else None,
            "overall_pct": overall, "min_pct": self.min_pct, "similarity_filter": self.sim_filter,
            "similarity": judge.info() if judge is not None else {"models": [], "note": HONEST_NOTE},
            "elapsed_sec": round(time.time() - t0, 1), "warnings": self.warnings, "flagged": flagged,
            "notes": notes, "variants": variants, "final": final_name, "segments": seg_report,
            "tries_avg": round(float(np.mean([r.tries for r in results if not r.cached])), 2)
            if any(not r.cached for r in results) else None,
        }
        if identical:
            report.update({"search": getattr(self, "_search_report", None) or {},
                           "continuity": assembly.get("continuity"), "max_candidates": self.max_candidates,
                           **nums})
        report_path = target(ext_=".json")
        atomic.write_text(report_path, json.dumps(report, ensure_ascii=False, indent=1))
        self._progress(1.0, f"完成：{final.name}")
        return NarrationResult(final, srt_path, report_path, len(audio_main) / sr, seg_report, self.warnings,
                               flagged=flagged, variants=variants, quality=self.quality, overall_pct=overall, notes=notes)

    def say(self, text: str, out_path: Union[str, Path]) -> NarrationResult:
        return self.narrate(text, out_path, subtitles=False)

    @staticmethod
    def _file_comment(tag: str, used: Sequence[Dict[str, Any]]) -> str:
        """写进音频文件里面的注释（WAV 的 INFO 注释、MP3 的标签）：改了文件名也能查到用的是哪个模型。"""
        files = [f"{f.get('kind')} {f.get('file')}（指纹 {f.get('fingerprint') or '没测出来'}）"
                 for m in used for f in (m.get("files") or []) if f.get("file")]
        return f"VoiceTwin 生成；模型：{tag}" + ("；模型文件：" + "、".join(files) if files else "")

    @staticmethod
    def _apply_layout(results: List[SegmentResult], layout: List[Tuple[float, int]], sr: int) -> None:
        for r, (start, n) in zip(results, layout):
            r.start, r.end = start, start + n / sr

    # ------------------------------------------------------------------ 报告
    def _seg_report(self, results: List[SegmentResult]) -> List[Dict[str, Any]]:
        out = []
        for r in results:
            entry = {
                "index": r.segment.index + 1, "text": r.segment.display, "tts_text": r.segment.text,
                "lang": r.segment.lang, "start": round(r.start, 3), "end": round(r.end, 3), "ref": r.ref_id,
                "cached": r.cached, "seed": r.seed,
                **{k: v for k, v in r.score.items() if k in ("speaker_sim", "cer", "rate", "issues", "pct", "pcts",
                                                              "sims", "hyp")},
                "pct": r.pct, "status": r.status, "hint": r.hint, "flagged": r.flagged, "tries": r.tries,
                "met": r.met, "candidates": r.candidates, "model": (r.model or {}).get("name"),
            }
            if r.path is not None:
                entry["clip"] = self.project.relpath(r.path)
            if self.quality == "identical":
                ex = r.extra or {}
                search = ex.get("search") if isinstance(ex.get("search"), dict) else {}
                entry.update({"arm": search.get("chosen_arm"), "arms": ex.get("arms") or [], "search": search,
                              "dp_changed": bool((ex.get("dp") or {}).get("changed"))})
            out.append(entry)
        return out

    def _assembly_numbers(self, results: List[SegmentResult], layout: List[Tuple[float, int]], audio: np.ndarray,
                          sr: int, gains: Optional[List[float]], assembly: Dict[str, Any]) -> Dict[str, Any]:
        """「一模一样」报告和小结里的实测数字（小结里的每个数都从这里来，也都写进报告）：
        停顿（用量你本人停顿的同一个方法量最后的音频）、句子之间的音量差（每句调好音量以后再量）、最后的响度、
        新生成几句 / 几句达标。量不出来的是 null（小结写「没测出来」）。"""
        twin = (self._identical_ctx() or {}).get("twin") or {}
        tp = twin.get("pauses") or {}
        kinds = list(getattr(self, "_pause_kinds", []) or [])
        targets = list(getattr(self, "_pause_targets", []) or [])
        gaps = self._measure_gaps(audio, sr, layout) if len(layout) > 1 else []

        def med(vals: List[Optional[float]]) -> Optional[float]:
            vals = [v for v in vals if v is not None]
            return round(float(np.median(vals)), 3) if vals else None

        comma = [g for g, k in zip(gaps, kinds) if k == "clause"]
        # 句号处：一段话里面的句号；整篇都是一句一段时用段落之间的
        sent = [g for g, k in zip(gaps, kinds) if k == "sentence"] or [g for g, k in zip(gaps, kinds) if k == "paragraph"]
        errors = [round(g - t, 3) if (g is not None and t is not None) else None for g, t in zip(gaps, targets)]
        kinds = kinds[:max(0, len(layout) - 1)]
        her_c, her_s = tp.get("comma") or {}, tp.get("sentence") or {}
        pauses = {"her": {"comma": her_c.get("median"), "sentence": her_s.get("median"),
                          "n_comma": int(her_c.get("n") or 0), "n_sentence": int(her_s.get("n") or 0)},
                  "this": {"comma": med(comma), "sentence": med(sent),
                           "n_comma": sum(1 for g in comma if g is not None),
                           "n_sentence": sum(1 for g in sent if g is not None)},
                  "kinds": kinds,
                  "targets": [None if t is None else round(t, 3) for t in targets[:max(0, len(layout) - 1)]],
                  "measured": gaps, "errors": errors,
                  "fit_passes": int((assembly.get("fit") or {}).get("passes") or 0)}
        loud = dict(assembly.get("loudness") or {})
        levels = []
        for k, r in enumerate(results):
            w = resample(r.wav, r.sr, sr) if r.sr != sr else r.wav
            g = gains[k] if gains is not None and k < len(gains) else 1.0
            levels.append(speech_level_db(np.asarray(w, dtype=np.float32) * np.float32(g), sr))
        lv = np.asarray([v for v in levels if v is not None], dtype=np.float64)
        loud["this_sd"] = round(float(np.std(lv - np.median(lv), ddof=1)), 2) if lv.size >= 2 else None
        loud["levels_db"] = [None if v is None else round(v, 2) for v in levels]
        loud["final_lufs"] = round(float(measure_lufs(audio, sr)), 2)
        fresh = [r for r in results if not r.cached]
        return {"pauses": pauses, "loudness": loud, "fresh_count": len(fresh),
                "met_count": sum(1 for r in fresh if r.met)}

    def _summary_lines(self, results: List[SegmentResult], flagged: List[int],
                       overall: Optional[float] = None, nums: Optional[Dict[str, Any]] = None) -> List[str]:
        fresh = [r for r in results if not r.cached]
        if self.quality == "identical" and nums is not None:
            return self._identical_summary(results, fresh, flagged, overall, nums)
        lines = []
        if fresh:
            avg = float(np.mean([r.tries for r in fresh]))
            line = f"本次生成：共 {len(results)} 句（新生成 {len(fresh)} 句），平均每句试了 {avg:.1f} 次"
            if self.quality == "identical":
                line = (f"本次生成：共 {len(results)} 句（新生成 {len(fresh)} 句），平均每句试了 {avg:.1f} 个版本"
                        f"（最多 {self.max_candidates} 个）")
            if self.adaptive:
                met = sum(1 for r in fresh if r.met)
                line += f"；{met} 句达到了「{QUALITY_SHORT[self.quality]}」的严格标准"
            lines.append(line + "。")
        else:
            lines.append(f"本次生成：共 {len(results)} 句，全部用的是之前生成好的结果。")
        if overall is None:
            overall = _weighted_pct(results)
        if overall is not None:
            lines.append(f"整篇像你本人 {overall:.1f}%（{PCT_HELP}；{HONEST_NOTE}）。")
        if flagged:
            lines.append("需要注意的句子：第 " + "、".join(str(n) for n in flagged) + " 句（可以只重做这几句）。")
        else:
            lines.append("没有需要特别注意的句子。")
        return lines

    def _identical_summary(self, results: List[SegmentResult], fresh: List[SegmentResult], flagged: List[int],
                           overall: Optional[float], nums: Dict[str, Any]) -> List[str]:
        """「一模一样」的小结（设计方案 §4.4）：每个数都是这一篇实测的、都在报告里；量不出来写「（没测出来）」。"""
        miss = "（没测出来）"

        def sec(v: Any) -> str:
            return f"{float(v):.2f} 秒" if isinstance(v, (int, float)) else miss

        lines = []
        if fresh:
            avg = round(float(np.mean([r.tries for r in fresh])), 2)  # 和报告里的 tries_avg 同一个数
            lines.append(f"本次生成：共 {len(results)} 句（新生成 {len(fresh)} 句），平均每句试了 {avg:.1f} 个版本"
                         f"（最多 {self.max_candidates} 个）；{nums.get('met_count', 0)} 句达到了「一模一样」的严格标准"
                         "（错字检查通过、像你本人不低于你自己录音的常见水平、语速音调在你平时的范围里）。")
        else:
            lines.append(f"本次生成：共 {len(results)} 句，全部用的是之前生成好的结果。")
        if overall is None:
            overall = _weighted_pct(results)
        if overall is not None:
            lines.append(f"整篇像你本人 {overall:.1f}%（{PCT_HELP}）。这个分数是从很多个版本里挑出来的最高分，会比真实水平"
                         "偏高一点；最终请用耳朵听，可以在「⑤ 鉴别」做盲听测试。")
        p = nums.get("pauses") or {}
        her, this = p.get("her") or {}, p.get("this") or {}
        if len(results) > 1:
            kinds = set(p.get("kinds") or [])
            now = []  # 这一篇里有哪种停顿才写哪种（没有在逗号处拆开的句子就不写逗号处）
            if "clause" in kinds:
                now.append(f"逗号处 {sec(this.get('comma'))}")
            if kinds & {"sentence", "paragraph"}:
                now.append(f"句号处 {sec(this.get('sentence'))}")
            lines.append(f"停顿（实测）：你本人 逗号处 {sec(her.get('comma'))}、句号处 {sec(her.get('sentence'))}"
                         + (f"；这次 {'、'.join(now)}" if now else "") + "。")
            loud = nums.get("loudness") or {}

            def db(v: Any) -> str:
                return f"±{float(v):.1f} dB" if isinstance(v, (int, float)) else miss

            lines.append(f"句子之间的音量差（实测）：你本人 {db(loud.get('her_sd'))}；这次 {db(loud.get('this_sd'))}。")
        search = getattr(self, "_search_report", None) or {}
        if fresh and isinstance(search.get("seconds_per_sentence"), (int, float)):
            line = f"这次实际速度：平均每句 {float(search['seconds_per_sentence']):.1f} 秒"
            if isinstance(search.get("gpu_util_avg"), (int, float)):
                line += f"；显卡平均使用率 {float(search['gpu_util_avg']):.0f}%（实测）"
            lines.append(line + "。")
        why = self._batch_fallback_reason(search, fresh)
        if why:
            lines.append(f"这次没能用上「显卡一次同时生成好几个版本」（原因：{why}），改成一个一个生成："
                         "结果的标准一样，只是更慢。")
        if flagged:
            lines.append("需要注意的句子：第 " + "、".join(str(n) for n in flagged) + " 句（可以只重做这几句）。")
        else:
            lines.append("没有需要特别注意的句子。")
        return lines

    def _batch_fallback_reason(self, search: Dict[str, Any], fresh: List[SegmentResult]) -> str:
        """这一篇本来应该同时生成好几个版本（引擎支持、每次不止 1 个），实际一次都没同时生成：返回实测记下的原因。"""
        if not fresh or not getattr(self.backend, "supports_batch", False) or int(self.n_candidates) <= 1:
            return ""
        by = search.get("by_batch") or {}
        if any(int(b) > 1 and int((v or {}).get("pieces") or 0) > 0 for b, v in by.items()):
            return ""
        reasons = search.get("single_reasons") or {}
        if search.get("split_fallbacks"):
            return f"同时生成的几个版本没能分开（{search.get('split_reason') or '原因没记下来'}）"
        if reasons:
            return max(reasons.items(), key=lambda kv: kv[1])[0]
        return ""

    # ------------------------------------------------------------------ 两个版本（「完美」「一模一样」档）
    def _step(self, lo: float, hi: float, k: int, n: int, msg: str) -> None:
        """长循环里的进度（每 10 句报一次，最后一句也报）。"""
        if k % 10 == 0 or k == n:
            self._progress(lo + (hi - lo) * k / max(n, 1), f"{msg} {k}/{n}")

    def _version_score(self, wavs: List[np.ndarray], results: List[SegmentResult], sr: int, mult: float,
                       rng: Tuple[float, float] = (0.0, 0.0), label: str = "",
                       reuse: Optional[Dict[int, Tuple[float, Optional[float]]]] = None
                       ) -> Tuple[float, Optional[float], List[Tuple[float, Optional[float]]]]:
        """同一个标准给整篇打分：每句（相似度为主 − 语速/音高偏差）按时长加权平均；同时给出整篇百分比。
        「一模一样」用它自己的完整打分（不查错字；声音两边补 0.3 秒静音，和挑版本时一样）。
        reuse：{第几句: (综合分, 百分比)}——这几句的声音和已经打过分的一模一样（「去杂音」版本里不用去杂音的句子），
        直接用那个分数（同一段声音，打出来就是这个数）。返回 (整篇分, 整篇百分比, 每句的 (综合分, 百分比))。"""
        totals, weights, pcts = [], [], []
        rows: List[Tuple[float, Optional[float]]] = []
        identical = self.quality == "identical"
        for k, (wav, r) in enumerate(zip(wavs, results), 1):
            _check_cancel()
            if label:
                self._step(rng[0], rng[1], k, len(wavs), label)
            if reuse is not None and (k - 1) in reuse:
                total, pct = reuse[k - 1]
            else:
                if identical and hasattr(self.scorer, "full"):
                    pad = np.zeros(int(round(ANALYSIS_PAD * sr)), dtype=np.float32)
                    s = self.scorer.full(np.concatenate([pad, np.asarray(wav, dtype=np.float32), pad]), sr,
                                         r.segment.text, send_lang(r.segment.text, r.segment.lang), mult,
                                         use_asr=False)
                else:
                    s = self.scorer.score(wav, sr, r.segment.text, r.segment.lang, speed=mult, use_asr=False,
                                          check_pauses=False)
                total, pct = float(s.total), s.pct
            dur = len(wav) / sr
            totals.append(total)
            weights.append(dur)
            pcts.append(pct)
            rows.append((total, pct))
        w = np.asarray(weights, dtype=np.float64)
        score = float(np.average(totals, weights=w)) if w.sum() > 0 else float(np.mean(totals))
        valid = [(p, d) for p, d in zip(pcts, weights) if p is not None]
        pct = round(float(np.average([p for p, _ in valid], weights=[d for _, d in valid])), 1) \
            if valid and sum(d for _, d in valid) > 0 else None
        return round(score, 4), pct, rows

    def _make_variants(self, results: List[SegmentResult], layout: List[Tuple[float, int]], audio_a: np.ndarray,
                       sr: int, mult: float, gains: Optional[List[float]] = None
                       ) -> Tuple[List[Dict[str, Any]], Dict[str, np.ndarray]]:
        wavs_a = [resample(r.wav, r.sr, sr) for r in results]
        n = len(results)
        identical = self.quality == "identical"
        score_a, pct_a, rows_a = self._version_score(wavs_a, results, sr, mult, (0.93, 0.95), "给「未去杂音」版本打分")
        variants = [{"name": VARIANT_RAW, "label": "版本 A：未去杂音", "score": score_a, "pct": pct_a}]
        audio_by_name = {VARIANT_RAW: audio_a}
        wavs_b: List[np.ndarray] = []
        noisy: List[int] = list(range(n))
        if identical:
            # 「一模一样」：只给说话部分量得出底噪（底噪 > −60 dBFS）的句子去杂音，别的句子 B 版本里和 A 一模一样
            floors = [self._speech_floor_db(w, sr) for w in wavs_a]
            noisy = [i for i, f in enumerate(floors) if f is not None and f > DENOISE_FLOOR_DB]
        if identical and not noisy:
            variants.append({"name": VARIANT_DENOISED, "label": "版本 B：去杂音", "score": score_a, "pct": pct_a,
                             "same_as_raw": True, "denoised_sentences": []})
            audio_by_name[VARIANT_DENOISED] = audio_a
            msg = "两个版本完全一样（每句里都量不出底噪，不需要去杂音）。"
            self.notes.append(msg)
            log.info(msg)
        else:
            for k, (r, w) in enumerate(zip(results, wavs_a), 1):
                _check_cancel()
                self._step(0.95, 0.97, k, n, "去杂音")
                if identical and (k - 1) not in noisy:
                    wavs_b.append(w)  # 这一句量不出底噪：和 A 一模一样
                    continue
                dn = self._denoised(r, w, sr)
                if dn is None:
                    wavs_b = []
                    break
                wavs_b.append(dn)
            if wavs_b:
                audio_b = self._render(layout, [(w, sr) for w in wavs_b], sr, gains)
                reuse = {i: rows_a[i] for i in range(n) if i not in noisy} if identical else None
                score_b, pct_b, _ = self._version_score(wavs_b, results, sr, mult, (0.97, 0.99), "给「去杂音」版本打分",
                                                        reuse=reuse)
                entry = {"name": VARIANT_DENOISED, "label": "版本 B：去杂音", "score": score_b, "pct": pct_b}
                if identical:
                    entry["denoised_sentences"] = [i + 1 for i in noisy]
                variants.append(entry)
                audio_by_name[VARIANT_DENOISED] = audio_b
            else:
                msg = ("没有安装 noisereduce，这次只生成了「未去杂音」一个版本（想要「去杂音」版本，"
                       "请重新双击 install_windows.bat 安装一次，安装程序会自动装上它）")
                self.warnings.append(msg)
                self.notes.append(msg)
                log.warning(msg)
        best = max(variants, key=lambda v: (v["score"], v["name"] == VARIANT_RAW))  # 一样高时用没处理过的
        for rank, v in enumerate(sorted(variants, key=lambda v: (-v["score"], v["name"] != VARIANT_RAW)), 1):
            v["rank"] = rank
        for v in variants:
            v["recommended"] = v is best
        if len(variants) > 1:
            other = next(v for v in variants if v is not best)
            if best.get("pct") is not None and other.get("pct") is not None:
                gap = float(best["pct"]) - float(other["pct"])
                detail = f"像你本人 {best['pct']:.1f}%，另一个版本 {other['pct']:.1f}%，相差 {gap:.1f}%；"
            else:
                detail = ""
            line = (f"⭐ 推荐：{best['label']}，更像你的原声（{detail}"
                    f"综合分 {best['score']:.3f} 对 {other['score']:.3f}）")
            self.notes.append(line)  # 最后和小结一起写进日志
        return variants, audio_by_name

    @staticmethod
    def _speech_floor_db(wav: np.ndarray, sr: int) -> Optional[float]:
        """一句话里说话部分的底噪（dBFS）：从第一个到最后一个有声音的帧（10 ms 一帧、40 ms 窗、自动静音阈值）之间，
        逐帧电平的 p10（句内停顿里有没有底噪）。整句都量不出声音时 None。"""
        wav = np.asarray(wav, dtype=np.float32)
        if wav.size < int(0.1 * sr):
            return None
        db = frame_rms_db(wav, sr)
        thr = auto_silence_threshold(wav, sr)
        idx = np.flatnonzero(db >= thr)
        if idx.size == 0:
            return None
        return float(np.percentile(db[idx[0]:idx[-1] + 1], 10))

    def _denoised(self, r: SegmentResult, wav: np.ndarray, sr: int) -> Optional[np.ndarray]:
        """这一句的去杂音版本（缓存在这句旁边，下次不用重算）。没有 noisereduce 时返回 None。
        「一模一样」：说话部分量不出底噪（≤ −60 dBFS）的句子原样返回（去杂音只会伤音色）。"""
        if self.quality == "identical":
            floor = self._speech_floor_db(wav, sr)
            if floor is None or floor <= DENOISE_FLOOR_DB:
                return np.asarray(wav, dtype=np.float32)
        cache = r.path.with_name(r.path.stem + f".dn{sr}.wav") if r.path is not None else None
        if cache is not None and cache.exists():
            try:
                # 比这句的音频还旧的去杂音版本不能用（这句后来重新生成过）
                fresh = not r.path.exists() or cache.stat().st_mtime >= r.path.stat().st_mtime
                w, s = load_audio(cache)
                if fresh and s == sr and len(w) == len(wav):
                    return w
            except Exception:
                pass
        out = denoise_light(wav, sr)
        if out is None:
            return None
        if cache is not None:
            try:
                save_audio(cache, out, sr, subtype="FLOAT")
            except Exception:
                pass
        return out

    # ------------------------------------------------------------------ 整篇再挑一遍（「一模一样」）
    def _delta_stats(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """你本人前后连着说的两段之间音调（半音）、语速（ln）、音色（1 − 余弦）平均变多少、波动多大，按句号 / 逗号分开
        （twin_profile.json 的 deltas）。量不出来（少于 8 对、波动是 0）的那一项不比。"""
        twin = (self._identical_ctx() or {}).get("twin") or {}
        deltas = twin.get("deltas") or {}
        out: Dict[str, Dict[str, Tuple[float, float]]] = {}
        for typ in ("sentence", "clause"):
            row: Dict[str, Tuple[float, float]] = {}
            d = deltas.get(typ) or {}
            for feat, key in (("f0", "f0_med_st"), ("rate", "log_rate")):
                st = d.get(key) or {}
                if isinstance(st.get("mean"), (int, float)) and isinstance(st.get("sd"), (int, float)) and st["sd"] > 0:
                    row[feat] = (float(st["mean"]), float(st["sd"]))
            st = (deltas.get("timbre") or {}).get(typ) or {}
            if isinstance(st, dict) and isinstance(st.get("mean"), (int, float)) \
                    and isinstance(st.get("sd"), (int, float)) and st["sd"] > 0:
                row["timbre"] = (float(st["mean"]), float(st["sd"]))
            if row:
                out[typ] = row
        return out

    def _dp_states(self, r: SegmentResult, plan: Optional[_Plan], free: bool) -> List[Dict[str, Any]]:
        """这一句在整篇再挑一遍时能选哪些版本：留下来的版本里，和现在用的这个同一个档次（读对了 / 达到全部标准）的；
        几乎没声音、不够像、去首尾以后是空的不要。不能动的句子（重新生成时没点名的）只有现在用的这一个。"""
        from types import SimpleNamespace

        from voicetwin.style.twin_profile import f0_median_hz
        from voicetwin.synth.search import store_dir, store_items

        seg = r.segment
        lang = send_lang(seg.text, seg.lang)
        chosen = (r.extra or {}).get("chosen") or {}
        cur_arm = (r.extra or {}).get("arm") or {}
        items, embs = ([], {})
        if plan is not None and plan.pool_key:
            items, embs = store_items(store_dir(self.project.cache_dir, plan.pool_key))

        def same(it: Dict[str, Any]) -> bool:
            if int(it.get("seed", -1)) != int(r.seed) or (it.get("arm") or {}) != cur_arm:
                return False
            if chosen:
                return int(it.get("row", -1)) == int(chosen.get("row", -2)) and \
                    abs(float(it.get("speed", 0.0)) - float(chosen.get("speed", -1.0))) < 1e-6
            return True

        cur_item = next((it for it in items if same(it)), None)

        def state(it: Optional[Dict[str, Any]]) -> Dict[str, Any]:
            if it is None:  # 现在用的这个没在留下来的版本里（存不了的时候）：按这一句的记录
                score = Score.from_dict(r.score or {})
                return {"item": None, "current": True, "total": float(score.total), "score": score,
                        "f0": f0_median_hz(r.wav, r.sr), "rate": score.rate, "emb": {}}
            score = Score.from_dict(it.get("score") or {})
            return {"item": it, "current": it is cur_item, "total": float(score.total), "score": score,
                    "f0": it.get("f0_med"), "rate": score.rate, "emb": embs.get(it["file"]) or {}}

        cur = state(cur_item)
        if not free or cur_item is None:
            return [cur]
        cand = SimpleNamespace(score=cur["score"])
        cls = (self._cer_ok(cand, lang), self._meets_targets(cand, seg))
        out = [cur]
        for it in items:
            if it is cur_item or it.get("empty"):
                continue
            st = state(it)
            obj = SimpleNamespace(score=st["score"])
            if "几乎没有声音" in (st["score"].issues or []) or not self._pct_ok(obj):
                continue
            if (self._cer_ok(obj, lang), self._meets_targets(obj, seg)) != cls:
                continue
            out.append(st)
        # 「差不多一样高」时挑版本按时长、音调挑（综合分不一定最高）：现在用的这个按这一组最高的综合分算，
        # 只有前后衔接真的更好时才换（不然只是因为综合分高一点点就换掉，等于推翻了挑版本时的规则）
        from voicetwin.synth.search import TIE_EPS

        top = max(st["total"] for st in out)
        if cur["total"] >= top - TIE_EPS:
            cur["node"] = top
        return out

    @staticmethod
    def _edge_cost(a: Dict[str, Any], b: Dict[str, Any], stats: Dict[str, Tuple[float, float]]) -> float:
        """前一句用 a、后一句用 b 时衔接得好不好：和你本人前后两段的变化比，每一项 0.03 × min(z², 9) 加起来。"""
        from voicetwin.eval.speaker import cosine

        cost = 0.0
        for feat, (mu, sd) in stats.items():
            delta = None
            if feat == "f0" and a.get("f0") and b.get("f0"):
                delta = 12.0 * math.log2(float(b["f0"]) / float(a["f0"]))
            elif feat == "rate" and a.get("rate") and b.get("rate"):
                delta = math.log(float(b["rate"]) / float(a["rate"]))
            elif feat == "timbre":
                common = sorted(set(a.get("emb") or {}) & set(b.get("emb") or {}))
                if common:
                    delta = float(np.mean([1.0 - cosine(a["emb"][m], b["emb"][m]) for m in common]))
            if delta is not None and math.isfinite(delta):
                cost += DP_WEIGHT * min(((delta - mu) / sd) ** 2, DP_ZCAP)
        return cost

    def _continuity(self, results: List[SegmentResult], free: Optional[Iterable[int]] = None) -> Dict[str, Any]:
        """整篇再挑一遍（设计方案 §1.9 第 2 条）：每句在留下来的、同一个档次的版本里，按「综合分 − 前后衔接的代价」
        整篇一起挑（Viterbi）；衔接的代价是前后两句的音调、语速、音色变化和你本人前后两段录音的变化比。
        free：重新生成时只有点名的那几句能换（别的句子一个都不动）；None = 每句都能换。换了的句子写回这句的缓存
        （下次直接用换过的、重新生成别的句子时也不会变回去），报告里每句记 dp_changed。"""
        n = len(results)
        info: Dict[str, Any] = {"applied": False, "changed": 0, "free": 0, "features": {}, "why": ""}
        for r in results:
            r.extra = dict(r.extra or {})
            r.extra["dp"] = {"changed": False}
        stats = self._delta_stats()
        if n < 2:
            info["why"] = "只有一句"
            return info
        if not stats:
            info["why"] = "你本人前后两句的音调、语速、音色变化没测出来（素材太少），这一步跳过"
            log.info("整篇再挑一遍：" + info["why"])
            return info
        free_set = set(range(n)) if free is None else {int(i) for i in free if 0 <= int(i) < n}
        plans = list(getattr(self, "_plans", None) or [])
        if len(plans) != n:
            plans = [self._plan(r.segment) for r in results]
        states = [self._dp_states(r, plans[i], i in free_set) for i, r in enumerate(results)]
        info["free"] = sum(1 for i in range(n) if len(states[i]) > 1)
        info["features"] = {typ: sorted(row) for typ, row in stats.items()}

        def node(st: Dict[str, Any]) -> float:
            return float(st.get("node", st["total"])) + (1e-9 if st["current"] else 0.0)  # 一样好时不换

        def typ_of(seg: ScriptSegment) -> str:
            return "clause" if seg.pause_after == "clause" else "sentence"  # 段落之间按句号的变化比（她的录音里没有单独的段落）

        acc = [node(st) for st in states[0]]
        back: List[List[int]] = [[0] * len(states[0])]
        for i in range(1, n):
            st_stats = stats.get(typ_of(results[i - 1].segment)) or {}
            row, bk = [], []
            for b in states[i]:
                vals = [acc[j] - self._edge_cost(a, b, st_stats) for j, a in enumerate(states[i - 1])]
                j = int(np.argmax(vals))
                row.append(vals[j] + node(b))
                bk.append(j)
            acc, back = row, back + [bk]
        k = int(np.argmax(acc))
        path = [0] * n
        for i in range(n - 1, -1, -1):
            path[i] = k
            k = back[i][k]
        changed = 0
        for i, k in enumerate(path):
            st = states[i][k]
            if st["current"]:
                continue
            try:
                results[i] = self._dp_swap(results[i], plans[i], st, states[i])
                changed += 1
            except Exception as exc:  # noqa: BLE001 - 换不成（留下的声音读不了）：照旧用原来的
                log.warning(f"整篇再挑一遍：第 {i + 1} 句换版本没成功（{exc}），照旧用原来的")
        info.update(applied=True, changed=changed)
        log.info(f"整篇再挑一遍：{info['free']} 句可以换，换了 {changed} 句（让前后句子的音调、语速、音色衔接得像你本人）")
        return info

    def _dp_swap(self, r: SegmentResult, plan: _Plan, st: Dict[str, Any],
                 states: List[Dict[str, Any]]) -> SegmentResult:
        """把这一句换成留下来的另一个版本：写回这句的缓存（声音 = 同样去首尾以后的那一段）和记录。"""
        from voicetwin.synth.search import Arm, SearchCand, store_dir

        folder = store_dir(self.project.cache_dir, plan.pool_key)
        it = st["item"]
        raw, sr = load_audio(folder / it["file"])
        delivered = self._trim(raw, sr)
        if delivered.size == 0:
            raise RuntimeError("这个版本去首尾以后是空的")

        def cand(s: Dict[str, Any], wav: np.ndarray) -> SearchCand:
            x = s["item"] or {}
            arm = Arm(**{k: v for k, v in (x.get("arm") or {}).items() if k in Arm.__dataclass_fields__}) \
                if x else Arm(str(r.ref_id), 0, 0)
            c = SearchCand(wav=wav, sr=int(x.get("sr", r.sr)), arm=arm, seed=int(x.get("seed", r.seed)),
                           req_seed=int(x.get("req_seed", 0)), row=int(x.get("row", 0)),
                           req_no=int(x.get("req_no", -1)), req_n=int(x.get("req_n", 1)), speed=float(x.get("speed", 1.0)),
                           mode=str(x.get("mode") or "single"), stored=True, refined=bool(x.get("refined")),
                           model=str(x.get("model") or ""))
            c.score = s["score"]
            return c

        best = cand(st, raw)
        cands = [best if s is st else cand(s, np.zeros(0, dtype=np.float32)) for s in states]
        try:
            meta = json.loads(plan.meta_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            meta = {}
        ctx = self._identical_ctx()
        extra = {k: meta[k] for k in ("search", "arms") if k in meta}
        # 换的时候用的是现在的说话习惯、排序权重（和挑版本时写记录一样）：下次读缓存时不会当成「标准变了」再重新排
        extra.update({"profile_sig": ctx["profile_sig"], "weights_version": ctx["weights_version"],
                      "arm": best.arm.to_dict(),
                      "chosen": {"seed": int(best.seed), "row": int(best.row), "speed": round(float(best.speed), 6)},
                      "dp": {"changed": True, "from_seed": int(r.seed)}})
        if isinstance(extra.get("search"), dict):
            extra["search"] = dict(extra["search"], chosen_arm=best.arm.label(plan.refs))
        met = bool(self._meets_targets(best, r.segment))
        return self._finish_segment(r.segment, plan, best, cands, r.tries, met, extra=extra, wav=delivered,
                                    ref_id=best.arm.ref_id, cached=r.cached, model_info=r.model)

    # ------------------------------------------------------------------ 拼接
    def _twin_pause(self, kind: Any, i: int) -> Optional[float]:
        """「一模一样」的停顿：你本人这一类停顿（逗号 / 句号）实测分布的 u 分位，u 在 0.2~0.8 之间随机
        （random.Random(种子 + 第几句)，同一篇每次一样）；段落之间用句号停顿的 0.85~0.97 分位。
        少于 8 个、没量出来时返回 None（按以前的方法）。"""
        twin = (self._identical_ctx() or {}).get("twin") or {}
        st = (twin.get("pauses") or {}).get("comma" if kind == "clause" else "sentence") or {}
        q = st.get("q")
        if int(st.get("n") or 0) < 8 or not isinstance(q, dict):
            return None
        pts = sorted((int(k[1:]) / 100.0, float(v)) for k, v in q.items()
                     if isinstance(v, (int, float)) and re.fullmatch(r"p\d{2}", str(k)))
        if len(pts) < 2:
            return None
        lo, hi = PARA_U if kind == "paragraph" else PAUSE_U
        u = random.Random(self.base_seed + i).uniform(lo, hi)
        return float(np.interp(u, [x for x, _ in pts], [y for _, y in pts]))

    def _pause(self, seg: ScriptSegment, i: int) -> float:
        kind = seg.pause_after
        if isinstance(kind, (int, float)):
            return float(kind)
        if self.scfg.get("pauses", "profile") == "fixed":
            return pause_seconds(self.profile, kind, self.scfg.get("fixed_pauses") or {})
        if self.quality == "identical":
            val = self._twin_pause(kind, i)
            if val is not None:
                return val
        lo, hi = pause_range(self.profile, kind)
        base = pause_seconds(self.profile, kind)
        rng = random.Random(self.base_seed + i)
        # 在你的常见停顿范围内轻微波动（偏向中位数），避免机械感
        val = base + (rng.random() - 0.5) * (hi - lo) * 0.6
        return float(max(0.08, val))

    def _layout(self, results: List[SegmentResult]) -> List[Tuple[float, int]]:
        """算出每句的起点（秒）和长度（采样数），写进 r.start / r.end。字幕和两个版本都用同一套时间。
        同时记下每两句之间的停顿目标（_pause_targets，秒）和种类（_pause_kinds）：「一模一样」量了再改时用。"""
        sr = max(r.sr for r in results)
        timed = any(r.segment.cue_start is not None for r in results)
        mult = self._speed_multiplier()
        cursor = LEAD_IN
        layout: List[Tuple[float, int]] = []
        self._pause_targets: List[Optional[float]] = []
        self._pause_kinds: List[str] = []
        for i, r in enumerate(results):
            n = len(resample(r.wav, r.sr, sr)) if r.sr != sr else len(r.wav)
            if timed and r.segment.cue_start is not None:
                start = r.segment.cue_start
                if start < cursor:  # 不能和上一句叠在一起（以前允许往回 20 毫秒：两句重叠、字幕时间也重叠）
                    if start + 0.5 < cursor:
                        self.warnings.append(f"第 {i + 1} 句比字幕时间轴晚了 {cursor - start:.1f} 秒（上一句太长）")
                    start = cursor
            else:
                start = cursor
            r.start, r.end = start, start + n / sr
            layout.append((start, n))
            kind = r.segment.pause_after
            self._pause_kinds.append("explicit" if isinstance(kind, (int, float)) else str(kind))
            if timed:
                # 句子之间至少留一点绝对静音（以前字幕挨着时两句之间一点停顿都没有）
                cursor = r.end + (TIMED_MIN_CLAUSE_GAP if r.segment.pause_after == "clause" else TIMED_MIN_GAP)
                self._pause_targets.append(None)
            else:
                pause = self._pause(r.segment, i)
                if not isinstance(r.segment.pause_after, (int, float)):
                    pause /= mult  # 说得慢，停顿也按比例长一点（讲稿里写明的秒数不变）
                cursor = r.end + pause
                self._pause_targets.append(pause)
        return layout

    def _measure_gaps(self, audio: np.ndarray, sr: int, layout: List[Tuple[float, int]]) -> List[Optional[float]]:
        """量每两句之间的停顿有多长：用量你本人停顿的同一个方法（utils.audio.silent_runs：10 ms 一帧、40 ms 窗、
        整段音频的自动静音阈值、至少 120 ms），找跨过这两句之间那段数字静音的静音区间。量不到（比 120 ms 短）是 None。"""
        runs = silent_runs(audio, sr, chunked=True)  # 整篇音频很长：逐帧电平分段算（结果一样，内存少很多）
        out: List[Optional[float]] = []
        for i in range(len(layout) - 1):
            end = layout[i][0] + layout[i][1] / sr
            mid = 0.5 * (end + layout[i + 1][0])
            hit = next(((a, b) for a, b in runs if a <= mid <= b), None)
            out.append(round(hit[1] - hit[0], 3) if hit else None)
        return out

    def _fit_pauses(self, layout: List[Tuple[float, int]], pieces: List[Tuple[np.ndarray, int]], sr: int,
                    gains: Optional[List[float]] = None) -> Tuple[List[Tuple[float, int]], Dict[str, Any]]:
        """停顿量了再改（设计方案 §1.9 第 3 条）：拼好以后用量你本人停顿的同一个方法量每两句之间的停顿，
        和目标差多少就把后面的句子挪多少（每次最多 ±0.15 秒；两句之间的数字静音至少 0.08 秒，句子不会叠在一起），
        再拼、再量，一共两遍。只挪句子的位置：停顿里照样全是 0。出错时用没改的停顿。"""
        targets = list(getattr(self, "_pause_targets", []) or [])
        info: Dict[str, Any] = {"passes": 0}
        if len(layout) < 2 or not any(t is not None for t in targets[:len(layout) - 1]):
            return layout, info
        # 每句的起点放在量停顿用的 10 毫秒一帧的格子上：句子挪动以后，它两头落在哪一帧跟着整帧整帧地挪，
        # 量出来的停顿就正好变多少（不放在格子上时，同样挪 5 毫秒，量出来可能变 0 也可能变 10 毫秒，改两遍还会差 20 毫秒）
        grid = max(1, int(round(sr * 0.01))) / float(sr)

        def snap(x: float, floor: float) -> float:
            return max(math.ceil(floor / grid - 1e-9), int(round(x / grid))) * grid

        cur = list(layout)
        try:
            for _ in range(FIT_PASSES):
                _check_cancel()
                gaps = self._measure_gaps(self._render(cur, pieces, sr, gains), sr, cur)
                new = [cur[0]]
                for i in range(1, len(cur)):
                    end_old = cur[i - 1][0] + cur[i - 1][1] / sr
                    zero_gap = cur[i][0] - end_old
                    t, m = targets[i - 1], gaps[i - 1]
                    if m is None:
                        m = zero_gap  # 量不到（比 120 ms 还短）：至少有这么长的数字静音
                    delta = float(np.clip(t - m, -FIT_STEP, FIT_STEP)) if t is not None else 0.0
                    end_new = new[i - 1][0] + new[i - 1][1] / sr
                    start = end_new + max(FIT_MIN_GAP, zero_gap + delta)
                    new.append((snap(start, end_new + FIT_MIN_GAP), cur[i][1]))
                cur = new
                info["passes"] += 1
            info["grid_s"] = round(grid, 6)
        except Exception as exc:  # noqa: BLE001 - 停止按钮不是 Exception，照常传出去
            log.warning(f"停顿量了再改这一步出错了（{exc}），按没改的停顿拼接")
            return layout, {"passes": 0, "error": str(exc)[:200]}
        return cur, info

    def _levels(self, results: List[SegmentResult], layout: List[Tuple[float, int]], sr: int
                ) -> Tuple[Optional[List[float]], Dict[str, Any]]:
        """每句一个固定的音量系数（设计方案 §1.9 第 4 条）：
        1. 每句说话时的响度 − 所有句子的中位数 = 这一句的音量差 d；
        2. 按你本人句子之间的音量差（twin_profile.json 的 loudness）缩小：乘 min(1, 你本人的标准差 / 这次的标准差)，
           再限制在你本人的 p05~p95 之间；
        3. 整篇的响度调到你原来录音的响度（和以前的目标一样）；
        4. 哪一句的最高点会超过 −1 dBFS，就把这一句单独调低——不用限幅器，也不整篇压。
        只乘系数：停顿里的 0 还是 0。返回 (每句的系数, 记录)；设置里关掉了音量调整时返回 (None, …)。"""
        target = self._target_lufs()
        if target is None:
            return None, {"applied": False, "why": "设置里关掉了音量调整（loudness: off）"}
        twin = (self._identical_ctx() or {}).get("twin") or {}
        tl = twin.get("loudness") or {}
        her_sd = tl.get("sd") if isinstance(tl.get("sd"), (int, float)) else None
        p05 = tl.get("p05") if isinstance(tl.get("p05"), (int, float)) else None
        p95 = tl.get("p95") if isinstance(tl.get("p95"), (int, float)) else None
        wavs = [resample(r.wav, r.sr, sr) if r.sr != sr else np.asarray(r.wav, dtype=np.float32) for r in results]
        levels = [speech_level_db(w, sr) for w in wavs]
        ok = [i for i, v in enumerate(levels) if v is not None]
        gain_db = [0.0] * len(results)
        before_sd = None
        shrink = 1.0
        if ok:
            med = float(np.median([levels[i] for i in ok]))
            d = {i: float(levels[i]) - med for i in ok}
            if len(ok) >= 2:
                before_sd = float(np.std([d[i] for i in ok], ddof=1))
            if her_sd is not None and before_sd and before_sd > 0:
                shrink = min(1.0, float(her_sd) / before_sd)
            for i in ok:
                dd = shrink * d[i]
                if p05 is not None and p95 is not None and p05 <= p95:
                    dd = float(np.clip(dd, p05, p95))
                gain_db[i] = dd - d[i]
        rendered = self._render(layout, [(w, sr) for w in wavs], sr, [10.0 ** (g / 20.0) for g in gain_db])
        cur = measure_lufs(rendered, sr)
        glob = float(target) - cur if math.isfinite(cur) and cur > -69.0 else 0.0
        lowered = []
        for i, w in enumerate(wavs):
            g = gain_db[i] + glob
            peak = float(np.max(np.abs(w))) if w.size else 0.0
            if peak > 0 and 20.0 * math.log10(peak) + g > PEAK_CEILING_DB:
                g = PEAK_CEILING_DB - 20.0 * math.log10(peak)
                lowered.append(i + 1)
            gain_db[i] = g
        info = {"applied": True, "her_sd": None if her_sd is None else round(float(her_sd), 2),
                "her_p05": p05, "her_p95": p95, "before_sd": None if before_sd is None else round(before_sd, 2),
                "shrink": round(shrink, 4), "target_lufs": round(float(target), 2), "global_db": round(glob, 2),
                "gains_db": [round(g, 2) for g in gain_db], "peak_lowered": lowered}
        if lowered:
            log.info(f"第 {'、'.join(str(i) for i in lowered)} 句调到目标音量会超过 −1 dBFS，这几句单独调低了一点"
                     "（不用限幅器，整篇的响度可能比目标低一点，报告里写着实测的数）")
        return [10.0 ** (g / 20.0) for g in gain_db], info

    def _render(self, layout: List[Tuple[float, int]], pieces: List[Tuple[np.ndarray, int]], sr: int,
                gains: Optional[Sequence[float]] = None) -> np.ndarray:
        """按排好的时间把每句放进一条全是 0 的音轨：停顿、开头、结尾都是绝对的数字静音。
        gains：每句乘一个固定的系数（「一模一样」调每句音量，只乘系数：0 还是 0）。"""
        total = (max((start + n / sr for start, n in layout), default=0.0)) + LEAD_OUT
        out = np.zeros(int(total * sr) + 1, dtype=np.float32)
        for k, ((start, n), (wav, wsr)) in enumerate(zip(layout, pieces)):
            w = resample(wav, wsr, sr) if wsr != sr else np.asarray(wav, dtype=np.float32)
            w = fade(w[:n], sr, in_ms=4.0, out_ms=8.0)
            if gains is not None and k < len(gains) and float(gains[k]) != 1.0:
                w = w * np.float32(gains[k])
            a = int(round(start * sr))
            w = w[: max(0, len(out) - a)]
            out[a:a + len(w)] += w
        return out

    def _target_lufs(self) -> Optional[float]:
        opt = self.scfg.get("loudness", "profile")
        if opt in (None, "off", False):
            return None
        if opt == "profile":
            loud = self.profile.get("loudness") or {}
            val = loud.get("source_lufs") or loud.get("clip_lufs")
            return float(val) if val is not None else -18.0
        return float(opt)

    def _write_audio(self, audio: np.ndarray, sr: int, out_path: Path, loudness: bool = True,
                     comment: Optional[str] = None) -> Path:
        """写一个给老师的音频文件。out_path 是最后的名字（已经带「_模型名」和扩展名，见 narrate）：先写临时文件，
        写好了才换成这个名字（写到一半出错不会留下半个文件，也不会碰到旁边同名的别的文件）。
        loudness：整篇调到目标响度（「一模一样」每句已经调好了，不再调）。comment：写进文件里面的注释（模型名）。"""
        target = self._target_lufs() if loudness else None
        if target is not None:
            audio = normalize_lufs(audio, sr, target, ceiling_db=-1.0)  # 只乘一个系数：0 还是 0
        out_path = Path(out_path)
        fmt = out_path.suffix.lower().lstrip(".") or "wav"
        tmp = atomic.tmp_for(out_path).with_suffix(".wav")
        enc = atomic.tmp_for(out_path).with_suffix(".enc")
        try:
            save_audio(tmp, audio, sr, comment=comment)
            log.info(f"输出响度 {measure_lufs(audio, sr):.1f} LUFS，时长 {len(audio) / sr:.1f} 秒")
            if fmt in ("mp3", "m4a", "flac"):
                encode(tmp, enc, metadata={"comment": comment} if comment else None, fmt=fmt)
                atomic.finish(enc, out_path)
                return out_path
            atomic.finish(tmp, out_path)
            return out_path
        finally:
            tmp.unlink(missing_ok=True)
            enc.unlink(missing_ok=True)

    def _write_srt(self, results: List[SegmentResult], path: Path) -> Path:
        from voicetwin.data.subtitles import Cue, write_srt

        cues = [Cue(r.start, r.end, r.segment.display) for r in results]
        return write_srt(cues, path)


def _check_cancel_or_stop(narrator: Any) -> None:
    """检查停止按钮；点了停止时先把后台量显卡的线程停下再报出去。"""
    try:
        _check_cancel()
    except BaseException:
        narrator._stop_gpu_sampler()
        raise


def _weighted_pct(results: List[SegmentResult]) -> Optional[float]:
    vals = [(r.pct, max(r.end - r.start, len(r.wav) / max(r.sr, 1))) for r in results if r.pct is not None]
    if not vals or sum(d for _, d in vals) <= 0:
        return None
    return round(float(np.average([p for p, _ in vals], weights=[d for _, d in vals])), 1)


def _reason(exc: Optional[BaseException]) -> str:
    if exc is None:
        return "未知原因"
    try:
        from voicetwin.errors import explain

        return explain(exc).title
    except Exception:
        return str(exc)[:80]


def _is_fatal(exc: BaseException) -> bool:
    try:
        from voicetwin.errors import is_fatal

        return bool(is_fatal(exc))
    except Exception:
        return False


def result_rows(segments: Sequence[Dict[str, Any]]) -> List[List[Any]]:
    """逐句结果表（#, 句子, 像你本人（%）, 状态, 提示），# 从 1 开始，和 --redo 的编号一致。"""
    rows = []
    for s in segments:
        pct = s.get("pct")
        hint = s.get("hint") or "；".join(s.get("issues") or [])
        rows.append([s.get("index"), s.get("text", ""), "" if pct is None else f"{pct:.1f}",
                     s.get("status") or ("⚠️" if hint else "✅"), hint])
    return rows


def clear_cache(project: Project) -> int:
    seg_dir = project.cache_dir / "segments"
    n = sum(1 for p in seg_dir.rglob("*.wav") if ".dn" not in p.name) if seg_dir.exists() else 0
    shutil.rmtree(seg_dir, ignore_errors=True)
    return n
