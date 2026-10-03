import random, sys, json, traceback, csv as _csv
from h import *
from voicetwin.utils.textutil import clean_transcript
from voicetwin.data import proofcheck as pc
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
NSTEP = int(sys.argv[2]) if len(sys.argv) > 2 else 30
rng = random.Random(seed)
corpus = [(rid, clean_transcript(x)) for rid, x in tf.builtin_mother() if 8 <= len(x) <= 50]
corr = lf.builtin_corrections()
inv = {}
for k, v in corr.items(): inv.setdefault(v, []).append(k)
def corrupt(s, n=2):
    for _ in range(n):
        cands = [(v, k) for v, ks in inv.items() for k in ks if v in s]
        if cands and rng.random() < 0.8:
            v, k = rng.choice(cands); s = s.replace(v, k, 1)
    return clean_transcript(s)
picked = [rng.choice(corpus) for i in range(7)]
use_ids = rng.random() < 0.5
texts = [corrupt(x) for _, x in picked]
ids = [rid for rid, _ in picked] if use_ids else None
if ids and len(set(ids)) < len(ids): ids = None
cfg, p = voice(texts, ids=ids)
recs = p.load_manifest()
def rand_auto(t):
    a = rng.randrange(0, max(1, len(t) - 3)); b = a + rng.choice([0, 1, 2])
    rep = rng.choice(["which", "那个", "", "了", "as", "威驰", "的"])
    alt = clean_transcript(t[:a] + rep + t[b:])
    if alt != t:
        return {"spans": [[a, max(b, a+1)]], "alt": alt, "reasons": ["自动"], "score": 0.6}
    return None
for r in recs:
    if rng.random() < 0.5:
        s = rand_auto(r["text"])
        if s: r["suspect"] = s
p.save_manifest(recs)
ids = [r["id"] for r in recs]
UPDIR = Path(tempfile.mkdtemp())
def upload_file():
    kind = rng.choice(["txt_orig", "txt_clean", "csv_orig", "csv_clean"])
    rows = p.load_manifest()
    if kind.startswith("txt"):
        f = UPDIR / "母本.txt"
        lines = [r["text"] if kind == "txt_orig" else dict(picked)[r["id"]] if r["id"] in dict(picked) else r["text"] for r in rows]
        f.write_text("\n".join(lines), encoding="utf-8")
    else:
        f = UPDIR / "transcripts.csv"
        with open(f, "w", encoding="utf-8-sig", newline="") as fh:
            w = _csv.writer(fh); w.writerow(["id", "text"])
            for r, (rid0, clean) in zip(rows, picked):
                w.writerow([r["id"], r["text"] if kind == "csv_orig" else clean])
    return [str(f)], kind
