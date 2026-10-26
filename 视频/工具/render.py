ES_FIXED=None; ZR=0.72
import re
from PIL import Image,ImageDraw,ImageFont
import os
S=int(os.environ.get("VIDEO_S","1"))  # 1=草稿1080p；定稿时 VIDEO_S=2 出 4K
W,H=1920*S,1080*S
F='fonts/'
def font(path,size,wght=None):
    f=ImageFont.truetype(F+path,size)
    if wght:
        try: f.set_variation_by_axes([wght] if 'Noto' in path else [14,wght] if False else [wght])
        except Exception: pass
    return f
EN=lambda s,w=600: _vf('Inter.ttf',s,w)
ZH=lambda s,w=500: _vf('NotoSansSC.ttf',s,w)
def _vf(p,s,w):
    f=ImageFont.truetype(F+p,s)
    try:
        axes=f.get_variation_axes(); vals=[]
        for a in axes:
            n=a.get('name',b'')
            n=n.decode() if isinstance(n,bytes) else n
            vals.append(w if 'eight' in n or n=='wght' else a.get('default',a['minimum']))
        f.set_variation_by_axes(vals)
    except Exception: pass
    return f
BG_TOP=(11,18,32); BG_BOT=(20,28,48)
FG_EN=(248,250,252); FG_ZH=(176,188,206); DIM=(100,116,139)
PAL=[(251,191,36),(56,189,248),(244,114,182),(74,222,128),(167,139,250),(251,146,60),(45,212,191),(248,113,113)]
def bg():
    im=Image.new('RGB',(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H; d.line([(0,y),(W,y)],fill=tuple(int(BG_TOP[i]*(1-t)+BG_BOT[i]*t) for i in range(3)))
    return im
def tokens_en(s,colors):
    # s with **bold**; returns list of (text,color)
    out=[]
    for i,part in enumerate(re.split(r'(\*\*[^*]+\*\*)',s)):
        if part.startswith('**'):
            w=part[2:-2]; out.append((w,colors.get(w.lower(),FG_EN)))
        elif part: out.append((part,FG_EN))
    return out
def tokens_zh(s,colors):
    out=[]
    for part in re.split(r'(\*\*[^*]+\*\*\([^)]*\))',s):
        m=re.match(r'\*\*([^*]+)\*\*\(([^)]*)\)',part)
        if m:
            out.append(('\x00',None)); out.append((m.group(1),colors.get(m.group(2).lower(),FG_ZH))); out.append(('\x00',None))
        elif part: out.append((part,FG_ZH))
    return out
def uw(fnt,u):
    return fnt.size*0.28 if u=='\x00' else fnt.getlength(u)
def layout(tokens,fnt,maxw,cjk=False):
    # split into words (en) or chars (zh), keep color
    units=[]
    for t,c in tokens:
        if t=='\x00': units.append(('\x00',None)); continue
        if t=='\n': units.append(('\n',None)); continue
        parts=re.findall(r'\S+\s*|\s+',t) if not cjk else ([t] if c not in (None,FG_ZH) else re.findall(r'[A-Za-z0-9.\-]+|.',t))
        units+= [(p,c) for p in parts]
    lines=[[]];wcur=0
    skip=False
    for u,c in units:
        if u=='\n':                                     # {{换行}}：强制换行，去掉行尾空格、下一行开头空格
            while lines[-1] and not lines[-1][-1][0].strip(): lines[-1].pop()
            lines.append([]); wcur=0; skip=True; continue
        if skip:
            u=u.lstrip(); skip=False
            if not u: continue
        w=uw(fnt,u)
        if u!='\x00' and wcur+w>maxw and lines[-1] and u.strip():
            lines.append([]);wcur=0
            u=u.lstrip() if not cjk else u
            w=uw(fnt,u)
        if u=='\x00' and not lines[-1]: continue
        lines[-1].append((u,c)); wcur+=w
    # drop spacer at line ends / next to CJK punctuation
    P='，。、；：！？）」』”'
    out=[]
    for ln in lines:
        while ln and ln[-1][0]=='\x00': ln=ln[:-1]
        clean=[]
        for i,(u,c) in enumerate(ln):
            if u=='\x00':
                nxt=ln[i+1][0] if i+1<len(ln) else ''
                prv=ln[i-1][0] if i>0 else ''
                if nxt[:1] in P or prv[-1:] in '（「『“' or nxt=='\x00': continue
            clean.append((u,c))
        out.append(clean)
    return out
LINKS=[]; NOTE_RULE=[False]
def _nkey(w,colors):
    """说明行用哪个重点词的颜色：原样、小写、首字母大写；都没有再找以它开头的重点词（13 用户写原形：@mount → mounted）"""
    return next((c for c in (w,w.lower(),w.capitalize()) if c in colors),None) or (next((c for c in colors if c.lower().startswith(w.lower())),None) if w else None)
def _note_txt(ln):
    """说明行实际显示的字：去掉 “@词|” 续行颜色标记和 “（@” 里的 @"""
    return re.sub(r'^@[^|（]*\|','',ln).replace('（@','（')
def _link_under(d,units,fnt,y):
    """脚本“连线”里的词组：在这一行里找到（忽略空白），从第一个字到最后一个字下面画一条线，颜色取两头的词色的平均"""
    if not LINKS: return
    cs=[];ix=[]
    for k,(u,c,x) in enumerate(units):
        for ch in u:
            if not ch.isspace() and ch!='\x00': cs.append(ch); ix.append(k)
    s=''.join(cs)
    for ph in LINKS:
        p=re.sub(r'\s','',ph); i=s.find(p)
        if i<0: continue
        a,b=ix[i],ix[i+len(p)-1]; ua,ca,xa=units[a]; ub,cb,xb=units[b]
        x0=xa+uw(fnt,ua)-uw(fnt,ua.lstrip()); x1=xb+fnt.getlength(ub.rstrip())
        col=tuple((p_+q_)//2 for p_,q_ in zip(ca,cb)) if ca and cb else (ca or cb)
        bt=max(d.textbbox((0,0),u_,font=fnt)[3] for u_,_,_ in units[a:b+1] if u_.strip() and u_!='\x00'); yy=y+bt+max(3,fnt.size*0.14)   # 12 用户：线别碰字，按实际字形底边往下留空
        d.line([(x0,yy),(x1,yy)],fill=col,width=max(2,int(fnt.size*0.06)))
def draw_lines(d,lines,fnt,y,lh,cx=W/2):
    for ln in lines:
        tw=sum(uw(fnt,u) for u,_ in ln); x=cx-tw/2; units=[]
        for u,c in ln:
            if u!='\x00': d.text((x,y),u,font=fnt,fill=c)
            units.append((u,c,x)); x+=uw(fnt,u)
        _link_under(d,units,fnt,y)
        y+=lh
    return y
def frame(en,zh,colors,header,progress,out):
    im=bg(); d=ImageDraw.Draw(im)
    hf=EN(28,500); d.text((80,56),header,font=hf,fill=DIM)
    ef=EN(56,600); zf=ZH(42,500)
    el=layout(tokens_en(en,colors),ef,1600); zl=layout(tokens_zh(zh,colors),zf,1600,cjk=True)
    eh=len(el)*80; zh_h=len(zl)*64; total=eh+60+zh_h
    y=(H-total)/2
    y=draw_lines(d,el,ef,y,80)
    d.line([(W/2-60,y+24),(W/2+60,y+24)],fill=(51,65,85),width=3)
    draw_lines(d,zl,zf,y+60,64)
    d.rectangle([0,H-8*S,W*progress,H],fill=(56,189,248))
    im.save(out)

def dim(c,f=0.38,bg=(17,42,35)):
    return tuple(int(bg[i]+(c[i]-bg[i])*f) for i in range(3))
def frame_stack(chunks,colors,header,progress,out,active=None):
    im=bg(); d=ImageDraw.Draw(im)
    d.text((80,56),header,font=EN(28,500),fill=DIM)
    ef=EN(50,600); zf=ZH(36,500)
    blocks=[]
    for e,z in chunks:
        el=layout(tokens_en(e,colors),ef,1640); zl=layout(tokens_zh(z,colors),zf,1640,cjk=True)
        blocks.append((el,zl))
    gap=54
    total=sum(len(el)*68+12+len(zl)*52 for el,zl in blocks)+gap*(len(blocks)-1)
    y=(H-total)/2
    for i,(el,zl) in enumerate(blocks):
        if active is not None and i!=active:
            el=[[(u,dim(c) if c else c) for u,c in ln] for ln in el]; zl=[[(u,dim(c) if c else c) for u,c in ln] for ln in zl]
        y=draw_lines(d,el,ef,y,68); y+=12
        y=draw_lines(d,zl,zf,y,52); y+=gap
    d.rectangle([0,H-8*S,W*progress,H],fill=(94,234,212))
    im.save(out)

def frame_stack_fit(chunks,colors,header,progress,out,active=None,maxw=1760,maxh=860):
  for maxlines in (1,2,3):
    found=False
    for es in range(92,(62 if maxlines==1 else 40),-2):
        zs=int(es*0.74); ef=EN(es,600); zf=ZH(zs,500)
        lhE=int(es*1.28); lhZ=int(zs*1.42); inner=int(es*0.22); gap=int(es*0.85)
        blocks=[(layout(tokens_en(e,colors),ef,maxw),layout(tokens_zh(z,colors),zf,maxw,cjk=True)) for e,z in chunks]
        total=sum(len(el)*lhE+inner+len(zl)*lhZ for el,zl in blocks)+gap*(len(blocks)-1)
        if total<=maxh and all(len(el)<=maxlines and len(zl)<=maxlines for el,zl in blocks): found=True; break
    if found: break
  if True:
    im=bg(); d=ImageDraw.Draw(im)
    y=(H-total)/2+30
    for i,(el,zl) in enumerate(blocks):
        if active is not None and i!=active:
            el=[[(u,dim(c) if c else c) for u,c in ln] for ln in el]; zl=[[(u,dim(c) if c else c) for u,c in ln] for ln in zl]
        y=draw_lines(d,el,ef,y,lhE); y+=inner
        y=draw_lines(d,zl,zf,y,lhZ); y+=gap
    d.rectangle([0,H-8*S,W*progress,H],fill=(94,234,212))
    im.save(out); return es

# ---------- interlinear (word-aligned) layout ----------
def _segs_en(t,colors):
    # {{…}} = 只显示不朗读的英文注解，颜色跟随前一个重点词；{{=}} = 这一格保持一行、不自动折行（不显示、不朗读）；
    # {{一行}} = 这一块（这一行的所有格子）整块排成一行、不折成两行（写在第一格英文开头；不显示、不朗读）。08 S17 用户要求
    # “Henry Whitehead set out to refute Snow but found”保持一行，set out to 下面加了两行彩色说明后格子变宽，会被自动折成两行。
    out=[]
    for p in re.split(r'(\*\*[^*]+\*\*|\{\{.*?\}\})',t):
        if p.startswith('**'): out.append((p[2:-2],colors.get(p[2:-2].lower())))
        elif p in ('{{=}}','{{一行}}'): continue
        elif p=='{{换行}}': out.append(('\n',None))   # 16 S15 用户：英文在这里换行，中文按中文语序整组排在两行英文下面（不显示、不朗读）
        elif p.startswith('{{'): out.append((p[2:-2],out[-1][1] if out else None))
        elif p: out.append((p,None))
    return out
def strip_gloss(t): return re.sub(r'\{\{.*?\}\}','',t)
# 中文标记：**词**(english) = 重点词；{{文字|english}} = 不是重点词、但用该重点词颜色显示的说明（如括号注释）；
# 中文里的 "\n" = 同一格内换行（第二行起居中排在第一行正下方）。
ZCOL=r'\{\{([^|{}]+)\|([^{}]+)\}\}'
def strip_zh(t): return re.sub(ZCOL,r'\1',t).replace('\n','')
def _segs_zh(t,colors):
    out=[]
    for p in re.split(r'(\*\*[^*]+\*\*\([^)]*\)|\{\{[^|{}]+\|[^{}]+\}\})',t):
        m=re.match(r'\*\*([^*]+)\*\*\(([^)]*)\)$',p); m2=re.match(ZCOL+'$',p)
        if m: out.append((m.group(1),colors.get(m.group(2).lower())))
        elif m2: out.append((m2.group(1),colors.get(m2.group(2).lower())))
        elif p: out.append((p,None))
    # 重点词中文两侧留小间隙（标点旁、格子边缘不加）
    PUN='，。、：；！？（）《》“”‘’,.;:!?()… '
    res=[]
    for i,(tx,c) in enumerate(out):
        if c is not None:
            if res and res[-1][0] and res[-1][0][-1] not in PUN and tx[0] not in PUN: res.append((KSP,None))
            res.append((tx,c))
            if i+1<len(out) and out[i+1][0] and out[i+1][0][0] not in PUN and tx[-1] not in PUN: res.append((KSP,None))
        else: res.append((tx,c))
    out=[]
    for tx,c in res:
        if tx==KSP and out and out[-1][0].endswith(KSP): continue
        out.append((tx,c))
    return out
KSP='\u2005'
GLOSS_ANCHOR={}   # 词下说明对齐（11 起）：{说明文字: 对准重点词中心的那个字}；make_video 从各脚本 "词下说明对齐" 读进来。这种说明不计入格宽、可越过格子右边（右边那格这一行是空的）
NOTE_RIGHT={}; _RIGHT_USE={}   # G37：句子英文 → {块（0 起）}：说明放在这一块正文的右侧（只由 说明放右侧特批 打开）
NOTE_WIDE={}   # 英文正文 → 用户特批的说明宽度倍数（L19 例外，只能由 说明放宽特批 打开）
def apply_script(d):
    """画面相关的脚本设置统一从这里读（出片程序和定稿视频核对都调它，两边画出来才一致；11 G9 核对没读到 词下说明对齐，S6 对不上）"""
    GLOSS_ANCHOR.clear(); GLOSS_ANCHOR.update(d.get('词下说明对齐', {}))
    LINKS[:] = d.get('连线', [])
    NOTE_WIDE.clear()   # L19 特批放宽（22 用户 2026-10-23：“经过我的允许，我的特批了，你才可以放宽……可以稍微放宽点，但是不要过于宽”）：只认带用户原话、写明“特批”、倍数 ≤1.5 的句子
    for k_, v_ in d.get('说明放宽特批', {}).items():
        if v_.get('倍数') == '整屏':   # G35（25 用户 2026-10-25 特批：“想方设法能够让整个屏幕的字体就是变得最大”）：结尾简述铺满屏宽，只认 25 起、最后一句、带“（简述：”、依据有用户原话
            ok_ = ('用户' in v_.get('依据', '') and '特批' in v_.get('依据', '') and str(d.get('no', '0')).isdigit() and int(d['no']) >= 25
                   and k_ == f"S{len(d['sentences'])}" and '（简述：' in (d['sentences'][-1]['chunks'][-1].get('note') or ''))
            if not ok_: raise SystemExit(f'【停止】说明放宽特批 {k_} 整屏不合规：只给 25 起最后一句的结尾简述，依据要写用户原话（含“用户”“特批”）（G35）')
        elif not ('用户' in v_.get('依据', '') and '特批' in v_.get('依据', '') and 1 < float(v_.get('倍数', 0)) <= 1.5):
            raise SystemExit(f'【停止】说明放宽特批 {k_} 不合规：依据要写用户原话（含“用户”“特批”），倍数在 1–1.5 之间（用户：“不要过于宽”）')
        NOTE_WIDE[' '.join(p[0] for c in d['sentences'][int(k_[1:]) - 1]['chunks'] for p in c['align'])] = v_['倍数'] if v_['倍数'] == '整屏' else float(v_['倍数'])
    NOTE_RIGHT.clear(); _RIGHT_USE.clear()   # G37（25 用户 2026-10-25：S17 ingenuity 说明放到正文右边，空间全部用上、字号再放大）：只认 25 起、依据带用户原话
    for k_, v_ in d.get('说明放右侧特批', {}).items():
        si_ = int(k_[1:]) - 1; bs_ = v_.get('块', []) if isinstance(v_, dict) else []
        if not (isinstance(v_, dict) and '用户' in v_.get('依据', '') and str(d.get('no', '0')).isdigit() and int(d['no']) >= 25 and 0 <= si_ < len(d['sentences'])
                and bs_ and all(isinstance(b, int) and 1 <= b <= len(d['sentences'][si_]['chunks']) and d['sentences'][si_]['chunks'][b - 1].get('note') for b in bs_)):
            raise SystemExit(f'【停止】说明放右侧特批 {k_} 不合规：只给 25 起、“块”写第几块（那一块要有说明），依据写用户原话（含“用户”，原话记进 用户同意记录.json）（G37）')
        NOTE_RIGHT[' '.join(p[0] for c in d['sentences'][si_]['chunks'] for p in c['align'])] = {b - 1 for b in bs_}
    ALIGN_RULE[0] = str(d.get('no', '0')).isdigit() and int(d.get('no', '0')) >= ALIGN_FROM   # 重点词对正只管 24 起（01–23 定稿画面不变，G9）
    NOTE_RULE[0] = str(d.get('no', '0')).isdigit() and int(d.get('no', '0')) >= 12   # L19 只管 12 起（已定稿的 01–11 画面不变）   # 12 用户：emotional attachment 两词颜色各用各的，下面一条下划线连起来表示是一个整体（中文“情感依恋”同样）
def _pair_cols(pairs,colors,ef,zf,gapx):
    cols=[]
    for en,zh in pairs:
        se=_segs_en(en,colors); zl=[_segs_zh(x,colors) for x in (zh or '').split('\n')]
        sz=[s for l in zl for s in l]; wl=[sum(zf.getlength(t) for t,_ in l) for l in zl]
        we=sum(ef.getlength(t) for t,_ in se); zr_=(zh or '').split('\n')
        wz=max([w_ for w_,r_ in zip(wl,zr_) if not (re.fullmatch(ZCOL,r_.strip()) and re.fullmatch(ZCOL,r_.strip()).group(1) in GLOSS_ANCHOR)] or [0])
        cols.append(dict(se=se,sz=sz,zl=zl,wl=wl,nz=len(zl),we=we,wz=wz,w=max(we,wz),nowrap='{{=}}' in en,brk='{{换行}}' in en,zr=(zh or '').split('\n'),er=en))
    return cols
def _wrap_cols(cols,maxw,gapx):
    g=_wrap_greedy(cols,maxw,gapx); g=[x for x in g if x]
    if len(g)<2 or any(isinstance(x,tuple) for x in g): return g
    tot=sum(c['w'] for c in cols)+gapx*(len(cols)-1); t=tot/len(g)
    while t<maxw:
        b=[x for x in _wrap_greedy(cols,t,gapx) if x]
        if len(b)<=len(g) and not any(isinstance(x,tuple) for x in b): return b
        t+=10
    return g
def _wrap_greedy(cols,maxw,gapx):
    rows=[[]];w=0
    for c in cols:
        if (c['w']>maxw or c.get('brk')) and not c['nowrap']:
            if rows[-1]: rows.append([])
            rows[-1]=('block',c); rows.append([]); w=0; continue
        add=c['w']+(gapx if rows[-1] else 0)
        if rows[-1] and w+add>maxw: rows.append([]); w=0; add=c['w']
        rows[-1].append(c); w+=add
    return rows
def _rows(p,colors,ef,zf,gapx,maxw):
    segs=[[]]
    for a,b in p:
        if a=='\n': segs.append([])
        else: segs[-1].append((a,b))
    out=[]
    for s in segs:
        if s and any('{{一行}}' in a for a,_ in s): out.append(_pair_cols(s,colors,ef,zf,gapx)); continue   # 整块一行（字号由 max_es 缩到放得下）
        if s: out+=[r for r in _wrap_cols(_pair_cols(s,colors,ef,zf,gapx),maxw,gapx) if r]
    return out
LAYOUT_ES=68*S; MAXW2=1860*S; MAXH2=1020*S
def _grouping(chunks,colors):
    es=LAYOUT_ES; ef=EN(es,600); zf=ZH(int(es*ZR),500); gapx=int(es*0.36)
    return [[('B' if isinstance(r,tuple) else len(r)) for r in _rows(p,colors,ef,zf,gapx,1840*S)] for p in chunks]
def _locked(p,grp,colors,ef,zf,gapx):
    cols=_pair_cols([(a,b) for a,b in p if a!='\n'],colors,ef,zf,gapx)
    rows=[];i=0
    for g in grp:
        if g=='B': rows.append(('block',cols[i])); i+=1
        else: rows.append(cols[i:i+g]); i+=g
    return rows
def _分右(n):
    """G37：放右侧的说明只取“（简述：”之前的部分（25 S17 ingenuity 的注释）；简述照旧在正文下面铺满屏宽。返回 (右侧行, 下面行)"""
    ls=n.split('\n'); k=next((j for j,l in enumerate(ls) if l.replace('#Y','').startswith('（简述：')),len(ls)); return ls[:k],ls[k:]
def _rt(rowsets,notes,right):
    return {i for i in right if i<len(notes) and notes[i] and _分右(notes[i])[0] and rowsets[i] and not any(isinstance(r,tuple) for r in rowsets[i])}
def _measure(chunks,colors,notes,es,grps,right=None):
    if right is None: right=_右(chunks,colors,notes)
    zs=int(es*ZR); ef=EN(es,600); zf=ZH(zs,500); gapx=int(es*0.36)
    rowsets=[_locked(p,g,colors,ef,zf,gapx) for p,g in zip(chunks,grps)]
    lhE=int(es*1.18); lhZ=int(zs*1.5); rgap=int(es*0.25); cgap=int(es*0.5)
    def rh(r):
        if isinstance(r,tuple):
            c=r[1]; ne=len(layout(c['se'],ef,MAXW2)); nz=sum(len(layout(l,zf,MAXW2,cjk=True)) for l in c['zl']); return ne*lhE+nz*lhZ
        return lhE+max(c['nz'] for c in r)*lhZ
    lhN=int(zs*1.45)
    total=sum(sum(rh(r) for r in rs)+(len(rs)-1)*rgap+(lhN*len(notes[i].split('\n')) if notes[i] else 0) for i,rs in enumerate(rowsets))+cgap*(len(rowsets)-1)   # note 里的 \n = 用户要的多行说明，每行一行高
    wide=max([sum(c['w'] for c in r)+gapx*(len(r)-1) for rs in rowsets for r in rs if not isinstance(r,tuple)]+[0])
    nf=ZH(int(zs*0.9),400); rt=_rt(rowsets,notes,right)
    if not rt: wide=max([wide]+[nf.getlength(_note_txt(ln)) for n in notes if n for ln in n.replace('#Y','').split('\n')])
    else:   # G37：说明放右侧
        def _rw(rs): return max(sum(c['w'] for c in r)+gapx*(len(r)-1) for r in rs)
        def _nw(ls): return max(nf.getlength(_note_txt(ln.replace('#Y',''))) for ln in ls)
        total=sum((max(sum(rh(r) for r in rs)+(len(rs)-1)*rgap,lhN*len(_分右(notes[i])[0]))+lhN*len(_分右(notes[i])[1]) if i in rt else sum(rh(r) for r in rs)+(len(rs)-1)*rgap+(lhN*len(notes[i].split('\n')) if notes[i] else 0)) for i,rs in enumerate(rowsets))+cgap*(len(rowsets)-1)
        wide=max([sum(c['w'] for c in r)+gapx*(len(r)-1) for i,rs in enumerate(rowsets) if i not in rt for r in rs if not isinstance(r,tuple)]
                 +[_rw(rowsets[i])+int(es*0.6)+_nw(_分右(notes[i])[0]) for i in rt]+[nf.getlength(_note_txt(ln)) for i,n in enumerate(notes) if n for ln in (_分右(n)[1] if i in rt else n.split('\n')) for ln in [ln.replace('#Y','')]]+[0])
    return rowsets,total,wide,(zs,ef,zf,gapx,lhE,lhZ,rgap,cgap,lhN)
def wide_notes(chunks,colors,notes,es):
    """L19（12 用户：说明“不要超过上面的那一行”）：每句的说明行不得比这一句英文正文最宽的一行宽。返回 [(第几组, 说明行, 说明宽, 正文宽)]"""
    rowsets,_,_,(zs,ef,zf,gapx,*_)=_measure(chunks,colors,notes,es,_grouping(chunks,colors)); nf=ZH(int(zs*0.9),400); out=[]
    ew=max([max(sum(uw(ef,u) for u,_ in ln) for ln in layout(r[1]['se'],ef,MAXW2)) if isinstance(r,tuple) else sum(c['we'] for c in r)+gapx*(len(r)-1) for rs in rowsets for r in rs]+[1])
    mul=NOTE_WIDE.get(' '.join(p[0] for ch in chunks for p in ch),1.0)   # 用户特批放宽的句子（apply_script 读 说明放宽特批）
    zp=mul=='整屏'; ew*=(1.0 if zp else mul)   # G35：整屏特批的结尾简述（从“（简述：”那一行起）只受整屏宽限制（max_es 按屏宽缩字号），不比正文
    rt=_rt(rowsets,notes,_右(chunks,colors,notes))
    for i,n in enumerate(notes):
        sk=False
        for ln in ((n or '') if i not in rt else '\n'.join(_分右(n)[1])).replace('#Y','').split('\n'):   # G37：放在正文右侧的说明不在正文下面，L19 只管下面的
            if zp and ln.startswith('（简述：'): sk=True
            if sk: continue
            if ln and nf.getlength(_note_txt(ln))>ew+1: out.append((i,_note_txt(ln),round(nf.getlength(_note_txt(ln))),round(ew)))
    return out
NOTE_PRI={'；': 0, '，': 1, '。': 1, '！': 1, '、': 2, '：': 2}
def 断点(t):
    """说明可以折行的位置 {位置: 优先级}：标点后（下一行不以右括号、右引号开头）；句末补充说明的括号整体放到下一行（说明分行.py 同一套）"""
    bp={i+1:NOTE_PRI[ch] for i,ch in enumerate(t[:-1]) if ch in NOTE_PRI and t[i+1] not in '）”'}
    for i,ch in enumerate(t):
        if ch=='（' and i>0:
            dep=0
            for j in range(i,len(t)):
                dep+={'（':1,'）':-1}.get(t[j],0)
                if dep==0: break
            if re.fullmatch(r'[。）]*',t[j+1:]): bp[i]=1
    return bp
def 折成(t,k,nf,pos):
    """把 t 在 pos（断点）处折成正好 k 行，让最宽的一行最窄；折不成返回 None（不限行数：说明分行 13 S6 以后长说明会超过 6 行）"""
    P=[0]+sorted(x for x in pos if 0<x<len(t))+[len(t)]; n=len(P); W={}
    def w(a,b):
        if (a,b) not in W: W[(a,b)]=nf.getlength(t[P[a]:P[b]])
        return W[(a,b)]
    if k<1 or k>n-1: return None
    INF=float('inf'); dp=[[INF]*n for _ in range(k+1)]; bk=[[0]*n for _ in range(k+1)]; dp[0][0]=0
    for c in range(1,k+1):
        for j in range(1,n):
            for i in range(c-1,j):
                if dp[c-1][i]<INF:
                    v=max(dp[c-1][i],w(i,j))
                    if v<dp[c][j]: dp[c][j]=v; bk[c][j]=i
    if dp[k][n-1]==INF: return None
    seg=[]; j=n-1
    for c in range(k,0,-1): i=bk[c][j]; seg.append(t[P[i]:P[j]]); j=i
    return seg[::-1]
def 简述整屏折行(chunks,colors,notes):
    """G35（25 用户 2026-10-25：“想方设法能够让整个屏幕的字体就是变得最大的这个方案”“以后一定要合理的安排，不要压缩成这个样子”）：
    结尾简述（从“（简述：”起）试 1–24 行的均匀折法，取整屏字号最大的（同字号取行少的）。返回 (字号, 新说明, 行数)"""
    i=next(i for i,n in enumerate(notes) if n and '（简述：' in n); n=notes[i]; a=n.index('（简述：'); head=n[:a]; t=n[a:].replace('\n','')
    nf=ZH(int(int(100*ZR)*0.9),400); pos=sorted(断点(t)); best=None
    for k in range(1,25):
        seg=折成(t,k,nf,pos)
        if not seg: continue
        nn=list(notes); nn[i]=head+'\n'.join(seg); es=min(max_es(chunks,colors,nn),100*S)
        if best is None or es>best[0]: best=(es,nn[i],k)
    return best
def _scan(chunks,colors,notes,grps,right):
    for es in range(130*S,30,-1):
        _,t,w,_=_measure(chunks,colors,notes,es,grps,right)
        if t<=MAXH2 and w<=MAXW2: return es
    return 30
def _右(chunks,colors,notes):
    """G37：这一句实际放右侧的块（用户特批的块里，右侧排法整屏字号更大才用；同一脚本结果固定）"""
    cand=NOTE_RIGHT.get(' '.join(p[0] for ch in chunks for p in ch))
    if not cand: return frozenset()
    nn=list(notes or [None]*len(chunks)); ck=(' '.join(p[0] for ch in chunks for p in ch),tuple(nn))
    if ck not in _RIGHT_USE:
        grps=_grouping(chunks,colors); a=_scan(chunks,colors,nn,grps,frozenset()); b=_scan(chunks,colors,nn,grps,frozenset(cand))
        _RIGHT_USE[ck]=frozenset(cand) if b>a else frozenset()
    return _RIGHT_USE[ck]
def max_es(chunks,colors,notes=None):
    notes=notes or [None]*len(chunks); grps=_grouping(chunks,colors)
    return _scan(chunks,colors,notes,grps,_右(chunks,colors,notes))
def orphan_lines(chunks,colors,notes,es):
    """L3 末行孤词（2026-10-10 08 S17：Henry Whitehead 并进下一行后字号从 62 升到 67，比较结构那一整组 were far more likely to
    succumb to the disease than others, 太宽、整组折行，“others,” 被单独挤到下一行）：按出片同一套排版，找出整组折行后
    最后一行只剩一个英文词的地方，返回 [(第几块, 最后一行的词)]。"""
    notes=notes or [None]*len(chunks)
    rowsets,_,_,(zs,ef,zf,*_)=_measure(chunks,colors,notes,es,_grouping(chunks,colors)); out=[]
    for i,rows in enumerate(rowsets):
        for r in rows:
            if isinstance(r,tuple):
                el=layout([(t,col or FG_EN) for t,col in r[1]['se']],ef,MAXW2)
                if len(el)>1:
                    last=''.join(u for u,_ in el[-1]).split()
                    if len(last)==1: out.append((i+1,last[0]))
    return out
ALIGN_RULE=[False]; ALIGN_FROM=24
def _key_spans(segs,fnt,x0,keys):
    """一行字里每个重点词（按颜色）从最左到最右的范围：{颜色: [左, 右]}；keys = 这一行 ** ** 里的重点词原文"""
    out={}; acc=x0
    for t,col in segs:
        w_=fnt.getlength(t)
        if col is not None and t in keys:
            b=out.setdefault(col,[acc,acc+w_]); b[0]=min(b[0],acc); b[1]=max(b[1],acc+w_)
        acc+=w_
    return out
def _zh_keys(r): return set(re.findall(r'\*\*([^*]+)\*\*\(',r))
def col_place(c,ef,zf,x,align=None):
    """一格里英文起点和每行中文起点（出片程序与 对正量.py 共用）。默认（01–23）：都在格内居中。
    重点词对正（24 起，用户 2026-10-24：“尽量让他放在这个就是正对着这个英文的底下，尽量尽可能在不影响这个整体布局的情况下”）：
    格宽、换行、分组、字一个不动，只在本格内平移英文行和各行中文，让同色中文的中心尽量落在英文重点词中心的正下方
    （总偏移最小；一样小时离原来居中最近）。说明行（词下说明）照旧跟着上一行的词走。"""
    xe0=x+(c['w']-c['we'])/2; xz0=[x+(c['w']-wl)/2 for wl in c['wl']]
    if not (ALIGN_RULE[0] if align is None else align): return xe0,xz0
    ek=_key_spans(c['se'],ef,0,set(re.findall(r'\*\*([^*]+)\*\*',c.get('er','')))); 
    lines=[]
    for k,l in enumerate(c['zl']):
        zk=_key_spans(l,zf,0,_zh_keys(c['zr'][k])); pr=[((ek[col][0]+ek[col][1])/2,(b[0]+b[1])/2) for col,b in zk.items() if col in ek]
        if pr and c['w']-c['wl'][k]>=0 and not (k and re.fullmatch(ZCOL,c['zr'][k].strip())): lines.append((k,pr))
    if not lines: return xe0,xz0
    def best(xe):
        cost=0.0; dev=abs(xe-xe0); pos={}
        for k,pr in lines:
            lo,hi=x,x+c['w']-c['wl'][k]; v=sorted(xe+ce-cz for ce,cz in pr); n=len(v)
            z=min(max(xz0[k],v[(n-1)//2]),v[n//2]); z=min(max(z,lo),hi)
            cost+=sum(abs(xe+ce-z-cz) for ce,cz in pr); dev+=abs(z-xz0[k]); pos[k]=z
        return round(cost,1),round(dev,1),pos
    lo,hi=x,x+c['w']-c['we']; cand={xe0,lo,hi}
    for k,pr in lines:
        for ce,cz in pr:
            for z in (x,x+c['w']-c['wl'][k],xz0[k]): cand.add(z+cz-ce)
    r_=min((best(min(max(e,lo),hi))+(min(max(e,lo),hi),) for e in cand),key=lambda t:(t[0],t[1]))
    xz=list(xz0)
    for k,z in r_[2].items(): xz[k]=z
    return r_[3],xz
def _under_x(c,k,zf,x,px=None):
    """同一格里，第 k 行只有一个说明 {{（…）|key}}、上一行有重点词 **词**(key)：说明的中心对准这个词的中心（不超出这一格）。否则 None（照常居中）"""
    if k==0: return None
    m=re.fullmatch(ZCOL,c['zr'][k].strip())
    if not m: return None
    key=m.group(2).lower(); prev=c['zr'][k-1]; mk=None
    for mm in re.finditer(r'\*\*([^*]+)\*\*\(([^)]*)\)',prev):
        if mm.group(2).lower()==key: mk=mm.group(1); break
    if mk is None: return None
    segs=c['zl'][k-1]; x0=x+(c['w']-c['wl'][k-1])/2 if px is None else px; acc=0.0; cx=None
    for t,_ in segs:
        if t==mk and cx is None: cx=x0+acc+zf.getlength(t)/2
        acc+=zf.getlength(t)
    if cx is None: return None
    wl=c['wl'][k]
    a_=GLOSS_ANCHOR.get(m.group(1)); j_=''.join(t for t,_ in c['zl'][k])
    if a_ and a_ in j_: return max(cx-zf.getlength(j_[:j_.index(a_)])-zf.getlength(a_)/2,x)   # 对准指定的字（11 S6：“人”对准“落子”）
    return min(max(cx-wl/2,x),x+c['w']-wl)
def frame_interlinear(chunks,colors,header,progress,out,active=None,maxw=1840,maxh=940,notes=None):
    notes=notes or [None]*len(chunks)
    es=ES_FIXED or max_es(chunks,colors,notes)
    maxw=MAXW2
    rowsets,total,_,(zs,ef,zf,gapx,lhE,lhZ,rgap,cgap,lhN)=_measure(chunks,colors,notes,es,_grouping(chunks,colors))
    rt=_rt(rowsets,notes,_右(chunks,colors,notes)); nf_=ZH(int(zs*0.9),400)
    im=bg(); d=ImageDraw.Draw(im)
    y=(H-total)/2
    for i,rows in enumerate(rowsets):
        on=(active is None or i==active)
        if i in rt:   # G37：说明放右侧：正文、说明左右并排，整块水平居中，上下各自居中
            h_=sum(lhE+max(c['nz'] for c in r)*lhZ for r in rows)+(len(rows)-1)*rgap; nr_=len(_分右(notes[i])[0]); nh_=lhN*nr_
            rw_=max(sum(c['w'] for c in r)+gapx*(len(r)-1) for r in rows); nw_=max(nf_.getlength(_note_txt(ln.replace('#Y',''))) for ln in _分右(notes[i])[0])
            M_=max(h_,nh_); x0_=(W-(rw_+int(es*0.6)+nw_))/2; top_=y; y=top_+(M_-h_)/2
        for r in rows:
            if isinstance(r,tuple):
                c=r[1]
                el=layout([(t,col or FG_EN) for t,col in c['se']],ef,maxw); zl=[ln for l in c['zl'] for ln in layout([(t,col or FG_ZH) for t,col in l],zf,maxw,cjk=True)]
                if not on:
                    el=[[(u,dim(cc) if cc else cc) for u,cc in ln] for ln in el]; zl=[[(u,dim(cc) if cc else cc) for u,cc in ln] for ln in zl]
                y=draw_lines(d,el,ef,y,lhE); y=draw_lines(d,zl,zf,y,lhZ); y+=rgap; continue
            tw=sum(c['w'] for c in r)+gapx*(len(r)-1); x=(W-tw)/2 if i not in rt else x0_+(rw_-tw)/2
            for c in r:
                xe,xz=col_place(c,ef,zf,x)
                xx=xe
                for t,col in c['se']:
                    f=col or FG_EN; f=f if on else dim(f); d.text((xx,y),t,font=ef,fill=f); xx+=ef.getlength(t)
                for k,(l,wl) in enumerate(zip(c['zl'],c['wl'])):
                    xx=xz[k]
                    ux=_under_x(c,k,zf,x,xz[k-1] if k else None)               # 单独一行的说明：放在它所注的那个词正下方（07 S4 用户要求）
                    if ux is not None: xx=ux
                    for t,col in l:
                        f=col or FG_ZH; f=f if on else dim(f); d.text((xx,y+lhE+k*lhZ),t,font=zf,fill=f); xx+=zf.getlength(t)
                x+=c['w']+gapx
            y+=lhE+max(c['nz'] for c in r)*lhZ+rgap
        if notes[i]:
            nf=ZH(int(zs*0.9),400); nc=FG_ZH if on else dim(FG_ZH)
            nt=notes[i]
            if nt.startswith('#Y'): nt=nt[2:]; nc=(251,191,36) if on else dim((251,191,36))
            ny_=top_+(M_-nh_)/2 if i in rt else None
            for li_,ln in enumerate(nt.split('\n')):
                if i in rt and li_==nr_: y=top_+M_+rgap   # 右侧注释画完，简述接在正文和注释下面
                lc=nc
                if ln.startswith('@') and '|' in ln:                   # 续行：“@extensive|可根据……” 用 extensive 的颜色
                    w_,ln=ln[1:].split('|',1); k_=_nkey(w_,colors)
                    if k_: lc=colors[k_] if on else dim(colors[k_])
                elif ln[1:2]=='@':                                       # 12 用户：说明行用对应重点词的颜色（“（@thorough …）”，@ 不显示）
                    ln=ln[0]+ln[2:]; w_=ln[1:].split(' ')[0]; k_=_nkey(w_,colors)
                    if k_: lc=colors[k_] if on else dim(colors[k_])
                if i in rt and li_<nr_: d.text((x0_+rw_+int(es*0.6),ny_),ln,font=nf,fill=lc); ny_+=lhN; continue
                d.text(((W-nf.getlength(ln))/2,y-rgap*0.3),ln,font=nf,fill=lc); y+=lhN
            if i in rt and nr_==len(nt.split('\n')): y=top_+M_+rgap
        y+=cgap-rgap
    d.rectangle([0,H-8*S,W*progress,H],fill=(94,234,212))
    im.save(out); return es
def frame_title(no,en,zh,out):
    from PIL import ImageDraw
    im=bg(); d=ImageDraw.Draw(im)
    AC=(251,191,36); TE=(94,234,212)
    # fit english title: up to 3 lines, as big as possible
    for es in range(150,60,-4):
        ef=EN(es,800); lines=[[]]
        for w in en.split():
            t=' '.join(lines[-1]+[w])
            if lines[-1] and ef.getlength(t)>1640: lines.append([w])
            else: lines[-1].append(w)
        if len(lines)<=3: break
    lines=[' '.join(l) for l in lines]
    zf=ZH(int(es*0.52),700); kf=ZH(34,700)
    kick=f"考研英语 · 精读  第 {no} 篇"
    lhE=int(es*1.12); hk=60; hz=int(es*0.52*1.4)
    total=hk+len(lines)*lhE+40+8+40+hz
    y=(H-total)/2
    d.text(((W-kf.getlength(kick))/2,y),kick,font=kf,fill=TE); y+=hk
    for l in lines:
        d.text(((W-ef.getlength(l))/2,y),l,font=ef,fill=(250,250,245)); y+=lhE
    y+=40; d.rectangle([W/2-90,y,W/2+90,y+8],fill=AC); y+=48
    d.text(((W-zf.getlength(zh))/2,y),zh,font=zf,fill=AC)
    im.save(out)
def sent_colors(colors,s):
    """这一句用的颜色：句里被隔开的短语（**pegged** … **to** ↔ (pegged to)），各部分按本句的短语取颜色。
    colors 是全篇按英文单词共用的，同一个小词（to）属于两句里不同的短语时，后一个会把前一个覆盖（15 S6 pegged … to 的 to 成了别的颜色）；01–14 没有这种情况，结果不变。"""
    ens=[w.lower() for c in s['chunks'] for w in re.findall(r'\*\*([^*]+)\*\*',c['en'])]; out=None
    for c in s['chunks']:
        for k in re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)',c['zh']):
            k=k.lower(); ps=k.split()
            if len(ps)>1 and k in colors and all(p in ens for p in ps) and any(colors.get(p)!=colors[k] for p in ps):
                out=out or dict(colors)
                for p in ps: out[p]=colors[k]
    return out or colors
def unify_colors(colors,sentences):
    """不连续的重点短语（如 **depends** partly **on** ↔ **取决于**(depends on)）：各部分用同一种颜色。"""
    for s in sentences:
        # 整句一起看：被隔开的短语可以跨块（2026-10-10 10 S16 **elevated** 在第2块、**to** 在第3块，原来按块看，
        # “把……抬高到了……的地位”一个字都没上色，to 还成了另一种颜色——草稿就是这样，我截图核对时才发现）
        ens=[w.lower() for c in s['chunks'] for w in re.findall(r'\*\*([^*]+)\*\*',c['en'])]
        for c in s['chunks']:
            for k in re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)',c['zh']):
                k=k.lower(); parts=k.split()
                if k in colors or len(parts)<2 or not all(p in ens for p in parts): continue
                col=colors.get(parts[0]); colors[k]=col
                for p in parts: colors[p]=col
    # 画面上标了颜色的中文意思（**…**(词)、词下说明 {{…|词}}）必须都找得到颜色，找不到就停（不能让重点词的意思变成白字上屏）
    miss=sorted({k for s in sentences for c in s['chunks'] for k in re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)',c['zh'])+[m[1] for m in re.findall(ZCOL,c['zh'])] if colors.get(k.lower()) is None})
    if miss: raise SystemExit(f'【停止】画面上这些中文意思找不到颜色（英文里对应的词没有加粗，或短语的几部分不在同一句）：{miss}')
    return colors
# —— G49 同屏颜色分得开（用户 2026-10-25 看 26 S10：“ripen into 和rapidly他们的这个颜色太相似了，你换成换成不能这么相似的颜色。”）
#    人眼看重点词主要分色相：ripened into 珊瑚红 0° 和 rapidly 琥珀黄 43° 相邻（CIEDE2000 色差 41，按色差算不小，但两个都是暖色，用户看着像）。
#    25 起（用户 2026-10-26 定稿 25：“所有的东西你按照新规矩来就行了”，起点从 26 移到 25）：同一屏相邻两个重点单元色相差 ≥60°，任意两个 ≥25°（一律，不许重复同色、不设口子；用户 2026-10-25：“以后一定要避免这种情况发生”）。
#    01–24 照旧按全篇顺序轮流取色（定稿画面不变，G9），不合格的列 制作记录/颜色太像清单.md
色相起=25; 相邻色相=60; 同屏色相=25
# 26 起的色板：10 种颜色两两色相差 ≥26°（原 8 色里橙 27° 和琥珀 43° 分不开，换掉橙，加青柠 82°、黄绿 111°、品紫 292°），一屏最多 10 个单元都不用重复（门一律、不设口子）
PAL26=[(248,113,113),(251,191,36),(190,242,100),(120,240,100),(74,222,128),(45,212,191),(56,189,248),(167,139,250),(232,121,249),(244,114,182)]
import colorsys as _cs
def _hue(c): return _cs.rgb_to_hsv(*[x/255 for x in c])[0]*360
def _hd(a,b): d=abs(_hue(a)-_hue(b))%360; return min(d,360-d)
def 句单元(s):
    """这一屏的重点单元（按英文出现顺序）：被隔开的短语（中文标 **…**(a b)）算一个单元，其余每个加粗词一个单元。返回 [(单元键, [组成的词])]"""
    ens=[w.lower() for c in s['chunks'] for w in re.findall(r'\*\*([^*]+)\*\*',c['en'])]; ph={}
    for c in s['chunks']:
        for k in re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)',c['zh']):
            ps=k.lower().split()
            if len(ps)>1 and all(p in ens for p in ps):
                for p in ps: ph.setdefault(p,k.lower())
    out=[]; seen=set()
    for w in ens:
        u=ph.get(w,w)
        if u in seen: continue
        seen.add(u); out.append((u,u.split() if u in ph.values() else [w]))
    return out
def 分色(d):
    """全篇重点词的颜色（unify_colors 之前）。01–25 照旧轮流取色；26 起按色相挑（相邻差最大、同屏差最大、用得少的优先）"""
    colors={}
    if not (str(d.get('no','0')).isdigit() and int(d['no'])>=色相起):
        i=0
        for s in d['sentences']:
            for c in s['chunks']:
                for w in re.findall(r'\*\*([^*]+)\*\*',c['en']):
                    if w.lower() not in colors: colors[w.lower()]=PAL[i%len(PAL)]; i+=1
        return colors
    used={}
    for s in d['sentences']:
        us=句单元(s); got=[colors.get(u) or colors.get(ws[0]) for u,ws in us]
        def ok(j,c,g):   # 放 c 在第 j 个单元：和已放的相邻 ≥60°、和同屏所有已放的 ≥25°（一律，不重复）
            if any(0<=k<len(us) and g[k] is not None and _hd(c,g[k])<相邻色相 for k in (j-1,j+1)): return False
            return all(g[k] is None or k==j or _hd(c,g[k])>=同屏色相 for k in range(len(us)))
        def 排(j,g):   # 回溯：按“和已放的差得越大越好、用得少的优先”的顺序试
            if j==len(us): return g
            if g[j] is not None: return 排(j+1,g)
            cs=sorted(PAL26,key=lambda c:(-min([_hd(c,x) for x in g if x is not None]+[360]),used.get(c,0),PAL26.index(c)))
            for c in cs:
                if ok(j,c,g):
                    g2=list(g); g2[j]=c; r=排(j+1,g2)
                    if r: return r
            return None
        res=排(0,list(got))
        if res is None:   # 找不到（同屏单元超过 10 个、或前面句子定死的颜色冲突）：照贪心放，门会停下交人处理
            res=list(got)
            for j in range(len(us)):
                if res[j] is None: res[j]=max(PAL26,key=lambda c:min([_hd(c,x) for x in res if x is not None]+[360]))
        for (u,ws),c in zip(us,res):
            if colors.get(u) is None and colors.get(ws[0]) is None: used[c]=used.get(c,0)+1
            colors.setdefault(u,c)
            for w in ws: colors.setdefault(w,c)
    return colors
def 同屏色差(d,colors):
    """门（26 起）：每屏相邻两个重点单元色相差 ≥60°，任意两个 ≥25°（超过 7 个单元才许重复用色）。返回问题"""
    if not (str(d.get('no','0')).isdigit() and int(d['no'])>=色相起): return []
    out=[]
    for si,s in enumerate(d['sentences'],1):
        sc=sent_colors(colors,s); us=句单元(s); cs=[(u,sc.get(u) or sc.get(ws[0])) for u,ws in us]
        for (a,ca),(b,cb) in zip(cs,cs[1:]):
            if ca and cb and _hd(ca,cb)<相邻色相: out.append(f'S{si} 相邻的 {a}↔{b} 色相只差 {_hd(ca,cb):.0f}°（要 ≥{相邻色相}°）')
        for (a,ca),(b,cb) in __import__('itertools').combinations(cs,2):
            if ca and cb and _hd(ca,cb)<同屏色相: out.append(f'S{si} 同屏 {a}↔{b} 色相只差 {_hd(ca,cb):.0f}°（要 ≥{同屏色相}°）')
    return sorted(set(out))
