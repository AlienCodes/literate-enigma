#!/usr/bin/env python3
"""执行效应演练（铁律：执行效应，CLAUDE.md 第19条；用户 2026-10-24：“所有我们踩过的坑，还有所有我们立的这个规矩都要执行起来……
这个东西它不去发挥作用，那你做这些事情，所有的这个事情都是无用功”）。
“门在”不算数，在真实流程里把违规挡下来才算数：拿真实脚本的副本注入违规，从真实入口跑，必须停下、而且停在对的编号上。
  入口 出片：踩坑核查.py NN 出片（交付核查 出片前 ⓪、定稿流水线 ① 调的就是它）；读音：读音核对.py NN（交付核查 出片前）；
  出片程序：make_video.py 只出声音（出片守门自检.py 的每一项就是这个入口的演练，这里要求它的印章有效并计入）。
每个场景先跑一遍原样（同一入口、同一篇），只看注入后**新多出来**的报错，所以篇目原有的待改项不干扰。
历史事故逐个重放：07 Inky 读音（A23）、22/24 牛津逗号“英式、不改”放行（T18/T35）、24 破折号（T36）。
演练自己也要被查（第4条“程序本身不许出错”）：把 T36 的门拆掉再跑，演练必须报“没挡住”。
全部挡住 → 写 工具/执行效应演练通过.json（被演练程序 + 规则执行表 的指纹、挡住的规矩）；规则执行核查.py 核对印章：
程序或规矩一改就要重演，不重演提交、推送、交付核查、定稿流水线一律停。没有演练样本的规矩算缺口，执行效应缺口基线.json 只许减少。
在视频工作目录（含 make_video.py、scripts/）下运行：python3 <工具目录>/执行效应演练.py      全部演练
                                                    python3 <工具目录>/执行效应演练.py --状态  一行状态（开工提醒用）"""
import os, sys, json, copy, re, subprocess, hashlib, shutil
from concurrent.futures import ThreadPoolExecutor
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
STAMP = f'{T}/执行效应演练通过.json'; GAPB = f'{T}/执行效应缺口基线.json'
被演练 = ['钩子/闸门.py', '踩坑核查.py', '译文核查.py', '破折号.py', 'check_all.py', '读音核对.py', 'make_video.py', 'render.py', '执行效应演练.py', '规则执行表.json', '放行口子核查.py', '放行口子表.json', '用户同意记录.json']
指纹 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else '无'


def 块(d, si, k=0): return d['sentences'][si]['chunks'][k]
def 改中文(c, old, new):
    c['zh'] = c['zh'].replace(old, new, 1); c['align'] = [[a, z.replace(old, new, 1)] for a, z in c['align']]
def 加中文(c, t): c['zh'] += t; c['align'][-1] = [c['align'][-1][0], c['align'][-1][1] + t]
def 改英文(c, old, new):
    c['en'] = c['en'].replace(old, new, 1); c['align'] = [[a.replace(old, new, 1), z] for a, z in c['align']]
def 首块(d, pred):
    for s in d['sentences']:
        for c in s['chunks']:
            if pred(c): return c
    raise KeyError('样本找不到')


def _t35(d): d['核对确认']['牛津逗号']['S13 008 metres down, upright and'] = '文章英文是英式写法，三项并列不用牛津逗号；不改'
def _t18(d):
    c = 首块(d, lambda c: 'food, and' in c['en']); 改英文(c, 'food, and', 'food and')
def _d3(d):
    c = 块(d, 2); w = re.findall(r'[A-Za-z]{5,}', re.sub(r'\*\*|\{\{.*?\}\}', '', c['en']))[0]; 改英文(c, w, w + 's')
def _d4(d):
    c = 首块(d, lambda c: re.search(r'\*\*[^*]+\*\*\([A-Za-z][^)]*\)', c['zh']))
    m = re.search(r'(\*\*[^*]+\*\*)\(([A-Za-z][^)]*)\)', c['zh']); 改中文(c, m.group(0), m.group(1))
def _t33(d):
    d['结尾解说'] = '结局'; c = d['sentences'][-1]['chunks'][-1]; c['note'] = c['note'].replace('（简述：', '（结局：')
def _l19(d): 块(d, 0)['note'] = '（这是一行故意写得非常非常长的说明，用来演练说明行不得比上面的英文正文宽这一条铁律，必须被出片前的核查拦下来才算真正执行）'
def _t16(d):
    c = 首块(d, lambda c: re.search(r'\d', re.sub(r'\*\*|\{\{.*?\}\}', '', c['en'])) and re.search(r'\d', c['zh']))
    n = re.findall(r'\d+', c['zh'])[0]; 改中文(c, n, '某')

