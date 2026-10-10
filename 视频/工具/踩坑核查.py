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
            ss.append({'en': ns(strip_en(c['en'])), '标记': re.findall(r'\{\{(?:[=/]|一行)\}\}', c['en']), '断行在': before, '画面各行': rows})
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
            # T24 用户口述（语音输入）多识别出来的词照抄进了画面（08 S16 用户口述“婉言拒绝(觉得方式比较体面，礼貌)”，“觉得”是语音输入多出来的，
            # 我按 T10 照抄；用户：“这个地方为什么会有一个觉得呢？……没有觉得那两个字”）：括号说明、note 里出现这类词，核对用户本意后写进 核对确认.口述
            segs = re.findall(r'（(?:[^（）]|（[^（）]*）)*）', c['zh']) + ([c['note']] if c.get('note') else [])
            for seg in segs:
                for m in re.finditer(r'觉得|嗯|呃|那个|就是说|然后呢|你知道', seg):
                    key = f'{C} {m.group(0)}'
                    if key not in d.get('核对确认', {}).get('口述', {}): conf.append(f'[T24] {key}  ← 用户口述（语音输入）里常多出来的词出现在括号说明或 note 里：{seg[:30]}，核对用户本意后改掉，或写进 核对确认.口述')
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


# T22 短语型用法只标了一个词（用户 2026-10-10 看 08 初稿：“这个地方 attributed to 肯定要把 to 也包含进去，也要标色。
# 你记住以后……短语型的用法……就不止一个词，这种复合用法你不能只标一个词”；T14 depend on 的坑重犯）：
# 重点词的固定搭配/短语动词/句型（速查表释义、note 里写的 attribute A to B、arise from、succumb to……，再加一张常用搭配兜底表），
# 搭配里的介词/小品词就在同一分句里（往后 6 个词以内，不跨 , ; : .），却没有一起加粗 → 逐个报出。
# 改法：连着的整体加粗（**arising from**）；被隔开的按 T14 两部分都加粗、中文括注写完整短语（**attributed** **epidemics** **to** / **归因于**(attributed to)）。
# 介词只是普通介词短语开头、不构成固定用法的，核实后写进 核对确认.短语："S6 plunged … from": "理由"。
PH_PREPS = 'to from as on in of with for into at by about out up off over upon onto against through away down back'.split()
PH_BACK = 'in on at by under with without within beyond'.split()   # 反方向：这些介词 + 名词重点词（in flocks、in desperation、on foot、by chance）
PH_SLOT = r"(?:A|B|C|sb|sth|sb's|sth's|one|one's|oneself|somebody|something|\.\.\.|…|……|doing|do)"
PH_CORE = {'attribute':['to'],'ascribe':['to'],'stem':['from'],'arise':['from'],'result':['in','from'],'derive':['from'],'originate':['from'],
 'depend':['on','upon'],'rely':['on','upon'],'consist':['of'],'account':['for'],'refer':['to'],'interpret':['as'],'regard':['as'],'view':['as'],
 'succumb':['to'],'cope':['with'],'deal':['with'],'insist':['on'],'focus':['on'],'belong':['to'],'adapt':['to'],'respond':['to'],'object':['to'],
 'contribute':['to'],'lead':['to'],'prevent':['from'],'distinguish':['from'],'differ':['from'],'suffer':['from'],'benefit':['from'],'emerge':['from'],
 'compensate':['for'],'search':['for'],'apply':['to','for'],'subject':['to'],'expose':['to'],'confine':['to'],'convert':['into'],'transform':['into'],
 'translate':['into'],'divide':['into'],'turn':['into'],'blame':['on','for'],'accuse':['of'],'deprive':['of'],'rob':['of'],'remind':['of'],'consist':['of'],
 'dispose':['of'],'approve':['of'],'conform':['to'],'cling':['to'],'resort':['to'],'yield':['to'],'amount':['to'],'adhere':['to'],'commit':['to'],
 'devote':['to'],'dedicate':['to'],'specialize':['in'],'engage':['in'],'participate':['in'],'result':['in','from'],'persist':['in'],'invest':['in'],
 'comply':['with'],'interfere':['with'],'associate':['with'],'equip':['with'],'provide':['with','for'],'charge':['with'],'credit':['with'],
 'spur':['on'],'set':['in','out','off','up'],'hold':['out','on','back'],'rattle':['off'],'carry':['out','on'],'figure':['out'],'point':['out'],
 'call':['for','on','off'],'stand':['for','out'],'take':['over','on','up'],'give':['up','in'],'bring':['about','up'],'come':['up','across','about'],
 'pore':['over'],'dwell':['on'],'feed':['on'],'prey':['on'],'live':['on'],'border':['on'],'hinge':['on'],'impose':['on'],'capitalize':['on'],
 'aware':['of'],'capable':['of'],'devoid':['of'],'free':['from','of'],'prone':['to'],'subject':['to'],'immune':['to'],'akin':['to'],'vulnerable':['to'],
 'susceptible':['to'],'relevant':['to'],'similar':['to'],'familiar':['with'],'content':['with'],'compatible':['with'],'consistent':['with'],
 'responsible':['for'],'eligible':['for'],'famous':['for'],'known':['for','as'],'confronted':['with'],'confront':['with'],'adjust':['for','to'],'beg':['to'],
}


