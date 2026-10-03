"""Open an OLD workspace with the CURRENT code (as after upgrading) and walk through the teacher's flow.

usage: python check_new.py <workspace_dir>
Prints PROBLEM lines for anything suspicious.
"""
import json
import sys
from pathlib import Path

REPO = "/home/user/literate-enigma"
sys.path.insert(0, REPO)
sys.path.insert(0, REPO + "/tests")
WS = Path(sys.argv[1])
import voicetwin  # noqa: E402

assert voicetwin.__file__.startswith(REPO), voicetwin.__file__
from conftest import make_cfg  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review, transcript_fix as tf  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402

V = "我的声音"
snap = json.loads((WS / "old_snapshot.json").read_text(encoding="utf-8"))
print("== workspace from", snap["version"], "->", voicetwin.__version__)
cfg = make_cfg(WS)
project = wf.open_project(cfg, V, must_exist=True)
ui = A.WebUI(cfg)
problems = []


def P(msg):
    problems.append(msg)
    print("PROBLEM:", msg)


def state():
    d = review.load_draft(project)
    out = {}
    for r in project.load_manifest():
        vals = review.current_values(r, d.get(r["id"]))
        a = review.analyze(r, vals["text"])
        out[r["id"]] = {"text": vals["text"], "dirty": review.is_dirty(r, d.get(r["id"])), "red": [list(x) for x in a["red"]],
                        "edits": [list(x) for x in a["edits"]], "undo": [list(x) for x in a["undo"]],
                        "adopted": a["adopted"], "active": a["active"], "deleted": bool(r.get("deleted")),
                        "saved": r.get("text")}
    return out


ids = [r["id"] for r in project.load_manifest()]
# 1. what the table shows right after upgrade vs what the old version showed
now = state()
for rid, old in snap["rows"].items():
    new = now[rid]
    for k in ("text", "dirty", "adopted", "active", "deleted"):
        if old[k] != new[k]:
            P(f"after upgrade row {ids.index(rid)} {k}: old={old[k]!r} new={new[k]!r}")
    for k in ("red", "edits", "undo"):
        if [list(x) for x in old[k]] != new[k]:
            P(f"after upgrade row {ids.index(rid)} {k}: old={old[k]!r} new={new[k]!r}")

# 2. page load handlers
outs = ui.on_load()
print("on_load ok; outputs", len(outs))
table = A._clips_table(cfg, V)
print("table rows", len(table))
cnt = A._clips_count_md(cfg, V)
print("count md:", cnt.replace("\n", " | ")[:600])
btn = ui.textfix_btn(V)
print("textfix btn interactive:", btn.get("interactive"))
if btn.get("interactive") is not True:
    P("one-click button not enabled after upgrade for never-corrected material")
info = ui.textfix_info(V)
if "只能用一次" in info.split("\n")[0]:
    P("textfix info says already used after upgrade")
blk = wf.training_blocker(project)
print("training blocker after upgrade:", blk or "(none)")
if (snap["blocker"] or "") != blk:
    P(f"training gate changed by upgrade: old={snap['blocker']!r} new={blk!r}")
print("voice status:", A._voice_status_md(cfg, V)[:300])
print("train plan preview:", ui.train_plan_preview(V, "dummy")[:300].replace("\n", " "))

# 3. undo replace from older version (v18.3+ mid)
if (project.root / review.UNDO_FILE).exists() and any(now[r]["dirty"] for r in now):
    pass  # keep it for later check

# 4. one click
before = state()
outs = list(ui.do_textfix(V))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("textfix done; btn interactive:", last["tr_btn"].get("interactive") if isinstance(last["tr_btn"], dict) else last["tr_btn"])
print("textfix md:", str(last["proof_md"])[:500].replace("\n", " | "))
after = state()
for rid in ids:
    b, a = before[rid], after[rid]
    if b["text"] != a["text"]:
        print(f"  row {ids.index(rid)} changed: {b['text']} -> {a['text']}")
# teacher's decisions that must survive
r = {i: ids[i] for i in range(len(ids))}
if after[r[3]]["text"] != before[r[3]]["text"]:
    P(f"row 3 (teacher clicked 这句没错 in old version) changed by one-click: {before[r[3]]['text']} -> {after[r[3]]['text']}")
if after[r[4]]["text"] != before[r[4]]["text"]:
    P("deleted row changed by one-click")
if "整件事儿" not in after[r[5]]["text"]:
    P(f"teacher's own edit lost on row 5: {after[r[5]]['text']}")
if after[r[8]]["text"] != before[r[8]]["text"]:
    P(f"row 8 (teacher adopted then UNDID the suggestion in old version) changed again by one-click: "
      f"{before[r[8]]['text']} -> {after[r[8]]['text']}")
for i in (0, 1):
    if not after[r[i]]["adopted"] and before[r[i]]["adopted"]:
        P(f"row {i}: adopted suggestion lost its red 'adopted' button after one-click (undo={after[r[i]]['undo']})")
if ui.textfix_btn(V).get("interactive") is not False:
    P("one-click button still enabled after use")

# 5. undo replace from older version still works (mid scenario only)
if (project.root / review.UNDO_FILE).exists():
    res = review.undo_replace(project)
    print("undo replace:", res, "row6:", state()[r[6]]["text"])

# 6. save + confirm + train + generate
msg, cnt_md, tbl = ui.do_save(V)
print("save:", msg[:200].replace("\n", " "))
msg, cnt_md, tbl = ui.do_confirm(V)
print("confirm:", msg[:200].replace("\n", " "))
blk = wf.training_blocker(project)
if blk:
    P(f"training still blocked after save+confirm: {blk}")
try:
    wf._check_material_before_training(project)
    print("train gate ok")
except Exception as exc:  # noqa: BLE001
    P(f"train failed after upgrade: {exc!r}")
try:
    res = wf.run_narrate(cfg, V, "今天我们学习as引导的定语从句。好，下课。", backend_name="dummy", quality="fast")
    print("narrate ok:", getattr(res, "audio", None) or res)
except Exception as exc:  # noqa: BLE001
    P(f"narrate failed after upgrade: {exc!r}")
print("== PROBLEMS:", len(problems))
