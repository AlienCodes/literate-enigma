from common import *
ws = Path(sys.argv[1]); cfg = make_cfg(ws)
p = wf.Project(cfg, V).ensure()
ids = [f"9999_test_{i:04d}" for i in range(len(TEXTS))]
p.save_manifest([{"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"} for i, t in zip(ids, TEXTS)])
print("created", p.root)