def sq_table(no):
    """文章速查表：{词(小写): 释义}"""
    md = glob.glob(f'{ROOT}/新版定稿/{no}-*.md')
    if not md: return {}
    t = open(md[0]).read(); t = t.split('## 速查表', 1)[1] if '## 速查表' in t else ''
    out = {}
    for l in re.split(r'\n## ', t)[0].splitlines():
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if len(c) >= 2 and c[0] not in ('词', '---', ''): out[c[0].lower()] = c[1]
    return out


def _lemma(w, sq):
    m = re.match(r'\s*[a-z./ ]*\s*\(([A-Za-z][A-Za-z ]*?)(?: 的[^)]*)?\)', sq.get(w.lower(), ''))
    if m: return m.group(1).split()[0].lower()
    x = w.lower()
    for suf, rep in (('ied', 'y'), ('ies', 'y'), ('ing', ''), ('ed', ''), ('es', ''), ('s', '')):
        if x.endswith(suf) and len(x) - len(suf) >= 3: return x[:-len(suf)] + rep
    return x


def _ph_pats(text, lem, word):
    return {m.group(3).lower() for m in re.finditer(r"\b(" + re.escape(lem) + r"\w*|" + re.escape(word.lower()) + r")\b((?:\s+" + PH_SLOT + r")*)\s+(" + '|'.join(PH_PREPS) + r")\b", text, re.I)}