def _unbold_prep(d, si, k, w, p):
    c = 块(d, si, k); 改英文(c, f'**{w} {p}**', f'**{w}** {p}'); 改中文(c, f'({w} {p})', f'({w})')
def _depart(d):
    c = 块(d, 0)
    if '**for**' in c['en']: 改英文(c, '**for**', 'for')
def _term(d):
    c = 首块(d, lambda c: '艾伦·图灵' in c['zh']); 改中文(c, '艾伦·图灵', '他')
def _zhdup(d):
    ms = [(si, k, m) for si, s in enumerate(d['sentences']) for k, c in enumerate(s['chunks']) for m in re.finditer(r'\*\*([^*]+)\*\*\(([^)]+)\)', c['zh'])]
    a = ms[0]; b = next(x for x in ms if x[0] != a[0] and x[2].group(2).lower() != a[2].group(2).lower())
    改中文(块(d, b[0], b[1]), b[2].group(0), f'**{a[2].group(1)}**({b[2].group(2)})')
def _l16(d):
    c = 首块(d, lambda c: c.get('note')); c['note'] = c['note'][:-1] + '\n，补充一句）'
def _gloss(d):
    c = 首块(d, lambda c: '|set out to}}' in c['zh']); new = re.sub(r'\n\{\{[^{}]*\|set out to\}\}', '', c['zh'])
    old = c['zh']; c['zh'] = new; c['align'] = [[a, re.sub(r'\n\{\{[^{}]*\|set out to\}\}', '', z)] for a, z in c['align']]
def _dir(d):
    c = 块(d, 0); c['en'] += ' before the war'; c['zh'] += '在战争之后才'; c['align'].append(['before the war', '在战争之后才'])
def _adv(d):
    c = 首块(d, lambda c: re.search(r'\*\*[^*]+的\*\*\(', c['zh'])); m = re.search(r'\*\*([^*]+)的\*\*\(', c['zh']); 改中文(c, m.group(0), f'**{m.group(1)}地**(')
def _zh1(d):
    c = 块(d, 3); m = re.search(r'[一-鿿](?![^*]*\*\*\()', re.sub(r'\*\*[^*]+\*\*\([^)]*\)', '', c['zh'])); 改中文(c, m.group(0), '某' if m.group(0) != '某' else '甲')
def _merge(d, need_bold=True):
    for s in d['sentences']:
        for c in s['chunks']:
            al = c['align']
            for i in range(len(al) - 1):
                if al[i][0] != '\n' and al[i + 1][0] != '\n' and (not need_bold or ('**' in al[i][1] and '**' in al[i + 1][1])):
                    al[i] = [al[i][0] + ' ' + al[i + 1][0], al[i][1] + al[i + 1][1]]; del al[i + 1]; return
def _coarse(d):
    c = max((c for s in d['sentences'] for c in s['chunks']), key=lambda c: len(c['align']))
    c['align'] = [[' '.join(a for a, _ in c['align'] if a != '\n'), ''.join(z for _, z in c['align'])]]
def _t23(d):
    c = 首块(d, lambda c: '**罪**(convicted of)' in c['zh']); 改中文(c, '**罪**(convicted of)', '罪')



