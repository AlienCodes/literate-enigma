#!/usr/bin/env python3
"""译文核查（规则执行机器，CLAUDE.md 第16条）：只有人能判的译文规矩，程序先把“可能有问题、必须有人核对”的地方逐个点名，
核对结论写进脚本 核对确认 或 逐句确认，没核对就不放行（踩坑核查 调用，21 起；已定稿的篇目不回头查）。
  [T9对齐]  对齐粗细以 01–03 为准：全篇平均每组超过 3 个英文词就停；5 个词以上的组逐个点名（用户 2026-10-23：“下面这个汉译尽量跟它所对应的这个英文最好对齐”）
  [T4方向]  before/after、增/减、多/少 这类方向词，中文对应那一格里没有同方向的字（05 S11 before 放在“之后才”上面）
  [T2词性]  速查表写 adj. 的重点词中文以“地”结尾、adv. 以“的”结尾、n. 以“地”结尾（earnest 译成“真心实意地”）
  [文10]    同一个英文重点词，全篇译法不一（抽象概念全篇统一用词）
  [W3]      中文里出现“放到…正下方”“改为”这类排版指令（用户写进译文的指令要转成 note，不能当译文）
  [T10改稿] 和上次发给用户的版本（脚本/已发版本/NN.json）比，中文、说明改了的字在待改清单（用户原话）里找不到——
            已定稿、已发给用户的中文，没有用户允许一律不改（铁13、守则4“说啥只改啥”）
  [逐句确认] 这一句是新的或改过（指纹对不上 制作记录/逐句确认/NN.json）：逐条核对 T2/T3 词性、T4 方向、T5 不横跨、T7 通顺、
            T8 读者看得懂、T9 对齐粗细、T13 整句读通、T21 重点词贴合语境 后，跑 python3 工具/逐句确认.py NN S几 "核对结论"
python3 译文核查.py --自检"""
import re, json, os, sys, hashlib, difflib, copy
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
起始篇 = 21
DIR = [(r'\bbefore\b', '前早先'), (r'\bafter(wards)?\b', '后之后随'), (r'\bearlier\b', '前早先'), (r'\blater\b', '后晚'),
       (r'\bincreas(e|es|ed|ing)\b', '增升涨提加多'), (r'\b(rise|rises|rose|risen|rising)\b', '升涨增上起'),
       (r'\bdecreas(e|es|ed|ing)\b', '减降跌少下'), (r'\b(decline|declines|declined|declining)\b', '降减衰少下拒'),
       (r'\bmore\b', '多更越'), (r'\b(less|fewer)\b', '少更减')]
PUN = '，。、：；！？（）《》“”‘’,.;:!?()…  '


def 去标(x):
    """比内容用：去掉加粗、重点词英文标注、格内换行、空格、彩色说明的外壳"""
    x = re.sub(r'\{\{([^|{}]+)\|[^{}]+\}\}', r'\1', x or '')
    x = re.sub(r'\*\*([^*]+)\*\*\([^)]*\)', r'\1', x).replace('**', '')
    return re.sub(r'[\s ]|#Y|\\n', '', x)


def 方向(d, ok):
    out = []
    for i, s in enumerate(d['sentences']):
        for k, c in enumerate(s['chunks']):
            for en, zh in c['align']:
                e_ = re.sub(r'\*\*|\{\{.*?\}\}', '', en).lower(); z_ = 去标(zh)
                for pat, chs in DIR:
                    m = re.search(pat, e_)
                    if m and not any(ch in z_ for ch in chs):
                        key = f'S{i + 1}-{k + 1} {m.group(0)}→{z_[:12]}'
                        if key not in ok.get('方向', {}): out.append(f'[T4方向] {key}  ← 方向词的中文里没有同方向的字（before 放在“之后”上面？），核对后写进 核对确认.方向')
    return out


def 词性(d, art, ok):
    pos = {}
    for l in (art or '').split('## 速查表', 1)[-1].splitlines():
        m = re.match(r'\|\s*([^|]+?)\s*\|\s*(?:本文：[^|]*?；\s*)?(adj|adv|n|v|vt|vi)\.', l)   # 速查表：“本文：…；词性. 释义”
        if m: pos[m.group(1).lower()] = m.group(2)
    out = []
    for i, s in enumerate(d['sentences']):
        for k, c in enumerate(s['chunks']):
            for zh, w in re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)', c['zh']):
                p = pos.get(w.lower()); bad = (p == 'adj' and zh.endswith('地')) or (p == 'adv' and zh.endswith('的')) or (p == 'n' and zh.endswith('地'))
                key = f'S{i + 1}-{k + 1} {w} {zh}'
                if bad and key not in ok.get('词性', {}): out.append(f'[T2词性] {key}  ← 速查表是 {p}.，中文词性对不上（adj. 不用“地”，adv. 不用“的”），核对后写进 核对确认.词性')
    return out


