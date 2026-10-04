"""素材准备总流程：视频/录音 → 干净、带文字、只有你本人声音的训练片段。

支持增量：以后再加新的视频，重新运行只会处理新文件，之前手动校对过的内容不会丢。
"""

from __future__ import annotations

import errno
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

import numpy as np

from voicetwin.data.asr import Transcriber, hf_mirror_hint, looks_hallucinated
from voicetwin.data.enhance import enhance_file
from voicetwin.data.slicer import find_segments
from voicetwin.data.subtitles import Cue, find_sidecar_subtitle, group_cues, parse_subtitles, refine_boundaries
from voicetwin.project import Project
from voicetwin.style.prosody import rate_stats
from voicetwin.utils.audio import clip_ratio, clipped_fraction, estimate_snr, load_audio, save_audio
from voicetwin.utils.ffmpeg import extract_audio
from voicetwin.utils.log import get_logger, setup_logging
from voicetwin.utils.textutil import detect_lang, en_words, ends_sentence, safe_name, short_hash, syllable_count

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


def discover_sources(inputs: Iterable[str], exclude: Iterable[Any] = ()) -> List[Path]:
    """找出要处理的视频 / 录音。exclude：不要的文件夹（声音分身自己的工作区、GPT-SoVITS 文件夹）——老师填的文件夹
    正好包含它们时，不能把程序自己切好的片段、生成的音频当成新素材（检查时发现 20 条变成 68 条）。"""
    skip = []
    for d in exclude:
        try:
            if d:
                skip.append(Path(d).expanduser().resolve())
        except OSError:
            continue
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
    skipped = 0
    for f in files:
        rf = f.resolve()
        key = str(rf)
        if key in seen:
            continue
        seen.add(key)
        if any(rf == d or d in rf.parents for d in skip):
            skipped += 1
            continue
        unique.append(rf)
    if skipped:
        log.warning(f"跳过了 {skipped} 个声音分身 / GPT-SoVITS 自己的文件（切好的片段、生成的音频等），它们不是新素材")
    return unique


def content_key(path: Path) -> str:
    """按内容认文件（文件名 + 大小 + 开头和结尾各 1 MB 的指纹）：同一个视频换了盘符、换了文件夹也认得出来。
    比较时只看后两部分（content_fingerprint），改了名字也认得出来。"""
    import hashlib

    st = path.stat()
    h = hashlib.sha1()
    with open(path, "rb") as f:
        h.update(f.read(1 << 20))
        if st.st_size > (2 << 20):
            f.seek(-(1 << 20), 2)
            h.update(f.read(1 << 20))
    return f"{path.name.lower()}|{st.st_size}|{h.hexdigest()[:16]}"


def content_fingerprint(key: Any) -> str:
    """content_key 去掉文件名的部分（大小 + 开头结尾的指纹）：同一个视频改了名字（「第6课 定语从句.mp4」、
    浏览器重新下载的「0006 (1).mp4」、Windows 的「副本」）也认得出来。sources.json 里以前记下的 key 一样能比。"""
    parts = str(key or "").rsplit("|", 2)
    return f"{parts[1]}|{parts[2]}" if len(parts) == 3 and parts[1] and parts[2] else ""