# (编号, 入口, 篇, 怎么造, 改法, 必须新报出的字样, 这一场演练证明的规矩)
场景 = [
    ('T36破折号', '出片', '24', '24 S2 中文加“——”（重放 24 草稿的破折号）', lambda d: 加中文(块(d, 1), '——'), '[T36]', ['T36', '守则18', '文34']),
    ('T35英式不改', '出片', '24', '牛津逗号确认写“英式写法、不改”（重放 22 S3、24 S8/S10 放行）', _t35, '[T18]', ['T35', 'T18', '文17']),
    ('T18去牛津逗号', '出片', '03', '03 去掉 food, and 的牛津逗号', _t18, '[T18]', ['T18', '文17', '单27']),
    ('D3改英文', '出片', '23', '23 S3 英文一个词加 s', _d3, '[D3]', ['D3', '文16']),
    ('D1换行标记', '出片', '23', '23 S1 英文混进 \\n', lambda d: 块(d, 0).__setitem__('en', 块(d, 0)['en'] + '\n'), '[D1]', ['D1']),
    ('D2对不上', '出片', '23', '23 S2 zh 多一个字、align 没跟', lambda d: 块(d, 1).__setitem__('zh', 块(d, 1)['zh'] + '多'), '[D2]', ['D2']),
    ('D4缺标记', '出片', '23', '23 重点词中文去掉 (英文) 标记', _d4, '[D4', ['D4']),
    ('T24口述词', '出片', '23', '23 S3 括号说明里加“觉得”', lambda d: 加中文(块(d, 2), '（觉得这样更体面）'), '[T24]', ['T24']),
    ('T27怎么理解', '出片', '23', '23 S1 说明写“结局怎么理解：……”', lambda d: 块(d, 0).__setitem__('note', '（结局怎么理解：……）'), '[T27]', ['T27', '守则10']),
    ('T28无结尾解说', '出片', '15', '15 去掉结尾解说', lambda d: d.pop('结尾解说'), '[T28]', ['T28', '守则11']),
    ('T33还写结局', '出片', '23', '23 结尾解说改回“结局”', _t33, '[T33]', ['T33']),
    ('L19说明太宽', '出片', '23', '23 S1 说明写成一长行', _l19, 'L19', ['L19', '守则14']),
    ('T16数字丢了', '出片', '23', '23 中文里把阿拉伯数字换成“某”', _t16, '[T16]', ['T16']),
    ('W4半角括号', '出片', '23', '23 S2 中文说明用半角括号', lambda d: 加中文(块(d, 1), '(说明)'), '[W4]', ['W4']),
    ('L13换行', '出片', '23', '23 S5 加 {{=}}（换行和用户看过的不同）', lambda d: 改英文(块(d, 4), 块(d, 4)['en'], 块(d, 4)['en'] + '{{=}}'), '[L13]', ['L13', '守则5']),
    ('G24特批无原话', '出片', '24', 'AI 自己写“说明放宽特批”（没有用户原话）', lambda d: d.__setitem__('说明放宽特批', {'S1': {'倍数': 1.2, '依据': 'AI 觉得这一句可以放宽一点'}}), '说明放宽特批', ['G24']),   # 排版程序（render.apply_script）先停，同样挡住
    ('G24非人声放宽', '出片', '24', '非人声确认写“放宽：听不出”', lambda d: d['核对确认'].setdefault('非人声', {}).__setitem__('99.00–99.10s', {'配音指纹': 'x', '依据': '放宽：听不出'}), '[口子]', ['G24']),
    ('G24引号无原话', '出片', '24', '括号含重点词的确认只写“沿用”，没有用户原话', lambda d: d['核对确认'].setdefault('括号含重点词', {}).__setitem__('S1-1 （**x**(y)）', '沿用原写法'), '[口子]', ['G24']),
    ('T22拆短语', '出片', '23', '23 S3 **rooted in** 去掉 in 的加粗', lambda d: _unbold_prep(d, 2, 0, 'rooted', 'in'), '[T22]', ['T22', '守则8']),
    ('T22depart重放', '出片', '24', '重放 24 S1 departed … for（用户看草稿才发现）：for 没加粗必须报出', _depart, 'S1 departed … for', ['T22', 'T14'], '不比原样'),
    ('T23意思标一半', '出片', '23', '23 convicted of 的“罪”去掉标记（意思只标一半）', _t23, '[T23]', ['T23', '守则8']),
    ('T30漏术语', '出片', '23', '23 中文把“艾伦·图灵”换成“他”', _term, '[T30]', ['T30']),
    ('T26中文重复', '出片', '23', '23 两个不同重点词用同一个中文', _zhdup, '[T26]', ['T26']),
    ('T19即', '出片', '23', '23 S2 正文加文言“即”', lambda d: 加中文(块(d, 1), '即此'), '[T19即]', ['T19']),
    ('L16行首标点', '出片', '23', '23 说明换行后以“，”开头', _l16, '[L16]', ['L16']),
    ('T25用户释义没上画面', '出片', '08', '08 S17 去掉用户给的 set out to 说明', _gloss, '[T25]', ['T25']),
    ('T4方向反了', '出片', '23', '23 S1 before 放在“之后才”上', _dir, '[T4方向]', ['T4', 'T20']),
    ('T2形容词译成地', '出片', '23', '23 形容词重点词“…的”改成“…地”', _adv, '[T2词性]', ['T2']),
    ('W3排版指令', '出片', '23', '23 S2 译文里混进“（放到翻译的正下方）”', lambda d: 加中文(块(d, 1), '（放到翻译的正下方）'), '[W3]', ['W3']),
    ('T10改稿无原话', '出片', '23', '23 S4 中文改一个字、没有用户原话', _zh1, '[T10改稿]', ['T10']),
    ('逐句确认没重做', '出片', '23', '23 S4 改了中文没重新逐句确认', _zh1, '[逐句确认]', ['T3', 'T7', 'T8', 'T15', 'T21']),
    ('T34同序挤一组', '出片', '23', '23 两个重点词合进一组', _merge, '[T34]', ['T34']),
    ('T9对齐太粗', '出片', '23', '23 最长一块的所有组合成一组', _coarse, '[T9对齐]', ['T9']),
    ('A23Inky', '读音', '07', '重放 07 Inky 读成 ink-EYE：读音改正表去掉 Inky', None, 'Inky', ['A23', '守则6']),
]


