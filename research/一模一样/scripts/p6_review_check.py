"""「一模一样」P6 审查后的实测（开发机，只用处理器，合成的声音，不是老师的数据）。

1. 一句话说话部分的底噪：以前的量法（有声音的那一段里逐帧电平的 p10）和现在的量法（每个频率取所有帧的 p10、
   再取所有频率的中位数，utils.audio.speech_noise_floor_db）各量出多少：干净的、连着说的句子；加了白噪声 / 粉红噪声的；
   句子里有停顿（数字静音 / 有底噪）的。以及量一句要多久。
2. 「去杂音」版本的响度：4 句有底噪（约 −50 dB）的句子，A 按 _levels 调到 −20 LUFS；B 用真的 noisereduce 去杂音，
   照搬 A 的系数（以前）和每句调回 A 的响度（现在，_match_levels）各是多少 LUFS、每句差多少。没装 noisereduce 时跳过。

运行：python research/一模一样/scripts/p6_review_check.py（结果写到旁边的 p6_review_check_结果.txt）
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from voicetwin.backends.workers.dummy_worker import synth_speech  # noqa: E402
from voicetwin.config import load_config  # noqa: E402
from voicetwin.project import Project  # noqa: E402
from voicetwin.synth import engine as eng  # noqa: E402
from voicetwin.synth.script import ScriptSegment  # noqa: E402
from voicetwin.utils.audio import (  # noqa: E402
    auto_silence_threshold,
    frame_rms_db,
    measure_lufs,
    speech_level_db,
    speech_noise_floor_db,
)

OUT = Path(__file__).with_name("p6_review_check_结果.txt")
LINES = []
TEXT = "今天我们来学习这个例子大家注意听"


def say(text: str = "") -> None:
    print(text)
    LINES.append(text)


def old_floor(wav: np.ndarray, sr: int) -> float:
    """P6 审查以前的量法（原样抄下来）：有声音的那一段里逐帧电平的 p10。"""
    db = frame_rms_db(wav, sr)
    idx = np.flatnonzero(db >= auto_silence_threshold(wav, sr))
    return float(np.percentile(db[idx[0]:idx[-1] + 1], 10))


def pink(n: int, rng: np.random.Generator) -> np.ndarray:
    x = np.fft.rfft(rng.normal(size=n))
    f = np.arange(x.size, dtype=np.float64)
    f[0] = 1.0
    y = np.fft.irfft(x / np.sqrt(f), n)
    return y / np.std(y)


def with_pause(seed: int, sr: int, hiss: float = 0.0, scale: float = 1.0) -> np.ndarray:
    a = synth_speech(TEXT, sr=sr, seed=seed, noise=0.0)[:sr]
    b = synth_speech(TEXT, sr=sr, seed=seed + 1, noise=0.0)[:sr]
    w = np.concatenate([a, np.zeros(sr // 4, np.float32), b]) * scale
    if hiss:
        w = w + np.random.default_rng(seed).normal(0, hiss, w.size)
    return eng.trim_edges(w.astype(np.float32), sr)


def check_floor() -> None:
    say("## 1. 一句话说话部分的底噪（dBFS；高于 −60 才去杂音）")
    say("每格：以前的量法 / 现在的量法。噪声的「应该是」= 20·log10(标准差)：白噪声 0.003 = −50.5，0.002 = −54.0，"
        "0.001 = −60.0，0.0005 = −66.0；粉红噪声的总电平也是 −50.5")
    for sr in (16000, 32000):
        for seed in (1, 3, 5):
            clean = eng.trim_edges(synth_speech(TEXT, sr=sr, seed=seed, noise=0.0), sr)
            rng = np.random.default_rng(seed)
            rows = [("干净", clean)]
            for name, sd in (("白 −50.5", 0.003), ("白 −54", 0.002), ("白 −60", 0.001), ("白 −66", 0.0005)):
                rows.append((name, clean + rng.normal(0, sd, clean.size)))
            rows.append(("粉红 −50.5", clean + 0.003 * pink(clean.size, rng)))
            cells = []
            for name, w in rows:
                w = np.asarray(w, dtype=np.float32)
                cells.append(f"{name} {old_floor(w, sr):.1f} / {speech_noise_floor_db(w, sr):.1f}")
            say(f"- {sr} Hz 种子 {seed}，连着说（句子里没有停顿）：" + "；".join(cells))
    for sr in (16000, 32000):
        cells = []
        for name, w in (("停顿里是数字静音", with_pause(1, sr)), ("停顿里有 −50.5 dB 底噪", with_pause(3, sr, 0.003)),
                        ("停顿里有 −60 dB 底噪", with_pause(5, sr, 0.001))):
            cells.append(f"{name} {old_floor(w, sr):.1f} / {speech_noise_floor_db(w, sr):.1f}")
        say(f"- {sr} Hz，句子中间有 0.25 秒停顿：" + "；".join(cells))
    w = eng.trim_edges(synth_speech(TEXT * 3, sr=32000, seed=1), 32000)
    t0 = time.perf_counter()
    for _ in range(20):
        speech_noise_floor_db(w, 32000)
    ms = (time.perf_counter() - t0) / 20 * 1000
    t0 = time.perf_counter()
    for _ in range(20):
        old_floor(w, 32000)
    ms_old = (time.perf_counter() - t0) / 20 * 1000
    say(f"- 量一句 {len(w) / 32000:.1f} 秒（32 kHz）：现在 {ms:.1f} 毫秒，以前 {ms_old:.1f} 毫秒")
    say()


class _Backend:
    name, display_name, supports_aux_refs, supports_batch, bcfg = "dummy", "测试", False, False, {}
    release_gpu_callback = None

    def model_id(self):
        return "m"

    def speed_calibration(self):
        return {"zh": 1.0}


def check_variant_level(tmp: Path) -> None:
    say("## 2. 「去杂音」版本的响度（目标 −20 LUFS，她句子之间的音量差 ±1.3 dB）")
    try:
        import noisereduce  # noqa: F401
    except Exception:
        say("没装 noisereduce，跳过")
        return
    cfg = load_config(overrides={"workspace": str(tmp / "ws"), "backend": "dummy", "speaker_encoder": "mfcc"},
                      user_config=False)
    project = Project(cfg, "实测")
    project.root.mkdir(parents=True, exist_ok=True)
    project.references_path.write_text("[]", encoding="utf-8")
    n = eng.Narrator(cfg, project, _Backend(), quality="identical", tier="none")
    n._identical = {"twin": {"loudness": {"sd": 1.3, "p05": -2.3, "p95": 1.2, "n": 30}}, "pool": [], "bank_sig": "",
                    "prior": {}, "prior_version": "", "weights": {}, "weights_version": "default", "block": {},
                    "profile_sig": "x"}
    n.profile = {"loudness": {"source_lufs": -20.0}}
    sr = 16000
    wavs = [with_pause(s, sr, 0.003, 0.3) for s in (1, 3, 5, 7)]
    results = [eng.SegmentResult(ScriptSegment(text=f"第{i}句", display=f"第{i}句", lang="zh", index=i), w, sr, {},
                                 "r1", False, i) for i, w in enumerate(wavs)]
    layout = n._layout(results)
    gains, _ = n._levels(results, layout, sr)
    wavs_b = [eng.denoise_light(w, sr) for w in wavs]
    changed = [i for i in range(len(wavs)) if not np.array_equal(wavs_b[i], wavs[i])]
    a = n._render(layout, [(w, sr) for w in wavs], sr, gains)
    b_old = n._render(layout, [(w, sr) for w in wavs_b], sr, gains)
    gains_b, info = n._match_levels(wavs, wavs_b, gains, changed, sr)
    b_new = n._render(layout, [(w, sr) for w in wavs_b], sr, gains_b)

    def levels(x: np.ndarray) -> str:
        return "、".join(f"{speech_level_db(x[int(round(s * sr)):int(round(s * sr)) + m], sr):.2f}" for s, m in layout)

    say(f"- 真的去过杂音的句子：第 {'、'.join(str(i + 1) for i in changed)} 句；每句调回了 "
        f"{'、'.join(f'{v:+.2f}' for v in info['restored_db'].values())} dB")
    say(f"- A：{measure_lufs(a, sr):.2f} LUFS，每句说话时的响度 {levels(a)} dB")
    say(f"- B 照搬 A 的系数（以前）：{measure_lufs(b_old, sr):.2f} LUFS，每句 {levels(b_old)} dB")
    say(f"- B 每句调回 A 的响度（现在）：{measure_lufs(b_new, sr):.2f} LUFS，每句 {levels(b_new)} dB")
    say(f"- 停顿里的 0：A {np.count_nonzero(a == 0.0)} 个，B（现在）{np.count_nonzero(b_new == 0.0)} 个")
    say()


def main() -> None:
    say(f"Python {sys.version.split()[0]}，numpy {np.__version__}")
    say()
    check_floor()
    with tempfile.TemporaryDirectory() as d:
        check_variant_level(Path(d))
    OUT.write_text("\n".join(LINES) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
