"""素材准备总流程：视频/录音 → 干净、带文字、只有你本人声音的训练片段。

支持增量：以后再加新的视频，重新运行只会处理新文件，之前手动校对过的内容不会丢。
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

import numpy as np

from voicetwin.data.asr import Transcriber, hf_mirror_hint, looks_hallucinated
from voicetwin.data.enhance import enhance_file
from voicetwin.data.slicer import find_segments
from voicetwin.data.subtitles import find_sidecar_subtitle, group_cues, parse_subtitles, refine_boundaries
from voicetwin.project import Project
from voicetwin.style.prosody import rate_stats
from voicetwin.utils.audio import clip_ratio, estimate_snr, load_audio, save_audio
from voicetwin.utils.ffmpeg import extract_audio
from voicetwin.utils.log import get_logger, setup_logging
from voicetwin.utils.textutil import detect_lang, ends_sentence, safe_name, short_hash, syllable_count

log = get_logger("prepare")

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".wmv", ".m4v", ".ts", ".mts", ".3gp"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma", ".amr"}
MEDIA_EXTS = VIDEO_EXTS | AUDIO_EXTS

ProgressFn = Callable[[float, str], None]


def discover_sources(inputs: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for item in inputs:
        p = Path(item).expanduser()
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in MEDIA_EXTS)
        elif p.is_file() and p.suffix.lower() in MEDIA_EXTS:
            files.append(p)
        elif p.exists():
            log.warning(f"跳过不支持的文件类型：{p}")
        else:
            log.warning(f"路径不存在：{p}")
    seen, unique = set(), []
    for f in files:
        key = str(f.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(f.resolve())
    return unique


def source_id(path: Path) -> str:
    st = path.stat()
    return f"{safe_name(path.stem, 24)}_{short_hash(str(path.resolve()), st.st_size, n=6)}"


def _progress(cb: Optional[ProgressFn], frac: float, msg: str) -> None:
    log.info(msg)
    if cb:
        try:
            cb(max(0.0, min(1.0, frac)), msg)
        except Exception:
            pass


# ============================================================================ 切片
def _slice_source(project: Project, sid: str, media: Path, clean_wav: Path, pcfg: Dict[str, Any]
                  ) -> List[Dict[str, Any]]:
    wav, sr = load_audio(clean_wav)
    mode = str(pcfg.get("segmentation", "auto")).lower()
    subtitle = find_sidecar_subtitle(media) if mode in ("auto", "srt") else None
    if mode == "srt" and subtitle is None:
        log.warning(f"  {media.name} 没有找到同名字幕，改用静音切分")
    min_d, max_d = float(pcfg.get("min_duration", 2.0)), float(pcfg.get("max_duration", 12.0))
    records: List[Dict[str, Any]] = []
    if subtitle is not None:
        cues = parse_subtitles(subtitle)
        log.info(f"  使用字幕 {subtitle.name}（{len(cues)} 条）切分")
        for k, g in enumerate(group_cues(cues, min_duration=3.0, max_duration=max_d)):
            s, e = refine_boundaries(wav, sr, g.start, g.end)
            records.append({"_s": s, "_e": e, "text": g.text, "gap_before": g.gap_before, "gap_after": g.gap_after,
                            "seg_mode": "srt", "forced_cuts": 0})
    else:
        scfg = pcfg.get("slicer", {}) or {}
        thr = scfg.get("threshold_db", "auto")
        segs = find_segments(
            wav, sr,
            threshold_db=None if thr in (None, "auto") else float(thr),
            min_interval_ms=float(scfg.get("min_interval_ms", 300)),
            hop_ms=float(scfg.get("hop_ms", 10)),
            max_sil_kept_ms=float(scfg.get("max_sil_kept_ms", 400)),
            min_duration=min_d,
            max_duration=max_d,
        )
        for seg in segs:
            records.append({"_s": seg.start, "_e": seg.end, "text": "", "gap_before": seg.gap_before,
                            "gap_after": seg.gap_after, "seg_mode": "energy", "forced_cuts": seg.forced_cuts,
                            "inner_gaps": seg.inner_gaps})
    out = []
    for k, rec in enumerate(records):
        cid = f"{sid}_{k:04d}"
        s, e = rec.pop("_s"), rec.pop("_e")
        clip = wav[s:e]
        if len(clip) < sr * 0.5:
            continue
        path = project.clips_dir / f"{cid}.wav"
        save_audio(path, clip, sr)
        rec.update({
            "id": cid,
            "path": project.relpath(path),
            "source": sid,
            "source_file": str(media),
            "start": round(s / sr, 3),
            "end": round(e / sr, 3),
            "duration": round(len(clip) / sr, 3),
            "lang": detect_lang(rec["text"]) if rec["text"] else "",
            "keep": True,
            "split": "train",
            "drop_reason": "",
        })
        out.append(rec)
    return out


# ============================================================================ 统计 & 过滤
def _clip_stats(project: Project, rec: Dict[str, Any]) -> None:
    wav, sr = load_audio(project.abspath(rec["path"]))
    stats = rate_stats(wav, sr, rec.get("text", ""))
    rec.update({
        "voiced": round(stats["voiced"], 3),
        "pauses": stats["pauses"],
        "syllables": stats["syllables"],
        "rate": round(stats["rate"], 3) if stats["rate"] else None,
        "snr": round(estimate_snr(wav, sr), 1),
        "clip_ratio": round(clip_ratio(wav), 5),
    })


def _embedding_cache(project: Project, encoder_name: str) -> Dict[str, np.ndarray]:
    path = project.cache_dir / f"emb_{encoder_name}.npz"
    if path.exists():
        with np.load(path) as data:
            return {k: data[k] for k in data.files}
    return {}


def _save_embedding_cache(project: Project, encoder_name: str, cache: Dict[str, np.ndarray]) -> None:
    project.cache_dir.mkdir(parents=True, exist_ok=True)
    np.savez(project.cache_dir / f"emb_{encoder_name}.npz", **cache)


def apply_filters(project: Project, records: List[Dict[str, Any]], pcfg: Dict[str, Any], cfg: Dict[str, Any],
                  progress: Optional[ProgressFn] = None) -> None:
    fcfg = pcfg.get("filter", {}) or {}
    min_d, max_d = float(pcfg.get("min_duration", 2.0)), float(pcfg.get("max_duration", 12.0))

    def auto_reason(r: Dict[str, Any]) -> str:
        text = r.get("text", "")
        if not text or syllable_count(text) < 2:
            return "没有识别出文字"
        if looks_hallucinated(text):
            return "疑似识别错误"
        if r.get("lang") not in ("zh", "en"):
            return "语言不是中文/英文"
        if r["duration"] < min_d:
            return "太短"
        if r["duration"] > max_d + 1.0:
            return "太长"
        if (r.get("clip_ratio") or 0) > float(fcfg.get("max_clip_ratio", 0.002)):
            return "有爆音"
        asr = r.get("asr") or {}
        if asr.get("avg_logprob") is not None and asr["avg_logprob"] < float(fcfg.get("min_avg_logprob", -1.0)):
            return "识别置信度低"
        if asr.get("no_speech_prob") is not None and asr["no_speech_prob"] > float(fcfg.get("max_no_speech_prob", 0.6)):
            return "可能不是语音"
        if not r.get("rate"):
            return "没有有效语音"
        return ""

    for r in records:
        r["drop_reason"] = auto_reason(r)

    # 语速离群：多半是文字和音频对不上
    for lang in ("zh", "en"):
        rates = [r["rate"] for r in records if not r["drop_reason"] and r.get("lang") == lang and r.get("rate")]
        if len(rates) < 8:
            continue
        med = float(np.median(rates))
        lo, hi = med * float(fcfg.get("rate_outlier_low", 0.5)), med * float(fcfg.get("rate_outlier_high", 1.8))
        for r in records:
            if not r["drop_reason"] and r.get("lang") == lang and r.get("rate") and not (lo <= r["rate"] <= hi):
                r["drop_reason"] = "语速异常（文字可能不对）"

    # 声纹离群：剔除不是你本人的片段
    if fcfg.get("speaker_outlier", True):
        from voicetwin.eval.speaker import centroid, cosine, get_speaker_encoder

        try:
            encoder = get_speaker_encoder(cfg.get("speaker_encoder", "auto"))
        except Exception as exc:
            log.warning(f"声纹模型不可用，跳过说话人过滤：{exc}")
            encoder = None
        if encoder is not None:
            cache = _embedding_cache(project, encoder.name)
            active = [r for r in records if not r["drop_reason"]]
            for i, r in enumerate(active):
                if r["id"] not in cache:
                    cache[r["id"]] = encoder.embed_file(project.abspath(r["path"]))
                if i % 50 == 0:
                    _progress(progress, 0.8 + 0.1 * i / max(len(active), 1), f"计算声纹 {i}/{len(active)}")
            _save_embedding_cache(project, encoder.name, cache)
            if len(active) >= 5:
                cen = centroid([cache[r["id"]] for r in active])
                for _ in range(2):
                    sims = np.array([cosine(cache[r["id"]], cen) for r in active])
                    thr_cfg = fcfg.get("speaker_min_similarity", "auto")
                    if thr_cfg in (None, "auto"):
                        med = float(np.median(sims))
                        mad = float(np.median(np.abs(sims - med))) * 1.4826
                        thr = float(np.clip(med - 3.5 * max(mad, 0.01), 0.55, 0.8))
                    else:
                        thr = float(thr_cfg)
                    inliers = [r for r, s in zip(active, sims) if s >= thr]
                    if len(inliers) >= 3:
                        cen = centroid([cache[r["id"]] for r in inliers])
                for r in active:
                    r["speaker_sim"] = round(cosine(cache[r["id"]], cen), 4)
                    if encoder.reliable and r["speaker_sim"] < thr:
                        r["drop_reason"] = "声音不像本人（可能是别人说话）"
                np.save(project.root / f"speaker_centroid.{encoder.name}.npy", cen)

    for r in records:
        if r.get("manual_keep") is not None:
            r["keep"] = bool(r["manual_keep"])
        else:
            r["keep"] = not r["drop_reason"]


def assign_splits(records: List[Dict[str, Any]], count: int) -> None:
    """留出一小部分片段不参与训练，用于自动挑选最佳模型和校准语速。"""
    kept = [r for r in records if r["keep"]]
    for r in records:
        if not r["keep"]:
            r["split"] = "train"
    count = min(count, len(kept) // 8)
    current = [r for r in kept if r.get("split") == "val"]
    need = count - len(current)
    if need <= 0:
        for r in current[count:]:
            r["split"] = "train"
        return
    pool = [r for r in kept if r.get("split") != "val" and 3.0 <= r["duration"] <= 9.0
            and r.get("forced_cuts", 0) == 0 and ends_sentence(r.get("text", ""))]
    if len(pool) < need:
        pool = [r for r in kept if r.get("split") != "val" and 2.5 <= r["duration"] <= 10.0]
    langs: Dict[str, List[Dict[str, Any]]] = {}
    for r in pool:
        langs.setdefault(r["lang"], []).append(r)
    total = sum(len(v) for v in langs.values()) or 1
    for lang, items in langs.items():
        share = max(2 if len(items) >= 10 else 0, round(need * len(items) / total))
        items.sort(key=lambda r: (r["source"], r["start"]))
        if share <= 0:
            continue
        idx = np.linspace(0, len(items) - 1, min(share, len(items))).round().astype(int)
        for i in sorted(set(idx.tolist())):
            items[i]["split"] = "val"


# ============================================================================ 主流程
def prepare(project: Project, inputs: Iterable[str], cfg: Dict[str, Any], progress: Optional[ProgressFn] = None,
            overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from voicetwin.data.references import select_references

    pcfg = dict(cfg.get("prepare", {}))
    if overrides:
        for k, v in overrides.items():
            if isinstance(v, dict):
                pcfg[k] = {**(pcfg.get(k) or {}), **v}
            else:
                pcfg[k] = v
    project.ensure()
    setup_logging(log_file=project.logs_dir / "prepare.log")
    t0 = time.time()
    sources_db: Dict[str, Any] = project.read_json(project.sources_path, {}) or {}
    records: Dict[str, Dict[str, Any]] = {r["id"]: r for r in project.load_manifest()}
    files = discover_sources(inputs)
    if not files and not records:
        raise FileNotFoundError("没有找到任何视频或音频文件。支持：" + " ".join(sorted(MEDIA_EXTS)))
    sr = int(pcfg.get("sample_rate", 44100))

    # 1) 提取 + 清理 + 切片
    for i, media in enumerate(files):
        sid = source_id(media)
        if sources_db.get(sid, {}).get("done"):
            continue
        _progress(progress, 0.05 + 0.35 * i / max(len(files), 1), f"[{i + 1}/{len(files)}] 处理 {media.name}")
        raw = project.raw_dir / f"{sid}.src.wav"
        clean = project.raw_dir / f"{sid}.wav"
        extract_audio(media, raw, sample_rate=sr)
        _, info = enhance_file(raw, clean, pcfg, work_dir=project.raw_dir)
        raw.unlink(missing_ok=True)
        new_recs = _slice_source(project, sid, media, clean, pcfg)
        for r in new_recs:
            records[r["id"]] = r
        wav_dur = sum(r["duration"] for r in new_recs)
        sources_db[sid] = {"file": str(media), "clean": project.relpath(clean), "segments": len(new_recs),
                           "speech_seconds": round(wav_dur, 1), "done": True, **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in info.items()}}
        project.write_json(project.sources_path, sources_db)
        project.save_manifest(records.values())

    # 2) 语音识别
    todo = [r for r in records.values() if not r.get("text") and not r.get("asr_done")]
    asr_cfg = dict(pcfg.get("asr", {}) or {})
    if todo and asr_cfg.get("engine", "faster-whisper") != "none":
        _progress(progress, 0.42, f"语音识别 {len(todo)} 个片段……{hf_mirror_hint()}")
        transcriber = Transcriber(asr_cfg)
        for i, r in enumerate(todo):
            wav16, _ = load_audio(project.abspath(r["path"]), sr=16000)
            res = transcriber.transcribe(wav16)
            r.update({"text": res.text, "lang": res.lang, "asr_done": True,
                      "asr": {"engine": res.engine, "avg_logprob": res.avg_logprob, "no_speech_prob": res.no_speech_prob}})
            if i % 20 == 0:
                _progress(progress, 0.42 + 0.3 * i / len(todo), f"识别 {i + 1}/{len(todo)}：{res.text[:30]}")
                project.save_manifest(records.values())
        project.save_manifest(records.values())
    elif todo:
        log.warning(f"{len(todo)} 个片段没有文字（识别引擎为 none 且没有字幕），它们不会参与训练")

    # 3) 片段统计
    _progress(progress, 0.74, "分析每个片段的语速、停顿和音质……")
    for r in records.values():
        if "voiced" not in r or r.get("_stats_text") != r.get("text"):
            _clip_stats(project, r)
            r["_stats_text"] = r.get("text")

    # 4) 过滤 / 划分 / 参考音频
    recs = sorted(records.values(), key=lambda r: r["id"])
    _progress(progress, 0.8, "过滤低质量片段、剔除不是你本人的声音……")
    apply_filters(project, recs, pcfg, cfg, progress)
    assign_splits(recs, int(pcfg.get("validation_count", 12)))
    project.save_manifest(recs)
    _progress(progress, 0.92, "挑选最具代表性的参考音频……")
    refs = select_references(project, recs, pcfg)
    project.export_csv(recs)
    summary = summarize(project, recs, refs)
    summary["elapsed_min"] = round((time.time() - t0) / 60.0, 1)
    project.write_json(project.root / "prepare_summary.json", summary)
    _progress(progress, 1.0, "素材准备完成")
    return summary


def summarize(project: Project, records: List[Dict[str, Any]], refs: List[Dict[str, Any]]) -> Dict[str, Any]:
    kept = [r for r in records if r["keep"]]
    by_lang: Dict[str, float] = {}
    for r in kept:
        by_lang[r["lang"]] = by_lang.get(r["lang"], 0.0) + r["duration"]
    reasons: Dict[str, int] = {}
    for r in records:
        if not r["keep"]:
            reason = r.get("drop_reason") or "手动删除"
            reasons[reason] = reasons.get(reason, 0) + 1
    warnings = []
    total_min = sum(by_lang.values()) / 60.0
    if total_min < 10:
        warnings.append(f"可用素材只有 {total_min:.1f} 分钟。能训练，但建议 ≥30 分钟，1~3 小时效果最好。")
    if 0 < by_lang.get("en", 0) / 60.0 < 5:
        warnings.append("英文素材不足 5 分钟：英文会带一点「中文腔」。如果要做英文课，建议加入英文讲课录音。")
    if not by_lang.get("en"):
        warnings.append("素材里没有英文。模型仍能说英文，但口音/语气不一定像你；有英文课录音的话请一起加入。")
    return {
        "voice": project.voice,
        "clips_total": len(records),
        "clips_kept": len(kept),
        "minutes_kept": round(total_min, 1),
        "minutes_by_lang": {k: round(v / 60.0, 1) for k, v in by_lang.items()},
        "val_clips": sum(1 for r in kept if r.get("split") == "val"),
        "dropped": reasons,
        "references": [{"id": r["id"], "lang": r["lang"], "kind": r["kind"], "text": r["text"]} for r in refs],
        "warnings": warnings,
        "transcripts_csv": str(project.csv_path),
    }
