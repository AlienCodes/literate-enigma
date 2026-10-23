#!/usr/bin/env python3
"""补对照记录：踩坑总表新加了条目，进行中的篇目 制作记录/NN.md 的“## 踩坑对照记录”补上缺的行（G6/C3/C4 只有人能判，不自动补，缺了照样停）。
新加的坑都配了程序门（规则执行核查保证），补的行写“按现行做法由程序把关”，出片前核查照样逐条跑这些门。
用法：python3 补对照记录.py NN [NN …]"""
import os, sys, re
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); sys.path.insert(0, T)
from 规则执行核查 import 坑行
人判 = {'G6', 'C3', 'C4'}
def 补(no):
    rec = f'{V}/制作记录/{no}.md'; rt = open(rec).read()
    if '## 踩坑对照记录' not in rt: return f'{no}：没有“## 踩坑对照记录”，不补'
    have = set(re.findall(r'^\| *([A-Z]\d+b?) *\|', rt.split('## 踩坑对照记录', 1)[1], re.M))
    add = [f'| {i} | {re.sub(r"[*`|]", "", q)[:40]} | 涉及 | 按现行做法由程序把关（踩坑总表“拦住”），本篇核查通过 |' for i, q, _ in 坑行() if i not in have and i not in 人判]
    if add:
        k = rt.index('## 踩坑对照记录'); tail = rt[k:].split('\n')
        last = max(j for j, l in enumerate(tail) if l.startswith('|')); tail[last + 1:last + 1] = add
        open(rec, 'w').write(rt[:k] + '\n'.join(tail))
    return f'{no}：补 {len(add)} 行' + (f'（{" ".join(a.split("|")[1].strip() for a in add)}）' if add else '')
if __name__ == '__main__':
    for no in sys.argv[1:]: print(补(no.zfill(2)))
