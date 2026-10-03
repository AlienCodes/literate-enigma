"""「一模一样」排序权重的校准（设计方案 research/一模一样/设计方案原文.md §1.3「Afterwards」、§2 P8）。只用 numpy / scipy。

生成时每句从几十个版本里挑一个，挑的依据是综合分（像你本人、错字、语速偏差、音调起伏、频谱形状……）。几项之间的权重
是工程上定的；这里用你没参加训练的真实录音实测一下：挑选第三步每句话生成的几个版本，各自和你本人读同一句的真实录音比
（「真实答案」= 和你那句录音的声纹有多像 − 音调走向差多少 − 长短差多少，都换成这一句里的 z 分数），看哪组权重排出来的
顺序和真实答案最一致（每句里的 Spearman 等级相关，取平均）。

为了不自己骗自己：每次留出一句不看，用其余的句子挑权重，再拿这组权重去排留出的那句（leave-one-item-out）；
平均下来比默认权重至少好 0.05、并且不是碰巧（对句子重新抽样 2000 次，95% 范围的下限也比默认的好）才换，
否则照旧用默认权重（adopted = False）。只看平均好 0.05：几十句、每句 8 个版本时，纯随机的真实答案也有大约四分之一的机会
碰巧超过（实测，见 research/一模一样/记录.md），所以另加了「不是碰巧」这一条。
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from voicetwin.utils.textutil import short_hash

#: 要试的权重（设计方案 §2 P8）
GRID_RATE = (0.2, 0.4, 0.8)
GRID_PROS = (0.0, 0.15, 0.3)
GRID_LTAS = (0.0, 0.04)
GRID_CAP = ("p90", "none")
#: 默认权重（和 eval/identical_judge.py 不校准时一样：语速 0.4、音调起伏 0、频谱 0、像你本人封顶在你自己录音的 p90）
DEFAULTS: Dict[str, Any] = {"rate": 0.4, "pros": 0.0, "ltas": 0.0, "cap": "p90"}
#: 留一句法平均比默认权重至少好这么多才换
MIN_GAIN = 0.05
#: 综合分里另外两项的权重（不校准）：像你本人 2.0、错字率 1.0
W_SPEAKER = 2.0
W_CER = 1.0
#: 一句话里至少要有几个能比的版本
MIN_CANDS = 3
#: 「不是碰巧」：对句子重新抽样几次、用哪个种子
N_BOOT = 2000
BOOT_SEED = 1234


def _num(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def grid() -> List[Dict[str, Any]]:
    return [{"rate": r, "pros": p, "ltas": l, "cap": c}
            for r, p, l, c in itertools.product(GRID_RATE, GRID_PROS, GRID_LTAS, GRID_CAP)]


def production_score(c: Dict[str, Any], w: Dict[str, Any], cap_value: Optional[float] = None) -> float:
    """按这组权重算的综合分（和生成时一样的写法）：
    2.0 × (min(像你本人, 你自己录音的 p90) − 0.5 × 模型之间的差别) / 100 − 错字率 − w_rate × 时长偏差
    − w_pros × 音调起伏偏差 − w_ltas × 频谱偏差。量不出来的项不算。"""
    pct = _num(c.get("pct_raw"))
    total = 0.0
    if pct is not None:
        if w.get("cap") == "p90" and cap_value is not None:
            pct = min(pct, float(cap_value))
        total += W_SPEAKER * (pct - 0.5 * float(_num(c.get("spread")) or 0.0)) / 100.0
    total -= W_CER * float(_num(c.get("cer")) or 0.0)
    total -= float(w.get("rate", 0.0)) * float(_num(c.get("dur_dev")) or 0.0)
    total -= float(w.get("pros", 0.0)) * float(_num(c.get("prosody_z")) or 0.0)
    total -= float(w.get("ltas", 0.0)) * float(_num(c.get("ltas_d")) or 0.0)
    return float(total)


def _z(values: Sequence[Optional[float]]) -> np.ndarray:
    """这一句里的 z 分数；量不出来的当作平均（z = 0）；都一样时全是 0。"""
    arr = np.asarray([np.nan if v is None else float(v) for v in values], dtype=np.float64)
    ok = np.isfinite(arr)
    out = np.zeros(arr.size, dtype=np.float64)
    if ok.sum() >= 2:
        mu, sd = float(arr[ok].mean()), float(arr[ok].std())
        if sd > 1e-12:
            out[ok] = (arr[ok] - mu) / sd
    return out


def truth_values(cands: Sequence[Dict[str, Any]]) -> np.ndarray:
    """真实答案：z(和你那句真实录音的声纹有多像) − z(音调走向差多少，半音) − z(|ln 长短比|)。"""
    r = _z([_num(c.get("to_real")) for c in cands])
    f0 = _z([_num(c.get("f0_rmse")) for c in cands])
    ratios = []
    for c in cands:
        d = _num(c.get("dur_ratio"))
        ratios.append(abs(math.log(d)) if d is not None and d > 0 else None)
    dur = _z(ratios)
    return r - f0 - dur


def spearman(a: Sequence[float], b: Sequence[float]) -> Optional[float]:
    """Spearman 等级相关（同分取平均名次）；有一边全一样时没有意义，返回 None。"""
    from scipy.stats import rankdata

    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.size < 2 or a.size != b.size:
        return None
    ra, rb = rankdata(a), rankdata(b)
    if float(np.std(ra)) < 1e-12 or float(np.std(rb)) < 1e-12:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


def _group_item(key: Any, cands: Sequence[Dict[str, Any]]) -> str:
    for c in cands:
        if c.get("item") is not None:
            return str(c["item"])
    return str(key)


def calibrate(cands_by_group: Dict[Any, Sequence[Dict[str, Any]]], cap_value: Optional[float] = None,
              min_gain: float = MIN_GAIN) -> Dict[str, Any]:
    """校准排序权重。cands_by_group：{(模型, 句子): [版本, …]}，每个版本是一个 dict：
    pct_raw、spread、cer、dur_dev、prosody_z、ltas_d（生成时就能算的），to_real、f0_rmse、dur_ratio（要和你的真实录音比，
    只用来算真实答案），item（哪一句：留一句法按它留）。cap_value：你自己录音的 p90（像你本人封顶用；没有就不封顶）。

    返回 {"weights", "version", "gain", "adopted", "loo", "default_score", "n_groups", "n_items"}：
    没换（adopted = False）时 weights 是空的、version 是 "default"（生成时照旧用默认权重，缓存键也不变）。"""
    table = grid()
    d_idx = next(i for i, w in enumerate(table) if all(w[k] == DEFAULTS[k] for k in DEFAULTS))
    rows: List[np.ndarray] = []
    items: List[str] = []
    for key, cands in cands_by_group.items():
        cands = [c for c in cands if isinstance(c, dict)]
        if len(cands) < MIN_CANDS:
            continue
        truth = truth_values(cands)
        if float(np.std(truth)) < 1e-12:
            continue
        vals = np.full(len(table), np.nan)
        for i, w in enumerate(table):
            rho = spearman([production_score(c, w, cap_value) for c in cands], truth)
            if rho is not None:
                vals[i] = rho
        if not np.isfinite(vals[d_idx]):
            continue
        rows.append(np.where(np.isfinite(vals), vals, 0.0))
        items.append(_group_item(key, cands))
    out: Dict[str, Any] = {"weights": {}, "version": "default", "gain": None, "adopted": False, "loo": None,
                           "default_score": None, "n_groups": len(rows), "n_items": len(set(items)),
                           "grid": len(table), "min_gain": min_gain}
    if not rows or len(set(items)) < 2:
        out["why"] = "能比的句子不够（至少要 2 句，每句至少 3 个版本）"
        return out
    S = np.vstack(rows)
    item_arr = np.asarray(items)
    loo_vals: List[float] = []
    item_gain: List[float] = []
    for h in sorted(set(items)):
        train, test = item_arr != h, item_arr == h
        if not train.any():
            continue
        best = _argmax(S[train].mean(axis=0), d_idx)
        loo_vals += [float(v) for v in S[test, best]]
        item_gain.append(float(np.mean(S[test, best] - S[test, d_idx])))
    loo = float(np.mean(loo_vals)) if loo_vals else None
    base = float(S[:, d_idx].mean())
    out.update(loo=None if loo is None else round(loo, 4), default_score=round(base, 4))
    if loo is None:
        return out
    gain = loo - base
    out["gain"] = round(gain, 4)
    g = np.asarray(item_gain, dtype=np.float64)
    idx = np.random.default_rng(BOOT_SEED).integers(0, g.size, size=(N_BOOT, g.size))
    lo = float(np.percentile(g[idx].mean(axis=1), 2.5))
    out["gain_lo"] = round(lo, 4)
    if gain >= min_gain and lo > 0:
        w = table[_argmax(S.mean(axis=0), d_idx)]
        out.update(adopted=True, weights=dict(w), version="cal-" + short_hash(sorted(w.items()), n=8))
    return out


def _argmax(scores: np.ndarray, default_idx: int) -> int:
    """分数最高的那组权重；一样高时优先默认权重，再按表里的顺序（结果固定，不随机）。"""
    best = float(np.max(scores))
    if scores[default_idx] >= best - 1e-12:
        return int(default_idx)
    return int(np.flatnonzero(scores >= best - 1e-12)[0])


def describe(result: Dict[str, Any]) -> str:
    """一句中文说明（日志、记录用）。只写实测的数。"""
    if not result:
        return ""
    if result.get("why"):
        return f"排序权重这次没校准（{result['why']}），照旧用默认的"
    gain = result.get("gain")
    if gain is None:
        return "排序权重这次没校准（量不出来），照旧用默认的"
    if result.get("adopted"):
        w = result.get("weights") or {}
        return (f"排序权重已按你的录音校准（留一句法实测比默认的排得更准 {gain:+.3f}）：语速 {w.get('rate')}、"
                f"音调起伏 {w.get('pros')}、频谱 {w.get('ltas')}、像你本人{'封顶在你自己录音的 p90' if w.get('cap') == 'p90' else '不封顶'}")
    if gain >= float(result.get("min_gain", MIN_GAIN)):
        return f"排序权重照旧用默认的（按你的录音校准好 {gain:+.3f}，但可能是碰巧：误差范围的下限没有比默认的好）"
    return f"排序权重照旧用默认的（按你的录音校准只好 {gain:+.3f}，不到 {result.get('min_gain', MIN_GAIN)}，不值得换）"
