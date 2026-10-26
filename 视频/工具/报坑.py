#!/usr/bin/env python3
"""报坑登记 + 取号（G54，用户 2026-10-26：“只要踩过这些坑，以后全部都要记录到这个踩坑指南里面……我们不是有这么一个机制吗？
就把这些所有踩过的坑加入到那个机制里面去”）。不另建机制：这里只是入口，坑一律进 踩坑总表 → 规则执行核查 → 执行效应演练。

  报坑：python3 报坑.py "27 S16 现象（实测）" [--会话 ID]   → 当场原子写进远端 视频/制作记录/坑登记.json，打印登记号 K#
  取号：python3 报坑.py --取号 G [--登记 K#] [--会话 ID] [--用途 说明]
        → 原子取号：读远端+本地的总表、预留，取最大号+1，只把这一条预留提交推到远端 main，推不上（别人刚取）就重取
  关门：总表里写出这条登记的入表编号那一行，登记就算已入表（不用手改状态）。
  查：  python3 报坑.py --查 [--严]   （规则执行核查每次跑：撞号、总表新行没取号就停；超期没入表的只提示。
        --严 = 定稿流水线 ⓪、推送两仓库改门程序时：超期没入表就停）
      python3 报坑.py --状态 / --自检
超期：登记后 24 小时没进总表；写明“改门会话”的宽限 72 小时。"""
import os, re, sys, json, subprocess, tempfile, datetime
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
REL = '视频/制作记录/坑登记.json'; STDREL = '视频/制作硬性标准与踩坑总结.md'
宽限 = {'普通': 24, '改门': 72}


def 现在(): return datetime.datetime.now(datetime.timezone.utc)
def 时刻(t=None): return (t or 现在()).strftime('%Y-%m-%dT%H:%MZ')
def 解时(s): return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%MZ').replace(tzinfo=datetime.timezone.utc)
def 空(): return {'说明': '报坑登记（G54）：入口在 工具/报坑.py；每条登记都要进踩坑总表（入表编号那一行写出来就算关门）', '起': {}, '登记': [], '预留': []}


def 总表编号(std):
    return [m.group(1) for m in re.finditer(r'^\| *([A-Z]\d+b?) *\|', std, re.M)]


def 号(x): m = re.match(r'([A-Z])(\d+)', x); return m.group(1), int(m.group(2))


def 自检残留(r): return r.get('用途') == '自检' or r.get('会话') in ('会话A', '会话B', '会话C') or str(r.get('现象', '')).startswith('自检造的')


def 判(std, d, now=None):
    """纯函数（自检用）：返回 (硬问题, 超期, 待入表)。硬问题 = 撞号、总表新行没取号；超期 = 过了宽限还没进总表"""
    now = now or 现在(); rows = 总表编号(std); hard, late, wait = [], [], []
    rs = [r['编号'] for r in d.get('预留', [])]
    for x in sorted({r for r in rs if rs.count(r) > 1}): hard.append(f'预留编号撞号：{x} 被取了两次（G54：取号要原子，推不上就重取）')
    for x in sorted({r for r in rows if rows.count(r) > 1}): hard.append(f'踩坑总表编号重复：{x}')
    for r in d.get('预留', []) + d.get('登记', []):   # K23：自检造的预留、登记跑进了真登记（自检推到了真远端）
        if 自检残留(r): hard.append(f'坑登记里有自检造的 {r.get("编号") or r.get("号")}（K23：自检推到了真远端）：python3 视频/工具/报坑.py --清自检')
    起 = d.get('起', {})
    for x in rows:
        p, n = 号(x)
        if p in 起 and n >= 起[p] and x not in rs:
            hard.append(f'总表 {x} 没有取号（G54：新坑编号一律 python3 视频/工具/报坑.py --取号 {p}，防几个会话同时写撞号）')
    for r in d.get('登记', []):
        if r.get('入表编号') in rows: continue
        h = (now - 解时(r['时刻'])).total_seconds() / 3600
        lim = 宽限['改门' if r.get('改门会话') else '普通']
        s = f'{r["号"]}（{r["时刻"]}，{r.get("会话", "")[-8:]}）{r["现象"][:50]}'
        (late if h > lim else wait).append(s + (f'：已 {h:.0f} 小时没进踩坑总表（宽限 {lim} 小时）' if h > lim else ''))
    return hard, late, wait


