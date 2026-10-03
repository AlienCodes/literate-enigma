"""Build a workspace with an OLD VoiceTwin version (v18.2 / v18.3 / v18.4), simulating what the teacher did.

usage: python build_old.py <old_src_dir> <workspace_dir> <scenario: clean|mid>
"""
import json
import sys
from pathlib import Path

SRC, WS, SCEN = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, SRC)
sys.path.insert(0, SRC + "/tests")
import voicetwin  # noqa: E402

assert str(Path(voicetwin.__file__).resolve()).startswith(str(Path(SRC).resolve())), voicetwin.__file__
from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review, proofcheck  # noqa: E402

VER = voicetwin.__version__
print("old version", VER)
lec = WS.parent / "lectures"
if not (lec / "第1课.wav").exists():
    make_lecture(lec / "第1课.wav", repeats=2)
cfg = make_cfg(WS)
V = "我的声音"
wf.run_prepare(cfg, V, [str(lec)])
project = wf.open_project(cfg, V, must_exist=True)
recs = project.load_manifest()
print("clips", len(recs), [r.get("keep") for r in recs])

# teacher-domain ASR output (with the typical recognition errors)
T = [
    "接下来我们就学习一下另外一个关系带词，艾子,这个关系带词相对来说比较特殊。",  # 0 old suspect, adopted + saved
    "首先，艾子这个关系代词，它最经常出现在非限定性定语从剧中。",  # 1 old suspect, adopted, NOT saved
    "在定语从句中，艾子主要被翻译为正如。",  # 2 hand-edited + saved
    "大多数情况下，艾子所代替的一般情况下就是整个句子中的主剧。",  # 3 old suspect dismissed
    "其次，这个关系代词最常见的使用方式并不是代指某个现行词。",  # 4 deleted
    "而是代指一整个句子，也就是说艾子所代替的一般是整件事情。",  # 5 hand-edited draft (unsaved in mid)
    "我们先来看借词后面接宾语的情况。",  # 6 find/replace 借词->介词 (v18.3+)
    "这个句子里的壮与从剧放在据首。",  # 7 old suspect untouched
    "例如下面这个句子，艾子引导的非限定性定语从句。",  # 8 old suspect alt; adopted then unadopted (draft==saved)
    "所以说这个现行词是整个主句。",  # 9 untouched, no suspect
]
for i, r in enumerate(recs):
    if i < len(T):
        r["text"] = T[i]
        r["lang"] = "zh"
        r["keep"] = True
        r.pop("drop_reason", None)
        r["drop_reason"] = ""
ids = [r["id"] for r in recs]


def sus(text, wrong, right, reason="另一个识别引擎听成了「{r}」"):
    s = text.index(wrong)
    return {"spans": [[s, s + len(wrong)]], "alt": text.replace(wrong, right, 1),
            "reasons": [reason.format(r=right)], "score": 0.62}


recs[0]["suspect"] = sus(T[0], "关系带词", "关系代词")
recs[1]["suspect"] = sus(T[1], "从剧", "从句")
recs[3]["suspect"] = sus(T[3], "艾子", "as")
recs[7]["suspect"] = sus(T[7], "壮与从剧", "状语从句")
recs[8]["suspect"] = sus(T[8], "艾子", "as")
project.save_manifest(recs)
project.export_csv(recs)

# teacher actions with the OLD code
review.adopt_suggestion(project, ids[0])
review.save_rows(project, [ids[0]])
review.adopt_suggestion(project, ids[1])
if SCEN == "clean":
    review.save_rows(project, [ids[1]])
review.set_draft(project, ids[2], text=T[2].replace("艾子", "as"))
review.save_rows(project, [ids[2]])
proofcheck.dismiss_suspect(project, ids[3])
wf.review_delete(cfg, V, ids[4])
review.set_draft(project, ids[5], text=T[5].replace("整件事情", "整件事儿"))
if SCEN == "clean":
    review.save_rows(project, [ids[5]])
if hasattr(review, "replace_matches"):
    review.replace_matches(project, "借词", "介词")
    if SCEN == "clean":
        review.save_rows(project, [ids[6]])
    else:
        review.save_find(project, "艾子", True, index=1, fresh=True)
review.adopt_suggestion(project, ids[8])
review.unadopt_suggestion(project, ids[8])

if SCEN == "clean" and hasattr(wf, "review_confirm"):
    res = wf.review_confirm(cfg, V)
    print("confirmed", res.get("confirmed"), res.get("counts"))
else:
    # confirmed earlier, then kept working (drafts pending)
    pass

# snapshot of what the OLD UI showed per row
out = {}
draft = review.load_draft(project)
for r in project.load_manifest():
    vals = review.current_values(r, draft.get(r["id"]))
    a = review.analyze(r, vals["text"])
    out[r["id"]] = {"text": vals["text"], "dirty": review.is_dirty(r, draft.get(r["id"])),
                    "red": a["red"], "edits": a["edits"], "undo": a["undo"], "adopted": a["adopted"],
                    "active": a["active"], "deleted": bool(r.get("deleted"))}
old_block = ""
if hasattr(wf, "training_blocker"):
    old_block = wf.training_blocker(project)
snap = {"version": VER, "rows": out, "unsaved": len(draft), "blocker": old_block,
        "confirmed": review.load_confirmed(project) if hasattr(review, "load_confirmed") else {}, "files": sorted(p.name for p in project.root.iterdir())}
(WS / "old_snapshot.json").write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in snap.items() if k != "rows"}, ensure_ascii=False))
