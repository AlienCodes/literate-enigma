import sys, os
BLOCK = os.environ.get("BLOCK_PY") == "1"
if BLOCK:
    sys.modules["pypinyin"] = None   # import pypinyin -> ImportError, like install route 2 (.venv)
    sys.modules["jieba"] = None
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf, lexicon_fix as lf
V = "我的声音"
TEXTS = [
    "其次，这个关系待词最常见的使用方式并不是代指某个先行次。",       # 代词->待词, 词->次 (homophones)
    "首先，as这个关系代词，它最经常出现在非限定性定语从句中。",       # clean
    "接下来我们就学习一下另外一个关系代词，艾子，这个关系代词相对来说比较特殊。",  # 艾子 -> as (corrections table)
    "而是代指一整个句子，也就是说 as所代替的一般是整件事情，而非单独某个对向。",   # 对象 -> 对向
    "这个介词一起使用的时候要注意凭借词汇。",
]
def texts(project):
    d = review.load_draft(project)
    return [review.current_values(r, d.get(r["id"]))["text"] for r in project.load_manifest()]
