"""Measure CPU cost of the precise judge members + f0 + VAD on the dev machine (4 cores, no GPU).
Input: 5 s deterministic speech-like signal (sv_models.selftest_signal). Prints seconds per call."""
import sys, time, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
import numpy as np
from voicetwin.eval import sv_models
from voicetwin.eval.sv_models import OnnxEmbedder, MODELS, selftest_signal
from voicetwin.eval.sv_frontend import SileroVAD
D = Path(__import__("os").environ.get("VT_SV_MODEL_DIR", "sv"))  # 声纹模型文件夹（scripts/fetch_sv_models.py 下载的）
sig5 = np.tile(selftest_signal(5.0), 1)
def bench(threads):
    embs = {k: OnnxEmbedder(MODELS[k], D / MODELS[k].file, threads=threads) for k in sv_models.DEFAULT_ENSEMBLE}
    for e in embs.values(): e.embed16k(sig5)  # warm-up
    res = {}
    for k, e in embs.items():
        t = time.perf_counter(); n = 5
        for _ in range(n): e.embed16k(sig5)
        res[k] = (time.perf_counter() - t) / n
    return embs, res
for th in (0, 1, 2):
    embs, res = bench(th)
    print(f"threads={th}: " + ", ".join(f"{k} {v*1000:.0f} ms" for k, v in res.items()), f"sum {sum(res.values())*1000:.0f} ms")
# throughput: 12 candidates, 3 models, serial vs 3 worker threads (one per model; threads=1 sessions)
embs, _ = bench(1)
t = time.perf_counter()
for _ in range(12):
    for e in embs.values(): e.embed16k(sig5)
ser = time.perf_counter() - t
embs0, _ = bench(0)
t = time.perf_counter()
for _ in range(12):
    for e in embs0.values(): e.embed16k(sig5)
ser0 = time.perf_counter() - t
def score(_):
    for e in embs.values(): e.embed16k(sig5)
t = time.perf_counter()
with ThreadPoolExecutor(4) as ex: list(ex.map(score, range(12)))
par = time.perf_counter() - t
print(f"12 candidates x 3 models: serial threads=1 {ser:.2f}s, serial threads=0 {ser0:.2f}s, 4 workers threads=1 {par:.2f}s (per-model lock)")
vad = SileroVAD(D / "silero_vad.onnx")
t = time.perf_counter(); 
for _ in range(5): vad.speech(sig5, 16000) if hasattr(vad, "speech") else None
print("vad api:", [m for m in dir(vad) if not m.startswith("_")])
from voicetwin.style.prosody import f0_stats
t = time.perf_counter()
for _ in range(3): f0_stats(sig5, 16000)
print(f"f0_stats (librosa.yin) 5 s: {(time.perf_counter()-t)/3*1000:.0f} ms")
