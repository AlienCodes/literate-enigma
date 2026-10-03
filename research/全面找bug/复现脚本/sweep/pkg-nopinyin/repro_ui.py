"""Web button path (WebUI.do_textfix) with pypinyin / jieba / jieba_fast missing."""
import os, sys, time
VT_ROOT = os.environ["VT_ROOT"]
for m in ("pypinyin", "jieba", "jieba_fast"):
    sys.modules[m] = None
sys.path.insert(0, VT_ROOT + "/research/文字校正/随机操作")
import h
from voicetwin import workflows as wf
from voicetwin.webui import app as A
cfg, project = h.voice(["我们来看这个借词短语。", "这是一个定语从剧，关系带词是which。"], name="v")
ui = A.WebUI(cfg)
O = ui.TEXTFIX_OUT
print("button interactive before:", ui.textfix_btn("v")["interactive"])
outs = list(ui.do_textfix("v"))
last = dict(zip(O, outs[-1]))
def val(x):
    return x.get("value") if isinstance(x, dict) else x
print("proof_bar:", str(val(last.get("proof_bar")))[:300].replace("\n", " "))
print("tr_info:", str(val(last.get("tr_info")))[-400:].replace("\n", " "))
print("tr_btn interactive after:", (last.get("tr_btn") or {}).get("interactive"))
print("used after:", wf.textfix_used(cfg, "v"), "| button now:", ui.textfix_btn("v")["interactive"])
for rid in ("c000", "c001"):
    print(rid, h.cur(project, rid)[1])
