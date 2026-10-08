#!/usr/bin/env python3
"""生成并核对一篇的对照文本（Word / HTML / PDF），再拷进仓库 视频/对照文本/。不要手敲命令（W8、W9）。
在视频工作目录（含 scripts/NN.json、render.py、fonts/）下运行：python3 <工具目录>/生成文本.py NN
先过《踩坑核查》（文本阶段），不通过就停止。生成后核对：Word 逐格读回与脚本一致；PDF 是本次生成、文字里有英文标题、不是浏览器错误页；
同一篇的所有 docx 文件名一起覆盖（W7）。最后把脚本同步进仓库 脚本/NN.json，并存为 脚本/已发版本/NN.json（下次比对换行用）。"""
import sys, os, re, json, glob, time, shutil, subprocess
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
no = sys.argv[1].zfill(2); js = os.path.abspath(f'scripts/{no}.json'); d = json.load(open(js))
docx, html, pdf = (os.path.abspath(f'{no}-文本.{x}') for x in ('docx', 'html', 'pdf'))
t0 = time.time(); bad = []
# 最高铁律：先过踩坑核查（含核查程序自检、踩坑对照记录、换行比对），不通过不生成、不发
r = subprocess.run(['python3', f'{T}/踩坑核查.py', no, '文本'], capture_output=True, text=True); print(r.stdout.strip())
if r.returncode: sys.exit('【踩坑核查不通过，不生成、不发给用户】')
subprocess.run(['python3', f'{T}/make_docx.py', js, docx], check=True)
subprocess.run(['python3', f'{T}/make_text.py', js, html], check=True)
if os.path.exists(pdf): os.remove(pdf)
subprocess.run(['/opt/pw-browsers/chromium', '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                f'--print-to-pdf={pdf}', 'file://' + html], capture_output=True)
# Word 逐格读回
from read_docx2 import segs
cells = [(e, ''.join(t for t, _ in z)) for k, v in segs(docx) if k == 'T' for e, z in v]
want = [(re.sub(r'\*\*|\{\{.*?\}\}', '', a), re.sub(r'\*\*|\([A-Za-z \-]+\)|\n', '', re.sub(r'\{\{([^|{}]+)\|[^{}]+\}\}', r'\1', b)))   # 颜色说明 {{文字|词}} 只取文字
        for s in d['sentences'] for c in s['chunks'] for a, b in c['align'] if a != '\n']
ns = lambda x: re.sub(r'\s', '', x)
if len(cells) != len(want): bad.append(f'Word 格数 {len(cells)} ≠ 脚本分组数 {len(want)}')
bad += [f'Word 格不一致：{x} ≠ {y}' for x, y in zip(cells, want) if ns(x[0]) != ns(y[0]) or ns(x[1]) != ns(y[1])][:10]
# PDF
if not os.path.exists(pdf) or os.path.getmtime(pdf) < t0: bad.append('PDF 没有生成（或不是本次生成的）')
else:
    import pymupdf
    txt = ''.join(p.get_text() for p in pymupdf.open(pdf))
    if d['title_en'] not in txt or re.search(r"reached|ERR_|could not be found", txt): bad.append('PDF 内容不对（可能是浏览器错误页，W9）')
if bad: sys.exit('【不通过】\n' + '\n'.join(bad))
dst = f'{T}/../对照文本'
for f in [f'{dst}/{no}-文本.docx'] + glob.glob(f'{dst}/{no}-文本-*.docx'):
    if '用户' in os.path.basename(f): continue          # 用户发回的修正稿不覆盖
    shutil.copy(docx, f)
shutil.copy(html, f'{dst}/{no}-文本.html'); shutil.copy(pdf, f'{dst}/{no}-文本.pdf')
# 脚本同步进仓库，并存为"已发版本"（下次比对换行，L13）；本次用到的换行同意转入记录
if d.get('换行变更已获同意'):
    d.setdefault('换行变更记录', []).append({'日期': time.strftime('%Y-%m-%d'), **d.pop('换行变更已获同意')})
    json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
shutil.copy(js, f'{T}/../脚本/{no}.json'); os.makedirs(f'{T}/../脚本/已发版本', exist_ok=True); shutil.copy(js, f'{T}/../脚本/已发版本/{no}.json')
print(f'第{no}篇对照文本：Word {len(cells)} 格逐格一致，PDF {len(pymupdf.open(pdf))} 页，已拷进 视频/对照文本/')
