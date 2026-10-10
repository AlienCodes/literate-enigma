#!/usr/bin/env python3
"""读音核对（A23，2026-10-09 用户：“每个单词的读音，尤其是这种额外的这种人名啊，或者是物名或者是机构名等等……这个读音一定得是正确的，你不能读错了……我们是权威性的，这个教学性文章你读错了就完蛋了”）。
起因：配音模型的注音程序（espeak 拼读规则）把 07 的 Inky 注成 ɪŋkˈaɪ（“因-凯”），正确是 /ˈɪŋki/，三处全读错，没有任何核查发现。
做法：逐句取配音实际用的音标（出片程序的 phonemes_of：espeak 注音 + 读音改正表 PRON_FIX），逐词与两本独立的发音词典比对：
  ① CMU 发音词典（cmudict，13 万词，美式）；② misaki 美式词典（Kokoro 官方注音词典，gold + silver）。都存在 工具/发音词典/。
  比对口径（只抓会听错的差别）：辅音序列、音节数、重音落在第几个音节、重读音节的元音；弱读元音（ə ɪ ᵻ ɐ ʌ 不重读时）算同一类，
  t/d 闪音 ɾ、喉塞 ʔ 与 t/d 算同一个。与任一本词典的任一读法一致 = 合格。
  报出三类：不一致（配音读法与两本词典都对不上）、词典里没有（必须查权威来源逐个核实）、专有名词（人名、地名、机构名、作品名等，
  不论是否一致都列出来，逐个查权威读音）。
用法（视频工作目录）：python3 读音核对.py NN [NN ...]          列出全部待核实的词
  核实过的写进 scripts/NN.json 的 核对确认.读音：{"Pfungst": {"读音": "ˈfʊŋst", "依据": "…（来源）"}}；配音读法与确认的读音不一致的，
  加进出片程序的 PRON_FIX 改正后重跑，直到“问题数 0”。"""
import re, json, sys, os
sys.path.insert(0, '.')
exec(open('make_video.py').read().split("if __name__")[0])
TD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '发音词典')
CMU = {}
for line in open(f'{TD}/cmudict.dict', encoding='utf-8'):
    p = line.split('#')[0].split()
    if p: CMU.setdefault(re.sub(r'\(\d+\)$', '', p[0]), []).append(p[1:])
MG = json.load(open(f'{TD}/us_gold.json')); MS = json.load(open(f'{TD}/us_silver.json'))
# 已核实读音表（全局，各篇共用）：{"Inky": {"标准读音": "ˈɪŋki", "可接受读音": [...], "判定": "...", "依据": "...", "来源": [url...]}}
VERIFIED = json.load(open(f'{TD}/已核实读音.json')) if os.path.exists(f'{TD}/已核实读音.json') else {}

# ---- 音标 → 粗音位（只保留会听错的区别）----
V_IPA = [('aɪ', 'AY'), ('aʊ', 'AW'), ('ɔɪ', 'OY'), ('eɪ', 'EY'), ('oʊ', 'OW'), ('əʊ', 'OW'), ('ɑː', 'AA'), ('ɔː', 'AO'), ('iː', 'IY'), ('uː', 'UW'),
         ('ɜː', 'ER'), ('ɚ', 'ER'), ('ɝ', 'ER'), ('ɜ', 'ER'), ('A', 'EY'), ('I', 'AY'), ('O', 'OW'), ('W', 'AW'),
         ('Y', 'OY'), ('Q', 'OW'), ('i', 'IY'), ('ɪ', 'IH'), ('ᵻ', 'IH'), ('e', 'EH'), ('ɛ', 'EH'), ('æ', 'AE'), ('a', 'AA'), ('ɑ', 'AA'), ('ɒ', 'AA'),
         ('ɔ', 'AO'), ('o', 'OW'), ('ʊ', 'UH'), ('u', 'UW'), ('ʌ', 'AH'), ('ə', 'AH'), ('ᵊ', 'AH'), ('ɐ', 'AH')]
