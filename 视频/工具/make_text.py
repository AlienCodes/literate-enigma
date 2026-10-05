import json,re,sys,html
import render as R
from make_video import T
d=json.load(open(sys.argv[1])); PAL=T['PAL']
colors={};i=0
for s in d['sentences']:
    for c in s['chunks']:
        for w in re.findall(r'\*\*([^*]+)\*\*',c['en']):
            if w.lower() not in colors: colors[w.lower()]=PAL[i%len(PAL)];i+=1
R.unify_colors(colors,d['sentences'])
rgb=lambda c:'rgb(%d,%d,%d)'%c
def seg(ss,cls):
    return ''.join(f'<b style="color:{rgb(c)}">{html.escape(t)}</b>' if c else html.escape(t) for t,c in ss)
def zhseg(z):
    if '\n' in z: return '<br>'.join(zhseg(x) for x in z.split('\n'))  # 中文格内换行
    ss=R._segs_zh(z,colors); out=[]
    for k,(t,c) in enumerate(ss):
        out.append(f'<b class="kz" style="color:{rgb(c)}">{html.escape(t)}</b>' if c else html.escape(t))
    return ''.join(out)
body=[]; prev=None; para=[]
def flush():
    if para: body.append('<section class="para">'+''.join(para)+'</section>'); para.clear()
for s in d['sentences']:
    if prev is not None and s['para']!=prev: flush()
    prev=s['para']; cs=[]
    for c in s['chunks']:
        cols=''.join('<br>' if e=='\n' else f'<span class="col"><span class="en">{seg(R._segs_en(e,colors),"")}</span><span class="zh">{zhseg(z)}</span></span>' for e,z in c['align'])
        note=f'<div class="note">{html.escape(c["note"].replace("#Y",""))}</div>' if c.get('note') else ''
        cs.append(f'<div class="chunk">{cols}{note}</div>')
    para.append('<div class="sent">'+''.join(cs)+'</div>')
flush()
out=f'''<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{d['no']} · {html.escape(d['title_en'])}</title>
<style>

:root{{--bg1:{rgb(T['BG_TOP'])};--bg2:{rgb(T['BG_BOT'])};--en:{rgb(T['FG_EN'])};--zh:{rgb(T['FG_ZH'])};--dim:{rgb(T['DIM'])}}}
body{{margin:0;background:linear-gradient(var(--bg1),var(--bg2));background-attachment:fixed;color:var(--en);font-family:Inter,"Noto Sans SC","PingFang SC",sans-serif;padding:32px 16px}}
main{{max-width:1100px;margin:auto}}
h1{{text-align:center;font-size:34px;margin:0 0 6px}} .tzh{{text-align:center;color:var(--zh);font-size:22px;margin-bottom:36px}}
.no{{color:var(--dim);text-align:center;font-size:14px;letter-spacing:.1em}}
.para{{margin:0 0 34px}} .sent{{margin:0 0 22px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,.06)}}
.chunk{{text-align:center;margin:6px 0 10px}}
.col{{display:inline-flex;flex-direction:column;align-items:center;margin:4px 9px;vertical-align:top}}
.en{{font-size:24px;font-weight:600;white-space:nowrap}} .zh{{font-size:16px;color:var(--zh);margin-top:2px}}
.zh b{{font-weight:600;margin:0 .2em}} .note{{color:var(--zh);font-size:15px;margin-top:4px}}
@media print{{body{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style></head><body><main>
<div class="no">{d['no']}</div><h1>{html.escape(d['title_en'])}</h1><div class="tzh">{html.escape(d['title_zh'])}</div>
{''.join(body)}</main></body></html>'''
open(sys.argv[2],'w').write(out)
