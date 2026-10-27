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
    import 速查表 as _SC   # S4：重点词速查表要有“本文义 + 词性 + 词义 + 例子”，不能只有“本文：”（G52：与 sync_article 共用同一个判断）
    for w_ in _SC.缺词性(t): bad.append(f'S4 速查表缺词性和词义（只有“本文：”）: {w_}')
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
    def d2a(d): c0(d)['align'][0][0]=c0(d)['align'][0][0]+'x'   # G79 门变异：拆了 align≠en、空译文、文章异常断行 这三道门没人发现
    def 空(d): c0(d)['zh']=''; c0(d)['align']=[[a,''] for a,_ in c0(d)['align']]
    造('align 与 en 不一致','D2 align',fd=d2a); 造('空译文','空译文',fd=空)
    造('文章英文异常断行','D1 文章英文',ft=lambda t:re.sub(r'(## 英文[^\n]*\n(?:\s*\n)*[^\n]+)', r'\1\n  **x**', t, count=1))
    造('速查表本文重复','S2',ft=lambda t:t.replace('## 速查表','## 速查表\n| x | 本文：a 本文：b |',1))
    造('速查表只有本文、缺词性','S4',ft=lambda t:t.replace('## 速查表','## 速查表\n| zzz | 本文：只有本文 | 1 |',1))
    if not (同词('dams','dam')=='撞车' and 同词('circulation','circulates') is None): fails.append('没抓到：撞词按屈折变化判（T12）')
    _o=json.load(open(f'{os.path.dirname(os.path.abspath(__file__))}/原稿重点词.json'))
    if len(_o)<20 or len(_o.get(os.path.relpath(glob.glob(f'{ROOT}/新版定稿/03-*.md')[0],ROOT),[]))<10: fails.append('原稿重点词.json 缺了或是空的：T12 会把原稿重点词误报成撞词（G18）')
    import tempfile, shutil as _sh   # G30：25 起没有 docx 不误停，23 缺 docx 仍停
    _r = tempfile.mkdtemp(); os.makedirs(f'{_r}/视频/视频'); open(f'{_r}/视频/视频/25.mp4', 'w').close(); open(f'{_r}/视频/视频/23.mp4', 'w').close()
    if 缺文件('25', _r): fails.append('误报：25 起守则17 不出 Word，没有 docx 也报缺（G30）')
    if not any('23-文本.docx' in x for x in 缺文件('23', _r)): fails.append('没抓到：23 缺对照文本 docx（G30）')
    _sh.rmtree(_r, ignore_errors=True)
    return fails
if sys.argv[1:2] in (['--自检'],['--撞车清单'],['--写提醒']):   # --写提醒 NN [--根 目录]（--根 只给 开工记录 自检用临时仓库）
    no=None
else:
    no=sys.argv[1].zfill(2)
    d=json.load(open(sys.argv[2] if len(sys.argv)>2 else f'{ROOT}/视频/脚本/{no}.json'))   # 可指定脚本路径（踩坑核查用工作目录里的脚本）
    md=glob.glob(f'{ROOT}/新版定稿/{no}-*.md')[0]; t=open(md).read()
    bad=查(d,t)
if no: bad += 缺文件(no)   # G30：25 起不要求 docx（守则17）

# 撞词提醒（踩坑总表 T12）：本篇重点词（含短语里的实词）若在其他篇加粗过（同一个词的屈折变化；同根不同词不算，CLAUDE.md 第15条），列出供核对
STOP={'the','and','for','with','into','from','that','this','have','been','about','over','under','after','before','out','off','its','his','her','their'}
def stem(w):   # 旧的粗略词干（只留给自检的兼容项，撞车判断改用 同词()）
    w=w.lower()
    for suf in ('ings','ing','ied','ies','ed','es','s'):
        if w.endswith(suf) and len(w)-len(suf)>=(3 if suf=='s' else 4): return w[:-len(suf)]
    return w
