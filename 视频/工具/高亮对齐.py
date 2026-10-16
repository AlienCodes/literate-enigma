#!/usr/bin/env python3
"""高亮对齐（2026-10-16 方法升级）：高亮同步核对报 BAD 的块，若两种独立办法（甲：带时长模型逐帧对齐；乙：每块单独合成拼接逐帧对齐）
给的开口时刻相差 ≤0.05 秒，说明开口很明确，是出片程序估错了——把两者平均值写进脚本 "高亮开始"（成片秒），出片程序直接用；
两种办法不一致的列出来交人看（用实际声音定，写 核对确认.高亮）。用法（视频工作目录，出片后）：python3 <工具目录>/高亮对齐.py NN [--写入]"""
import sys, re, json, subprocess, os
T = os.path.dirname(os.path.abspath(__file__)); no = sys.argv[1]; W = '--写入' in sys.argv
o = subprocess.run(['python3', f'{T}/高亮同步核对.py', no], capture_output=True, text=True).stdout
ov = {}; human = []
for l in o.splitlines():
    m = re.search(r'S(\d+) BAD 第(\d+)块.*?高亮\s+([\d.]+)s\s+开始读 乙\s+([\d.]+)s\s+甲\s+([\d.]+)s', l)
    if not m: continue
    k = f'S{m.group(1)} 第{m.group(2)}块'; y, j = float(m.group(4)), float(m.group(5))
    (ov.__setitem__(k, round((y + j) / 2, 3)) if abs(y - j) <= 0.05 else human.append(f'{k}：高亮 {m.group(3)}  乙 {y}  甲 {j}（两种办法不一致，用实际声音定）'))
print(f'{no} 高亮对齐：两种办法一致、可直接写入 {len(ov)} 块 {ov}；交人看 {len(human)} 块'); [print('  人看', h) for h in human]
if W and ov:
    js = f'scripts/{no}.json'; d = json.load(open(js)); d.setdefault('高亮开始', {}).update(ov); json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1); print('已写进', js)