C_IPA = [('tʃ', 'CH'), ('dʒ', 'JH'), ('ʧ', 'CH'), ('ʤ', 'JH'), ('θ', 'TH'), ('ð', 'DH'), ('ʃ', 'SH'), ('ʒ', 'ZH'), ('ŋ', 'NG'), ('ɹ', 'R'), ('r', 'R'),
         ('ɾ', 'TD'), ('ʔ', 'TD'), ('j', 'Y'), ('ɡ', 'G'), ('g', 'G'), ('p', 'P'), ('b', 'B'), ('t', 'T'), ('d', 'D'), ('k', 'K'), ('f', 'F'), ('v', 'V'),
         ('s', 'S'), ('z', 'Z'), ('h', 'HH'), ('m', 'M'), ('n', 'N'), ('l', 'L'), ('w', 'W'), ('x', 'K'), ('ç', 'HH')]
VOWELS = {v for _, v in V_IPA} | {'AH', 'ER'}


def ipa_phones(s):
    """IPA（espeak 或 misaki 写法）→ [(音位, 重音 0/1/2)]；重音号标在音节开头，记到这个音节的元音上"""
    out = []; i = 0; pend = 0
    # espeak 美式写法：iəɹ / ɪəɹ = /ɪr/（near 的元音）；aɪɚɹ / aʊɚɹ + 元音 = /aɪr/ /aʊr/
    s = s.replace('iəɹ', 'ɪɹ').replace('ɪəɹ', 'ɪɹ').replace('aɪɚɹ', 'aɪɹ').replace('aʊɚɹ', 'aʊɹ')
    while i < len(s):
        ch = s[i]
        if ch in 'ˈˌ': pend = 1 if ch == 'ˈ' else 2; i += 1; continue
        if ch in ' -‿.,;:!?': i += 1; continue
        hit = None
        for sym, ph in V_IPA:
            if s.startswith(sym, i): hit = (sym, ph); break
        if hit and hit[0] in ('A', 'I', 'O', 'W', 'Y', 'Q') and False: hit = None
        if hit:
            out.append((hit[1], pend)); pend = 0; i += len(hit[0]); continue
        for sym, ph in C_IPA:
            if s.startswith(sym, i): hit = (sym, ph); break
        if hit: out.append((hit[1], -1)); i += len(hit[0]); continue
        i += 1                                                   # ̩ 等附加符号
    # ER 后面的 R 并入 ER；ɑɹ ɔɹ ɛɹ ɪɹ 保留 R；相连的同一个辅音（ɹɹ、nn）算一个
    res = []
    for ph, st in out:
        if ph == 'R' and res and res[-1][0] == 'ER': continue
        if st < 0 and res and res[-1] == (ph, st): continue
        res.append((ph, st))
    return res


def arpa_phones(seq):
    res = []
    for p in seq:
        m = re.match(r'([A-Z]+)(\d?)', p); ph, d = m.group(1), m.group(2)
        if ph in VOWELS: res.append((ph, int(d) if d else 0))
        else: res.append((ph, -1))
    out = []
    for ph, st in res:
        if ph == 'R' and out and out[-1][0] == 'ER': continue
        out.append((ph, st))
    return out


def key(phs):
    # /j/ + 元音 与 /i/ + 元音 算同一种读法（stallion /ˈstæljən/ 与 /ˈstæliən/、million）
    phs = [('IY', 0) if (p == 'Y' and s < 0 and i + 1 < len(phs) and phs[i + 1][1] >= 0) else (p, s) for i, (p, s) in enumerate(phs)]
    q = []
    for p, s in phs:
        if q and p in ('IY', 'IH') and s == 0 and q[-1][0] in ('IY', 'IH') and q[-1][1] >= 0: continue    # /ɪ/+/j/ 合并
        q.append((p, s))
    phs = q
    cons = [p for p, s in phs if s < 0]
    vow = [(p, s) for p, s in phs if s >= 0]
    prim = [i for i, (p, s) in enumerate(vow) if s == 1]
    return cons, vow, prim


def _norm_ng(c):
    return ['N' if (x == 'NG' and i + 1 < len(c) and c[i + 1] in ('K', 'G')) else x for i, x in enumerate(c)]


def cons_eq(a, b):
    a, b = _norm_ng(a), _norm_ng(b)
    if len(a) != len(b):
        # 喉塞/闪音可能把 t 吞掉（button bʌʔn），允许少一个 TD
        if abs(len(a) - len(b)) == 1:
            for x, y in ((a, b), (b, a)):
                if len(x) > len(y):
                    for i in range(len(x)):
                        if x[i] in ('TD', 'T', 'D') and cons_eq(x[:i] + x[i + 1:], y): return True
        return False
    for x, y in zip(a, b):
        if x == y: continue
        if 'TD' in (x, y) and {x, y} <= {'TD', 'T', 'D'}: continue
        if {x, y} <= {'HH'} : continue
        return False
    return True