def load_sources(project: Project, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """处理过哪些视频（sources.json）。坏了（写到一半断电）：留一份 .bad，按校对表里已经有的片段重建——
    不能当成都没处理过（不然所有视频再处理一遍，同一段话在训练里出现两次）。"""
    import json

    from voicetwin.utils import atomic

    p = project.sources_path
    try:
        data = json.loads(atomic.read_text(p))
    except FileNotFoundError:
        return {}
    except ValueError:
        data = None
    if isinstance(data, dict):
        return data
    atomic.keep_bad_copy(p)
    log.warning("sources.json 坏了：按校对表里已经有的片段重建（这些视频不再重复处理）")
    out: Dict[str, Any] = {}
    for r in records:
        sid = str(r.get("source") or "")
        if sid:
            out.setdefault(sid, {"done": True, "rebuilt": True, "file": ""})
    return out


def _segments(info: Dict[str, Any]) -> int:
    try:
        return int(info.get("segments") or 0)
    except (TypeError, ValueError):
        return 0


def sidecar_fingerprint(media: Path) -> str:
    """同名字幕的内容指纹（大小 + 开头结尾的指纹，不看名字）；没有同名字幕时是 "none"。记进 sources.json：一段也没切出来的视频，
    换了同名字幕（或者加上、删掉字幕）以后要重新处理。字幕一时打不开（被别的程序占着）时报 OSError。"""
    sub = find_sidecar_subtitle(media)
    return "none" if sub is None else (content_fingerprint(content_key(sub)) or "none")


def _done_entry(sources_db: Dict[str, Any], path: Path, with_rows: Optional[Set[str]] = None) -> Optional[Dict[str, Any]]:
    """already_done 的实现：处理过时返回 sources.json 里认出它的那条记录（校对表里有它的片段、sources.json 没记时是 {}），
    没处理过返回 None。"""
    sub_fp: List[str] = []

    def same_sidecar(info: Dict[str, Any]) -> bool:
        if not sub_fp:
            try:
                sub_fp.append(sidecar_fingerprint(path))
            except OSError:
                sub_fp.append("")
        return bool(sub_fp[0]) and info.get("sub") == sub_fp[0]

    def done(sid: str, info: Any) -> bool:
        if not isinstance(info, dict) or not info.get("done"):
            return False
        if with_rows is not None and sid in with_rows:
            return True
        if _segments(info) > 0:
            return with_rows is None
        # 一段也没切出来：同名字幕没变才算处理过（真的静音的文件再处理一遍也没用）。字幕换了（以前和视频对不上、
        # 是乱码）、加上或删掉了，或者是以前的版本记的（没记字幕指纹，例如 UTF-16 字幕一条都读不出的那些）→ 再处理一次
        return same_sidecar(info)

    sid0 = source_id(path)
    if with_rows is not None and sid0 in with_rows:
        return {}
    info0 = sources_db.get(sid0)
    if done(sid0, info0):
        return info0
    try:
        key = content_key(path)
        size = path.stat().st_size
    except OSError:
        key, size = "", -1
    fp = content_fingerprint(key)
    for sid, info in sources_db.items():
        if not done(sid, info):
            continue
        if fp and content_fingerprint(info.get("key")) == fp:
            return info
        old = str(info.get("file") or "")
        if info.get("key") or not old or Path(old).name.lower() != path.name.lower():
            continue
        # 旧版本的记录：编号里有「原来的位置 + 文件大小」的指纹 → 大小一样才算同一个视频（同名的另一个视频不会被跳过）
        if size < 0 or not str(sid).endswith("_" + short_hash(old, size, n=6)):
            continue
        try:
            moved = not Path(old).exists()
        except OSError:
            moved = True
        if moved:
            return info
    return None


def already_done(sources_db: Dict[str, Any], path: Path, with_rows: Optional[Set[str]] = None) -> bool:
    """这个视频处理过没有：同一个位置；或者内容一样（换了盘符 / 文件夹、改了名字）；或者旧版本记下的（没有内容指纹）
    同名、同样大小的文件，原来的位置已经找不到了（多半就是搬了地方）。

    with_rows：校对表里有片段的视频编号（不给就不看校对表）。校对表里已经有这个位置的视频的片段 → 处理过
    （写完校对表、还没记进 sources.json 就断电了：不能再切一遍，老师改过的字会被冲掉）；sources.json 记了「切出 N 段」、
    校对表里却一段都没有（以前的版本先记「处理过」、写校对表失败留下的）→ 不算处理过，再切一遍补上。
    记的是「一段也没切出来」：同名字幕没变才算处理过（换了字幕会重新处理，见 sidecar_fingerprint）。"""
    return _done_entry(sources_db, path, with_rows) is not None


#: 每个声音文件夹里程序自己生成的子文件夹（切好的片段、参考音频、生成的音频……）：里面的音频不是新素材。
#: 不包括 uploads（网页上传的视频就存在那里）
GENERATED_DIRS = ("raw", "clips", "references", "exports", "models", "outputs", "cache", "logs")


def pending_sources(project: Project, files: Iterable[Path], sources_db: Dict[str, Any],
                    records: Iterable[Dict[str, Any]], empty: Optional[List[Path]] = None) -> Tuple[List[Path], int]:
    """这次要处理的文件，返回 (要处理的文件, 重复的个数)。处理过的跳过（already_done）；同一个视频这次出现了好几份
    （网页上传了、旁边又填了它所在的文件夹；文件夹里有备份、「副本」、改了名字的）只处理一份——以前每一份都切一遍，
    同一句话训练两次，还可能一份当训练、一份当考试。留下的那份：有同名字幕的优先，再是文件夹里的原件（不是 uploads 里的），
    再不行就是先找到的那个。文件一时读不了（OSError）的照常算新的：处理时会说明原因、跳过、下次再试。
    empty：给了就把「以前处理过、一段也没切出来、这次也没变」而跳过的文件放进去（结果里再提醒一次怎么办）。"""
    with_rows = {str(r.get("source") or "") for r in records}
    with_rows.discard("")
    uploads = (Path(project.root) / "uploads").resolve()
    cand: List[Path] = []
    for f in files:
        try:
            hit = _done_entry(sources_db, f, with_rows)
        except OSError:
            hit = None
        if hit is not None:
            if empty is not None and hit.get("sub") and _segments(hit) <= 0:  # 按「字幕没变」认出来的 0 段记录
                empty.append(f)
            continue
        cand.append(f)
    groups: Dict[str, List[Path]] = {}
    for f in cand:
        try:
            fp = content_fingerprint(content_key(f))
        except OSError:
            fp = ""
        groups.setdefault(fp or f"path|{f}", []).append(f)

    def rank(f: Path) -> Tuple[int, int]:
        return (0 if find_sidecar_subtitle(f) is not None else 1, 1 if uploads in f.parents else 0)

    keep = {min(g, key=rank) for g in groups.values()}
    new = [f for f in cand if f in keep]
    return new, len(cand) - len(new)


def read_sidecar_cues(subtitle: Path) -> Optional[List[Cue]]:
    """读同名字幕。读不出能用的内容（不是字幕文件、坏了、解出来一大半是乱码）返回 None：改用按停顿切 + 语音识别
    （以前这样的视频一段都切不出来，还记成处理过）。文件一时打不开（被别的程序占着）照常报错：这个视频这次跳过、下次再试。"""
    cues = parse_subtitles(subtitle)
    text = "".join(c.text for c in cues)
    if not cues or text.count("\ufffd") > 0.1 * len(text):
        return None
    return cues


def usable_sidecar(media: Path) -> Optional[Path]:
    """能用的同名字幕（读得出内容）；没有、或者读不出内容时返回 None（要靠语音识别）。"""
    sub = find_sidecar_subtitle(media)
    if sub is None:
        return None
    try:
        return sub if read_sidecar_cues(sub) is not None else None
    except OSError:
        return sub


def _own_dirs(project: Project, cfg: Dict[str, Any]) -> List[Any]:
    """声音分身自己生成的文件夹（每个声音的 clips / raw / references / outputs …，不含上传的 uploads）、
    GPT-SoVITS 文件夹：里面的音频不是素材。"""
    dirs: List[Any] = []
    ws = Path(project.root).parent
    try:
        for vdir in ws.iterdir() if ws.exists() else []:
            if vdir.is_dir():
                dirs += [vdir / name for name in GENERATED_DIRS]
    except OSError:
        pass
    try:
        from voicetwin.eval.speaker import gsv_root_from_cfg

        dirs.append(gsv_root_from_cfg(cfg))
    except Exception:  # noqa: BLE001
        pass
    return dirs


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
def _slice_source(project: Project, sid: str, media: Path, clean_wav: Path, pcfg: Dict[str, Any],
                  clip_info: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """切成小段。clip_info：enhance_file 在原始录音上数的满格样本（每段记进 clip_src，「有爆音」按它查）。"""
    wav, sr = load_audio(clean_wav)
    mode = str(pcfg.get("segmentation", "auto")).lower()
    subtitle = find_sidecar_subtitle(media) if mode in ("auto", "srt") else None
    if mode == "srt" and subtitle is None:
        log.warning(f"  {media.name} 没有找到同名字幕，改用静音切分")
    min_d, max_d = float(pcfg.get("min_duration", 2.0)), float(pcfg.get("max_duration", 12.0))
    records: List[Dict[str, Any]] = []
    cues = read_sidecar_cues(subtitle) if subtitle is not None else None
    if subtitle is not None and cues is None:
        log.warning(f"  ⚠️ 字幕「{subtitle.name}」读不出内容（可能不是字幕文件，或者文件坏了），这个视频改用静音切分 + "
                    "语音识别（识别出来的文字请在校对表里看一看）")
    if subtitle is not None and cues is not None:
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
    counts, hop = (clip_info or {}).get("clip_counts"), int((clip_info or {}).get("clip_hop") or 0)
    out = []
    for k, rec in enumerate(records):
        cid = f"{sid}_{k:04d}"
        s, e = rec.pop("_s"), rec.pop("_e")
        clip = wav[s:e]
        if len(clip) < sr * 0.5:
            continue
        path = project.clips_dir / f"{cid}.wav"
        save_audio(path, clip, sr)
        if counts is not None and hop > 0:  # 原始录音（统一音量以前）这一段满格样本的比例
            rec["clip_src"] = round(clipped_fraction(counts, hop, s, e), 5)
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
    """声纹缓存（只是为了快）：读不了（写到一半断电、硬盘满了留下的半个文件）就当没有，重新算，不能让保存 / 确认一直失败。"""
    path = project.cache_dir / f"emb_{encoder_name}.npz"
    if not path.exists():
        return {}
    try:
        with np.load(path) as data:
            return {k: data[k] for k in data.files}
    except Exception as exc:  # noqa: BLE001 - BadZipFile / ValueError / OSError / EOFError 都一样处理
        log.warning(f"声纹缓存读不了（{exc}），重新计算")
        return {}


def _save_embedding_cache(project: Project, encoder_name: str, cache: Dict[str, np.ndarray]) -> None:
    """先写临时文件再换上去：硬盘满了 / 两个保存同时写，也不会留下半个文件。"""
    from voicetwin.utils import atomic

    project.cache_dir.mkdir(parents=True, exist_ok=True)
    path = project.cache_dir / f"emb_{encoder_name}.npz"
    tmp = atomic.tmp_for(path).with_suffix(".npz")
    try:
        np.savez(tmp, **cache)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    atomic.finish(tmp, path)


def _save_npy(path: Path, arr: np.ndarray) -> None:
    """先写临时文件再换上去（同上）。"""
    from voicetwin.utils import atomic

    tmp = atomic.tmp_for(path).with_suffix(".npy")
    try:
        np.save(tmp, arr)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    atomic.finish(tmp, path)


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
        # clip_src：原始录音（统一音量以前）里满格样本的比例。clip_ratio 是按统一过音量的片段算的，最响只有 -1 dB，
        # 永远查不出爆音（留着给以前准备的素材）
        clipped = max(float(r.get("clip_ratio") or 0), float(r.get("clip_src") or 0))
        if clipped > float(fcfg.get("max_clip_ratio", 0.002)):
            return "有爆音"
        # 老师改过、保存了的文字：识别引擎的把握（置信度、像不像语音）说的是原来识别出来的字，不再算数——不然改对了也一直
        # 不用来训练，表格里灰色、还不写原因。改回原来识别的字时照旧算。没有 orig_text 的是 v18 改的（那时还不记最初识别的
        # 文字，只有文字真的改了才记 text_edited）：也算改过
        human = bool(r.get("text_edited")) and ("orig_text" not in r or str(text) != str(r.get("orig_text") or ""))
        asr = {} if human else (r.get("asr") or {})
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
        rates = [r["rate"] for r in records if not r["drop_reason"] and not r.get("deleted") and r.get("lang") == lang
                 and r.get("rate")]
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
            # 老师删除的不算（比如删的是学生说话、别人的声音）：不然会把「你本人的声音」的平均值带偏
            active = [r for r in records if not r["drop_reason"] and not r.get("deleted")]
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
                _save_npy(project.root / f"speaker_centroid.{encoder.name}.npy", cen)

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
def _remember_sources_with_rows(project: Project, files: Iterable[Path], sources_db: Dict[str, Any],
                                records: Iterable[Dict[str, Any]]) -> None:
    """校对表里已经有片段、sources.json 却没记「处理过」的视频（写完校对表、还没记就断电了）：补记上（带内容指纹，
    以后搬了地方、改了名字也认得出来）。"""
    counts: Dict[str, int] = {}
    for r in records:
        sid = str(r.get("source") or "")
        if sid:
            counts[sid] = counts.get(sid, 0) + 1
    changed = False
    for f in files:
        try:
            sid = source_id(f)
            if sid not in counts or (sources_db.get(sid) or {}).get("done"):
                continue
            key = content_key(f)
        except OSError:
            continue
        sources_db[sid] = {"file": str(f), "key": key, "segments": counts[sid], "done": True, "rebuilt": True}
        changed = True
    if changed:
        project.write_json(project.sources_path, sources_db)


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
    records: Dict[str, Dict[str, Any]] = {r["id"]: r for r in project.load_manifest()}
    sources_db: Dict[str, Any] = load_sources(project, records.values())
    had_records = bool(records)
    files = discover_sources(inputs, exclude=_own_dirs(project, cfg))
    if not files and not records:
        raise FileNotFoundError("没有找到任何视频或音频文件。支持：" + " ".join(sorted(MEDIA_EXTS)))
    sr = int(pcfg.get("sample_rate", 44100))

    # 0) 只处理新文件（之前处理过的跳过；上次失败的会重试；同一个视频出现好几份只处理一份）
    _remember_sources_with_rows(project, files, sources_db, records.values())
    still_empty: List[Path] = []
    new, dup = pending_sources(project, files, sources_db, records.values(), empty=still_empty)
    done_before = len(files) - len(new) - dup
    head = f"找到 {len(files)} 个视频/录音"
    if done_before or dup:
        head += f"，其中 {len(new)} 个是新的"
    if done_before:
        head += f"（另有 {done_before} 个文件之前已经处理过，这次跳过）"
    if dup:
        head += f"；另有 {dup} 个和别的文件是同一个视频（上传的和文件夹里的是同一个，或者是备份、改了名字的），只处理一次"
    _progress(progress, 0.0, head)

    # 1) 提取 + 清理 + 切片：按文件大小分配进度
    total_bytes = sum(_file_size(f) for f in new) or 1
    cum = 0
    skipped_files: List[Dict[str, str]] = []
    empty_files: List[str] = []
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
        clip_info: Dict[str, Any] = {}
        ok = False
        try:
            _progress(progress, base, f"{tag} 从视频里提取声音：{media.name}（{_size_text(size)}）")
            extract_audio(media, raw, sample_rate=sr)
            _check_cancel()
            step2 = "去除背景音乐（这一步很慢，大约是视频时长的 1/3）" if pcfg.get("separate_vocals") else "降噪、统一音量"
            _progress(progress, base + 0.25 * span, f"{tag} {step2}")
            _, info = enhance_file(raw, clean, pcfg, work_dir=project.raw_dir, clip_info=clip_info)
            _check_cancel()
            _progress(progress, base + 0.75 * span, f"{tag} 切成小段……")
            new_recs = _slice_source(project, sid, media, clean, pcfg, clip_info=clip_info)
            log.info(f"  切出 {len(new_recs)} 段")
            ok = True
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
            # 提取出来的整段声音、去背景音乐留下的人声（都和整个视频一样长）用完就删；没做完（出错、点了停止）时
            # 清理好的那份也删掉（下次重新做）
            raw.unlink(missing_ok=True)
            (project.raw_dir / f"{sid}.src.vocals.wav").unlink(missing_ok=True)
            if not ok:
                clean.unlink(missing_ok=True)
            clip_info.clear()
        for r in new_recs:
            records[r["id"]] = r
        if not new_recs:
            empty_files.append(media.name)
        wav_dur = sum(r["duration"] for r in new_recs)
        try:
            ckey = content_key(media)
        except OSError:
            ckey = ""
        try:  # 同名字幕的指纹：一段也没切出来时，换了字幕会重新处理（字幕和视频对不上、是乱码的那些）
            sub_fp = sidecar_fingerprint(media)
        except OSError:
            sub_fp = ""
        sources_db[sid] = {"file": str(media), "key": ckey, "sub": sub_fp, "clean": project.relpath(clean),
                           "segments": len(new_recs), "speech_seconds": round(wav_dur, 1), "done": True,
                           **{k2: (round(v, 2) if isinstance(v, float) else v) for k2, v in info.items()}}
        # 先写校对表、再记「处理过」：写校对表失败（硬盘满了、被同步软件占着）时，下次会重新切这个视频
        # （以前先记了「处理过」，它的片段永远不在校对表里）
        project.save_manifest(records.values())
        project.write_json(project.sources_path, sources_db)
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
    refs = select_references(project, recs, pcfg, cleanup=True)  # 准备素材时不会有生成在跑：旧的参考音频可以删
    csv_locked = False
    try:
        project.export_csv(recs)
    except PermissionError:  # transcripts.csv 正被 Excel / WPS 打开：素材已经准备好了（manifest 保存了），只是表格没能更新
        csv_locked = True
    summary = summarize(project, recs, refs)
    if csv_locked:
        summary["warnings"].insert(0, "transcripts.csv 正被 Excel / WPS 打开，这次没能更新它（素材已经准备好了，网页上的校对表"
                                      "是最新的）。关掉 Excel 以后在网页上点一次「保存修改」就会更新")
    summary["elapsed_min"] = round((time.time() - t0) / 60.0, 1)
    summary["files_total"] = len(files)
    summary["files_new"] = n_new - len(skipped_files)
    summary["skipped_files"] = skipped_files
    if had_records and not new:
        summary["warnings"].insert(0, "这次没有找到新的视频（文件夹里的都处理过了）")
    if empty_files:
        names = "、".join(f"「{n}」" for n in empty_files[:5])
        if len(empty_files) > 5:
            names += f"等 {len(empty_files)} 个文件"
        summary["warnings"].insert(0, f"{names}里没有找到能用的说话声音，一段也没切出来（可能没录上声音、文件太短，"
                                      "或者同名字幕和视频对不上）。请打开听一下：没录上声音的，换成能听到你讲课声音的文件再准备一次；"
                                      "如果是同名字幕和视频对不上，把同名字幕换成对的（或者删掉）再点「开始准备素材」，"
                                      "会重新处理这个视频")
    if still_empty:
        names = "、".join(f"「{f.name}」" for f in still_empty[:5])
        if len(still_empty) > 5:
            names += f"等 {len(still_empty)} 个文件"
        summary["warnings"].insert(0, f"{names}以前处理过，一段也没切出来，这次文件和同名字幕都没变，没有再处理。"
                                      "如果是同名字幕和视频对不上，把同名字幕换成对的（或者删掉）再点「开始准备素材」，"
                                      "会重新处理；没录上声音的，换成能听到你讲课声音的文件")
    if dup:
        summary["warnings"].insert(0, f"有 {dup} 个文件和别的文件是同一个视频（上传的和文件夹里的是同一个，或者是备份、"
                                      "改了名字的），只处理了一次，同一段话不会训练两次")
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
    if reasons.get("有爆音"):
        warnings.append(f"有 {reasons['有爆音']} 段录音有爆音（录的时候声音太大、或者话筒离嘴太近，声音破了），没有用来训练。"
                        "以后录音把音量调小一点、话筒离远一点；你听着没问题的句子，可以在校对表里点「⋯ 选项」→「✅ 这一条也要用」")
    total_min = sum(by_lang.values()) / 60.0
    if total_min < 10:
        warnings.append(f"可用素材只有 {total_min:.1f} 分钟。能训练，但建议 ≥30 分钟，1~3 小时效果最好。")
    if 0 < by_lang.get("en", 0) / 60.0 < 5:
        warnings.append("英文素材不足 5 分钟：英文会带一点「中文腔」。如果要做英文课，建议加入英文讲课录音。")
    if not by_lang.get("en"):
        # 中文句子里夹着的英文（例如「首先，as这个关系代词……」）如实数出来，不能说「没有英文」
        mixed = [r for r in kept if r.get("lang") == "zh" and en_words(r.get("text") or "")]
        if mixed:
            n_words = sum(len(en_words(r.get("text") or "")) for r in mixed)
            warnings.append(f"素材里有 {len(mixed)} 句夹着英文（共 {n_words} 个英文单词），没有纯英文的句子。"
                            "模型仍能说英文，但整句英文的口音/语气不一定像你；有英文课录音的话请一起加入。")
        else:
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