# —— 撞车判断（T12、G32，用户 2026-10-23/24/25）：只有同一个词的时态、复数、三单才算撞车；同根不同词不算（CLAUDE.md 第15条）。
#    2026-10-25 修：旧 stem 把 -ing/-ings/-ed 一律去掉，earn↔earnings、fleet↔fleeting、lodgings↔lodged 被误判成撞车，dose↔doses 反而漏掉。
#    现在：-ing/-ings 形式当独立的词（fleeting、earnings、surroundings）；复数/三单/同一动词的两个时态才算撞车；
#    程序拿不准的（-ing↔-ings 如 proceeding↔proceedings、连字符 built in↔built-in）；原形↔-ed 是同一个动词的时态，算撞车（第15条，2026-10-25 主对话核对）列“待用户判”，不自动当撞车也不自动放过
def 旧键(b):
    ws=词(b); return ' '.join(stem(w) for w in ws) if ws else None
def 单CVC(s): return bool(re.search(r'[^aeiou][aeiou][^aeiouwxy]$', s)) and len(re.findall(r'[aeiouy]+', s))==1
def 词基(w):
    w=w.lower(); b={w}
    if w.endswith(('ing','ings')): return b
    if w.endswith('ies') and len(w)>4: b.add(w[:-3]+'y')
    if w.endswith('es') and len(w)>4 and w[:-2].endswith(('s','x','z','ch','sh','o')): b.add(w[:-2])   # doses→dos 也留（dose 由 -s 得到）；employees 不出 employe
    if w.endswith('s') and not w.endswith('ss') and len(w)>3: b.add(w[:-1])
    if w.endswith('ied') and len(w)>4: b.add(w[:-3]+'y')
    if w.endswith('ed') and len(w)>4:
        if not 单CVC(w[:-2]): b.add(w[:-2])   # scraped 不是 scrap 的过去式（scrap→scrapped 双写）
        if w[:-1].endswith('e') and not w[:-2].endswith('e'): b.add(w[:-1])   # settled→settle；employed 不出 employe
        if len(w)>5 and w[-3]==w[-4]: b.add(w[:-3])   # stopped→stop
    return b
def _同(a, b):
    a, b = a.lower(), b.lower()
    if a==b: return '撞车'
    if (a.endswith('ings') and b==a[:-1]) or (b.endswith('ings') and a==b[:-1]): return '待判'   # proceeding↔proceedings
    if a.endswith(('ing','ings')) or b.endswith(('ing','ings')): return None
    common=词基(a)&词基(b)
    if not common: return None
    return '撞车'
def 词(b):
    ws=re.findall(r"[A-Za-z]+",b)
    if len(ws)==1 and (len(ws[0])<3 or ws[0].lower() in STOP): return None
    return ws or None
虚词={'a','an','the','on','in','to','of','at','by','for','from','with','into','onto','upon','up','down','out','off','over','away','back','about','around','through','as'}
def 实词(b):
    """N（26 会话报，2026-10-25）：短语拆出实词比（去掉介词、小品词、冠词）：hinged on↔hinge on、in vain↔vain 都查得到；
    多个实词的短语照旧按整体比（trade journal ≠ journal，用户 2026-10-16）"""
    ws=re.findall(r"[A-Za-z]+",b); c=[w for w in ws if w.lower() not in 虚词]
    if len(ws)==1: return 词(b)
    return c or None
def _小品(b): return [w.lower() for w in re.findall(r"[A-Za-z]+",b) if w.lower() in 虚词 and w.lower() not in ('a','an','the')]
def 原有(b, orig):
    """原稿就有的重点词：原样在原稿重点词里，或按 T22 扩成短语（hinged → hinged on、vain → in vain：多出来的只是介词、小品词、冠词）"""
    if b.lower() in orig: return True
    c=实词(b); return bool(c) and ' '.join(c).lower() in orig
def 同词(x, y):
    """两个重点词：'撞车'（同一个词）、'待判'（程序拿不准）、None（不同的词）。按实词比：短语对短语、短语对单词都查；多实词短语按整体"""
    a, b = 实词(x), 实词(y)
    vx, vy = (re.findall(r"[A-Za-z]+",s) for s in (x, y))
    if len(vx)>1 and len(vy)>1 and _小品(x)!=_小品(y): return None   # G48（用户 2026-10-25：“这个根本就不算撞车，这完全是两个不同的短语啊”）：短语对短语，介词/小品词不同（bring in↔bring back）是两个词
    if not a or not b or len(a)!=len(b): return None
    r=[_同(p,q) for p,q in zip(a,b)]
    if None in r: return None
    if '待判' in r or ('-' in x)!=('-' in y): return '待判'   # built in↔built-in
    return '撞车'
