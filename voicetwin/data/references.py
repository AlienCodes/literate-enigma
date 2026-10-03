"""挑选参考音频：合成时告诉模型"用这种语气说话"。

好的参考音频 = 你本人、干净、一句完整的话、语速和音高都接近你平时讲课的状态、3~10 秒。
中文、英文分别挑；如果素材里有疑问句/感叹句，也各挑一条，合成疑问句时用疑问语气的参考。
"""

from __future__ import annotations

import math
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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


#: 同时挑参考音频（例如两个保存同时做完）时一个一个来，不会互相删掉对方刚写的文件
_REFS_LOCK = threading.Lock()


def select_references(project: Project, records: List[Dict[str, Any]], pcfg: Dict[str, Any],
                      cleanup: bool = False) -> List[Dict[str, Any]]:
    """挑参考音频（每种语言几条、陈述 / 疑问 / 感叹都有），写进 references/ 和 references.json。

    不删正在用的文件：表格保存时重新挑，只加新的（同一句已经有了就不重写）；「生成」「挑选最佳模型」这时可能正用着
    以前挑的那几条（以前先把 references/ 里的全删掉，生成到一半找不到参考音频就失败了）。cleanup=True（准备素材时，
    这时不会有生成在跑）才把不再用的旧文件删掉。"""
    with _REFS_LOCK:
        return _select_references(project, records, pcfg, cleanup)


def _select_references(project: Project, records: List[Dict[str, Any]], pcfg: Dict[str, Any],
                       cleanup: bool) -> List[Dict[str, Any]]:
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
    for r in chosen:
        wav, sr = load_audio(project.abspath(r["path"]))
        trimmed, _, _ = trim_silence(wav, sr, pad_ms=80)
        dur = len(trimmed) / sr
        if not (min_d - 0.3 <= dur <= max_d + 0.3):
            # 太长就从句中停顿处截短不可靠，直接跳过；太短也跳过
            continue
        path = project.refs_dir / f"{r['id']}.wav"
        if not path.exists():  # 同一句的参考音频内容一样：已经有了就不重写（可能正被生成用着）
            from voicetwin.utils import atomic

            tmp = atomic.tmp_for(path).with_suffix(".wav")
            try:
                save_audio(tmp, trimmed, sr)
            except BaseException:
                try:
                    tmp.unlink()
                except OSError:
                    pass
                raise
            atomic.finish(tmp, path)
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
    if cleanup:  # 准备素材时：不再用的旧参考音频删掉（这时不会有生成在跑）
        keep = {Path(x["path"]).name for x in refs}
        for old in project.refs_dir.glob("*.wav"):
            if old.name not in keep:
                try:
                    old.unlink()
                except OSError:
                    pass
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


# ============================================================================ 「一模一样」档的参考录音库
#: 参考录音库（refs_bank.json，在声音文件夹里）：「一模一样」档每句话从里面挑几条最合适的当参考。
#: references.json 和别的档位都不动；库里的音频（references/bank/<id>.wav）第一次要用时才写。
BANK_FILE = "refs_bank.json"
BANK_EMB_FILE = "bank_emb.npz"          # 在 cache/ 里：库里每条录音的声纹（按片段 id + 文件大小 + 修改时间）
BANK_DIR = "bank"                        # references/bank/
BANK_VERSION = 1
BANK_RAW_SECONDS = (3.0, 11.0)           # 片段本身的长度
BANK_SECONDS = (3.2, 9.8)                # 去掉首尾静音（留 80 ms）以后：合成引擎要求参考音频 3~10 秒


def bank_eligible(r: Dict[str, Any]) -> bool:
    """能不能进参考录音库：用来训练的（没删除、训练集）、有保存好的文字、中文或英文、没有硬切开、3~11 秒、
    一句完整的话（问句都算）。"""
    text = str(r.get("text") or "").strip()
    if not text or not r.get("keep", True) or r.get("deleted") or r.get("split", "train") != "train":
        return False
    if r.get("lang") not in ("zh", "en") or int(r.get("forced_cuts") or 0) != 0:
        return False
    try:
        dur = float(r.get("duration") or 0.0)
    except (TypeError, ValueError):
        return False
    if not (BANK_RAW_SECONDS[0] <= dur <= BANK_RAW_SECONDS[1]):
        return False
    return sentence_kind(text) == "question" or ends_sentence(text)


