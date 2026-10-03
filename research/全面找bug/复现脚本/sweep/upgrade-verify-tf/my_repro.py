"""Independent repro (current working tree): one-click (once=True) and rows it skipped.

A: a clip with no text yet (interrupted recognition) -> one-click -> text arrives -> does the button light up for it?
B: a grey row (keep=False, program judged unusable) with text -> one-click -> teacher turns it on ("use") + saves
   -> is it corrected? does the button light up? Control: once=False would have corrected it.
usage: python my_repro.py <tmpdir>
"""
import json
import sys
from pathlib import Path

REPO = "/home/user/literate-enigma"
sys.path.insert(0, REPO)
sys.path.insert(0, REPO + "/tests")
from conftest import make_cfg  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review, transcript_fix as tf  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402

base = Path(sys.argv[1])


def mk(name, rows):
    cfg = make_cfg(base / name)
    project = wf.Project(cfg, "V").ensure()
    import numpy as np, soundfile as sf
    (project.root / "clips").mkdir(parents=True, exist_ok=True)
    t = np.arange(int(32000 * 3.0)) / 32000
    for r in rows:
        sf.write(str(project.root / "clips" / f"{r['id']}.wav"), (0.2 * np.sin(2 * np.pi * 220 * t)).astype("float32"), 32000)
    project.save_manifest([dict({"path": f"clips/{r['id']}.wav", "lang": "zh", "duration": 3.0, "split": "train"}, **r)
                           for r in rows])
    return cfg, project


def cur(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    return review.current_values(rec, review.load_draft(project).get(rid))["text"]


GREY_T = "接下来我们学习另外一个关系带词，艾子，这个关系带词相对来说比较特殊。"
rows = [
    {"id": "c000", "text": "首先艾子这个关系代词经常出现在非限定性定语从剧中。", "keep": True},
    {"id": "c001", "text": "", "keep": False, "drop_reason": "没有识别出文字"},
    {"id": "c002", "text": GREY_T, "keep": False, "drop_reason": "语速异常（文字可能不对）"},
]
# ---- A + B with once=True (web button)
cfg, project = mk("once", rows)
ui = A.WebUI(cfg)
print("button before:", ui.textfix_btn("V")["interactive"])
outs = list(ui.do_textfix("V"))
summary = [str(o) for o in outs[-1] if isinstance(o, str) and "检查了" in str(o)] if isinstance(outs[-1], tuple) else []
res_md = [x for x in (str(v) for o in outs for v in (o if isinstance(o, tuple) else [o])) if "检查了" in x]
print("summary:", res_md[-1][:200] if res_md else "(not found)")
used = json.loads((project.root / tf.USED_FILE).read_text(encoding="utf-8"))["ids"]
print("used ids:", used)
print("c000 after:", cur(project, "c000"))
print("c002 (grey) after:", cur(project, "c002"))
print("button after:", ui.textfix_btn("V")["interactive"])
# A: recognition finishes for c001
recs = project.load_manifest()
recs[1].update(text="这里的借词后面要接宾语，艾子引导的定语从剧。", keep=True, drop_reason="", asr_done=True)
project.save_manifest(recs)
print("[A] new ids after recognition:", tf.textfix_new_ids(project), "button:", ui.textfix_btn("V")["interactive"])
# B: teacher turns the grey row on and saves (do this before the second one-click so we can see the button state)
msg = ui.do_clip_action("V", json.dumps({"action": "use", "id": "c002", "no": "3"}))[0]
print("[B] use:", str(msg)[:60])
ui.do_save("V")
print("[B] new ids after grey row turned on + saved:", tf.textfix_new_ids(project))
outs = list(ui.do_textfix("V"))
print("[A] c001 after second one-click:", cur(project, "c001"))
print("[B] c002 after second one-click:", cur(project, "c002"))
rec2 = {r["id"]: r for r in project.load_manifest()}["c002"]
print("[B] c002 is training material:", review.is_material(rec2), "| button:", ui.textfix_btn("V")["interactive"])
print("[B] info:", ui.textfix_info("V").split("\n")[0][:80])
try:
    wf.run_transcript_fix(cfg, "V", once=True)
except ValueError as e:
    print("[B] once=True again ->", str(e)[:50])

# ---- Control: same grey row already turned on, once=False (CLI) -> what the one-click would have done
cfg2, project2 = mk("ctrl", [{"id": "c002", "text": GREY_T, "keep": True}])
wf.run_transcript_fix(cfg2, "V", once=False)
print("[control] keep=True row after one-click:", cur(project2, "c002"))
