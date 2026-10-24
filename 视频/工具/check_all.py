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
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import 破折号 as _PZ   # 例外：文章的破折号换成逗号/冒号/括号（T36）
    if not _PZ.英文一致(' '.join(' '.join(v) for k,v in sorted(paras.items())),en): bad.append('D3 英文与文章原文不一致')
    for line in t.split('## 速查表',1)[1].split('\n'):
        if line.count('本文：')>1: bad.append(f'S2 速查表"本文："重复: {line[:50]}')
    if re.search(r'\n {1,}\*\*',en): bad.append('D1 文章英文出现异常断行')
    for line in t.split('## 速查表',1)[1].split('\n## ',1)[0].split('\n'):   # S4：重点词速查表要有“本文义 + 词性 + 词义 + 例子”，不能只有“本文：”
        m=re.match(r'^\|\s*([^|]+?)\s*\|\s*([^|]*)\|',line)
        if m and '本文：' in m.group(2) and not re.search(r'本文：[^|]*?；\s*(adj|adv|n|v|vt|vi|phr|prep|conj|pron|num|det|abbr|int|interj|aux|modal|art|短语|习语|固定搭配)\.',m.group(2)):
            bad.append(f'S4 速查表缺词性和词义（只有“本文：”）: {m.group(1)}')
    return bad
DOCX_起 = 25   # 守则17（用户 2026-10-24：“以后先不要再去做word或者是PDF了……先只做视频即可”）：25 起没有对照文本 docx 不算缺；
               # 用户要文本时 生成文本.py 出 Word 并逐格读回照查。24 以前照旧要求（G30：25 草稿出片前被“缺 docx”拦住）
def 缺文件(no, root=ROOT):
    fs = [f'{root}/视频/视频/{no}.mp4'] + ([f'{root}/视频/对照文本/{no}-文本.docx'] if int(no) < DOCX_起 else [])
    return [f'缺文件: {os.path.relpath(f, root)}' for f in fs if not os.path.exists(f)]
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
    import tempfile, shutil as _sh   # G30：25 起没有 docx 不误停，23 缺 docx 仍停
    _r = tempfile.mkdtemp(); os.makedirs(f'{_r}/视频/视频'); open(f'{_r}/视频/视频/25.mp4', 'w').close(); open(f'{_r}/视频/视频/23.mp4', 'w').close()
    if 缺文件('25', _r): fails.append('误报：25 起守则17 不出 Word，没有 docx 也报缺（G30）')
    if not any('23-文本.docx' in x for x in 缺文件('23', _r)): fails.append('没抓到：23 缺对照文本 docx（G30）')
    _sh.rmtree(_r, ignore_errors=True)
    return fails
if sys.argv[1:2] in (['--自检'],['--撞车清单']):
    no=None
else:
    no=sys.argv[1].zfill(2)
    d=json.load(open(sys.argv[2] if len(sys.argv)>2 else f'{ROOT}/视频/脚本/{no}.json'))   # 可指定脚本路径（踩坑核查用工作目录里的脚本）
    md=glob.glob(f'{ROOT}/新版定稿/{no}-*.md')[0]; t=open(md).read()
    bad=查(d,t)
if no: bad += 缺文件(no)   # G30：25 起不要求 docx（守则17）

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
T12全篇_起 = 25   # T12（用户 2026-10-24：“这个撞车检查肯定要看整个70篇文章啊……以后撞车检查是为了检查70篇文章。不是说只看这个已经做完的文章”）：
                  # 25 起，新版定稿 全部篇目都比（没做视频的按它 md 里的加粗词）；01–24 已定稿的照旧只比做了视频的（不回头查）
def 他篇(no, root=ROOT, 全=False):
    """{撞词键: {篇号}}：别的篇目在文章英文里加粗过的重点词"""
    out={}
    for f in glob.glob(f'{root}/新版定稿/[0-9][0-9]-*.md'):
        n=os.path.basename(f)[:2]
        if n==no: continue
        js_=f'{root}/视频/脚本/{n}.json'
        if not os.path.exists(js_) and int(no)<T12全篇_起 and not 全: continue   # 24 以前：还没做视频的篇目不算（2026-10-23：33 的 doses 把已定稿的 18 dose 反报成新撞词）
        ac_={x.lower() for x in json.load(open(js_)).get('allow_clash',[])} if os.path.exists(js_) else set()
        e=open(f).read().split('## 英文',1)[1].split('## 中文',1)[0]
        for b in re.findall(r'\*\*([^*]+)\*\*',e):
            if b.lower() in ac_: continue   # 那一篇里用户已同意保留的撞词（如 08 set foot in、set out to），这一对两边都不再报（03 set in 原来被反过来报出）
            k=ckey(b)
            if k: out.setdefault(k,set()).add(n)
    return out
