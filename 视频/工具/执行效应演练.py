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
被演练 = ['踩坑核查.py', '译文核查.py', '破折号.py', 'check_all.py', '读音核对.py', 'make_video.py', 'render.py', '执行效应演练.py', '规则执行表.json', '放行口子核查.py', '放行口子表.json', '用户同意记录.json']
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
    ('A23Inky', '读音', '07', '重放 07 Inky 读成 ink-EYE：读音改正表去掉 Inky', None, 'Inky', ['A23', '守则6']),
]


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
    for sid, entry, no, how, fn, want, rules in 场景:
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
            c, o = 跑(entry, no, ws); new = o - bo[(entry, no)][1]
            hit = [l for l in new if want in l]
            ok = c != 0 and bool(hit)
            return sid, ok, (hit[0][:90] if hit else f'没挡住（退出码 {c}，新报出 {len(new)} 行：{"；".join(sorted(new))[:120]}）')
        res = list(ex.map(one, jobs))
    for x in os.listdir(root):
        if x.startswith('演练_'): shutil.rmtree(f'{root}/{x}', ignore_errors=True)
    return res


def 覆盖():
    """{规矩: 演练样本}：本程序的场景 + 出片守门自检（make_video 入口）的每一项"""
    cov = {}
    for sid, entry, no, how, fn, want, rules in 场景:
        for r in rules: cov.setdefault(r, []).append(f'执行效应演练 {sid}')
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
