#!/usr/bin/env python3
"""踩坑核查（最高铁律：踩过的坑绝不再踩）。任何东西交出去之前都要过这一关：
  python3 踩坑核查.py NN 文本   # 发 Word / HTML / PDF 之前（生成文本.py 自动调用）
  python3 踩坑核查.py NN 出片   # 出视频之前（交付核查.py 出片前 自动调用）
  python3 踩坑核查.py 通用      # 做文章、视频以外的任何事之前：列出沟通、保存类的坑和铁律，逐条对照
  python3 踩坑核查.py 自检      # 只做核查程序自检
每次运行先做"核查程序自检"：在第03篇（已定稿）的副本里故意造出每一种能用程序查的坑，必须全部抓到，且原稿不得误报；
抓不到 = 核查失灵，不得交付。然后：
  ① 踩坑对照记录：制作记录/NN.md 里本阶段涉及的每一条（文本：T D W C G；出片：全部）都填了"涉及/不涉及"和怎么防的；
  ② 能用程序查的坑逐条查（下面每个检查都写明对应的踩坑编号）；
  ③ 需要逐个确认的（疑似缺牛津逗号、数字对不上）必须在 scripts/NN.json 的"核对确认"里逐条写明结论；
  ④ 换行（L13）：与上次发给用户的版本（脚本/已发版本/NN.json）逐句比对，有变化必须在"换行变更已获同意"里写明用户原话；
  ⑤ 存视频的文件夹只存定稿（G7）：已定稿篇目的草稿、试听视频、旧版本必须删掉。
新坑入表时，凡是能用程序查的，必须同时在这里加检查、在自检里加一个故意造坑的样本。"""
import sys, os, re, json, glob, copy, subprocess
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); ROOT = os.path.dirname(V)
STAGE_PREFIX = {'文本': 'TDWCG', '出片': 'TDWCGLHAS'}
NUMW = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'twenty': 20, 'thirty': 30, 'fifty': 50, 'hundred': 100}
strip_en = lambda x: re.sub(r'\*\*|\{\{.*?\}\}', '', x)
ns = lambda x: re.sub(r'[\*\s]', '', x)


def pit_rows():
    """《踩坑总表》每一行：(编号, 出过的问题, 以后怎么防)"""
    out = []
    for line in open(f'{V}/踩坑总表.md').read().splitlines():
        m = re.match(r'^\| *([A-Z]\d+b?) *\|(.*)\|\s*$', line)
        if m:
            cells = [c.strip() for c in m.group(2).split('|')]
            out.append((m.group(1), cells[0], cells[-1] if len(cells) > 1 else ''))
    return out


def record_gate(no, stage):
    """① 踩坑对照记录：本阶段涉及的条目逐条填完"""
    rec = f'{V}/制作记录/{no}.md'
    return record_gate_text(open(rec).read() if os.path.exists(rec) else '', no, stage)


def record_gate_text(txt, no, stage):
    if '## 踩坑对照记录' not in txt:
        return [f'制作记录/{no}.md 没有"## 踩坑对照记录"（先运行：交付核查.py {no} 对照表，再逐条填写）']
    sec = txt[txt.index('## 踩坑对照记录'):]
    rows = {m.group(1): [c.strip() for c in m.group(2).split('|')] for m in re.finditer(r'^\| *([A-Z]\d+b?) *\|(.*)\|\s*$', sec, re.M)}
    need = [i for i, _, _ in pit_rows() if i[0] in STAGE_PREFIX[stage]]
    miss = [i for i in need if i not in rows]
    blank = [i for i in need if i in rows and not (len(rows[i]) >= 3 and rows[i][-2] in ('涉及', '不涉及') and rows[i][-1] not in ('', '待填'))]
    err = []
    if miss: err.append(f'踩坑对照记录缺条目（《踩坑总表》新加的条目要补进去）：{" ".join(miss)}')
    if blank: err.append(f'踩坑对照记录没填完（{stage}阶段必须填）：{" ".join(blank)}')
    return err


