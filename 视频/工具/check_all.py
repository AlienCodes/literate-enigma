#!/usr/bin/env python3
"""交付前自动检查：python3 视频/工具/check_all.py NN
对应《踩坑总表》D1–D4、S2、T11 等可自动查的条目。全部通过才能交付。"""
import json,re,sys,glob,os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
no=sys.argv[1].zfill(2); bad=[]
d=json.load(open(f'{ROOT}/视频/脚本/{no}.json'))
md=glob.glob(f'{ROOT}/新版定稿/{no}-*.md')[0]; t=open(md).read()
en=t.split('## 英文',1)[1].split('## 中文',1)[0]
strip=lambda x:re.sub(r'[\*\s]','',x)
paras={}
for s in d['sentences']:
    for c in s['chunks']:
        if '\n' in c['en']: bad.append(f'D1 英文里混入换行标记: {c["en"][:40]}')
        joined=' '.join(a for a,_ in c['align'] if a!='\n')
        if strip(joined)!=strip(c['en']): bad.append(f'D2 align 与 en 不一致: {c["en"][:40]}')
        if ''.join(b for _,b in c['align'])!=c['zh']: bad.append(f'D2 zh 与分组拼接不一致: {c["zh"][:30]}')
        marks={m.lower() for m in re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)',c['zh'])}
        for w in re.findall(r'\*\*([^*]+)\*\*',c['en']):
            if w.lower() not in marks: bad.append(f'D4 重点词缺中文标记: {w}')
        if not c['zh'].strip() and c['en'].strip(): bad.append(f'空译文: {c["en"][:40]}')
    paras.setdefault(s['para'],[]).append(' '.join(c['en'] for c in s['chunks']))
if strip(''.join(' '.join(v) for k,v in sorted(paras.items())))!=strip(en): bad.append('D3 英文与文章原文不一致')
if '\\n' in en or '\n \n' in en.strip(): pass
for line in t.split('## 速查表',1)[1].split('\n'):
    if line.count('本文：')>1: bad.append(f'S2 速查表"本文："重复: {line[:50]}')
if re.search(r'\n {1,}\*\*',en): bad.append('D1 文章英文出现异常断行')
for f in [f'{ROOT}/视频/视频/{no}.mp4',f'{ROOT}/视频/对照文本/{no}-文本.docx']:
    if not os.path.exists(f): bad.append(f'缺文件: {os.path.relpath(f,ROOT)}')
print('\n'.join(bad) if bad else f'第{no}篇：全部检查通过')
sys.exit(1 if bad else 0)