# 仓库入口（D 类：读仓库文件的门，如 制作记录/NN.md 的踩坑对照记录、25 起才查的固定格式）：
# 在临时“仓库镜像”里跑真程序（镜像 = 仓库根的符号链接，只有要改的文件是副本；程序从镜像路径启动，V/ROOT 指向镜像，真仓库一个字不动）。
# 25 还没有：用 24 的脚本、制作记录副本当 25（篇号设成 25，25 起才查的门就生效）。
# (编号, 入口, 篇, 怎么造, 改法(files: {仓库相对路径: 文本}), 必须新报出的字样, 规矩)
def _rec(no): return f'视频/制作记录/{no}.md'
def _改行(f, no, i, v): f[_rec(no)] = re.sub(rf'^(\| *{i} *\|.*\| *(?:涉及|不涉及) *\|).*\|\s*$', lambda m: m.group(1) + f' {v} |', f[_rec(no)], count=1, flags=re.M)
def _删节(f, no, h): t = f[_rec(no)]; i = t.index(h); j = t.find('\n## ', i + 1); f[_rec(no)] = t[:i] + (t[j + 1:] if j > 0 else '')
仓库场景 = [
    ('G6固定格式25', '踩坑出片', '25', '25 的 G6 写成套话以外的自由句子（不是“本篇无/本篇有”）', lambda f: _改行(f, '25', 'G6', '用户两次要求不冲突，没有需要问的'), '只认固定格式', ['G6', 'C3', 'C4']),
    ('C4固定格式25', '踩坑出片', '25', '25 的 C4 写“本篇有：合并改了”但没有用户原话', lambda f: _改行(f, '25', 'C4', '本篇有：两次插话合并成一次改了'), '只认固定格式', ['C4', 'C3']),
    ('G6套话', '踩坑出片', '25', '25 的 G6 用开工自动填的套话', lambda f: _改行(f, '25', 'G6', '按现行做法由程序把关（踩坑总表“拦住”），本篇核查通过'), '只有人能判', ['G6', 'C3', 'C4']),
    ('法1对照没填完', '踩坑出片', '25', '25 踩坑对照记录 T1 一格写回“待填”', lambda f: _改行(f, '25', 'T1', '待填'), '没填完', ['法1']),
    ('守则13没写方法设计', '踩坑出片', '25', '25 制作记录删掉“## 方法设计”', lambda f: _删节(f, '25', '## 方法设计'), '[T31]', ['守则13', 'T31']),
    ('守则12没写方法复盘', '踩坑出片', '25', '25 制作记录删掉“## 方法复盘”', lambda f: _删节(f, '25', '## 方法复盘'), '[T29]', ['守则12', 'T29']),
    ('S2速查表本文重复', '踩坑出片', '24', '24 速查表 departed 一行写成两个“本文：”', lambda f: _改文(f, _文24, '| departed | v.', '| departed | 本文：离开；本文：出发；v.'), 'S2 速查表', ['S2']),
    ('S4速查表缺词性', '踩坑出片', '24', '24 速查表 remote 一行只剩“本文：”', lambda f: _改文(f, _文24, '| remote | adj. 偏远的', '| remote | 本文：偏远的 |x'), 'S4 速查表缺词性', ['S4']),
    ('G18原稿重点词空', '踩坑出片', '24', '原稿重点词.json 没有本篇（重放 20 篇浅克隆）', lambda f: _改json(f, '视频/工具/原稿重点词.json', lambda o: o.pop(_文24)), 'G18 原稿重点词', ['G18']),
    ('T11重点词漏标', '踩坑出片', '24', '24 一个重点词的中文去掉 (英文) 标记（check_all D4）', lambda f: _改json(f, '视频/脚本/24.json', _d4), '[check_all] D4', ['T11']),
    ('T12新加撞词', '踩坑出片', '24', '24 把别篇加粗过的词也加粗（新加重点词撞词）', lambda f: _改json(f, '视频/脚本/24.json', _撞词), 'T12 新加重点词撞词', ['T12', 'T17']),
]
# 拆门自查（每种入口拆一道门，演练必须报“没挡住”）：(入口, 篇, 用哪一场, 拆门代码)
仓库拆门 = [('踩坑出片', '25', 'G6固定格式25', 'K.人判格式_起 = 999')]


