# 复现 proofcheck#3：重复规则不看数字的值
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from voicetwin.data import proofcheck as pc
from voicetwin.utils.textutil import clean_transcript
for raw in ["那么第一种情况 第二种情况我们分别来看", "三月三号 三月四号我们考试", "第一个例句 第二个例句都是定语从句",
            "第一个空第二个空第三个空都填介词", "第一种情况第一种情况我们分别来看", "我们来看一下我们来看一下",
            "第一题第二题", "第三种用法，第四种用法", "三三三", "第一第一第一"]:
    t = clean_transcript(raw)
    ev = pc._repeats(t)
    print(repr(t), [(t[e.start:e.end], e.reason, e.weight) for e in ev])
