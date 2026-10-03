"""Lost update: wf.review_save()/review_delete()/review_confirm() run apply_review() OUTSIDE review._LOCK.

apply_review() does load_manifest() -> filters/splits -> save_manifest(); a quick action (save one row, delete a
row) that lands in that window is overwritten with the stale copy.

Mode "hook": deterministic. We wrap prepare.apply_filters so that, while thread A (保存修改) is inside
apply_review (after its load_manifest), thread B performs 「💾 保存这一行」 for another row and 「🗑️ 删除这一行」
for a third row, both of which complete normally. Then A continues and saves.

Mode "timing": no hooks at all; thread B fires a few ms after A started, repeated N times; counts lost updates.
"""
import random
import sys
import threading
import time

from common import cleanup, lecture, make_cfg, workspace

from voicetwin import workflows as wf
from voicetwin.data import prepare as prep_mod
from voicetwin.data import review

mode = sys.argv[1] if len(sys.argv) > 1 else "hook"
VOICE = "竞争测试"
ws = workspace("race")
cfg = make_cfg(ws)
wf.run_prepare(cfg, VOICE, [str(lecture(2))])
proj = wf.open_project(cfg, VOICE, must_exist=True)
ids = [r["id"] for r in proj.load_manifest() if r.get("keep") and r.get("text")]
X, Y, Z = ids[0], ids[1], ids[2]

if mode == "hook":
    inside, b_done = threading.Event(), threading.Event()
    orig = prep_mod.apply_filters

    def hooked(*a, **kw):
        if threading.current_thread().name == "A":
            inside.set()
            b_done.wait(30)
        return orig(*a, **kw)

    prep_mod.apply_filters = hooked
    review.set_draft(proj, X, text="甲：老师改好的第一句。")

    def thread_a():
        wf.review_save(cfg, VOICE)  # 「保存修改」

    def thread_b():
        inside.wait(30)
        review.set_draft(proj, Y, text="乙：老师改好的另一句。")
        r1 = wf.review_save(cfg, VOICE, ids=[Y])  # 「💾 保存这一行」
        r2 = wf.review_delete(cfg, VOICE, Z)       # 「🗑️ 删除这一行」
        print("B finished OK: saved", r1["saved"], "deleted", r2["id"])
        b_done.set()

    ta, tb = threading.Thread(target=thread_a, name="A"), threading.Thread(target=thread_b, name="B")
    ta.start(); tb.start(); ta.join(); tb.join()
    prep_mod.apply_filters = orig
    recs = {r["id"]: r for r in proj.load_manifest()}
    print("X text:", recs[X]["text"])
    print("Y text:", recs[Y]["text"], "| Y still in draft:", Y in review.load_draft(proj))
    print("Z deleted:", recs[Z].get("deleted"), "keep:", recs[Z].get("keep"))
    from voicetwin.data.exporters import train_records
    print("Z used for training:", any(r["id"] == Z for r in train_records(proj, include_val=True)))
else:
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    lost_text = lost_del = 0
    for k in range(n):
        # reset Y/Z
        recs = proj.load_manifest()
        for r in recs:
            if r["id"] == Z and r.get("deleted"):
                review.restore_clip(proj, Z)
        review.set_draft(proj, X, text=f"甲{k}：老师改好的第一句。")
        from voicetwin.utils.textutil import clean_transcript
        want = clean_transcript(f"乙{k}：老师改好的另一句。")
        review.set_draft(proj, Y, text=want)

        def a():
            wf.review_save(cfg, VOICE, ids=[X])

        def b():
            time.sleep(random.uniform(0.0, float(sys.argv[3]) if len(sys.argv) > 3 else 0.05))
            wf.review_save(cfg, VOICE, ids=[Y])
            wf.review_delete(cfg, VOICE, Z)

        ta, tb = threading.Thread(target=a), threading.Thread(target=b)
        ta.start(); tb.start(); ta.join(); tb.join()
        recs = {r["id"]: r for r in proj.load_manifest()}
        lt = recs[Y]["text"] != want
        ld = not recs[Z].get("deleted")
        lost_text += lt
        lost_del += ld
        print(f"round {k}: Y text lost={lt} (now {recs[Y]['text'][:12]!r}, draft has Y={Y in review.load_draft(proj)}), Z delete lost={ld}")
    print(f"lost saved edits: {lost_text}/{n}; lost deletions: {lost_del}/{n}")
cleanup()