_文24 = os.path.relpath(__import__('glob').glob(f'{os.path.dirname(V)}/新版定稿/24-*.md')[0], os.path.dirname(V))
def _读(f, k): return f[k] if k in f else open(f'{os.path.dirname(V)}/{k}').read()
def _改文(f, k, old, new):
    t = _读(f, k); assert old in t, old; f[k] = t.replace(old, new, 1)
def _改json(f, k, fn):
    o = json.loads(_读(f, k)); fn(o); f[k] = json.dumps(o, ensure_ascii=False, indent=1)
def _英文段(x):
    t = open(x).read(); return t.split('## 英文', 1)[1].split('## 中文', 1)[0]
def _撞词(d):
    """24 里找一个别篇加粗过、24 原稿没加粗的词，加粗并补中文标记"""
    P = os.path.dirname(V); import glob
    other = {b.lower() for x in glob.glob(f'{P}/新版定稿/[0-9][0-9]-*.md') if not os.path.basename(x).startswith('24') and os.path.exists(f'{V}/脚本/{os.path.basename(x)[:2]}.json')
             for b in re.findall(r'\*\*([^*]+)\*\*', _英文段(x)) if ' ' not in b}
    orig = {x.lower() for x in json.load(open(f'{T}/原稿重点词.json')).get(_文24, [])}
    for s in d['sentences']:
        for c in s['chunks']:
            for i, (a, z) in enumerate(c['align']):
                for w in re.findall(r'(?<![*A-Za-z])([a-z]{6,})(?![*A-Za-z])', a):
                    if w in other and w not in orig and z and '**' not in z:
                        c['en'] = re.sub(rf'(?<![*A-Za-z]){w}(?![*A-Za-z])', f'**{w}**', c['en'], count=1); c['align'][i] = [re.sub(rf'(?<![*A-Za-z]){w}(?![*A-Za-z])', f'**{w}**', a, count=1), f'**{z}**({w})']
                        c['zh'] = ''.join(b for _, b in c['align']); return
    raise KeyError('24 里没有可撞的词')


def 仓库底稿(no):
    """镜像里要改的文件的底稿（篇号 25 用 24 的副本；G6/C3/C4 先填合格的固定格式，原样就不报这一格）"""
    src = '24' if no == '25' else no
    rec = open(f'{V}/制作记录/{src}.md').read()
    f = {_rec(no): rec, f'视频/脚本/{no}.json': open(f'{V}/脚本/{src}.json').read()}
    for i in ('G6', 'C3', 'C4'): _改行(f, no, i, '本篇无：演练底稿，用户没有提互相冲突的要求，没有插话，没有多版本设计稿')
    return f


def 镜像(M, files):
    """M = 仓库镜像根：其余一律符号链接到真仓库，files 里的写成副本（父目录变成真目录）"""
    P = os.path.dirname(V); shutil.rmtree(M, ignore_errors=True); os.makedirs(M)
    real = {'/'.join(k.split('/')[:i]) for k in files for i in range(1, len(k.split('/')))}
    def fill(rel):
        for x in os.listdir(f'{P}/{rel}' if rel else P):
            r = f'{rel}/{x}' if rel else x
            if x == '.git' or r in files: continue
            if r in real: os.makedirs(f'{M}/{r}'); fill(r)
            else: os.symlink(f'{P}/{r}', f'{M}/{r}')
    fill('')
    for k, t in files.items(): os.makedirs(os.path.dirname(f'{M}/{k}'), exist_ok=True); open(f'{M}/{k}', 'w').write(t)
    return M


def 仓库跑(entry, no, M, ws, 拆门=None):
    tool = f'{M}/视频/工具'
    if entry == '踩坑出片':
        cmd = ['python3', '-c', f"import sys;sys.path.insert(0,{tool!r});import 踩坑核查 as K;{拆门};sys.argv=['踩坑核查.py',{no!r},'出片'];sys.exit(K.main())"] if 拆门 else ['python3', f'{tool}/踩坑核查.py', no, '出片']
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ws, timeout=900)
    return r.returncode, set(l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip())