def 同词异译(d, ok):
    m_ = {}
    for s in d['sentences']:
        for c in s['chunks']:
            for zh, w in re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)', c['zh']): m_.setdefault(w.lower(), set()).add(zh)
    out = []
    for w, zs in m_.items():
        key = f'{w}：{"/".join(sorted(zs))}'
        if len(zs) > 1 and key not in ok.get('同词异译', {}): out.append(f'[文10] {key}  ← 同一个英文重点词全篇译法不一（抽象概念全篇统一用词），核对后写进 核对确认.同词异译')
    return out


def 排版指令(d, ok):
    out = []
    for i, s in enumerate(d['sentences']):
        for k, c in enumerate(s['chunks']):
            for m in re.finditer(r'放到|移到|正下方|正上方|改为|改成|加在|去掉|删掉|删去', re.sub(r'\{\{.*?\}\}', '', c['zh'])):
                key = f'S{i + 1}-{k + 1} {m.group(0)}'
                if key not in ok.get('排版指令', {}): out.append(f'[W3] {key}  ← 中文里像是用户写的排版指令（要转成 note，不能当译文），核对后写进 核对确认.排版指令')
    return out


def 改稿门(d, old, 清单):
    """old：上次发给用户的脚本；清单：待改清单全文（用户原话）。改了的字（新加的、删掉的）都必须在清单里找得到"""
    if not old: return []
    q = 去标(清单); out = []
    for i, (s, s0) in enumerate(zip(d['sentences'], old['sentences'])):
        for k, (c, c0) in enumerate(zip(s['chunks'], s0['chunks'])):
            for what, a, b in (('中文', c0.get('zh'), c.get('zh')), ('说明', c0.get('note'), c.get('note'))):
                a, b = 去标(a), 去标(b)
                if a == b: continue
                if sorted(a) == sorted(b) and '对齐' in 清单: continue   # 只按英文语序调了中文先后、字一个不变（T9 对齐，待改清单里有用户“对齐”原话）
                for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
                    if tag == 'equal': continue
                    for seg in (b[j1:j2], a[i1:i2]):
                        s_ = seg.strip(PUN)
                        if not s_ or (len(s_) == 1 and s_ in '的地得了着过们'): continue
                        if s_ not in q:
                            out.append(f'[T10改稿] S{i + 1} 第{k + 1}块{what}改了“{s_[:20]}”，待改清单（用户原话）里找不到——已发给用户的中文没有用户允许一律不改（铁13，守则4：说啥只改啥）')
                            break
    return out


def 词数(a): return len(re.findall(r"[A-Za-z0-9][\w'’-]*", re.sub(r'\{\{.*?\}\}|\*\*', '', a)))


def 对齐(d, ok):
    """[T9对齐] 用户 2026-10-23（22 S15）：“下面这个汉译尽量跟它所对应的这个英文最好对齐”；文6 对齐粗细以 01–03 为准（平均每组 1.75–2.67 个英文词）。
    返回 (错误, 待确认)：全篇平均每组超过 3 个英文词就停；5 个词以上的组逐个点名，能拆就拆，确实是语序必须倒过来的写进 核对确认.对齐"""
    g = [(i, k, a) for i, s in enumerate(d['sentences']) for k, c in enumerate(s['chunks']) for a, _ in c['align'] if a != '\n' and 词数(a) > 0]
    if not g: return [], []
    avg = sum(词数(a) for *_, a in g) / len(g); err, conf = [], []
    if avg > 3.0: err.append(f'[T9对齐] 全篇平均每组 {avg:.2f} 个英文词，比 01–03 定稿（1.75–2.67）粗：中英语序一致的地方逐词或按意群拆开，每个中文放在它对应的英文正下方（用户 2026-10-23：“下面这个汉译尽量跟它所对应的这个英文最好对齐”）')
    for i, k, a in g:
        n = 词数(a); key = f'S{i + 1}-{k + 1} {re.sub(r"[*]", "", a)[:30]}'
        if n >= 5 and key not in ok.get('对齐', {}):
            conf.append(f'[T9对齐] {key}  ← 这一组 {n} 个英文词：能拆就拆到词或意群；确实是语序必须倒过来（后置定语、从句、of 结构、提前的介词短语、同位语）的，在 核对确认.对齐 写明原因')
    return err, conf


