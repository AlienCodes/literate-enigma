"""说话风格档案：从你的录音里统计语速、停顿习惯、音高和响度。

合成时用它来：
- 在句与句、段与段之间插入和你本人习惯一致的停顿；
- 自动校准语速（快慢和你原来讲课一样）；
- 把最终音频的响度调到和你原来的录音一致，方便直接剪进课程里；
- 给候选音频打分（音高/语速越接近你本人越好）。
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from voicetwin.project import Project
from voicetwin.style.prosody import f0_stats, quantiles
from voicetwin.utils.audio import load_audio, measure_lufs
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import SENT_END_CHARS, ends_clause, ends_sentence

log = get_logger("profile")

DEFAULT_PAUSES = {"clause": 0.25, "sentence": 0.55, "paragraph": 1.1}
DEFAULT_RATE = {"zh": 4.6, "en": 4.2}


def build_profile(project: Project, max_pitch_clips: int = 60) -> Dict[str, Any]:
    records = project.load_manifest(only_kept=True)
    if not records:
        raise RuntimeError("还没有可用的素材，请先运行素材准备。")
    profile: Dict[str, Any] = {"voice": project.voice, "clips": len(records),
                               "minutes": round(sum(r["duration"] for r in records) / 60.0, 1)}

    # 语速（音节/秒，不含停顿）
    profile["rate"] = {}
    for lang in ("zh", "en"):
        rates = [r["rate"] for r in records if r.get("lang") == lang and r.get("rate")]
        if rates:
            profile["rate"][lang] = quantiles(rates)

    # 停顿
    sentence_gaps: List[float] = []
    clause_gaps: List[float] = []
    all_gaps: List[float] = []
    for r in records:
        text = r.get("text", "")
        ga = r.get("gap_after")
        if ga is not None and 0.12 <= ga <= 4.0:
            all_gaps.append(ga)
            if ends_sentence(text):
                sentence_gaps.append(ga)
            elif ends_clause(text) or ga < 0.6:
                clause_gaps.append(ga)
        inner_sentence_marks = sum(text[:-1].count(c) for c in SENT_END_CHARS)
        if inner_sentence_marks == 0:
            clause_gaps += [p for p in (r.get("pauses") or []) if 0.12 <= p <= 1.5]
    pauses: Dict[str, Any] = {"clause": DEFAULT_PAUSES["clause"], "sentence": DEFAULT_PAUSES["sentence"],
                              "paragraph": DEFAULT_PAUSES["paragraph"], "stats": {}}
    if len(clause_gaps) >= 5:
        pauses["clause"] = float(np.clip(np.median(clause_gaps), 0.12, 0.8))
        pauses["stats"]["clause"] = quantiles(clause_gaps)
    if len(sentence_gaps) >= 5:
        pauses["sentence"] = float(np.clip(np.median(sentence_gaps), 0.25, 1.6))
        pauses["stats"]["sentence"] = quantiles(sentence_gaps)
    elif len(all_gaps) >= 5:
        pauses["sentence"] = float(np.clip(np.median(all_gaps), 0.25, 1.6))
    if len(all_gaps) >= 10:
        pauses["paragraph"] = float(np.clip(np.percentile(all_gaps, 90), pauses["sentence"] + 0.25, 3.0))
    else:
        pauses["paragraph"] = max(pauses["paragraph"], pauses["sentence"] + 0.4)
    pauses["stats"]["all"] = quantiles(all_gaps) if all_gaps else {}
    profile["pauses"] = pauses

    # 音高
    profile["pitch"] = {}
    for lang in ("zh", "en"):
        items = [r for r in records if r.get("lang") == lang]
        if not items:
            continue
        step = max(1, len(items) // max_pitch_clips)
        meds, stds = [], []
        for r in items[::step][:max_pitch_clips]:
            wav, sr = load_audio(project.abspath(r["path"]), sr=16000)
            st = f0_stats(wav, sr)
            if st:
                meds.append(st["f0_median"])
                stds.append(st["f0_semitone_std"])
        if meds:
            profile["pitch"][lang] = {"f0_median": float(np.median(meds)), "semitone_std": float(np.median(stds)),
                                      "f0_p10": float(np.percentile(meds, 10)), "f0_p90": float(np.percentile(meds, 90))}

    # 响度：优先用原始录音（清理前）的响度，这样合成结果可以无缝剪进原课程
    sources = project.read_json(project.sources_path, {}) or {}
    src_lufs = [v.get("orig_lufs") for v in sources.values() if isinstance(v.get("orig_lufs"), (int, float))]
    src_lufs = [x for x in src_lufs if -60 < x < 0]
    clip_lufs = []
    for r in records[:: max(1, len(records) // 40)][:40]:
        wav, sr = load_audio(project.abspath(r["path"]))
        clip_lufs.append(measure_lufs(wav, sr))
    profile["loudness"] = {
        "source_lufs": float(np.median(src_lufs)) if src_lufs else None,
        "clip_lufs": float(np.median(clip_lufs)) if clip_lufs else None,
    }
    project.write_json(project.profile_path, profile)
    _log_profile(profile)
    return profile


def _log_profile(p: Dict[str, Any]) -> None:
    for lang, name in (("zh", "中文"), ("en", "英文")):
        if lang in p.get("rate", {}):
            log.info(f"  {name}语速：{p['rate'][lang]['p50']:.2f} 音节/秒（不含停顿）")
        if lang in p.get("pitch", {}):
            log.info(f"  {name}音高：{p['pitch'][lang]['f0_median']:.0f} Hz，起伏 {p['pitch'][lang]['semitone_std']:.1f} 半音")
    pz = p.get("pauses", {})
    log.info(f"  停顿习惯：逗号 {pz.get('clause', 0):.2f}s / 句号 {pz.get('sentence', 0):.2f}s / 段落 {pz.get('paragraph', 0):.2f}s")


def target_rate(profile: Dict[str, Any], lang: str) -> float:
    rate = (profile.get("rate") or {}).get(lang) or (profile.get("rate") or {}).get("zh" if lang == "en" else "en")
    if rate and rate.get("p50"):
        return float(rate["p50"])
    return DEFAULT_RATE.get(lang, 4.5)


def pause_seconds(profile: Dict[str, Any], kind: str, fixed: Dict[str, float] = None) -> float:
    if fixed:
        return float(fixed.get(kind, DEFAULT_PAUSES.get(kind, 0.5)))
    pauses = profile.get("pauses") or {}
    return float(pauses.get(kind, DEFAULT_PAUSES.get(kind, 0.5)))


def pause_range(profile: Dict[str, Any], kind: str) -> tuple:
    """停顿的自然波动范围（25%~75% 分位），用于让停顿不死板。"""
    stats = ((profile.get("pauses") or {}).get("stats") or {}).get(kind) or {}
    base = pause_seconds(profile, kind)
    lo, hi = stats.get("p25"), stats.get("p75")
    if lo is None or hi is None:
        return base * 0.85, base * 1.15
    return float(min(lo, base)), float(max(hi, base))
