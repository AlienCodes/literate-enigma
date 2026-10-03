"""独立复现：「检查完了：其中 N 条可能有错（已在表格里标红）」和表格里真的标红的行 / 表格上方的数字对不对得上。
全部走真的网页处理函数（WebUI.do_proofcheck / do_clip_action / refresh_clips），第二个识别引擎是假的（不加载模型）。"""
import re, json, logging
from common import *
from voicetwin.webui import app as A

logging.disable(logging.CRITICAL)
A._info = lambda *a, **k: None
COL = A.CLIP_HEADERS.index(A.COL_SUSPECT)


def look(ui, label, last=None):
    count, rows = ui.refresh_clips("v", False, None)
    _, rows_sus = ui.refresh_clips("v", True, None)
    m = re.search(r"\*\*(\d+)\*\* 条可能有错", count)
    out = {
        "message": (last["proof_md"].splitlines()[0] if last else None),
        "header_count": int(m.group(1)) if m else 0,
        "red_rows": [r[1] for r in rows if "vt-red" in str(r[COL]) or "vt-sus" in str(r[COL])],
        "only_sus_rows": [r[1] for r in rows_sus],
    }
    print(f"[{label}]", json.dumps(out, ensure_ascii=False))
    return out


def proof(ui):
    outs = list(ui.do_proofcheck("v", False))
    return dict(zip(ui.PROOF_OUT, outs[-1]))


def msg_count(last):
    m = re.search(r"其中 \*\*(\d+)\*\* 条可能有错", last["proof_md"])
    return int(m.group(1)) if m else 0


texts = ["我们今天讲十个函数", "下面我们来看第二个例子", "那么到底什么是定语从句呢"]
heard = {"c000": "我们今天讲是个函数", "c001": "下面我们来看第二个例子", "c002": "那么到底什么是定语从句呢"}

print("== A. 老师已经把错字改好（没保存），再点自动查找（报告里的 s2c）")
cfg, project = voice(texts)
fake_engine(heard)
review.set_draft(project, "c000", text="我们今天讲四个函数")
ui = A.WebUI(cfg)
last = proof(ui)
o = look(ui, "A", last)
print("   message count =", msg_count(last), "| header =", o["header_count"], "| red rows =", len(o["red_rows"]))

print("== B. 一行查出可能有错以后被程序改成不用（灰色），再点自动查找")
cfg, project = voice(texts)
fake_engine(heard)
ui = A.WebUI(cfg)
last = proof(ui)
look(ui, "B0 after first check", last)
recs = project.load_manifest()
for r in recs:
    if r["id"] == "c000":
        r["keep"] = False
        r["drop_reason"] = "语速异常（文字可能不对）"
project.save_manifest(recs)
last = proof(ui)
o = look(ui, "B1 c000 grey, check again", last)
print("   message count =", msg_count(last), "| header =", o["header_count"], "| red rows =", o["red_rows"],
      "| 只看可能有错的 =", o["only_sus_rows"])

print("== C. 同上，老师在灰色那一行点「✅ 这一条也要用」（还没保存），再点自动查找")
r = ui.do_clip_action("v", json.dumps({"action": "use", "id": "c000", "no": "1"}), False)
print("   action msg:", r[0])
look(ui, "C0 after use (unsaved)")
last = proof(ui)
o = look(ui, "C1 check again", last)
print("   message count =", msg_count(last), "| header =", o["header_count"], "| red rows =", o["red_rows"])
print("   message:", last["proof_md"].splitlines()[0])

print("== D. 删除一行可能有错的（紫色），再点自动查找")
cfg, project = voice(texts)
fake_engine(heard)
ui = A.WebUI(cfg)
proof(ui)
wf.review_delete(cfg, "v", "c000") if hasattr(wf, "review_delete") else review.delete_clip(project, "c000")
last = proof(ui)
o = look(ui, "D1", last)
print("   message count =", msg_count(last), "| header =", o["header_count"], "| red rows =", o["red_rows"],
      "| 只看可能有错的 =", o["only_sus_rows"])
