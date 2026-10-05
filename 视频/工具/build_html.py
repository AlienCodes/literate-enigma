#!/usr/bin/env python3
"""生成「考研英语精读」单文件合集（考研英语精读-70篇.html）。
数据来源：新版定稿/NN-*.md（全部 70 篇）+ 视频/脚本/NN.json（已定稿视频的逐词对照）。
用法：python3 jingdu/tools/build_site.py
"""
import re, json, os, glob, html, shutil
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
OUT=os.path.join(ROOT,'jingdu')
PAL=[(251,191,36),(56,189,248),(244,114,182),(190,242,100),(196,181,253),(251,146,60),(94,234,212),(252,165,165)]
rgb=lambda c:'#%02x%02x%02x'%c
esc=html.escape

CSS="""
:root{--bg1:#0e241e;--bg2:#143028;--en:#f0f7f2;--zh:#aac4b6;--dim:#6e8c7d;--ac:#fbbf24;--te:#5eead4;--card:rgba(255,255,255,.04);--line:rgba(255,255,255,.08)}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;background:linear-gradient(180deg,var(--bg1),var(--bg2)) fixed;color:var(--en);
font-family:Inter,"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.5}
a{color:inherit;text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:28px 16px 80px}
.kick{color:var(--te);font-weight:700;letter-spacing:.08em;font-size:14px;display:flex;align-items:center;gap:14px;justify-content:center}
.kick:before,.kick:after{content:"";width:56px;height:2px;background:var(--te);opacity:.8}
.hero{text-align:center;padding:48px 0 36px;position:relative}
.hero h1{font-weight:900;font-size:clamp(36px,7vw,84px);line-height:1.05;margin:18px 0 18px;letter-spacing:-.01em}
.hl{background:linear-gradient(90deg,#ffd640,#ff7850);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 18px rgba(255,120,80,.35))}
.ghost{background:linear-gradient(90deg,#f8faf6 0%,#f8faf6 35%,rgba(200,255,230,.15) 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.tag{display:inline-block;background:var(--ac);color:#14281f;font-weight:900;border-radius:12px;padding:8px 22px;font-size:clamp(20px,3.4vw,40px)}
.sub{color:var(--zh);margin-top:22px;font-size:15px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-top:28px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;position:relative;transition:.15s;display:block}
.card:hover{border-color:var(--te);transform:translateY(-2px)}
.card .no{font-weight:900;font-size:30px;color:rgba(160,230,200,.25);position:absolute;right:14px;top:6px}
.card .t{font-weight:700;font-size:17px;padding-right:40px}
.card .z{color:var(--ac);font-weight:700;margin-top:6px}
.badge{display:inline-block;margin-top:10px;font-size:12px;font-weight:700;border-radius:6px;padding:2px 8px;background:rgba(94,234,212,.15);color:var(--te)}
.badge.wait{background:rgba(255,255,255,.06);color:var(--dim)}
.nav{display:flex;justify-content:space-between;gap:10px;font-size:14px;color:var(--zh);margin-bottom:8px;flex-wrap:wrap}
.nav a:hover{color:var(--te)}
.tools{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin:6px 0 26px}
.btn{border:1px solid var(--line);background:var(--card);color:var(--en);border-radius:10px;padding:8px 14px;font-size:14px;cursor:pointer;font-family:inherit}
.btn.on{border-color:var(--te);color:var(--te)}
video{width:100%;border-radius:14px;border:1px solid var(--line);background:#000;display:block;margin:0 auto 30px}
.para{margin:0 0 30px;padding-bottom:18px;border-bottom:1px solid var(--line)}
.sent{margin:0 0 18px}
.chunk{text-align:center;margin:4px 0 8px}
.col{display:inline-flex;flex-direction:column;align-items:center;margin:4px 8px;vertical-align:top}
.en{font-size:clamp(17px,2.3vw,26px);font-weight:600;white-space:nowrap}
.zh{font-size:clamp(13px,1.65vw,18px);color:var(--zh);margin-top:2px}
.zh b{font-weight:700;margin:0 .15em}
.note{color:var(--zh);font-size:clamp(12px,1.5vw,16px);margin:2px 0 6px;text-align:center}
.note.y{color:var(--ac)}
.br{flex-basis:100%;height:0;display:block}
.plain p{font-size:clamp(17px,2vw,21px);line-height:1.75;margin:0 0 18px}
.plain p.zhp{color:var(--zh);font-size:clamp(15px,1.8vw,18px);margin-bottom:30px}
.plain b{font-weight:700}
body.hide-zh .zh,body.hide-zh .zhp,body.hide-zh .note{visibility:hidden}
body.hide-en .en,body.hide-en .enp{visibility:hidden}
h2{font-size:20px;margin:40px 0 14px;color:var(--te)}
table{width:100%;border-collapse:collapse;font-size:15px}
td,th{border-bottom:1px solid var(--line);padding:8px 6px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600}
td.w{font-weight:700;white-space:nowrap}
.foot{color:var(--dim);font-size:13px;text-align:center;margin-top:50px}
@media(max-width:640px){.col{margin:3px 5px}.en{white-space:normal}}
"""
FONTS='<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&family=Noto+Sans+SC:wght@400;500;700;900&display=swap" rel="stylesheet">'
def page(title,body,script=''):
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>{FONTS}<link rel="stylesheet" href="style.css"></head><body><div class="wrap">{body}</div>{script}</body></html>'

