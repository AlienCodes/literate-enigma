# 复查（第四轮 g2 的检查意见）用的复现脚本，原样保留；不给参数就用这个仓库：/tmp/gsv39/bin/python 复查_p2_correct_upload.py
# textfix#1 probes: uploaded typed script with typos the fix may still let through
import sys, tempfile, json
from pathlib import Path
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review

CASES = [
    # (row = recognition error, upload = correct 母本)
    ("我们在来看一个例子，这个例子比较简单。", "我们再来看一个例子，这个例子比较简单。"),
    ("好，我们一起来度一下这个句子，注意它的语调和停顿。", "好，我们一起来读一下这个句子，注意它的语调和停顿。"),
    ("他跑得很快，但是他写的字很难看，我们要注意的地得的用法。", "他跑得很快，但是他写的字很难看，我们要注意的地得的用法。"),
    ("这个句子里面的动词要用过去式，因为事情已经发生了。", "这个句子里面的动词要用过去式，因为事情已经发声了。"),
    ("我们来看这个句子，它的主语是一个动名词短语，后面的谓语用单数。", "我们来看这个句子，它的主语是一个动名词短语，后面的谓语用单数。"),
    ("那么我们现在在来看第二个句子，它是一个定语从句。", "那么我们现在再来看第二个句子，它是一个定语从句。"),
]
for row, up in CASES:
    with tempfile.TemporaryDirectory() as d:
        cfg = make_cfg(Path(d) / "ws")
        project = wf.Project(cfg, "v").ensure()
        project.save_manifest([{"id": "c000", "path": "clips/c000.wav", "text": row, "lang": "zh",
                                "duration": 3.0, "keep": True, "split": "train"}])
        p = Path(d) / "讲稿.txt"
        p.write_text(up + "\n", encoding="utf-8")
        try:
            res = wf.run_transcript_fix(cfg, "v", once=True, files=[str(p)])
        except ValueError as e:
            print("REFUSED", up, str(e)[:60]); continue
        draft = review.load_draft(project)
        r = project.load_manifest()[0]
        cur = review.current_values(r, draft.get(r["id"]))["text"]
        info = review.analyze(r, cur)
        tag = "CHANGED" if cur != row else "same   "
        print(tag, cur, "| edits", info["edits"], "| sure", info.get("sure"), "| reasons", info["reasons"][:2])
