"""Repro: in an install without pypinyin / jieba (install_windows.ps1 mode 2 'venv' installs .[asr,webui,denoise,docx,sv],
none of which pulls pypinyin or jieba), the one-click correction fixes nothing from the corrections table, yet the
one-time use is consumed (button grey forever for this batch) -- only afterwards does the page warn to reinstall with mode 1."""
import sys
import os
VT_ROOT = os.environ.get("VT_ROOT", "/home/user/literate-enigma")  # repo checkout to test (for committed HEAD: git archive HEAD | tar -x -C <dir>)
for m in ("pypinyin", "jieba", "jieba_fast"):
    sys.modules[m] = None   # simulate not installed
sys.path.insert(0, VT_ROOT + "/research/文字校正/随机操作")
import h
from voicetwin import workflows as wf
from voicetwin.data import transcript_fix as tf, lexicon_fix as lf
print("has_pinyin", tf.has_pinyin(), "has_jieba", lf.has_jieba())
cfg, project = h.voice(["我们来看这个借词短语。", "这是一个定语从剧，关系带词是which。"], name="v")
r = wf.run_transcript_fix(cfg, "v", once=True)
print("fixes", r.get("fixes"), "adopted", (r.get("adopted") or {}).get("changes"), "pinyin", r.get("pinyin"), "jieba", r.get("jieba"))
print("used (button grey):", wf.textfix_used(cfg, "v"))
for rid in ("c000", "c001"):
    print(rid, h.cur(project, rid)[1])
