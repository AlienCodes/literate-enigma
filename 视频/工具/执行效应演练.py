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
import os, sys, json, copy, re, subprocess, hashlib, shutil, tempfile
from concurrent.futures import ThreadPoolExecutor
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
STAMP = f'{T}/执行效应演练通过.json'; GAPB = f'{T}/执行效应缺口基线.json'
被演练 = ['钩子/闸门.py', '踩坑核查.py', '译文核查.py', '破折号.py', 'check_all.py', '读音核对.py', 'make_video.py', 'render.py', '执行效应演练.py', '规则执行表.json', '放行口子核查.py', '放行口子表.json', '同意记录追加.py',
         '定稿流水线.sh', '归档定稿视频.py', '定稿视频核对.py', '工作稿核对.py', '补对照记录.py', '重查记录.py', '全篇核查.py', '开工提醒.sh', '开工记录.py', '初稿生成/核对.py', '规则执行核查.py', '排版自检.py', 'title2.py', '演练镜像.py', '演练样本/清单.json', '报坑.py', '开工必读.py', '意思个数.py']
sys.path.insert(0, T); import 演练镜像 as 镜
from 演练镜像 import 指纹, 样, 读样, 块, _读, _改文, _改json, _rec, _改行, 仓库底稿, 镜像, _工具副本, 工作区, _git状态   # 冻结样本、镜像（与声音演练共用）


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
def _同词异译(d):
    hits = [(c, m) for s in d['sentences'] for c in s['chunks'] for m in re.finditer(r'\*\*([^*]+)\*\*\(convicted of\)', c['zh'])]
    c, m = hits[1]; 改中文(c, m.group(0), f'**{m.group(1)}过**(convicted of)')
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
    ('T9对齐太粗', '出片', '23', '23 最长一块的所有组合成一组', _coarse, '[T9对齐]', ['T9', 'T5', '文6']),
    ('T13倍数结构', '出片', '23', '23 S1 加 half as strong as（比较、倍数结构没整组核对）', lambda d: (块(d, 0).__setitem__('en', 块(d, 0)['en'] + ' half as strong as'), 块(d, 0).__setitem__('zh', 块(d, 0)['zh'] + '一半强'), 块(d, 0)['align'].append(['half as strong as', '一半强'])), '[T13]', ['T13', '文8']),
    ('文10同词异译', '出片', '23', '23 第二处 convicted of 换一个中文（全篇译法不一）', _同词异译, '[文10]', ['文10']),
    ('A23Inky', '读音', '07', '重放 07 Inky 读成 ink-EYE：读音改正表去掉 Inky', None, 'Inky', ['A23', '守则6']),
]


# 仓库入口（D 类：读仓库文件的门，如 制作记录/NN.md 的踩坑对照记录、25 起才查的固定格式）：
# 在临时“仓库镜像”里跑真程序（镜像 = 仓库根的符号链接，只有要改的文件是副本；程序从镜像路径启动，V/ROOT 指向镜像，真仓库一个字不动）。
# 25 还没有：用 24 的脚本、制作记录副本当 25（篇号设成 25，25 起才查的门就生效）。
# (编号, 入口, 篇, 怎么造, 改法(files: {仓库相对路径: 文本}), 必须新报出的字样, 规矩)
def _加收工(f, no):   # G65：制作记录加一个很贵的收工行
    t = f[_rec(no)]; t = t.decode() if isinstance(t, bytes) else t
    f[_rec(no)] = t.replace('## token 记录\n', '## token 记录\n- 收工 2026-10-24T00:00（UTC）：等效 99.0M；主对话 99999 次、平均 900k （演练）\n', 1)


def _删节(f, no, h): t = f[_rec(no)]; i = t.index(h); j = t.find('\n## ', i + 1); f[_rec(no)] = t[:i] + (t[j + 1:] if j > 0 else '')
def _三义(d):
    c = 首块(d, lambda c: re.search(r'\*\*[^*/]+\*\*\(', c.get('zh', '')) is not None); c['zh'] = re.sub(r'\*\*([^*/]+)\*\*\(', r'**\1/演练甲/演练乙**(', c['zh'], count=1)
def _括号包词(d):
    c = 首块(d, lambda c: re.search(r'\*\*[^*]+\*\*\([^)]+\)', c['zh'])); m = re.search(r'\*\*[^*]+\*\*\([^)]+\)', c['zh']); 改中文(c, m.group(0), f'（{m.group(0)}）')
def _加注解(d):
    c = 块(d, 0); i = next(i for i, (a, z) in enumerate(c['align']) if a != '\n' and '**' not in a)
    a = c['align'][i][0]; c['en'] = c['en'].replace(a, a + ' {{(演练注解)}}', 1); c['align'][i][0] = a + ' {{(演练注解)}}'
def _镜像印章(f):
    """镜像里的演练印章按镜像里的文件重算（生成文本 先过规则执行核查；只为镜像里的前置门放行，真仓库的印章不动）"""
    k = '视频/工具/执行效应演练通过.json'; st = json.loads(_读(f, k) if not isinstance(f.get(k), bytes) else f[k].decode())
    for x in 被演练:
        t = f.get(f'视频/工具/{x}'); t = t.encode() if isinstance(t, str) else (None if isinstance(t, tuple) else t)
        st[x] = hashlib.sha256(t).hexdigest() if t is not None else 指纹(f'{T}/{x}')   # 演练样本/ 在镜像里是链接：按真文件算
    import 同意记录追加 as TY; t = _读(f, '视频/工具/用户同意记录.json'); st['_同意记录前缀'] = TY.印(json.loads(t.decode() if isinstance(t, bytes) else t))
    f[k] = json.dumps(st, ensure_ascii=False)
    import 执行效应声音演练 as SY; k2 = '视频/工具/执行效应声音演练通过.json'   # 声音演练印章同样按镜像重算（镜像里只是前置门，真印章不动）
    st2 = {}
    for x in SY.声音被演练:
        t = f.get(f'视频/工具/{x}'); t = t.encode() if isinstance(t, str) else (None if isinstance(t, tuple) else t); st2[x] = hashlib.sha256(t).hexdigest() if t is not None else 指纹(f'{T}/{x}')
    f[k2] = json.dumps(st2, ensure_ascii=False)
    import 规则执行核查 as _R; st3 = {}   # L 彩排印章同样按镜像重算（镜像里只是前置门；真印章要 GitHub 全新容器彩排才盖）
    for x in _R.STAMPED['彩排.sh'][1]:
        t = f.get(f'视频/工具/{x}'); t = t.encode() if isinstance(t, str) else (None if isinstance(t, tuple) else t); st3[x] = hashlib.sha256(t).hexdigest() if t is not None else 指纹(f'{T}/{x}')
    f['视频/工具/彩排通过.json'] = json.dumps(st3, ensure_ascii=False)
def _变异(prog, old, new):
    def fn(f):
        k = f'视频/工具/{prog}'; t = f[k].decode() if isinstance(f[k], bytes) else f[k]
        assert t.count(old) == 1, f'{prog} 里找不到（或不止一处）：{old[:40]}'; f[k] = t.replace(old, new).encode()
    return fn


