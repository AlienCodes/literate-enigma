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
        parts=re.findall(r'\S+\s*|\s+',t) if not cjk else ([t] if c not in (None,FG_ZH) else re.findall(r'[A-Za-z0-9.\-]+|.',t))
        units+= [(p,c) for p in parts]
    lines=[[]];wcur=0
    for u,c in units:
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
def draw_lines(d,lines,fnt,y,lh,cx=W/2):
    for ln in lines:
        tw=sum(uw(fnt,u) for u,_ in ln); x=cx-tw/2
        for u,c in ln:
            if u!='\x00': d.text((x,y),u,font=fnt,fill=c)
            x+=uw(fnt,u)
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
    # {{…}} = 只显示不朗读的英文注解，颜色跟随前一个重点词
    out=[]
    for p in re.split(r'(\*\*[^*]+\*\*|\{\{.*?\}\})',t):
        if p.startswith('**'): out.append((p[2:-2],colors.get(p[2:-2].lower())))
        elif p.startswith('{{'): out.append((p[2:-2],out[-1][1] if out else None))
        elif p: out.append((p,None))
    return out
def strip_gloss(t): return re.sub(r'\{\{.*?\}\}','',t)
def _segs_zh(t,colors):
    out=[]
    for p in re.split(r'(\*\*[^*]+\*\*\([^)]*\))',t):
        m=re.match(r'\*\*([^*]+)\*\*\(([^)]*)\)$',p)
        if m: out.append((m.group(1),colors.get(m.group(2).lower())))
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
def _pair_cols(pairs,colors,ef,zf,gapx):
    cols=[]
    for en,zh in pairs:
        se=_segs_en(en,colors); sz=_segs_zh(zh or '',colors)
        we=sum(ef.getlength(t) for t,_ in se); wz=sum(zf.getlength(t) for t,_ in sz)
        cols.append(dict(se=se,sz=sz,we=we,wz=wz,w=max(we,wz)))
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
        if c['w']>maxw:
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
def _measure(chunks,colors,notes,es,grps):
    zs=int(es*ZR); ef=EN(es,600); zf=ZH(zs,500); gapx=int(es*0.36)
    rowsets=[_locked(p,g,colors,ef,zf,gapx) for p,g in zip(chunks,grps)]
    lhE=int(es*1.18); lhZ=int(zs*1.5); rgap=int(es*0.25); cgap=int(es*0.5)
    def rh(r):
        if isinstance(r,tuple):
            c=r[1]; ne=len(layout(c['se'],ef,MAXW2)); nz=len(layout(c['sz'],zf,MAXW2,cjk=True)); return ne*lhE+nz*lhZ
        return lhE+lhZ
    lhN=int(zs*1.45)
    total=sum(sum(rh(r) for r in rs)+(len(rs)-1)*rgap+(lhN if notes[i] else 0) for i,rs in enumerate(rowsets))+cgap*(len(rowsets)-1)
    wide=max([sum(c['w'] for c in r)+gapx*(len(r)-1) for rs in rowsets for r in rs if not isinstance(r,tuple)]+[0])
    nf=ZH(int(zs*0.9),400); wide=max([wide]+[nf.getlength(n.replace('#Y','')) for n in notes if n])
    return rowsets,total,wide,(zs,ef,zf,gapx,lhE,lhZ,rgap,cgap,lhN)
def max_es(chunks,colors,notes=None):
    notes=notes or [None]*len(chunks); grps=_grouping(chunks,colors)
    for es in range(130*S,30,-1):
        _,t,w,_=_measure(chunks,colors,notes,es,grps)
        if t<=MAXH2 and w<=MAXW2: return es
    return 30
def frame_interlinear(chunks,colors,header,progress,out,active=None,maxw=1840,maxh=940,notes=None):
    notes=notes or [None]*len(chunks)
    es=ES_FIXED or max_es(chunks,colors,notes)
    maxw=MAXW2
    rowsets,total,_,(zs,ef,zf,gapx,lhE,lhZ,rgap,cgap,lhN)=_measure(chunks,colors,notes,es,_grouping(chunks,colors))
    im=bg(); d=ImageDraw.Draw(im)
    y=(H-total)/2
    for i,rows in enumerate(rowsets):
        on=(active is None or i==active)
        for r in rows:
            if isinstance(r,tuple):
                c=r[1]
                el=layout([(t,col or FG_EN) for t,col in c['se']],ef,maxw); zl=layout([(t,col or FG_ZH) for t,col in c['sz']],zf,maxw,cjk=True)
                if not on:
                    el=[[(u,dim(cc) if cc else cc) for u,cc in ln] for ln in el]; zl=[[(u,dim(cc) if cc else cc) for u,cc in ln] for ln in zl]
                y=draw_lines(d,el,ef,y,lhE); y=draw_lines(d,zl,zf,y,lhZ); y+=rgap; continue
            tw=sum(c['w'] for c in r)+gapx*(len(r)-1); x=(W-tw)/2
            for c in r:
                xx=x+(c['w']-c['we'])/2
                for t,col in c['se']:
                    f=col or FG_EN; f=f if on else dim(f); d.text((xx,y),t,font=ef,fill=f); xx+=ef.getlength(t)
                xx=x+(c['w']-c['wz'])/2
                for t,col in c['sz']:
                    f=col or FG_ZH; f=f if on else dim(f); d.text((xx,y+lhE),t,font=zf,fill=f); xx+=zf.getlength(t)
                x+=c['w']+gapx
            y+=lhE+lhZ+rgap
        if notes[i]:
            nf=ZH(int(zs*0.9),400); nc=FG_ZH if on else dim(FG_ZH)
            nt=notes[i]
            if nt.startswith('#Y'): nt=nt[2:]; nc=(251,191,36) if on else dim((251,191,36))
            d.text(((W-nf.getlength(nt))/2,y-rgap*0.3),nt,font=nf,fill=nc); y+=lhN
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
def unify_colors(colors,sentences):
    """不连续的重点短语（如 **depends** partly **on** ↔ **取决于**(depends on)）：各部分用同一种颜色。"""
    for s in sentences:
        for c in s['chunks']:
            ens=[w.lower() for w in re.findall(r'\*\*([^*]+)\*\*',c['en'])]
            for k in re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)',c['zh']):
                k=k.lower(); parts=k.split()
                if k in colors or len(parts)<2 or not all(p in ens for p in parts): continue
                col=colors.get(parts[0]); colors[k]=col
                for p in parts: colors[p]=col
    return colors
