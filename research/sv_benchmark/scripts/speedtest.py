import time, glob, os, numpy as np, librosa, sherpa_onnx, warnings
warnings.filterwarnings('ignore')
y, _ = librosa.load('data/sr-data/enroll/leijun-sr-2.wav', sr=16000)
y = y.astype(np.float32)
for m in sorted(glob.glob('models/*.onnx')):
    if 'silero' in m: continue
    cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=m, num_threads=4, debug=False, provider='cpu')
    t0=time.time(); ex = sherpa_onnx.SpeakerEmbeddingExtractor(cfg); tl=time.time()-t0
    def emb():
        s = ex.create_stream(); s.accept_waveform(16000, y); s.input_finished()
        return np.array(ex.compute(s))
    e=emb(); t0=time.time()
    for _ in range(3): e=emb()
    print(f"{os.path.basename(m)[:58]:58s} dim={ex.dim:4d} load={tl:5.2f}s per4.8s={((time.time()-t0)/3)*1000:7.1f}ms")