def article_en(no):
    md = glob.glob(f'{ROOT}/新版定稿/{no}-*.md')
    return open(md[0]).read().split('## 英文', 1)[1].split('## 中文', 1)[0] if md else None


_R = None
def _render():
    """视频画面的排版程序（与出片同一套），字体用仓库 资源/字体/"""
    global _R
    if _R is None:
        sys.path.insert(0, T); import render as R
        R.F = f'{V}/资源/字体/'; _R = R
    return _R


def layout(d):
    """换行结构（L13）：用出片的排版程序算出每屏每一行实际是哪几个英文词、中文占几行；
    再加上 chunk 划分、手动断行标记 ["\n",""]、英文里的 {{=}}/{{/}} 标记。只改分组、不改画面上的行，不算换行变化。"""
    R = _render(); es = R.LAYOUT_ES; ef = R.EN(es, 600); zf = R.ZH(int(es * R.ZR), 500); gapx = int(es * 0.36)
    sig = []
    for s in d['sentences']:
        colors = {w.lower(): (1, 1, 1) for c in s['chunks'] for w in re.findall(r'\*\*([^*]+)\*\*', c['en'])}
        ss = []
        for c in s['chunks']:
            before = []; acc = []
            for a, z in c['align']:
                if a == '\n': before.append(ns(strip_en(' '.join(acc))))
                else: acc.append(a)
            rows = []
            for r in R._rows([tuple(p) for p in c['align']], colors, ef, zf, gapx, 1840 * R.S):
                cols = [r[1]] if isinstance(r, tuple) else r
                rows.append(('整格折行' if isinstance(r, tuple) else '行', ns(''.join(t for col in cols for t, _ in col['se'])), max(col['nz'] for col in cols)))
            ss.append({'en': ns(strip_en(c['en'])), '标记': re.findall(r'\{\{[=/]\}\}', c['en']), '断行在': before, '画面各行': rows})
        sig.append(ss)
    return sig