def bank_dir(project: Project) -> Path:
    return project.refs_dir / BANK_DIR


def bank_path(project: Project) -> Path:
    return project.root / BANK_FILE


def bank_signature(entries: List[Dict[str, Any]]) -> str:
    """库的指纹：哪些片段、文字是什么（文字改了并保存，指纹就变）。"""
    import hashlib

    h = hashlib.sha1("\n".join(sorted(f"{e['id']}|{e.get('text', '')}" for e in entries)).encode("utf-8"))
    return h.hexdigest()[:16]


def eligible_signature(project: Project, records: List[Dict[str, Any]]) -> str:
    """能进库的片段的指纹：哪些片段、文字、录音文件（大小 + 修改时间）。和库里记的不一样，库就要重新整理
    （「准备「一模一样」」用它判断，不用读音频）。"""
    import hashlib

    from voicetwin.style.twin_profile import _file_key

    rows = sorted(f"{r['id']}|{str(r.get('text') or '').strip()}|{_file_key(project.abspath(r['path'])) or '-'}"
                  for r in records if bank_eligible(r) and r.get("id") and r.get("path"))
    return hashlib.sha1("\n".join(rows).encode("utf-8")).hexdigest()[:16]


def load_reference_bank(project: Project) -> Optional[Dict[str, Any]]:
    data = project.read_json(bank_path(project), None)
    if not isinstance(data, dict) or data.get("version") != BANK_VERSION:
        return None
    return data


def _load_bank_emb(project: Project, quiet: bool = False) -> Dict[str, np.ndarray]:
    """声纹缓存（只是为了快）：读不了就当没有，重新算。quiet：只是顺便看看（重算说话习惯时），读不了不提醒。"""
    path = project.cache_dir / BANK_EMB_FILE
    if not path.exists():
        return {}
    try:
        with np.load(path) as data:
            return {k: data[k] for k in data.files}
    except Exception as exc:  # noqa: BLE001 - 写到一半断电留下的半个文件等
        if quiet:
            log.debug(f"参考录音库的声纹缓存读不了（{exc}）")
        else:
            log.warning(f"参考录音库的声纹缓存读不了（{exc}），重新计算")
        return {}


def _emb_base(project: Project, entry: Dict[str, Any]) -> str:
    """声纹缓存里这一条的名字：片段 id + 文件大小 + 修改时间（片段文件变了就对不上，要重新算）。"""
    from voicetwin.style.twin_profile import _file_key

    return f"{entry['id']}|{_file_key(project.abspath(entry['path'])) or '-'}"


def _done_tag(models: List[str]) -> str:
    return "__done__" + ",".join(models)


def cached_bank_embeddings(project: Project, bank: Dict[str, Any]) -> Dict[str, Dict[str, np.ndarray]]:
    """refs_bank.json 里每条录音缓存好的声纹 {片段 id: {模型: 声纹}}（不用打分模型；片段文件变了的、没算过的不在里面）。
    重算说话习惯时用它重新算前后两句的音色变化。"""
    models = sorted(str(m) for m in bank.get("judge_models") or [])
    if not models:
        return {}
    cache = _load_bank_emb(project, quiet=True)
    if not cache:
        return {}
    out: Dict[str, Dict[str, np.ndarray]] = {}
    for e in bank.get("entries") or []:
        try:
            base = _emb_base(project, e)
        except (KeyError, TypeError, ValueError):
            continue
        if f"{base}|{_done_tag(models)}" not in cache:
            continue
        got = {m: cache[f"{base}|{m}"] for m in models if f"{base}|{m}" in cache}
        if got:
            out[str(e["id"])] = got
    return out


def _save_bank_emb(project: Project, cache: Dict[str, np.ndarray]) -> None:
    from voicetwin.utils import atomic

    project.cache_dir.mkdir(parents=True, exist_ok=True)
    path = project.cache_dir / BANK_EMB_FILE
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


