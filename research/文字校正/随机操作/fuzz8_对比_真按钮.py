"""Round-5 differential fuzzer (new checks, not in fuzz6):
  D1 'own export is no information': uploading 下载改好的文字 (the rows' own current texts) as the only mother must give
     the same table (text / red / suggestions / undo) as a click with no upload;
  D2 'click is idempotent': a second click right after a click changes nothing (texts and what the table shows);
  D3 'save is display-neutral': 保存修改 doesn't change what the table shows (red / suggestions / undo / blue)."""
import random, sys, json, traceback, shutil, tempfile
from h import *
from conftest import make_cfg
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
picked = []
while len(picked) < 6:
    x = rng.choice(corpus)
    if x not in picked: picked.append(x)
texts = [corrupt(x) for _, x in picked]
ids = [rid for rid, _ in picked]          # real ids: the row's own builtin line is excluded (like the teacher's data)
cfg, p = voice(texts, ids=ids)
def rand_auto(t):
    a = rng.randrange(0, max(1, len(t) - 3)); b = a + rng.choice([0, 1, 2, 3])
    rep = rng.choice(["which", "那个", "", "了", "as", "威驰", "的", "单单"])
    alt = clean_transcript(t[:a] + rep + t[b:])
    if alt != t and rng.random() < 0.7:
        return {"spans": [[a, max(b, a + 1)]], "alt": alt, "reasons": ["自动"], "score": 0.6}
    if rng.random() < 0.5:
        return {"spans": [[a, max(b, a + 1)]], "alt": "", "reasons": ["只标红"], "score": 0.6}
    return None
recs = p.load_manifest()
for r in recs:
    s = rand_auto(r["text"])
    if s: r["suspect"] = s
p.save_manifest(recs)
MARK = "曌"
def disp(project, rid):
    rec, c = cur(project, rid)
    if rec.get("deleted"): return ("DELETED", c)
    i = review.analyze(rec, c)
    return (c, tuple(i["red"]), tuple(i["edits"]), tuple(i["undo"]), tuple(i["sure"]))
def table(project): return {k: disp(project, k) for k in ids}
def clone(no_uploads=False):
    d = Path(tempfile.mkdtemp()); cfg2 = make_cfg(d / "ws")
    p2 = wf.Project(cfg2, "v")
    shutil.copytree(p.root, p2.root)
    if no_uploads:
        shutil.rmtree(p2.root / tf.TRANSCRIPT_DIR, ignore_errors=True)
    return cfg2, p2
