"""P8 深度挑选里只用处理器的几步在开发机（4 核）上要多久：音调走向（MFCC + 音高 + DTW）、四项评分（2000 次重新抽样）、
10 个模型的排名（两两成对比较）、读写一次请求的结果。没有声纹模型和显卡，声纹打分、识别、生成的时间测不了（老师电脑上实测）。
运行：python research/一模一样/scripts/p8_select_timing.py
"""
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from voicetwin.eval import lang_groups as LG  # noqa: E402
from voicetwin.synth import select as sel  # noqa: E402


def glide(f0a, f0b, dur, sr=32000):
    t = np.arange(int(dur * sr)) / sr
    f = np.linspace(f0a, f0b, t.size)
    ph = 2 * np.pi * np.cumsum(f) / sr
    return (0.3 * np.sin(ph) + 0.15 * np.sin(2 * ph)).astype(np.float32)


def timed(fn, n):
    fn()  # 第一次（librosa / numba 要准备）不算
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n


real = sel._mfcc_f0(glide(120, 220, 5.0), 32000)
gen_wav = glide(125, 215, 5.4)
t_feat = timed(lambda: sel._mfcc_f0(gen_wav, 32000), 10)
gen = sel._mfcc_f0(gen_wav, 32000)
t_dtw = timed(lambda: sel._f0_dtw(gen, real), 10)
r, rmse = sel._f0_dtw(gen, real)
print(f"音调走向（5 秒、32 kHz）：MFCC + 音高 {1000 * t_feat:.0f} 毫秒，DTW + 相关 {1000 * t_dtw:.1f} 毫秒（r_F0 = {r:.3f}，"
      f"均方根差 {rmse:.2f} 半音）")

rng = np.random.default_rng(0)
groups = ["mixed"] * 24 + ["zh"] * 20
items = [{"key": f"k{i}", "group": g, "pct": float(rng.uniform(85, 100)), "w": float(rng.uniform(2, 8))}
         for i, g in enumerate(groups)]
t_four = timed(lambda: LG.group_scores(items, {"mixed": 0.56, "zh": 0.44}), 20)
print(f"四项评分（44 句、2000 次重新抽样）：{1000 * t_four:.1f} 毫秒")


def res(i):
    per = {f"k{k}": {"S": 1.0, "pct": float(rng.uniform(85, 100)), "cer": 0.0, "group": g, "w": 3.0, "kind": "val"}
           for k, g in enumerate(groups)}
    four = LG.group_scores([{"key": k, "group": v["group"], "pct": v["pct"], "w": v["w"]} for k, v in per.items()],
                           {"mixed": 0.56, "zh": 0.44})
    return {"id": f"m{i}", "ckpt": None, "previous": False, "four": four, "cer": 0.0, "total": 1.0, "per_item": per,
            "failed": 0, "n_items": 44, "pct": four["composite"]["mean"]}


models = [res(i) for i in range(10)]
t_rank = timed(lambda: sel.rank_results(models), 3)
print(f"排名（10 个模型 × 44 句，两两成对比较、读错字把关）：{t_rank:.2f} 秒")
