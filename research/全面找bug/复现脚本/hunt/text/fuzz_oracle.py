"""Oracle check for per-row 采用 / 已采用 after the real one-click, with random teacher edits in between.
For every successful adopt: each change cur->new must be one of the suggestion's own pieces (some state->alt), teacher
MARK chars kept, and new must be closer to alt. For unadopt: each change must reverse a program piece, closer to base.
usage: python fuzz_oracle.py seed rounds"""
import random, sys, json, shutil
from h import *
from voicetwin.utils.textutil import clean_transcript
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
R = int(sys.argv[2]) if len(sys.argv) > 2 else 10
rng = random.Random(seed)
corpus = [clean_transcript(x) for _, x in tf.builtin_mother() if 8 <= len(x) <= 45]
corr = lf.builtin_corrections(); inv = {}
for k, v in corr.items(): inv.setdefault(v, []).append(k)
def corrupt(s):
    for _ in range(3):
        c = [(v, k) for v, ks in inv.items() for k in ks if v in s]
        if c and rng.random() < 0.8:
            v, k = rng.choice(c); s = s.replace(v, k, 1)
    if rng.random() < 0.4:
        k = rng.randrange(len(s)); s = s[:k] + s[k] + s[k:]
    return clean_transcript(s)
MARK = "曌"
probs = []; stats = {"adopt_ok": 0, "adopt_ref": 0, "un_ok": 0, "un_ref": 0}
for rnd in range(R):
    texts = [corrupt(rng.choice(corpus)) for _ in range(6)]
    cfg, p = voice(texts)
    recs = p.load_manifest()
    for r in recs:   # unsure auto suggestions next to the table fixes
        t = r["text"]
        if rng.random() < 0.6 and len(t) > 4:
            a = rng.randrange(0, len(t) - 2); b = a + rng.choice([0, 1, 2])
            alt = clean_transcript(t[:a] + rng.choice(["那个", "的", "as", "", t[a:b] * 2, "了"]) + t[b:])
            if alt != t: r["suspect"] = {"spans": [[a, max(b, a + 1)]], "alt": alt, "reasons": ["自动"], "score": 0.6}
    p.save_manifest(recs)
    wf.run_transcript_fix(cfg, "v", once=True)
    for r in p.load_manifest():
        rid = r["id"]
        for trial in range(8):
            rec, c = cur(p, rid)
            st = review.known_states(rec)
            if not st: break
            # random teacher edit (sometimes none)
            if rng.random() < 0.7 and len(c) > 3:
                k = rng.randrange(0, len(c)); kind = rng.choice(["ins", "rep", "del", "dup"])
                new = {"ins": c[:k] + MARK + c[k:], "rep": c[:k] + MARK + c[k + 1:], "del": c[:k] + c[k + 1:],
                       "dup": c[:k] + c[k] + c[k:]}[kind]
                if clean_transcript(new): review.set_draft(p, rid, text=new)
            rec, c = cur(p, rid); info = review.analyze(rec, c)
            ops = [o for o, ok in (("adopt", info["edits"]), ("unadopt", info["undo"])) if ok]
            if not ops: continue
            op = rng.choice(ops)
            states = [st[k] for k in ("base", "direct", "sure", "alt") if st.get(k)]
            try:
                if op == "adopt":
                    new = review.adopt_suggestion(p, rid)["text"]
                    allowed = {pc_ for x in states for pc_ in review.change_pieces(x, st["alt"])}
                    target = st["alt"]; stats["adopt_ok"] += 1
                else:
                    new = review.unadopt_suggestion(p, rid)["text"]
                    allowed = {pc_ for x in states for pc_ in review.change_pieces(x, st["base"])}
                    target = st["base"]; stats["un_ok"] += 1
            except ValueError:
                stats["adopt_ref" if op == "adopt" else "un_ref"] += 1; continue
            extra = [pc_ for pc_ in review.change_pieces(c, new) if pc_ not in allowed]
            if new.count(MARK) < c.count(MARK): probs.append((op, "MARK lost", c, new, st))
            elif extra: probs.append((op, "piece not from suggestion", c, new, extra, st))
            elif review.unit_dist(new, target) >= review.unit_dist(c, target): probs.append((op, "not closer", c, new, st))
    shutil.rmtree(Path(p.root).parents[1], ignore_errors=True)
print("seed", seed, stats, "problems", len(probs))
for x in probs[:6]: print("  ", json.dumps(x, ensure_ascii=False)[:900])
