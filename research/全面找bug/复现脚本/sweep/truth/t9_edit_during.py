"""一键校正进行中老师改了一句：这一句这次没处理（下次还能用），结果说明怎么说？按钮呢？"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf
from voicetwin.webui import app as A
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
p = wf.Project(cfg, "v").ensure()
texts = ["我们先来看艾子引导的定语从剧。", "关系代词that不能和借词一起提前。", "这个句子完全没有错。"]
p.save_manifest([{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(texts)])
orig = tf.check_text
state = {"n": 0}
def patched(*a, **k):
    state["n"] += 1
    if state["n"] == 1:  # 检查期间老师在网页上改了第 2 句
        review.set_draft(p, "c1", text="关系代词that不能和介词一起提前到句首。")
    return orig(*a, **k)
tf.check_text = patched
ui = A.WebUI(cfg)
outs = list(ui.do_textfix("v"))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print(last["proof_md"].split("\n\n- 标准库")[0])
print("button interactive after:", last["tr_btn"]["interactive"])
print("tr_info:", last["tr_info"][:120])
