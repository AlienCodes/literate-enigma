"""Compute speaker embeddings for every model x preprocessing x set; cache as npy.

usage: python3 embed_all.py [model-substring ...]
"""
import glob
import os
import sys
import time

import numpy as np
import sherpa_onnx

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = sorted(m for m in glob.glob(os.path.join(HERE, "models", "*.onnx")) if "silero" not in m)
SETS = os.environ.get("SETS", "en_eval,en_cal,en_cohort,zh").split(",")
OUT = os.path.join(HERE, "emb")
PREPS = os.environ.get("PREPS", "raw,vad").split(",")
os.makedirs(OUT, exist_ok=True)
VAD_MODEL = os.path.join(HERE, "models", "silero_vad.onnx")
PAD = int(0.10 * 16000)


def make_vad():
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = VAD_MODEL
    cfg.silero_vad.threshold = 0.5
    cfg.silero_vad.min_silence_duration = 0.25
    cfg.silero_vad.min_speech_duration = 0.10
    cfg.silero_vad.max_speech_duration = 30.0
    cfg.silero_vad.window_size = 512
    cfg.sample_rate = 16000
    cfg.num_threads = 1
    return cfg


def vad_speech(y, cfg):
    """Keep only speech (silero VAD), each segment padded by 100 ms of the original audio."""
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=max(30, int(len(y) / 16000) + 5))
    w = cfg.silero_vad.window_size
    spans = []
    for i in range(0, len(y), w):
        vad.accept_waveform(y[i:i + w])
        while not vad.empty():
            seg = vad.front
            spans.append((seg.start, seg.start + len(seg.samples)))
            vad.pop()
    vad.flush()
    while not vad.empty():
        seg = vad.front
        spans.append((seg.start, seg.start + len(seg.samples)))
        vad.pop()
    if not spans:
        return y
    merged = []
    for s, e in spans:
        s, e = max(0, s - PAD), min(len(y), e + PAD)
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    out = np.concatenate([y[s:e] for s, e in merged])
    return out if len(out) >= 0.5 * 16000 else y


def main(filters):
    sets = {s: dict(np.load(os.path.join(HERE, f"set_{s}.npz"), allow_pickle=True)) for s in SETS}
    vcfg = make_vad()
    cache = {}
    from speech_only import speech_only
    fns = {"vad": lambda a: vad_speech(a, vcfg), "nrg": speech_only}
    for prep in PREPS:
        if prep == "raw":
            continue
        for s in SETS:
            p = os.path.join(OUT, f"{prep}_{s}.npy")
            if os.path.exists(p):
                cache[prep, s] = np.load(p, allow_pickle=True)
            else:
                t0 = time.time()
                cache[prep, s] = np.array([fns[prep](np.asarray(a, np.float32)) for a in sets[s]["audio"]], dtype=object)
                np.save(p, cache[prep, s], allow_pickle=True)
                kept = sum(len(a) for a in cache[prep, s]) / max(1, sum(len(a) for a in sets[s]["audio"]))
                print(f"{prep} {s}: kept {kept:.0%} of audio ({time.time() - t0:.0f}s)", flush=True)
    for m in MODELS:
        name = os.path.basename(m)[:-5]
        if filters and not any(f in name for f in filters):
            continue
        ex = sherpa_onnx.SpeakerEmbeddingExtractor(
            sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=m, num_threads=4, provider="cpu"))
        for prep in PREPS:
            for s in SETS:
                p = os.path.join(OUT, f"{name}__{prep}__{s}.npy")
                if os.path.exists(p):
                    continue
                t0 = time.time()
                src = sets[s]["audio"] if prep == "raw" else cache[prep, s]
                embs = []
                for a in src:
                    st = ex.create_stream()
                    st.accept_waveform(16000, np.asarray(a, np.float32))
                    st.input_finished()
                    embs.append(np.asarray(ex.compute(st), np.float32))
                np.save(p, np.stack(embs))
                print(f"{name} {prep} {s}: {len(embs)} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
