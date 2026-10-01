"""素材准备总流程：视频/录音 → 干净、带文字、只有你本人声音的训练片段。

支持增量：以后再加新的视频，重新运行只会处理新文件，之前手动校对过的内容不会丢。
"""

from __future__ import annotations

import errno
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

try:  # U1：停止按钮
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover
    def _check_cancel() -> None:
        return None

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


def _progress(cb: Optional[ProgressFn], frac: float, msg: str, log_it: bool = True) -> None:
    """报告进度。逐段的高频进度传 log_it=False，免得网页日志刷屏。TaskCancelled（停止按钮）照常传出去。"""
    if log_it:
        log.info(msg)
    if cb:
        try:
            cb(max(0.0, min(1.0, frac)), msg)
        except Exception:
            pass


def _size_text(n_bytes: int) -> str:
    if n_bytes >= 1024 ** 3:
        return f"{n_bytes / 1024 ** 3:.1f} GB"
    return f"{max(1, round(n_bytes / 1024 ** 2))} MB"


def _file_size(path: Path) -> int:
    try:
        return max(1, int(path.stat().st_size))
    except OSError:
        return 1


def _friendly_title(exc: BaseException) -> str:
    try:
        from voicetwin.errors import explain

        return explain(exc).title
    except Exception:
        return str(exc)[:120] or type(exc).__name__


