"""中英混合：FunASR 拼不出英文（写成中文音译），faster-whisper 把中文听成英文。看看会不会把对的英文标红 / 建议改成中文。"""
from common import *
cases = [
    ("我们用Excel的VLOOKUP函数查一下", "我们用一克塞尔的微路卡普函数查一下", "funasr"),
    ("who引导的定语从句修饰人", "户引导的定语从句修饰人", "funasr"),
    ("关系代词which指物，who指人", "关系代词维奇指物户指人", "funasr"),
    ("这里的that不能省略", "这里的贼特不能省略", "funasr"),
    ("这里的that不能省略", "这里的that不能省略", "funasr"),
    ("I am a teacher这句话的主语是I", "爱m a teacher这句话的主语是爱", "funasr"),
    ("先行词是the boy", "先行词是the boy", "funasr"),
    ("先行词是the boy", "先行词是这boy", "funasr"),
    ("我们今天讲定语从句", "we今天讲定语从句", "faster-whisper"),
    ("这个句子的谓语是is", "这个句子的谓语是一次", "funasr"),
    ("用Python写一个for循环", "用派森写一个佛循环", "funasr"),
    ("用Python写一个for循环", "用Python写一个for循环", "faster-whisper"),
    ("这是GPT-SoVITS的模型", "这是GPT so vits的模型", "faster-whisper"),
    ("PPT第3页", "PPT第三页", "funasr"),
    ("50%的同学", "百分之五十的同学", "funasr"),
]
for text, other, eng in cases:
    sus = pc.build_suspect(text, other, None, engine=eng, lang="zh")
    if sus:
        red = [text[s:e] for s, e in sus["spans"]]
        print(f"FLAG {text!r:32} heard={other!r:30} red={red} alt={sus['alt']!r} score={sus['score']}")
    else:
        print(f"ok   {text!r:32} heard={other!r}")
# 只有规则（没有第二个引擎）
for text in ["who引导的定语从句修饰人", "关系代词which指物，who指人", "so我们今天就讲到这里", "she是主格her是宾格", "the是定冠词"]:
    sus = pc.build_suspect(text, None, None, lang="zh")
    print("rules:", text, "->", ([text[s:e] for s, e in sus["spans"]], sus["alt"], sus["reasons"]) if sus else None)
