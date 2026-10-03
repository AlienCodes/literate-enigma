"""Random UI-like operations with the real web one-click (once=True), several batches of material.
Checks: no unexpected exception; on every click rows outside `only` unchanged (manifest/draft/rejected), teacher's
typed MARK chars kept, dismissed rows unchanged, no rejected piece re-applied; save display-neutral; adopt/unadopt
round trips; used-button state. usage: python fuzz_once.py seed steps"""
import random, sys, json, traceback, shutil
from h import *
from voicetwin.utils.textutil import clean_transcript
from voicetwin.data import proofcheck as pc
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
NSTEP = int(sys.argv[2]) if len(sys.argv) > 2 else 40
rng = random.Random(seed)
corpus = [(rid, clean_transcript(x)) for rid, x in tf.builtin_mother() if 6 <= len(x) <= 60]
corr = lf.builtin_corrections()
inv = {}
for k, v in corr.items(): inv.setdefault(v, []).append(k)
def corrupt(s, n=2):
    for _ in range(n):
        cands = [(v, k) for v, ks in inv.items() for k in ks if v in s]
        if cands and rng.random() < 0.8:
            v, k = rng.choice(cands); s = s.replace(v, k, 1)
    if rng.random() < 0.3:  # duplicated chars
        k = rng.randrange(len(s)); s = s[:k] + s[k] + s[k:]
    if rng.random() < 0.15:
        s = s + rng.choice([" OK, let's go.", "，对吧？", " the the", "看看看", "的的"])
    return clean_transcript(s)
def rand_auto(t):
    if not t: return None
    a = rng.randrange(0, max(1, len(t) - 3)); b = a + rng.choice([0, 1, 2, 3])
    rep = rng.choice(["which", "那个", "", "了", "as", "威驰", "的", "看看", "the", t[a:b] + t[a:b]])
    alt = clean_transcript(t[:a] + rep + t[b:])
    if rng.random() < 0.08: alt = clean_transcript(rng.choice(corpus)[1])  # whole sentence different
    if alt and alt != t and rng.random() < 0.75:
        return {"spans": [[a, max(b, a + 1)]], "alt": alt, "reasons": ["自动"], "score": 0.6}
    if rng.random() < 0.5:
        return {"spans": [[a, max(b, a + 1)]], "alt": "", "reasons": ["只标红"], "score": 0.6}
    return None
nb = [0]
def new_batch(p, n):
    recs = p.load_manifest()
    for i in range(n):
        rid, x = rng.choice(corpus)
        t = corrupt(x)
        if rng.random() < 0.15 and recs: t = rng.choice(recs)["text"]          # same sentence recorded again
        r = {"id": f"b{nb[0]}_{i:02d}", "path": f"clips/b{nb[0]}_{i}.wav", "text": t, "lang": "zh", "duration": 3.0,
             "keep": rng.random() > 0.1, "split": "train"}
        if rng.random() < 0.5:
            s = rand_auto(t)
            if s: r["suspect"] = s
        recs.append(r)
    nb[0] += 1
    p.save_manifest(recs)
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws"); p = wf.Project(cfg, "v").ensure()
p.save_manifest([])
new_batch(p, 6)
MARK = "曌"
probs, log, refused = [], [], []
def ids(): return [r["id"] for r in p.load_manifest()]
def disp(rid):
    rec, c = cur(p, rid)
    if rec.get("deleted"): return ("DELETED", c)
    i = review.analyze(rec, c)
    return (c, tuple(i["red"]), tuple(i["edits"]), tuple(i["undo"]), tuple(i["sure"]))
def snap():
    m = {r["id"]: json.dumps(r, ensure_ascii=False, sort_keys=True) for r in p.load_manifest()}
    return m, review.load_draft(p), review.load_rejected(p)
def clone():
    d2 = Path(tempfile.mkdtemp()); c2 = make_cfg(d2 / "ws"); p2 = wf.Project(c2, "v")
    shutil.copytree(p.root, p2.root); return c2, p2, d2
