"""WHATS_NEW 18.5 claim: 'your mother corpus: 1008 sentences had 138 recognition errors ... install this version and click
one-click correction once and they will all be fixed'. Rebuild the original ASR text of each sentence by undoing the 138
fixes in core_corpus.tsv, put the 1005 sentences in a temp voice with the same ids, click once, count what got fixed."""
import sys, time, os
VT_ROOT = os.environ.get("VT_ROOT", "/home/user/literate-enigma")
sys.path.insert(0, VT_ROOT + "/research/文字校正/随机操作")
import h
from voicetwin import workflows as wf
from voicetwin.data import transcript_fix as tf
from voicetwin.data import review
mother = list(tf.builtin_mother())
fixes = tf.builtin_fixes()
orig = {}
problems = 0
for rid, text in mother:
    t = text
    for a, b, why in fixes.get(rid, ()):
        if b in t:
            t = t.replace(b, a, 1)
        else:
            problems += 1
    orig[rid] = t
print("sentences", len(mother), "fix rows", sum(len(v) for v in fixes.values()), "ids with fixes", len(fixes),
      "fix ids not in corpus", [k for k in fixes if k not in orig], "unreversible", problems)
ids = [rid for rid, _ in mother]
cfg, project = h.voice([orig[i] for i in ids], ids=ids, name="v")
t0 = time.time()
r = wf.run_transcript_fix(cfg, "v", once=True)
print("time %.1fs" % (time.time() - t0), "fixes", r.get("fixes"), "fixed_rows", r.get("fixed_rows"),
      "adopted", (r.get("adopted") or {}).get("changes"))
good = bad = 0
miss = []
for rid, text in mother:
    now = h.cur(project, rid)[1]
    if rid in fixes:
        if now == text:
            good += 1
        else:
            miss.append((rid, orig[rid][:60], now[:60], text[:60]))
    elif now != text:
        bad += 1
        miss.append(("CHANGED-UNFIXED " + rid, orig[rid][:60], now[:60], text[:60]))
print("sentences with fixes fully corrected:", good, "/", len(fixes), "; sentences without fixes changed:", bad)
for m in miss[:15]:
    print(m)
