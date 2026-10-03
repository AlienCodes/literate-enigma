"""老师讲英语语法：句子里的 whose / why / he / way 是对的。FunASR 拼不出英文，听成「户字 / 外 / 喜 / 位」。
自动查错字会不会把对的英文标红、建议改成中文？一键全部文字校正会不会采用？"""
from common import *
from voicetwin.webui.app import _suggest_cell
texts = ["今天我们来讲whose引导的定语从句", "那这个比较特殊的先行词就是way。", "在这个定语从句里面，谓语是give,而主语是he。",
         "关系副词主要有三个，when,where和why。", "whose后面一定要接名词"]
heard = ["今天我们来讲户字引导的定语从句", "那这个比较特殊的先行词就是位", "在这个定语从句里面谓语是给而主语是喜",
         "关系副词主要有三个文威尔和外", "户字后面一定要接名词"]
cfg, project = voice(texts)
fake_engine({f"c{i:03d}": h for i, h in enumerate(heard)})
res = pc.find_suspects(project, cfg)
print("auto check:", res["flagged"], "of", res["checked"], "flagged")
for i in range(len(texts)):
    rid = f"c{i:03d}"
    info = show(project, rid, "auto")
    rec, t = cur(project, rid)
    import re
    print("     button text:", re.sub("<[^>]+>", " ", _suggest_cell(info)).strip())
res = wf.run_transcript_fix(cfg, "v", once=True)
print("one-click adopted:", res["adopted"])
for i in range(len(texts)):
    show(project, f"c{i:03d}", "after one-click")
review.adopt_suggestion(project, "c000")
print("teacher clicks 采用 on row 1 ->", cur(project, "c000")[1])
