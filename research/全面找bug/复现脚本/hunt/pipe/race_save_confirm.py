"""「保存修改」 (A) still running its re-statistics (apply_review, outside review._LOCK) when the teacher, having
corrected one more sentence Z, clicks 「✅ 确认训练素材」 (B).  B saves Z and records the confirmation; then A writes its
stale copy of the manifest.  Z's correction is gone (its draft was consumed by B), nothing tells the teacher."""
import threading
from common import cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf
from voicetwin.data import prepare as prep_mod, review
from voicetwin.data.exporters import gptsovits_list_text
ws = workspace("race2"); cfg = make_cfg(ws); V = "张老师"
wf.run_prepare(cfg, V, [str(lecture(2))])
p = wf.open_project(cfg, V, must_exist=True)
recs = [r for r in p.load_manifest() if r.get("keep") and r.get("text") and r.get("split") == "train"]
Y, Z = recs[0], recs[1]
FIX_Z = Z["text"].replace("。", "").rstrip("，") + "（改好）。"
inside, b_done = threading.Event(), threading.Event()
orig = prep_mod.apply_filters
def hooked(*a, **kw):
    if threading.current_thread().name == "A":
        inside.set(); b_done.wait(30)
    return orig(*a, **kw)
prep_mod.apply_filters = hooked
review.set_draft(p, Y["id"], text=Y["text"].replace("。", "！"))
def a(): wf.review_save(cfg, V)
def b():
    inside.wait(30)
    review.set_draft(p, Z["id"], text=FIX_Z)
    out = wf.review_confirm(cfg, V)
    print("B: confirm returned confirmed =", out["confirmed"], "saved =", out["saved"])
    b_done.set()
ta, tb = threading.Thread(target=a, name="A"), threading.Thread(target=b, name="B")
ta.start(); tb.start(); ta.join(); tb.join()
prep_mod.apply_filters = orig
zrec = next(r for r in p.load_manifest() if r["id"] == Z["id"])
print("Z wanted :", review.clean_transcript(FIX_Z))
print("Z in manifest now:", zrec["text"], "| Z draft left:", Z["id"] in review.load_draft(p))
print("training_blocker:", repr(wf.training_blocker(p)))
wf.review_confirm(cfg, V)   # teacher clicks confirm again as told
lst = gptsovits_list_text(p, "spk")
print("after re-confirm, training list line for Z:", [l.split("|")[3] for l in lst.splitlines() if l.startswith(Z["id"] + ".wav|")])
cleanup()
