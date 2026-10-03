"""Upgrade fuzz: random teacher sessions with an OLD version, then open the workspace with the CURRENT version.

usage:
  python fuzz_upgrade.py old <old_src> <ws_dir> <seed>   # build (old code)
  python fuzz_upgrade.py new <repo>    <ws_dir> <seed>   # check (new code)
"""
import json
import random
import sys
import traceback
from pathlib import Path

MODE, SRC, WS, SEED = sys.argv[1], sys.argv[2], Path(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, SRC)
sys.path.insert(0, SRC + "/tests")
import voicetwin  # noqa: E402

assert str(Path(voicetwin.__file__).resolve()).startswith(str(Path(SRC).resolve()))
from conftest import make_cfg  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review, proofcheck  # noqa: E402

V = "我的声音"
rng = random.Random(SEED)
PAIRS = [("借词", "介词"), ("艾子", "as"), ("关系带词", "关系代词"), ("从剧", "从句"), ("现行词", "先行词"),
         ("主剧", "主句"), ("据首", "句首"), ("定于从句", "定语从句"), ("例语", "例句"), ("壮与从剧", "状语从句")]
TEMPL = ["我们先来看{0}后面接宾语的情况。", "首先，{0}这个关系代词经常出现在非限定性{1}中。",
         "这个句子里的{0}放在{1}。", "大多数情况下，{0}所代替的就是整个句子中的{1}。",
         "例如下面这个句子，{0}引导的{1}。", "所以说这个{0}是整个{1}，大家看一看看。",
         "我们我们再来看一下{0}和{1}的区别。", "今天我们讲的是{0}，下节课讲{1}。",
         "Next, let's look at the {0} example.", "这就是{0}的的全部内容了。"]


def snapshot(project):
    d = review.load_draft(project)
    out = {}
    for r in project.load_manifest():
        vals = review.current_values(r, d.get(r["id"]))
        a = review.analyze(r, vals["text"])
        out[r["id"]] = {"text": vals["text"], "saved": r.get("text"), "dirty": review.is_dirty(r, d.get(r["id"])),
                        "deleted": bool(r.get("deleted")), "ok": r.get("suspect_ok"), "keep": vals["keep"],
                        "red": [list(x) for x in a["red"]], "edits": [list(x) for x in a["edits"]],
                        "undo": [list(x) for x in a["undo"]], "adopted": a["adopted"]}
    return out


if MODE == "old":
    cfg = make_cfg(WS)
    project = wf.Project(cfg, V).ensure()
    recs = []
    for i in range(14):
        a, b = rng.sample(PAIRS, 2)
        t = rng.choice(TEMPL).format(rng.choice([a[0], a[1]]), rng.choice([b[0], b[1]]))
        recs.append({"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh", "duration": 3.0,
                     "keep": rng.random() > 0.1, "split": "train", "asr_done": True})
    for r in recs:  # old-style suspects (auto proofcheck format)
        if rng.random() < 0.6:
            t = r["text"]
            cands = [(w, c) for w, c in PAIRS if w in t]
            if cands:
                w, c = rng.choice(cands)
                s = t.index(w)
                alt = t.replace(w, c, 1)
            else:
                s = rng.randrange(0, max(1, len(t) - 2))
                w = t[s:s + 2]
                alt = t[:s] + rng.choice(["那个", "这个", "", "the"]) + t[s + 2:]
            r["suspect"] = {"spans": [[s, s + len(w)]], "alt": alt if alt != t else "", "reasons": ["另一个识别引擎听成了别的"],
                            "score": round(rng.uniform(0.45, 0.9), 3)}
    project.save_manifest(recs)
    ids = [r["id"] for r in recs]
    log = []
    for step in range(rng.randint(4, 18)):
        rid = rng.choice(ids)
        op = rng.choice(["edit", "adopt", "unadopt", "save", "save_all", "delete", "restore", "dismiss", "revert",
                         "replace", "undo_replace", "confirm"])
        try:
            if op == "edit":
                d = review.load_draft(project)
                rec = {r["id"]: r for r in project.load_manifest()}[rid]
                t = review.current_values(rec, d.get(rid))["text"]
                w, c = rng.choice(PAIRS)
                if w in t:
                    t = t.replace(w, c, 1)
                else:
                    k = rng.randrange(0, len(t))
                    t = t[:k] + rng.choice(["好", "啊", "这", ""]) + t[k + 1:]
                review.set_draft(project, rid, text=t)
            elif op == "adopt":
                review.adopt_suggestion(project, rid)
            elif op == "unadopt":
                review.unadopt_suggestion(project, rid)
            elif op == "save":
                review.save_rows(project, [rid])
            elif op == "save_all":
                review.save_rows(project)
            elif op == "delete":
                review.delete_clip(project, rid)
            elif op == "restore":
                review.restore_clip(project, rid)
            elif op == "dismiss":
                proofcheck.dismiss_suspect(project, rid)
            elif op == "revert":
                review.discard_draft(project, rid)
            elif op == "replace" and hasattr(review, "replace_matches"):
                w, c = rng.choice(PAIRS)
                review.replace_matches(project, w, c)
            elif op == "undo_replace" and hasattr(review, "undo_replace"):
                review.undo_replace(project)
            elif op == "confirm":
                review.save_rows(project)
                review.save_confirmed(project, project.load_manifest())
            log.append([op, rid, "ok"])
        except (ValueError, KeyError) as exc:
            log.append([op, rid, f"refused: {str(exc)[:30]}"])
    blk = wf.training_blocker(project) if hasattr(wf, "training_blocker") else None
    snap = {"version": voicetwin.__version__, "log": log, "rows": snapshot(project), "blocker": blk}
    (WS / "old.json").write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    print("built", voicetwin.__version__, len(log))
    sys.exit(0)

