#!/usr/bin/env python3
"""生成并核对一篇的对照文本（Word / HTML / PDF），再拷进仓库 视频/对照文本/。不要手敲命令（W8、W9）。
在视频工作目录（含 scripts/NN.json、render.py、fonts/）下运行：python3 <工具目录>/生成文本.py NN
先过《踩坑核查》（文本阶段），不通过就停止。生成后核对：Word 逐格读回与脚本一致；PDF 是本次生成、文字里有英文标题、不是浏览器错误页；
同一篇的所有 docx 文件名一起覆盖（W7）。最后把脚本同步进仓库 脚本/NN.json，并存为 脚本/已发版本/NN.json（下次比对换行用）。"""
import sys, os, re, json, glob, time, shutil, subprocess
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
from read_docx2 import segs
ns = lambda x: re.sub(r'\s', '', x)
def 读回核对(docx, d):
    """W1/文27：Word 逐格读回，必须与脚本分组一致"""
    bad = []
    cells = [(e, ''.join(t for t, _ in z)) for k, v in segs(docx) if k == 'T' for e, z in v]
    import render as _R
    want = [(''.join(x for x, _ in _R._segs_en(a, {})),   # 英文按 make_docx 同一个函数：{{注解}} 照常显示，{{=}}、{{一行}} 不显示（D5）
            re.sub(r'\*\*|\([A-Za-z \-]+\)|\n', '', re.sub(r'\{\{([^|{}]+)\|[^{}]+\}\}', r'\1', b)))   # 颜色说明 {{文字|词}} 只取文字
            for s in d['sentences'] for c in s['chunks'] for a, b in c['align'] if a != '\n']
    if len(cells) != len(want): bad.append(f'Word 格数 {len(cells)} ≠ 脚本分组数 {len(want)}')
    bad += [f'Word 格不一致：{x} ≠ {y}' for x, y in zip(cells, want) if ns(x[0]) != ns(y[0]) or ns(x[1]) != ns(y[1])][:10]
    return bad, cells
def PDF核对(pdf, t0, title):
    """W5/W8/W9：PDF 必须是本次生成的、有英文标题、不是浏览器错误页"""
    if not os.path.exists(pdf) or os.path.getmtime(pdf) < t0: return ['PDF 没有生成（或不是本次生成的）']
    import pymupdf
    txt = ''.join(p.get_text() for p in pymupdf.open(pdf))
    if title not in re.sub(r'\s+', ' ', txt) or re.search(r"can.t be reached|ERR_|could not be found", txt): return ['PDF 内容不对（可能是浏览器错误页，W9）']
    return []
def 要覆盖(dst, no):
    """W7/文28：同一篇所有 docx 文件名一起覆盖；用户发回的修正稿（文件名带“用户”）不覆盖"""
    return [f for f in [f'{dst}/{no}-文本.docx'] + sorted(glob.glob(f'{dst}/{no}-文本-*.docx')) if '用户' not in os.path.basename(f)]
if sys.argv[1:2] == ['--自检']:
    import tempfile, copy
    fails = []; td = tempfile.mkdtemp(); V_ = os.path.dirname(T)
    d0 = json.load(open(f'{V_}/脚本/03.json')); json.dump(d0, open(f'{td}/03.json', 'w'), ensure_ascii=False)
    subprocess.run(['python3', f'{T}/make_docx.py', f'{td}/03.json', f'{td}/a.docx'], check=True, capture_output=True, cwd=T)
    if 读回核对(f'{td}/a.docx', d0)[0]: fails.append('Word 读回 误报：' + 读回核对(f'{td}/a.docx', d0)[0][0])
    d1 = copy.deepcopy(d0); c1 = d1['sentences'][1]['chunks'][0]; c1['align'][0][1] += '多'; c1['zh'] = ''.join(b for _, b in c1['align'])
    if not any('Word 格不一致' in x for x in 读回核对(f'{td}/a.docx', d1)[0]): fails.append('没抓到：Word 和脚本对不上（W1）')
    d2 = copy.deepcopy(d0); d2['sentences'][1]['chunks'][0]['align'].append(['extra', '多一格'])   # G79 门变异：格数不对这道门没人发现
    if not any('Word 格数' in x for x in 读回核对(f'{td}/a.docx', d2)[0]): fails.append('没抓到：Word 格数和脚本分组数对不上（W1）')
    if not PDF核对(f'{td}/没有.pdf', time.time(), 'x'): fails.append('没抓到：PDF 没有生成（W5/W8/W9）')
    for n_ in ('03-文本.docx', '03-文本-待修正.docx', '03-文本-用户改.docx'): open(f'{td}/{n_}', 'w').write('x')
    if [os.path.basename(x) for x in 要覆盖(td, '03')] != ['03-文本.docx', '03-文本-待修正.docx']: fails.append('没抓到：docx 没有一起覆盖，或覆盖了用户的修正稿（W7）')
    shutil.rmtree(td, ignore_errors=True)
    print('生成文本 自检：' + ('通过（Word 逐格读回、PDF 没生成、docx 一起覆盖且不碰用户稿：错例全部报出，正例不误报）' if not fails else '失灵！' + '；'.join(fails)))
    sys.exit(1 if fails else 0)