def text_checks(d, art=None, sent=None):
    """② ③ ④ 能用程序查的坑。返回 (错误, 待确认, 参考)；每条以 [编号] 开头"""
    err, conf, ref = [], [], []
    ok = d.get('核对确认', {}); ox_ok = ok.get('牛津逗号', {}); num_ok = ok.get('数字', {})
    paras = {}
    for i, s in enumerate(d['sentences']):
        S = f'S{i + 1}'
        en_sent = ' '.join(strip_en(c['en']) for c in s['chunks'])
        # T18 牛津逗号：疑似"A, B and C"（and/or 前没有逗号）逐个确认
        for m in re.finditer(r"(?<![\w'-])([\w'-]+(?: [\w'-]+){0,3}), ([\w'-]+(?: [\w'-]+){0,3}) (and|or) ", en_sent):
            key = f'{S} {m.group(0).strip()}'
            if key not in ox_ok: conf.append(f'[T18] {key}  ← 是不是三项以上并列、缺牛津逗号？逐个确认后写进 核对确认.牛津逗号')
        for k, c in enumerate(s['chunks']):
            C = f'{S}-{k + 1}'
            if '\n' in c['en']: err.append(f'[D1] {C} 英文里混入换行标记')
            if ns(' '.join(a for a, _ in c['align'] if a != '\n')) != ns(c['en']): err.append(f'[D2] {C} align 英文与 en 不一致')
            if ''.join(z for _, z in c['align']) != c['zh']: err.append(f'[D2] {C} zh 与 align 中文拼接不一致')
            if c['en'].strip() and not c['zh'].strip(): err.append(f'[T6] {C} 空译文')
            marks = {m.lower() for m in re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)', c['zh'])}
            for w in re.findall(r'\*\*([^*]+)\*\*', c['en']):
                if w.lower() not in marks and not any(w.lower() in m.split() for m in marks): err.append(f'[D4] {C} 重点词 {w} 缺中文标记')
            for m in re.finditer(r'\*\*([^*]+)\*\*', c['zh']):
                if not c['zh'][m.end():].startswith('('): err.append(f'[D4格式] {C} 中文重点词 **{m.group(1)}** 后面没有紧跟 (英文)')
            z = re.sub(r'\*\*|\([A-Za-z][^)]*\)', '', c['zh'])
            if re.search(r'[一-鿿）】》”][,.;:?!]|[,;:?!][一-鿿（【《“]', z): err.append(f'[标点] {C} 中文里用了半角标点：{c["zh"][:30]}')
            if re.search(r'[「」『』"]', z): err.append(f'[标点] {C} 引号要用中文引号“”：{c["zh"][:30]}')
            if re.search(r'\((?![A-Za-z])', z): err.append(f'[W4] {C} 中文说明用了半角括号（要用全角（））')
            if c.get('note') and not re.match(r'^(#\w+)?（.*）$', c['note'], re.S): err.append(f'[注释] {C} 注释要写在全角（）里：{c["note"][:30]}')
            # T16 数字：英文里的阿拉伯数字，中文里要有同一个数（写法不同的逐个确认）
            for num in re.findall(r'\d[\d,]*\d|\d', strip_en(c['en'])):
                if num not in c['zh'] and num.replace(',', '') not in c['zh'].replace(',', ''):
                    key = f'{C} {num}'
                    if key not in num_ok: conf.append(f'[T16] {key}  ← 中文里没有这个数，读法/写法核对后写进 核对确认.数字')
            # T19：第04篇初稿与 01–03 定稿写法不一致、经独立审校查出的几类（01–03 里从未出现或只出现过经用户认可的个例）
            if re.search(r'\*\*\([^)]*\)了', c['zh']): err.append(f'[T19了] {C} "了"要放进加粗里（如 **扫描了**(scanned)）：{c["zh"][:30]}')
            def ask(tag, what, hint):
                key = f'{C} {what}'
                if key not in ok.get(tag, {}): conf.append(f'[T19{tag}] {key}  ← {hint}，核对后写进 核对确认.{tag}')
            for m in re.finditer(r'(?<!也就)(?<!的)(?<!就)是\*\*[^*]+的\*\*', c['zh']): ask('是的', m.group(0), '"是**…的**"多半生硬（01–03 没有先例，如"都是至关重要的"→"都至关重要"）')
            for w, v in NUMW.items():
                if re.search(rf'\b{w}\b', strip_en(c['en']), re.I) and re.search(rf'(?<![\d,.]){v}(?![\d,])', c['zh']): ask('数字写法', w, '英文是单词数字，中文写成了阿拉伯数字')
            if re.search(r'[“”]', c['zh']) and not re.search(r'["“”]', c['en']): ask('引号', '“”', '英文没有引号，中文却加了引号')
            if '即' in re.sub(r'（[^（）]*）|\*\*[^*]+\*\*\([^)]*\)', '', c['zh']): ask('即', '即', '正文（括号外）用了文言的"即"')
            for m in re.finditer(r'\*\*[^*]*们\*\*', c['zh']): ask('们', m.group(0), '名词重点词带"们"')
            for m in re.finditer(r'（[^（）]*\*\*[^（）]*）', c['zh']): ask('括号含重点词', m.group(0), '括号里包着重点词：原文的译文不能放进括号当补充（T1）')
            for a in re.findall(r'（[^（）]*）', re.sub(r'\*\*[^*]+\*\*\([^)]+\)', '', c['zh'])):
                ref.append(f'[T1] {C} 括号内容 {a}（若是原文没有的补充，需用户认可）')
        paras.setdefault(s['para'], []).append(' '.join(re.sub(r'\{\{.*?\}\}', '', c['en']) for c in s['chunks']))
    if art is not None and ns(''.join(' '.join(v) for _, v in sorted(paras.items()))) != ns(art): err.append('[D3] 英文与文章原文不一致（英文一个字都不能改，牛津逗号除外且要同步到文章）')
    if sent is not None:
        a, b = layout(sent), layout(d); appr = d.get('换行变更已获同意', {})
        if len(a) != len(b): err.append(f'[L13] 句数变了（{len(a)} → {len(b)}），换行变更必须经用户同意')
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y and f'S{i + 1}' not in appr: err.append(f'[L13] S{i + 1} 换行与上次发给用户的版本不同，没有用户同意（写进 换行变更已获同意："S{i + 1}": "用户原话"）')
    return err, conf, ref