# ------------------------------------------------------------------------------------------- new
from voicetwin.data import transcript_fix as tf  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402

old = json.loads((WS / "old.json").read_text(encoding="utf-8"))
cfg = make_cfg(WS)
project = wf.open_project(cfg, V, must_exist=True)
problems = []


def P(kind, msg):
    problems.append([kind, msg])


try:
    now = snapshot(project)
    for rid, o in old["rows"].items():
        n = now[rid]
        for k in ("text", "saved", "dirty", "deleted", "keep"):
            if o[k] != n[k]:
                P("display-core", f"{rid} {k}: {o[k]!r} -> {n[k]!r}")
        for k in ("red", "edits", "undo", "adopted"):
            if o[k] != n[k]:
                P("display-diff", f"{rid} {k}: {o[k]!r} -> {n[k]!r}  text={n['text']}")
    ui = A.WebUI(cfg)
    ui.on_voice_change(V)
    tbl = A._clips_table(cfg, V)
    for i in range(len(tbl)):
        ui.on_clip_pick(V, tbl, i, 4)
    A._clips_count_md(cfg, V)
    ui.textfix_info(V)
    if ui.textfix_btn(V)["interactive"] is not True:
        P("button", "one-click not enabled after upgrade")
    blk = wf.training_blocker(project)
    if old["blocker"] is not None and (old["blocker"] or "") != blk:
        P("gate", f"blocker changed: {old['blocker']!r} -> {blk!r}")
    before = snapshot(project)
    outs = list(ui.do_textfix(V))
    after = snapshot(project)
    for rid in before:
        b, a = before[rid], after[rid]
        if b["deleted"] and a["text"] != b["text"]:
            P("lost", f"deleted row {rid} changed")
        if b["ok"] and b["ok"] == b["text"] and a["text"] != b["text"]:
            P("lost", f"dismissed row {rid} changed: {b['text']} -> {a['text']}")
        # the teacher's own changes (draft/saved vs original recognised text) must still be there
        rec = {r["id"]: r for r in project.load_manifest()}[rid]
        orig = review.original_text(rec)
        mine = review.change_pieces(orig, b["text"])
        gone = [pc for pc in mine if pc not in review.change_pieces(orig, a["text"]) and pc[1] and pc[1] not in a["text"]]
        if gone:
            P("lost", f"{rid} teacher change {gone} disappeared: {b['text']} -> {a['text']}")
    # every row action still works without crashing
    for rid, a in after.items():
        if a["deleted"]:
            continue
        for act in ("adopt", "unadopt"):
            if (act == "adopt" and a["edits"]) or (act == "unadopt" and a["undo"]):
                try:
                    import shutil, tempfile  # noqa: E401
                    tmp = Path(tempfile.mkdtemp(dir=str(WS)))
                    shutil.copytree(project.root, tmp / V)
                    p2 = wf.open_project(make_cfg(tmp), V, must_exist=True)
                    (review.adopt_suggestion if act == "adopt" else review.unadopt_suggestion)(p2, rid)
                    shutil.rmtree(tmp)
                except ValueError:
                    pass
    review.save_rows(project)
    review.save_confirmed(project, project.load_manifest())
    blk = wf.training_blocker(project)
    if blk:
        P("gate", f"still blocked after save+confirm: {blk}")
except Exception:  # noqa: BLE001
    P("crash", traceback.format_exc()[-800:])
print(json.dumps({"seed": SEED, "from": old["version"], "problems": problems}, ensure_ascii=False))
