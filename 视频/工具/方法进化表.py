#!/usr/bin/env python3
"""方法进化表（G65）。用户 2026-10-26 原话：“我们一定一定要有一套非常非常非常非常非常非常完美的……从头到尾做视频的这个方法，而且要不断的进化和升级……
一定要采用虹吸效应，用最完美的方法，最高的效率最少的token做出最好最好，最好最好的视频……就我们的这个方法一定要不停的总结进化，总结进化，总结进化，直到绝对完美为止。”
“一定一定一定要就是不要浪费token……有的地方他用机器完完全全能起到甚至更好的效果，你在这个地方花token用人去做，反而就是浪费时间……”

数据：① 每个会话一份 制作记录/方法进化/<会话>.json（收工记录.py 每轮自动写：篇、角色、等效 token、调用、平均/最后上下文、按步骤花费、手工重复）；
      ② 以前的会话：NN.md “## token 记录”里没带会话号的收工行，按累计调用数掉下来切成一段段会话，每段取最后一行再相加（标“估”）。
用法（在哪个目录跑都行）：
  --写入        写 制作记录/方法进化表.md：每篇一行（所有会话加总）+ 趋势 + 按开工必读⑤步骤表的每步预计/实测 token
  --状态        一行趋势 + GitHub 工作流最近结果（开工提醒第一屏）
  --门 NN       NN 和前三篇中位数比，任何一项变差：NN.md “## 方法复盘”要有“进化落地：<提交号|G##|K##>”且查得到，没有就停
                （定稿流水线 ⓪、开工记录.py 开下一篇时调；程序先把对比和最费的三步写进 NN.md “## 方法进化”）
  --会话 NN|角色 从本会话记录写 方法进化/<会话>.json（收工记录.py 调）
  --上下文      本会话最后一次调用带的上下文；出稿、改稿会话超 40 万退出码 1（草稿声音.sh 开头调：先写交接，主会话开新改稿会话）
  --自检"""
import os, sys, re, json, glob, statistics, subprocess, datetime
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
REC = f'{V}/制作记录'; 会话目录 = [f'{REC}/方法进化']; OUT = f'{REC}/方法进化表.md'
起 = 27            # 门从 27 查（27 是本规矩立下后第一篇定稿的）
上下文限 = 400     # k：出稿、改稿会话超过就先交接（26 实测：调用到 500k 上下文时每次约 5.5 万等效，新会话约 2.3 万）
不全 = {'22': '只记到第一稿会话', '24': '只记到第一稿会话'}   # 主会话 2026-10-26 查：这两篇后来的会话没记收工行，不进比较基线
W = dict(input_tokens=1, cache_creation_input_tokens=1.25, cache_read_input_tokens=0.1, output_tokens=5)
项 = [('等效', 'M', '等效 token'), ('调用', '', '调用'), ('平均上下文', 'k', '平均上下文'), ('手工重复', '', '手工重复')]
_收工 = re.compile(r'^- (?:收工|进行中（每轮自动更新）) (\S+?)（UTC）：等效 ([\d.]+)M；主对话 (\d+) 次、平均 (\d+)k')


def 会话号():   # 本会话记录文件名就是会话号
    p = 本会话记录(); return os.path.basename(p)[:8] if p else '本机'


def 角色():
    try: return json.load(open(os.path.expanduser('~/.会话开工.json'))).get('角色', '')
    except Exception: return ''


def 本会话记录():
    fs = glob.glob('/root/.claude/projects/*/*.jsonl') + glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))
    return max(fs, key=os.path.getmtime) if fs else None