def 读本地():
    f = f'{P}/{REL}'
    return json.load(open(f)) if os.path.exists(f) else 空()


def git(*a, repo=None, inp=None, env=None):
    base = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}   # K23：提交前钩子里 git 导出 GIT_DIR/GIT_INDEX_FILE，继承了 -C 也落到真仓库
    r = subprocess.run(['git', '-C', repo or P, *a], capture_output=True, text=True, input=inp, env={**base, **(env or {})})
    return r.returncode, r.stdout


def 隔离查(repo, root):
    """K23：自检用的仓库和它的 origin 必须都在自检的临时目录里，否则不推（2026-10-26 自检造的坑被推到了真远端 main）"""
    rr = os.path.realpath(root) + os.sep; e = []
    c, gd = git('rev-parse', '--absolute-git-dir', repo=repo)
    if c or not os.path.realpath(gd.strip()).startswith(rr): e.append(f'仓库 {gd.strip()} 不在 {root} 里')
    c, url = git('remote', 'get-url', 'origin', repo=repo)
    if c or '://' in url or not os.path.realpath(url.strip()).startswith(rr): e.append(f'origin {url.strip()} 不在 {root} 里')
    return e


def 原子写(改, repo=None, 分支='main', 说明='报坑登记'):
    """把 改(远端坑登记) 的结果作为只改这一个文件的提交推到远端；别人刚推了就重读远端再来（这就是防撞号）"""
    if repo and os.path.realpath(repo) != os.path.realpath(P):   # 自检等指定了别的仓库：只许推它自己目录里的假远端
        e = 隔离查(repo, os.path.dirname(repo))
        if e: raise SystemExit('【停止】自检指向真 origin（K23）：' + '；'.join(e))
    repo = repo or P
    for k in range(8):
        git('fetch', '-q', 'origin', 分支, repo=repo)
        c, base = git('rev-parse', f'origin/{分支}', repo=repo); base = base.strip()
        c, txt = git('show', f'{base}:{REL}', repo=repo)
        d = json.loads(txt) if c == 0 else 空()
        c, std = git('show', f'{base}:{STDREL}', repo=repo)
        out, ret = 改(d, std if c == 0 else '')
        idx = tempfile.mktemp(); e = {'GIT_INDEX_FILE': idx}
        git('read-tree', base, repo=repo, env=e)
        c, blob = git('hash-object', '-w', '--stdin', repo=repo, inp=json.dumps(out, ensure_ascii=False, indent=1) + '\n')
        git('update-index', '--add', '--cacheinfo', f'100644,{blob.strip()},{REL}', repo=repo, env=e)
        c, tree = git('write-tree', repo=repo, env=e); os.remove(idx)
        c, cm = git('commit-tree', tree.strip(), '-p', base, '-m', 说明 + '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>', repo=repo,
                    env={'GIT_AUTHOR_NAME': 'Claude', 'GIT_AUTHOR_EMAIL': 'noreply@anthropic.com', 'GIT_COMMITTER_NAME': 'Claude', 'GIT_COMMITTER_EMAIL': 'noreply@anthropic.com'})
        if git('push', '-q', 'origin', f'{cm.strip()}:refs/heads/{分支}', repo=repo)[0] == 0:
            git('fetch', '-q', 'origin', 分支, repo=repo)
            f = f'{repo}/{REL}'; os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, 'w').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n'); git('add', REL, repo=repo)   # 本地暂存同一内容：之后推送两仓库合并时两边相同、不冲突
            return ret
    raise SystemExit('【停止】推了 8 次都被别人抢先（网络或远端有问题），没有取到号；不许自己编号')


def 并本地(d, loc):
    """远端为准，补上本地有、远端没有的登记（只追加）"""
    have = {r['号'] for r in d['登记']}
    d['登记'] += [r for r in loc.get('登记', []) if r['号'] not in have]
    hv = {(r['编号'], r.get('会话')) for r in d['预留']}; d['预留'] += [r for r in loc.get('预留', []) if (r['编号'], r.get('会话')) not in hv]
    for k, v in loc.get('起', {}).items(): d.setdefault('起', {}).setdefault(k, v)
    return d


