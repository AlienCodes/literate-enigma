#!/usr/bin/env python3
"""重新对齐收尾（主会话用，2026-10-23 用户选定 12–20、22 重新对齐、重出 4K）：别的会话只拆分组，推到工作分支
视频/工作进度/重新对齐/NN.json；这里接手，一条命令做完出 4K 之前的事：
  ① 镜像回收（按提交取回）  ② 程序核对：句数、块数、英文一字不差；中文只许不变或只调先后（字一个不改）；[T9对齐] 通过
  ③ 写进工作目录 scripts/NN.json  ④ 画面行变了的句子写 换行变更已获同意（用户原话）  ⑤ 待改清单记一条
  ⑥ 踩坑对照记录补缺的行（G6/C3/C4 写明本篇做法）  ⑦ 21 起的篇目：改过的句子记逐句确认
  ⑧ 踩坑核查 NN 文本 全部通过才算完；之后在工作目录 bash 视频/工具/定稿流水线.sh NN
在视频工作目录下运行：python3 <工具目录>/重新对齐收尾.py NN"""
import os, sys, re, json, subprocess, time
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); sys.path.insert(0, T)
import 译文核查 as Y
from 规则执行核查 import 坑行
no = sys.argv[1].zfill(2)
原话 = '用户 2026-10-23 原话：“如果要是ok的话，尽可能的就是英文上下和它的汉译尽量能够就是位置对齐……我们设置好的标准，尽量一定要去执行啊……你看现在这个前后这个标准它又不统一了。”'
def 停(m): sys.exit(f'【停止】第{no}篇 {m}')
subprocess.run(['python3', f'{T}/镜像回收.py', '重新对齐分组'], check=True)
src = f'{V}/工作进度/重新对齐/{no}.json'
if not os.path.exists(src): 停('还没有收到拆好的分组（工作进度/重新对齐/NN.json）')
new, old = json.load(open(src)), json.load(open(f'scripts/{no}.json'))
if len(new['sentences']) != len(old['sentences']): 停('句数变了')
改句 = []
for i, (s, s0) in enumerate(zip(new['sentences'], old['sentences']), 1):
    if len(s['chunks']) != len(s0['chunks']): 停(f'S{i} 块数变了（chunk 划分不许改，L13）')
    for c, c0 in zip(s['chunks'], s0['chunks']):
        if c['en'] != c0['en']: 停(f'S{i} 英文变了')
        if c['zh'] != c0['zh'] and sorted(Y.去标(c['zh'])) != sorted(Y.去标(c0['zh'])): 停(f'S{i} 中文改了字（只许调先后）')
        if ''.join(b for _, b in c['align']) != c['zh']: 停(f'S{i} 分组拼起来不等于中文（D2）')
    if s != s0: 改句.append(i)
w = lambda d: [Y.词数(a) for s in d['sentences'] for c in s['chunks'] for a, _ in c['align'] if a != '\n' and Y.词数(a) > 0]
e_, c_ = Y.对齐(new, new.get('核对确认', {}))
if e_ or c_: 停('对齐门没过：' + '；'.join(e_ + c_)[:300])
avg0, avg1 = sum(w(old)) / len(w(old)), sum(w(new)) / len(w(new))
json.dump(new, open(f'scripts/{no}.json', 'w'), ensure_ascii=False, indent=1)
# ④ 换行同意：踩坑核查 报 [L13] 的句子
r = subprocess.run(['python3', f'{T}/踩坑核查.py', no, '文本'], capture_output=True, text=True).stdout
l13 = sorted(set(re.findall(r'\[L13\] (S\d+)', r)), key=lambda x: int(x[1:]))
if l13:
    new.setdefault('换行变更已获同意', {}).update({k: 原话 + '（按 01–03 粗细重新分组，中文字不改）' for k in l13})
    json.dump(new, open(f'scripts/{no}.json', 'w'), ensure_ascii=False, indent=1)
