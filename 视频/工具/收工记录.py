#!/usr/bin/env python3
"""收工记录（T31，用户 2026-10-16：“每次你做的所有的事情都要有一个token的消费记录”）：
从 制作记录/NN.md 的“开工时刻：…（UTC）”起，用 token账本.py 算这篇花了多少等效 token、调用几次，写进“## token 记录”。
交付核查 出片后 自动调用（不用记着手动跑）。用法：python3 收工记录.py NN"""
import sys, re, os, subprocess, datetime
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{V}/工具'); import 方法进化表 as JH   # G65
if '--只会话' in sys.argv:   # 改门、主会话没有当前篇：只写本会话的进化记录（篇 = 角色）
    a = sys.argv.index('--只会话'); JH.写会话(sys.argv[a + 1] if len(sys.argv) > a + 1 else (JH.角色() or '会话')); sys.exit(0)
no = sys.argv[1]; V = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); f = f'{V}/制作记录/{no}.md'
s = open(f).read(); m = re.search(r'开工时刻：\s*(\d{4}-\d\d-\d\dT\d\d:\d\d)', s)
if not m: sys.exit(f'【停止】{f} 没有“开工时刻：YYYY-MM-DDTHH:MM（UTC）”，先在“## token 记录”下补上（T31）')
o = subprocess.run(['python3', f'{V}/工具/token账本.py', '--从', m.group(1)], capture_output=True, text=True).stdout.splitlines()
tot = next((l for l in o if l.startswith('全部等效')), '?'); calls = next((l for l in o if l.startswith('调用次数')), '?')
tl = next((l for l in o if l.startswith('按调用的工具')), '')[:120]; drag = next((l for l in o if l.startswith('拖带最多')), '')[:120]
live = '--进行中' in sys.argv     # 每轮结束由钩子自动更新（一边干活一边记），只保留一行，不越记越长
head = '- 进行中（每轮自动更新）' if live else '- 收工'
line = f"{head} {datetime.datetime.utcnow():%Y-%m-%dT%H:%M}（UTC）：{tot.split('（')[0].replace('全部等效 token：', '等效 ')}；{calls.replace('调用次数与平均每次带的上下文： ', '')}｜{tl}｜{drag}｜会话 {JH.会话号()}"
s = re.sub(r'\n- 进行中（每轮自动更新）[^\n]*', '', s)
if '## token 记录' not in s: s = s.rstrip('\n') + '\n\n## token 记录\n'
a = s.index('## token 记录'); b = s.find('\n## ', a + 3); b = len(s) if b < 0 else b
s = s[:b].rstrip('\n') + '\n' + line + '\n' + ('\n' + s[b:].lstrip('\n') if b < len(s) else '')
open(f, 'w').write(s); print(line)
JH.写会话(no, 从=m.group(1)); JH.写表()   # G65：本会话按篇的进化记录（按步骤花费、手工重复、上下文），重写 方法进化表.md