def build_reference_bank(project: Project, records: List[Dict[str, Any]], judge: Any = None,
                         progress: Optional[Callable[[float, str], None]] = None) -> List[Dict[str, Any]]:
    """「一模一样」档的参考录音库：所有符合条件的训练片段，每条带上挑参考时要用的特征，存进 refs_bank.json。

    - 条件见 bank_eligible；去掉首尾静音（留 80 ms）以后还要是 3.2~9.8 秒；
    - 特征：音节数、英文比例、句型、语速、长度、来自哪个视频、在视频里的位置、前面停了多久、是不是一段话的开头
      （前面的停顿 ≥ 你句号处停顿的 p85）、里面最长的停顿、原来挑参考的分数（_score）、音高；
    - judge（精准声纹打分）有的话：每条算声纹（缓存在 cache/bank_emb.npz，按 id + 文件大小 + 修改时间）、
      自己和你的平均声纹有多像（self_pct），并填 twin_profile.json 里前后两句的音色变化；没有就不算（这几项是 null）；
    - 库里的音频不在这里写（第一次要用时 bank_wav 才写），references.json 不动。"""
    from voicetwin.style import twin_profile as tp
    from voicetwin.utils.textutil import syllable_count

    try:
        from voicetwin.utils.progress import check_cancel
    except ImportError:  # pragma: no cover
        def check_cancel() -> None:
            return None

    pool = sorted((r for r in records if bank_eligible(r)), key=lambda r: str(r["id"]))
    clips = tp.collect_clips(project, pool) if pool else {}
    prof = tp.load_twin_profile(project) or {}
    p85 = ((((prof.get("pauses") or {}).get("sentence") or {}).get("q")) or {}).get("p85")
    if p85 is None:  # 你句号处的停顿还没量出来：用原来说话风格里的段落停顿
        p85 = float(((project.load_profile().get("pauses") or {}).get("paragraph")) or 1.1)
    rates: Dict[str, List[float]] = {}
    for r in pool:
        if r.get("rate"):
            rates.setdefault(r["lang"], []).append(float(r["rate"]))
    med_rate = {lang: float(np.median(v)) for lang, v in rates.items()}

    entries: List[Dict[str, Any]] = []
    for r in pool:
        c = clips.get(str(r["id"]))
        if c is None:
            continue
        feat = c["feat"]
        trim = feat.get("trim")
        if not trim or len(trim) != 3 or not trim[2]:
            continue
        a, b, sr = int(trim[0]), int(trim[1]), int(trim[2])
        dur = (b - a) / sr
        if not (BANK_SECONDS[0] <= dur <= BANK_SECONDS[1]):
            continue
        text = str(r["text"]).strip()
        syl = syllable_count(text)
        voiced = float(feat.get("voiced") or 0.0)
        rate = r.get("rate") or (syl / voiced if syl and voiced >= 0.3 else None)
        gap_before = c.get("gap_before") if c.get("mode") == "raw" else r.get("gap_before")
        gaps = [float(e) - float(s) for s, e in feat.get("gaps") or []]
        entries.append({
            "id": str(r["id"]),
            "path": r["path"],
            "wav": project.relpath(bank_dir(project) / f"{r['id']}.wav"),
            "text": text,
            "lang": r["lang"],
            "kind": sentence_kind(text),
            "syllables": syl,
            "en_ratio": tp._r(tp.en_share(text), 4),
            "rate": tp._r(rate, 4),
            "dur": tp._r(dur, 3),
            "trim": [a, b, sr],
            "source": str(r.get("source") or ""),
            "start": tp._r(r.get("start"), 3),
            "gap_before": tp._r(gap_before, 3),
            "para_initial": bool(gap_before is None or float(gap_before) >= float(p85)),
            "max_pause": tp._r(max(gaps) if gaps else 0.0, 3),
            "base": tp._r(_score(r, med_rate.get(r["lang"], 4.5)), 4),
            "f0_med": feat.get("f0_med_hz"),
            "self_pct": None,
        })

    judge_sig, models = "", []
    embs_by_id: Dict[str, Dict[str, np.ndarray]] = {}
    if judge is not None and getattr(judge, "available", False) and entries:
        models = sorted(judge.models)
        try:
            judge_sig = str(judge.signature())
        except Exception:  # noqa: BLE001
            judge_sig = ""
        cache = _load_bank_emb(project)
        keep: Dict[str, np.ndarray] = {}
        done_tag = _done_tag(models)
        fresh = 0
        for k, e in enumerate(entries):
            check_cancel()
            base = _emb_base(project, e)
            if f"{base}|{done_tag}" in cache:
                got = {m: cache[f"{base}|{m}"] for m in models if f"{base}|{m}" in cache}
                secs = float(cache[f"{base}|{done_tag}"].reshape(-1)[0])
            else:
                try:
                    wav, sr = load_audio(project.abspath(e["path"]))
                    a, b, _ = e["trim"]
                    got, seconds = judge.embed_with_seconds(wav[a:b], sr)
                except Exception as exc:  # noqa: BLE001 - 个别片段算不了声纹：这一条没有声纹，别的照常
                    log.debug(f"参考录音 {e['id']} 算不了声纹：{exc}")
                    continue
                secs = float(seconds) if seconds is not None else -1.0
                fresh += 1
            for m, v in got.items():
                keep[f"{base}|{m}"] = np.asarray(v, dtype=np.float32)
            keep[f"{base}|{done_tag}"] = np.asarray([secs], dtype=np.float64)
            # 用存进缓存的那份（float32）：以后重算说话习惯时从缓存算的音色变化和这次一个数都不差
            embs_by_id[e["id"]] = {m: keep[f"{base}|{m}"] for m in got}
            try:
                res = judge.judge_embeddings(got, secs if secs >= 0 else None)
                e["self_pct"] = tp._r(res.get("pct_raw"), 2)
            except Exception:  # noqa: BLE001
                e["self_pct"] = None
            if progress is not None and (k % 10 == 0 or k == len(entries) - 1):
                progress((k + 1) / len(entries), f"给你的 {len(entries)} 条录音打分，挑参考录音……{k + 1}/{len(entries)}")
            if fresh and fresh % 50 == 0:  # 中途停下也不白算
                _save_bank_emb(project, {**cache, **keep})
        if fresh or set(keep) != set(cache):
            try:
                _save_bank_emb(project, keep)
            except OSError as exc:  # 缓存写不了：这次照样算完，下次再算一遍
                log.debug(f"参考录音库的声纹缓存写不了：{exc}")

    data = {"version": BANK_VERSION, "bank_sig": bank_signature(entries), "judge_sig": judge_sig,
            "judge_models": models, "n": len(entries), "seconds": list(BANK_SECONDS), "entries": entries,
            "eligible_sig": eligible_signature(project, records)}
    from voicetwin.utils import atomic

    atomic.write_text(bank_path(project), tp.dumps(data))
    if embs_by_id:
        try:
            tp.fill_timbre_deltas(project, project.load_manifest(), embs_by_id, judge_sig)
        except Exception as exc:  # noqa: BLE001 - 只是少一项统计
            log.debug(f"前后两句的音色变化没算出来：{exc}")
    return entries


