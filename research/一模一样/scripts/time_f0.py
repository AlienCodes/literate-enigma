"""Warm timing of the non-judge parts of Scorer.score on a 5 s, 32 kHz signal (what the engine scores)."""
import sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
import numpy as np
from pathlib import Path
from voicetwin.eval.sv_models import selftest_signal
from voicetwin.style.prosody import f0_stats, f0_track
from voicetwin.utils.audio import speech_activity, resample
from voicetwin.eval.sv_frontend import SileroVAD
D = Path(__import__("os").environ.get("VT_SV_MODEL_DIR", "sv"))  # 声纹模型文件夹（scripts/fetch_sv_models.py 下载的）
s16 = selftest_signal(5.0)
s32 = resample(s16, 16000, 32000)
def t(f, n=5):
    f(); a = time.perf_counter()
    for _ in range(n): f()
    return (time.perf_counter() - a) / n * 1000
print(f"f0_stats 32k input: {t(lambda: f0_stats(s32, 32000)):.0f} ms")
print(f"f0_stats 16k input: {t(lambda: f0_stats(s16, 16000)):.0f} ms")
print(f"speech_activity 32k: {t(lambda: speech_activity(s32, 32000)):.0f} ms")
print(f"resample 32k->16k: {t(lambda: resample(s32, 32000, 16000)):.0f} ms")
vad = SileroVAD(D / "silero_vad.onnx")
print(f"silero speech_only 16k: {t(lambda: vad.speech_only(s16, 16000) if vad.speech_only.__code__.co_argcount>2 else vad.speech_only(s16)):.0f} ms")
