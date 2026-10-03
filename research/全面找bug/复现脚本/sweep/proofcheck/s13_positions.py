"""没保存的修改（老师在前面加字 / 删字）以后点自动查错字：红字落在对的字上吗？保存以后呢？"""
from common import *
cases = [("我们今天讲十个函数", "那么我们今天讲十个函数", "我们今天讲是个函数"),
         ("嗯我们今天讲十个函数", "我们今天讲十个函数", "嗯我们今天讲是个函数"),
         ("我们今天讲VFIXED的用法", "好，我们今天讲VFIXED的用法", "我们今天讲v fixed的用法"),
         ("看看看这个十个函数", "看看这个十个函数", "看看看这个是个函数")]
for saved, draft, heard in cases:
    cfg, project = voice([saved])
    fake_engine({"c000": heard})
    review.set_draft(project, "c000", text=draft)
    pc.find_suspects(project, cfg)
    i1 = show(project, "c000", "unsaved")
    review.save_rows(project)
    i2 = show(project, "c000", "saved")
    pc.find_suspects(project, cfg)
    i3 = show(project, "c000", "saved+recheck")
