# 复查（第四轮 g2 的检查意见）用的复现脚本，原样保留；不给参数就用这个仓库：/tmp/gsv39/bin/python 复查_p1_upload.py
# textfix#1 probes: uploaded typed script with typos the fix may still let through
import sys, tempfile, json
from pathlib import Path
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review

CASES = [
    # (row correct, uploaded typo)
    ("这个句子的意义很重要，我们要好好理解它的用法。", "这个句子的异议很重要，我们要好好理解它的用法。"),
    ("好，下面我们来做一下练习，大家把书翻到第三十页。", "好，下面我们来做一下联系，大家把书翻到第三十页。"),
    ("这个时候我们要注意，后面的动词要用过去式。", "这个事后我们要注意，后面的动词要用过去式。"),
    ("This is the sentence which I like very much, and we will read it again and again in class today.", "This is the sentense which I like very much, and we will read it again and again in class today."),
    ("我们来看这个句子，He is the man who I met yesterday.", "我们来看这个句子，He is the man who I meet yesterday."),
    ("所以这里要用关系代词which，不能用that。", "所以这里要用关系代词wich，不能用that。"),
    ("我们再来看一个例子，这个例子比较简单。", "我们在来看一个例子，这个例子比较简单。"),
    ("这个词在句子里面作表语，大家要记住。", "这个词在句子里面作表雨，大家要记住。"),
    ("我们先来看一下定语从句的先行词是什么。", "我们先来看一下定语从句的先行次是什么。"),
    ("这个动词是及物动词，后面要接宾语。", "这个动词是急物动词，后面要接宾雨。"),
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