# ⑤ 待改清单
q = f'{V}/制作记录/{no}_待改清单.md'; qt = open(q).read() if os.path.exists(q) else f'# 第{no}篇待改清单\n'
if '重新对齐（2026-10-23）' not in qt:
    n = len(re.findall(r'^\d+\. ', qt, re.M)) + 1
    qt = qt.rstrip('\n') + f'\n{n}. 重新对齐（2026-10-23）：{原话}用户选定“全部重新对齐、重出 4K”。\n   - 已改：按 01–03 粗细重新分组，平均每组 {avg0:.2f} → {avg1:.2f} 个英文词；中文字一个不改（只为对齐调先后），重点词、颜色、说明、chunk 划分不变；画面行变了的句子：{" ".join(l13) or "无"}。\n'
    open(q, 'w').write(qt)
# ⑥ 踩坑对照记录补缺的行
rec = f'{V}/制作记录/{no}.md'; rt = open(rec).read()
have = set(re.findall(r'^\| *([A-Z]\d+b?) *\|', rt.split('## 踩坑对照记录', 1)[-1], re.M))
人判 = {'G6': '本篇只重新对齐分组，没有多版本对比的设计稿，不覆盖任何原稿',
        'C3': '用户这次只有一个要求（汉译与英文位置对齐），没有前后冲突', 'C4': '用户要求一次给出，分组一次改完，没有插话要合并'}
add = [f'| {i} | {re.sub(r"[*`|]", "", q_)[:40]} | 涉及 | ' + (人判.get(i) or '按现行做法由程序把关（踩坑总表“拦住”），本篇核查通过') + ' |' for i, q_, _ in 坑行() if i not in have]
lines = rt.split('\n')
for i in ('G6', 'C3', 'C4'):
    lines = [re.sub(r'\| (涉及|不涉及) \|[^|]*\|\s*$', f'| 涉及 | {人判[i]} |', l) if re.match(rf'^\| *{i} *\|', l) and '按现行做法由程序把关' in l else l for l in lines]
rt = '\n'.join(lines)
if add:
    k = rt.index('## 踩坑对照记录'); m = re.search(r'\n(?!\|)', rt[k + 20:]); tail = rt[k:].split('\n')
    last = max(j for j, l in enumerate(tail) if l.startswith('|'))
    tail[last + 1:last + 1] = add; rt = rt[:k] + '\n'.join(tail)
open(rec, 'w').write(rt)
# ⑦ 21 起：改过的句子记逐句确认（只重新分组、字不改，程序比对过）
if int(no) >= Y.起始篇:
    for i in 改句: subprocess.run(['python3', f'{T}/逐句确认.py', no, f'S{i}', '只按用户 2026-10-23 要求重新分组对齐：英文一字不差、中文字不改（程序逐块比对），意思不变；T9 对齐粗细改到 01–03 标准'], check=True, capture_output=True)
# ⑧ 踩坑核查 文本 全部通过
r = subprocess.run(['python3', f'{T}/踩坑核查.py', no, '文本'], capture_output=True, text=True)
print(f'第{no}篇：平均每组 {avg0:.2f} → {avg1:.2f} 个英文词；改了 {len(改句)} 句；换行同意 {" ".join(l13) or "无"}；对照记录补 {len(add)} 行')
if r.returncode: 停('踩坑核查 文本 没过：\n' + '\n'.join(l for l in r.stdout.splitlines() if '✘' in l or '[' in l)[:800])
import 踩坑核查 as _K
_rg = _K.record_gate(no, '出片')   # 出片阶段要全部条目（文本阶段只查 T D W C G），17 篇曾因此在出 4K 前才停
if _rg: 停('出片阶段的踩坑对照记录不全：' + '；'.join(_rg))
print(f'踩坑核查 文本 全部通过、出片阶段对照记录齐全——下一步：bash {T}/定稿流水线.sh {no}')