def _is_disk_full(exc: BaseException) -> bool:
    if isinstance(exc, OSError) and (exc.errno == errno.ENOSPC or getattr(exc, "winerror", None) == 112):
        return True
    try:
        from voicetwin.errors import explain

        return explain(exc).key == "disk"
    except Exception:
        return False


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

        _progress(progress, 0.80, "加载声纹模型，检查每段话是不是你本人的声音……")
        try:
            encoder = get_speaker_encoder(cfg.get("speaker_encoder", "auto"))
        except Exception as exc:
            log.warning(f"声纹模型不可用，跳过说话人过滤：{exc}")
            encoder = None
        if encoder is not None:
            cache = _embedding_cache(project, encoder.name)
            active = [r for r in records if not r["drop_reason"]]
            todo_emb = [r for r in active if r["id"] not in cache]
            for j, r in enumerate(todo_emb):
                _check_cancel()
                cache[r["id"]] = encoder.embed_file(project.abspath(r["path"]))
                if j % 10 == 0 or j == len(todo_emb) - 1:
                    _progress(progress, 0.80 + 0.10 * (j + 1) / len(todo_emb), f"计算声纹 {j + 1}/{len(todo_emb)}",
                              log_it=(j % 50 == 0 or j == len(todo_emb) - 1))
                if j % 200 == 199:
                    _save_embedding_cache(project, encoder.name, cache)
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
        if r.get("deleted"):  # 老师在校对表里删除的：一直不用（可以在校对表下面恢复）
            r["keep"] = False
            r["drop_reason"] = "老师删除"
        elif r.get("manual_keep") is not None:
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
    """素材准备。进度只报 0.00~0.95（之后的风格分析、查错字和 100% 由 workflows.run_prepare 报告）。"""
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
    had_records = bool(records)
    files = discover_sources(inputs)
    if not files and not records:
        raise FileNotFoundError("没有找到任何视频或音频文件。支持：" + " ".join(sorted(MEDIA_EXTS)))
    sr = int(pcfg.get("sample_rate", 44100))

    # 0) 只处理新文件（之前处理过的跳过；上次失败的会重试）
    new = [f for f in files if not sources_db.get(source_id(f), {}).get("done")]
    done_before = len(files) - len(new)
    head = f"找到 {len(files)} 个视频/录音"
    if done_before:
        head += f"，其中 {len(new)} 个是新的（另有 {done_before} 个文件之前已经处理过，这次跳过）"
    _progress(progress, 0.0, head)

    # 1) 提取 + 清理 + 切片：按文件大小分配进度
    total_bytes = sum(_file_size(f) for f in new) or 1
    cum = 0
    skipped_files: List[Dict[str, str]] = []
    n_new = len(new)
    for k, media in enumerate(new, 1):
        _check_cancel()
        size = _file_size(media)
        base = 0.02 + 0.38 * cum / total_bytes
        span = 0.38 * size / total_bytes
        cum += size
        sid = source_id(media)
        raw = project.raw_dir / f"{sid}.src.wav"
        clean = project.raw_dir / f"{sid}.wav"
        tag = f"[第 {k}/{n_new} 个文件]"
        try:
            _progress(progress, base, f"{tag} 从视频里提取声音：{media.name}（{_size_text(size)}）")
            extract_audio(media, raw, sample_rate=sr)
            _check_cancel()
            step2 = "去除背景音乐（这一步很慢，大约是视频时长的 1/3）" if pcfg.get("separate_vocals") else "降噪、统一音量"
            _progress(progress, base + 0.25 * span, f"{tag} {step2}")
            _, info = enhance_file(raw, clean, pcfg, work_dir=project.raw_dir)
            _check_cancel()
            _progress(progress, base + 0.75 * span, f"{tag} 切成小段……")
            new_recs = _slice_source(project, sid, media, clean, pcfg)
            log.info(f"  切出 {len(new_recs)} 段")
        except Exception as exc:
            if _is_disk_full(exc):  # 硬盘满了：后面的文件也一样会失败
                raise
            reason = _friendly_title(exc)
            # 原始报错（英文 Traceback）只写进黑色窗口和 voicetwin.log；sources.json 里也记一份，方便帮忙的人查
            log.warning(f"⚠️ 跳过第 {k} 个文件「{media.name}」：{reason}（其它视频继续处理）", exc_info=exc)
            sources_db[sid] = {"file": str(media), "failed": reason,  # 没有 done：修好文件后下次会重试
                               "error": repr(exc)[:500]}
            skipped_files.append({"file": media.name, "path": str(media), "reason": reason})
            project.write_json(project.sources_path, sources_db)
            continue
        finally:
            raw.unlink(missing_ok=True)
        for r in new_recs:
            records[r["id"]] = r
        wav_dur = sum(r["duration"] for r in new_recs)
        sources_db[sid] = {"file": str(media), "clean": project.relpath(clean), "segments": len(new_recs),
                           "speech_seconds": round(wav_dur, 1), "done": True,
                           **{k2: (round(v, 2) if isinstance(v, float) else v) for k2, v in info.items()}}
        project.write_json(project.sources_path, sources_db)
        project.save_manifest(records.values())
    if new and len(skipped_files) == len(new) and not records:
        detail = "；".join(f"{x['file']}（{x['reason']}）" for x in skipped_files[:3])
        raise RuntimeError(f"所有视频都没能处理：{detail}。请换成能正常播放的视频或录音再试。")

    # 2) 语音识别
    todo = [r for r in records.values() if not r.get("text") and not r.get("asr_done")]
    asr_cfg = dict(pcfg.get("asr", {}) or {})
    if todo and asr_cfg.get("engine", "faster-whisper") != "none":
        _progress(progress, 0.40, "加载识别模型（第一次使用会先自动下载，约 3 GB，可能要 10~30 分钟，之后就快了）"
                  + hf_mirror_hint())
        transcriber = Transcriber(asr_cfg)
        transcriber.progress = progress
        transcriber.progress_range = (0.40, 0.44)
        transcriber._load()
        _progress(progress, 0.44, f"开始识别每段话的文字（共 {len(todo)} 段）")
        last = 0.0
        for i, r in enumerate(todo):
            _check_cancel()
            wav16, _ = load_audio(project.abspath(r["path"]), sr=16000)
            res = transcriber.transcribe(wav16)
            r.update({"text": res.text, "lang": res.lang, "asr_done": True,
                      "asr": {"engine": res.engine, "avg_logprob": res.avg_logprob, "no_speech_prob": res.no_speech_prob}})
            is_last = i == len(todo) - 1
            if time.time() - last >= 1.0 or is_last:
                last = time.time()
                _progress(progress, 0.44 + 0.30 * (i + 1) / len(todo), f"识别 {i + 1}/{len(todo)}：{res.text[:20]}",
                          log_it=(i % 20 == 0 or is_last))
            if i % 20 == 19:
                project.save_manifest(records.values())
        project.save_manifest(records.values())
    elif todo:
        log.warning(f"{len(todo)} 个片段没有文字（识别引擎为 none 且没有字幕），它们不会参与训练")

    # 3) 片段统计
    need = [r for r in records.values() if "voiced" not in r or r.get("_stats_text") != r.get("text")]
    _progress(progress, 0.74, f"分析每段话的语速和停顿（共 {len(need)} 段）……")
    for k, r in enumerate(need):
        _check_cancel()
        _clip_stats(project, r)
        r["_stats_text"] = r.get("text")
        if k % 25 == 0 or k == len(need) - 1:
            _progress(progress, 0.74 + 0.06 * (k + 1) / len(need), f"分析语速和停顿 {k + 1}/{len(need)}", log_it=False)

    # 4) 过滤 / 划分 / 参考音频
    recs = sorted(records.values(), key=lambda r: r["id"])
    apply_filters(project, recs, pcfg, cfg, progress)
    assign_splits(recs, int(pcfg.get("validation_count", 20)))
    project.save_manifest(recs)
    _progress(progress, 0.90, "挑选最具代表性的参考音频……")
    refs = select_references(project, recs, pcfg)
    project.export_csv(recs)
    summary = summarize(project, recs, refs)
    summary["elapsed_min"] = round((time.time() - t0) / 60.0, 1)
    summary["files_total"] = len(files)
    summary["files_new"] = n_new - len(skipped_files)
    summary["skipped_files"] = skipped_files
    if had_records and not new:
        summary["warnings"].insert(0, "这次没有找到新的视频（文件夹里的都处理过了）")
    if skipped_files:
        summary["warnings"].insert(0, f"有 {len(skipped_files)} 个文件没能处理（见「跳过的文件」），其它的已经处理好了")
    project.write_json(project.root / "prepare_summary.json", summary)
    _progress(progress, 0.95, "素材整理完成")
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
        "references": [{"no": i, "id": r["id"], "lang": r["lang"], "kind": r["kind"], "text": r["text"]}
                       for i, r in enumerate(refs, 1)],
        "warnings": warnings,
        "transcripts_csv": str(project.csv_path),
    }
