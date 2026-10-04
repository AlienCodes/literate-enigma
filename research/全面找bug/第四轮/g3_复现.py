"""第四轮找 bug，g3 组（校对表的数据）：7 条一起复现（只用数据层，不联网、不用录音）。
用法（仓库根目录）：PYTHONPATH=. python research/全面找bug/第四轮/g3_复现.py <临时目录>
每条最后写 BUG（问题还在）或 ok（修好了）。修以前 7 条全是 BUG，修以后全是 ok（输出见 g3.md）。"""
import json
import os
import sys
import tempfile
import threading
import unittest.mock as um
from pathlib import Path

sys.path.insert(0, os.environ.get("PYTHONPATH", "."))
sys.path.insert(0, str(Path(os.environ.get("PYTHONPATH", ".")) / "tests"))
from conftest import make_cfg  # noqa: E402

from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review as R  # noqa: E402
from voicetwin.utils import atomic  # noqa: E402

base = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp())


def voice(name, rows):
    cfg = make_cfg(base / name)
    p = wf.Project(cfg, "v").ensure()
    p.save_manifest([dict({"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "duration": 3.0, "keep": True,
                           "split": "train", "lang": "zh"}, **r) for i, r in enumerate(rows)])
    return cfg, p


# ---- review#1：草稿里的「保留」是旧的副本
cfg, p = voice("r1", [{"text": "", "keep": False, "lang": "", "drop_reason": "没有文字"}])
R.set_draft(p, "c000", text="这是老师自己打的一句话。")
print("r1 draft:", R.load_draft(p))
recs = p.load_manifest()  # 再点一次「开始准备素材」：识别出文字、过滤以后 keep=True
recs[0].update(text="这是识别出来的一句话。", lang="zh", keep=True, drop_reason="", asr_done=True)
p.save_manifest(recs)
R.prune_draft(p)
res = R.save_rows(p)
r = p.load_manifest()[0]
print("r1 save changed:", res["changed"], "| keep =", r["keep"], "manual_keep =", r.get("manual_keep"),
      "->", "BUG" if r["keep"] is False else "ok")

# 反方向：草稿里抄的是 keep=True，程序后来把这条判成不能用
cfg, p = voice("r1b", [{"text": "第一句话。"}])
R.set_draft(p, "c000", text="第一句话改了。")
recs = p.load_manifest()
recs[0].update(keep=False, drop_reason="声音不像本人")
p.save_manifest(recs)
R.save_rows(p)
r = p.load_manifest()[0]
print("r1b keep =", r["keep"], "manual_keep =", r.get("manual_keep"), "->", "BUG" if r["keep"] else "ok")

# ---- review#2：写文件从来不 fsync
cfg, p = voice("r2", [{"text": "一句话。"}])
calls = []
real_fsync = os.fsync
with um.patch.object(os, "fsync", lambda fd: (calls.append(fd), real_fsync(fd))):
    R.set_draft(p, "c000", text="一句话改了。")
    R.save_rows(p)
print("r2 fsync calls during set_draft + save_rows:", len(calls), "->", "BUG" if not calls else "ok")
# 断电后 manifest 是空的：「开始准备素材」把 transcripts.csv 也冲成空的（最后一份文字没了）
p.export_csv(p.load_manifest())
p.manifest_path.write_bytes(b"")
p.export_csv(p.load_manifest())
left = p.csv_path.read_text(encoding="utf-8-sig").count("\n") - 1
backups = [x.name for x in p.root.iterdir() if "transcripts" in x.name and "备份" in x.name]
print("r2 csv rows after exporting an empty manifest:", left, "| backups:", backups,
      "->", "BUG" if left == 0 and not backups else "ok")

# ---- review#3：撤销最后一条修改时删不掉草稿文件（Windows 上别的线程正读着）
cfg, p = voice("r3", [{"text": "首先我们看一个最简单的例子。"}])
R.set_draft(p, "c000", text="首先我们看一个最难的例子。")
real_unlink = Path.unlink
fails = {"n": 1}


def locked_unlink(self, *a, **kw):
    if self.name == R.DRAFT_FILE and fails["n"] > 0:
        fails["n"] -= 1
        raise PermissionError(32, "另一个程序正在使用此文件，进程无法访问。")
    return real_unlink(self, *a, **kw)


with um.patch.object(Path, "unlink", locked_unlink):
    n = R.discard_draft(p, "c000")
print("r3 discard returned", n, "| draft after revert:", R.load_draft(p), "->",
      "BUG" if R.load_draft(p) else "ok")

# ---- review#4：v18.2~v18.4 的确认记录不升级，只改语言照样能训练
cfg, p = voice("r4", [{"text": "Next, let's look at the 定语 clause example."}, {"text": "第二句。"}])
recs = p.load_manifest()
R.confirm_path(p).write_text(json.dumps({"time": "2026-09-30 10:00:00", "signature": R.material_signature(recs, 1),
                                         "counts": R.material_counts(recs)}), encoding="utf-8")
print("r4 blocker after upgrade:", repr(wf.training_blocker(p)))
R.load_confirmed(p)  # 网页打开校对表
R.set_draft(p, "c000", lang="en")
R.save_rows(p)
b = wf.training_blocker(p)
print("r4 blocker after a language-only change:", repr(b[:30]), "->", "BUG" if not b else "ok")

# ---- review#5：替换被表格的整理改回去了，还说换了 N 处、冲掉上一次的撤销记录
cfg, p = voice("r5", [{"text": "这里的 as,意思是正如。"}, {"text": "Next, let's look at it, as you see."},
                      {"text": "我们先来看艾子的用法。"}])
R.replace_matches(p, "艾子", "as")
res = R.replace_matches(p, ",", "，")
print("r5 replace result:", {k: res[k] for k in ("count", "rows")}, "| texts:",
      [R.current_values(r, R.load_draft(p).get(r["id"]))["text"] for r in p.load_manifest()[:2]])
u = R.undo_replace(p)
print("r5 undo of the real replace:", u, "->", "BUG" if res["count"] or not u["rows"] else "ok")

# ---- review#6：撤销替换把老师后来选的语言改回去
cfg, p = voice("r6", [{"text": "Next, let's look at a slightly more complex example.", "lang": "en"}])
R.replace_matches(p, "slightly", "much")
R.set_draft(p, "c000", lang="zh")
u = R.undo_replace(p)
v = R.current_values(p.load_manifest()[0], R.load_draft(p).get("c000"))
print("r6 undo:", u, "| values:", v, "->", "BUG" if v["lang"] == "en" else "ok")

# ---- appB#3：确认还在跑的时候做的「全部替换」，撤销记录被确认删掉
cfg, p = voice("r7", [{"text": "我们先来看借词后面接宾语的情况。"}, {"text": "我们再看一个例子。"}])
real_apply = wf.apply_review


def slow_apply(cfg_, voice_, read_csv=True):
    R.replace_matches(p, "我们", "咱们")  # 老师在确认还没做完时点了「全部替换」
    return {}


with um.patch.object(wf, "apply_review", slow_apply):
    out = wf.review_confirm(cfg, "v")
print("r7 confirmed:", out["confirmed"], "| has undo after confirm:", R.has_undo(p), "->",
      "BUG" if not R.has_undo(p) else "ok")