MARK = "曌"
expect_mark = {}
rej_watch = {}   # rid -> (text right after unadopt, list of proposed windows)
probs, log = [], []
teacher_pairs = {}
def disp(rid): return cur(p, rid)[1]
for step in range(NSTEP):
    op = rng.choice(["click", "click", "click_up", "save", "save1", "adopt", "unadopt", "unadopt", "edit", "discard1",
                     "discard_all", "dismiss", "delete", "restore", "replace", "undo_replace", "autocheck", "revert_type", "revert_type"])
    rid = rng.choice(ids)
    before = {k: disp(k) for k in ids}
    recs_b = {r["id"]: r for r in p.load_manifest()}
    try:
        if op == "click": wf.run_transcript_fix(cfg, "v")
        elif op == "click_up":
            files, kind = upload_file(); op = f"click_up:{kind}"
            wf.run_transcript_fix(cfg, "v", files=files)
        elif op == "save": review.save_rows(p)
        elif op == "save1": review.save_rows(p, [rid])
        elif op == "adopt":
            rec, c = cur(p, rid)
            if review.analyze(rec, c)["edits"] and not rec.get("deleted"):
                review.adopt_suggestion(p, rid); rej_watch.pop(rid, None)
            else: op = "adopt-noop"
        elif op == "unadopt":
            rec, c = cur(p, rid)
            if review.analyze(rec, c)["undo"] and not rec.get("deleted"):
                old_pairs = list(review.load_rejected(p).get(rid, []))
                review.unadopt_suggestion(p, rid)
                rec2 = {r["id"]: r for r in p.load_manifest()}[rid]
                new_pairs = [q for q in review.load_rejected(p).get(rid, []) if q not in old_pairs]
                rej_watch[rid] = (disp(rid), [q[1] for q in new_pairs], [q[0] for q in new_pairs])
            else: op = "unadopt-noop"
        elif op == "edit":
            rec, c = cur(p, rid)
            if not rec.get("deleted") and len(c) > 4:
                k = rng.randrange(1, len(c) - 1)
                new = c[:k] + MARK + c[k + rng.choice([0, 1]):]
                review.set_draft(p, rid, text=new); expect_mark[rid] = disp(rid).count(MARK)
                rej_watch.pop(rid, None)
            else: op = "edit-noop"
        elif op == "revert_type":
            rec, c = cur(p, rid)
            o = review.original_text(rec)
            blocks = [b for b in review._opcodes(o, c) if b[0] != "equal" and MARK not in c[b[3]:b[4]]]
            if blocks and not rec.get("deleted"):
                tag, i1, i2, j1, j2 = rng.choice(blocks)
                new = c[:j1] + o[i1:i2] + c[j2:]
                if clean_transcript(new):
                    review.set_draft(p, rid, text=new); rej_watch.pop(rid, None)
                else: op = "revert_type-noop"
            else: op = "revert_type-noop"
        elif op == "discard1":
            review.discard_draft(p, rid); expect_mark[rid] = disp(rid).count(MARK); rej_watch.pop(rid, None)
        elif op == "discard_all":
            review.discard_draft(p, None)
            for k in ids: expect_mark[k] = disp(k).count(MARK)
            rej_watch.clear()
        elif op == "dismiss": pc.dismiss_suspect(p, rid)
        elif op == "delete": review.delete_clip(p, rid)
        elif op == "restore": review.restore_clip(p, rid)
        elif op == "replace":
            r_ = review.replace_matches(p, "我们", "咱们")
            for k in r_["ids"]: rej_watch.pop(k, None)
        elif op == "undo_replace":
            review.undo_replace(p)
            for k in ids: expect_mark[k] = disp(k).count(MARK)
            rej_watch.clear()
        elif op == "autocheck":
            pc.build_suspect = lambda text, *a, **kw: rand_auto(text) if rng.random() < 0.5 else None
            pc.find_suspects(p, cfg)
    except Exception as e:
        probs.append(("EXC", step, op, rid, repr(e), traceback.format_exc()[-800:]))
    log.append((op, rid))
    if op in ("unadopt", "edit", "discard1", "revert_type") and before[rid] != disp(rid):
        tw = teacher_pairs.setdefault(rid, set())
        tw |= set(review.change_pieces(disp(rid), before[rid]))
    if op == "adopt": teacher_pairs.pop(rid, None)
    if op == "discard_all": teacher_pairs.clear()
    if op.startswith("click"):
        for k in ids:
            if before[k] != disp(k) and teacher_pairs.get(k):
                bad = set(review.change_pieces(before[k], disp(k))) & teacher_pairs[k]
                if bad and MARK not in str(bad):
                    probs.append(("teacher revert overridden", step, op, k, before[k], disp(k), sorted(bad)))
    after = {k: disp(k) for k in ids}
    for k, n in list(expect_mark.items()):
        if after[k].count(MARK) < n:
            probs.append(("teacher edit lost", step, op, k, before[k], after[k]))
        expect_mark[k] = after[k].count(MARK)
    if op.startswith("click"):
        recs_a = {r["id"]: r for r in p.load_manifest()}
        for k in ids:
            r0 = recs_b[k]
            if r0.get("suspect_ok") and r0["suspect_ok"] == before[k] and after[k] != before[k]:
                probs.append(("dismissed row changed", step, op, k, before[k], after[k]))
        for k, (t_u, props, wants) in list(rej_watch.items()):
            for pr, wa in zip(props, wants):
                if pr in after[k] and pr not in before[k]:
                    probs.append(("rejected re-applied", step, op, k, "undo->" + t_u, "now " + after[k], pr))
        # click right after click+save(all) must not change anything
        if len(log) >= 3 and log[-3][0].startswith("click") and log[-2][0] == "save" and review.load_draft(p):
            probs.append(("click after click+save changed", step, op, {k: v["text"] for k, v in review.load_draft(p).items()}))
print("seed", seed, "problems", len(probs))
seen = set()
for x in probs:
    if x[0] in seen and x[0] != "EXC": continue
    seen.add(x[0]); print("  ", x)
if probs: print("   ops:", log)
