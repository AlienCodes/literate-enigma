"""One-click + table functions on odd row texts (manifest written directly, like prepare / Excel import could)."""
import traceback, json
from h import *
from voicetwin.data import proofcheck as pc
odd = ["", " ", "。", "a", "看看看看看看看看", "的的的的的", "借词" * 400, "​借词​", "😀借词😀是定语从剧", "𠮷借词𠮷",
       "ＡＢＣ借词１２３", "\x00借词\x1b", "借\t词", "I can see the the the cat.", "as as as 艾子艾子", "，，，。。。",
       "关系带词关系带词关系带词", "这是一个(定语从剧)。", "借词，", "借词" + "a" * 3000, "借词́", "&lt;b&gt;借词",
       "<script>借词</script>", "借词\r\n定语从剧", "Ⅷ借词", "ﾃｽﾄ借词", "定语从剧" * 50]
ids = [f"c{i:03d}" for i in range(len(odd))]
cfg, p = voice(odd, ids=ids)
recs = p.load_manifest()
for r in recs:  # odd suspects too
    t = r["text"]
    r["suspect"] = {"spans": [[0, max(1, len(t))], [len(t) + 5, len(t) + 9], [-3, 1]], "alt": (t[::-1] if len(t) < 50 else ""),
                    "reasons": ["自动"], "score": 0.6}
p.save_manifest(recs)
errs = []
def tryit(name, fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except (ValueError, KeyError) as e:
        return ("refused", str(e)[:40])
    except Exception as e:
        errs.append((name, a[1:] if len(a) > 1 else "", repr(e)[:200], traceback.format_exc()[-600:]))
for rid in ids:
    rec, c = cur(p, rid)
    tryit("analyze", review.analyze, rec, c)
r = tryit("click", wf.run_transcript_fix, cfg, "v", once=True)
print("click ->", r if not isinstance(r, dict) else (r.get("fixes"), r.get("adopted")))
for rid in ids:
    rec, c = cur(p, rid)
    tryit("analyze2", review.analyze, rec, c)
    tryit("adopt", review.adopt_suggestion, p, rid)
    tryit("unadopt", review.unadopt_suggestion, p, rid)
    tryit("edit", review.set_draft, p, rid, text=c + "曌")
    tryit("discard", review.discard_draft, p, rid)
    tryit("dismiss", pc.dismiss_suspect, p, rid)
tryit("save", review.save_rows, p)
tryit("export", review.export_text, p)
tryit("replace", review.replace_matches, p, "借词", "")
tryit("undo_replace", review.undo_replace, p)
tryit("find", review.find_matches, p, "​")
for rid in ids:
    rec, c = cur(p, rid)
    tryit("analyze3", review.analyze, rec, c)
print("errors:", len(errs))
for e in errs[:10]: print(json.dumps(e, ensure_ascii=False)[:1200])