_K = re.compile(r'\*\*[^*]+\*\*')
_ZK = re.compile(r'(\*\*[^*]+\*\*\([^)]*\))')
_标点 = re.compile(r'^[\s，。、；：！？“”‘’（）《》…—\-,.;:!?()"\'·]*$')
def 同序(a, b):
    """一组里两个以上重点词，中文里重点词的先后和英文一样（倒装的不算）"""
    ks = [x.lower() for x in _K.findall(a)]
    zs = ['**' + x.split('**(')[1][:-1].lower() + '**' for x in _ZK.findall(b) if '**(' in x]
    return len(ks) >= 2 and ks == zs
def 拆(a, b):
    """[T34] 把同序的多重点词组拆开：每个重点词带着它的中文单独一组；重点词之间的英文和中文一一对得上就单独一组，
    没有中文的英文（a、the）跟着后面的重点词，标点跟着前面的。英文按空格切（拼回去一字不差），中文只切不改（D2）。不同序返回 None"""
    if not 同序(a, b): return None
    toks = re.sub(r'\{\{.*?\}\}', lambda m: m.group(0).replace(' ', '\0'), a).split(' ')
    units, cur, depth = [], [], 0   # 英文：('K', 文) 重点词（可能跨几个空格）或 ('E', 文)
    for tk in toks:
        n = tk.count('**')
        if depth or n:
            cur.append(tk); depth = (depth + n) % 2
            if not depth: units.append(['K', ' '.join(cur)]); cur = []
        elif units and not re.search(r'[A-Za-z0-9]', tk.replace('\0', ' ')): units[-1][1] += ' ' + tk   # 纯标点跟前面
        else: units.append(['E', tk])
    E, K = [[]], []
    for ty, x in units:
        if ty == 'K': K.append(x); E.append([])
        else: E[-1].append(x)
    E = [' '.join(e).replace('\0', ' ') for e in E]; K = [k.replace('\0', ' ') for k in K]
    C = _ZK.split(b); Z, C = C[1::2], C[0::2]
    if len(K) != len(Z) or len(E) != len(C): return None
    out, pre_e, pre_z = [], '', ''
    def 单独(e, c):   # 稳妥才单独成组：英文 ≤2 个词、中文 ≤3 个字、不是“……的”（“的”结尾多半是后置定语提前，如 of the modern computer → 现代计算机的）
        z = re.sub(r'[^\u4e00-\u9fff]', '', c)
        return bool(e) and 0 < len(z) <= 3 and 词数(e) <= 2 and not z.endswith('的')
    if 单独(E[0], C[0]): out.append([E[0], C[0]])
    else: pre_e, pre_z = E[0], C[0]
    for i in range(len(K)):
        g = [(pre_e + ' ' + K[i]).strip(), pre_z + Z[i]]; pre_e = pre_z = ''
        e, c = E[i + 1], C[i + 1]
        if i < len(K) - 1 and 单独(e, c): out += [g, [e, c]]
        elif i < len(K) - 1: g[1] += c; out.append(g); pre_e = e   # 中间拿不准的：中文跟前一个重点词，英文跟后一个
        else: g[0] = (g[0] + ' ' + e).strip(); g[1] += c; out.append(g)
    assert ' '.join(x for x, _ in out) == a and ''.join(y for _, y in out) == b, (a, b, out)
    return out
def 同序组(d, ok):
    """[T34] 用户 2026-10-23 看 23：“这个避免它还是没有完美的对应到这个avert的下面……才智也没有非常精准的放到这个intellect的下面……立一道闸”。
    一组里两个以上重点词、中文先后和英文一样 → 必须拆开，每个重点词的中文在它自己的英文正下方；倒装的（an emblem of virtue → 美德的象征）照旧整组。
    例外只认用户同意：核对确认.同序 里这一组的说明含“用户”"""
    err = []
    for i, s in enumerate(d['sentences']):
        for k, c in enumerate(s['chunks']):
            for a, b in c['align']:
                if a == '\n' or not 同序(a, b): continue
                key = f'S{i + 1}-{k + 1} {re.sub(r"[*]", "", a)[:30]}'
                if '用户' in ok.get('同序', {}).get(key, ''): continue
                err.append(f'[T34] {key}  ← 两个以上重点词挤在一组、中文先后和英文一样：拆开，每个重点词的中文放在它自己的英文正下方。'
                           f'自动拆（中文一字不改）：python3 工具/拆分组.py NN --写入')
    return err


