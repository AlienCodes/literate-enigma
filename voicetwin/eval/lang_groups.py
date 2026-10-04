"""四项评分：中英夹在一起 / 纯中文 / 纯英文 / 综合总评分（老师 10-04 的要求：「一定要做到绝对的精准」）。

挑模型（synth/select.py 的 select_deep）用它；以后生成一篇讲稿的报告也用同样的四项（同一套算法，只是综合总评分的
比例按这篇讲稿里各类句子的时长）。算法（research/一模一样/记录.md「四项评分的算法」）：

1. 句子按文字自动分组（text_group）：有汉字也有英文单词 = 中英夹在一起；只有汉字 = 纯中文；只有英文 = 纯英文；
   标点、数字不算。
2. 每一句的「像你本人 %」照旧用声纹模型打分（只看人声、AS-norm、两头校准、短句子按自己的短句标准），
   **再按组单独校准**（build_group_calibration）：「100%」= 你自己同一类句子的真实录音的中位水平。声纹模型都是用中文
   训练的，同一个人说英文、夹英文的句子分数本来就低一些；不分组校准，这两类句子会被冤枉地打低。
   校准用你全部能用的真实录音（不只是没参加训练的那 20 句；拿来算「平均声纹」的那些片段不用——它们本来就是尺子的一部分，
   自己给自己打分会偏高）。某一组不到 8 句时用总体的标准，并写明「这一组你的录音太少，按总体标准算」。
   换算：你自己这一组的每段录音先按给生成的句子打分时**完全一样**的算法打分（每个声纹模型没封顶的「像你本人」，
   短的录音也按同样长度的短句标准——不然一组录音只是比较短，也会被当成「这类句子天生分数低」放大），这一组的中位数
   就是这一组的「100%」：每个模型的系数 = 100 / 这一组的中位数；生成的句子每个模型的分数 × 系数，再几个模型取平均
   （和原来一样），最后限制在 0~100（和原来显示的「像你本人 %」一样）。
3. 每组分数 = 这一组每句「像你本人 %」按人声时长加权的平均（长句子信息多、更可靠），同时给出 95% 误差范围
   （对句子重新抽样 2000 次）和句数。一组不到 8 句时只写平均、不写误差范围（句子太少，重新抽样量出来的范围太窄、不可信），
   比两个模型时这一组也不算「明显更好 / 更差」（只算进综合总评分）。
4. 综合总评分 = 各组分数按你讲课里各组真实所占的时间比例加权（挑模型时按你全部素材实测的比例；没有的组不算、比例重新分配）；
   误差范围一起算（每次重新抽样时各组一起抽）。
5. 和读错检查分开：这四项都只是「像不像」，读没读错单独显示。
6. 显示：「中英夹在一起 X% ± a（n 句）｜纯中文 Y% ± b（m 句）｜纯英文 —（没有这类句子）｜综合总评分 Z% ± c」，
   量不出来写「（没测出来）」；有英文时提示「声纹模型判断英文没有中文准，请再用耳朵听」。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import count_cjk, en_words, short_hash

log = get_logger("lang_groups")

#: 三组（显示的顺序：中英夹在一起最重要，放第一个）
GROUP_ORDER: Tuple[str, ...] = ("mixed", "zh", "en")
GROUP_LABELS = {"mixed": "中英夹在一起", "zh": "纯中文", "en": "纯英文"}
COMPOSITE_LABEL = "综合总评分"
EN_NOTE = "声纹模型判断英文没有中文准，请再用耳朵听"
NOT_MEASURED = "（没测出来）"
NO_ITEMS = "—（没有这类句子）"
#: 某一组你的真实录音少于这么多句时，这一组用总体的标准（不单独校准）
MIN_GROUP_CLIPS = 8
#: 误差范围：对句子重新抽样多少次、用哪个种子（固定的种子：同样的数据每次算出来一样）
N_BOOT = 2000
BOOT_SEED = 1234
#: 一组（或者两个模型比的时候共同的句子）少于这么多句时不写误差范围、不算「明显」：句子太少时重新抽样量出来的范围太窄
#: （实测：两个模型其实一样好时，1 句 100%、5 句 18%、8 句 10.5% 会被说成「明显不一样」，
#: research/一模一样/scripts/p8_boot_small_n.py），和按组校准的最少句数一样
MIN_INTERVAL_N = 8
CALIB_FILE = "lang_calib.json"          # 在 cache/ 里：按组校准的结果
CALIB_EMB_FILE = "lang_calib_emb.npz"   # 在 cache/ 里：参考录音库里没有的那些录音的声纹（按片段 id + 文件大小 + 修改时间）
#: 2 = 你自己的录音按给生成的句子打分时一样的算法（同样的短句标准）校准；声纹缓存里另记人声秒数
CALIB_VERSION = 2
#: 声纹缓存里这段录音的人声秒数（声纹模型做人声检测以后的长度，−1 = 量不出来）
SECONDS_KEY = "__seconds__"


# ============================================================================ 1. 分组
def text_group(text: Any) -> str:
    """句子属于哪一组：mixed（有汉字也有英文单词）/ zh（只有汉字）/ en（只有英文单词）/ ""（都没有，例如只有数字）。
    标点、数字不算。"""
    t = str(text or "")
    cjk = count_cjk(t) > 0
    en = len(en_words(t)) > 0
    if cjk and en:
        return "mixed"
    if cjk:
        return "zh"
    if en:
        return "en"
    return ""


def _kept(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in records if r.get("keep", True) and not r.get("deleted") and str(r.get("text") or "").strip()]


def material_shares(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """你的素材里各组实际说话的时间（秒）和比例：每段用素材准备时量的人声时长（voiced），没量的用片段长度。
    返回 {"seconds", "n", "shares", "source", "total_s", "n_lines"}；一段都没有时 shares 是空的。"""
    seconds = {g: 0.0 for g in GROUP_ORDER}
    n = {g: 0 for g in GROUP_ORDER}
    used_voiced = used_dur = 0
    for r in _kept(records):
        g = text_group(r.get("text"))
        if not g:
            continue
        val = _num(r.get("voiced"))
        if val is not None and val > 0:
            used_voiced += 1
        else:
            val = _num(r.get("duration"))
            if val is None or val <= 0:
                continue
            used_dur += 1
        seconds[g] += float(val)
        n[g] += 1
    total = sum(seconds.values())
    shares = {g: seconds[g] / total for g in GROUP_ORDER} if total > 0 else {}
    source = "voiced" if used_dur == 0 else ("duration" if used_voiced == 0 else "voiced+duration")
    return {"seconds": {g: round(v, 2) for g, v in seconds.items()}, "n": n,
            "shares": {g: round(v, 6) for g, v in shares.items()}, "source": source,
            "total_s": round(total, 2), "n_lines": sum(n.values())}


def composite_weights(shares: Optional[Dict[str, float]], present: Iterable[str],
                      fallback: Optional[Dict[str, float]] = None) -> Tuple[Dict[str, float], str]:
    """综合总评分里各组的比例：只算这次量到了的组（present），按 shares 重新分配到加起来是 1。
    shares 里这些组都是 0（或者没有 shares）时用 fallback（例如这次检查的句子里各组的时长）。返回 (比例, 用的是哪种)。"""
    present = [g for g in GROUP_ORDER if g in set(present)]
    if not present:
        return {}, "none"
    for src, table in (("material", shares), ("items", fallback)):
        if not table:
            continue
        vals = {g: max(0.0, float(table.get(g) or 0.0)) for g in present}
        tot = sum(vals.values())
        if tot > 0:
            return {g: v / tot for g, v in vals.items() if v > 0}, src
    return {g: 1.0 / len(present) for g in present}, "equal"


# ============================================================================ 2. 每个声纹模型的分数、按组校准
def member_raws(judge: Any, embs: Dict[str, np.ndarray], seconds: Optional[float]) -> Dict[str, float]:
    """每个声纹模型各自没封顶的「像你本人」（和 SimilarityJudge.judge_embeddings 里取平均之前的一样）。"""
    out: Dict[str, float] = {}
    for m in list(getattr(judge, "members", []) or []):
        emb = (embs or {}).get(m.name)
        if emb is None:
            continue
        try:
            raw = m.pct_raw(emb, seconds)
        except Exception:  # noqa: BLE001 - 这一个模型打不了分：不算它
            raw = None
        if raw is not None and math.isfinite(float(raw)):
            out[m.name] = float(raw)
    return out


def _num(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _ruler(m: Any) -> Optional[Tuple[str, float, float]]:
    """这个声纹模型的尺子：(打分方式, 0% 的分数, 100% 的分数)。两头校准：AS-norm 后的分数、i0、g50；
    只有余弦校准：余弦相似度、0、p50。没校准时 None。"""
    calib = getattr(m, "calib", {}) or {}
    if getattr(m, "two_sided", False):
        return "asnorm", float(calib["i0"]), float(calib["g50"])
    p50 = _num(calib.get("p50"))
    if p50 is not None and p50 > 0:
        return "cosine", 0.0, p50
    return None


def _centroid_ids(project: Any, members: Sequence[Any]) -> List[str]:
    """拿来算「平均声纹」的那些片段（speaker_centroid.<模型>.judge.json 里记的）：它们自己给自己打分会偏高，按组校准时不用。"""
    ids: set = set()
    for m in members:
        path = Path(project.root) / f"speaker_centroid.{m.name}.judge.json"
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
            ids.update(str(x) for x in meta.get("ids") or [])
        except (OSError, ValueError, AttributeError):
            continue
    return sorted(ids)


def _file_key(project: Any, rec: Dict[str, Any]) -> str:
    from voicetwin.style.twin_profile import _file_key as fk

    return str(fk(project.abspath(rec["path"])) or "-")


def _secs(value: Any) -> Optional[float]:
    """缓存里记的人声秒数（−1 = 量不出来 → None）。"""
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    v = _num(arr[0]) if arr.size else None
    return v if v is not None and v >= 0 else None


def _clip_embeddings(project: Any, judge: Any, recs: Sequence[Dict[str, Any]],
                     progress: Optional[Callable[[float, str], None]] = None
                     ) -> Dict[str, Tuple[Dict[str, np.ndarray], Optional[float]]]:
    """每段录音每个声纹模型的声纹 + 人声几秒（声纹模型做人声检测以后的长度，和给生成的句子打分时用的一样：
    短句子的「100%」标准按它定；量不出来是 None）。参考录音库已经算过的直接用（cache/bank_emb.npz，人声秒数也记在里面），
    别的算一次存在 cache/lang_calib_emb.npz（按片段 id + 文件大小 + 修改时间，文件变了就重新算）。"""
    from voicetwin.data.references import _done_tag, _load_bank_emb
    from voicetwin.utils.audio import load_audio

    try:
        from voicetwin.utils.progress import check_cancel
    except ImportError:  # pragma: no cover
        def check_cancel() -> None:
            return None

    models = sorted(str(m) for m in getattr(judge, "models", []) or [])
    if not models:
        return {}
    tag = _done_tag(models)
    bank_cache = _load_bank_emb(project, quiet=True)
    path = Path(project.cache_dir) / CALIB_EMB_FILE
    own: Dict[str, np.ndarray] = {}
    if path.exists():
        try:
            with np.load(path) as data:
                own = {k: data[k] for k in data.files}
        except Exception as exc:  # noqa: BLE001 - 缓存坏了：重新算
            log.debug(f"按组校准的声纹缓存读不了（{exc}），重新计算")
            own = {}
    keep: Dict[str, np.ndarray] = {}
    out: Dict[str, Tuple[Dict[str, np.ndarray], Optional[float]]] = {}
    fresh = 0
    todo = []
    for r in recs:
        base = f"{r['id']}|{_file_key(project, r)}"
        got: Dict[str, np.ndarray] = {}
        secs: Optional[float] = None
        if f"{base}|{tag}" in bank_cache:  # 参考录音库：完成标记里记的就是人声秒数
            got = {m: bank_cache[f"{base}|{m}"] for m in models if f"{base}|{m}" in bank_cache}
            secs = _secs(bank_cache[f"{base}|{tag}"])
        # 自己的缓存：以前的版本存的没有人声秒数，不用（重新算）
        if not got and f"{base}|{tag}" in own and f"{base}|{SECONDS_KEY}" in own:
            got = {m: own[f"{base}|{m}"] for m in models if f"{base}|{m}" in own}
            secs = _secs(own[f"{base}|{SECONDS_KEY}"])
            if got:
                keep.update({f"{base}|{m}": v for m, v in got.items()})
                keep[f"{base}|{tag}"] = own[f"{base}|{tag}"]
                keep[f"{base}|{SECONDS_KEY}"] = own[f"{base}|{SECONDS_KEY}"]
        if got:
            out[str(r["id"])] = (got, secs)
        else:
            todo.append((r, base))
    for k, (r, base) in enumerate(todo):
        check_cancel()
        try:
            wav, sr = load_audio(project.abspath(r["path"]))
            if hasattr(judge, "embed_with_seconds"):
                got, secs = judge.embed_with_seconds(wav, sr)
            else:  # 别的打分器（没有人声检测）：用素材准备时量的人声时长
                got, secs = judge.embed(wav, sr), _num(r.get("voiced"))
        except Exception as exc:  # noqa: BLE001 - 个别录音读不了：这一段不算
            log.debug(f"按组校准时跳过 {r.get('id')}：{exc}")
            continue
        if not got:
            continue
        secs = float(secs) if secs is not None and math.isfinite(float(secs)) and float(secs) >= 0 else None
        out[str(r["id"])] = ({m: np.asarray(v, dtype=np.float32) for m, v in got.items()}, secs)
        keep.update({f"{base}|{m}": np.asarray(v, dtype=np.float32) for m, v in got.items()})
        keep[f"{base}|{tag}"] = np.asarray([1.0])
        keep[f"{base}|{SECONDS_KEY}"] = np.asarray([secs if secs is not None else -1.0], dtype=np.float64)
        fresh += 1
        if progress is not None and (k % 10 == 0 or k == len(todo) - 1):
            try:
                progress((k + 1) / len(todo), f"按句子种类校准打分：给你的录音打分……{k + 1}/{len(todo)}")
            except Exception:  # noqa: BLE001 - 进度条出问题不影响校准（停止按钮是 BaseException，照常传出去）
                pass
    if fresh or set(keep) != set(own):
        try:
            from voicetwin.utils import atomic

            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = atomic.tmp_for(path).with_suffix(".npz")
            np.savez(tmp, **keep)
            atomic.finish(tmp, path)
        except Exception as exc:  # noqa: BLE001 - 缓存写不了：这次照样算完
            log.debug(f"按组校准的声纹缓存写不了：{exc}")
    return out


def build_group_calibration(project: Any, judge: Any, records: Optional[Sequence[Dict[str, Any]]] = None,
                            progress: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
    """按组校准（见本文件开头第 2 条）。返回并缓存（cache/lang_calib.json，素材、打分标准都没变时直接用）：
    {"ok", "groups": {组: {"n", "calibrated", "factors": {模型: 系数}, "median_pct": {模型: 这一组你的录音按总体标准、
    和给生成的句子打分一样的算法（同样的短句标准）是多少 %}, "note"}}, "excluded_centroid", "n_clips", "sig"}。
    没有能用的声纹模型时 ok = False（四项都量不出来）。"""
    members = list(getattr(judge, "members", []) or []) if judge is not None else []
    rulers = {m.name: _ruler(m) for m in members}
    if not members or not any(rulers.values()):
        return {"ok": False, "why": "没有校准好的声纹模型", "groups": {}}
    recs = list(records) if records is not None else project.load_manifest(only_kept=True)
    usable = [r for r in _kept(recs) if r.get("path") and r.get("id") and text_group(r.get("text"))]
    centroid = set(_centroid_ids(project, members))
    usable = sorted((r for r in usable if str(r["id"]) not in centroid), key=lambda r: str(r["id"]))
    try:
        jsig = str(judge.signature())
    except Exception:  # noqa: BLE001
        jsig = ""
    sig = short_hash(CALIB_VERSION, jsig, [(str(r["id"]), str(r.get("text") or ""), _file_key(project, r)) for r in usable],
                     sorted(centroid), MIN_GROUP_CLIPS, sorted((k, v) for k, v in rulers.items() if v), n=16)
    path = Path(project.cache_dir) / CALIB_FILE
    try:
        old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, ValueError):
        old = None
    if isinstance(old, dict) and old.get("sig") == sig and old.get("version") == CALIB_VERSION:
        return old
    embs = _clip_embeddings(project, judge, usable, progress)
    scores: Dict[str, Dict[str, List[float]]] = {g: {} for g in GROUP_ORDER}
    counts = {g: 0 for g in GROUP_ORDER}
    for r in usable:
        got, secs = embs.get(str(r["id"])) or ({}, None)
        if not got:
            continue
        g = text_group(r.get("text"))
        counts[g] += 1
        for m in members:
            if rulers.get(m.name) is None or m.name not in got:
                continue
            try:  # 和给生成的句子打分一样：没封顶的「像你本人」，短的录音按同样长度的短句标准
                raw = m.pct_raw(got[m.name], secs)
            except Exception as exc:  # noqa: BLE001
                log.debug(f"按组校准时 {m.name} 打不了分：{exc}")
                continue
            if raw is not None and math.isfinite(float(raw)):
                scores[g].setdefault(m.name, []).append(float(raw))
    groups: Dict[str, Any] = {}
    for g in GROUP_ORDER:
        n = counts[g]
        entry: Dict[str, Any] = {"label": GROUP_LABELS[g], "n": n, "calibrated": False, "factors": {},
                                 "median_pct": {}, "note": ""}
        if n == 0:
            entry["note"] = "你的素材里没有这类句子"
        elif n < MIN_GROUP_CLIPS:
            entry["note"] = f"「{GROUP_LABELS[g]}」这一组你的录音太少（只有 {n} 句，至少要 {MIN_GROUP_CLIPS} 句），按总体标准算"
        else:
            factors, med_pct, bad = {}, {}, []
            for m in members:
                vals = scores[g].get(m.name) or []
                if rulers.get(m.name) is None or len(vals) < MIN_GROUP_CLIPS:
                    continue
                med = float(np.median(vals))
                med_pct[m.name] = round(med, 2)
                if med <= 5.0:  # 这一组你自己的录音几乎不像你（量得不对）：不按它校准
                    bad.append(m.name)
                    continue
                factors[m.name] = round(100.0 / med, 6)
            entry["median_pct"] = med_pct
            if factors and not bad:
                entry.update(calibrated=True, factors=factors)
            else:
                entry["note"] = f"「{GROUP_LABELS[g]}」这一组没能单独校准（你自己的录音分数量得不对），按总体标准算"
        groups[g] = entry
    out = {"version": CALIB_VERSION, "ok": True, "sig": sig, "groups": groups, "n_clips": len(usable),
           "excluded_centroid": len(centroid), "min_clips": MIN_GROUP_CLIPS}
    try:
        from voicetwin.utils import atomic

        path.parent.mkdir(parents=True, exist_ok=True)
        atomic.write_text(path, json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    except Exception as exc:  # noqa: BLE001 - 写不了缓存：下次再算
        log.debug(f"按组校准的结果写不了：{exc}")
    return out


def calibrated_raw(raws: Dict[str, float], group: str, calib: Optional[Dict[str, Any]]) -> Optional[float]:
    """按组校准以后、没封顶的「像你本人」：每个模型的分数 × 这一组的系数，再取平均。没有分数时 None；
    这一组没单独校准（录音太少等）时系数是 1（= 总体标准）。"""
    if not raws:
        return None
    entry = ((calib or {}).get("groups") or {}).get(group) or {}
    factors = entry.get("factors") if entry.get("calibrated") else {}
    vals = [float(v) * float((factors or {}).get(name, 1.0)) for name, v in raws.items()]
    return float(np.mean(vals)) if vals else None


def calibrated_pct(raws: Dict[str, float], group: str, calib: Optional[Dict[str, Any]]) -> Optional[float]:
    """按组校准以后的「像你本人 %」（0~100，和原来显示的一样）。"""
    raw = calibrated_raw(raws, group, calib)
    return None if raw is None else float(min(100.0, max(0.0, raw)))


def calibration_notes(calib: Optional[Dict[str, Any]], groups: Iterable[str]) -> List[str]:
    """这几组里没单独校准的说明（「这一组你的录音太少，按总体标准算」）。"""
    out = []
    for g in GROUP_ORDER:
        if g not in set(groups):
            continue
        entry = ((calib or {}).get("groups") or {}).get(g) or {}
        if entry and not entry.get("calibrated") and entry.get("note") and entry.get("n"):
            out.append(str(entry["note"]))
        elif entry and not entry.get("n"):
            out.append(f"「{GROUP_LABELS[g]}」这一组你的素材里没有，按总体标准算")
    return out


# ============================================================================ 3、4. 每组分数、综合总评分、误差范围
def _boot_idx(rng: np.random.Generator, m: int, n_boot: int) -> np.ndarray:
    return rng.integers(0, m, size=(int(n_boot), m))


def _weighted(x: np.ndarray, w: np.ndarray, idx: Optional[np.ndarray] = None) -> Any:
    if idx is None:
        return float((w * x).sum() / w.sum())
    ww = w[idx]
    return (ww * x[idx]).sum(axis=1) / ww.sum(axis=1)


def _clean(items: Iterable[Dict[str, Any]], group: str) -> Tuple[List[str], np.ndarray, np.ndarray]:
    keys, xs, ws = [], [], []
    for it in items:
        if it.get("group") != group or it.get("pct") is None:
            continue
        keys.append(str(it.get("key")))
        xs.append(float(it["pct"]))
        ws.append(max(1e-6, float(it.get("w") or 1.0)))
    return keys, np.asarray(xs, dtype=np.float64), np.asarray(ws, dtype=np.float64)


def group_scores(items: Sequence[Dict[str, Any]], shares: Optional[Dict[str, float]] = None,
                 n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> Dict[str, Any]:
    """四项评分。items：每句 {"key", "group", "pct"（按组校准的「像你本人 %」，生成失败算 0，量不出来是 None）, "w"（人声秒数）}。
    shares：综合总评分里各组的比例（你素材里各组实际说话时间的比例；没有时按这些句子的时长）。
    返回 {"groups": {组: {"label", "n", "n_measured", "status": ok/unmeasured/none, "mean", "lo", "hi", "pm", "few"}},
    "composite": {"mean", "lo", "hi", "pm", "weights", "weights_source", "status"}, "n_boot", "seed"}。
    误差范围 = 对句子重新抽样 n_boot 次的 2.5% ~ 97.5%；pm 是均值到两头里远的那一边（保守）。
    一组量到的不到 MIN_INTERVAL_N 句：few = True，只有平均，lo / hi / pm 是 None（句子太少，量不出可信的误差范围）；
    这一组照样算进综合总评分。"""
    rng = np.random.default_rng(int(seed))
    groups: Dict[str, Any] = {}
    boots: Dict[str, np.ndarray] = {}
    means: Dict[str, float] = {}
    item_w: Dict[str, float] = {}
    for g in GROUP_ORDER:
        n = sum(1 for it in items if it.get("group") == g)
        _, x, w = _clean(items, g)
        entry: Dict[str, Any] = {"label": GROUP_LABELS[g], "n": n, "n_measured": int(x.size)}
        if n == 0:
            entry["status"] = "none"
        elif x.size == 0:
            entry["status"] = "unmeasured"
        else:
            mean = _weighted(x, w)
            bm = _weighted(x, w, _boot_idx(rng, x.size, n_boot))
            entry.update(status="ok", mean=round(mean, 2), few=bool(x.size < MIN_INTERVAL_N))
            if x.size >= MIN_INTERVAL_N:
                lo, hi = (float(v) for v in np.percentile(bm, [2.5, 97.5]))
                entry.update(lo=round(lo, 2), hi=round(hi, 2), pm=round(max(mean - lo, hi - mean), 2))
            else:
                entry.update(lo=None, hi=None, pm=None)
            boots[g], means[g], item_w[g] = bm, mean, float(w.sum())
        groups[g] = entry
    weights, src = composite_weights(shares, boots.keys(), fallback=item_w)
    comp: Dict[str, Any] = {"label": COMPOSITE_LABEL, "weights": {g: round(v, 6) for g, v in weights.items()},
                            "weights_source": src}
    if weights:
        mean = float(sum(weights[g] * means[g] for g in weights))
        bm = sum(weights[g] * boots[g] for g in weights)
        lo, hi = (float(v) for v in np.percentile(bm, [2.5, 97.5]))
        comp.update(status="ok", mean=round(mean, 2), lo=round(lo, 2), hi=round(hi, 2),
                    pm=round(max(mean - lo, hi - mean), 2))
    else:
        comp["status"] = "unmeasured" if items else "none"
    return {"groups": groups, "composite": comp, "n_boot": int(n_boot), "seed": int(seed)}


def paired_compare(items_a: Sequence[Dict[str, Any]], items_b: Sequence[Dict[str, Any]],
                   weights: Dict[str, float], n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> Dict[str, Any]:
    """两个模型在同样的句子上比（成对：每次重新抽样时两个模型抽到的是同样的句子）。
    返回每组和综合总评分的「A − B」：{"diff", "lo", "hi", "n", "few", "clear": "a"（A 明显更像）/ "b" / None（分不出来）}，
    以及 p_a = 重新抽样里 A 的综合总评分更高的比例。一组共同的句子不到 MIN_INTERVAL_N 句（few）时这一组的 clear 总是
    None：句子太少，分不出谁明显更好（只算进综合总评分）。"""
    rng = np.random.default_rng(int(seed))
    out: Dict[str, Any] = {"groups": {}}
    comp_a, comp_b = None, None
    for g in GROUP_ORDER:
        ka, xa, wa = _clean(items_a, g)
        kb, xb, wb = _clean(items_b, g)
        common = [k for k in ka if k in set(kb)]
        if not common:
            continue
        ia = {k: i for i, k in enumerate(ka)}
        ib = {k: i for i, k in enumerate(kb)}
        a = np.asarray([xa[ia[k]] for k in common])
        b = np.asarray([xb[ib[k]] for k in common])
        w = np.asarray([wa[ia[k]] for k in common])  # 权重（人声秒数）两个模型一样：按句子定的
        idx = _boot_idx(rng, len(common), n_boot)
        ba, bb = _weighted(a, w, idx), _weighted(b, w, idx)
        d = ba - bb
        lo, hi = (float(v) for v in np.percentile(d, [2.5, 97.5]))
        diff = _weighted(a, w) - _weighted(b, w)
        few = len(common) < MIN_INTERVAL_N
        out["groups"][g] = {"diff": round(diff, 3), "lo": round(lo, 3), "hi": round(hi, 3), "n": len(common),
                            "few": few, "clear": None if few else ("a" if lo > 0 else ("b" if hi < 0 else None))}
        if g in weights:
            comp_a = (0 if comp_a is None else comp_a) + weights[g] * ba
            comp_b = (0 if comp_b is None else comp_b) + weights[g] * bb
    if comp_a is not None and comp_b is not None:
        d = np.asarray(comp_a) - np.asarray(comp_b)
        lo, hi = (float(v) for v in np.percentile(d, [2.5, 97.5]))
        out["composite"] = {"diff": round(float(np.mean(d)), 3), "lo": round(lo, 3), "hi": round(hi, 3),
                            "clear": "a" if lo > 0 else ("b" if hi < 0 else None)}
        out["p_a"] = round(float(np.mean(d > 0)), 4)
    return out


# ============================================================================ 6. 显示
def _fmt(label: str, entry: Dict[str, Any], count: bool = True) -> str:
    """一项：「中英夹在一起 97.1% ± 2.3（28 句）」/「纯英文 95.0%（只有 1 句，太少，量不出误差范围）」/
    「纯英文 —（没有这类句子）」/「纯中文（没测出来）」。"""
    if entry.get("status") == "none":
        return f"{label} {NO_ITEMS}"
    if entry.get("status") != "ok" or entry.get("mean") is None:
        return f"{label}{NOT_MEASURED}"
    n = int(entry.get("n_measured") or 0)
    if entry.get("pm") is None:  # 句子太少：只写量到的平均，不写误差范围
        return f"{label} {float(entry['mean']):.1f}%" + (f"（只有 {n} 句，太少，量不出误差范围）" if count else "")
    text = f"{label} {float(entry['mean']):.1f}% ± {float(entry['pm']):.1f}"
    return text + (f"（{n} 句）" if count else "")


def four_scores_text(scores: Optional[Dict[str, Any]]) -> str:
    """「中英夹在一起 X% ± a（n 句）｜纯中文 Y% ± b（m 句）｜纯英文 —（没有这类句子）｜综合总评分 Z% ± c」。
    只写量到的数；量不出来写「（没测出来）」。± 是 95% 误差范围里离平均值远的那一边。"""
    groups = (scores or {}).get("groups") or {}
    parts = [_fmt(GROUP_LABELS[g], groups.get(g) or ({"status": "none"} if scores else {})) for g in GROUP_ORDER]
    parts.append(_fmt(COMPOSITE_LABEL, (scores or {}).get("composite") or {}, count=False))
    return "｜".join(parts)


def few_groups(scores: Optional[Dict[str, Any]]) -> List[str]:
    """量到了、但句子太少（不到 MIN_INTERVAL_N 句）的组：比两个模型时这几组不算「明显更好 / 更差」。"""
    groups = (scores or {}).get("groups") or {}
    return [g for g in GROUP_ORDER if (groups.get(g) or {}).get("status") == "ok" and (groups.get(g) or {}).get("few")]


def has_english(scores: Optional[Dict[str, Any]]) -> bool:
    """有没有带英文的句子（中英夹在一起 / 纯英文）参加了比较：有的话要提示声纹模型判断英文没那么准。"""
    groups = (scores or {}).get("groups") or {}
    return any(int((groups.get(g) or {}).get("n") or 0) > 0 for g in ("mixed", "en"))


def weights_text(weights: Dict[str, float], source: str = "material") -> str:
    """综合总评分的比例说明（「中英夹在一起 56%、纯中文 44%」）。"""
    if not weights:
        return ""
    body = "、".join(f"{GROUP_LABELS[g]} {100.0 * weights[g]:.0f}%" for g in GROUP_ORDER if g in weights)
    if source == "material":
        return f"综合总评分按你素材里各类句子实际说话时间的比例算：{body}"
    if source == "items":
        return f"综合总评分按这次检查的句子里各类句子的时长比例算（你素材里的比例没量出来）：{body}"
    return f"综合总评分的比例：{body}"