def phrase_checks(d, no):
    """[T22] 返回待确认列表"""
    sq = sq_table(no); ok = d.get('核对确认', {}).get('短语', {}); out = []
    for i, s in enumerate(d['sentences'], 1):
        en = ' '.join(c['en'] for c in s['chunks']); notes = ' '.join(c.get('note', '') for c in s['chunks'])
        keys = [k.lower().split() for c in s['chunks'] for k in re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)', c['zh'])]
        toks = []
        for m in re.finditer(r'\*\*([^*]+)\*\*|([^*\s]+)', re.sub(r'\{\{.*?\}\}', '', en)):
            toks += [(w, True) for w in m.group(1).split()] if m.group(1) else [(m.group(2), False)]
        for j, (w, b) in enumerate(toks):
            wc = re.sub(r"[^\w'-]", '', w)
            if not b or not wc: continue
            # 反方向：介词紧挨在名词重点词前面、中间没有冠词（09 S3 in **flocks**、S5 In **desperation**，用户 2026-10-10：“In desperation，作为整体，
            # 作为一个整体。而不是单独desperation。”）——零冠词的“介词 + 名词”多是固定用法；名词看速查表词性（n.），速查表没有这一行也报
            pv = re.sub(r"[^\w'-]", '', toks[j - 1][0]).lower() if j else ''
            if pv in PH_BACK and not toks[j - 1][1] and re.match(r'(n\.|$)', sq.get(wc.lower(), '')):
                key = f'S{i} {pv} … {wc}'
                if key not in ok and not any(pv in k and wc.lower() in k for k in keys):
                    out.append(f'[T22] {key}「{toks[j - 1][0]} {w}」  ← 介词 + 名词的固定用法（in flocks、in desperation）只标了名词？是就整体加粗、同色，中文意思标全（T23）；不是就核实后写进 核对确认.短语')
            lem = _lemma(wc, sq)
            preps = _ph_pats(sq.get(wc.lower(), '') + ' ' + sq.get(lem, '') + ' ' + notes, lem, wc) | set(PH_CORE.get(lem, []))
            for prep in sorted(preps):
                for q in range(j + 1, min(len(toks), j + 7)):
                    t, bb = toks[q]
                    if re.sub(r"[^\w'-]", '', t).lower() == prep:
                        if not bb and not any(prep in k and wc.lower() in k for k in keys):
                            key = f'S{i} {wc} … {prep}'
                            if key not in ok: out.append(f'[T22] {key}「{" ".join(x for x, _ in toks[j:q + 1])}」  ← 重点词的短语型用法只标了一个词？是固定搭配就整体加粗、同色（被隔开的按 T14），不是就核实后写进 核对确认.短语')
                        break
                    if re.search(r'[,;:.!?]$', t): break
    return out


def selftest_phrase():
    """T22 自检：07 的 **stems from**、02 的 **depends** partly **on** 去掉介词的加粗，必须报出；原样不报这两处"""
    fails = []
    for no, si, en0, en1, k0, k1, key in (('07', 6, '**stems from**', '**stems** from', '(stems from)', '(stems)', 'stems … from'),
                                          ('02', 15, '**depends** partly **on**', '**depends** partly on', '(depends on)', '(depends)', 'depends … on')):
        base = json.load(open(f'{V}/脚本/{no}.json'))
        if any(key in x for x in phrase_checks(base, no)): fails.append(f'T22 原稿误报：{no} {key}')
        d = copy.deepcopy(base); hit = False
        for c in d['sentences'][si]['chunks']:
            if en0 in c['en']:
                c['en'] = c['en'].replace(en0, en1); c['align'] = [[a.replace(en0, en1), z.replace(k0, k1)] for a, z in c['align']]
                c['zh'] = c['zh'].replace(k0, k1); hit = True
        if not hit: fails.append(f'T22 自检样本找不到：{no} S{si + 1} {en0}')
        elif not any(key in x for x in phrase_checks(d, no)): fails.append(f'没抓到：短语只标一个词（T22，{no} {en1}）')
    # 反方向（介词 + 名词）：09 S5 造成只标 desperation 必须报出；整体标 In desperation 不报（不依赖 09 脚本现在改没改）
    base = json.load(open(f'{V}/脚本/09.json'))
    for en_, zh_, want in (('In **desperation**,', '**绝望**(desperation)之中，', True), ('**In desperation**,', '**绝望之中**(In desperation)，', False)):
        d = copy.deepcopy(base); c = d['sentences'][4]['chunks'][0]
        if 'desperation' not in c['en']: fails.append('T22 自检样本找不到：09 S5 desperation'); break
        c['en'], c['zh'], c['align'] = en_, zh_, [[en_, zh_]]
        got = any('S5 in … desperation' in x for x in phrase_checks(d, '09'))
        if got != want: fails.append('没抓到：介词 + 名词只标名词（T22，09 In **desperation**）' if want else 'T22 误报：整体标的 **In desperation** 被报出')
    return fails