def 仓库演练(W, root, 只=None):
    todo = [s for s in 仓库场景 if not 只 or s[0] in 只]
    if not todo: return []
    base, jobs = {}, []
    for sid, entry, no, how, fn, want, rules in todo:
        f0 = 仓库底稿(no)
        if (entry, no) not in base:
            d = json.loads(f0[f'视频/脚本/{no}.json'])
            base[(entry, no)] = (镜像(f'{root}/演练_镜像_原样_{entry}_{no}', f0), 工作区(W, root, f'原样仓库_{entry}_{no}', no, d))
        f = dict(f0)
        try: fn(f)
        except Exception as e: jobs.append((sid, None, None, f'样本找不到：{e}')); continue
        if f == f0: jobs.append((sid, None, None, '样本找不到：改法没改动任何文件')); continue
        jobs.append((sid, 镜像(f'{root}/演练_镜像_{sid}', f), 工作区(W, root, f'仓库_{sid}', no, json.loads(f[f'视频/脚本/{no}.json'])), None))
    with ThreadPoolExecutor(4) as ex:
        bo = dict(zip(base, ex.map(lambda k: 仓库跑(k[0], k[1], *base[k]), base)))
        def one(j):
            sid, M, ws, err = j
            if err: return sid, False, err
            s = next(x for x in 仓库场景 if x[0] == sid); entry, no, want = s[1], s[2], s[5]
            c, o = 仓库跑(entry, no, M, ws); hit = [l for l in o - bo[(entry, no)][1] if want in l]
            return sid, c != 0 and bool(hit), (hit[0][:90] if hit else f'没挡住（退出码 {c}）')
        res = list(ex.map(one, jobs))
        for entry, no, sid, code in 仓库拆门:
            if 只 and sid not in 只: continue
            j = next((x for x in jobs if x[0] == sid and x[1]), None)
            if not j: res.append((f'自查拆门_{entry}', False, '样本找不到')); continue
            c, o = 仓库跑(entry, no, j[1], j[2], 拆门=code); caught = any(s[5] in l for s in 仓库场景 if s[0] == sid for l in o - bo[(entry, no)][1])
            res.append((f'自查拆门_{entry}', not caught, f'拆掉门（{code}）后演练报“没挡住”（演练能发现坏门）' if not caught else '拆掉门后演练还说挡住了：演练失灵'))
    return res


# 钩子入口（Claude 钩子 = 我自己每一个动作的真实入口）：(编号, 闸门种类, 工具调用, 必须出现的字样, 规矩)
钩子场景 = [
    ('C5派子代理', '子代理', {'tool_input': {'prompt': '帮我把这篇审校一遍'}}, '【T29 闸门】', ['C5', 'T29']),
    ('A25一次发两个', '发文件', {'tool_input': {'files': ['a.mp4', 'b.mp4']}}, '【A25 闸门】', ['A25', 'W8', 'W9', '守则7']),
    ('A25没过核查就发', '发文件', {'tool_input': {'files': ['/tmp/演练_没核查.mp4']}}, '没有核查通过的回执', ['A25', '守则7']),
    ('G13跳过钩子', '命令', {'tool_input': {'command': 'git commit --no-verify -m x'}}, '【规则执行闸门】', ['G13', '守则16']),
    ('G13改钩子路径', '命令', {'tool_input': {'command': 'git config core.hooksPath /dev/null'}}, 'core.hooksPath', ['G13']),
    ('C1强推master', '命令', {'tool_input': {'command': 'git push -f origin master'}}, '【部署闸门】', ['C1', 'C2']),
    ('C2部署', '命令', {'tool_input': {'command': 'npx vercel --prod'}}, '【部署闸门】', ['C1', 'C2']),
    ('W2直接读Word', '命令', {'tool_input': {'command': "python3 -c \"from docx import Document; Document('用户.docx')\""}}, '【W2 闸门】', ['W2']),
    ('G10中文pkill', '命令', {'tool_input': {'command': 'pkill -f 定稿流水线'}}, '【G10 闸门】', ['G10']),
]


def 跑钩子(kind, payload):
    for f in payload.get('tool_input', {}).get('files', []):   # 闸门只查存在的文件：造一个没有回执的真文件
        if f.startswith('/tmp/演练_'): open(f, 'wb').write(os.urandom(64))
    r = subprocess.run(['python3', f'{T}/钩子/闸门.py', kind], input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True, timeout=60)
    return r.stdout + r.stderr


def 工作区(W, root, sid, no, d, 改正=None):
    ws = f'{root}/演练_{sid}'; shutil.rmtree(ws, ignore_errors=True); os.makedirs(f'{ws}/scripts')   # 与工作目录并排（出片程序按 ../tts 找模型）
    for x in os.listdir(W):
        if x == 'scripts' or x.startswith('work_') or x.endswith(('.mp4', '.mp3', '.wav', '.json')): continue
        os.symlink(f'{W}/{x}', f'{ws}/{x}')
    json.dump(d, open(f'{ws}/scripts/{no}.json', 'w'), ensure_ascii=False, indent=1)
    if 改正 is not None: json.dump(改正, open(f'{ws}/读音改正.json', 'w'), ensure_ascii=False, indent=1)
    return ws