def selftest():
    """核查程序自检：在已定稿的第03篇副本里逐一造坑，每一种都必须抓到；原稿不得误报"""
    base = json.load(open(f'{V}/脚本/03.json')); art = article_en('03')
    e0, c0, _ = text_checks(base, art, base)
    fails = [f'原稿误报：{x}' for x in e0 + c0]
    def find(pred):
        for s in base['sentences']:
            for k, c in enumerate(s['chunks']):
                if pred(c): return base['sentences'].index(s), k
    def mut(name, tag, fn, art2=None):
        d = copy.deepcopy(base); fn(d); e, c, _ = text_checks(d, art2 if art2 is not None else art, base)
        if not any(x.startswith(f'[{tag}]') for x in e + c): fails.append(f'没抓到：{name}')
    si, ck = find(lambda c: 'food, and' in c['en'])
    def ox(d):
        c = d['sentences'][si]['chunks'][ck]; c['en'] = c['en'].replace('food, and', 'food and')
        c['align'] = [[a.replace('food, and', 'food and'), z] for a, z in c['align']]
    mut('牛津逗号被去掉（T18）', 'T18', ox, art.replace('food, and', 'food and'))
    mut('英文里混进换行标记（D1）', 'D1', lambda d: d['sentences'][0]['chunks'][0].__setitem__('en', d['sentences'][0]['chunks'][0]['en'] + '\n'))
    def d2(d): d['sentences'][1]['chunks'][0]['zh'] += '多'
    mut('zh 与分组拼接不一致（D2）', 'D2', d2)
    def d3(d):
        c = d['sentences'][2]['chunks'][0]; w = re.findall(r'[A-Za-z]{4,}', strip_en(c['en']))[0]
        c['en'] = c['en'].replace(w, w + 's', 1); c['align'] = [[a.replace(w, w + 's', 1), z] for a, z in c['align']]
    mut('英文被改动（D3）', 'D3', d3)
    si4, ck4 = find(lambda c: '(broth)' in c['zh'])
    def d4(d):
        c = d['sentences'][si4]['chunks'][ck4]; c['zh'] = c['zh'].replace('(broth)', ''); c['align'] = [[a, z.replace('(broth)', '')] for a, z in c['align']]
    mut('重点词缺中文标记（D4）', 'D4', d4)
    def d4f(d):
        c = d['sentences'][6]['chunks'][0]; c['zh'] += '**多加粗**'; c['align'][-1][1] += '**多加粗**'
    mut('中文加粗后没有(英文)标记（D4格式）', 'D4格式', d4f)
    si5, ck5 = find(lambda c: '，' in c['zh'])
    def pu(d):
        c = d['sentences'][si5]['chunks'][ck5]; c['zh'] = c['zh'].replace('，', ',', 1)
        done = False
        for g in c['align']:
            if not done and '，' in g[1]: g[1] = g[1].replace('，', ',', 1); done = True
    mut('中文用了半角逗号', '标点', pu)
    def qu(d):
        c = d['sentences'][3]['chunks'][0]; c['zh'] = '「' + c['zh'] + '」'; c['align'][0][1] = '「' + c['align'][0][1]; c['align'][-1][1] += '」'
    mut('中文用了「」引号', '标点', qu)
    si7, ck7 = find(lambda c: '1984' in c['zh'])
    def nu(d):
        c = d['sentences'][si7]['chunks'][ck7]; c['zh'] = c['zh'].replace('1984', '1948'); c['align'] = [[a, z.replace('1984', '1948')] for a, z in c['align']]
    mut('数字抄错（T16）', 'T16', nu)
    def lb(d): d['sentences'][4]['chunks'][0]['align'].insert(1, ['\n', ''])
    mut('擅自加换行（L13）', 'L13', lb)
    def lb2(d): d['sentences'][5]['chunks'][0]['en'] += '{{=}}'
    mut('擅自加"不换行"标记（L13）', 'L13', lb2)
    def d2e(d):
        c = d['sentences'][7]['chunks'][0]; c['align'][0][0] += ' extra'
    mut('align 英文与 en 不一致（D2）', 'D2', d2e)
    def em(d):
        c = d['sentences'][8]['chunks'][0]; c['zh'] = ''; c['align'] = [[a, ''] for a, _ in c['align']]
    mut('漏译、空译文', 'T6', em)
    def hp(d):
        c = d['sentences'][9]['chunks'][0]; c['zh'] += '(补充)'; c['align'][-1][1] += '(补充)'
    mut('中文说明用了半角括号（W4）', 'W4', hp)
    ids = [i for i, _, _ in pit_rows()]
    tpl = '## 踩坑对照记录\n' + '\n'.join(f'| {i} | x | 待填 | 待填 |' for i in ids)
    if not record_gate_text(tpl, '03', '文本'): fails.append('没抓到：踩坑对照记录没填完')
    full = '## 踩坑对照记录\n' + '\n'.join(f'| {i} | x | 不涉及 | 已核对 |' for i in ids)
    if not record_gate_text(full.replace(f'| {ids[0]} | x | 不涉及 | 已核对 |\n', ''), '03', '出片'): fails.append('没抓到：踩坑对照记录缺条目')
    if record_gate_text(full, '03', '出片'): fails.append('误报：填完的踩坑对照记录被判不合格')
    def rg(d):   # 只把一组拆成两组、画面上的行不变：不应报换行变化
        c = d['sentences'][0]['chunks'][0]; a, z = c['align'][0]
        if ' ' in a: w = a.split(' '); c['align'][0:1] = [[w[0], z], [' '.join(w[1:]), '']]
    dd = copy.deepcopy(base); rg(dd); e, _, _ = text_checks(dd, art, base)
    if any(x.startswith('[L13]') for x in e): fails.append('误报：只改分组、画面行不变，被当成换行变化')
    def zl(d):
        c = d['sentences'][10]['chunks'][0]; c['align'][0][1] += '\n'; c['zh'] = ''.join(z for _, z in c['align'])
    mut('擅自在中文格内分行（L13）', 'L13', zl)
    def zfind(sub):
        for s_ in base['sentences']:
            for k_, c_ in enumerate(s_['chunks']):
                if sub in c_['zh']: return base['sentences'].index(s_), k_
    def rep(sub, new):
        si_, ck_ = zfind(sub)
        def f(d):
            c = d['sentences'][si_]['chunks'][ck_]; c['zh'] = c['zh'].replace(sub, new, 1)
            done = False
            for g in c['align']:
                if not done and sub in g[1]: g[1] = g[1].replace(sub, new, 1); done = True
            assert done
        return f
    mut('"了"放在加粗外（T19）', 'T19了', rep('**刮了下来**(scraped)', '**刮下来**(scraped)了'))
    mut('"是**…的**"生硬（T19）', 'T19是的', rep('**不利的**(hostile)', '是**不利的**(hostile)'))
    mut('英文单词数字写成阿拉伯数字（T19）', 'T19数字写法', rep('两个培养皿', '2个培养皿'))
    mut('英文没有引号、中文加了引号（T19）', 'T19引号', rep('**盛行的**(prevalent)', '“**盛行的**(prevalent)”'))
    mut('正文用"即"（T19）', 'T19即', rep('**盛行的**(prevalent)', '即**盛行的**(prevalent)'))
    mut('名词重点词带"们"（T19）', 'T19们', rep('**妻子**(spouse)', '**妻子们**(spouse)'))
    mut('括号里包着重点词（T19/T1）', 'T19括号含重点词', rep('**盛行的**(prevalent)', '（**盛行的**(prevalent)）'))
    def nt(d):
        c = next(c for s in d['sentences'] for c in s['chunks'] if c.get('note')); c['note'] = c['note'].strip('（）')
    mut('注释没写在全角括号里', '注释', nt)
    return fails