REDUCED = {'AH', 'IH', 'ER', 'UH', 'IY', 'EH'}


def same(tts, ref):
    ca, va, pa = key(tts); cb, vb, pb = key(ref)
    if not cons_eq(ca, cb): return False, '辅音不同'
    if len(va) != len(vb): return False, f'音节数不同（{len(va)} / {len(vb)}）'
    if len(va) >= 2 and pa and pb and not (set(pa) & set(pb)): return False, f'重音位置不同（第 {pa[0] + 1} / 第 {pb[0] + 1} 个音节）'
    for (x, sx), (y, sy) in zip(va, vb):
        stressed = (sx == 1 and sy >= 1) or (sy == 1 and sx >= 1)
        if x == y: continue
        if not stressed and x in REDUCED and y in REDUCED: continue
        if {x, y} in ({'AA', 'AO'}, {'AH', 'UH'}) or (not stressed and {x, y} <= {'AH', 'AA', 'AO', 'OW', 'UW'}): continue   # 美式 cot/caught 合并等
        if stressed: return False, f'重读元音不同（{x} / {y}）'
        return False, f'元音不同（{x} / {y}）'
    return True, ''


def refs(word):
    w0 = re.sub(r"['’]s$", '', word)
    if w0 != word:                                    # 所有格：查原词，读音加 s/z
        return [(src, v + ' +s', ph + [('Z', -1)]) for src, v, ph in refs(w0)] + [(src, v + ' +s', ph + [('S', -1)]) for src, v, ph in refs(w0)] + [(src, v + ' +ɪz', ph + [('IH', 0), ('Z', -1)]) for src, v, ph in refs(w0)]
    if '-' in word:                                   # 连字符词：各部分拼起来
        parts = [refs(x) for x in word.split('-')]
        if all(parts):
            import itertools
            return [('拼合', ' + '.join(v for _, v, _ in combo), [x for _, _, ph in combo for x in ph]) for combo in itertools.islice(itertools.product(*parts), 64)]
        return []
    out = []
    for w in {word, word.lower(), word.capitalize()}:
        for src, d in (('misaki', MG), ('misaki', MS)):
            v = d.get(w)
            if isinstance(v, dict): v = v.get('DEFAULT') or next(iter(v.values()))
            if isinstance(v, str): out.append((src, v, ipa_phones(v)))
        for seq in CMU.get(w.lower(), []): out.append(('CMU', ' '.join(seq), arpa_phones(seq)))
    return out


FUNC = set('a an the of to in on at by for and or but as is was be been were are it its that this with from not no so than then he she they his her their them we you i me my our your had has have into onto up who which what when how'.split())


def words_of(text):
    # 带数字的（12th、62nd、1990s）不在这里查——数字读法由 交付核查 的数字读法清单（A11）逐个核对
    return [w for w in re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)*(?:-[A-Za-z0-9]+)*", text) if not re.search(r'\d', w)]