仓库场景 = [
    ('G6固定格式25', '踩坑出片', '25', '25 的 G6 写成套话以外的自由句子（不是“本篇无/本篇有”）', lambda f: _改行(f, '25', 'G6', '用户两次要求不冲突，没有需要问的'), '只认固定格式', ['G6', 'C3', 'C4']),
    ('C4固定格式25', '踩坑出片', '25', '25 的 C4 写“本篇有：合并改了”但没有用户原话', lambda f: _改行(f, '25', 'C4', '本篇有：两次插话合并成一次改了'), '只认固定格式', ['C4', 'C3']),
    ('G6套话', '踩坑出片', '25', '25 的 G6 用开工自动填的套话', lambda f: _改行(f, '25', 'G6', '按现行做法由程序把关（踩坑总表“拦住”），本篇核查通过'), '只有人能判', ['G6', 'C3', 'C4']),
    ('法1对照没填完', '踩坑出片', '25', '25 踩坑对照记录 T1 一格写回“待填”', lambda f: _改行(f, '25', 'T1', '待填'), '没填完', ['法1', '流3', '铁7']),
    ('守则13没写方法设计', '踩坑出片', '25', '25 制作记录删掉“## 方法设计”', lambda f: _删节(f, '25', '## 方法设计'), '[T31]', ['守则13', 'T31']),
    ('守则12没写方法复盘', '踩坑出片', '25', '25 制作记录删掉“## 方法复盘”', lambda f: _删节(f, '25', '## 方法复盘'), '[T29]', ['守则12', 'T29']),
    ('S2速查表本文重复', '踩坑出片', '24', '24 速查表 departed 一行写成两个“本文：”', lambda f: _改文(f, _文24, '| departed | v.', '| departed | 本文：离开；本文：出发；v.'), 'S2 速查表', ['S2']),
    ('S4速查表缺词性', '踩坑出片', '24', '24 速查表 remote 一行只剩“本文：”', lambda f: _改文(f, _文24, '| remote | adj. 偏远的', '| remote | 本文：偏远的 |x'), 'S4 速查表缺词性', ['S4']),
    ('G18原稿重点词空', '踩坑出片', '24', '原稿重点词.json 没有本篇（重放 20 篇浅克隆）', lambda f: _改json(f, '视频/工具/原稿重点词.json', lambda o: o.pop(_文24)), 'G18 原稿重点词', ['G18']),
    ('T11重点词漏标', '踩坑出片', '24', '24 一个重点词的中文去掉 (英文) 标记（check_all D4）', lambda f: _改json(f, '视频/脚本/24.json', _d4), '[check_all] D4', ['T11']),
    ('T12新加撞词', '踩坑出片', '24', '24 把别篇加粗过的词也加粗（新加重点词撞词）', lambda f: _改json(f, '视频/脚本/24.json', _撞词), 'T12 新加重点词撞词', ['T12', 'T17']),
    # —— C 类：定稿 / 归档 / 清点 / 流水线（镜像里真跑，流水线走到 ① 就掐掉；真仓库 git status 不许变）
    ('L12归档1080p', '归档', '24', '视频/视频/24.mp4 放 1080p 草稿，跑 归档定稿视频', lambda f: f.__setitem__('视频/视频/24.mp4', ('链接', f'{V}/视频/草稿1080p/24_1080p.mp4')), '不是 4K 定稿视频', ['L12']),
    ('G9存的不是最终版', '清点', '23', '视频/视频/23.mp4 换成别的视频（存了老视频）', lambda f: f.__setitem__('视频/视频/23.mp4', ('链接', f'{V}/视频/22.mp4')), '[G9] 第23篇 视频/视频/23.mp4', ['G9']),
    ('G9旧标题旧版本', '清点', '23', '最终版4K视频 多一个旧标题的 23', lambda f: f.__setitem__('最终版4K视频/23 - Old Title - 旧标题.mp4', ('链接', f'{V}/视频/23.mp4')), '文件名与定稿脚本的标题不一致', ['G9']),
    ('流7没说定稿就定稿', '流水线', '24', '用户同意记录里没有“定稿 24”，跑定稿流水线', lambda f: _改json(f, '视频/工具/用户同意记录.json', lambda o: o.__setitem__('记录', [r for r in o['记录'] if not (r.get('篇') == '24' and '定稿' in r.get('用于', ''))])), '用户还没说定稿', ['流7']),
    ('G28定稿后撤回', '流水线', '24', '用户同意记录里“定稿 24”后面又有一条“撤回 定稿 24”，跑定稿流水线', lambda f: _改json(f, '视频/工具/用户同意记录.json', lambda o: o.__setitem__('记录', [r for r in o['记录'] if not (r.get('篇') == '24' and '定稿' in r.get('用于', ''))]
        + [{'篇': '24', '日期': '2026-10-24', '原话': '演练：最终版出来了吗，给我', '用于': '定稿 24', '来源': '演练'}, {'篇': '24', '日期': '2026-10-24', '原话': '演练：暂停，我先核查一下', '用于': '撤回 定稿 24', '来源': '演练'}])), '用户还没说定稿', ['G28']),
    ('G30不出Word不误停', '踩坑出片', '25', '25 没有对照文本 docx（守则17 只做视频）', None, lambda c, o, M: (not any('25-文本.docx' in l for l in o), '25 没有 docx 不报缺（守则17）' if not any('25-文本.docx' in l for l in o) else '误停：' + next(l for l in o if '25-文本.docx' in l)[:80]), ['G30', '守则17']),
    ('G30缺docx仍停23', '踩坑出片', '23', '已定稿的 23 对照文本 docx 没了', lambda f: f.__setitem__('视频/对照文本/23-文本.docx', ('链接', '/演练不存在/23-文本.docx')), '缺文件: 视频/对照文本/23-文本', ['G30']),
    ('T12全篇撞车', '踩坑出片', '25', '25 新加一个只在没做视频的篇目里加粗过的词（撞车看整个70篇）', lambda f: _改json(f, '视频/脚本/25.json', _撞词全篇), 'T12 撞车', ['G32', 'G33']),
    ('G54报坑超期', '流水线', '24', '坑登记里一条登记 30 小时前报的、还没进踩坑总表，跑定稿流水线', lambda f: _改json(f, '视频/制作记录/坑登记.json', lambda o: o['登记'].append({'号': 'K999', '时刻': (__import__('datetime').datetime.now(__import__('datetime').timezone.utc) - __import__('datetime').timedelta(hours=30)).strftime('%Y-%m-%dT%H:%MZ'), '会话': '演练', '现象': '演练造的超期没入表的坑'})), '演练造的超期没入表', ['G54']),
    ('G60证据链不全', '流水线', '24', '24 一条机制证据都没有（证据起始篇改成 24 重放），跑定稿流水线', _变异('证据.py', '起 = 28', '起 = 24'), '机制证据不全', ['G60']),
    ('G62步骤表没跟', '规则核查', '24', '草稿流程.md 加了一步、开工必读没重新生成', _变异('草稿流程.md', '\n## 禁止', '\n9. 演练造的新步骤 `python3 $T/x.py NN`\n\n## 禁止'), '与现行规矩', ['G62']),
    ('G65进化变差没落地', '流水线', '24', '24 制作记录加一个 99M、99999 次调用的收工行（比前三篇中位数贵得多），方法复盘没有进化落地（起始篇改成 24 重放），跑定稿流水线', lambda f: (_变异('方法进化表.py', '\n起 = 27 ', '\n起 = 24 ')(f), _加收工(f, '24')), '【G65 方法进化】', ['G65']),
    ('G71机制闲置', '流水线', '24', '闲置报警起始篇改成 24 重放：24–26 已做完、一条机制证据都没有（每个机制连续三篇该用没用），跑定稿流水线', _变异('证据.py', '闲置从 = 28', '闲置从 = 24'), '机制闲置', ['G71']),
    ('G63没开工就提交', '会话开工查', '24', '本会话没跑 会话开工.py（没读开工必读），提交前检查', None, '本会话还没开工', ['G63']),
    ('G72老条目被改', '配音缓存自检', '24', '出片程序读缓存时不再核老条目指纹（老条目被改、被换也照用）', _变异('make_video.py', "    if _OLD.get(b)==h: return", "    return"), '没抓到：老条目被改', ['G72']),
    ('G72无标记新条目', '配音缓存自检', '24', '出片程序读缓存时不再查 .单线程 标记（多线程悄悄合成的新条目也照用）', _变异('make_video.py', "    if os.path.exists(p+'.单线程'):\n        if open(p+'.单线程').read().strip()==h: return", "    if True:\n        return"), '没抓到：没有 .单线程 标记', ['G72']),
    ('G73取号弄脏本地', '报坑自检', '24', '原子写推完又往本地工作区写一份坑登记并暂存（K32 的老毛病）', _变异('报坑.py', "            git('fetch', '-q', 'origin', 分支, repo=repo)   # K32", "            git('fetch', '-q', 'origin', 分支, repo=repo); open(f'{repo}/{REL}', 'w').write('{}'); git('add', REL, repo=repo)   # K32"), '没抓到：取号后本地工作区留了改动', ['G73']),
    ('G66没持锁改门', '报坑自检', '24', '改门锁的提交前检查被改成谁都放行（没持锁也能改门程序）', _变异('报坑.py', "    if 锁有效(L, now) and L['会话'] == 会话: return []", "    return []"), '没持锁的会话改门程序', ['G66']),
    ('G64自检指向真origin', '报坑自检', '24', '报坑.py 取号自检的临时仓库 origin 被改成真仓库', _变异('报坑.py', "sh('git init -q --bare r.git && git clone -q r.git a && git clone -q r.git b')", "sh('git init -q --bare r.git && git clone -q r.git a && git clone -q r.git b && git -C a remote set-url origin /home/user/postgraduate-vocabulary')"), '自检指向真 origin', ['G64']),
    ('G55做事对照没写', '踩坑出片', '25', '25 制作记录没有“## 做事对照记录”（开工必读的起始篇改成 25 重放）', _变异('开工必读.py', '起 = 28', '起 = 25'), '[开工必读] 制作记录/25.md 没有“## 做事对照记录”', ['G55', '文35']),
    ('文36三个意思', '踩坑出片', '25', '25 一个重点词的中文写成三个意思（意思个数的起始篇改成 25 重放）', lambda f: (_变异('意思个数.py', '起 = 27', '起 = 25')(f), _改json(f, '视频/脚本/25.json', _三义)), '[文36]', ['文36']),
    ('G19工作稿是旧稿', '流水线', '23', '仓库 视频/脚本/23.json 被别的会话改了，工作目录还是旧稿', lambda f: (f.__setitem__('工作稿', f['视频/脚本/23.json']), _改json(f, '视频/脚本/23.json', lambda d: d.__setitem__('title_zh', d['title_zh'] + '（新）'))), '旧稿（G19）', ['G19']),
    ('画17规则核查在最前', '流水线', '23', '规则执行表一道门的锚改坏，流水线必须停在 ⓪、不进 ①', lambda f: _改json(f, '视频/工具/规则执行表.json', lambda r: r['T36'].__setitem__('门', [['破折号.py', '演练造的坏锚']])), '演练造的坏锚', ['画17']),
    ('G21程序把关的坑自动补', '踩坑出片', '25', '对照记录缺 T36 一行（程序把关的新坑）：必须自动补上、不停', lambda f: f.__setitem__(_rec('25'), re.sub(r'^\| *T36 *\|.*\n', '', f[_rec('25')], flags=re.M)),
     lambda c, o, M: ((not any('缺条目' in l and 'T36' in l for l in o)) and bool(re.search(r'^\| *T36 *\|', open(f'{M}/{_rec("25")}').read(), re.M)), '缺 T36 → 自动补进对照记录，没有白停'), ['G21']),
    ('G22改了定稿脚本要提醒', '踩坑文本', '23', '改了已定稿 23 的脚本（存的 4K 对不上了）', lambda f: _改json(f, '视频/脚本/23.json', lambda d: d.__setitem__('title_zh', d['title_zh'] + '（改）')),
     lambda c, o, M: (any('[G22]' in l for l in o), next((l[:90] for l in o if '[G22]' in l), '没提醒重出 4K')), ['G22']),
    ('铁4改了出片程序要全篇重查', '欠着', '23', 'make_video.py 改一处（全篇重查记录都是通过的）', lambda f: f.__setitem__('视频/工具/make_video.py', f['视频/工具/make_video.py'] + b'\n# \xe6\xbc\x94\xe7\xbb\x83\xe6\x94\xb9\xe4\xb8\x80\xe5\xa4\x84\n'),
     lambda c, o, M: (c == 0, '全篇核查 --欠着 报欠着（流水线 ⑦ 全篇重查）' if c == 0 else '改了出片程序却不欠着'), ['铁4', '画21', '音29']),
    ('G14钩子会锁死', '规则核查', '24', '钩子命令去掉“|| true”', lambda f: f.__setitem__('.claude/settings.json', f['.claude/settings.json'].replace(' || true', '', 1)), '钩子会锁死', ['G14']),
    ('G25演练读现稿', '演练入口', '24', '演练程序改回读工作目录的现稿 scripts/24.json', _变异('执行效应演练.py', '_A镜像 = ' + '[None]\n', '_A镜像 = ' + "[None]\n_读现稿 = lambda W: open(f'{W}/" + "scripts/24.json')\n"), '读了现稿', ['G25']),
    ('A26挂钩原文没了', '规则核查', '24', '出片程序里核查程序挂钩的那一句改掉', lambda f: _断挂钩(f), '挂钩的出片程序原文没了', ['A26']),
    ('守则1开工提醒', '开工提醒', '24', '新会话开工（真开工钩子）', None, lambda c, o, M: (any('【开工必做' in l for l in o), '开工钩子打印【开工必做】'), ['守则1']),
    ('G23开工记录不覆盖', '开工记录', '25', '主对话已写好方法设计后再跑 开工记录', None,
     lambda c, o, M: (open(f'{M}/{_rec("25")}').read().startswith(仓库底稿('25')[_rec('25')].rstrip('\n')), '已有的制作记录原样保留、只追加'), ['G23']),
    ('T37多词重点词不误报', '初稿', '24', '重放 24：hinge on 等多词重点词，初稿核对不许报“缺”', None, lambda c, o, M: (c == 0 and not any('缺：' in l for l in o) and any('对照里都在' in l for l in o), '多词重点词不误报'), ['T37']),
    # —— B 类：画面、片头（render.py、title2.py 的做法就是门）：镜像里把排版程序改坏一处（= 有人改程序改坏了画面），
    #    真入口 排版自检.py（规则执行核查每次当场跑：提交、推送、交付核查、定稿流水线 ⓪ 都过它）必须报出那一条
    *[(f'{k}排版程序改坏', '排版', '24', how, _变异(prog, old, new), f'没抓到：{want}', rules) for k, prog, how, old, new, want, rules in [
        ('L1', 'render.py', '字号不再取放得下的最大号（固定一个小号）', 'for es in range(130*S,30,-1):', 'for es in [60*S]:', 'L1/L4 每屏字号铺满', ['L1']),
        ('L4', 'render.py', '字号全片统一（不按句算）', 'for es in range(130*S,30,-1):', 'for es in [60*S]:', 'L4 字号按句算', ['L4']),
        ('L5', 'render.py', '中文字号比例改成 0.8', 'ES_FIXED=None; ZR=0.72', 'ES_FIXED=None; ZR=0.8', 'L5 中文 = 英文 × 0.72', ['L5']),
        ('L2', 'render.py', '一行放得下也拆行', "if u!='\\x00' and wcur+w>maxw and lines[-1] and u.strip():", "if u!='\\x00' and lines[-1] and u.strip():", 'L2 放得下不拆行', ['L2']),
        ('L3', 'render.py', '末行孤词不再查', 'def orphan_lines(chunks,colors,notes,es):', 'def orphan_lines(chunks,colors,notes,es):\n    return []', 'L3 末行孤词查得出', ['L3']),
        ('L6', 'render.py', '数字按单个数字拆', "parts=re.findall(r'\\S+\\s*|\\s+',t) if not cjk", "parts=re.findall(r'\\d\\s*|[^\\d\\s]+\\s*|\\s+',t) if not cjk", 'L6 数字不拆', ['L6']),
        ('L7', 'render.py', '说明不计入字号', 'wide=max([wide]+[nf.getlength(_note_txt(ln))', 'wide=max([wide]+[0*nf.getlength(_note_txt(ln))', 'L7 说明计入字号', ['L7']),
        ('L8', 'render.py', '正文页画上标题', 'nf_=ZH(int(zs*0.9),400)\n    im=bg(); d=ImageDraw.Draw(im)', "nf_=ZH(int(zs*0.9),400)\n    im=bg(); d=ImageDraw.Draw(im); d.text((40,20),str(header),fill=(255,255,255),font=ZH(40*S,400))", 'L8 正文页不画标题', ['L8']),
        ('L10', 'render.py', '另译不再用黄字', 'nc=(251,191,36) if on else dim((251,191,36))', 'nc=(200,200,200) if on else dim((200,200,200))', 'L10 另译黄字', ['L10']),
        ('L11', 'render.py', '重点词中文两侧不留间隙', 'tx[0] not in PUN: res.append((KSP,None))', 'tx[0] not in PUN: pass', 'L11 重点词两侧间隙', ['L11']),
        ('L15', 'render.py', '中文意思找不到颜色也不停', 'if miss: raise SystemExit(f\'【停止】画面上这些中文意思找不到颜色', 'if False: raise SystemExit(f\'【停止】画面上这些中文意思找不到颜色', 'L15 找不到颜色就停', ['L15']),
        ('D5', 'render.py', '{{注解}} 也朗读', "def strip_gloss(t): return re.sub(r'\\{\\{.*?\\}\\}','',t)", 'def strip_gloss(t): return t', 'D5 注解只显示不朗读', ['D5']),
        ('D6', 'render.py', '中文格内 \\n 不去掉', "def strip_zh(t): return re.sub(ZCOL,r'\\1',t).replace('\\n','')", "def strip_zh(t): return re.sub(ZCOL,r'\\1',t)", 'D6 格内分行与彩色说明', ['D6']),
        ('画1', 'render.py', '画面改成 16:10', 'W,H=1920*S,1080*S', 'W,H=1920*S,1200*S', '画1 画面 16:9', ['画1']),
        ('L20', 'render.py', '重点词中文不再对正（退回格内居中）', '    if not (ALIGN_RULE[0] if align is None else align): return xe0,xz0', '    return xe0,xz0', 'L20 重点词对正', ['L20', '画22', '单28']),
        ('L20旧篇', 'render.py', '对正排法开到 01–23（定稿画面变了）', 'ALIGN_RULE=[False]; ALIGN_FROM=24', 'ALIGN_RULE=[False]; ALIGN_FROM=1', 'L20 01–23 照旧居中', ['L20', '画22']),
        ('G35', 'render.py', '无特批放宽上限从 1.5 改成 9（说明可以无限放宽）', "1 < float(v_.get('倍数', 0)) <= 1.5", "1 < float(v_.get('倍数', 0)) <= 9", 'L19 放宽特批上限', ['G35']),
        ('G37', 'render.py', '说明放右侧不再要求用户原话', "if not (isinstance(v_, dict) and '用户' in v_.get('依据', '') and", "if not (isinstance(v_, dict) and", 'G37 说明放右侧没有用户原话必停', ['G37']),
        ('H1', 'title2.py', '片头色块往右偏', '[(W - zw) / 2 - pad, y, (W + zw) / 2 + pad, y + ph]', '[(W - zw) / 2 - pad + 300 * S, y, (W + zw) / 2 + pad + 300 * S, y + ph]', 'H1 片头色块水平居中', ['H1']),
        ('H2', 'title2.py', '色块不是圆角', 'radius=18 * S, fill=AC1', 'radius=0, fill=AC1', 'H2 色块是圆角长方形', ['H2']),
        ('H3', 'title2.py', '色块里的字往下偏', 'y + (ph - (bb[3] - bb[1])) / 2 - bb[1]), zh', 'y + (ph - (bb[3] - bb[1])) / 2 - bb[1] + 20 * S), zh', 'H3 色块里的字上下居中', ['H3']),
    ]],
    ('G7定稿篇目草稿没删', '踩坑出片', '23', '已定稿的 23 还留着 1080p 草稿', lambda f: f.__setitem__('视频/视频/草稿1080p/23_1080p.mp4', ('链接', f'{V}/视频/草稿1080p/24_1080p.mp4')), '[G7]', ['G7']),
    ('T6空译文', '踩坑出片', '23', '23 S4 一块中文清空', lambda f: _改json(f, '视频/脚本/23.json', lambda d: (块(d, 3).__setitem__('zh', ''), 块(d, 3).__setitem__('align', [[a, ''] for a, _ in 块(d, 3)['align']]))), '[T6]', ['T6']),
    ('T1括号包重点词', '踩坑出片', '23', '23 第一个重点词的中文外面加括号（说明里包着重点词）', lambda f: _改json(f, '视频/脚本/23.json', _括号包词), 'T19括号含重点词', ['T1']),
    # —— 对照文本（守则17 暂停出 Word/PDF；恢复出文本时这些门照样要挡）：镜像里真跑 生成文本.py（出 Word/HTML/PDF、逐格读回）
    ('W5没生成PDF', '生成文本', '23', '浏览器转 PDF 失败（PDF 没有生成）', _变异('生成文本.py', "f'--print-to-pdf={pdf}'", "f'--print-to-pdf={pdf}.演练'"), 'PDF 没有生成', ['W5']),
    ('W1Word和脚本对不上', '生成文本', '23', 'make_docx 写进 Word 的字少一个', _变异('make_docx.py', 'r=p.add_run(t);', 'r=p.add_run(t[:-1] if len(t)>3 else t);'), 'Word 格不一致', ['W1']),
    ('W10读回不按同一函数', '生成文本', '23', '读回时英文不按 make_docx 的同一个函数（{{注解}} 原样比）', lambda f: (_改json(f, '视频/脚本/23.json', _加注解), _变异('生成文本.py', "''.join(x for x, _ in _R._segs_en(a, {}))", "(a if 1 else ''.join(x for x, _ in _R._segs_en(a, {})))")(f)), 'Word 格不一致', ['W10']),
    ('W7用户修正稿不覆盖', '生成文本', '23', '对照文本里有用户发回的修正稿 23-文本-用户修正.docx', lambda f: f.__setitem__('视频/对照文本/23-文本-用户修正.docx', b'USER-FIXED'),
     lambda c, o, M: (c == 0 and open(f'{M}/视频/对照文本/23-文本-用户修正.docx', 'rb').read() == b'USER-FIXED' and open(f'{M}/视频/对照文本/23-文本.docx', 'rb').read() != 读样('视频/对照文本/23-文本.docx', True),
                      '用户修正稿原样、23-文本.docx 一起覆盖' if c == 0 else f'生成文本没跑通（退出码 {c}）：' + '；'.join(sorted(o))[-150:]), ['W7']),
]
# 拆门自查（每种入口拆一道门，演练必须报“没挡住”）：(入口, 篇, 用哪一场, 拆门代码)
仓库拆门 = [('踩坑出片', '25', 'G6固定格式25', 'K.人判格式_起 = 999'),
        ('流水线', '24', '流7没说定稿就定稿', lambda f: f.__setitem__('视频/工具/放行口子核查.py', f['视频/工具/放行口子核查.py'].replace(b'def \xe5\xae\x9a\xe7\xa8\xbf\xe5\x90\x8c\xe6\x84\x8f(no, rec=None):', b'def \xe5\xae\x9a\xe7\xa8\xbf\xe5\x90\x8c\xe6\x84\x8f(no, rec=None):\n    return True'))),
        ('排版', '24', 'L5排版程序改坏', lambda f: f.__setitem__('视频/工具/排版自检.py', f['视频/工具/排版自检.py'].replace('判(\'L5 中文 = 英文 × 0.72\', '.encode(), '判(\'L5 中文 = 英文 × 0.72\', True or '.encode()))),
        ('清点', '23', 'G9存的不是最终版', 'import hashlib;hashlib.sha256=lambda b=b\'\': hashlib.md5(b\'\')')]


