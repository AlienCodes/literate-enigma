"""Same root cause as t5: 保存修改's apply_review rewrites manifest.jsonl from a stale copy without review._LOCK.
If the teacher starts 「一键全部文字校正」 (new material) right after 保存修改 (allowed: the edit guard only blocks
save while textfix runs, not textfix while save runs), the one-click's red marks / 已采用 state for the new rows are
lost although its fixes are in the drafts and the batch is marked used."""
import threading, time, sys
import numpy as np, soundfile as sf
from h import *
N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
ids = [f"a{i:03d}" for i in range(N)] + ["n000", "n001"]
texts = ["这个借词是一个定语从剧。"] * N + ["它是一个关键代词", "我们看关系带词。"]
cfg, p = voice(texts, ids=ids, extra={k: {"source": "s1", "start": float(i), "end": float(i) + 3} for i, k in enumerate(ids)})
sr = 32000; rng = np.random.default_rng(0)
for r in p.load_manifest():
    path = p.abspath(r["path"]); path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), (0.1 * np.sin(np.arange(sr * 3) / 10) * (rng.random(sr * 3) > 0.3)).astype(np.float32), sr)
wf.apply_review(cfg, "v", read_csv=False)
tf.mark_textfix_used(p, ids[:N])                   # batch 1 already used; n000/n001 are new material
for k in ids[:N]: review.set_draft(p, k, text="这个介词是一个定语从句。")   # teacher fixed batch 1 by hand, unsaved
def save():
    t = time.time(); wf.review_save(cfg, "v"); print("保存修改 took", round(time.time() - t, 2))
def click():
    time.sleep(0.2); t = time.time(); wf.run_transcript_fix(cfg, "v", once=True); print("one-click took", round(time.time() - t, 2))
a = threading.Thread(target=save); b = threading.Thread(target=click); a.start(); b.start(); a.join(); b.join()
for k in ("n000", "n001"):
    rec, c = cur(p, k); i = review.analyze(rec, c)
    print(k, c, "| suspect kept:", "suspect" in rec, "| 已采用 undo:", i["undo"], "(expected suspect + undo)")
print("button grey:", tf.textfix_used(p))
