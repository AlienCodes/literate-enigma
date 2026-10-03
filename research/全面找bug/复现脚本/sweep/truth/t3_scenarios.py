import sys, tempfile
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A

def mk(texts, name="v", extra=None):
    d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
    project = wf.Project(cfg, name).ensure()
    recs = [{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True,
             "split": "train"} for i, t in enumerate(texts)]
    for i, kv in (extra or {}).items():
        recs[i].update(kv)
    project.save_manifest(recs)
    return cfg, project

print("=== (b) 还没识别出文字：按钮 / 说明 ===")
cfg, p = mk(["", "", ""])
ui = A.WebUI(cfg)
print("btn interactive:", ui.textfix_btn("v")["interactive"])
print("info:", ui.textfix_info("v"))
print("ever used:", wf.textfix_ever_used(cfg, "v"))

print("=== (b2) 全部删除了 ===")
cfg, p = mk(["我们先来看艾子引导的定语从句。"], extra={0: {"deleted": True, "keep": False}})
ui = A.WebUI(cfg)
print("btn interactive:", ui.textfix_btn("v")["interactive"])
print("info:", ui.textfix_info("v"))

print("=== (c) 第二批素材：结果消息 ===")
cfg, p = mk(["我们先来看艾子引导的定语从剧。", "关系代词that不能和借词一起提前。", "这个句子完全没有错。"])
ui = A.WebUI(cfg)
outs = list(ui.do_textfix("v"))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("first:", last["proof_md"].splitlines()[0])
recs = p.load_manifest()
recs.append({"id": "n1", "path": "clips/n1.wav", "text": "这里的借词后面要接宾语。", "lang": "zh", "duration": 3.0, "keep": True, "split": "train"})
p.save_manifest(recs)
print("btn after new material:", ui.textfix_btn("v")["interactive"])
print("info after new material:", ui.textfix_info("v"))
outs = list(ui.do_textfix("v"))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("second md:\n", last["proof_md"])
print("clips_count:\n", last["clips_count"])

print("=== (d) 用过以后上传母本 ===")
f = Path(tempfile.mkdtemp()) / "新讲稿.txt"; f.write_text("今天讲定语从句。", encoding="utf-8")
outs = list(ui.do_textfix("v", [str(f)]))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("proof_bar has once msg:", "只能用一次" in str(last["proof_bar"]))
print("saved uploads:", wf.transcript_info(cfg, "v"))