def ckey(b):   # 分组用（同组里再用 同词 判）：每个实词的前 3 个字母
    ws=实词(b); return ' '.join(w.lower()[:3] for w in ws) if ws else None
T12全篇_起 = 25   # T12（用户 2026-10-24：“这个撞车检查肯定要看整个70篇文章啊……以后撞车检查是为了检查70篇文章。不是说只看这个已经做完的文章”；
                  # 2026-10-25：“查撞车清单是70篇，全部都查给70篇……所有的重点词汇全部都查，不是说只查已经做完的”）：
                  # 25 起，本篇所有重点词和 新版定稿 全部篇目的所有重点词比（做了视频的按脚本，没做的按 md 加粗）；01–24 已定稿的照旧（只比新加的、做了视频的），不回头改，列进撞车清单
def _加粗(t): return re.findall(r'\*\*([^*]+)\*\*',t)
def 篇重点词(n, root=ROOT):
    """第 n 篇的全部重点词（去掉用户同意保留的 allow_clash）：做了视频的按脚本英文，没做的按文章英文加粗"""
    js_=f'{root}/视频/脚本/{n}.json'
    if os.path.exists(js_):
        d_=json.load(open(js_)); ac_={x.lower() for x in d_.get('allow_clash',[])}
        ws=[b for s in d_['sentences'] for c in s['chunks'] for b in _加粗(c['en'])]
    else:
        mds=glob.glob(f'{root}/新版定稿/{n}-*.md'); ac_=set()
        ws=_加粗(open(mds[0]).read().split('## 英文',1)[1].split('## 中文',1)[0]) if mds else []
    return [b for b in dict.fromkeys(ws) if b.lower() not in ac_]
def 他篇(no, root=ROOT, 全=False):
    """{分组键: [(篇号, 原词)]}：别的篇目的重点词"""
    out={}
    for f in glob.glob(f'{root}/新版定稿/[0-9][0-9]-*.md'):
        n=os.path.basename(f)[:2]
        if n==no: continue
        js_=f'{root}/视频/脚本/{n}.json'
        if not os.path.exists(js_) and int(no)<T12全篇_起 and not 全: continue   # 01–24（已定稿，用户说“以后”）：还没做视频的篇目不算，按全部篇目的结果列在撞车清单
        for b in 篇重点词(n, root):
            k=ckey(b)
            if k: out.setdefault(k,[]).append((n,b))
    return out
def 撞车(d, no, others, orig):
    """返回 (撞车, 待判)。25 起本篇所有重点词都比、待判也报；01–24 只比新加的、只报撞车"""
    new_only=int(no)<T12全篇_起; hit, ask = [], []
    ac_={x.lower() for x in d.get('allow_clash',[])}
    for b in dict.fromkeys(b for s in d['sentences'] for c in s['chunks'] for b in _加粗(c['en'])):
        if b.lower() in ac_ or (原有(b, orig) if not new_only else b.lower() in orig): continue   # 原稿就有的重点词（含 T22 扩成的短语）撞车：不去掉、不停，写进制作记录“## 撞车提醒”告诉用户（J，用户 2026-10-25）
        for n, o in others.get(ckey(b) or '', []):
            v=同词(b, o) if not new_only else ('撞车' if 旧键(b) and 旧键(b)==旧键(o) else None)   # 01–24：沿用原先的判法（已定稿的结果不变，按新判法的列进撞车清单）
            if v=='撞车': hit.append(f'{b} 也在第 {n} 篇加粗（{o}）')
            elif v=='待判' and not new_only: ask.append(f'{b} ↔ 第 {n} 篇 {o}')
    return sorted(set(hit)), sorted(set(ask))
