"""P8 排序权重校准（voicetwin/synth/calibrate_rank.py）：真实答案是纯随机数时，会不会「碰巧」换掉默认权重；
埋进去的权重能不能找回来。比较只看「留一句法平均好 0.05」（设计方案原文）和另加「对句子重新抽样 2000 次、
95% 范围的下限也比默认的好」两种规则。
运行：python research/一模一样/scripts/p8_calibrate_noise.py
"""
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from voicetwin.synth import calibrate_rank as CR  # noqa: E402


def cands(rng, n_groups, w_true, noise, per=8, cap=110.0):
    groups = {}
    for gi in range(n_groups):
        out = []
        for _ in range(per):
            c = {"pct_raw": float(rng.uniform(80, 130)), "spread": float(rng.uniform(0, 10)), "cer": 0.0,
                 "dur_dev": float(rng.uniform(0, 0.3)), "prosody_z": float(rng.uniform(0, 2)),
                 "ltas_d": float(rng.uniform(0, 3)), "f0_rmse": 1.0, "dur_ratio": 1.0, "item": f"i{gi}"}
            c["to_real"] = float(rng.normal()) if noise else CR.production_score(c, w_true, cap)
            out.append(c)
        groups[f"m|i{gi}"] = out
    return groups


for n_groups in (20, 60):
    only_mean = both = 0
    seeds = range(1, 201)
    t0 = time.perf_counter()
    for seed in seeds:
        r = CR.calibrate(cands(np.random.default_rng(seed), n_groups, CR.DEFAULTS, True), cap_value=110.0)
        only_mean += int(r["gain"] is not None and r["gain"] >= CR.MIN_GAIN)
        both += int(r["adopted"])
    dt = (time.perf_counter() - t0) / len(seeds)
    print(f"纯随机，{n_groups} 句 × 8 个版本，{len(seeds)} 个种子：只看平均好 0.05 → {only_mean} 次换掉默认权重"
          f"（{100 * only_mean / len(seeds):.1f}%）；另加误差范围下限 → {both} 次（{100 * both / len(seeds):.1f}%）；"
          f"每次校准 {1000 * dt:.0f} 毫秒")
planted = {"rate": 0.8, "pros": 0.3, "ltas": 0.04, "cap": "none"}
ok = 0
for seed in range(1, 51):
    r = CR.calibrate(cands(np.random.default_rng(seed), 20, planted, False), cap_value=110.0)
    ok += int(r["adopted"] and r["weights"] == planted)
print(f"埋进去的权重（语速 0.8、音调起伏 0.3、频谱 0.04、不封顶），20 句 × 8 个版本，50 个种子：找回 {ok} 次")