def check(no):
    d = json.load(open(f'scripts/{no}.json'))
    conf = d.get('核对确认', {}).get('读音', {})
    texts = [('标题', d['title_en'])] + [(f'S{i}', ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks'])) for i, s in enumerate(d['sentences'], 1)]
    rows = []; seen = {}
    for lab, t in texts:
        sp = spoken(re.sub(r'\*\*', '', R.strip_gloss(t)))
        ph_sent = re.sub(r'[ˈˌ\s]', '', phonemes_of(sp))
        ws = words_of(sp)
        for i, w in enumerate(ws):
            ph = re.sub(r'[,;:.!?"“”]', '', phonemes_of(w)).strip()
            if w.lower() not in FUNC and re.sub(r'[ˈˌ\s]', '', ph) not in ph_sent:
                cv = conf.get(w) or VERIFIED.get(w)
                if not (isinstance(cv, dict) and cv.get('整句读法已核实')):
                    rows.append(('不一致', f"{no} 待核实 [不一致] {w}  单读 /{ph}/ 与整句里的读法不同（整句：/{phonemes_of(sp)}/）｜出现在 {lab}", True))
                continue
            lw = re.sub(r"['’]s$", '', w).lower()
            # 专有名词：句中大写；句首大写但 misaki 词典里没有小写的普通词（06 Wilhelm、07 Inky 在句首）；全大写缩写（PNAS、SAT、UK）
            proper = w[0].isupper() and (i > 0 or (lw not in MG and lw not in MS and lw.split('-')[0] not in MG) or (w.isupper() and len(w) > 1))
            if lab == '标题' and w[0].isupper() and lw in MG and not w.isupper(): proper = False   # 标题里的普通词首字母大写
            k_ = (w, ph)
            if k_ in seen: seen[k_][1].append(lab); continue
            rs = refs(w); tts = ipa_phones(ph)
            ok = [r for r in rs if same(tts, r[2])[0]]
            if w.lower() in FUNC and (ok or not rs): continue
            if rs and ok and not proper: seen[k_] = (None, [lab]); continue
            why = '词典里没有' if not rs else ('不一致：' + '；'.join(sorted({same(tts, r[2])[1] for r in rs})) if not ok else '')
            cat = '专有名词' if proper else ('词典里没有' if not rs else '不一致')
            c = conf.get(w) or VERIFIED.get(w)
            if c is None and VERIFIED.get(re.sub(r"['’]s$", '', w)): c = dict(VERIFIED[re.sub(r"['’]s$", '', w)], 原词=True)
            seen[k_] = ((cat, w, ph, why, rs, c), [lab])
    for (w, ph), (info, labs) in seen.items():
        if info is None: continue
        cat, w, ph, why, rs, c = info
        refstr = '；'.join(f'{s}: {v}' for s, v, _ in rs[:4]) or '（两本词典都没有）'
        okf = [c.get('标准读音', c.get('读音', ''))] + list(c.get('可接受读音', [])) if isinstance(c, dict) else []
        if isinstance(c, dict) and c.get('原词'):          # 所有格：核实的是原词，配音读法去掉词尾 s/z 再比
            ph_cmp = re.sub(r'(ᵻ|ɪ)?[sz]$', '', ph)
        else: ph_cmp = ph
        # 已核实的词：配音音标必须与核实的读法逐个符号一致（连重音号；只忽略空格）——配音读法有任何变化都要重新核实
        #（宽松比对会放过次重读音节的元音错，如 03 Helicobacter 原来读 hˈɛlɪkˌɑːbæktɚ）
        done = any(v and re.sub(r'\s', '', v) == re.sub(r'\s', '', ph_cmp) for v in okf)
        state = 'OK（已核实）' if done else ('BAD（已核实，但配音读法与核实的读音不一致，加进 PRON_FIX）' if isinstance(c, dict) else '待核实')
        rows.append((cat, f"{no} {state} [{cat}] {w}  配音读作 /{ph}/  {('｜' + why) if why else ''}｜词典：{refstr}｜出现在 {','.join(dict.fromkeys(labs))}", state != 'OK（已核实）'))
    return rows


def export(no):
    """待核实的词 → JSON（给核查员）：词、配音音标、类别、出现的句子和原句"""
    d = json.load(open(f'scripts/{no}.json'))
    sents = {'标题': d['title_en'], **{f'S{i}': ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks']) for i, s in enumerate(d['sentences'], 1)}}
    out = []
    for cat, line, bad in check(no):
        if not bad: continue
        m = re.match(r'\S+ \S+ \[(\S+)\] (\S+)\s+(?:配音读作|单读) /([^/]*)/(.*)｜出现在 (\S+)', line)
        if not m: continue
        labs = m.group(5).split(',')
        out.append({'篇': no, '类别': m.group(1), '词': m.group(2), '配音音标': m.group(3), '程序说明': m.group(4).strip(' ｜'), '出现在': labs, '原句': sents.get(labs[0], '')})
    return out


def selftest(no):
    """阳性对照：① 把本篇一个查词典合格的多音节实词的重音挪到别的音节（模拟 hippocampus 那种重音错），必须报出；
    ② 本篇用到读音改正表里的词时，关掉改正，必须报出（模拟 Inky 读错）。原样不得因这两步多报。"""
    global phonemes_of
    base = {line for _, line, bad in check(no) if bad}
    d = json.load(open(f'scripts/{no}.json'))
    text = ' '.join([d['title_en']] + [' '.join(c['en'] for c in s_['chunks']) for s_ in d['sentences']])
    orig = phonemes_of; res = []
    # ① 挪重音
    tgt = None
    for w in words_of(spoken(re.sub(r'\*\*', '', R.strip_gloss(text)))):
        if w.lower() in FUNC or len(w) < 7 or w[0].isupper() or '-' in w: continue
        ph = re.sub(r'[,;:.!?]', '', orig(w)).strip()
        if ph.count('ˈ') == 1 and len([p_ for p_, s_ in ipa_phones(ph) if s_ >= 0]) >= 3 and any(same(ipa_phones(ph), r[2])[0] for r in refs(w)):
            tgt = (w, ph); break
    if tgt:
        w, ph = tgt; syl = re.findall(r'[ˈˌ]?[^ˈˌ]+', ph)
        bad_ph = ph.replace('ˈ', '')
        vow = [m_.start() for m_ in re.finditer('[aeiouæɑɔəɛɪʊʌɚɜɐᵻ]', bad_ph)]
        first_v = vow[0]; idx = ph.index('ˈ')
        bad_ph = (bad_ph[:first_v] + 'ˈ' + bad_ph[first_v:]) if idx > first_v + 1 else (bad_ph[:vow[-1]] + 'ˈ' + bad_ph[vow[-1]:])
        def fake(t, _w=w, _ph=ph, _bad=bad_ph):
            r = orig(t)
            return r.replace(_ph, _bad) if re.search(r'(?<![A-Za-z])' + re.escape(_w) + r'(?![A-Za-z])', t) else r
        phonemes_of = fake; got = {line for _, line, bad in check(no) if bad}; phonemes_of = orig
        res.append((f'把 {w} 的重音挪成 /{bad_ph}/', any(f'] {w} ' in l_ for l_ in got - base)))
    # ② 关掉读音改正
    used = [w for w in PRON_WORDS if re.search(r'(?<![A-Za-z])' + re.escape(w) + r'(?![A-Za-z])', text, flags=re.I)
            and re.sub(r'\s', '', PRON_WORDS[w]) != re.sub(r'\s|[,;:.!?]', '', KT.tokenizer.phonemize(w, 'en-us'))]   # McArthur 只差一个空格，听不出，不拿来测
    if used:
        keep = dict(PRON_WORDS); PRON_WORDS.clear()
        got = {line for _, line, bad in check(no) if bad}; PRON_WORDS.update(keep)
        res.append((f'关掉读音改正（{"、".join(used)}）', all(any(f'] {w} ' in l_ for l_ in got - base) for w in used)))
    ok = bool(res) and all(h for _, h in res)
    print(f"{'✔' if ok else '✘'} 读音核对 自检：{no} " + '；'.join(f"{n}{'报出' if h else '没报出'}" for n, h in res) if res else f'✘ 读音核对 自检：{no} 找不到可用来自检的词')
    return ok


if __name__ == '__main__':
    if '--自检' in sys.argv:
        sys.exit(0 if selftest([a for a in sys.argv[1:] if re.fullmatch(r'\d\d', a)][0]) else 1)
    if '--导出' in sys.argv:
        allr = []
        for no in [a for a in sys.argv[1:] if re.fullmatch(r'\d\d', a)]: allr += export(no)
        json.dump(allr, open(sys.argv[sys.argv.index('--导出') + 1], 'w'), ensure_ascii=False, indent=1); print('导出', len(allr)); sys.exit(0)
    total = 0
    for no in [a for a in sys.argv[1:] if not a.startswith('--') and re.fullmatch(r'\d\d', a)]:
        rows = check(no)
        order = {'不一致': 0, '词典里没有': 1, '专有名词': 2}
        for cat, line, bad in sorted(rows, key=lambda r: order[r[0]]): print(line)
        n = sum(1 for r in rows if r[2]); total += n
        print(f'{no} 读音核对 待核实 {n} 处（不一致 {sum(1 for r in rows if r[0] == "不一致" and r[2])}、词典里没有 {sum(1 for r in rows if r[0] == "词典里没有" and r[2])}、专有名词 {sum(1 for r in rows if r[0] == "专有名词" and r[2])}）')
    print('问题数', total)
    sys.exit(1 if total else 0)