UPDIR = Path(tempfile.mkdtemp())
for step in range(NSTEP):
    op = rng.choice(["click", "click", "newbatch", "save", "save1", "adopt", "adopt", "unadopt", "unadopt", "edit", "edit",
                     "discard1", "dismiss", "delete", "restore", "replace", "undo_replace", "autocheck", "revert_type",
                     "keep", "export_up", "adopt_unadopt_check"])
    allids = ids(); rid = rng.choice(allids)
    m0, d0, j0 = snap()
    before = {k: cur(p, k)[1] for k in allids}
    try:
        if op in ("click", "export_up"):
            only = set(tf.textfix_new_ids(p)); files = None
            if op == "export_up":
                try:
                    files = [review.export_text(p)["path"]]
                except ValueError: files = None
            try:
                wf.run_transcript_fix(cfg, "v", once=True, files=files)
                if not only: probs.append(("click allowed although used", step))
            except ValueError as e:
                if only: probs.append(("click refused although new rows", step, str(e)[:60]))
                op += "-refused"
            if not op.endswith("refused"):
                m1, d1, j1 = snap()
                for k in m0:
                    if k in only: continue
                    if m0[k] != m1[k]: probs.append(("outside-only manifest changed", step, k, m0[k][:300], m1[k][:300]))
                    if d0.get(k) != d1.get(k): probs.append(("outside-only draft changed", step, k, d0.get(k), d1.get(k)))
                    if j0.get(k) != j1.get(k): probs.append(("outside-only rejected changed", step, k))
                if tf.textfix_new_ids(p): probs.append(("button not grey after click", step, tf.textfix_new_ids(p)))
                for k in allids:
                    a = cur(p, k)[1]
                    if a.count(MARK) < before[k].count(MARK): probs.append(("teacher MARK lost by click", step, k, before[k], a))
                    rec0 = json.loads(m0[k])
                    if rec0.get("suspect_ok") and rec0["suspect_ok"] == before[k] and a != before[k]:
                        probs.append(("dismissed row changed", step, k, before[k], a))
                    if a != before[k] and j0.get(k):
                        bad = {tuple(x) for x in j0[k]}
                        hit = [pc_ for pc_ in review.change_pieces(before[k], a) if pc_ in bad]
                        if hit: probs.append(("rejected re-applied", step, k, before[k], a, hit))
        elif op == "newbatch": new_batch(p, rng.randrange(1, 5))
        elif op == "save":
            a = {k: disp(k) for k in allids}; review.save_rows(p); b = {k: disp(k) for k in allids}
            diff = {k: (a[k], b[k]) for k in allids if a[k] != b[k]}
            if diff: probs.append(("save changed the display", step, diff))
        elif op == "save1": review.save_rows(p, [rid])
        elif op == "adopt":
            rec, c = cur(p, rid)
            if review.analyze(rec, c)["edits"] and not rec.get("deleted"):
                try:
                    review.adopt_suggestion(p, rid)
                    if MARK not in review.suspect_base(rec) and cur(p, rid)[1].count(MARK) < c.count(MARK): probs.append(("adopt removed teacher MARK", step, rid, c, cur(p, rid)[1]))
                except ValueError as e: refused.append(("adopt", str(e)[:20]))
            else: op += "-noop"
        elif op == "unadopt":
            rec, c = cur(p, rid)
            if review.analyze(rec, c)["undo"] and not rec.get("deleted"):
                try:
                    review.unadopt_suggestion(p, rid)
                    if MARK not in str(review.known_states(rec)) and cur(p, rid)[1].count(MARK) < c.count(MARK): probs.append(("unadopt removed teacher MARK", step, rid, c, cur(p, rid)[1]))
                except ValueError as e: refused.append(("unadopt", str(e)[:20]))
            else: op += "-noop"
        elif op == "edit":
            rec, c = cur(p, rid)
            if len(c) > 4 and not rec.get("deleted"):
                k = rng.randrange(1, len(c) - 1); review.set_draft(p, rid, text=c[:k] + MARK + c[k + rng.choice([0, 1]):])
            else: op += "-noop"
        elif op == "revert_type":
            rec, c = cur(p, rid)
            o = review.original_text(rec)
            blocks = [b for b in review._opcodes(o, c) if b[0] != "equal" and MARK not in c[b[3]:b[4]]]
            if blocks and not rec.get("deleted"):
                tag, i1, i2, j1, j2 = rng.choice(blocks)
                new = c[:j1] + o[i1:i2] + c[j2:]
                if clean_transcript(new): review.set_draft(p, rid, text=new)
            else: op += "-noop"
        elif op == "keep":
            rec, c = cur(p, rid)
            if not rec.get("deleted"):
                vals = review.current_values(rec, review.load_draft(p).get(rid)); review.set_draft(p, rid, keep=not vals["keep"])
        elif op == "discard1": review.discard_draft(p, rid)
        elif op == "dismiss": pc.dismiss_suspect(p, rid)
        elif op == "delete": review.delete_clip(p, rid)
        elif op == "restore": review.restore_clip(p, rid)
        elif op == "replace": review.replace_matches(p, rng.choice(["我们", "的", "the", "看"]), rng.choice(["咱们", "地", "", "a"]))
        elif op == "undo_replace": review.undo_replace(p)
        elif op == "autocheck":
            pc.build_suspect = lambda text, *a, **kw: rand_auto(text)
            pc.find_suspects(p, cfg)
        elif op == "adopt_unadopt_check":
            for k in allids:
                rec, c = cur(p, k)
                if rec.get("deleted"): continue
                info = review.analyze(rec, c)
                if info["edits"] and not info["undo"]:
                    c2, p2, dd = clone()
                    try:
                        review.adopt_suggestion(p2, k)
                        if review.analyze(*cur(p2, k))["undo"]:
                            review.unadopt_suggestion(p2, k)
                            if cur(p2, k)[1] != c: probs.append(("adopt+unadopt not round trip", step, k, c, cur(p2, k)[1]))
                        else: probs.append(("adopt leaves nothing to undo", step, k, c, cur(p2, k)[1]))
                    except ValueError as e: refused.append(("D4", str(e)[:20]))
                    shutil.rmtree(dd, ignore_errors=True)
                if info["undo"] and not info["edits"]:
                    c2, p2, dd = clone()
                    try:
                        review.unadopt_suggestion(p2, k)
                        if review.analyze(*cur(p2, k))["edits"]:
                            review.adopt_suggestion(p2, k)
                            if cur(p2, k)[1] != c: probs.append(("unadopt+adopt not round trip", step, k, c, cur(p2, k)[1]))
                    except ValueError as e: refused.append(("D5", str(e)[:20]))
                    shutil.rmtree(dd, ignore_errors=True)
    except (ValueError, KeyError) as e:
        refused.append((op, str(e)[:30]))
    except Exception as e:
        probs.append(("EXC", step, op, rid, repr(e), traceback.format_exc()[-700:]))
    log.append((op, rid))
print("seed", seed, "problems", len(probs), "refused", len(refused))
seen = set()
for x in probs:
    if x[0] in seen and x[0] != "EXC": continue
    seen.add(x[0]); print("  ", json.dumps(x, ensure_ascii=False)[:1500])
if probs or "-v" in sys.argv: print("   ops:", log)
shutil.rmtree(d, ignore_errors=True); shutil.rmtree(UPDIR, ignore_errors=True)