_文24 = os.path.relpath(__import__('glob').glob(样('新版定稿/24-*.md'))[0], 镜.样本根)
def _英文段(x):
    t = open(x).read(); return t.split('## 英文', 1)[1].split('## 中文', 1)[0]
def _撞词(d):
    """24 里找一个别篇加粗过、24 原稿没加粗的词，加粗并补中文标记"""
    import glob
    other = {b.lower() for x in glob.glob(样('新版定稿/[0-9][0-9]-*.md')) if not os.path.basename(x).startswith('24') and os.path.exists(样(f'视频/脚本/{os.path.basename(x)[:2]}.json'))
             for b in re.findall(r'\*\*([^*]+)\*\*', _英文段(x)) if ' ' not in b}
    orig = {x.lower() for x in json.loads(读样('视频/工具/原稿重点词.json')).get(_文24, [])}
    for s in d['sentences']:
        for c in s['chunks']:
            for i, (a, z) in enumerate(c['align']):
                for w in re.findall(r'(?<![*A-Za-z])([a-z]{6,})(?![*A-Za-z])', a):
                    if w in other and w not in orig and z and '**' not in z:
                        c['en'] = re.sub(rf'(?<![*A-Za-z]){w}(?![*A-Za-z])', f'**{w}**', c['en'], count=1); c['align'][i] = [re.sub(rf'(?<![*A-Za-z]){w}(?![*A-Za-z])', f'**{w}**', a, count=1), f'**{z}**({w})']
                        c['zh'] = ''.join(b for _, b in c['align']); return
    raise KeyError('24 里没有可撞的词')


