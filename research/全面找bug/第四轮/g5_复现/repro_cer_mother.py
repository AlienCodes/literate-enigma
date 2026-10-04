"""复查（第二次检查意见 NEW）：生成时的识别校验（错字率）没看母本标准库的对照表（data/lexicon/corrections.txt）。
讲稿写 as、读对了，Whisper 写成「艾子」（对照表里正好有「艾子 => as」）就算 2 个错字。
用法：VT_ROOT=<仓库目录> python repro_cer_mother.py
"""
import os
import sys

sys.path.insert(0, os.environ.get("VT_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[4])))
from voicetwin.eval.metrics import _pinyin_fn, cer_details

print("pypinyin:", _pinyin_fn() is not None)
PAIRS = [
    ("这里的as是介词。", "这里的艾子是介词", "对照表：艾子 => as"),
    ("这里的as是介词。", "这里的艾子是借词", "艾子 => as、借词 => 介词"),
    ("as所引导的定语从句。", "艾子所引导的电影从句", "艾子 => as、电影从句 => 定语从句"),
    ("然后用关系副词 when 引导。", "然后用关系副词问引导", "关系副词问 => 关系副词when"),
    ("这个词是先行词。", "这个词是现行词", "现行词 => 先行词"),
    ("这里的has是动词。", "这里的艾子是动词", "讲稿里没有 as：照样算错"),
    ("这里的as是介词。", "这里的艾子艾子是介词", "多了一个：照样算错"),
    ("我们今天讲十个函数", "我们今天讲个函数", "和母本无关的漏字：照样算错"),
]
for ref, hyp, why in PAIRS:
    rate, err, units = cer_details(ref, hyp, "zh")
    print(f"讲稿「{ref}」 识别「{hyp}」 → 错 {err} / {units}（{rate:.0%}）  {why}")