def 比较结构(d, ok):
    """[T13] 比较、倍数结构（half as strong as、twice as、three times as、as … as）：01 S? “……的一半”单独放一格整句读不通。逐个点名核对整组处理、整句读得通"""
    out = []
    for i, s in enumerate(d['sentences']):
        en = ' '.join(re.sub(r'\*\*|\{\{.*?\}\}', '', c['en']) for c in s['chunks'])
        for m in re.finditer(r"\b(half|twice|(?:\w+) times) as \w+ as\b|\bas (?:\w+ ){1,2}as\b", en, re.I):
            key = f'S{i + 1} {m.group(0)}'
            if key not in ok.get('比较结构', {}): out.append(f'[T13] {key}  ← 比较、倍数结构：整组处理、整句读得通（“……的一半”不能单独放一格），核对后写进 核对确认.比较结构')
    return out


def 指纹(s):
    return hashlib.sha1(json.dumps([(c.get('en'), c.get('zh'), c.get('note'), c.get('align')) for c in s['chunks']], ensure_ascii=False).encode()).hexdigest()[:12]


def 逐句(d, rec):
    out = []
    for i, s in enumerate(d['sentences']):
        r = rec.get(f'S{i + 1}')
        if not r or r.get('指纹') != 指纹(s):
            out.append(f'[逐句确认] S{i + 1} 是新的或改过：逐条核对 T2/T3 词性、T4 方向、T5 不横跨、T7 通顺、T8 读者看得懂、T9 对齐粗细、T13 整句读通、T21 重点词贴合语境，'
                       f'再跑 python3 工具/逐句确认.py NN S{i + 1} "核对结论"')
    return out


def 查(d, no, art):
    """踩坑核查 调用：返回 (错误, 待确认)"""
    ok = d.get('核对确认', {})
    if 12 <= int(no) < 起始篇: _e, _c = 对齐(d, ok); return _e + 同序组(d, ok), _c   # T9 对齐 12 起：用户 2026-10-23 选定 12–20、22 也按标准重新对齐、重出 4K；T34 同序重点词必须拆开
    if int(no) < 起始篇: return [], []
    def 读(p, j=False):
        try: return json.load(open(p)) if j else open(p).read()
        except Exception: return {} if j else ''
    err = 改稿门(d, 读(f'{V}/脚本/已发版本/{no}.json', True), 读(f'{V}/制作记录/{no}_待改清单.md'))
    _ae, _ac = 对齐(d, ok); err += _ae + 同序组(d, ok)
    conf = _ac + 比较结构(d, ok) + 方向(d, ok) + 词性(d, art, ok) + 同词异译(d, ok) + 排版指令(d, ok) + [x.replace(' NN ', f' {no} ') for x in 逐句(d, 读(f'{V}/制作记录/逐句确认/{no}.json', True))]
    return err, conf


