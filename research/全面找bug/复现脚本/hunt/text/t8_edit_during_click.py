"""Teacher edits a row while 「一键全部文字校正」 is running (row edits are not blocked during the task).
check_with_transcript drops that row's result ('检查期间改过'), but run_transcript_fix still marks it used:
the row never gets checked and the button stays grey."""
from h import *
cfg, p = voice(["这个借词是一个定语从剧。", "我们看关系带词。"])
orig_check = tf.check_text
state = {"done": False}
def check_text_and_teacher_types(text, *a, **kw):
    if not state["done"]:
        state["done"] = True   # teacher double-clicks row 2 and adds a word while the check is still running
        review.set_draft(p, "c001", text="我们再看关系带词。")
    return orig_check(text, *a, **kw)
tf.check_text = check_text_and_teacher_types
r = wf.run_transcript_fix(cfg, "v", once=True)
tf.check_text = orig_check
print("only", r["only"], "checked", r["checked"])
print("c000:", cur(p, "c000")[1])
rec, c = cur(p, "c001")
print("c001:", c, "| suspect:", rec.get("suspect"))
print("button grey:", tf.textfix_used(p), "(c001 was never corrected: 带词 still there)")
