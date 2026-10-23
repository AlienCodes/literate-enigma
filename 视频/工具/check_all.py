#!/usr/bin/env python3
"""交付前自动检查：python3 视频/工具/check_all.py NN
对应《踩坑总表》D1–D4、S2、T11 等可自动查的条目。全部通过才能交付。"""
import json,re,sys,glob,os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
strip=lambda x:re.sub(r'[\*\s]','',x)
def 查(d,t):
    """D1–D4、S2：脚本 d 与文章原文 t 的一致性（自检直接调用）"""
    bad=[]; en=t.split('## 英文',1)[1].split('## 中文',1)[0]; paras={}
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
    for line in t.split('## 速查表',1)[1].split('\n'):
        if line.count('本文：')>1: bad.append(f'S2 速查表"本文："重复: {line[:50]}')
    if re.search(r'\n {1,}\*\*',en): bad.append('D1 文章英文出现异常断行')
    for line in t.split('## 速查表',1)[1].split('\n## ',1)[0].split('\n'):   # S4：重点词速查表要有“本文义 + 词性 + 词义 + 例子”，不能只有“本文：”
        m=re.match(r'^\|\s*([^|]+?)\s*\|\s*([^|]*)\|',line)
        if m and '本文：' in m.group(2) and not re.search(r'本文：[^|]*?；\s*(adj|adv|n|v|vt|vi|phr|prep|conj|pron|num|det|abbr|int|interj|aux|modal|art|短语|习语|固定搭配)\.',m.group(2)):
            bad.append(f'S4 速查表缺词性和词义（只有“本文：”）: {m.group(1)}')
    return bad
def 自检():
    """在第03篇（已定稿）副本里逐一造错，每一种都必须报出；原样不得误报"""
    import copy
    d0=json.load(open(f'{ROOT}/视频/脚本/03.json')); t0=open(glob.glob(f'{ROOT}/新版定稿/03-*.md')[0]).read(); fails=[]
    if 查(d0,t0): fails.append('原样误报：'+'；'.join(查(d0,t0))[:80])
    def 造(name,tag,fd=None,ft=None):
        d=copy.deepcopy(d0); t=t0
        if fd: fd(d)
        if ft: t=ft(t)
        if not any(x.startswith(tag) for x in 查(d,t)): fails.append(f'没抓到：{name}（{tag}）')
    c0=lambda d:d['sentences'][1]['chunks'][0]
    def d1(d): c0(d)['en']=c0(d)['en']+'\n'
    def d2(d): c0(d)['zh']=c0(d)['zh']+'多'
    def d4(d):
        c=next(c for s in d['sentences'] for c in s['chunks'] if re.search(r'\*\*[^*]+\*\*\(',c['zh']))
        c['zh']=re.sub(r'\*\*([^*]+)\*\*\([^)]+\)',r'\1',c['zh'],1); c['align']=[[a,re.sub(r'\*\*([^*]+)\*\*\([^)]+\)',r'\1',b,1)] for a,b in c['align']]
    造('英文混入换行标记','D1',fd=d1); 造('中文与分组拼接不一致','D2',fd=d2); 造('重点词缺中文标记','D4',fd=d4)
    造('英文与文章原文不一致','D3',ft=lambda t:t.replace('## 英文','## 英文\nExtra words here.',1))
    造('速查表本文重复','S2',ft=lambda t:t.replace('## 速查表','## 速查表\n| x | 本文：a 本文：b |',1))
    造('速查表只有本文、缺词性','S4',ft=lambda t:t.replace('## 速查表','## 速查表\n| zzz | 本文：只有本文 | 1 |',1))
    if not (stem('dams')==stem('dam') and stem('circulation')!=stem('circulates')): fails.append('没抓到：撞词按屈折变化判（T12）')
    _o=json.load(open(f'{os.path.dirname(os.path.abspath(__file__))}/原稿重点词.json'))
    if len(_o)<20 or len(_o.get(os.path.relpath(glob.glob(f'{ROOT}/新版定稿/03-*.md')[0],ROOT),[]))<10: fails.append('原稿重点词.json 缺了或是空的：T12 会把原稿重点词误报成撞词（G18）')
    return fails
if sys.argv[1:2]==['--自检']:
    no=None
else:
    no=sys.argv[1].zfill(2)
    d=json.load(open(sys.argv[2] if len(sys.argv)>2 else f'{ROOT}/视频/脚本/{no}.json'))   # 可指定脚本路径（踩坑核查用工作目录里的脚本）
    md=glob.glob(f'{ROOT}/新版定稿/{no}-*.md')[0]; t=open(md).read()
    bad=查(d,t)
