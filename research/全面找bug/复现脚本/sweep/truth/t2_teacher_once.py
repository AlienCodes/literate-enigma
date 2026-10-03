"""WHATS_NEW 18.5 说「1008 句里还有 138 处……点一次「一键全部文字校正」就会全部改好」：用网页按钮真正走的路径
（WebUI.do_textfix → run_transcript_fix(once=True, adopt_all=True)）在老师的原文上验证，并核对结果消息里的数字。"""
import csv, difflib, sys, tempfile, re
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A
D = Path("/home/user/literate-enigma/research/文字校正/老师的母本")
ORIG = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
CLEAN = {r["id"]: r["text"] for r in csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig"))}
FIXES = [ln.rstrip("\n").split("\t") for ln in open(D / "修缮记录.tsv", encoding="utf-8")][1:]
print("columns", list(ORIG[0].keys()))
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
project = wf.Project(cfg, "我的声音").ensure()
recs = []
for r in ORIG:
    rec = {"id": r["id"], "path": f"clips/{r['id']}.wav", "text": r["text"], "lang": "zh", "duration": 3.0,
           "keep": r["keep"] == "1", "split": "train"}
    if r["drop_reason"] == "老师删除":
        rec["deleted"] = True
    recs.append(rec)
project.save_manifest(recs)
ui = A.WebUI(cfg)
outs = list(ui.do_textfix("我的声音"))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print(last["proof_md"])
draft = review.load_draft(project)
exact = need = extra = rows = chunks = 0
wrong = []
for r in ORIG:
    if r["drop_reason"] == "老师删除":
        continue
    cur = draft.get(r["id"], {}).get("text", r["text"])
    want = CLEAN[r["id"]]
    if want != r["text"]:
        need += 1
        exact += cur == want
        if cur != want:
            wrong.append(f"{r['id']}: want {want!r}\n      got  {cur!r}")
    elif cur != r["text"]:
        extra += 1
        wrong.append(f"EXTRA {r['id']}: {r['text']!r} -> {cur!r}")
    if cur != r["text"]:
        rows += 1
        chunks += sum(1 for op in difflib.SequenceMatcher(None, r["text"], cur).get_opcodes() if op[0] != "equal")
print(f"need {need}, exact {exact}, extra rows changed {extra}; rows changed {rows}, diff chunks {chunks}")
print("\n".join(wrong[:20]))
print("button interactive after:", last["tr_btn"].get("interactive"))