def 报(现象, 会话, repo=None):
    loc = 读本地() if repo is None else 空()
    def 改(d, std):
        d = 并本地(d, loc); n = max([int(r['号'][1:]) for r in d['登记']] + [0]) + 1
        d['登记'].append({'号': f'K{n}', '时刻': 时刻(), '会话': 会话, '现象': 现象}); return d, f'K{n}'
    return 原子写(改, repo, 说明=f'报坑登记：{现象[:30]}')


def 取(前缀, 会话, 用途='', 登记号=None, repo=None):
    loc = 读本地() if repo is None else 空()
    lstd = open(f'{repo or P}/{STDREL}').read() if os.path.exists(f'{repo or P}/{STDREL}') else ''
    def 改(d, std):
        d = 并本地(d, loc)
        ns = [号(x)[1] for x in 总表编号(std) + 总表编号(lstd) + [r['编号'] for r in d['预留']] if 号(x)[0] == 前缀]
        x = f'{前缀}{max(ns + [0]) + 1}'
        d['预留'].append({'编号': x, '会话': 会话, '时刻': 时刻(), '用途': 用途})
        for r in d['登记']:
            if r['号'] == 登记号: r['入表编号'] = x
        return d, x
    return 原子写(改, repo, 说明=f'取号：{前缀}（{用途[:30]}）')


def 自检():
    fails = []; now = 解时('2026-10-27T12:00Z')
    std = '| G52 | a | b | c |\n| G53 | a | b | c |\n| A45 | a | b | c |\n'
    d = {'起': {'G': 53}, '预留': [{'编号': 'G53'}], '登记': [
        {'号': 'K1', '时刻': '2026-10-26T06:00Z', '现象': '已入表的', '入表编号': 'G53'},
        {'号': 'K2', '时刻': '2026-10-27T06:00Z', '现象': '刚登记的'},
        {'号': 'K3', '时刻': '2026-10-25T06:00Z', '现象': '改门中的', '改门会话': 'session_x'}]}
    h, l, w = 判(std, d, now)
    if h or l: fails.append(f'原样误报：{h + l}')
    if not any('K2' in x for x in w): fails.append('没列出待入表的登记')
    d1 = json.loads(json.dumps(d)); d1['登记'].append({'号': 'K4', '时刻': '2026-10-26T06:00Z', '现象': '自检造的超期没入表'})
    if not any('K4' in x for x in 判(std, d1, now)[1]): fails.append('没抓到：登记超过 24 小时没进总表')
    d2 = json.loads(json.dumps(d)); d2['登记'][2]['时刻'] = '2026-10-23T06:00Z'
    if not any('K3' in x for x in 判(std, d2, now)[1]): fails.append('没抓到：改门中超过 72 小时')
    if not any('G54 没有取号' in x for x in 判(std + '| G54 | 自检造的没取号 | b | c |\n', d, now)[0]): fails.append('没抓到：总表新行没取号')
    d4 = json.loads(json.dumps(d)); d4['预留'].append({'编号': 'G54', '会话': '会话A', '用途': '自检'})
    if not any('自检造的' in x for x in 判(std, d4, now)[0]): fails.append('没抓到：自检造的预留进了真登记（K23）')
    d3 = json.loads(json.dumps(d)); d3['预留'].append({'编号': 'G53'})
    if not any('撞号' in x for x in 判(std, d3, now)[0]): fails.append('没抓到：预留撞号')
    if not any('重复' in x for x in 判(std + '| G53 | x | y | z |\n', d, now)[0]): fails.append('没抓到：总表编号重复')
    # 真跑取号：本地假远端，A 取号后 B（本地是旧的）再取，必须拿到下一个号，不许撞
    tmp = tempfile.mkdtemp(); _env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}; sh = lambda c: subprocess.run(c, shell=True, cwd=tmp, capture_output=True, env=_env)
    sh('git init -q --bare r.git && git clone -q r.git a && git clone -q r.git b')
    for who in ('a',):
        os.makedirs(f'{tmp}/{who}/视频/制作记录'); open(f'{tmp}/{who}/{STDREL}', 'w').write(std)
        json.dump({**空(), '起': {'G': 53}, '预留': [{'编号': 'G53'}]}, open(f'{tmp}/{who}/{REL}', 'w'))
        sh(f'cd {who} && git add -A && git -c user.name=x -c user.email=x@x commit -qm i && git push -q origin HEAD:main')
    sh('cd b && git pull -q origin main')
    sh('git clone -q r.git c && git -C c remote set-url origin ' + P)   # 造坑：自检仓库的 origin 指向真仓库，必须不推就停
    try: 取('G', '会话C', '自检', repo=f'{tmp}/c'); fails.append('没抓到：自检指向真 origin 照样取号推送（K23）')
    except SystemExit as e:
        if '自检指向真 origin' not in str(e): fails.append(f'自检指向真 origin 停的理由不对：{e}')
    iso = 隔离查(f'{tmp}/a', tmp)
    if iso: fails.append('自检指向真 origin（K23）：' + '；'.join(iso)); subprocess.run(['rm', '-rf', tmp]); return fails
    try:
        x1 = 取('G', '会话A', '自检', repo=f'{tmp}/a'); x2 = 取('G', '会话B', '自检', repo=f'{tmp}/b')
        k1 = 报('自检造的坑', '会话B', repo=f'{tmp}/b'); k2 = 报('自检造的坑2', '会话A', repo=f'{tmp}/a')
        if (x1, x2) != ('G54', 'G55'): fails.append(f'没抓到：两个会话先后取号撞号（拿到 {x1} {x2}）')
        if (k1, k2) != ('K1', 'K2'): fails.append(f'两个会话先后报坑登记号撞了（{k1} {k2}）')
    except SystemExit as e: fails.append(f'取号真跑失败：{e}')
    subprocess.run(['rm', '-rf', tmp])
    return fails