# T23 中文意思只标了一部分（用户 2026-10-10 看 08 初稿：“Vindicate 他的意思是证明什么什么是对的……但是你在标注的时候只标注了一个，
# 证明了后面那个对的却没有标注上……如果说要标注一个单词的意思，你标注全了，你不要说只标注一部分”）：
# 速查表释义里写成“证明……正确”“把……归因于”“在……期间”这种被隔开的意思，中文里只标了其中一处（这个词只有一个 **…**(词) 标记），
# 而标了的那一处正是这个意思的一半 → 报出。改法：两处都标同一个英文，如 反倒**证明了**(vindicating)斯诺是**正确的**(vindicating)；
# 不是这个意思的（本句用的是别的义项），核实后写进 核对确认.中文意思："S17 vindicating": "理由"。
def _zh_parts(defn):
    out = []
    for item in re.split(r'[；;，,]', re.sub(r'（[^）]*）|\([^)]*\)', '', defn)):
        if '……' in item:
            a, b = item.split('……', 1)
            a = re.findall(r'[一-鿿]+$', a); b = re.findall(r'^[一-鿿]+', b)
            if a and b: out.append((a[0][-4:], b[0][:4]))
    return out


def _overlap(x, y):
    return any(x[i:i + 2] in y for i in range(len(x) - 1)) or (len(x) == 1 and x in y) or (len(y) == 1 and y in x)


def meaning_checks(d, no):
    """[T23] 返回待确认列表"""
    sq = sq_table(no); ok = d.get('核对确认', {}).get('中文意思', {}); out = []
    for i, s in enumerate(d['sentences'], 1):
        zh = ''.join(c['zh'] for c in s['chunks'])
        marks = re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)', zh)
        for k in dict.fromkeys(m for _, m in marks):
            got = [z for z, m in marks if m == k]
            if len(got) != 1: continue
            defn = sq.get(k.lower(), '') or sq.get(_lemma(k, sq), '')
            for a, b in _zh_parts(defn):
                if _overlap(got[0], a) or _overlap(got[0], b):
                    key = f'S{i} {k}'
                    if key not in ok: out.append(f'[T23] {key}：意思是“{a}……{b}”，中文只标了“{got[0]}”一处  ← 被隔开的意思两处都要标同一个英文（如 **证明了**(vindicating)……**正确的**(vindicating)）；不是这个义项的核实后写进 核对确认.中文意思')
                    break
    return out


def selftest_meaning():
    """T23 自检：08 S17 定稿两处都标了 vindicating（证明了……正确的），原样不报；去掉“正确的”的标记、只剩“证明了”一处，必须报出"""
    fails = []; base = json.load(open(f'{V}/脚本/08.json'))
    if any('S17 vindicating' in x for x in meaning_checks(base, '08')): fails.append('T23 误报：两处都标了仍报出（08 S17 vindicating）')
    d = copy.deepcopy(base); hit = False
    for c in d['sentences'][16]['chunks']:
        if '**正确的**(vindicating)' in c['zh']:
            c['zh'] = c['zh'].replace('**正确的**(vindicating)', '正确的'); c['align'] = [[a, z.replace('**正确的**(vindicating)', '正确的')] for a, z in c['align']]; hit = True
    if not hit: fails.append('T23 自检样本找不到：08 S17 **正确的**(vindicating)')
    elif not any('S17 vindicating' in x for x in meaning_checks(d, '08')): fails.append('没抓到：中文意思只标一部分（T23，08 S17 vindicating）')
    return fails


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
    def t24(d):
        c = d['sentences'][2]['chunks'][0]; c['zh'] += '（觉得这样更体面）'; c['align'][-1] = [c['align'][-1][0], c['align'][-1][1] + '（觉得这样更体面）']
    mut('括号说明里有语音输入多出来的“觉得”（T24）', 'T24', t24)
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


def check_all_text(no, js, stage='出片'):
    """check_all.py（D1–D4、撞词 T12、速查表 S2）；视频文件出片后才有，不算；
    文本阶段：本篇的对照文本正是 生成文本.py 接下来要生成的（生成后逐格读回核对），新篇第一次生成时还没有，不算"""
    r = subprocess.run(['python3', f'{T}/check_all.py', no, js], capture_output=True, text=True)
    skip = ('缺文件: 视频/视频/',) + ((f'缺文件: 视频/对照文本/{no}-文本',) if stage == '文本' else ())
    return [l for l in (r.stdout + r.stderr).splitlines() if l.strip() and '全部检查通过' not in l and not l.startswith(skip)]