def _撞词全篇(d):
    """T12 全篇（用户 2026-10-24：撞车检查看整个70篇）：25（24 的副本）里找一个只在没做视频的篇目加粗过的词，加粗并补中文标记"""
    import glob
    made = {b.lower() for x in glob.glob(样('新版定稿/[0-9][0-9]-*.md')) if os.path.exists(样(f'视频/脚本/{os.path.basename(x)[:2]}.json')) for b in re.findall(r'\*\*([^*]+)\*\*', _英文段(x))}
    other = {b.lower() for x in glob.glob(样('新版定稿/[0-9][0-9]-*.md')) if not os.path.basename(x).startswith(('24', '25')) and not os.path.exists(样(f'视频/脚本/{os.path.basename(x)[:2]}.json'))
             for b in re.findall(r'\*\*([^*]+)\*\*', _英文段(x)) if ' ' not in b} - made
    for s in d['sentences']:
        for c in s['chunks']:
            for i, (a, z) in enumerate(c['align']):
                for w in re.findall(r'(?<![*A-Za-z])([a-z]{6,})(?![*A-Za-z])', a):
                    if w in other and z and '**' not in z:
                        c['en'] = re.sub(rf'(?<![*A-Za-z]){w}(?![*A-Za-z])', f'**{w}**', c['en'], count=1); c['align'][i] = [re.sub(rf'(?<![*A-Za-z]){w}(?![*A-Za-z])', f'**{w}**', a, count=1), f'**{z}**({w})']
                        c['zh'] = ''.join(b for _, b in c['align']); return
    raise KeyError('25 里没有只在没做视频的篇目加粗过的词')