VIDEO_EXT = ('.mp4', '.mov', '.m4v', '.webm', '.mkv', '.avi')


def video_folders(root):
    """G7（用户 2026-10-08）：存定稿视频的文件夹只存定稿版本，有瑕疵的旧版本、草稿及时删除。
    最终版4K视频/：每篇一个"NN - 英文标题 - 中文标题.mp4"；视频/视频/：只有 NN.mp4，且与归档的定稿逐字节相同；
    已定稿的篇目，视频/视频/草稿1080p/ 里的草稿和 视频/试听/ 里的试听视频必须删掉（没定稿的篇目在修改阶段可以暂存草稿）。"""
    import hashlib
    md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
    err = []; fin = {}
    for p in sorted(glob.glob(f'{root}/最终版4K视频/*')):
        b = os.path.basename(p)
        if b == 'README.md': continue
        m = re.match(r'(\d\d) - .+ - .+\.mp4$', b)
        if not m: err.append(f'[G7] 最终版4K视频/ 里有不是定稿命名的文件：{b}'); continue
        if m.group(1) in fin: err.append(f'[G7] 最终版4K视频/ 里第{m.group(1)}篇不止一个版本：{b}')
        fin[m.group(1)] = p
    for p in sorted(glob.glob(f'{root}/视频/视频/*')):
        b = os.path.basename(p)
        if os.path.isdir(p):
            if b != '草稿1080p': err.append(f'[G7] 视频/视频/ 里有多余的文件夹：{b}')
            continue
        m = re.match(r'(\d\d)\.mp4$', b)
        if not m: err.append(f'[G7] 视频/视频/ 里有不是定稿的文件：{b}')
        elif m.group(1) not in fin: err.append(f'[G7] 视频/视频/{b} 没有归档到 最终版4K视频/（定稿后运行 归档定稿视频.py）')
        elif md5(p) != md5(fin[m.group(1)]): err.append(f'[G7] 视频/视频/{b} 与 最终版4K视频/ 里的定稿不是同一个版本')
    for p in sorted(glob.glob(f'{root}/视频/视频/草稿1080p/*')) + [q for q in sorted(glob.glob(f'{root}/视频/试听/*')) if q.lower().endswith(VIDEO_EXT)]:
        m = re.match(r'(\d\d)', os.path.basename(p))
        if m and m.group(1) in fin: err.append(f'[G7] 第{m.group(1)}篇已定稿，旧草稿/试听视频没删：{os.path.relpath(p, root)}')
    return err


