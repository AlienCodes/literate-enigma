"""Repro: 一键全部文字校正 'one use per batch' marks clips whose ASR has not finished yet as used.
After the teacher resumes 开始准备素材 and ASR fills in their text, the button stays grey and those
sentences are never corrected -- contradicting '以后加了新的素材、识别完，按钮会再亮起来，只改新加的句子'."""
import sys
import os
VT_ROOT = os.environ.get("VT_ROOT", "/home/user/literate-enigma")  # repo checkout to test (for committed HEAD: git archive HEAD | tar -x -C <dir>)
sys.path.insert(0, VT_ROOT + "/research/文字校正/随机操作")
import h
from voicetwin import workflows as wf
from voicetwin.data import transcript_fix as tf

cfg, project = h.voice(["接下来我们学习一下关系代词。", "这是一个借词短语。"], name="v")
r = wf.run_transcript_fix(cfg, "v", once=True)
print("batch 1: fixes", r.get("fixes"), "only", r.get("only"), "-> used:", wf.textfix_used(cfg, "v"))

# teacher adds a new video; 开始准备素材 slices it (manifest saved) but ASR is stopped / fails before finishing
recs = project.load_manifest()
recs += [{"id": "n000", "path": "clips/n000.wav", "text": "", "lang": "zh", "duration": 3.0, "keep": True, "split": "train"},
         {"id": "n001", "path": "clips/n001.wav", "text": "", "lang": "zh", "duration": 3.0, "keep": True, "split": "train"}]
project.save_manifest(recs)
print("after slicing new video, ASR not done -> button grey?", wf.textfix_used(cfg, "v"), "(False = button lit)")
r = wf.run_transcript_fix(cfg, "v", once=True)
print("teacher clicks it now: only", r.get("only"), "fixes", r.get("fixes"))

# teacher clicks 开始准备素材 again; ASR finishes the new clips (prepare.py line ~424 sets text + asr_done)
recs = project.load_manifest()
for x in recs:
    if x["id"] == "n000":
        x.update(text="这里用的是借词短语。", asr_done=True)
    if x["id"] == "n001":
        x.update(text="这是一个定语从剧。", asr_done=True)
project.save_manifest(recs)
used = wf.textfix_used(cfg, "v")
print("after ASR finished the new clips -> button grey?", used, "(expected False: '识别完，按钮会再亮起来')")
try:
    wf.run_transcript_fix(cfg, "v", once=True)
    print("ran")
except ValueError as e:
    print("click refused:", str(e)[:60])
for rid in ("n000", "n001"):
    print(rid, h.cur(project, rid)[1])