def _断挂钩(f):
    import importlib; sys.path.insert(0, T); RG = importlib.import_module('规则执行核查')
    for k, t in f.items():
        if not (k.startswith('视频/工具/') and k.endswith('.py')) or not isinstance(t, bytes): continue
        t = t.decode(); 
        if os.path.basename(k) in ('make_video.py', 'render.py', '规则执行核查.py', '执行效应演练.py') or 'make_video.py' not in t: continue
        for l in t.splitlines():
            for q, anc in re.findall(r"""(?:_?src|read\(\))\.(?:index|split|replace)\(\s*(['"])(.+?)\1""", l):
                mv = f['视频/工具/make_video.py'].decode()
                if anc in mv: f['视频/工具/make_video.py'] = mv.replace(anc, anc[:-1] + '\u2060' + anc[-1]).encode(); return
    raise KeyError('找不到挂钩的原文')


无原样 = {'归档', '流水线', '初稿', '生成文本', '会话开工查'}   # 这些入口原样跑会真做事（归档写文件、流水线出 4K）：不跑原样，只认必须报出的字样
def 仓库跑(entry, no, M, ws, 拆门=None):
    tool = f'{M}/视频/工具'; env = {**os.environ, 'CLAUDE_PROJECT_DIR': M}
    py = lambda prog, *a: ['python3', '-c', f"import sys;sys.path.insert(0,{tool!r});sys.argv=[{prog!r}]+{list(a)!r};import runpy;{拆门};runpy.run_path({tool + '/' + prog!r},run_name='__main__')"] if 拆门 else ['python3', f'{tool}/{prog}', *a]
    if entry == '踩坑出片':
        cmd = ['python3', '-c', f"import sys;sys.path.insert(0,{tool!r});import 踩坑核查 as K;{拆门};sys.argv=['踩坑核查.py',{no!r},'出片'];sys.exit(K.main())"] if 拆门 else ['python3', f'{tool}/踩坑核查.py', no, '出片']
    elif entry == '踩坑文本': cmd = ['python3', f'{tool}/踩坑核查.py', no, '文本']
    elif entry == '排版': cmd = ['python3', f'{tool}/排版自检.py']
    elif entry == '生成文本': cmd = ['python3', f'{tool}/生成文本.py', no]
    elif entry == '归档': cmd = py('归档定稿视频.py', no)
    elif entry == '清点': cmd = py('定稿视频核对.py', '--只查清点和镜像', no)
    elif entry == '规则核查': cmd = ['python3', f'{tool}/规则执行核查.py']
    elif entry == '演练入口': cmd = ['python3', f'{tool}/执行效应演练.py', '--只过门']   # G25：演练开跑前查读现稿
    elif entry == '欠着': cmd = ['python3', f'{tool}/全篇核查.py', '--欠着']
    elif entry == '开工提醒': cmd = ['bash', f'{tool}/开工提醒.sh']
    elif entry == '报坑自检': cmd = ['python3', f'{tool}/报坑.py', '--自检']   # G64：自检只许碰假远端
    elif entry == '配音缓存自检': cmd = ['python3', f'{tool}/配音缓存核对.py', '--自检']   # G72：出片程序的缓存两道门
    elif entry == '会话开工查': cmd = ['python3', f'{tool}/会话开工.py', '--查']; env['HOME'] = tempfile.mkdtemp(prefix='演练_空HOME_')   # G63：空 HOME = 没开工的会话
    elif entry == '开工记录': cmd = ['python3', f'{tool}/开工记录.py', no]
    elif entry == '初稿': cmd = ['python3', f'{tool}/初稿生成/gen{no}.py']
    elif entry == '流水线':   # 真跑 定稿流水线.sh（镜像里），走到“① 出片前核查”就掐掉：前面的门该停没停 = 没挡住；后面的出 4K、归档、推送一步不做
        pr = subprocess.Popen(['bash', f'{tool}/定稿流水线.sh', no], cwd=ws, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True); out = []
        for l in pr.stdout:
            out.append(l.strip())
            if l.startswith('== ') and '⓪' not in l: pr.kill(); out.append('【演练掐断：流水线走到了 ⓪ 以后的步骤】'); break
        pr.wait(); return (pr.returncode if '【演练掐断' not in out[-1] else 0), set(x for x in out if x)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ws, timeout=900, env=env)
    return r.returncode, set(l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip())


