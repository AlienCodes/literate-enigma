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
            if w.lower() not in marks and not any(w.lower() in m.split() for m in marks): bad.append(f'D4 重点词缺中文标记: {w}')
        if not c['zh'].strip() and c['en'].strip(): bad.append(f'空译文: {c["en"][:40]}')
    paras.setdefault(s['para'],[]).append(' '.join(re.sub(r'\{\{.*?\}\}','',c['en']) for c in s['chunks']))
if strip(''.join(' '.join(v) for k,v in sorted(paras.items())))!=strip(en): bad.append('D3 英文与文章原文不一致')
if '\\n' in en or '\n \n' in en.strip(): pass
for line in t.split('## 速查表',1)[1].split('\n'):
    if line.count('本文：')>1: bad.append(f'S2 速查表"本文："重复: {line[:50]}')
if re.search(r'\n {1,}\*\*',en): bad.append('D1 文章英文出现异常断行')
for f in [f'{ROOT}/视频/视频/{no}.mp4',f'{ROOT}/视频/对照文本/{no}-文本.docx']:
    if not os.path.exists(f): bad.append(f'缺文件: {os.path.relpath(f,ROOT)}')

# 撞词提醒（踩坑总表 T12）：本篇重点词（含短语里的实词）若在其他篇加粗过（同根），列出供核对
STOP={'the','and','for','with','into','from','that','this','have','been','about','over','under','after','before','out','off','its','his','her','their'}
def stem(w):
    w=w.lower()
    for suf in ('ingly','edly','ness','ment','ings','ing','ied','ies','ed','es','ly','s'):
        if w.endswith(suf) and len(w)-len(suf)>=4: return w[:-len(suf)]
    return w
others={}
for f in glob.glob(f'{ROOT}/新版定稿/[0-9][0-9]-*.md'):
    n=os.path.basename(f)[:2]
    if n==no: continue
    e=open(f).read().split('## 英文',1)[1].split('## 中文',1)[0]
    for b in re.findall(r'\*\*([^*]+)\*\*',e):
        for w in re.findall(r"[A-Za-z]+",b):
            if len(w)>=3 and w.lower() not in STOP: others.setdefault(stem(w),set()).add(n)
import subprocess
base=subprocess.run(['git','-C',ROOT,'show','fc50170:'+os.path.relpath(md,ROOT)],capture_output=True,text=True).stdout
orig={b.lower() for b in re.findall(r'\*\*([^*]+)\*\*',base.split('## 中文')[0])}
warn=[]
for s in d['sentences']:
    for c in s['chunks']:
        for b in re.findall(r'\*\*([^*]+)\*\*',c['en']):
            if b.lower() in orig: continue
            if b.lower() in [x.lower() for x in d.get('allow_clash',[])]: continue  # 用户明确要求保留的撞词
            for w in re.findall(r"[A-Za-z]+",b):
                if len(w)>=3 and w.lower() not in STOP and stem(w) in others: warn.append(f'{b}（{w}）也在第 {"、".join(sorted(others[stem(w)]))} 篇加粗')
bad+=['T12 新加重点词撞词（按规则应去掉并提醒用户）: '+x for x in sorted(set(warn))]
print('\n'.join(bad) if bad else f'第{no}篇：全部检查通过')
sys.exit(1 if bad else 0)