def 自检T12():
    import tempfile, shutil as _sh; f=[]; r=tempfile.mkdtemp()
    try:
        os.makedirs(f'{r}/新版定稿'); os.makedirs(f'{r}/视频/脚本')
        open(f'{r}/新版定稿/30-假.md','w').write('## 英文\nThe **glaciers** and **circulation** of water.\n## 中文\n')
        o25, o23 = 他篇('25', r), 他篇('23', r)
        if ckey('glacier') not in o25: f.append('没抓到：没做视频的第30篇加粗过的词，25 新加同一个词（屈折变化）不报（T12 全篇）')
        if ckey('circulates') in o25: f.append('误报：同根不同词（circulation↔circulates）算成撞车（T12）')
        if ckey('glacier') in o23: f.append('误报：01–24 已定稿的回头查没做视频的篇目（T12 只从 25 起）')
    finally: _sh.rmtree(r, ignore_errors=True)
    return f
def 撞车(d, others, orig):
    warn=[]
    for s in d['sentences']:
        for c in s['chunks']:
            for b in re.findall(r'\*\*([^*]+)\*\*',c['en']):
                if b.lower() in orig: continue
                if b.lower() in [x.lower() for x in d.get('allow_clash',[])]: continue  # 用户明确要求保留的撞词
                k=ckey(b)
                if k in others: warn.append(f'{b} 也在第 {"、".join(sorted(others[k]))} 篇加粗')
    return warn
if sys.argv[1:2]==['--撞车清单']:   # G32：01–24 已定稿不回头改（用户说“以后”），按全部 70 篇的范围会撞车的列出来交用户看
    L=['# 撞车清单（程序生成：python3 视频/工具/check_all.py --撞车清单）','','01–24 已定稿，用户说撞车检查“以后”看整个70篇：这些篇目不改，只列出按全部篇目比会撞车的新加重点词，交用户看。','']
    _oj=json.load(open(f'{os.path.dirname(os.path.abspath(__file__))}/原稿重点词.json')); n_=0
    for n in [f'{i:02d}' for i in range(1,T12全篇_起)]:
        js=f'{ROOT}/视频/脚本/{n}.json'; mds=glob.glob(f'{ROOT}/新版定稿/{n}-*.md')
        if not os.path.exists(js) or not mds: continue
        old=set(撞车(json.load(open(js)), 他篇(n), set(_oj.get(os.path.relpath(mds[0],ROOT),[]))))
        new=sorted(set(撞车(json.load(open(js)), 他篇(n, 全=True), set(_oj.get(os.path.relpath(mds[0],ROOT),[])))) - old)
        if new: L+=[f'- 第{n}篇：'+'；'.join(new)]; n_+=len(new)
    if n_==0: L+=['（无）']
    open(f'{ROOT}/视频/制作记录/撞车清单.md','w').write('\n'.join(L)+'\n'); print(f'撞车清单：01–24 按全部篇目比新多出 {n_} 处，写进 制作记录/撞车清单.md'); sys.exit(0)
if no is None:
    _f=自检()+自检T12(); print('check_all 自检：'+('通过（D1/D2/D3/D4/S2/S4/T12 造出来的错全部报出，原样无误报）' if not _f else '失灵！'+'；'.join(_f))); sys.exit(1 if _f else 0)
others=他篇(no)
import subprocess
_of=f'{os.path.dirname(os.path.abspath(__file__))}/原稿重点词.json'   # G18：缺了或没有本篇就停（新容器浅克隆没有原稿提交，原稿重点词会被误报成新撞词）
_oj=json.load(open(_of)) if os.path.exists(_of) else {}
if not _oj.get(os.path.relpath(md,ROOT)): bad.append(f'G18 原稿重点词.json 缺了或没有本篇（{os.path.relpath(md,ROOT)}）：撞词核查会把原稿重点词误报成新撞词')
orig=set(_oj.get(os.path.relpath(md,ROOT),[]))  #   # 原稿（提交 fc50170）的重点词，存成文件：新容器浅克隆没有这个提交，T12 曾因此误报撞词（2026-10-23 第20篇）
warn=撞车(d, others, orig)
bad+=['T12 新加重点词撞词（按规则应去掉并提醒用户）: '+x for x in sorted(set(warn))]
print('\n'.join(bad) if bad else f'第{no}篇：全部检查通过')
sys.exit(1 if bad else 0)
