"""第四轮 g4 / pipeline#7：自动降噪的噪声样本从哪里取。

讲课录音开头 20 秒一直在说话（没有停顿），后面每句之间停 0.6~1.2 秒，加上白噪声。比较「说话的那些时间」
降噪前后的能量变化（越接近 0 dB 越好，说明没有削掉老师的声音）：
- 不给噪声样本（修以前的代码：noisereduce 拿开头 600000 个样本当噪声 = 44.1 kHz 下的 13.6 秒，正好是说话声）
- 给真正的噪声样本（理想情况）
- 现在程序里的 denoise()（噪声样本取停顿里最安静的部分）

运行（要 noisereduce，整合包同版本环境里有）：/tmp/gsv39/bin/python research/全面找bug/第四轮/g4_脚本/denoise_profile.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import noisereduce as nr  # noqa: E402

from conftest import SENTENCES  # noqa: E402
from voicetwin.backends.workers.dummy_worker import synth_speech  # noqa: E402
from voicetwin.data.enhance import denoise  # noqa: E402
from voicetwin.utils.audio import estimate_snr  # noqa: E402


def lecture(sr, seed=0):
    rng = np.random.default_rng(seed)
    parts, mask, t, k = [], [], 0.0, 0
    while t < 20.0:
        w = synth_speech(SENTENCES[k % len(SENTENCES)], sr=sr, seed=k)
        parts.append(w)
        mask.append(np.ones(len(w), bool))
        t += len(w) / sr
        k += 1
    for _ in range(12):
        w = synth_speech(SENTENCES[k % len(SENTENCES)], sr=sr, seed=k)
        k += 1
        z = np.zeros(int(rng.uniform(0.6, 1.2) * sr), np.float32)
        parts += [w, z]
        mask += [np.ones(len(w), bool), np.zeros(len(z), bool)]
    return np.concatenate(parts).astype(np.float32), np.concatenate(mask)


def main():
    for sr in (44100, 16000):
        clean, m = lecture(sr)
        rng = np.random.default_rng(5)
        for std in (0.01, 0.02):
            noise = rng.normal(0, std, len(clean)).astype(np.float32)
            noisy = clean + noise

            def change(out):
                return 10 * np.log10(np.mean(out[m].astype(np.float64) ** 2) / np.mean(noisy[m].astype(np.float64) ** 2))

            old = nr.reduce_noise(y=noisy, sr=sr, stationary=True, prop_decrease=0.6, n_std_thresh_stationary=1.5)
            ideal = nr.reduce_noise(y=noisy, sr=sr, y_noise=noise[:sr * 5], stationary=True, prop_decrease=0.6,
                                    n_std_thresh_stationary=1.5)
            now = denoise(noisy, sr, 0.6)
            print(f"{sr} Hz 噪声 std {std}（估计信噪比 {estimate_snr(noisy, sr):.1f} dB）：说话声能量变化 "
                  f"修以前 {change(old):.2f} dB | 理想 {change(ideal):.2f} dB | 现在 {change(now):.2f} dB")


if __name__ == "__main__":
    main()