def 统计(path, 从=''):
    """一个会话记录 → 等效、调用、平均/最后上下文、按步骤（每次调用的花费记到它之前最后一个正式程序上）、手工重复（同一段内联脚本跑了两次以上）"""
    progs = {os.path.basename(x) for x in glob.glob(f'{T}/*.py') + glob.glob(f'{T}/*.sh') + glob.glob(f'{T}/*/*.py')}
    seen, 步, 内联 = set(), {}, {}; cur = '开工前'; n = ctx = last = e = 0
    for l in open(path, errors='ignore'):
        try: j = json.loads(l)
        except Exception: continue
        if 从 and (j.get('timestamp') or '') < 从: continue
        m = j.get('message') or {}
        if j.get('type') != 'assistant' or not isinstance(m, dict) or not m.get('usage'): continue
        if m.get('id') not in seen:   # 同一次调用的内容块分好几行记，用量只算一次，工具调用每行都看
            seen.add(m.get('id')); u = m['usage']; c = sum((u.get(k) or 0) * w for k, w in W.items())
            cx = sum(u.get(k) or 0 for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
            n += 1; ctx += cx; last = cx; e += c; 步[cur] = 步.get(cur, 0) + c
        for t in m.get('content') or []:
            if not (isinstance(t, dict) and t.get('type') == 'tool_use' and t.get('name') == 'Bash'): continue
            cmd = str((t.get('input') or {}).get('command', ''))
            ps = [x for x in re.findall(r'(?:python3|bash)\s+(?:-\S+\s+)*[^\s;|&]*?([\w一-鿿]+\.(?:py|sh))\b', cmd) if x in progs]
            if ps: cur = ps[-1]
            if re.search(r'python3\s+(-I\s+)?-c\b|python3\s+-\s*<<|<<\s*[\'"]?\w+', cmd):
                k = re.sub(r'\s+', ' ', re.sub(r'\d+', '#', cmd)).strip()[:160]; 内联[k] = 内联.get(k, 0) + 1
    return {'等效': round(e / 1e6, 2), '调用': n, '平均上下文': round(ctx / n / 1000) if n else 0, '最后上下文': round(last / 1000),
            '按步骤': {k: round(v / 1e6, 2) for k, v in sorted(步.items(), key=lambda x: -x[1])}, '手工重复': [[k[:80], c] for k, c in 内联.items() if c >= 2]}


def 写会话(篇, path=None, 从=''):
    path = path or 本会话记录()
    if not path: return None
    try: 角色 = json.load(open(os.path.expanduser('~/.会话开工.json'))).get('角色', '')
    except Exception: 角色 = ''
    d = {'会话': 会话号(), '篇': 篇, '角色': 角色, '更新': f'{datetime.datetime.utcnow():%Y-%m-%dT%H:%M}', **统计(path, 从)}
    os.makedirs(会话目录[0], exist_ok=True); json.dump(d, open(f'{会话目录[0]}/{d["会话"]}.json', 'w'), ensure_ascii=False, indent=1); return d


def 旧会话(txt):
    """NN.md 里没带会话号的收工行：累计调用数掉下来就是另一个会话；每段取最后一行"""
    节 = '\n'.join(m.group(0) for m in re.finditer(r'^## token 记录[^\n]*\n[\s\S]*?(?=^## |\Z)', txt, re.M))   # 有的篇有两节 token 记录
    seg, out, prev = None, [], -1
    for l in 节.splitlines():
        m = _收工.match(l)
        if not m or '｜会话 ' in l: continue
        r = {'等效': float(m.group(2)), '调用': int(m.group(3)), '平均上下文': int(m.group(4))}
        if seg and r['调用'] < prev: out.append(seg)
        seg, prev = r, r['调用']
    return out + ([seg] if seg else [])


def 汇总(rec=REC, 目录=None):
    篇 = {}
    for f in sorted(glob.glob(f'{rec}/[0-9][0-9].md')):
        no = os.path.basename(f)[:2]; txt = open(f).read(); ss = 旧会话(txt)
        篇[no] = {'会话': [dict(s, 估=True) for s in ss], '改稿条数': 0, '报坑': 0}
        q = f'{rec}/{no}_待改清单.md'
        if os.path.exists(q): 篇[no]['改稿条数'] = len(re.findall(r'^\d+\.', open(q).read(), re.M))
    for f in glob.glob(f'{目录 or 会话目录[0]}/*.json'):
        try: d = json.load(open(f))
        except Exception: continue
        if re.fullmatch(r'\d\d', str(d.get('篇', ''))): 篇.setdefault(d['篇'], {'会话': [], '改稿条数': 0, '报坑': 0})['会话'].append(d)
    try:
        for k in json.load(open(f'{rec}/坑登记.json')).get('登记', []):
            m = re.match(r'(\d\d)\s', k.get('现象', ''))
            if m and m.group(1) in 篇: 篇[m.group(1)]['报坑'] += 1
    except Exception: pass
    行 = {}
    for no, v in 篇.items():
        ss = v['会话']
        if not ss: continue
        c = sum(s['调用'] for s in ss); 新 = [s for s in ss if not s.get('估')]
        步 = {}
        for s in 新:
            for k, x in (s.get('按步骤') or {}).items(): 步[k] = round(步.get(k, 0) + x, 2)
        行[no] = {'等效': round(sum(s['等效'] for s in ss), 1), '调用': c, '平均上下文': round(sum(s['调用'] * s['平均上下文'] for s in ss) / c) if c else 0,
                 '会话数': len(ss), '估': any(s.get('估') for s in ss), '改稿条数': v['改稿条数'], '报坑': v['报坑'],
                 '手工重复': sum(len(s.get('手工重复') or []) for s in 新) if 新 else None, '按步骤': 步,
                 '超限会话': [s['会话'] for s in 新 if s.get('最后上下文', 0) > 上下文限]}
    return 行


def 基线(行, no):
    prev = [k for k in sorted(行) if k < no and k not in 不全][-3:]
    return prev, {k: (statistics.median([行[p][k] for p in prev if 行[p].get(k) is not None]) if any(行[p].get(k) is not None for p in prev) else None) for k, _, _ in 项}


def 落地查(txt, repos=None, 号=None):
    m = re.search(r'^## 方法复盘[^\n]*\n([\s\S]*?)(?=^## |\Z)', txt, re.M)
    hs = re.findall(r'进化落地[：:]\s*([^\n]+)', m.group(1)) if m else []
    if 号 is None:
        try: 号 = {k['号'] for k in json.load(open(f'{REC}/坑登记.json')).get('登记', [])} | set(json.load(open(f'{T}/规则执行表.json')))
        except Exception: 号 = set()
    ok = []
    for h in hs:
        for x in re.findall(r'\b([0-9a-f]{7,40}|[GK]\d+)\b', h):
            if x[0] in 'GK' and x in 号: ok.append(x)
            elif x[0] not in 'GK' and any(subprocess.run(['git', '-C', r, 'cat-file', '-e', x + '^{commit}'], capture_output=True).returncode == 0 for r in (repos or [P, '/home/user/literate-enigma']) if os.path.isdir(r)): ok.append(x)
    return ok


def 门(no, 行=None, txt=None, 写=True, repos=None, 号=None):
    """返回 (问题列表, 写进 NN.md 的“## 方法进化”节)"""
    行 = 汇总() if 行 is None else 行; f = f'{REC}/{no}.md'; txt = (open(f).read() if os.path.exists(f) else '') if txt is None else txt
    if int(no) < 起: return [], ''
    if no not in 行: return [f'【G65 方法进化】{no} 没有一条 token 记录（收工记录.py 每轮自动写；没有就是记录钩子没跑）'], ''
    prev, b = 基线(行, no); r = 行[no]
    差 = [(lab, r[k], b[k], u) for k, u, lab in 项 if r.get(k) is not None and b.get(k) is not None and r[k] > b[k]]
    top = '；'.join(f'{k} {v}M' for k, v in sorted(r['按步骤'].items(), key=lambda x: -x[1])[:3]) or '（这篇的会话没有按步骤记录）'
    节 = (f'## 方法进化（G65，程序写：本篇所有会话加总，和前三篇 {"、".join(prev)} 的中位数比）\n'
          + '- ' + '；'.join(f'{lab} {r[k]}{u}（中位 {b[k]}{u}）' for k, u, lab in 项 if r.get(k) is not None and b.get(k) is not None) + '\n'
          + f'- 最费的三步：{top}；手工重复 {r["手工重复"] if r["手工重复"] is not None else "—"}\n'
          + (f'- 变差：{"、".join(x[0] for x in 差)} → “## 方法复盘”写“进化落地：<提交号或 G##/K##>：改了什么”（已落成程序的改进）\n' if 差 else '- 没有变差\n'))
    if 写 and os.path.exists(f):
        t2 = re.sub(r'^## 方法进化（G65[^\n]*\n(?:- [^\n]*\n)*', '', txt, flags=re.M)
        a = t2.find('\n## 方法复盘'); t2 = (t2[:a + 1] + 节 + '\n' + t2[a + 1:]) if a >= 0 else t2.rstrip('\n') + '\n\n' + 节
        if t2 != txt: open(f, 'w').write(t2)
    if 差 and not 落地查(txt, repos, 号):
        return [f'【G65 方法进化】{no} 比前三篇中位数变差（{"；".join(f"{a} {x}{u} > {y}{u}" for a, x, y, u in 差)}），方法复盘里没有查得到的“进化落地：<提交号|G##|K##>”：'
                f'先把最费的地方（{top}）改成程序、提交，再写这一行'], 节
    return [], 节


def 写表(行=None):
    行 = 汇总() if 行 is None else 行; ks = sorted(行)
    L = ['# 方法进化表（G65，由 工具/方法进化表.py --写入 生成，不要手改）', '',
         '用户 2026-10-26：“这套方法一定要不停的去进化……越来越能够就是省token……在耗费token量最少的情况下，能够做出比消耗token还要完美……的视频”。'
         '每篇一行，所有会话（出稿、改稿、定稿）加总；“估”= 有老会话按收工行切段估算；手工重复 = 同一段内联脚本跑了两次以上（守则2：手工第二次就改成程序）。'
         f'从 {起} 起，定稿和开下一篇前和前三篇中位数比，任何一项变差就要“进化落地”。', '',
         '| 篇 | 等效 token | 调用 | 平均上下文 | 会话 | 用户改稿条数 | 报坑 | 手工重复 | 比前三篇中位 |', '|---|---|---|---|---|---|---|---|---|']
    for no in ks:
        r = 行[no]; prev, b = 基线(行, no)
        cmp = '；'.join(f'{lab}{"↑" if r[k] > b[k] else "↓"}' for k, _, lab in 项[:3] if b.get(k)) if prev else '—'
        L.append(f'| {no}{"（不全）" if no in 不全 else ""} | {r["等效"]}M{"（估）" if r["估"] else ""} | {r["调用"]} | {r["平均上下文"]}k | {r["会话数"]} | {r["改稿条数"]} | {r["报坑"]} | {"—" if r["手工重复"] is None else r["手工重复"]} | {cmp} |')
    L += ['', '## 每步预计/实测 token（同一张 开工必读 ⑤ 步骤表；实测 = 最近一篇有按步骤记录的会话，预计 = 最近三篇中位数）', '',
          '| 第几步 | 做什么 | 正式入口 | 在哪做 | 预计 | 实测 |', '|---|---|---|---|---|---|']
    try:
        sys.path.insert(0, T); import 开工必读 as K; rows = K.步骤表(reg=json.load(open(f'{T}/规则执行表.json')))
    except Exception: rows = []
    有步 = [no for no in ks if 行[no]['按步骤']]
    for i, (段, 做, cmd, 在, 证, g) in enumerate(rows, 1):
        p = cmd.split()[0] if cmd != '—' else ''
        xs = [行[no]['按步骤'].get(p) for no in 有步[-3:] if 行[no]['按步骤'].get(p)] if p else []
        L.append(f'| {i} | {做} | {cmd} | {在} | {str(round(statistics.median(xs), 2)) + "M" if xs else "—"} | {str(xs[-1]) + "M" if xs else "—"} |')
    open(OUT, 'w').write('\n'.join(L) + '\n'); return OUT


def 状态():
    行 = 汇总(); ks = [k for k in sorted(行) if k >= '21']
    s = ' → '.join(f'{k} {行[k]["等效"]}M{"*" if 行[k]["估"] else ""}' for k in ks)
    cur = ks[-1] if ks else None; prev, b = 基线(行, cur) if cur else ([], {})
    c = f'；{cur} 比前三篇中位 {b["等效"]}M {"变差↑" if 行[cur]["等效"] > b["等效"] else "变好↓"}' if cur and b.get('等效') else ''
    超 = [f'{k}:{"、".join(行[k]["超限会话"])}' for k in ks if 行[k]['超限会话']]
    print(f'【方法进化（G65）】等效 token：{s}{c}（*=含估算）；表：视频/制作记录/方法进化表.md' + (f'；上下文超 {上下文限}k 的会话：{" ".join(超)}' if 超 else ''))
    rs = []
    for f in glob.glob(f'{V}/云端/结果/*.结果.txt'):
        t = open(f).read(); ts = subprocess.run(['git', '-C', P, 'log', '-1', '--format=%cI', '--', f], capture_output=True, text=True).stdout.strip()
        g = lambda k: (re.search(rf'^{k} (\S+)', t, re.M) or [None, '?'])[1]
        rs.append((ts, os.path.basename(f).replace('.结果.txt', ''), g('运行'), g('退出码')))
    rs.sort(reverse=True)
    print('【GitHub 工作流最近结果】' + ('；'.join(f'{n} 运行 {r} 退出码 {c}（{t[5:16]}）' for t, n, r, c in rs[:3]) if rs else '视频/云端/结果/ 还没有回写'))


def 自检():
    import tempfile; f = []
    d = tempfile.mkdtemp(prefix='进化自检_'); os.makedirs(f'{d}/会话')
    L = lambda e, c, a, tag='': f'- 收工 2026-10-2xT00:00（UTC）：等效 {e}M；主对话 {c} 次、平均 {a}k （子代理共 0 个记录文件）{tag}'
    t = '## token 记录\n' + '\n'.join([L(1, 10, 100), L(2, 20, 100), L(1, 5, 200), L(9, 99, 300, '｜会话 x')]) + '\n## 方法复盘\n'
    ss = 旧会话(t)
    if [s['等效'] for s in ss] != [2, 1]: f.append(f'没抓到：老会话按累计调用切段（应 [2,1]，得 {[s["等效"] for s in ss]}）')
    for no, e in (('24', 1), ('25', 2), ('26', 3)): open(f'{d}/{no}.md', 'w').write('## token 记录\n' + L(e, 10, 100) + '\n## 方法复盘\n')
    open(f'{d}/27.md', 'w').write('## token 记录\n' + L(9, 10, 100) + '\n## 方法复盘\n')
    行 = 汇总(d, f'{d}/会话')
    if 行.get('27', {}).get('等效') != 9: f.append('汇总没把 27 算成 9M')
    e, _ = 门('27', 行, open(f'{d}/27.md').read(), 写=False, repos=[], 号=set())
    if not e: f.append('没抓到：27 比前三篇中位数贵三倍、没写进化落地')
    e, _ = 门('27', 行, open(f'{d}/27.md').read() + '- 进化落地：deadbee 假提交\n', 写=False, repos=[d], 号=set())
    if not e: f.append('没抓到：进化落地写的提交号查不到')
    e, _ = 门('27', 行, open(f'{d}/27.md').read() + '- 进化落地：G63 会话开工\n', 写=False, repos=[], 号={'G63'})
    if e: f.append('误停：进化落地写了查得到的 G63 还停')
    行['27']['等效'] = 1; 行['27']['手工重复'] = None
    e, _ = 门('27', 行, open(f'{d}/27.md').read(), 写=False, repos=[], 号=set())
    if e: f.append('误停：27 比中位数便宜也停')
    lg = f'{d}/log.jsonl'
    with open(lg, 'w') as o:
        for i, (cmd, cx) in enumerate([('python3 -c "print(1)"', 100000), ('bash 草稿声音.sh 27', 200000), ('python3 -c "print(2)"', 500000)]):
            o.write(json.dumps({'type': 'assistant', 'timestamp': '2026', 'message': {'id': str(i), 'usage': {'cache_read_input_tokens': cx, 'output_tokens': 100},
                                'content': [{'type': 'tool_use', 'name': 'Bash', 'input': {'command': cmd}}]}}) + '\n')
    s = 统计(lg)
    if len(s['手工重复']) != 1: f.append('没抓到：同一段内联脚本跑了两次（手工重复）')
    if s['最后上下文'] != 500 or '草稿声音.sh' not in s['按步骤']: f.append('统计错：最后上下文或按步骤')
    if 上下文超(s, '改稿') is None: f.append('没抓到：改稿会话上下文 500k 超限')
    if 上下文超(s, '改门') is not None: f.append('误停：改门会话不按改稿的上下文限挡')
    return ['方法进化表 自检：' + x for x in f]


def 上下文超(s, 角色):
    if 角色 in ('出稿', '改稿') and s['最后上下文'] > 上下文限:
        return (f'【停止】本会话上下文已 {s["最后上下文"]}k（超 {上下文限}k，G65）：每次调用都要把整段上下文重读一遍，再改下去越改越贵。'
                f'先把现状和待改清单写进 制作记录/NN.md，推送，报主会话开新改稿会话接着做（用户在新会话里接着看片）')
    return None


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--自检' in a:
        e = 自检(); print('\n'.join(e) or '方法进化表 自检通过（老会话切段、变差没落地必停、假提交号必停、落地查得到放行、手工重复、改稿上下文超限）'); sys.exit(1 if e else 0)
    if '--会话' in a: d = 写会话(a[a.index('--会话') + 1], 从=a[a.index('--从') + 1] if '--从' in a else ''); print(f'会话记录：{d and d["等效"]}M'); sys.exit(0)
    if '--上下文' in a:
        p = 本会话记录()
        if not p: print('没有会话记录（GitHub 或演练里跑），不查上下文'); sys.exit(0)
        try: 角色 = json.load(open(os.path.expanduser('~/.会话开工.json'))).get('角色', '')
        except Exception: 角色 = ''
        s = 统计(p); m = 上下文超(s, 角色); print(m or f'本会话上下文 {s["最后上下文"]}k（限 {上下文限}k）'); sys.exit(1 if m else 0)
    if '--门' in a:
        no = a[a.index('--门') + 1].zfill(2); e, 节 = 门(no); print('\n'.join(e) or f'方法进化 {no}：通过')
        if not e and int(no) >= 起: import 证据 as _ZJ; _ZJ.记(no, '方法进化', 详情={'进化表行': 节.splitlines()[1][2:] if 节 else ''})   # G60：使用证据
        sys.exit(1 if e else 0)
    if '--状态' in a: 状态(); sys.exit(0)
    if '--写入' in a: print('已写', 写表()); sys.exit(0)
    print(__doc__)
