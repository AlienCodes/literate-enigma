#!/usr/bin/env python3
"""踩坑总表每一行：(编号, 出过的问题, 以后怎么防)。唯一来源：《制作硬性标准与踩坑总结》里的表。"""
import os, re
T = os.path.dirname(os.path.abspath(__file__)); STD = f'{os.path.dirname(T)}/制作硬性标准与踩坑总结.md'
def 坑行(text=None):
    text = open(STD).read() if text is None else text
    out = []
    for line in text.splitlines():
        m = re.match(r'^\| *([A-Z]\d+b?) *\|(.*)\|\s*$', line)
        if m:
            cells = [c.strip() for c in m.group(2).split('|')]
            out.append((m.group(1), cells[0], cells[-1] if len(cells) > 1 else ''))
    return out