def 仓库演练(W, root, 只=None):
    todo = [s for s in 仓库场景 if not 只 or s[0] in 只]
    if not todo: return []
    g0 = _git状态(); base, jobs = {}, []
    for sid, entry, no, how, fn, want, rules in todo:
        f0 = 仓库底稿(no, entry)
        if (entry, no) not in base and entry not in 无原样:
            base[(entry, no)] = (镜像(f'{root}/演练_镜像_原样_{entry}_{no}', f0), 工作区(W, root, f'原样仓库_{entry}_{no}', no, json.loads(f0[f'视频/脚本/{no}.json'])))
        f = dict(f0)
        try: fn and fn(f)
        except Exception as e: jobs.append((sid, None, None, f'样本找不到：{e!r}')); continue
        if entry == '生成文本': _镜像印章(f)
        ws = 工作区(W, root, f'仓库_{sid}', no, json.loads(f[f'视频/脚本/{no}.json']))
        if '工作稿' in f: open(f'{ws}/scripts/{no}.json', 'w').write(f.pop('工作稿'))   # 工作目录里的稿（G19：比仓库旧）
        jobs.append((sid, 镜像(f'{root}/演练_镜像_{sid}', f), ws, None))
    with ThreadPoolExecutor(4) as ex:
        bo = dict(zip(base, ex.map(lambda k: 仓库跑(k[0], k[1], *base[k]), base)))
        def one(j):
            sid, M, ws, err = j
            if err: return sid, False, err
            s = next(x for x in 仓库场景 if x[0] == sid); entry, no, want = s[1], s[2], s[5]
            c, o = 仓库跑(entry, no, M, ws)
            if callable(want): ok, msg = want(c, o, M); return sid, ok, msg
            new = o - bo[(entry, no)][1] if (entry, no) in bo else o; hit = [l for l in new if want in l]
            return sid, c != 0 and bool(hit), (hit[0][:90] if hit else f'没挡住（退出码 {c}，新报出：{"；".join(sorted(new))[:120]}）')
        res = list(ex.map(one, jobs))
        for entry, no, sid, code in 仓库拆门:
            if 只 and sid not in 只: continue
            j = next((x for x in jobs if x[0] == sid and x[1]), None)
            if not j: res.append((f'自查拆门_{entry}', False, '样本找不到')); continue
            s = next(x for x in 仓库场景 if x[0] == sid)
            if callable(code):   # 拆门 = 再改一个程序文件（镜像里），其余同那一场
                f = 仓库底稿(no, entry); s[4] and s[4](f); code(f); M2 = 镜像(f'{root}/演练_镜像_拆门_{sid}', f); ws2 = 工作区(W, root, f'拆门_{sid}', no, json.loads(f[f'视频/脚本/{no}.json']))
                c, o = 仓库跑(entry, no, M2, ws2); code = '改坏 ' + sid + ' 的门'
            else: c, o = 仓库跑(entry, no, j[1], j[2], 拆门=code)
            caught = s[5](c, o, j[1])[0] if callable(s[5]) else (c != 0 and any(s[5] in l for l in o - bo.get((entry, no), (0, set()))[1]))
            res.append((f'自查拆门_{entry}', not caught, f'拆掉门（{code[:40]}）后演练报“没挡住”（演练能发现坏门）' if not caught else '拆掉门后演练还说挡住了：演练失灵'))
    if _git状态() != g0: res.append(('真仓库没被碰', False, '演练改了真仓库（git status 变了）：镜像漏了写入的路径，先修演练'))
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
    ('W6发Word提醒背景色', '发文件后', {'tool_input': {'files': ['/tmp/演练_对照.docx']}}, '【W6 提醒】', ['W6'], '提醒'),   # 提醒进我的上下文，不拦
    ('G59临时改钩子路径', '命令', {'tool_input': {'command': 'git -c core.hooksPath=/dev/null commit -qm x'}}, 'K16', ['G59']),
    ('G59GIT环境变量', '命令', {'tool_input': {'command': 'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null git commit -qm x'}}, 'K16', ['G59']),
    ('G59删钩子', '命令', {'tool_input': {'command': 'rm -f .git/hooks/pre-commit 视频/工具/githooks/pre-commit'}}, 'K16', ['G59']),
    ('G60手写证据', '改文件', {'tool_input': {'file_path': '/home/user/postgraduate-vocabulary/视频/制作记录/证据/28.jsonl'}}, '【G60 证据闸门】', ['G60']),
    ('G61出稿会话改门程序', '改文件', {'tool_input': {'file_path': '/home/user/postgraduate-vocabulary/视频/工具/踩坑核查.py'}, '_角色': '出稿'}, '【G61 会话角色闸门】', ['G61']),
    ('G74推请求没约唤醒', '收工', {'_请求账': {'请求': [{'名字': '演练请求', '时刻': '2026-10-26T12:47:00Z'}]}}, '【K34 云端请求闸门】', ['G74']),
    ('G15heredoc里的字不误拦', '命令', {'tool_input': {'command': "cat > /tmp/演练.md <<'EOF'\ngit push -f origin master\nnpx vercel --prod\nEOF"}}, '', ['G15'], '放行'),
]


def 跑钩子(kind, payload):
    payload = dict(payload); 角色 = payload.pop('_角色', None); env = dict(os.environ)
    账 = payload.pop('_请求账', None)
    if 账 is not None:   # G74：在临时 HOME 里放一份请求账（推了请求、没约唤醒），从真实收工闸门入口跑
        h = tempfile.mkdtemp(prefix='演练_请求账_'); json.dump(账, open(f'{h}/.云端请求.json', 'w'), ensure_ascii=False); env['HOME'] = h
    if 角色:   # G61：在临时 HOME 里记一个会话角色，从真实闸门入口跑
        h = tempfile.mkdtemp(prefix='演练_角色_'); json.dump({'角色': 角色}, open(f'{h}/.会话开工.json', 'w')); env['HOME'] = h
    for f in payload.get('tool_input', {}).get('files', []):   # 闸门只查存在的文件：造一个没有回执的真文件
        if f.startswith('/tmp/演练_'): open(f, 'wb').write(os.urandom(64))
    r = subprocess.run(['python3', f'{T}/钩子/闸门.py', kind], input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True, timeout=60, env=env)
    return r.stdout + r.stderr


def 跑(entry, no, ws, 拆门=None):
    TA = _A镜像[0]   # A 类也从冻结镜像跑：踩坑核查、读音核对 读到的制作记录、文章都是冻结拷贝
    if entry == '出片':
        if 拆门:   # 演练自查：拆掉一道门（真实入口，其余不变）
            cmd = ['python3', '-c', f"import sys;sys.path.insert(0,{TA!r});import 破折号;破折号.查=lambda d,no=None:[];import 踩坑核查;sys.argv=['踩坑核查.py',{no!r},'出片'];sys.exit(踩坑核查.main())"]
        else: cmd = ['python3', f'{TA}/踩坑核查.py', no, '出片']
    else: cmd = ['python3', f'{TA}/读音核对.py', no]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ws, timeout=600)
    return r.returncode, set(l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip())


_A镜像 = [None]
def 演练(W, 只=None):
    root = os.path.dirname(os.path.abspath(W))
    _A镜像[0] = 镜像(f'{root}/演练_镜像_A', {}) + '/视频/工具'
    fix = json.load(open(f'{T}/发音词典/读音改正.json'))
    jobs, base = [], {}
    for sid, entry, no, how, fn, want, rules, *_ in 场景:
        if 只 and sid not in 只: continue
        d0 = json.loads(读样(f'视频/脚本/{no}.json'))   # 冻结拷贝，不读工作目录的现稿
        if (entry, no) not in base: base[(entry, no)] = 工作区(W, root, f'原样_{entry}_{no}', no, d0, fix if entry == '读音' else None)
        d = copy.deepcopy(d0)
        try:
            if fn: fn(d)
        except Exception as e: jobs.append((sid, None, f'样本找不到：{e}')); continue
        jobs.append((sid, 工作区(W, root, sid, no, d, {k: v for k, v in fix.items() if k != 'Inky'} if sid == 'A23Inky' else (fix if entry == '读音' else None)), None))
    jobs.append(('自查拆门', 工作区(W, root, '自查拆门', '24', (lambda d: (加中文(块(d, 1), '——'), d)[1])(json.loads(读样('视频/脚本/24.json')))), None))
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
        for sid, kind, payload, want, _, *mode in 钩子场景:
            if 只 and sid not in 只: continue
            o = 跑钩子(kind, payload); mode = mode[0] if mode else '拦'
            拦了 = '"deny"' in o or '"block"' in o   # G74：收工闸门（Stop）拦是 "block"，PreToolUse 拦是 "deny"
            ok = (want in o and 拦了) if mode == '拦' else (want in o and not 拦了)   # 提醒：要有提醒、不拦；放行：不许误拦
            if ok and mode != '拦': res.append((sid, True, ('提醒：' + want) if mode == '提醒' else '没有误拦')); continue
            res.append((sid, ok, ('拦下：' + want) if ok else f'没挡住：{o[:100]}'))
    res += 仓库演练(W, root, 只)
    if 镜.查样本(): res.append(('冻结样本没被改', False, '；'.join(镜.查样本())))   # 演练里的程序写穿了冻结拷贝：先修镜像
    for x in os.listdir(root):
        if x.startswith('演练_'): (os.unlink if os.path.islink(f'{root}/{x}') else lambda p: shutil.rmtree(p, ignore_errors=True))(f'{root}/{x}')
    return res


