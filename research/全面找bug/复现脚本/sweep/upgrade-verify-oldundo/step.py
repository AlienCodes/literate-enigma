"""One step of the upgrade scenario, run with whichever code tree SRC points to.

usage: python step.py <SRC> <WS> <action> [row]
  build      : prepare a voice with SRC code, give rows ASR-like text + a proofcheck-style suspect (v18.4 format)
  undo_saved : click 采用, 保存修改, click red button (undo), 保存修改     (row index, default 0)
  undo_draft : click 采用, click red button (undo) without saving in between, then 保存修改
  show       : print record + what the UI shows for that row
  oneclick   : run 一键全部文字校正 (once=True, current code only) and print resulting text of every row
"""
import json
import sys
from pathlib import Path

SRC, WS, ACT = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
ROW = int(sys.argv[4]) if len(sys.argv) > 4 else 0
sys.path.insert(0, SRC)
sys.path.insert(0, SRC + "/tests")
import voicetwin  # noqa: E402

assert str(Path(voicetwin.__file__).resolve()).startswith(str(Path(SRC).resolve())), voicetwin.__file__
from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review  # noqa: E402

V = "我的声音"
cfg = make_cfg(WS)
print(f"[{ACT}] code version", voicetwin.__version__)

# (ASR text, wrong, right)  -- one row per independent scenario
ROWS = [
    ("这个句子里的壮与从剧放在据首。", "壮与从剧", "状语从句"),   # 0: undo after save (v18.4)
    ("我们来看一下这个现行词的用法。", "现行词", "先行词"),       # 1: undo after save (v18.5 control)
    ("这是一个非限定性定语从剧的例子。", "从剧", "从句"),          # 2: untouched, adopt_all should adopt
    ("他说这里要用关系带词来连接。", "关系带词", "关系代词"),      # 3: undo without saving in between (v18.4)
]


def sus(text, wrong, right):
    s = text.index(wrong)
    return {"spans": [[s, s + len(wrong)]], "alt": text.replace(wrong, right, 1),
            "reasons": [f"另一个识别引擎听成了「{right}」"], "score": 0.62}


if ACT == "build":
    lec = WS.parent / "lectures"
    make_lecture(lec / "第1课.wav", repeats=1)
    wf.run_prepare(cfg, V, [str(lec)])
    p = wf.open_project(cfg, V, must_exist=True)
    recs = p.load_manifest()
    for i, r in enumerate(recs):
        if i < len(ROWS):
            t, w, rt = ROWS[i]
            r.update(text=t, lang="zh", keep=True, drop_reason="", suspect=sus(t, w, rt))
        else:
            r["keep"] = False
            r["drop_reason"] = "测试不用"
    p.save_manifest(recs)
    p.export_csv(recs)
    print("rows:", len(recs))
    sys.exit(0)

p = wf.open_project(cfg, V, must_exist=True)
rid = p.load_manifest()[ROW]["id"]


def rec():
    return {x["id"]: x for x in p.load_manifest()}[rid]


if ACT == "undo_saved":
    review.adopt_suggestion(p, rid)
    wf.review_save(cfg, V, [rid])
    print("after adopt+save:", rec()["text"])
    review.unadopt_suggestion(p, rid)
    wf.review_save(cfg, V, [rid])
    print("after undo+save :", rec()["text"])
elif ACT == "undo_draft":
    review.adopt_suggestion(p, rid)
    review.unadopt_suggestion(p, rid)
    wf.review_save(cfg, V, [rid])
    print("after adopt,undo,save:", rec()["text"], "| draft entries:", len(review.load_draft(p)))
elif ACT == "show":
    r = rec()
    print(json.dumps({k: r.get(k) for k in ("text", "orig_text", "text_edited", "suspect")}, ensure_ascii=False))
    a = review.analyze(r, review.current_values(r, review.load_draft(p).get(rid))["text"])
    print("UI: edits(blue 采用 button)=", a["edits"], "undo(red)=", a["undo"])
    rej = Path(p.root) / "review_rejected.json"
    print("review_rejected.json:", rej.read_text(encoding="utf-8") if rej.exists() else "(none)")
elif ACT == "oneclick":
    res = wf.run_transcript_fix(cfg, V, once=True)
    print("one-click result: fixes", res.get("fixes"), "adopted", res.get("adopted"), "only", res.get("only"))
    draft = review.load_draft(p)
    for i, r in enumerate(p.load_manifest()[:len(ROWS)]):
        print(f"  row {i}: saved={r['text']}  shown={review.current_values(r, draft.get(r['id']))['text']}")
