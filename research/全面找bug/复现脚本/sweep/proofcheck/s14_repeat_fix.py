"""识别出来的口误重复（我们我们 / 这个这个这个）被自动查错字标红；老师删掉多余的那个（改对了）以后，红字还在吗？"""
from common import *
cases = [("我们我们今天讲函数", "我们今天讲函数"), ("这个这个这个函数很重要", "这个函数很重要"),
         ("这个这个这个函数很重要", "这个这个函数很重要"), ("看看看这个例子", "看看这个例子"),
         ("就是说就是说我们要注意", "就是说我们要注意"), ("定语从句定语从句很重要", "定语从句很重要")]
for saved, fixed in cases:
    cfg, project = voice([saved])
    fake_engine({"c000": saved})  # 第二个引擎听到的一样（录音里确实说了两遍）
    pc.find_suspects(project, cfg)
    rec, t = cur(project, "c000")
    before = [t[s:e] for s, e in review.analyze(rec, t)["red"]]
    review.set_draft(project, "c000", text=fixed)
    rec, t = cur(project, "c000"); i1 = review.analyze(rec, t)
    review.save_rows(project)
    rec, t = cur(project, "c000"); i2 = review.analyze(rec, t)
    print(f"{saved} red={before} -> teacher fixed {fixed!r}: unsaved red={[t[s:e] for s,e in i1['red']]} "
          f"saved red={[t[s:e] for s,e in i2['red']]} reasons={i2['reasons'] if i2['red'] else ''}")
