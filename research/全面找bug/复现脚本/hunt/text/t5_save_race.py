"""Lost update: 「保存修改」 runs wf.review_save -> apply_review, which reloads + rewrites manifest.jsonl WITHOUT
review._LOCK (and _clip_stats reads every changed clip's audio, so it takes seconds after the one-click changed many rows).
Row actions (gradio clip-action event = a different concurrency group, so they run at the same time) that write the
manifest meanwhile are silently overwritten:
   - 👍 这句没错 (dismiss_suspect, no apply_review of its own) -> the red mark and suggestion come back
   (delete / restore / 保存这一行 call apply_review themselves, so they usually win the race by luck)
usage: python t5_save_race.py [N rows]"""
import threading, time, sys
import numpy as np, soundfile as sf
from h import *
from voicetwin.data import proofcheck as pc
N = int(sys.argv[1]) if len(sys.argv) > 1 else 123
texts = ["这个借词是一个定语从剧。"] * N
cfg, p = voice(texts, extra={f"c{i:03d}": {"source": "s1", "start": float(i), "end": float(i) + 3} for i in range(N)})
sr = 32000
rng = np.random.default_rng(0)
for r in p.load_manifest():
    path = p.abspath(r["path"]); path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), (0.1 * np.sin(np.arange(sr * 3) / 10) * (rng.random(sr * 3) > 0.3)).astype(np.float32), sr)
wf.apply_review(cfg, "v", read_csv=False)   # stats like after prepare
wf.run_transcript_fix(cfg, "v", once=True)  # one-click: N rows fixed (unsaved drafts)
print("unsaved rows after one-click:", len(review.load_draft(p)))
last = f"c{N-1:03d}"
recs = p.load_manifest(); recs[-1]["suspect"] = {"spans": [[0, 2]], "alt": "", "reasons": ["x"], "score": 0.6}
p.save_manifest(recs)
err = []
def save():
    try:
        t = time.time(); wf.review_save(cfg, "v"); print("保存修改 took", round(time.time() - t, 2), "s")
    except Exception as e: err.append(repr(e))
def other():
    time.sleep(0.4)
    try:
        pc.dismiss_suspect(p, last)                                         # 👍 这句没错 (UI: do_clip_action "ok")
        print("这句没错 done; red now:", "suspect" in cur(p, last)[0])
    except Exception as e: err.append(repr(e))
a = threading.Thread(target=save); b = threading.Thread(target=other)
a.start(); b.start(); a.join(); b.join()
m = {r["id"]: r for r in p.load_manifest()}
print("errors", err)
print("AFTER BOTH FINISHED:")
print(" ", last, "suspect_ok:", m[last].get("suspect_ok"), "| still red:", "suspect" in m[last], "(expected suspect_ok set, not red)")
