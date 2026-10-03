"""Rows that had no text yet (prepare stopped before 识别文字 finished) or keep=False when the web one-click ran
are marked 'used' although the one-click never looked at them. After prepare resumes and recognises them, the button
stays grey and those rows never get corrected."""
from h import *
cfg, p = voice(["这个借词是一个定语从剧。", "", "我们看关系带词。"],
               extra={"c001": {"asr_done": False}, "c002": {"keep": False, "drop_reason": "太短"}})
r = wf.run_transcript_fix(cfg, "v", once=True)
print("checked", r["checked"], "only", r["only"])
print("draft after click:", {k: v["text"] for k, v in review.load_draft(p).items()})
# prepare resumes and recognises c001 (same as prepare.py step 2 writing text into the record)
recs = p.load_manifest()
recs[1]["text"] = "这个借词是一个定语从剧。"; recs[1]["asr_done"] = True
p.save_manifest(recs)
# teacher turns on c002 ("要用") and saves
review.set_draft(p, "c002", keep=True); review.save_rows(p)
print("button grey (textfix_used):", tf.textfix_used(p), "new ids:", tf.textfix_new_ids(p))
try:
    wf.run_transcript_fix(cfg, "v", once=True)
except ValueError as e:
    print("click refused:", str(e)[:30])
print("c001 text:", cur(p, "c001")[1], "| c002 text:", cur(p, "c002")[1])
