"""Repro: after the one-time use, 撤销删除 (restore) a sentence that was deleted before the run -> the greyed
「一键全部文字校正」 button lights up again, although no new material was added."""
import sys
import os
VT_ROOT = os.environ.get("VT_ROOT", "/home/user/literate-enigma")  # repo checkout to test (for committed HEAD: git archive HEAD | tar -x -C <dir>)
sys.path.insert(0, VT_ROOT + "/research/文字校正/随机操作")
import h
from voicetwin import workflows as wf
from voicetwin.data import review
cfg, project = h.voice(["这个借词后面要接宾语。", "这是一个定语从剧。", "关系带词指代先行词。"], name="v")
review.delete_clip(project, "c002")
wf.run_transcript_fix(cfg, "v", once=True)
print("after one-time use -> used/grey:", wf.textfix_used(cfg, "v"))
review.restore_clip(project, "c002")
print("after 撤销删除 of c002 -> used/grey:", wf.textfix_used(cfg, "v"), "(teacher's rule: once per batch; no new material added)")