# T25 用户给的释义只写进了速查表、画面上没有（08 S17 set out to；用户 2026-10-10：“set out to do something 的意思是：带着明确的目标开始做某事，
# 或者下定决心要去完成某事。……为什么下面的翻译为什么没有这个解说呢？”）：待改清单里用户原话中“……的意思是：……”“……下面要有：……”给出的释义，
# 必须出现在画面的中文里（去掉标点、换行、颜色标记后比对）。
def _gloss_norm(t): return re.sub(r'[\s，。、；：:,;.（）()“”"\'·…—\-]', '', re.sub(r'\{\{([^|{}]+)\|[^{}]+\}\}', r'\1', t))
# 待改清单逐条落实（09 起，用户 2026-10-10：“要改的东西，我们最后统一修改”）：每一条写明改完后的原文——
# “画面上要有：`…`”“英文要有：`…`”“画面上不要有：`…`”（反引号里逐字照脚本写），出片前逐字比对脚本，漏改一条就停。
def user_gloss_checks(d, no, txt=None):
    if txt is None:
        f = f'{V}/制作记录/{no}_待改清单.md'
        if not os.path.exists(f): return []
        txt = open(f).read()
    zh = _gloss_norm(''.join(c['zh'] + c.get('note', '') for s in d['sentences'] for c in s['chunks']))   # note 也在画面上（09 S18 结局解读放在 note 里）
    out = []
    for m in re.finditer(r'(?:的意思是|下面要有)[：:]\s*([^。”\n]+)', txt):
        g = _gloss_norm(m.group(1))
        if len(g) >= 4 and g not in zh: out.append(f'[T25] 待改清单里用户给的释义“{m.group(1)[:40]}”没有出现在画面上（要在这个词的中文正下方加同色括号）')
    zhs = [c['zh'] for s in d['sentences'] for c in s['chunks']] + [c.get('note', '') for s in d['sentences'] for c in s['chunks']]; ens = [c['en'] for s in d['sentences'] for c in s['chunks']]
    for k, x in re.findall(r'(画面上要有|英文要有|画面上不要有)[：:]\s*`([^`]+)`', txt):
        if any(x in t for t in (ens if k == '英文要有' else zhs)) == (k == '画面上不要有'):
            out.append(f'[T25] 待改清单里“{k}：{x[:40]}”没有落实（用户要改的地方漏改了）')
    return sorted(set(out))
# T26 同一篇里两个不同的重点词用了同一个中文（09 用户把 payout 改成“赏金”，S18 payments 原来也是“赏金”）：学生分不清哪个是哪个，报出待确认；
# 同一个词的不同形式（flock / flocks）、被隔开的同一个意思（**把**(likened to)…**比作**(likened to)）不算。确实要一样的写进 核对确认.中文重复：{"赏金": "理由"}。
def zh_dup_checks(d):
    ok = d.get('核对确认', {}).get('中文重复', {}); seen = {}
    for s_ in d['sentences']:
        for c in s_['chunks']:
            for z, e in re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)', c['zh']): seen.setdefault(z, set()).add(e.lower())
    return [f'[T26] 中文“{z}”同时是 {"、".join(sorted(es))} 的意思——两个不同的重点词用了同一个中文，学生分不清；换一个，确实要一样就写进 核对确认.中文重复'
            for z, es in sorted(seen.items()) if len({re.sub(r'(ies|es|s|ed|ing)$', '', e) for e in es}) > 1 and z not in ok]