probs, log, refused = [], [], []
for step in range(NSTEP):
    op = rng.choice(["click", "click", "export_up", "export_up", "save", "adopt", "unadopt", "unadopt", "edit",
                     "discard1", "dismiss", "revert_type", "autocheck", "replace", "undo_replace"])
    rid = rng.choice(ids)
    try:
        if op == "click":
            wf.run_transcript_fix(cfg, "v")
            c2, p2 = clone()
            a = table(p); wf.run_transcript_fix(c2, "v"); b = table(p2)
            diff = {k: (a[k], b[k]) for k in ids if a[k] != b[k]}
            if diff: probs.append(("D2 click not idempotent", step, diff))
        elif op == "export_up":
            exp = review.export_text(p)
            c2, p2 = clone(no_uploads=True)
            wf.run_transcript_fix(cfg, "v", files=[exp["path"]])
            wf.run_transcript_fix(c2, "v")
            a, b = table(p), table(p2)
            cleaner = lf.Lexicon.build([])
            lines = {k: cur(p2, k)[1] for k in ids}
            dirty = {k for k in ids if cleaner.list_fixes(lines[k])}
            diff = {k: ("with own export", a[k], "no upload", b[k]) for k in ids if a[k] != b[k] and k not in dirty}
            if diff: probs.append(("D1 own export changed the result", step, diff))
            shutil.rmtree(p.root / tf.TRANSCRIPT_DIR, ignore_errors=True)  # don't keep it as a mother for later steps
        elif op == "save":
            a = table(p); review.save_rows(p); b = table(p)
            diff = {k: (a[k], b[k]) for k in ids if a[k] != b[k]}
            if diff: probs.append(("D3 save changed the display", step, diff))
        elif op == "adopt":
            rec, c = cur(p, rid)
            if review.analyze(rec, c)["edits"] and not rec.get("deleted"): review.adopt_suggestion(p, rid)
            else: op += "-noop"
        elif op == "unadopt":
            rec, c = cur(p, rid)
            if review.analyze(rec, c)["undo"] and not rec.get("deleted"): review.unadopt_suggestion(p, rid)
            else: op += "-noop"
        elif op == "edit":
            rec, c = cur(p, rid)
            if len(c) > 4:
                k = rng.randrange(1, len(c) - 1); review.set_draft(p, rid, text=c[:k] + MARK + c[k + rng.choice([0, 1]):])
            else: op += "-noop"
        elif op == "revert_type":
            rec, c = cur(p, rid)
            o = review.original_text(rec)
            blocks = [b for b in review._opcodes(o, c) if b[0] != "equal" and MARK not in c[b[3]:b[4]]]
            if blocks:
                tag, i1, i2, j1, j2 = rng.choice(blocks)
                new = c[:j1] + o[i1:i2] + c[j2:]
                if clean_transcript(new): review.set_draft(p, rid, text=new)
            else: op += "-noop"
        elif op == "discard1": review.discard_draft(p, rid)
        elif op == "dismiss": pc.dismiss_suspect(p, rid)
        elif op == "replace": review.replace_matches(p, "我们", "咱们")
        elif op == "undo_replace": review.undo_replace(p)
        elif op == "autocheck":
            pc.build_suspect = lambda text, *a, **kw: rand_auto(text)
            pc.find_suspects(p, cfg)
    except Exception as e:
        probs.append(("EXC", step, op, rid, repr(e), traceback.format_exc()[-600:]))
    log.append((op, rid))
    try:
        for k in ids:
            rec, c = cur(p, k)
            if rec.get("deleted") or not isinstance(rec.get("suspect"), dict): continue
            info = review.analyze(rec, c)
            base = review.suspect_base(rec); alt = str(rec["suspect"].get("alt") or "")
            if info["edits"] and alt and review.apply_edits(c, info["undo"]) == base:
                c3, p3 = clone()
                try:
                    got = review.adopt_suggestion(p3, k)["text"]
                    if got != clean_transcript(alt):
                        probs.append(("D6 adopt gives something else than the suggestion", step, k, "now " + c, "alt " + alt, "adopt -> " + got))
                except ValueError as e:
                    refused.append(("D6-refused", step, k, str(e)[:40]))
            if info["edits"] and not info["undo"]:
                c2, p2 = clone()
                try:
                    review.adopt_suggestion(p2, k)
                except ValueError as e:
                    refused.append(("D4-refused", step, k, str(e)[:40])); continue
                if review.analyze(*cur(p2, k))["undo"]:
                    try:
                        review.unadopt_suggestion(p2, k)
                    except ValueError as e:
                        refused.append(("D4b-refused", step, k, str(e)[:40])); continue
                    if cur(p2, k)[1] != c: probs.append(("D4 adopt+unadopt not a round trip", step, k, c, cur(p2, k)[1]))
                else: probs.append(("D4 adopt leaves nothing to undo", step, k, c, cur(p2, k)[1]))
            if info["undo"] and not info["edits"]:
                c2, p2 = clone()
                try:
                    review.unadopt_suggestion(p2, k)
                except ValueError as e:
                    refused.append(("D5-refused", step, k, str(e)[:40])); continue
                if review.analyze(*cur(p2, k))["edits"]:
                    try:
                        review.adopt_suggestion(p2, k)
                    except ValueError as e:
                        refused.append(("D5b-refused", step, k, str(e)[:40])); continue
                    if cur(p2, k)[1] != c: probs.append(("D5 unadopt+adopt not a round trip", step, k, c, cur(p2, k)[1]))
    except Exception as e:
        probs.append(("EXC-check", step, repr(e), traceback.format_exc()[-600:]))
print("seed", seed, "problems", len(probs), "refused", len(refused), refused[:3])
seen = set()
for x in probs:
    if x[0] in seen and x[0] != "EXC": continue
    seen.add(x[0]); print("  ", json.dumps(x, ensure_ascii=False)[:1500])
if probs: print("   ops:", log)