for f in ([f'{ROOT}/视频/视频/{no}.mp4',f'{ROOT}/视频/对照文本/{no}-文本.docx'] if no else []):
    if not os.path.exists(f): bad.append(f'缺文件: {os.path.relpath(f,ROOT)}')

# 撞词提醒（踩坑总表 T12）：本篇重点词（含短语里的实词）若在其他篇加粗过（同一个词的屈折变化；同根不同词不算，CLAUDE.md 第15条），列出供核对
STOP={'the','and','for','with','into','from','that','this','have','been','about','over','under','after','before','out','off','its','his','her','their'}
def stem(w):
    w=w.lower()
    # 只去屈折词尾（时态、复数、三单）：用户 2026-10-23“他们并不是一个词，只是同根词……他们也不属于那种就是时态上的变化”——
    # 同根不同词（circulation↔circulates、imprisonment↔imprisoned）不算撞车；同一个词的时态/复数变化（dam↔dams、settled↔settles）才算
    for suf in ('ings','ing','ied','ies','ed','es','s'):
        if w.endswith(suf) and len(w)-len(suf)>=(3 if suf=='s' else 4): return w[:-len(suf)]   # 's' 留 3 个字母：dams→dam（09 dam 撞第47篇 dams，原来查不出）
    return w
assert stem('dams')==stem('dam')=='dam' and stem('drought')=='drought' and stem('settled')==stem('settles') and stem('circulation')!=stem('circulates') and stem('imprisonment')!=stem('imprisoned') and stem('contribution')!=stem('contributed')   # 自检：时态/复数算同一个词，同根不同词不算（用户 2026-10-23）
def ckey(b):
    """撞词按整个重点词比：短语型重点词（trade journal、take first place）是一个整体，组成它的单个词在别篇加粗过不算撞车（用户 2026-10-16：“这是一个短语型词汇……这个不算撞车”）；单词照旧去词尾比（dams = dam）"""
    ws=[w.lower() for w in re.findall(r"[A-Za-z]+",b)]
    if len(ws)==1 and (len(ws[0])<3 or ws[0] in STOP): return None
    return ' '.join(stem(w) for w in ws) or None
assert ckey('trade journal')!=ckey('journal') and ckey('Dams')==ckey('dam') and ckey('set out to')==ckey('Set out to')   # 自检
if no is None:
    _f=自检(); print('check_all 自检：'+('通过（D1/D2/D3/D4/S2/S4/T12 造出来的错全部报出，原样无误报）' if not _f else '失灵！'+'；'.join(_f))); sys.exit(1 if _f else 0)
others={}
for f in glob.glob(f'{ROOT}/新版定稿/[0-9][0-9]-*.md'):
    n=os.path.basename(f)[:2]
    if n==no: continue
    js_=f'{ROOT}/视频/脚本/{n}.json'
    if not os.path.exists(js_): continue   # 还没做视频的篇目（如 33 草稿）不算：撞车由后做的那篇让（2026-10-23：33 的 doses 把已定稿的 18 dose 反报成新撞词）
    ac_={x.lower() for x in json.load(open(js_)).get('allow_clash',[])} if os.path.exists(js_) else set()
    e=open(f).read().split('## 英文',1)[1].split('## 中文',1)[0]
    for b in re.findall(r'\*\*([^*]+)\*\*',e):
        if b.lower() in ac_: continue   # 那一篇里用户已同意保留的撞词（如 08 set foot in、set out to），这一对两边都不再报（03 set in 原来被反过来报出）
        k=ckey(b)
        if k: others.setdefault(k,set()).add(n)
import subprocess
orig=set(json.load(open(f'{os.path.dirname(os.path.abspath(__file__))}/原稿重点词.json')).get(os.path.relpath(md,ROOT),[]))   # 原稿（提交 fc50170）的重点词，存成文件：新容器浅克隆没有这个提交，T12 曾因此误报撞词（2026-10-23 第20篇）
warn=[]
for s in d['sentences']:
    for c in s['chunks']:
        for b in re.findall(r'\*\*([^*]+)\*\*',c['en']):
            if b.lower() in orig: continue
            if b.lower() in [x.lower() for x in d.get('allow_clash',[])]: continue  # 用户明确要求保留的撞词
            k=ckey(b)
            if k in others: warn.append(f'{b} 也在第 {"、".join(sorted(others[k]))} 篇加粗')
bad+=['T12 新加重点词撞词（按规则应去掉并提醒用户）: '+x for x in sorted(set(warn))]
print('\n'.join(bad) if bad else f'第{no}篇：全部检查通过')
sys.exit(1 if bad else 0)