def selftest_zhdup():
    """T26 自检：09 原样不报；把 S17 payout 和 S18 payments 的中文都改成“赏金”（09 草稿修改时出过的情况），必须报出——不依赖 09 现在的写法"""
    base = json.load(open(f'{V}/脚本/09.json')); fails = []
    if zh_dup_checks(base): fails.append('T26 误报：09 原样被报出：' + '；'.join(zh_dup_checks(base)))
    d = copy.deepcopy(base); hit = 0
    for s_ in d['sentences'][16:18]:
        for c in s_['chunks']:
            for k in ('payout', 'payments'):
                if f'({k})' in c['zh']: c['zh'] = re.sub(r'\*\*[^*]+\*\*\(' + k + r'\)', f'**赏金**({k})', c['zh']); hit += 1
    if hit < 2: fails.append('T26 自检样本找不到：09 S17 payout、S18 payments')
    elif not any('赏金' in x for x in zh_dup_checks(d)): fails.append('没抓到：两个重点词用了同一个中文（T26，09 payout/payments 赏金）')
    return fails
def selftest_gloss():
    """T25 自检：08 定稿原样不报；去掉 S17 set out to 下面的说明，必须报出；待改清单逐条落实：已落实的不报，没落实的必须报出"""
    base = json.load(open(f'{V}/脚本/08.json')); fails = []
    if user_gloss_checks(base, '08'): fails.append('T25 误报：08 定稿原样被报出：' + '；'.join(user_gloss_checks(base, '08')))
    ok_ = '画面上要有：`**丧生**(perished)。`\n英文要有：`**attributed** **epidemics** **to** miasma`\n画面上不要有：`**丧命**(perished)`'
    if user_gloss_checks(base, '08', ok_): fails.append('T25 误报：08 已落实的改动被报出：' + '；'.join(user_gloss_checks(base, '08', ok_)))
    for bad_ in ('画面上要有：`**丧命**(perished)`', '英文要有：`**attributed** epidemics`', '画面上不要有：`**丧生**(perished)`'):
        if not user_gloss_checks(base, '08', bad_): fails.append(f'没抓到：待改清单的改动没落实（T25，{bad_}）')
    d = copy.deepcopy(base); hit = False
    for c in d['sentences'][16]['chunks']:
        if '带着明确的目标' in c['zh']:
            c['zh'] = re.sub(r'\n\{\{[^{}]*\|set out to\}\}', '', c['zh']); hit = True
    if not hit: fails.append('T25 自检样本找不到：08 S17 set out to 的说明')
    elif not user_gloss_checks(d, '08'): fails.append('没抓到：用户给的释义没上画面（T25，08 S17 set out to）')
    return fails


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
    fails = selftest() + selftest_folders() + selftest_phrase() + selftest_meaning() + selftest_gloss() + selftest_zhdup()
    print('核查程序自检：' + ('通过（每一种造出来的坑都抓到，原稿无误报）' if not fails else '【失灵】' + '；'.join(fails)))
    if fails: print('【核查程序失灵，不得交付】'); return 1
    if args and args[0] == '自检': return 0
    no, stage = args[0].zfill(2), args[1]
    js = f'scripts/{no}.json' if os.path.exists(f'scripts/{no}.json') else f'{V}/脚本/{no}.json'
    d = json.load(open(js)); snap = f'{V}/脚本/已发版本/{no}.json'
    sent = json.load(open(snap)) if os.path.exists(snap) else None
    err = record_gate(no, stage) + video_folders(ROOT)
    e, conf, ref = text_checks(d, article_en(no), sent); err += e
    # T22 只查以后新做的篇目（09 起）。用户 2026-10-10：“以后查就行，已经做完了，这几天不要再查了……刚刚做完这篇，你查啥？不用再查了，又浪费时间……以后每次都要（查）”
    # 已做完的 01–08 不回头查；08 只改用户点名的 S2 attributed … to（制作记录/08_待改清单.md）
    if int(no) >= 9: conf += phrase_checks(d, no)
    if int(no) >= 9: conf += meaning_checks(d, no)                 # T23 同样只查以后新做的篇目（用户：“以后我们再去做的时候……防止再犯”）
    if int(no) >= 9: conf += zh_dup_checks(d)                      # T26 两个重点词同一个中文（09 起）
    err += user_gloss_checks(d, no)                                # T25 用户给的释义要上画面（有待改清单的篇目都查）
    err += [f'[check_all] {x}' for x in check_all_text(no, os.path.abspath(js), stage)]
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