def 覆盖():
    """{规矩: 演练样本}：本程序的场景 + 出片守门自检（make_video 入口）的每一项"""
    cov = {}
    for sid, entry, no, how, fn, want, rules, *_ in 场景:
        for r in rules: cov.setdefault(r, []).append(f'执行效应演练 {sid}')
    for sid, kind, payload, want, rules, *_ in 钩子场景:
        for r in rules: cov.setdefault(r, []).append(f'执行效应演练 {sid}（钩子）')
    for sid, entry, no, how, fn, want, rules in 仓库场景:
        for r in rules: cov.setdefault(r, []).append(f'执行效应演练 {sid}（仓库镜像）')
    # 已有的真入口自检（规则执行核查每次当场跑）：在临时仓库/临时副本里真跑那支程序、造错必须停
    for prog, rs in {'推送自检.py（临时仓库真跑 推送两仓库.sh）': ['G1', 'G2', 'G3', 'G4', 'G11', '守则3', '流12', 'G16', 'G20', 'G5', 'G58', 'G67', 'G87', 'G88', 'G89', 'G98', 'G99', 'G100'],
                     '同步自检.py（临时副本真跑 sync_article.py）': ['S1', 'S3', 'S5'],
                     '用上核查.py --自检（K53：现行文档把已淘汰程序当命令写必报、历史记录不误报）': ['G103'],
                     '流程自检.py（K54：准备机器.sh 里 curl | tar 管道解压重放必报）': ['G104'],
                     '推请求.py --自检（K59/K60：乱序发、缺一步、彩排排前、不等收齐必拒，没全过或补丁改过不许收）+ 报坑.py --自检（会话 ID 自动填）+ 门变异.py --自检（受影响门）+ 执行效应声音演练.py --自检（分片合并）': ['G105', 'G106', 'G107'],
                     '执行效应声音演练 自查拆门_原样自检（K55：镜像里拆 audio_qc 削波门，原样稿必须报自检失灵）+ 原样自检 每场': ['A46'],
                     '会话开工.py --自检（K52：两个仓库读过的版本都算，都没读照停）': ['G102'],
                     '丝滑.py --自检（K56：自动登记没成功的不丝滑必列进未闭环；K57：改门会话不丝滑变差没写进化落地必报；K73：彩排停下数开工记录不算、不丝滑/内容问题/坏行都算）+ 方法进化表.py --自检（K58：改门会话上下文超 300k 必停）': ['G108', 'G109', 'G110', 'G121'],
                     '钩子/钩子自检.py（临时仓库真判 收工：已推过的 token 记录不拦、新的照拦）': ['G101'],
                     '会话开工.py --自检 + 开工必读.py --自检（O/N：第一屏三大主义、顺序）': ['G93'],
                     '用上核查.py --自检（P：临时工具目录真跑 完全不用/老做法冲突/重复）': ['G94'],
                     '规则执行核查 机器自检（python3.11 真编译造的嵌套引号 f-string）+ 彩排（3.11 全新容器）': ['G95'],
                     '报坑.py --自检（临时仓库真跑：镜像判定、K23 隔离）': ['G96'],
                     '推请求.py --自检（临时仓库真跑：补丁没提交随请求提交）': ['G97'],
                     '彩排.sh（GitHub 全新容器真跑 会话开工 → 流程自检 → 定稿流水线 25 到 ④，0 次停下才盖印章）': ['G92'],
                     '丝滑.py --自检 + 方法进化表.py --自检（K：分类、计数、五个入口接线；不丝滑变差要进化落地）': ['G91'],
                     '会话开工.py --自检（M：缺包装不上必停并说缺什么、缺包先自动装、包齐不误装；开工源码必先调 环境检查）': ['G90'],
                     '出片守门自检.py（隔离工作区真跑 make_video.py）': ['A44', 'A36'],
                     '出片指纹.py --自检（临时工具目录新加被 import 的模块必进清单、工作目录缺模块必停；定稿流水线、两个演练入口真跑 --核对工作目录）': ['G27'],
                     'check_all.py --自检（临时仓库真跑 查提醒/写提醒：原稿撞车词没写进制作记录必停、漏词必停、写了放行；踩坑核查 25 起每次跑 查提醒）': ['G34'],
                     'check_all.py --自检（N：T22 扩成的短语仍算原有、不当新加；短语拆实词比，短语对单词漏报必停）': ['G38'],
                     '踩坑核查.py 自检（G39：方法设计空模板必报、写全的不报；踩坑核查 NN 出片每次先跑自检）': ['G39'],
                     '开工记录.py --自检（临时仓库真跑 开工记录 和 check_all --写提醒：已有方法设计一字不变；改回先清空再读必报）': ['G46'],
                     '逐词对齐.py --自检（重放 26 S14 something rolling downhill 合组必停；踩坑核查 26 起每次调 逐词对齐.查）': ['G47'],
                     'check_all.py --自检（G48：短语对短语小品词不同不报 bring in↔bring back，hinge on↔hinged on 必报）': ['G48'],
                     '颜色核对.py --自检（重放 26 S10 珊瑚红↔琥珀黄相邻必停；出片程序、踩坑核查 25 起都调 同屏色差）': ['G49'],
                     '颜色核对.py --自检（G50：扫工具目录，自己算颜色不用共用分色的必停；造假抽屏必报）': ['G50'],
                     '结尾句接点.py --自检（--写入 用的同一个 合并()：写了前段增益dB 再跑接点，增益必须还在）': ['G31'],
                     '规则执行核查.py 重依赖自检（经本地模块顶层导入 scipy 必报、try 里和函数里不报；规则执行核查每次跑；旧版 机器复听.py 实测报出）': ['G44'],
                     '余音删法核对.py --自检（K27：27 S6 余音必留、停顿底噪照删；换回旧删法、拆掉调用必报；规则执行核查当场跑）': ['G69'],
                     '确认按位置迁移.py --自检（K28：27 S12 边上重叠 1 ms 必迁，整段在区间里、盖住短区间必不迁；规则执行核查当场跑）': ['G70'],
                     '机器复听.py --带自检（K25：吞这一句最长一段的中间七成，whisper 补不回；27、25 实测必报；交付核查 出片后每次跑）': ['G68'],
                     '推请求.py --自检（出片守门自检印章过期时带补丁的主演练必停；流程自检当场跑）': ['G76'],
                     '流程自检.py 有重建()（拿掉 ① 前 a.wav 重建那一行必报；规则执行核查当场跑）': ['G77'],
                     '流程自检.py 跑文本门()（定稿流水线 ④ 两行真跑：假 生成文本.py 失败必停、默认 --只核查；K37 原样那一行重放必抓；规则执行核查当场跑）': ['G78'],
                     '流程自检.py sh门真跑()（全部 .sh 每道门单独真跑必须停：拆掉的门、注释吞掉的门必报；门变异.py 拆门重跑；规则执行核查当场跑）': ['G79', '守则20'],
                     '踩坑核查.py 自检 record_meta_checks（28 没有“## 机制漏洞”、会话补空着或写“无”没依据必报；规则执行核查当场跑）': ['G79', '守则20'],
                     '流程自检.py yml中文变量()（工作流 export 中文名、$中文名必报；规则执行核查当场跑）': ['G80'],
                     '流程自检.py K38 重放（HOME 里放推了请求没约唤醒的账，钩子自检必须照样通过；规则执行核查当场跑）': ['G81'],
                     '门变异.py --自检 _并行()（K44：探测带演练的门一次只跑一道、不带的照常并行；规则执行核查当场跑）': ['G86'],
                     '推请求.py --自检 补丁打不上()（K43：工作分支上打不上的补丁必停、打得上不拦；流程自检当场跑）': ['G85'],
                     '流程自检.py drill写回()（K41：drill.yml 写回 put() 遇 409 不重试、artifact 名字带 / 必报，K41 原样重放；规则执行核查当场跑）': ['G84'],
                     '报坑.py --自检 自检_K29（镜像 origin 里原子写必停、主仓库不误报；规则执行核查当场跑）': ['G82'],
                     '用上核查.py --自检（新程序没登记、下线没用户原话必报；拆掉规则执行核查/改门锁/开工打印/门变异的接线必报；规则执行核查当场跑）': ['G83', '守则20'],
                     '机器复听.py --比较自检（27 S4 kilometres/kilometers、S14 40%/per cent 必须不报，漏词读错照报；规则执行核查当场跑）': ['G56'],
                     '结尾句接点.py --自检（27 S16：估的词尾晚 0.4 秒、吸气前有长静音，接点必须落在出片程序要删的那段里；规则执行核查当场跑）': ['G53'],
                     '速查表.py 自检 + check_all.py --自检 S4（速查表只有“本文：”必报；sync_article 用同一个判断，写完缺就停在定稿流水线 ④）': ['G52'],
                     '高亮同步核对.py --确认自检（25 起高亮确认的“开始读”落在音中间、静音里必拒；规则执行核查当场跑）': ['G45'],
                     '纯人声核对.py --确认自检（25 起像可闻吸气的非人声确认必拒、没有实测或实测对不上必拒；重放 25 S10；规则执行核查当场跑）': ['G43'],
                     '音频首要法则.py --自检（踩坑总表删一条音频坑必被发现、CLAUDE.md 第一条不是首要法则必停；规则执行核查每次核对 音频首要法则.md）': ['守则0'],
                     '停顿位置精确核对.py --自检 + 响度一致性核对.py --确认自检（25 起离后词为负没用插入点的停顿位置确认、超过 7.1 dB 的响度骤降确认必须不收；规则执行核查当场跑）': ['G40'],
                     '执行效应声音演练（结束核对两个仓库的配音缓存，留下就报；演练镜像 --自检 造坑）': ['G29']}.items():
        for r in rs: cov.setdefault(r, []).append(prog)
    cov.setdefault('守则19', []).append('执行效应演练 自查拆门（拆掉 T36 的门，演练必须报没挡住）')
    import 执行效应声音演练 as SY   # 声音演练（单独盖印章，声音核查程序一改就要重演）
    for sid, stage, how, fs, fw, want, rules, *_ in SY.声音场景:
        for r in rules: cov.setdefault(r, []).append(f'执行效应声音演练 {sid}（交付核查 {stage}）')
    sys.path.insert(0, T); import 出片守门自检 as G
    for c in G.CASES:
        if c[5] is not None: cov.setdefault(c[0], []).append(f'出片守门自检 {c[0]}')
    reg = json.load(open(f'{T}/规则执行表.json'))
    while True:   # “同”：同一道门，演练了那道门就演练了它（同 可以连着：法2 同 音34 同 A19）
        more = {k: [f'同 {o}' for o in v.get('同', []) if o in cov] for k, v in reg.items() if k not in cov and not k.startswith('_') and any(o in cov for o in v.get('同', []))}
        if not more: break
        cov.update(more)
    return cov