_OJ=f'{os.path.dirname(os.path.abspath(__file__))}/原稿重点词.json'
def 提醒项(n, root=ROOT):
    """J（用户 2026-10-25：“这些撞车的词先记住先存着……真正等到我去做那一篇的时候，一定要在那一篇有一个机制提醒我……先不要把它去掉”）：
    本篇原有的重点词（原稿就加粗的；没做视频的篇目全部算原有）和全部 70 篇比，撞车或待判的 [(词, 篇, 别篇的词, 判)]"""
    ws=篇重点词(n, root); mds=glob.glob(f'{root}/新版定稿/{n}-*.md')
    if os.path.exists(f'{root}/视频/脚本/{n}.json') and mds:
        o=set(json.load(open(_OJ)).get(os.path.relpath(mds[0],root),[])) if os.path.exists(_OJ) else set(); ws=[w for w in ws if 原有(w, o)]
    oth=他篇(n, root, 全=True); out=[]
    for b in ws:
        for m,o2 in oth.get(ckey(b) or '',[]):
            v=同词(b,o2)
            if v: out.append((b,m,o2,v))
    return out
def 提醒节(n, root=ROOT):
    it=提醒项(n, root)
    L=['## 撞车提醒',f'（程序生成：python3 视频/工具/check_all.py --写提醒 {n}。用户 2026-10-25：撞车的词先留着、最后统一处理，做到这一篇时要告诉用户。发草稿时把这一节告诉用户。）','']
    L+=[f'- {b}：第 {m} 篇也加粗（{o}）'+('，程序拿不准是不是同一个词，待用户判' if v=='待判' else '') for b,m,o,v in it] or ['- 本篇原有的重点词没有和别篇撞车']
    return '\n'.join(L)+'\n'
def 写提醒(n, root=ROOT):
    p=f'{root}/视频/制作记录/{n}.md'; t=open(p).read() if os.path.exists(p) else ''; sec=提醒节(n, root)
    m=re.search(r'^## 撞车提醒[^\n]*$', t, re.M)   # G46：只认行首整行标题（26 方法设计正文里引了“## 撞车提醒”，从那句冲到下一节）
    if m:
        i=m.start(); j=t.find('\n## ', m.end()); t=t[:i]+sec+(t[j+1:] if j>0 else '')
    else: t=t.rstrip('\n')+('\n\n' if t else '')+sec
    open(p,'w').write(t); return 提醒项(n, root)
def 查提醒(n, root=ROOT):
    """门：本篇原有重点词有撞车，制作记录/NN.md 没有“## 撞车提醒”或漏了哪个词就停"""
    it=提醒项(n, root)
    if not it: return []
    p=f'{root}/视频/制作记录/{n}.md'; t=open(p).read() if os.path.exists(p) else ''
    m_=re.search(r'^## 撞车提醒[^\n]*$', t, re.M)
    if not m_: return [f'T12 撞车提醒没写进 制作记录/{n}.md（本篇原有重点词撞车 {len(it)} 处：先留着、要告诉用户）：python3 视频/工具/check_all.py --写提醒 {n}']
    i=m_.start(); j=t.find('\n## ', m_.end()); s=t[i:j if j>0 else len(t)]
    miss=sorted({b for b,m,o,v in it if not re.search(rf'(?<![A-Za-z]){re.escape(b)}(?![A-Za-z])', s)})
    return [f'T12 撞车提醒漏了：{"、".join(miss)}（重跑 python3 视频/工具/check_all.py --写提醒 {n}）'] if miss else []
