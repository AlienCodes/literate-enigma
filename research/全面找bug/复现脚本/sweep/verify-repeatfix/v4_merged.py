"""变体：重复的红字和旁边另一处红字（只隔空格 / 紧挨着）在查错字时被合成一段；老师删掉多余的那遍以后，重复那部分还红吗？"""
import logging
from common import *
logging.disable(logging.CRITICAL)

def run(label, saved, heard, fixed):
    cfg, project = voice([saved])
    fake_engine({"c000": heard})
    pc.find_suspects(project, cfg)
    rec, t = cur(project, "c000")
    sus = rec.get("suspect") or {}
    a0 = review.analyze(rec, t)
    review.set_draft(project, "c000", text=fixed)
    rec1, t1 = cur(project, "c000"); a1 = review.analyze(rec1, t1)
    review.save_rows(project)
    rec2, t2 = cur(project, "c000"); a2 = review.analyze(rec2, t2)
    print(f"[{label}] {saved!r} heard={heard!r} spans={[t[s:e] for s, e in sus.get('spans') or []]} reasons={sus.get('reasons')}\n"
          f"     -> {fixed!r}: unsaved red={[t1[s:e] for s,e in a1['red']]}  saved red={[t2[s:e] for s,e in a2['red']]} "
          f"edits={[(t2[s:e], r) for s,e,r in a2['edits']]} active={a2['active']}\n"
          f"     panel reasons shown: {'；'.join(a2['reasons']) if (a2['active'] or a2['adopted']) else '(none)'}")

run("space-merged", "定语从句定语从句 VFIXED 很重要", "定语从句定语从句 VFIXED 很重要", "定语从句 VFIXED 很重要")
run("space-merged-the", "我们讲 the the the VFIXED 从句", "我们讲 the the the VFIXED 从句", "我们讲 the VFIXED 从句")
run("adjacent-disagree", "看看看这个例子", "看看看那个例子", "看看这个例子")
run("adjacent-disagree2", "这个这个这个函数很重要", "这个这个这个寒暑很重要", "这个函数很重要")
run("adjacent-disagree3", "定语从句定语从句很重要", "定语从句定语从句狠重要", "定语从句很重要")
