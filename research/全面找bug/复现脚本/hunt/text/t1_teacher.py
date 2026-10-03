import csv, time, sys
from h import *
M = Path(ROOT) / "research/文字校正/老师的母本"
orig = list(csv.DictReader(open(M / "母本_原文.csv", encoding="utf-8-sig")))
clean = {r["id"]: r["text"] for r in csv.DictReader(open(M / "母本_修缮后.csv", encoding="utf-8-sig"))}
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
project = wf.Project(cfg, "老师").ensure()
project.save_manifest([{"id": r["id"], "path": f"clips/{r['id']}.wav", "text": r["text"], "lang": "zh",
                        "duration": 3.0, "keep": r["keep"] == "1", "deleted": r["drop_reason"] == "老师删除",
                        "split": "train"} for r in orig])
mode = sys.argv[1] if len(sys.argv) > 1 else "once"
t = time.time()
before = {r["id"]: dict(r) for r in project.load_manifest()}
if mode == "once":
    res = wf.run_transcript_fix(cfg, "老师", once=True)
elif mode == "upload_clean":
    res = wf.run_transcript_fix(cfg, "老师", once=True, files=[str(M / "母本_修缮后.csv")])
print("secs", round(time.time()-t,1), "fixes", res["fixes"], "adopted", res["adopted"]["changes"], res["adopted"]["rows"])
draft = review.load_draft(project)
need = {r["id"] for r in orig if r["text"] != clean[r["id"]] and r["drop_reason"] != "老师删除"}
print("draft", len(draft), "need", len(need), "extra", sorted(set(draft)-need)[:10], "missing", sorted(need-set(draft))[:10])
bad = [i for i in need & set(draft) if draft[i]["text"] != clean[i]]
print("wrong", len(bad), [(i, draft[i]["text"], clean[i]) for i in bad[:3]])
# table display check: what shows red/edits after
recs = project.load_manifest()
n_edits = sum(1 for r in recs if not r.get("deleted") and review.analyze(r, review.current_values(r, draft.get(r["id"]))["text"])["edits"])
print("rows with remaining suggestions", n_edits)
t = table(project)
review.save_rows(project)
t2 = table(project)
diff = [k for k in t if t[k] != t2[k]]
print("save display diffs", len(diff), [(k, t[k], t2[k]) for k in diff[:3]])
print("used", tf.textfix_used(project))