def bank_wav(project: Project, entry: Dict[str, Any]) -> Path:
    """库里一条参考录音的音频（去掉首尾静音的片段）：第一次要用时才写（先写临时文件再换上去），以后直接用。"""
    from voicetwin.utils import atomic

    path = bank_dir(project) / f"{entry['id']}.wav"
    if path.exists():
        return path
    wav, sr = load_audio(project.abspath(entry["path"]))
    a, b, tsr = (int(x) for x in entry["trim"])
    if tsr != sr:  # 片段的采样率和量的时候不一样（不该发生）：按秒换算
        a, b = int(round(a * sr / tsr)), int(round(b * sr / tsr))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = atomic.tmp_for(path).with_suffix(".wav")
    try:
        save_audio(tmp, wav[a:b], sr)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    atomic.finish(tmp, path)
    return path


def prune_bank_files(project: Project, records: List[Dict[str, Any]]) -> int:
    """素材准备时（这时不会有生成在跑）：删掉库里已经不能用的音频（片段删了、不用来训练了等）。返回删了几个。"""
    folder = bank_dir(project)
    if not folder.is_dir():
        return 0
    ok = {str(r.get("id")) for r in records if bank_eligible(r)}
    removed = 0
    for f in folder.glob("*.wav"):
        if f.stem not in ok:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    return removed
