"""P8 审查后：四项评分里一组（或者两个模型比的时候共同的句子）只有几句时，2000 次成对重新抽样的 95% 范围靠不靠得住。
两个模型其实一样好（每句的差别是纯随机，均值 0、标准差 2 个百分点）时，范围不包括 0（= 被说成「明显更好 / 更差」）
的比例应该是 5% 左右；句子太少时远远超过。voicetwin/eval/lang_groups.py 的 MIN_INTERVAL_N（8）按这个定。
运行：python research/一模一样/scripts/p8_boot_small_n.py
"""
import numpy as np

N_BOOT = 2000
TRIALS = 400


def main() -> None:
    rng = np.random.default_rng(0)
    for n in (1, 2, 3, 4, 5, 6, 8, 10, 20):
        false = 0
        for _ in range(TRIALS):
            d = rng.normal(0, 2.0, n)
            idx = rng.integers(0, n, size=(N_BOOT, n))
            bm = d[idx].mean(axis=1)
            lo, hi = np.percentile(bm, [2.5, 97.5])
            false += bool(lo > 0 or hi < 0)
        print(f"{n:2d} 句：被说成「明显不一样」的比例 {false / TRIALS:.1%}（应该是 5% 左右）")


if __name__ == "__main__":
    main()
