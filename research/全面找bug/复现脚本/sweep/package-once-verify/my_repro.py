"""Independent repro: 一键全部文字校正 (once=True) and clips whose speech recognition has not finished yet.

Usage: VT_ROOT=<checkout> python my_repro.py
Scenarios:
  A  main: batch1 corrected -> 2 new clips sliced with empty text (prepare.py shape: text "", lang "", keep True)
     -> button state? click if lit -> ASR fills text -> button must light again and correct both
  B  partial ASR (prepare saves manifest every 20 clips): 1 of 2 new clips has text -> click -> other one finishes
     -> button must light again and correct the second
  C  whitespace-only text from ASR before recognition (text "  ")
  D  corrupted textfix_used.json while untranscribed clips exist (record rebuilt from all ids)
"""
import os
import sys

VT_ROOT = os.environ["VT_ROOT"]
sys.path.insert(0, VT_ROOT + "/research/文字校正/随机操作")
import h  # noqa: E402  (adds VT_ROOT and VT_ROOT/tests to sys.path)
from voicetwin import workflows as wf  # noqa: E402

assert wf.__file__.startswith(VT_ROOT), wf.__file__
print("testing code at", os.path.dirname(wf.__file__))


def new_clip(cid, text=""):
    return {"id": cid, "path": f"clips/{cid}.wav", "text": text, "lang": "", "duration": 3.0, "keep": True,
            "split": "train", "drop_reason": "", "source": "s2"}


def click(cfg, name):
    try:
        r = wf.run_transcript_fix(cfg, name, once=True)
        return f"ran (only={r.get('only')}, fixes={r.get('fixes')}, adopted={(r.get('adopted') or {}).get('changes')})"
    except ValueError as e:
        return "REFUSED: " + str(e)[:40]


def asr_finish(project, texts):
    recs = project.load_manifest()
    for x in recs:
        if x["id"] in texts:
            x.update(text=texts[x["id"]], lang="zh", asr_done=True)
    project.save_manifest(recs)


def lit(cfg, name):
    return "LIT" if not wf.textfix_used(cfg, name) else "grey"


NEW = {"n000": "这里用的是借词短语。", "n001": "这是一个定语从剧。"}
BATCH1 = ["接下来我们学习一下关系代词。", "这是一个借词短语。"]
results = {}

# ---------- A
cfg, project = h.voice(BATCH1, name="a")
print("\n[A] batch1 click:", click(cfg, "a"), "| button:", lit(cfg, "a"))
recs = project.load_manifest() + [new_clip("n000"), new_clip("n001")]
project.save_manifest(recs)
st = lit(cfg, "a")
print("[A] new clips sliced, ASR not done -> button:", st)
if st == "LIT":
    print("[A] teacher clicks while ASR pending:", click(cfg, "a"))
asr_finish(project, NEW)
st2 = lit(cfg, "a")
print("[A] ASR finished -> button:", st2, "(expected LIT)")
print("[A] teacher clicks:", click(cfg, "a"))
a_txt = {rid: h.cur(project, rid)[1] for rid in NEW}
print("[A] texts:", a_txt)
results["A"] = st == "grey" and st2 == "LIT" and "从句" in a_txt["n001"] and "借词短语" not in a_txt["n000"]

# ---------- B
cfg, project = h.voice(BATCH1, name="b")
click(cfg, "b")
project.save_manifest(project.load_manifest() + [new_clip("n000", NEW["n000"]), new_clip("n001")])
print("\n[B] 1 of 2 recognized -> button:", lit(cfg, "b"), "| click:", click(cfg, "b"), "| after:", lit(cfg, "b"))
asr_finish(project, {"n001": NEW["n001"]})
st = lit(cfg, "b")
print("[B] second recognized -> button:", st, "| click:", click(cfg, "b"))
b_txt = {rid: h.cur(project, rid)[1] for rid in NEW}
print("[B] texts:", b_txt)
results["B"] = st == "LIT" and "从句" in b_txt["n001"]

# ---------- C
cfg, project = h.voice(BATCH1, name="c")
click(cfg, "c")
project.save_manifest(project.load_manifest() + [new_clip("n000", "  "), new_clip("n001", "　")])
st = lit(cfg, "c")
print("\n[C] whitespace-only text -> button:", st, "(expected grey)")
results["C"] = st == "grey"

# ---------- D
cfg, project = h.voice(BATCH1, name="d")
click(cfg, "d")
project.save_manifest(project.load_manifest() + [new_clip("n000"), new_clip("n001")])
used = os.path.join(str(project.root), "textfix_used.json")
with open(used, "w", encoding="utf-8") as f:
    f.write("{bad json")
print("\n[D] corrupt record + 2 unrecognized clips -> button:", lit(cfg, "d"))
asr_finish(project, NEW)
st = lit(cfg, "d")
print("[D] ASR finished -> button:", st, "| click:", click(cfg, "d"))
d_txt = {rid: h.cur(project, rid)[1] for rid in NEW}
print("[D] texts:", d_txt)
results["D"] = st == "LIT" and "从句" in d_txt["n001"]

print("\nRESULTS (True = behaves as documented):", results)
