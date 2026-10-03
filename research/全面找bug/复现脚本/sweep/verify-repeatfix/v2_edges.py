"""修好以后的边界：不该清掉的红字不被清掉；和建议 / 其他红字不冲突（当前代码，只经过 analyze + set_draft + save_rows）。"""
import logging
from common import *
logging.disable(logging.CRITICAL)

def run(label, saved, heard, fixed, save=True):
    cfg, project = voice([saved])
    fake_engine({"c000": heard})
    pc.find_suspects(project, cfg)
    rec, t = cur(project, "c000"); a0 = review.analyze(rec, t)
    review.set_draft(project, "c000", text=fixed)
    rec, t = cur(project, "c000"); a1 = review.analyze(rec, t)
    if save:
        review.save_rows(project)
        rec, t = cur(project, "c000")
    a2 = review.analyze(rec, t)
    f = lambda a, tt: [tt[s:e] for s, e in a["red"]]
    print(f"[{label}] {saved!r} red0={f(a0, a0['text'])} edits0={[(a0['text'][s:e], r) for s,e,r in a0['edits']]}"
          f" -> {fixed!r}: red={f(a2, t)} edits={[(t[s:e], r) for s,e,r in a2['edits']]} undo={[(t[s:e], r) for s,e,r in a2['undo']]}"
          f" active={a2['active']} adopted={a2['adopted']} reasons={a2['reasons'] if (a2['active'] or a2['adopted']) else '-'}")

# 1. 第二个引擎听到的没有重复（有建议），老师自己删掉了重复：不再标红、没有多余的按钮
run("alt+manual", "定语从句定语从句很重要", "定语从句很重要", "定语从句很重要")
# 2. 改了句子别的地方（没碰重复）：红字应该还在
run("other-edit", "这个这个这个函数很重要", "这个这个这个函数很重要", "这个这个这个函数重要")
# 3. 在重复前面加了字（挨着但没改重复）：红字应该还在
run("insert-before", "这个这个这个函数很重要", "这个这个这个函数很重要", "那这个这个这个函数很重要")
# 4. 在重复后面加字（挨着）：红字应该还在
run("insert-after", "看看看这个例子", "看看看这个例子", "看看看了这个例子")
# 5. 删掉重复以后又打回去：红字回来
run("retype", "定语从句定语从句很重要", "定语从句定语从句很重要", "定语从句定语从句很重要")
# 6. 重复 + 另一处红字：删掉重复，另一处还标着
run("two-spans", "这个这个这个 VFIXED 很重要", "这个这个这个 VFIXED 很重要", "这个 VFIXED 很重要")
# 7. 没保存（草稿）也一样
run("unsaved", "看看看这个例子", "看看看这个例子", "看看这个例子", save=False)
# 8. 两处重复，只删掉一处：另一处还在
run("two-repeats", "看看看这个例子这个这个这个很重要", "看看看这个例子这个这个这个很重要", "看看这个例子这个这个这个很重要")