def 自检():
    """每一项造一个错例（必须报出）和正例（不得误报）"""
    fails = []
    def 句(*pairs): return {'chunks': [{'en': ' '.join(a for a, _ in pairs), 'zh': ''.join(b for _, b in pairs), 'align': [list(p) for p in pairs]}]}
    d = {'sentences': [句(('He came', '他来了'), ('before the war', '在战争之前'))]}
    if 方向(d, {}): fails.append('T4方向 误报：before → 之前')
    d2 = copy.deepcopy(d); d2['sentences'][0]['chunks'][0]['align'][1][1] = '之后才'
    if not 方向(d2, {}): fails.append('没抓到：before 放在“之后才”上面（T4/T20）')
    art = '## 速查表\n| earnest | 本文：真心实意的；adj. 认真的，真诚的（an earnest wish） | 1 |\n'
    if not 词性({'sentences': [句(('in earnest', '**真心实意地**(earnest)'))]}, art, {}): fails.append('没抓到：adj. 译成“…地”（T2）')
    if 词性({'sentences': [句(('in earnest', '**真心实意的**(earnest)'))]}, art, {}): fails.append('T2词性 误报')
    if not 同词异译({'sentences': [句(('scan', '**扫描**(scan)')), 句(('scan', '**浏览**(scan)'))]}, {}): fails.append('没抓到：同一个重点词全篇译法不一（文10）')
    if 同词异译({'sentences': [句(('scan', '**扫描**(scan)')), 句(('scan', '**扫描**(scan)'))]}, {}): fails.append('文10 误报')
    if not 排版指令({'sentences': [句(('it', '它（放到翻译的正下方）'))]}, {}): fails.append('没抓到：译文里的排版指令（W3）')
    old = {'sentences': [句(('Prices soared', '价格一路飙升'))]}; new = copy.deepcopy(old); new['sentences'][0]['chunks'][0]['zh'] = '价格暴涨'
    if not 改稿门(new, old, '用户：这一句不用改'): fails.append('没抓到：没有用户原话就改了已发的中文（T10/铁13）')
    if 改稿门(new, old, '用户原话：“价格暴涨” 一路飙升 改为 暴涨'): fails.append('T10改稿 误报：用户原话里有的改动')
    if 改稿门(old, old, ''): fails.append('T10改稿 误报：没改')
    re_ = copy.deepcopy(old); re_['sentences'][0]['chunks'][0]['zh'] = '一路飙升价格'
    if 改稿门(re_, old, '用户原话：汉译尽量跟英文对齐'): fails.append('T10改稿 误报：只为对齐调了中文先后')
    if not 改稿门(re_, old, '用户：这一句不用改'): fails.append('没抓到：没有用户原话就调了中文先后（T10）')
    if not 比较结构({'sentences': [句(('half as strong as', '……的一半那么强'))]}, {}): fails.append('没抓到：比较、倍数结构（T13）')
    if 比较结构({'sentences': [句(('as a child', '小时候'))]}, {}): fails.append('T13 误报：as a child')
    细 = {'sentences': [句(('He', '他'), ('came', '来了'), ('before the war', '在战争之前'))]}
    粗 = {'sentences': [句(('He came to the city before the war began', '他在战争开始前来到这座城市'))]}
    if 对齐(细, {}) != ([], []): fails.append('T9对齐 误报：逐词对齐的句子')
    e_, c_ = 对齐(粗, {})
    if not e_: fails.append('没抓到：全篇对齐比 01–03 粗（T9/文6）')
    if not c_: fails.append('没抓到：一组塞了 9 个英文词（T9/文6）')
    if 对齐(粗, {'对齐': {c_[0].split('  ←')[0][len('[T9对齐] '):]: '整句语序倒装'}})[1]: fails.append('T9对齐 误报：写了原因的组')
    坏 = {'sentences': [句(('a **formidable** **intellect**', '**强大的**(formidable)**才智**(intellect)，'))]}
    if not 同序组(坏, {}): fails.append('没抓到：两个重点词同序挤在一组（T34）')
    if 同序组({'sentences': [句(('an **emblem** of **virtue**,', '**美德**(virtue)的**象征**(emblem)，'))]}, {}): fails.append('T34 误报：倒装的整组')
    if 同序组(坏, {'同序': {'S1-1 a formidable intellect': '我觉得不用拆'}}) == []: fails.append('T34 放行了没有用户同意的例外')
    if 拆('to **avert** **imprisonment**,', '为了**避免**(avert)**入狱**(imprisonment)，') != [['to', '为了'], ['**avert**', '**避免**(avert)'], ['**imprisonment**,', '**入狱**(imprisonment)，']]: fails.append('T34 自动拆错了：to avert imprisonment')
    if 拆('a **formidable** **intellect**', '**强大的**(formidable)**才智**(intellect)，') != [['a **formidable**', '**强大的**(formidable)'], ['**intellect**', '**才智**(intellect)，']]: fails.append('T34 自动拆错了：a formidable intellect')
    _拆后 = {'sentences': [句(*拆('a **formidable** **intellect**', '**强大的**(formidable)**才智**(intellect)，'))]}
    if 同序组(_拆后, {}): fails.append('T34 拆完还报')
    s = 句(('Prices soared', '价格一路飙升')); rec = {'S1': {'指纹': 指纹(s)}}
    if 逐句({'sentences': [s]}, rec): fails.append('逐句确认 误报：确认过、没改的句子')
    s2 = copy.deepcopy(s); s2['chunks'][0]['zh'] = '价格飙升'
    if not 逐句({'sentences': [s2]}, rec): fails.append('没抓到：改过的句子没重新确认（逐句确认）')
    return fails


if __name__ == '__main__':
    if '--自检' in sys.argv:
        f = 自检(); print('译文核查 自检：' + ('通过（对齐粗细、方向词、词性、同词异译、排版指令、改稿门、逐句确认：错例全部报出，正例不误报）' if not f else '失灵！' + '；'.join(f)))
        sys.exit(1 if f else 0)
