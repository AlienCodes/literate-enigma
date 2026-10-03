"""g5 复现（纯函数部分）：停顿标记、硬切、开头结尾停顿、错字率、一个汉字开头的英文句子。"""
import sys
import os; sys.path.insert(0, os.environ.get("VT_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[4])))
from voicetwin.synth.script import parse_script, _hard_split
from voicetwin.eval.metrics import cer_details
from voicetwin.utils.textutil import send_lang

print("== synth#1 停顿标记")
for m in ["[停顿=2]", "【停顿=2】", "【停顿】", "[停顿＝2]", "［停顿=2］", "【停顿2秒】"]:
    segs = parse_script(f"第一句话讲完了呢。{m}第二句话开始了。")
    print(repr(m), [(s.text, s.display, s.pause_after) for s in segs])

print("== synth#7 硬切")
for t in ["今天我们要讲的内容是英语考试里面经常出现的各种各样的陷阱和常见错误以及怎么避免它们的方法还有一些别的东西",
          "我们先来看一下第一个例句 然后我们一起来分析它的结构和用法 最后再做几道练习题巩固一下今天学的内容",
          "这个句子里的先行词the beautiful and interesting book on the desk所以要特别注意它的用法和位置"]:
    for s in parse_script(t):
        print(repr(s.text), s.pause_after)
print(_hard_split("一" * 48 + "beautiful" + "二" * 10, 50))

print("== synth#8 开头结尾停顿")
print([(s.text, s.pause_after, s.extra) for s in parse_script("[停顿=3]第一句话在这里讲。")])
print([(s.text, s.pause_after, s.extra) for s in parse_script("第一句话在这里讲。[停顿=3]")])

print("== synth#5 错字率")
for ref, hyp in [("这个考点大约占了30%的分数。", "这个考点大约占了百分之三十的分数"),
                 ("正确率是95%。", "正确率是百分之九十五"),
                 ("上课时间是10:30。", "上课时间是十点半"),
                 ("上课时间是10:35。", "上课时间是十点三十五分"),
                 ("这个考点大约占了30%的分数。", "这个考点大约占了三十的分数"),
                 ("这个考点大约占了30%的分数。", "这个考点大约占了30%的分数")]:
    print(ref, "|", hyp, "->", cer_details(ref, hyp))

print("== proofcheck#4")
for t in ["好，Do you have any brothers or sisters at home?", "好。Do you have any brothers or sisters at home?",
          "比如 I have a sister who is a doctor and she lives in Beijing."]:
    for s in parse_script(t):
        print(repr(s.text), s.lang, "send:", send_lang(s.text, s.lang))
