import sys
import os; sys.path.insert(0, os.environ.get("VT_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[4])))
from voicetwin.synth.script import parse_script, _hard_split, chunk_sentence
from voicetwin.utils.textutil import syllable_count
T = ["今天我们要讲的内容是英语考试里面经常出现的各种各样的陷阱和常见错误以及怎么避免它们的方法还有一些别的东西",
     "我们先来看一下第一个例句 然后我们一起来分析它的结构和用法 最后再做几道练习题巩固一下今天学的内容 然后我们一起来分析它的结构和用法",
     "这个句子里的先行词是the beautiful and interesting book on the desk next to the window of the classroom所以要特别注意它的用法和位置",
     "一" * 48 + "beautiful" + "二" * 10,
     "一" * 120]
for t in T:
    print([ (p, syllable_count(p)) for p in _hard_split(t, 50)])
    print("  parse:", [(s.text, s.pause_after) for s in parse_script(t)])
s = "，".join(["这是一个比较长的分句用来测试"] * 8) + "。"
print(chunk_sentence(s, 50))
