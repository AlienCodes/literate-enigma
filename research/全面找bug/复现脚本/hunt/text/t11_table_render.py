"""Render the real table (_clips_table/_clips_count_md) for odd rows before/after the one-click and per-row actions."""
import traceback
from h import *
from voicetwin.webui import app
odd = ["", " ", "。", "a", "看看看看看看看看", "的的的的的", "​借词​", "😀借词😀是定语从剧", "𠮷借词𠮷", "ＡＢＣ借词１２３",
       "\x00借词\x1b", "借\t词", "I can see the the the cat.", "as as as 艾子艾子", "，，，。。。", "关系带词关系带词关系带词",
       "这是一个(定语从剧)。", "借词，", "借词́", "<script>借词</script>", "借词\r\n定语从剧", "Ⅷ借词", "ﾃｽﾄ借词", "&amp;借词"]
ids = [f"c{i:03d}" for i in range(len(odd))]
cfg, p = voice(odd, ids=ids)
recs = p.load_manifest()
for r in recs:
    t = r["text"]
    r["suspect"] = {"spans": [[0, max(1, len(t))]], "alt": t[::-1], "reasons": ["自动<b>"], "score": 0.6}
p.save_manifest(recs)
errs = []
def render(tag):
    for only in (False, True):
        try:
            app._clips_table(cfg, "v", only); app._clips_count_md(cfg, "v")
        except Exception as e:
            errs.append((tag, repr(e), traceback.format_exc()[-500:]))
render("before")
wf.run_transcript_fix(cfg, "v", once=True); render("after click")
for rid in ids:
    for fn in (review.adopt_suggestion, review.unadopt_suggestion):
        try: fn(p, rid)
        except (ValueError, KeyError): pass
    render("after adopt/unadopt " + rid)
review.save_rows(p); render("after save")
print("errors", len(errs)); [print(e) for e in errs[:5]]