def 缺口():
    reg = json.load(open(f'{T}/规则执行表.json')); cov = 覆盖()
    return sorted(k for k in reg if not k.startswith('_') and k not in cov and not reg[k].get('演练说明'))


def 已说明():
    """造不出端到端样本、逐条写了原因和替代办法的规矩（规则执行表 “演练说明”: {原因, 替代}）：单独列出，不算悄悄留着"""
    reg = json.load(open(f'{T}/规则执行表.json')); cov = 覆盖()
    return sorted(k for k in reg if not k.startswith('_') and k not in cov and reg[k].get('演练说明'))


def 写缺口清单():
    reg = json.load(open(f'{T}/规则执行表.json')); g, e = 缺口(), 已说明()
    L = ['# 执行效应缺口清单（程序生成：python3 视频/工具/执行效应演练.py --缺口清单）', '',
         f'规矩 {len([k for k in reg if not k.startswith("_")])} 条；还没有端到端演练样本的 {len(g)} 条（基线 执行效应缺口基线.json，只许减少，目标 0）；'
         f'造不出端到端样本、已逐条说明原因和替代办法的 {len(e)} 条。', '', '## 还没有演练样本', '']
    L += [f'- {k}：{(reg[k].get("文") or "")[:40]}' for k in g] or ['（无）']
    L += ['', '## 造不出端到端样本（逐条原因 + 替代办法）', '']
    L += [f'- **{k}**：原因：{reg[k]["演练说明"]["原因"]}；替代：{reg[k]["演练说明"]["替代"]}' for k in e] or ['（无）']
    open(os.path.join(V, '制作记录', '执行效应缺口清单.md'), 'w').write('\n'.join(L) + '\n')


def 印章有效():
    try: st = json.load(open(STAMP))
    except Exception: return False
    import 同意记录追加 as TY   # 用户同意记录.json 不盖指纹，只许追加（主对话记用户原话不让印章失效）
    return all(st.get(x) == 指纹(f'{T}/{x}') for x in 被演练) and not TY.查(st=st.get('_同意记录前缀'))


def 状态():
    reg = json.load(open(f'{T}/规则执行表.json')); g = 缺口(); n = len([k for k in reg if not k.startswith('_')])
    ok = 印章有效(); e = 已说明()
    import 执行效应声音演练 as SY; sok = SY.印章有效()
    return (f'执行效应：{n - len(g) - len(e)} 条规矩有端到端演练样本、{len(g)} 条还没有（缺口基线只许减少）、{len(e)} 条造不出样本已逐条说明；最近一次演练'
            + ('全部挡住、印章有效' if ok else '【已过期或没通过：程序或规矩改过，在视频工作目录重跑 执行效应演练.py】')
            + ('；声音演练印章有效' if sok else '；【声音演练印章过期：在视频工作目录重跑 执行效应声音演练.py】'))


def main():
    a = sys.argv[1:]
    if '--状态' in a: print(状态()); return 0
    if '--缺口' in a: print(' '.join(缺口())); return 0
    if '--缺口清单' in a: 写缺口清单(); print(状态()); return 0
    W = os.getcwd()
    if not os.path.exists('make_video.py') or not os.path.isdir('scripts'): sys.exit('【停止】请在视频工作目录（含 make_video.py、scripts/）下运行')
    import 出片指纹 as _ZW   # G27：出片程序清单从 make_video 的 import 自动找全
    if _ZW.核对工作目录('.', T): sys.exit('【停止】' + '；'.join(_ZW.核对工作目录('.', T)) + '：先 python3 出片指纹.py --拷 . 再演练')
    e = 镜.查读现稿() + 镜.查样本()   # 演练只读冻结拷贝（改稿会话改现稿，演练不受影响）
    if e: sys.exit('【停止】' + '；'.join(e))
    if '--只过门' in a: print('演练开跑前的门：通过（只读冻结拷贝）'); return 0
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
    reg0 = json.load(open(f'{T}/规则执行表.json')); e = 已说明(); eb = json.load(open(GAPB)).get('已说明') if os.path.exists(GAPB) else None
    thin = [k for k in e if len(str(reg0[k]['演练说明'].get('原因', ''))) < 20 or len(str(reg0[k]['演练说明'].get('替代', ''))) < 20]
    if thin: bad.append(f'演练说明太空（原因、替代各至少 20 字）：{" ".join(thin)}')
    if eb is not None and len(e) > eb: bad.append(f'“造不出样本”变多（{len(e)} > 基线 {eb}）：新规矩要加演练场景，不许往说明里推')
    if bad or only:
        print('执行效应演练：' + ('【没通过：' + '、'.join(bad) + '】' if bad else '部分演练通过（只跑了一部分，不盖印章）')); return 1 if bad else 0
    reg = json.load(open(f'{T}/规则执行表.json')); cov = 覆盖()   # 规则执行表每条记“演练”样本（程序按场景自动写，不手填）
    for k, v in reg.items():
        if k.startswith('_'): continue
        if k in cov: v['演练'] = cov[k]
        else: v.pop('演练', None)
    json.dump(reg, open(f'{T}/规则执行表.json', 'w'), ensure_ascii=False, indent=1)
    import 同意记录追加 as TY; json.dump({**{x: 指纹(f'{T}/{x}') for x in 被演练}, '_同意记录前缀': TY.印(), '_挡住': [s for s, _, _ in res], '_有演练的规矩': len(cov)}, open(STAMP, 'w'), ensure_ascii=False, indent=1)
    if base is None or len(g) < base or eb is None or len(e) < eb:
        json.dump({'缺口': len(g), '已说明': len(e), '说明': '缺口 = 没有端到端演练样本的规矩条数；已说明 = 造不出样本、逐条写了原因和替代的条数；两个都只许减少，缺口目标 0'}, open(GAPB, 'w'), ensure_ascii=False, indent=1)
    print(f'执行效应演练：通过（{len(res)} 场演练全部挡在对的编号上，拆掉的门被发现；印章已写）'); return 0


if __name__ == '__main__':
    sys.exit(main())