def selftest_folders():
    """G7 自检：临时目录里造一份"已定稿、草稿没删"的目录，必须报出；删干净的必须不报"""
    import tempfile
    fails = []
    with tempfile.TemporaryDirectory() as r:
        for q in ('最终版4K视频', '视频/视频/草稿1080p', '视频/试听'): os.makedirs(f'{r}/{q}')
        for q in ('最终版4K视频/03 - A - 甲.mp4', '视频/视频/03.mp4'): open(f'{r}/{q}', 'wb').write(b'final')
        if video_folders(r): fails.append(f'误报：只有定稿的目录被判不合格 {video_folders(r)}')
        open(f'{r}/视频/视频/草稿1080p/03_1080p.mp4', 'wb').write(b'draft')
        if not any('03_1080p' in x for x in video_folders(r)): fails.append('没抓到：已定稿篇目的草稿没删（G7）')
        os.remove(f'{r}/视频/视频/草稿1080p/03_1080p.mp4'); open(f'{r}/视频/试听/03_试听.mp4', 'wb').write(b'x')
        if not any('03_试听' in x for x in video_folders(r)): fails.append('没抓到：已定稿篇目的试听视频没删（G7）')
        os.remove(f'{r}/视频/试听/03_试听.mp4'); open(f'{r}/视频/视频/03.mp4', 'wb').write(b'old')
        if not any('不是同一个版本' in x for x in video_folders(r)): fails.append('没抓到：视频/视频/ 里留着旧版本（G7）')
        open(f'{r}/视频/视频/03.mp4', 'wb').write(b'final'); open(f'{r}/最终版4K视频/03 - A - 乙.mp4', 'wb').write(b'final')
        if not any('不止一个版本' in x for x in video_folders(r)): fails.append('没抓到：最终版4K视频/ 里同一篇有两个版本（G7）')
    return fails


