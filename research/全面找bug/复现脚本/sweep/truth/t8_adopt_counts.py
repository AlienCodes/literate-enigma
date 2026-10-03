import sys, tempfile, difflib
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
p = wf.Project(cfg, "v").ensure()
texts = ["这里的威驰引导定语从句，借词后面接宾语。", "我们再看威驰引导的非限定性定语从句。", "这里用威驰来指代前面整个句子。"]
recs = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(texts)]
for r in recs:
    at = r["text"].index("威驰")
    r["suspect"] = {"spans": [[at, at + 2]], "alt": r["text"][:at] + "which" + r["text"][at + 2:], "reasons": ["另一个引擎听到 which"], "score": 0.7}
p.save_manifest(recs)
ui = A.WebUI(cfg)
outs = list(ui.do_textfix("v"))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print(last["proof_md"])
draft = review.load_draft(p)
rows = chunks = 0
for r in p.load_manifest():
    cur = review.current_values(r, draft.get(r["id"]))["text"]
    if cur != r["text"]:
        rows += 1; ch = [o for o in difflib.SequenceMatcher(None, r["text"], cur).get_opcodes() if o[0] != "equal"]; chunks += len(ch)
        print("CHANGED", r["text"], "->", cur)
    print("  left:", review.analyze(r, cur)["red"], review.analyze(r, cur)["edits"])
print("rows", rows, "chunks", chunks)
