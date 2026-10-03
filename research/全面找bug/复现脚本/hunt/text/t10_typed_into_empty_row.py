"""A clip where recognition gave no text (text == ""): the table tells the teacher to double-click 「文字」 and type the
sentence herself. Because the original text is empty, orig_text is never recorded, so _changed_chars() sees no
teacher change and the one-click 'corrects' the characters she typed (invariant 2)."""
from h import *
cfg, p = voice(["今天我们讲定语从句。", ""], extra={"c001": {"keep": False, "drop_reason": "没有识别出文字", "asr_done": True}})
typed = "这里的借词和艾子都是我自己打的字。"
review.set_draft(p, "c001", text=typed)          # double-click 「文字」 and type the sentence
review.set_draft(p, "c001", keep=True)           # 「要用」
for saved in (False, True):
    import shutil
    d2 = Path(tempfile.mkdtemp()); c2 = make_cfg(d2 / "ws"); p2 = wf.Project(c2, "v"); shutil.copytree(p.root, p2.root)
    if saved: review.save_rows(p2)
    rec, c = cur(p2, "c001")
    print(("saved" if saved else "unsaved"), "| before click:", c, "| orig_text:", rec.get("orig_text"))
    wf.run_transcript_fix(c2, "v", once=True)
    rec, c = cur(p2, "c001")
    print("        after click: ", c, "  (expected unchanged:", typed, ")")
    shutil.rmtree(d2, ignore_errors=True)
