"""Simulate an install without pypinyin / jieba / jieba_fast and run the web button's backend (once=True)."""
import os, sys, json
VT_ROOT = os.environ["VT_ROOT"]
BLOCK = os.environ.get("BLOCK", "1") == "1"
if BLOCK:
    for m in ("pypinyin", "jieba", "jieba_fast"):
        sys.modules[m] = None  # import -> ImportError, like not installed
sys.path.insert(0, VT_ROOT + "/research/文字校正/随机操作")
import h  # inserts VT_ROOT and VT_ROOT/tests
from voicetwin import workflows as wf
from voicetwin.data import transcript_fix as tf, lexicon_fix as lf
import voicetwin
print("voicetwin from", voicetwin.__file__)
print("has_pinyin", tf.has_pinyin(), "has_jieba", lf.has_jieba())
cfg, project = h.voice(["我们来看这个借词短语。", "这是一个定语从剧，关系带词是which。"], name="v")
print("used before:", wf.textfix_used(cfg, "v"))
try:
    r = wf.run_transcript_fix(cfg, "v", once=True)
    print("RESULT fixes", r.get("fixes"), "adopted", (r.get("adopted") or {}).get("changes"),
          "pinyin", r.get("pinyin"), "jieba", r.get("jieba"))
except ValueError as e:
    print("REFUSED (ValueError):", e)
print("used after (button grey):", wf.textfix_used(cfg, "v"))
for rid in ("c000", "c001"):
    print(rid, h.cur(project, rid)[1])
used_file = project.root / tf.USED_FILE if hasattr(project, "root") else None
print("textfix_used.json exists:", used_file.exists() if used_file else "?")