def parse_md(p):
    t=open(p).read()
    title_en=re.search(r'# EN: (.*)',t).group(1).strip(); title_zh=re.search(r'# ZH: (.*)',t).group(1).strip()
    en=t.split('## 英文',1)[1].split('## 中文',1)[0].strip()
    zh=t.split('## 中文',1)[1].split('## 速查表',1)[0].strip()
    tb=t.split('## 速查表',1)[1].split('\n## ',1)[0]
    rows=re.findall(r'^\| (.+?) \| (.+?) \| (\d+) \|$',tb,re.M)
    return dict(title_en=title_en,title_zh=title_zh,en=[p for p in en.split('\n\n') if p.strip()],zh=[p for p in zh.split('\n\n') if p.strip()],rows=rows)

def colors_for(texts):
    c={};i=0
    for t in texts:
        for w in re.findall(r'\*\*([^*]+)\*\*',t):
            if w.lower() not in c: c[w.lower()]=PAL[i%8]; i+=1
    return c
def en_html(s,c):
    out=[]
    for part in re.split(r'(\*\*[^*]+\*\*)',s):
        if part.startswith('**'): w=part[2:-2]; out.append(f'<b style="color:{rgb(c.get(w.lower(),PAL[0]))}">{esc(w)}</b>')
        else: out.append(esc(part))
    return ''.join(out)
def zh_html(s,c):
    out=[]
    for part in re.split(r'(\*\*[^*]+\*\*\([^)]*\))',s):
        m=re.match(r'\*\*([^*]+)\*\*\(([^)]*)\)$',part)
        if m: out.append(f'<b style="color:{rgb(c.get(m.group(2).lower(),PAL[0]))}" title="{esc(m.group(2))}">{esc(m.group(1))}</b>')
        else: out.append(esc(part))
    return ''.join(out)
def title_html(t,fx):
    out=[]
    for w in t.split():
        k=w.strip(',.')
        cls='hl' if k in fx.get('hl',[]) else 'ghost' if k in fx.get('ghost',[]) else ''
        out.append(f'<span class="{cls}">{esc(w)}</span>' if cls else esc(w))
    return ' '.join(out)

TOGGLE='''<script>
const b=document.body;function set(m){b.classList.remove('hide-zh','hide-en');if(m)b.classList.add(m);
document.querySelectorAll('[data-m]').forEach(x=>x.classList.toggle('on',x.dataset.m===(m||'')));try{localStorage.setItem('jd-mode',m||'')}catch(e){}}
document.querySelectorAll('[data-m]').forEach(x=>x.onclick=()=>set(x.dataset.m));try{set(localStorage.getItem('jd-mode')||'')}catch(e){set('')}
</script>'''

