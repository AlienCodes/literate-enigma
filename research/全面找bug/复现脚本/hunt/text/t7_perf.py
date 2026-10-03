"""How long do the table functions take on a long row (the table calls analyze for every row on every refresh)."""
import time, sys
from h import *
n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
text = "这个借词是一个定语从剧，" * n
cfg, p = voice([text])
t = time.time(); wf.run_transcript_fix(cfg, "v", once=True); print("len", len(text), "click", round(time.time() - t, 2))
rec, c = cur(p, "c000")
t = time.time(); i = review.analyze(rec, c); print("analyze (fixed text)", round(time.time() - t, 2), "undo", len(i["undo"]))
# teacher types one char somewhere: text no longer a known state -> _toward/_on_path paths
review.set_draft(p, "c000", text=c[:5] + "曌" + c[5:])
rec, c = cur(p, "c000")
t = time.time(); i = review.analyze(rec, c); print("analyze (teacher typed)", round(time.time() - t, 2), "undo", len(i["undo"]))
t = time.time()
try:
    review.unadopt_suggestion(p, "c000"); print("unadopt", round(time.time() - t, 2))
except ValueError as e: print("unadopt refused", round(time.time() - t, 2))