def 自检T12():
    import tempfile, shutil as _sh; f=[]; r=tempfile.mkdtemp()
    for x, y, want in [('dose','doses','撞车'), ('slight','slight','撞车'), ('dam','dams','撞车'), ('settled','settles','撞车'), ('earn','earnings',None), ('fleet','fleeting',None),
                       ('circulation','circulates',None), ('lodgings','lodged',None), ('enterprising','enterprises',None), ('engravings','Engraved',None),
                       ('scraped','scrapped',None), ('employees','employed',None), ('stopped','stop','撞车'), ('assess','assessed','撞车'), ('scale','scaled','撞车'), ('walks','walked','撞车'), ('proceedings','proceeding','待判'), ('built in','built-in','待判'), ('trade journal','journal',None), ('hinged on','hinge on','撞车'), ('in vain','vain','撞车'), ('hinged on','hinged','撞车'), ('set foot in','set out to',None), ('brought in','brought back',None), ('set out to','set in',None), ('hinged on','hinge on','撞车'), ('combed through','combed','撞车')]:
        if 同词(x, y)!=want: f.append(f'撞车判断错：{x}↔{y} 判成 {同词(x, y)}，应为 {want}（T12/G32）')
    try:
        os.makedirs(f'{r}/新版定稿'); os.makedirs(f'{r}/视频/脚本')
        open(f'{r}/新版定稿/30-假.md','w').write('## 英文\nThe **glaciers** and **circulation** of water.\n## 中文\n')
        d25={'sentences':[{'chunks':[{'en':'Old **glacier** and **circulates**.'}]}]}
        h25,_=撞车(d25,'25',他篇('25', r),set()); h23,_=撞车(d25,'23',他篇('23', r),set())
        if not any('glacier' in x for x in h25): f.append('没抓到：没做视频的第30篇加粗过的词，25 我们新加同一个词不报（T12 全篇）')
        if any('circulates' in x for x in h25): f.append('误报：同根不同词（circulation↔circulates）算成撞车（T12）')
        if h23: f.append('误报：01–24 已定稿的回头查没做视频的篇目（只列撞车清单）')
        os.makedirs(f'{r}/视频/制作记录'); open(f'{r}/新版定稿/26-本.md','w').write('## 英文\nA **glacier** here.\n## 中文\n'); open(f'{r}/视频/制作记录/26.md','w').write('# 26\n\n## 方法设计\nx\n')
        if not 查提醒('26', r): f.append('没抓到：本篇原有重点词撞车，制作记录没有“## 撞车提醒”（J）')
        open(f'{r}/视频/制作记录/26.md','a').write('\n## 撞车提醒\n- 别的词\n')
        if not 查提醒('26', r): f.append('没抓到：撞车提醒漏了撞车的词（J）')
        写提醒('26', r)
        if 查提醒('26', r) or '## 方法设计' not in open(f'{r}/视频/制作记录/26.md').read(): f.append('误报：写了撞车提醒还报，或写提醒冲掉了制作记录别的节（J）')
        h,_=撞车({'sentences':[{'chunks':[{'en':'A **glacier**.'}]}]},'26',他篇('26', r),{'glacier'})
        h2,_=撞车({'sentences':[{'chunks':[{'en':'It **glaciers on** them.'}]}]},'26',他篇('26', r),{'glaciers'})
        if h2: f.append('没抓到：原稿重点词按 T22 扩成短语（glaciers → glaciers on）被当成我们新加的、要求不加（N）')
        h3,_=撞车({'sentences':[{'chunks':[{'en':'It **glacier on** them.'}]}]},'26',他篇('26', r),set())
        if not h3: f.append('没抓到：短语（glacier on）和别篇单词（glaciers）撞车漏报（N）')
        if h: f.append('误报：原稿就有的重点词撞车被当成要去掉（J：先留着、只提醒）')
        h16,_=撞车({'sentences':[{'chunks':[{'en':'**scaled**'}]}]},'16',{ckey('scale'):[('15','scale')]},set())
        if h16: f.append('误报：01–24 已定稿篇目按新判法被拦（只列撞车清单，不改）')
    finally: _sh.rmtree(r, ignore_errors=True)
    return f
if sys.argv[1:2]==['--写提醒']:
    n=sys.argv[2].zfill(2); _rt=sys.argv[sys.argv.index('--根')+1] if '--根' in sys.argv else ROOT; it=写提醒(n, _rt); print(f'第{n}篇 撞车提醒：{len(it)} 处，已写进 制作记录/{n}.md 的“## 撞车提醒”' + ''.join(f'\n  {b}：第 {m} 篇也加粗（{o}）' + ('，待用户判' if v=='待判' else '') for b,m,o,v in it)); sys.exit(0)
