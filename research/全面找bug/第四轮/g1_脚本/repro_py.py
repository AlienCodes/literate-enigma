"""第四轮 g1：在 Python 层面复现网页的几个问题（不需要浏览器）。用法：python repro_py.py <仓库> <临时目录>"""
import json
import os
import shutil
import sys
from pathlib import Path

REPO, TMP = sys.argv[1], Path(sys.argv[2])
sys.path.insert(0, REPO + "/tests")
sys.path.insert(0, REPO)
from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402

TMP.mkdir(parents=True, exist_ok=True)
lect = TMP / "lect"
make_lecture(lect / "第1课.wav")
cfg = make_cfg(TMP / "ws")
wf.run_prepare(cfg, "v", [str(lect)])
ui = A.WebUI(cfg)
project = wf.Project(cfg, "v")


def act(action, cid, **extra):
    payload = json.dumps(dict(action=action, id=cid, no="3", seq="t", **extra), ensure_ascii=False)
    return A._safe("校对表", 3, 0)(ui.do_clip_action)("v", payload, False)


recs = project.load_manifest()
for r in recs:
    r.pop("suspect", None)
T = "我们今天学习定语从句"
recs[2].update(text=T, keep=True, manual_keep=True, suspect={"spans": [[6, 7]], "alt": "我们今天学习状语从句",
                                                            "reasons": ["测试"], "score": 0.7})
T2 = "我们我们来看看第二个第二个例子。"
recs[3].update(text=T2, keep=True, manual_keep=True, suspect={"spans": [[0, 2], [9, 12]], "alt": "我们来看看第二个例子。",
                                                             "reasons": ["测试"], "score": 0.7})
project.save_manifest(recs)
c2, c3 = recs[2]["id"], recs[3]["id"]

print("== appA#1 编辑框开着时采用了建议，再按回车")
act("adopt", c2)
msg, _, _ = act("edit", c2, text=T + "吧", orig=T)  # 编辑框是在采用之前打开的：orig 是旧的句子
print("草稿：", review.load_draft(project).get(c2, {}).get("text"))
print("撤销记录：", review.load_rejected(project).get(c2))
print("提示：", msg[:120].replace("\n", " "))

print("== appA#2/appB#2/appC#1 被拒绝的采用")
act("edit", c3, text="我们我们来看第二个第二个例子。")
msg, cnt, tbl = act("adopt", c3)
print("提示：", msg[:160].replace("\n", " "))
print("表格重画了吗：", not (isinstance(tbl, dict) and tbl.get("__type__") == "update"))

print("== appA#3 下载失败时文件框")
out = A._safe("下载改好的文字", 2, 0)(ui.do_download_text)("v")
print("第 1 次：", out[1] if not isinstance(out[1], dict) else out[1].get("value"))
d = project.root / "review_draft.json"
saved = d.read_bytes() if d.exists() else b"{}"
if d.exists():
    d.unlink()
d.mkdir()
out = A._safe("下载改好的文字", 2, 0)(ui.do_download_text)("v")
print("第 2 次（草稿读不了）的文件框：", out[1])
d.rmdir()
d.write_bytes(saved)

print("== appB#5 准备完以后的提示")
infos = []
A._info = lambda m: infos.append(m)  # noqa
print("训练前的拦截：", wf.training_blocker_for(cfg, "v")[:60])
print("== appB#7 「每句的平均」")
from types import SimpleNamespace  # noqa: E402
res = SimpleNamespace(overall_pct=94.3, segments=[{"pct": 80.0, "duration": 1}] * 10 + [{"pct": 97.0, "duration": 9}] * 10)
print([x for x in A._gen_summary_md(res).splitlines() if "像你本人" in x][:2])

print("== appC#2 delete_cache")
import inspect  # noqa: E402
src = inspect.getsource(A.WebUI.build)
print([l.strip() for l in src.splitlines() if "delete_cache" in l])

print("== appB#1 uploads 被删")
up = TMP / "upl"
up.mkdir(exist_ok=True)
make_lecture(up / "第2课.wav", repeats=1, seed=3)
A._prepare_job(cfg, "v", [str(up / "第2课.wav")], "", {})
dst = project.root / "uploads" / "第2课.wav"
print("uploads 里：", dst.exists())
(up / "第2课.wav").unlink()  # gradio 的缓存没了
try:
    A._prepare_job(cfg, "v", [str(up / "第2课.wav")], "", {})
    print("第二次准备成功")
except Exception as exc:
    print("第二次准备出错：", type(exc).__name__)
print("uploads 里还有吗：", dst.exists())
