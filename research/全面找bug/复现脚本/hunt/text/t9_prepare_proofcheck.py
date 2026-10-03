"""Batch 1 one-clicked + saved. Teacher adds new material: 开始准备素材 re-runs 自动查错字 on ALL rows (run_prepare ->
find_suspects). Batch-1 rows lose their 「已采用」(undo) state, and when the second engine heard the same wrong word, they
get a red mark + a 「采用」 suggestion that reverts the program's fix. The one-click (once per batch) never looks at
batch-1 rows again, so it can't clear them as it did before the once-rule."""
from h import *
from voicetwin.data import proofcheck as pc
orig = {"c000": "它是一个关键代词", "c001": "这个借词是一个定语从剧。"}
cfg, p = voice(list(orig.values()))
wf.run_transcript_fix(cfg, "v", once=True)
review.save_rows(p)
def show(tag):
    for k in orig:
        rec, c = cur(p, k); i = review.analyze(rec, c)
        print(f"  {tag} {k}: {c} red={i['red']} 采用={review.describe_edits(c, i['edits'])!r} 已采用(undo)={review.describe_adopted(c, i['undo'])!r}")
show("after one-click+save")
# new material arrives (batch 2) and prepare's proofcheck runs on every row; second engine heard the original words
review.set_draft(p, "c001", text="这个介词是一个定语从句呀。"); review.save_rows(p)   # teacher's own word 呀
show("after teacher edit+save")
recs = p.load_manifest(); recs.append({"id": "d000", "path": "clips/d000.wav", "text": "新的一句话里有借词。", "lang": "zh",
                                       "duration": 3.0, "keep": True, "split": "train"}); p.save_manifest(recs)
other = dict(orig, d000="新的一句话里有借词。")  # second engine: same mishearing as the first engine
pc._EngineRunner.recognize = lambda self, rec, lang: (other[rec["id"]], None, pc.ENGINE_FUNASR)
pc.find_suspects(p, cfg)
show("after prepare's 自动查错字")
print("  button new ids:", tf.textfix_new_ids(p))
wf.run_transcript_fix(cfg, "v", once=True)
show("after one-click on batch 2")
