"""Verify: 撤销刚才的替换 message for a row already reverted back to the pre-replace text."""
import sys, json, re, tempfile, shutil
from pathlib import Path
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A

strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))
TEXTS = ["今天我们来学习定语从句。", "我们先来看一个例子。", "这一句没有那个词。", "最后我们做个练习。"]


def setup(tag):
    d = Path(tempfile.mkdtemp(prefix=tag + "_", dir=HERE))
    cfg = make_cfg(d / "ws")
    p = wf.Project(cfg, "v").ensure()
    p.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh", "duration": 3.0,
                      "keep": True, "split": "train"} for i, t in enumerate(TEXTS)])
    return d, cfg, p, A.WebUI(cfg)


def cur(p, rid):
    rec = {r["id"]: r for r in p.load_manifest()}[rid]
    return review.current_values(rec, review.load_draft(p).get(rid))["text"]


def act(ui, action, cid, **extra):
    payload = json.dumps(dict(action=action, id=cid, no="1", seq="t", **extra), ensure_ascii=False)
    return ui.do_clip_action("v", payload, False)


def show_undo(st):
    s = strip(st)
    i = s.find("撤销")
    print("   undo message:", s[:400])

# Scenario A: replace all, revert one row via ⋯ 选项 → 撤销这一行的修改, then 撤销刚才的替换
d, cfg, p, ui = setup("A")
ui.do_find("v", "我们", True, False)
st, *_ = ui.do_replace_all("v", "我们", "咱们", True, False)
print("A replace:", strip(st)[:120])
msg, *_ = act(ui, "revert", "c000")
print("A revert c000:", strip(msg), "| now:", cur(p, "c000"))
st, *_ = ui.do_undo_replace("v", False)
show_undo(st)
print("   texts after:", [cur(p, f"c{i:03d}") for i in range(4)])
print("   raw undo_replace result would have been ->", "see message")
shutil.rmtree(d)

# Scenario B: replace all, teacher types the original text back by hand (double-click edit)
d, cfg, p, ui = setup("B")
ui.do_replace_all("v", "我们", "咱们", True, False)
act(ui, "edit", "c001", text="我们先来看一个例子。")
print("B edited c001 back by hand:", cur(p, "c001"))
st, *_ = ui.do_undo_replace("v", False)
show_undo(st)
shutil.rmtree(d)

# Scenario C: replace ONE row only, then revert that row, then undo replace -> only row already back
d, cfg, p, ui = setup("C")
ui.do_find("v", "我们", True, False)
st, *_ = ui.do_replace_one("v", "我们", "咱们", True, False)
print("C replace one:", strip(st)[:100], "| c000 now:", cur(p, "c000"))
act(ui, "revert", "c000")
print("C reverted:", cur(p, "c000"))
st, *_ = ui.do_undo_replace("v", False)
show_undo(st)
shutil.rmtree(d)

# Scenario D (control): replace all, edit one row to something different -> kept message is correct
d, cfg, p, ui = setup("D")
ui.do_replace_all("v", "我们", "咱们", True, False)
act(ui, "edit", "c001", text="老师自己又改了。")
st, *_ = ui.do_undo_replace("v", False)
show_undo(st)
shutil.rmtree(d)
