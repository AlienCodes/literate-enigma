"""一键全部文字校正：结果消息里的数字和实际改动对得上吗？"""
import os, sys, difflib
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
import tempfile
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A

texts = ["我们先来看艾子引导的定语从剧。", "关系代词that不能和借词一起提前到定语从句的句首。",
         "这个句子完全没有错。", "凭借词汇量取胜", "艾子和借词都是常见的识别错误，艾子要改成as。",
         "今天我们讲一下非谓语动词的用法。", "现在分词作壮语的时候要注意逻辑主语。"]
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
project = wf.Project(cfg, "v").ensure()
ids = [f"c{i:03d}" for i in range(len(texts))]
recs = [{"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"}
        for i, t in zip(ids, texts)]
# 自动查错字的建议（像 proofcheck 那样）
recs[5]["suspect"] = {"spans": [[8, 12]], "alt": "今天我们讲一下飞谓语动词的用法。", "reasons": ["另一个引擎听成：飞谓语"], "score": 0.6}
recs[6]["suspect"] = {"spans": [[5, 7]], "alt": "现在分词作状语的时候要注意逻辑主语。", "reasons": ["另一个引擎听成：状语"], "score": 0.6}
project.save_manifest(recs)
ui = A.WebUI(cfg)
outs = list(ui.do_textfix("v"))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("==== proof_md ====\n", last["proof_md"])
print("==== tr_info ====\n", last["tr_info"])
print("==== proof_bar (len) ====", len(str(last["proof_bar"])))
draft = review.load_draft(project)
nrows = nchunks = 0
for r in project.load_manifest():
    cur = review.current_values(r, draft.get(r["id"]))["text"]
    if cur != r["text"]:
        nrows += 1
        sm = difflib.SequenceMatcher(None, r["text"], cur)
        ch = [op for op in sm.get_opcodes() if op[0] != "equal"]
        nchunks += len(ch)
        print("CHANGED", r["id"], r["text"], "->", cur, "chunks", len(ch))
    info = review.analyze(r, cur)
    print("  row", r["id"], "red", info["red"], "edits", info["edits"])
print("actual rows changed", nrows, "diff chunks", nchunks)