def 跑(entry, no, ws, 拆门=None):
    if entry == '出片':
        if 拆门:   # 演练自查：拆掉一道门（真实入口，其余不变）
            cmd = ['python3', '-c', f"import sys;sys.path.insert(0,{T!r});import 破折号;破折号.查=lambda d,no=None:[];import 踩坑核查;sys.argv=['踩坑核查.py',{no!r},'出片'];sys.exit(踩坑核查.main())"]
        else: cmd = ['python3', f'{T}/踩坑核查.py', no, '出片']
    else: cmd = ['python3', f'{T}/读音核对.py', no]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ws, timeout=600)
    return r.returncode, set(l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip())


def 演练(W, 只=None):
    root = os.path.dirname(os.path.abspath(W))
    fix = json.load(open(f'{T}/发音词典/读音改正.json'))
    jobs, base = [], {}
    for sid, entry, no, how, fn, want, rules, *_ in 场景:
        if 只 and sid not in 只: continue
        d0 = json.load(open(f'{W}/scripts/{no}.json'))
        if (entry, no) not in base: base[(entry, no)] = 工作区(W, root, f'原样_{entry}_{no}', no, d0, fix if entry == '读音' else None)
        d = copy.deepcopy(d0)
        try:
            if fn: fn(d)
        except Exception as e: jobs.append((sid, None, f'样本找不到：{e}')); continue
        jobs.append((sid, 工作区(W, root, sid, no, d, {k: v for k, v in fix.items() if k != 'Inky'} if sid == 'A23Inky' else (fix if entry == '读音' else None)), None))
    jobs.append(('自查拆门', 工作区(W, root, '自查拆门', '24', (lambda d: (加中文(块(d, 1), '——'), d)[1])(json.load(open(f'{W}/scripts/24.json')))), None))
    with ThreadPoolExecutor(4) as ex:
        bo = dict(zip(base, ex.map(lambda k: 跑(k[0], k[1], base[k]), base)))
        def one(j):
            sid, ws, err = j
            if err: return sid, False, err
            if sid == '自查拆门':
                c, o = 跑('出片', '24', ws, 拆门=True); new = o - bo.get(('出片', '24'), (0, set()))[1]
                return sid, not any('[T36]' in l for l in new), '拆掉 T36 的门后，演练报“没挡住”（演练能发现坏门）' if not any('[T36]' in l for l in new) else '拆掉门后演练还说挡住了：演练失灵'
            s = next(x for x in 场景 if x[0] == sid); entry, no, want = s[1], s[2], s[5]
            c, o = 跑(entry, no, ws); new = o if len(s) > 7 and s[7] == '不比原样' else o - bo[(entry, no)][1]   # 重放真实事故：现行脚本里的漏网处本身就必须报出
            hit = [l for l in new if want in l]
            ok = c != 0 and bool(hit)
            return sid, ok, (hit[0][:90] if hit else f'没挡住（退出码 {c}，新报出 {len(new)} 行：{"；".join(sorted(new))[:120]}）')
        res = list(ex.map(one, jobs))
        for sid, kind, payload, want, _ in 钩子场景:
            if 只 and sid not in 只: continue
            o = 跑钩子(kind, payload); ok = want in o and '"deny"' in o
            res.append((sid, ok, ('拦下：' + want) if ok else f'没挡住：{o[:100]}'))
    res += 仓库演练(W, root, 只)
    for x in os.listdir(root):
        if x.startswith('演练_'): (os.unlink if os.path.islink(f'{root}/{x}') else lambda p: shutil.rmtree(p, ignore_errors=True))(f'{root}/{x}')
    return res


def 覆盖():
    """{规矩: 演练样本}：本程序的场景 + 出片守门自检（make_video 入口）的每一项"""
    cov = {}
    for sid, entry, no, how, fn, want, rules, *_ in 场景:
        for r in rules: cov.setdefault(r, []).append(f'执行效应演练 {sid}')
    for sid, kind, payload, want, rules in 钩子场景:
        for r in rules: cov.setdefault(r, []).append(f'执行效应演练 {sid}（钩子）')
    for sid, entry, no, how, fn, want, rules in 仓库场景:
        for r in rules: cov.setdefault(r, []).append(f'执行效应演练 {sid}（仓库镜像）')
    # 已有的真入口自检（规则执行核查每次当场跑）：在临时仓库/临时副本里真跑那支程序、造错必须停
    for prog, rs in {'推送自检.py（临时仓库真跑 推送两仓库.sh）': ['G1', 'G2', 'G3', 'G4', 'G11', '守则3', '流12'],
                     '同步自检.py（临时副本真跑 sync_article.py）': ['S1', 'S3', 'S5'],
                     '出片守门自检.py（隔离工作区真跑 make_video.py）': ['A44', 'A36']}.items():
        for r in rs: cov.setdefault(r, []).append(prog)
    cov.setdefault('守则19', []).append('执行效应演练 自查拆门（拆掉 T36 的门，演练必须报没挡住）')
    sys.path.insert(0, T); import 出片守门自检 as G
    for c in G.CASES:
        if c[5] is not None: cov.setdefault(c[0], []).append(f'出片守门自检 {c[0]}')
    reg = json.load(open(f'{T}/规则执行表.json'))
    for k, v in reg.items():   # “同”：同一道门，演练了那道门就演练了它
        if k not in cov and any(o in cov for o in v.get('同', [])): cov[k] = [f'同 {o}' for o in v.get('同', []) if o in cov]
    return cov