def main():
    a = sys.argv[1:]
    def opt(k, dft=''):
        return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else dft
    会话 = opt('--会话', '（没写会话：报坑时加 --会话 session_…）')
    if '--自检' in a:
        f = 自检(); print('报坑登记自检：' + ('通过（超期没入表、改门超 72 小时、总表新行没取号、预留撞号、总表重号都抓到；两个会话先后取号不撞）' if not f else '失灵！' + '；'.join(f)))
        return 1 if f else 0
    if '--清自检' in a:   # K23：原子清掉真登记里的自检残留（只改坑登记这一个文件）
        n = [0]
        def 改(d, std):
            for k in ('预留', '登记'):
                keep = [r for r in d.get(k, []) if not 自检残留(r)]; n[0] += len(d.get(k, [])) - len(keep); d[k] = keep
            return d, n[0]
        原子写(改, 说明='报坑登记：清掉自检推到真远端的预留和登记（K23）'); print(f'清掉自检残留 {n[0]} 条'); return 0
    if '--取号' in a:
        x = 取(opt('--取号'), 会话, opt('--用途'), opt('--登记') or None); print(f'取号：{x}（已推到远端预留；总表这一行写 {x}）'); return 0
    if '--查' in a or '--状态' in a:
        d = 读本地(); h, l, w = 判(open(f'{P}/{STDREL}').read(), d)
        if '--状态' in a:
            print(f'【报坑登记】待入表 {len(w)} 条、超期 {len(l)} 条' + ('：' + '；'.join(l + w)[:300] if l or w else '') + ('；问题：' + '；'.join(h) if h else '')); return 0
        for x in w: print('  提示（待入表，G54）：', x)
        for x in h + (l if '--严' in a else []): print('  ✘', x)
        if not ('--严' in a) and l:
            for x in l: print('  提示（超期，定稿流水线和推门程序会停）：', x)
        return 1 if h or ('--严' in a and l) else 0
    if a and not a[0].startswith('--'):
        k = 报(a[0], 会话); print(f'登记号：{k}（报主会话时附上；坑写进总表时 python3 视频/工具/报坑.py --取号 <字头> --登记 {k}）'); return 0
    print(__doc__); return 1


if __name__ == '__main__':
    sys.exit(main())
