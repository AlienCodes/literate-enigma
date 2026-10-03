"""Invariant 4: after the first batch is used, random teacher ops on old rows, then new material + click once:
old rows (manifest record, draft entry, rejected memory) must be byte-identical."""
import random, sys, json, traceback, copy
from h import *
from voicetwin.utils.textutil import clean_transcript
from voicetwin.data import proofcheck as pc
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
rng = random.Random(seed)
corpus = [(rid, clean_transcript(x)) for rid, x in tf.builtin_mother() if 8 <= len(x) <= 50]
corr = lf.builtin_corrections()
inv = {}
for k, v in corr.items(): inv.setdefault(v, []).append(k)
def corrupt(s, n=2):
    for _ in range(n):
        cands = [(v, k) for v, ks in inv.items() for k in ks if v in s]
        if cands and rng.random() < 0.85:
            v, k = rng.choice(cands); s = s.replace(v, k, 1)
    return clean_transcript(s)
def pick(n):
    out = []
    while len(out) < n:
        x = rng.choice(corpus)
        if x not in out: out.append(x)
    return out
first = pick(6)
cfg, p = voice([corrupt(x) for _, x in first], ids=[f"a{i}" for i in range(6)])
recs = p.load_manifest()
for r in recs:
    if rng.random() < 0.5:
        t = r["text"]; a = rng.randrange(0, max(1, len(t) - 3)); b = a + rng.choice([1, 2])
        alt = clean_transcript(t[:a] + rng.choice(["那个", "的", "as", ""]) + t[b:])
        r["suspect"] = {"spans": [[a, b]], "alt": alt if alt != t else "", "reasons": ["自动"], "score": 0.6}
p.save_manifest(recs)
wf.run_transcript_fix(cfg, "v", once=True)
old_ids = [r["id"] for r in p.load_manifest()]
MARK = "曌"
probs = []
for step in range(rng.randrange(3, 12)):
    op = rng.choice(["adopt", "unadopt", "edit", "save", "dismiss", "discard1", "delete", "restore", "replace"])
    rid = rng.choice(old_ids)
    try:
        rec, c = cur(p, rid)
        info = review.analyze(rec, c)
        if op == "adopt" and info["edits"]: review.adopt_suggestion(p, rid)
        elif op == "unadopt" and info["undo"]: review.unadopt_suggestion(p, rid)
        elif op == "edit" and len(c) > 4:
            k = rng.randrange(1, len(c) - 1); review.set_draft(p, rid, text=c[:k] + MARK + c[k + 1:])
        elif op == "save": review.save_rows(p)
        elif op == "dismiss": pc.dismiss_suspect(p, rid)
        elif op == "discard1": review.discard_draft(p, rid)
        elif op == "delete": review.delete_clip(p, rid)
        elif op == "restore": review.restore_clip(p, rid)
        elif op == "replace": review.replace_matches(p, "我们", "咱们")
    except ValueError:
        pass
def snap():
    m = {r["id"]: json.dumps(r, ensure_ascii=False, sort_keys=True) for r in p.load_manifest()}
    return m, review.load_draft(p), review.load_rejected(p)
# new material: some new rows, including copies of old texts (same sentence recorded again)
second = pick(4)
recs = p.load_manifest()
newtexts = [corrupt(x) for _, x in second] + [recs[0]["text"], recs[1].get("orig_text") or recs[1]["text"]]
for i, t in enumerate(newtexts):
    recs.append({"id": f"b{i}", "path": f"clips/b{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"})
p.save_manifest(recs)
m0, d0, j0 = snap()
newids = tf.textfix_new_ids(p)
# restored rows (deleted at first click) count as new too
try:
    wf.run_transcript_fix(cfg, "v", once=True)
except Exception as e:
    probs.append(("EXC", repr(e), traceback.format_exc()[-500:]))
m1, d1, j1 = snap()
for k in m0:
    if k in newids: continue
    if m0[k] != m1[k]: probs.append(("manifest changed", k, m0[k], m1[k]))
    if d0.get(k) != d1.get(k): probs.append(("draft changed", k, d0.get(k), d1.get(k)))
    if j0.get(k) != j1.get(k): probs.append(("rejected changed", k, j0.get(k), j1.get(k)))
print("seed", seed, "new", len(newids), "problems", len(probs))
for x in probs[:5]: print("  ", json.dumps(x, ensure_ascii=False)[:800])
