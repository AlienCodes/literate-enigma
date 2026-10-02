"""挑选参考音频：合成时告诉模型"用这种语气说话"。

好的参考音频 = 你本人、干净、一句完整的话、语速和音高都接近你平时讲课的状态、3~10 秒。
中文、英文分别挑；如果素材里有疑问句/感叹句，也各挑一条，合成疑问句时用疑问语气的参考。
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

import numpy as np

from voicetwin.project import Project
from voicetwin.utils.audio import load_audio, save_audio, trim_silence
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import ends_sentence, normalize_for_cer, sentence_kind

log = get_logger("references")


def _score(r: Dict[str, Any], med_rate: float) -> float:
    sim = r.get("speaker_sim")
    sim = 0.8 if sim is None else float(sim)
    snr = min(float(r.get("snr") or 20.0), 45.0) / 45.0
    lp = (r.get("asr") or {}).get("avg_logprob")
    lp_n = 0.7 if lp is None else float(np.clip(1.0 + lp, 0.0, 1.0))
    rate = r.get("rate") or med_rate
    rate_dev = abs(math.log(max(rate, 0.1) / max(med_rate, 0.1)))
    dur = float(r.get("duration", 6.0))
    dur_pref = 1.0 - min(abs(dur - 6.5) / 6.5, 1.0)
    long_pause = 1.0 if max(r.get("pauses") or [0.0]) > 0.9 else 0.0
    return 3.0 * sim + 1.0 * snr + 0.6 * lp_n - 2.5 * rate_dev + 0.6 * dur_pref - 0.6 * long_pause


def select_references(project: Project, records: List[Dict[str, Any]], pcfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    rcfg = pcfg.get("references", {}) or {}
    count = int(rcfg.get("count", 8))
    min_d, max_d = float(rcfg.get("min_duration", 3.5)), float(rcfg.get("max_duration", 9.5))
    pool = [r for r in records if r["keep"] and r.get("split", "train") == "train" and r.get("rate")
            and r.get("lang") in ("zh", "en") and r.get("forced_cuts", 0) == 0
            and min_d - 0.5 <= r["duration"] <= max_d + 1.5 and ends_sentence(r.get("text", ""))]
    if not pool:  # 放宽条件
        pool = [r for r in records if r["keep"] and r.get("rate") and r.get("lang") in ("zh", "en")
                and min_d - 0.5 <= r["duration"] <= max_d + 1.5]
    by_lang: Dict[str, List[Dict[str, Any]]] = {}
    for r in pool:
        by_lang.setdefault(r["lang"], []).append(r)
    total = sum(len(v) for v in by_lang.values()) or 1

    chosen: List[Dict[str, Any]] = []
    for lang, items in by_lang.items():
        med = float(np.median([r["rate"] for r in items]))
        for r in items:
            r["_ref_score"] = _score(r, med)
        items.sort(key=lambda r: -r["_ref_score"])
        quota = max(2, round(count * len(items) / total))
        picked: List[Dict[str, Any]] = []
        used_sources: Dict[str, int] = {}
        seen_texts: set = set()  # 同一句话（例如每节课都说的开场白）只选一次，让参考语气更多样
        for kind in ("question", "exclaim"):  # 各挑一条疑问句 / 感叹句
            best = next((r for r in items if sentence_kind(r["text"]) == kind), None)
            if best is not None:
                picked.append(best)
                seen_texts.add(normalize_for_cer(best["text"]))
        statements = [r for r in items if sentence_kind(r["text"]) == "statement"]
        for r in statements:  # 陈述句优先分散到不同视频
            if len([p for p in picked if sentence_kind(p["text"]) == "statement"]) >= quota:
                break
            if used_sources.get(r.get("source", ""), 0) >= 2 and len(statements) > quota * 2:
                continue
            key = normalize_for_cer(r["text"])
            if key in seen_texts:
                continue
            seen_texts.add(key)
            picked.append(r)
            used_sources[r.get("source", "")] = used_sources.get(r.get("source", ""), 0) + 1
        chosen += picked

    refs: List[Dict[str, Any]] = []
    project.refs_dir.mkdir(parents=True, exist_ok=True)
    for old in project.refs_dir.glob("*.wav"):
        old.unlink()
    for r in chosen:
        wav, sr = load_audio(project.abspath(r["path"]))
        trimmed, _, _ = trim_silence(wav, sr, pad_ms=80)
        dur = len(trimmed) / sr
        if not (min_d - 0.3 <= dur <= max_d + 0.3):
            # 太长就从句中停顿处截短不可靠，直接跳过；太短也跳过
            continue
        path = project.refs_dir / f"{r['id']}.wav"
        save_audio(path, trimmed, sr)
        refs.append({
            "id": r["id"],
            "path": project.relpath(path),
            "text": r["text"],
            "lang": r["lang"],
            "kind": sentence_kind(r["text"]),
            "duration": round(dur, 2),
            "score": round(float(r.get("_ref_score", 0.0)), 3),
            "source": r.get("source", ""),
            "rate": r.get("rate"),
        })
    for r in records:
        r.pop("_ref_score", None)
    refs.sort(key=lambda x: (x["lang"], x["kind"] != "statement", -x["score"]))
    project.write_json(project.references_path, refs)
    if not refs:
        log.warning("没有挑到合适的参考音频（需要 3.5~9.5 秒、完整一句话的片段）。可在 transcripts.csv 里检查文字后重试。")
    else:
        for lang in ("zh", "en"):
            best = next((x for x in refs if x["lang"] == lang), None)
            if best:
                log.info(f"  主参考（{lang}）：{best['text']}（{best['duration']} 秒）")
    return refs


def pick_reference(refs: List[Dict[str, Any]], lang: str, kind: str = "statement",
                   prefer_id: str = "") -> Dict[str, Any]:
    """为一句话挑参考音频：先按指定 id，再按语言+句型，最后退而求其次。"""
    if not refs:
        raise RuntimeError("这个声音还没有参考音频，请先运行素材准备（voicetwin prepare）。")
    if prefer_id:
        for r in refs:
            if r["id"] == prefer_id or r["path"] == prefer_id:
                return r
    same_lang = [r for r in refs if r["lang"] == lang] or refs
    same_kind = [r for r in same_lang if r["kind"] == kind]
    if same_kind:
        return same_kind[0]
    statements = [r for r in same_lang if r["kind"] == "statement"]
    return (statements or same_lang)[0]


def aux_references(refs: List[Dict[str, Any]], main: Dict[str, Any], n: int) -> List[Dict[str, Any]]:
    """额外参考（融合音色用）：同语言、陈述句、不同于主参考。"""
    if n <= 0:
        return []
    others = [r for r in refs if r["id"] != main["id"] and r["lang"] == main["lang"] and r["kind"] == "statement"]
    return others[:n]