def check_all_text(no, js):
    """check_all.py（D1–D4、撞词 T12、速查表 S2）；文本阶段视频文件还没有，不算"""
    r = subprocess.run(['python3', f'{T}/check_all.py', no, js], capture_output=True, text=True)
    return [l for l in (r.stdout + r.stderr).splitlines() if l.strip() and '全部检查通过' not in l and not l.startswith('缺文件: 视频/视频/')]


def main():
    args = sys.argv[1:]
    if args and args[0] == '通用':
        print('做任何事之前逐条对照（沟通、保存类的坑 + 铁律）：')
        for i, a, b in pit_rows():
            if i[0] in 'CG': print(f'  {i}  {a}\n       → {b}')
        print('铁律：教材零瑕疵；踩过的坑绝不再踩；不自己检查自己；改一处全部重查；先核查后交付（硬性条件第〇节）')
        vf = selftest_folders() or video_folders(ROOT)
        print('存视频的文件夹只存定稿（G7）：' + ('通过' if not vf else '\n  ✘ ' + '\n  ✘ '.join(vf)))
        return 1 if vf else 0
    fails = selftest() + selftest_folders()
    print('核查程序自检：' + ('通过（每一种造出来的坑都抓到，原稿无误报）' if not fails else '【失灵】' + '；'.join(fails)))
    if fails: print('【核查程序失灵，不得交付】'); return 1
    if args and args[0] == '自检': return 0
    no, stage = args[0].zfill(2), args[1]
    js = f'scripts/{no}.json' if os.path.exists(f'scripts/{no}.json') else f'{V}/脚本/{no}.json'
    d = json.load(open(js)); snap = f'{V}/脚本/已发版本/{no}.json'
    sent = json.load(open(snap)) if os.path.exists(snap) else None
    err = record_gate(no, stage) + video_folders(ROOT)
    e, conf, ref = text_checks(d, article_en(no), sent); err += e
    err += [f'[check_all] {x}' for x in check_all_text(no, os.path.abspath(js))]
    print(f'第{no}篇 {stage}阶段 踩坑核查（{js}）：')
    if sent is None: print('  （还没有"已发版本"，这次不比对换行；生成文本.py 成功后会保存）')
    for x in err: print('  ✘ ' + x)
    for x in conf: print('  ？ ' + x)
    for x in ref: print('  · ' + x)
    bad = bool(err or conf)
    print('  全部通过' if not bad else f'  【不通过：{len(err)} 个错误，{len(conf)} 处待确认，不得交付】')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