def 缺口():
    reg = json.load(open(f'{T}/规则执行表.json')); cov = 覆盖()
    return sorted(k for k in reg if not k.startswith('_') and k not in cov)


def 印章有效():
    try: st = json.load(open(STAMP))
    except Exception: return False
    return all(st.get(x) == 指纹(f'{T}/{x}') for x in 被演练)


def 状态():
    reg = json.load(open(f'{T}/规则执行表.json')); g = 缺口(); n = len([k for k in reg if not k.startswith('_')])
    ok = 印章有效()
    return f'执行效应：{n - len(g)} 条规矩有端到端演练样本、{len(g)} 条还没有（缺口基线只许减少）；最近一次演练' + ('全部挡住、印章有效' if ok else '【已过期或没通过：程序或规矩改过，在视频工作目录重跑 执行效应演练.py】')


def main():
    a = sys.argv[1:]
    if '--状态' in a: print(状态()); return 0
    if '--缺口' in a: print(' '.join(缺口())); return 0
    W = os.getcwd()
    if not os.path.exists('make_video.py') or not os.path.isdir('scripts'): sys.exit('【停止】请在视频工作目录（含 make_video.py、scripts/）下运行')
    for x in ('make_video.py', 'render.py'):
        if 指纹(x) != 指纹(f'{T}/{x}'): sys.exit(f'【停止】工作目录的 {x} 与仓库不一致，先拷过来再演练')
    for no in sorted({s[2] for s in 场景} | {'24'}):
        if 指纹(f'scripts/{no}.json') != 指纹(f'{V}/脚本/{no}.json'): sys.exit(f'【停止】工作目录的 scripts/{no}.json 与仓库不一致，先拷过来再演练（演练要用现行脚本）')
    only = [x for x in a if not x.startswith('--')]
    res = 演练(W, only)
    for sid, ok, msg in res: print(f"{'✔' if ok else '✘'} {sid}：{msg}")
    sys.path.insert(0, T); import 规则执行核查 as RG
    gok = RG.印章有效('出片守门自检.py')
    print(('✔' if gok else '✘') + ' 出片守门自检（make_video 入口的演练）印章' + ('有效' if gok else '对不上：先跑 出片守门自检.py'))
    bad = [s for s, ok, _ in res if not ok] + ([] if gok else ['出片守门自检'])
    g = 缺口(); base = json.load(open(GAPB))['缺口'] if os.path.exists(GAPB) else None
    print(f'没有演练样本的规矩：{len(g)} 条' + (f'（基线 {base}）' if base is not None else ''))
    if base is not None and len(g) > base: bad.append(f'缺口变多（{len(g)} > 基线 {base}）：新规矩要同时加演练场景')
    if bad or only:
        print('执行效应演练：' + ('【没通过：' + '、'.join(bad) + '】' if bad else '部分演练通过（只跑了一部分，不盖印章）')); return 1 if bad else 0
    reg = json.load(open(f'{T}/规则执行表.json')); cov = 覆盖()   # 规则执行表每条记“演练”样本（程序按场景自动写，不手填）
    for k, v in reg.items():
        if k.startswith('_'): continue
        if k in cov: v['演练'] = cov[k]
        else: v.pop('演练', None)
    json.dump(reg, open(f'{T}/规则执行表.json', 'w'), ensure_ascii=False, indent=1)
    json.dump({**{x: 指纹(f'{T}/{x}') for x in 被演练}, '_挡住': [s for s, _, _ in res], '_有演练的规矩': len(cov)}, open(STAMP, 'w'), ensure_ascii=False, indent=1)
    if base is None or len(g) < base: json.dump({'缺口': len(g), '说明': '没有端到端演练样本的规矩条数，只许减少，目标 0'}, open(GAPB, 'w'), ensure_ascii=False, indent=1)
    print(f'执行效应演练：通过（{len(res)} 场演练全部挡在对的编号上，拆掉的门被发现；印章已写）'); return 0


if __name__ == '__main__':
    sys.exit(main())