def build():
    files=sorted(glob.glob(os.path.join(ROOT,'新版定稿','[0-9][0-9]-*.md')))
    arts=[]
    for f in files:
        no=os.path.basename(f)[:2]; a=parse_md(f); a['no']=no
        j=os.path.join(ROOT,'视频','脚本',f'{no}.json'); a['json']=json.load(open(j)) if os.path.exists(j) else None
        a['video']=os.path.exists(os.path.join(ROOT,'视频','视频',f'{no}.mp4'))
        arts.append(a)
    cards=''.join(f'''<a class="card" href="#a{a["no"]}"><div class="no">{a["no"]}</div><div class="t">{esc(a["title_en"])}</div><div class="z">{esc(a["title_zh"])}</div>
<span class="badge{'' if a['json'] else ' wait'}">{'视频定稿 · 逐词对照' if a['json'] else '双语全文'}</span></a>''' for a in arts)
    done=sum(1 for a in arts if a['json'])
    parts=[f'''<div class="hero" id="top"><div class="kick">考研英语精读</div><h1>70 Stories Worth <span class="hl">Every Word</span></h1>
<span class="tag">70 篇双语精读 · 3600+ 考研重点词</span><div class="sub">已定稿 {done} / 70 篇 · 持续更新</div></div>
<div class="tools sticky"><button class="btn" data-m="">中英对照</button><button class="btn" data-m="hide-zh">只看英文</button><button class="btn" data-m="hide-en">只看中文</button><a class="btn" href="#top">目录</a></div>
<div class="grid">{cards}</div>''']
    for k,a in enumerate(arts):
        d=a['json']; fx=(d or {}).get('title_fx',{})
        body=f'<article id="a{a["no"]}"><div class="hero"><div class="kick">考研英语精读 · No.{a["no"]}</div><h1>{title_html(a["title_en"],fx)}</h1><span class="tag">{esc(a["title_zh"])}</span></div>'
        if d:
            c=colors_for([ch['en'] for s in d['sentences'] for ch in s['chunks']])
            import sys as _s; _s.path.insert(0,os.path.dirname(__file__)); import render as _R; _R.unify_colors(c,d['sentences'])
            out=[];prevp=None;buf=[]
            for s in d['sentences']:
                if prevp is not None and s['para']!=prevp: out.append('<section class="para">'+''.join(buf)+'</section>'); buf=[]
                prevp=s['para']; cs=[]
                for ch in s['chunks']:
                    cols=''.join('<span class="br"></span>' if e=='\n' else f'<span class="col"><span class="en">{en_html(e,c)}</span><span class="zh">{zh_html(z,c)}</span></span>' for e,z in ch['align'])
                    n=ch.get('note'); nt=f'<div class="note{" y" if n and n.startswith("#Y") else ""}">{esc(n.replace("#Y",""))}</div>' if n else ''
                    cs.append(f'<div class="chunk">{cols}</div>{nt}')
                buf.append('<div class="sent">'+''.join(cs)+'</div>')
            out.append('<section class="para">'+''.join(buf)+'</section>')
            body+=''.join(out)
        else:
            c=colors_for(a['en'])
            body+='<div class="plain">'+''.join(f'<p class="enp">{en_html(e,c)}</p><p class="zhp">{zh_html(z,c)}</p>' for e,z in zip(a['en'],a['zh']))+'</div>'
        trs=''.join(f'<tr><td class="w" style="color:{rgb(c.get(w.lower(),PAL[0]))}">{esc(w)}</td><td>{esc(m)}</td><td>{p}</td></tr>' for w,m,p in a['rows'])
        body+=f'<h2>速查表 · {len(a["rows"])} 词</h2><table><tr><th>词</th><th>释义</th><th>段</th></tr>{trs}</table><div class="nav" style="margin-top:30px"><a href="#top">↑ 回到目录</a></div></article>'
        parts.append(body)
    css=CSS+"article{border-top:2px solid var(--line);margin-top:60px}.sticky{position:sticky;top:0;z-index:5;background:rgba(14,36,30,.92);padding:8px 0;margin:0}"
    doc=f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>考研英语精读 · 70 篇</title><style>{css}</style></head><body><div class="wrap">{"".join(parts)}<div class="foot">每篇重点词英中同色 · 定稿篇目与视频逐词对照一致</div></div>{TOGGLE}</body></html>'
    out=os.path.join(ROOT,'考研英语精读-70篇.html'); open(out,'w').write(doc)
    print('built',out,len(arts),'articles,',done,'finalized',os.path.getsize(out)//1024,'KB')
if __name__=='__main__': build()