if sys.argv[1:2]==['--撞车清单']:   # G32：70 篇所有重点词两两比，交用户看（01–24 已定稿的只列不改）
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 重查记录 import 已出片; 定=set(已出片())
    nos=sorted(os.path.basename(x)[:2] for x in glob.glob(f'{ROOT}/新版定稿/[0-9][0-9]-*.md'))
    allw=[(n,b) for n in nos for b in 篇重点词(n)]; grp={}
    for n,b in allw:
        k=ckey(b)
        if k: grp.setdefault(k,[]).append((n,b))
    res={'撞车':[], '待判':[]}
    for g in grp.values():
        for i_ in range(len(g)):
            for j_ in range(i_+1,len(g)):
                (n1,b1),(n2,b2)=g[i_],g[j_]
                if n1==n2: continue
                v=同词(b1,b2)
                if v: res[v].append(f'- 第{n1}篇 {b1}{"（已定稿）" if n1 in 定 else ""} ↔ 第{n2}篇 {b2}{"（已定稿）" if n2 in 定 else ""}')
    keep=[]
    for n in nos:
        js=f'{ROOT}/视频/脚本/{n}.json'
        if not os.path.exists(js): continue
        for w in json.load(open(js)).get('allow_clash',[]):
            hits=[f'第{m}篇 {o}' for m,o in 他篇(n, 全=True).get(ckey(w) or '',[]) if 同词(w,o)]
            keep.append(f'- 第{n}篇 {w}{"（已定稿）" if n in 定 else ""}：' + ('、'.join(hits) if hits else '（按现行判法已不撞）'))
    L=['# 撞车清单（程序生成：python3 视频/工具/check_all.py --撞车清单）','',
       '先存着、最后统一处理（用户 2026-10-25：“这些撞车的词先记住先存着……真正等到我去做那一篇的时候……要告诉我……先不要把它去掉”）。做到第NN篇时，程序把本篇的写进 制作记录/NN.md 的“## 撞车提醒”。','',
       f'新版定稿 {len(nos)} 篇、{len(set(b.lower() for _,b in allw))} 个不同重点词（做了视频的按脚本，没做的按文章加粗；用户同意保留的 allow_clash 不算），两两比。只有同一个词的时态、复数、三单算撞车；同根不同词不算（CLAUDE.md 第15条）。',
       '01–24 已定稿的只列不改（用户点名的除外）；25 起正在做的那一篇让（去掉本篇的标记、告诉用户）。','',f'## 撞车（{len(res["撞车"])} 组）','']+(sorted(res['撞车']) or ['（无）'])+['',f'## 待用户判（{len(res["待判"])} 组，程序拿不准：-ing↔-ings、连字符）','']+(sorted(res['待判']) or ['（无）'])+['',f'## 用户同意先保留（allow_clash，{len(keep)} 个）','']+(keep or ['（无）'])
    open(f'{ROOT}/视频/制作记录/撞车清单.md','w').write('\n'.join(L)+'\n'); print(f'撞车清单：撞车 {len(res["撞车"])} 组、待用户判 {len(res["待判"])} 组，写进 制作记录/撞车清单.md'); sys.exit(0)
if no is None:
    _f=自检()+自检T12(); print('check_all 自检：'+('通过（D1/D2/D3/D4/S2/S4/T12 造出来的错全部报出，原样无误报）' if not _f else '失灵！'+'；'.join(_f))); sys.exit(1 if _f else 0)
others=他篇(no)
import subprocess
_of=f'{os.path.dirname(os.path.abspath(__file__))}/原稿重点词.json'   # G18：缺了或没有本篇就停（新容器浅克隆没有原稿提交，原稿重点词会被误报成新撞词）
_oj=json.load(open(_of)) if os.path.exists(_of) else {}
if not _oj.get(os.path.relpath(md,ROOT)): bad.append(f'G18 原稿重点词.json 缺了或没有本篇（{os.path.relpath(md,ROOT)}）：撞词核查会把原稿重点词误报成新撞词')
orig=set(_oj.get(os.path.relpath(md,ROOT),[]))  #   # 原稿（提交 fc50170）的重点词，存成文件：新容器浅克隆没有这个提交，T12 曾因此误报撞词（2026-10-23 第20篇）
warn, ask=撞车(d, no, others, orig)
if int(no)<T12全篇_起: bad+=['T12 新加重点词撞词（按规则应去掉并提醒用户）: '+x for x in warn]
else: bad+=['T12 撞车（25 起我们新加的重点词和全部 70 篇比，撞了一律不加；用户要加的告诉用户，用户说留就写 allow_clash）: '+x for x in warn]
bad+=['T12 待用户判（我们新加的重点词，程序拿不准是不是同一个词；用户判：保留就写进 allow_clash，算撞车就去掉本篇标记）: '+x for x in ask]
if int(no)>=T12全篇_起: bad+=查提醒(no)   # J：原稿就有的重点词撞车先留着，但必须写进 制作记录/NN.md 的“## 撞车提醒”告诉用户
print('\n'.join(bad) if bad else f'第{no}篇：全部检查通过')
sys.exit(1 if bad else 0)