no = sys.argv[1].zfill(2); js = os.path.abspath(f'scripts/{no}.json'); d = json.load(open(js))
只核查 = '--只核查' in sys.argv   # 守则17（用户 2026-10-24：“以后先不要再去做word或者是PDF了……先只做视频即可”）：只过核查、存已发版本，不出 Word/HTML/PDF
docx, html, pdf = (os.path.abspath(f'{no}-文本.{x}') for x in ('docx', 'html', 'pdf'))
t0 = time.time(); bad = []
# 最高铁律：先过踩坑核查（含核查程序自检、踩坑对照记录、换行比对），不通过不生成、不发
r = subprocess.run(['python3', f'{T}/踩坑核查.py', no, '文本'], capture_output=True, text=True); print(r.stdout.strip())
if r.returncode: sys.exit('【踩坑核查不通过，不生成、不发给用户】')
if 只核查:
    if d.get('换行变更已获同意'):
        d.setdefault('换行变更记录', []).append({'日期': time.strftime('%Y-%m-%d'), **d.pop('换行变更已获同意')})
        json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
    shutil.copy(js, f'{T}/../脚本/{no}.json'); os.makedirs(f'{T}/../脚本/已发版本', exist_ok=True); shutil.copy(js, f'{T}/../脚本/已发版本/{no}.json')
    sys.exit(print(f'第{no}篇：文本核查全部通过，脚本已存为已发版本（只核查：不出 Word/PDF，守则17）'))
subprocess.run(['python3', f'{T}/make_docx.py', js, docx], check=True)
subprocess.run(['python3', f'{T}/make_text.py', js, html], check=True)
if os.path.exists(pdf): os.remove(pdf)
subprocess.run(['/opt/pw-browsers/chromium', '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                f'--print-to-pdf={pdf}', 'file://' + html], capture_output=True)
# Word 逐格读回
_b, cells = 读回核对(docx, d); bad += _b
# PDF
bad += PDF核对(pdf, t0, d['title_en'])
if bad: sys.exit('【不通过】\n' + '\n'.join(bad))
dst = f'{T}/../对照文本'
for f in 要覆盖(dst, no): shutil.copy(docx, f)          # W7：用户发回的修正稿不覆盖
shutil.copy(html, f'{dst}/{no}-文本.html'); shutil.copy(pdf, f'{dst}/{no}-文本.pdf')
# 脚本同步进仓库，并存为"已发版本"（下次比对换行，L13）；本次用到的换行同意转入记录
if d.get('换行变更已获同意'):
    d.setdefault('换行变更记录', []).append({'日期': time.strftime('%Y-%m-%d'), **d.pop('换行变更已获同意')})
    json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
shutil.copy(js, f'{T}/../脚本/{no}.json'); os.makedirs(f'{T}/../脚本/已发版本', exist_ok=True); shutil.copy(js, f'{T}/../脚本/已发版本/{no}.json')
sys.path.insert(0, f'{T}/钩子'); import 闸门; 闸门.记回执([docx, html, pdf] + [f'{dst}/{no}-文本.{x}' for x in ('docx', 'html', 'pdf')], f'生成文本 第{no}篇')   # 发文件闸门凭回执放行
import pymupdf
print(f'第{no}篇对照文本：Word {len(cells)} 格逐格一致，PDF {len(pymupdf.open(pdf))} 页，已拷进 视频/对照文本/')
