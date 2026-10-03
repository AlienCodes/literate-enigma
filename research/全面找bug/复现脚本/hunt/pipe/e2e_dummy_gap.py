import sys, json, numpy as np, soundfile as sf
from pathlib import Path
p = Path(sys.argv[1])
wav, sr = sf.read(str(p), dtype="int16")
rep = json.loads(p.with_suffix(".report.json").read_text(encoding="utf-8"))
prev = 0.0
for s in rep["segments"]:
    a = int(round(prev*sr)); b = int(round(s["start"]*sr))
    nz = np.nonzero(wav[a:b])[0]
    print(s["index"], "gap", a, b, "nonzero offsets from gap start:", (nz[:5]).tolist(), "from gap end:", (b - a - nz[-5:]).tolist() if len(nz) else [], "vals", wav[a:b][nz][:8].tolist())
    prev = s["end"]
a = int(round(prev*sr)); nz = np.nonzero(wav[a:])[0]
print("tail", nz[:10].tolist(), wav[a:][nz][:10].tolist())
