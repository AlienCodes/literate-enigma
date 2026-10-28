#!/usr/bin/env python3
"""推 GitHub 工作流请求的正式入口（K34/G74，2026-10-26）：在镜像工作分支新建 视频/云端/请求/<名字>.txt、提交、推送，
记进本机请求账（~/.云端请求.json），并提醒：GitHub 写回结果不会唤醒会话，推完必须 send_later 约 20 分钟叫回自己；
没约唤醒，收工闸门（钩子/闸门.py 收工）就拦。格式见 视频/云端/请求/说明.md。
用法：python3 视频/工具/推请求.py <名字> "<任务行>" ["# 注释"]    例：推请求.py G72主演练 "主演练 补丁=视频/云端/待演练/G72单线程.diff"
改门推送（K59/K60）：python3 视频/工具/推请求.py <名字> 改门推送
  —— 把主仓库这次的改动做成补丁 视频/云端/待演练/<名字>.diff，GitHub 一条请求按 门变异 → 主演练+声音演练 → 彩排 走完，全过把印章写回；
  回来后 python3 视频/工具/推请求.py --收 <名字> "提交说明"：核对全过、补丁没变，打上结果补丁，推送两仓库。印章不再手排。"""
import os, sys, json, subprocess, datetime, re, tempfile, shutil
L = '/home/user/literate-enigma'; B = 'claude/adoring-hamilton-5qskmm'
账 = os.path.expanduser('~/.云端请求.json')
def g(*a): return subprocess.run(['git', '-C', L, *a], capture_output=True, text=True)
def 本地慢印章(行, 有效=None, 缺口数=None):
    """K35：带补丁的 主演练 只在 GitHub 跑主演练；本地才跑的慢自检（出片守门自检）印章不在补丁里，GitHub 上每场都先撞“印章对不上”，白跑一轮。
    推之前查本仓库工作树：本地慢自检印章过期就停（先在视频工作目录跑它、再重做补丁）"""
    if not any(x in 行 for x in ('主演练', '改门推送')) or '补丁=' not in 行: return ''
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 规则执行核查 as R
    有效 = 有效 or R.印章有效
    bad = [p for p in R.STAMPED if p not in ('执行效应演练.py', '执行效应声音演练.py', '彩排.sh') and not 有效(p)]   # 演练印章本身就是这次请求要盖的；彩排印章也只在 GitHub 上盖，而彩排要先有主演练印章（K60：两头互等，死锁）
    if bad: return f'本地慢自检印章过期：{bad}（K35：先在视频工作目录跑 python3 视频/工具/{bad[0]}，通过后重做补丁再推主演练）'
    import 执行效应演练 as Y   # 2026-10-26 K37v2：新规矩没登记演练覆盖，GitHub 主演练报“缺口变多”白跑一轮；本地几秒就查得出
    g = 缺口数 if 缺口数 is not None else len(Y.缺口()); b = json.load(open(Y.GAPB))['缺口'] if os.path.exists(Y.GAPB) else 0
    return f'执行效应演练缺口 {g} 条 > 基线 {b}：新规矩先在 执行效应演练.py 登记演练（python3 视频/工具/执行效应演练.py --状态 看），再做补丁推主演练' if g > b else ''
def 补丁打不上(行, repo=L):
    """K43：镜像工作分支被主会话同步过，旧补丁打不上，GitHub 上全部 job 两分钟就挂。推之前在拉过的工作分支上 git apply --check"""
    m = re.search(r'补丁=(\S+)', 行)
    if not m: return ''
    p = m.group(1); r = subprocess.run(['git', '-C', repo, 'apply', '--check', p], capture_output=True, text=True)
    return '' if r.returncode == 0 else f'补丁 {p} 在工作分支上打不上（K43：主仓库更新过，先合并最新 main 再重做补丁）：{(r.stderr or r.stdout).strip()[-150:]}'
def 待提交补丁(行, repo=L):
    """K50：补丁文件没提交（新文件或改过），GitHub 上打补丁找不到/打的是旧版：随请求一起提交"""
    m = re.search(r'补丁=(\S+)', 行)
    if not m: return []
    r = subprocess.run(['git', '-C', repo, 'status', '--porcelain', '--', m.group(1)], capture_output=True, text=True).stdout.strip()
    return [m.group(1)] if r else []
P = '/home/user/postgraduate-vocabulary'; 工作流 = f'{L}/.github/workflows/drill.yml'
def 定稿前提(行, 跑=None):
    """阶段 B：定稿 NN 发到 GitHub 前，本地先过 ⓪ 里两道人和证据的门（用户原话“定稿 NN”、证据链），不过就不发，不白跑一台机器"""
    w = 行.split()
    if w[:1] != ['定稿']: return ''
    跑 = 跑 or (lambda c: subprocess.run(['python3', f'{os.path.dirname(os.path.abspath(__file__))}/{c[0]}', *c[1:]], capture_output=True, text=True).returncode)
    for n in [x for x in w[1:] if re.fullmatch(r'\d\d', x)] or ['?']:
        if n == '?': return '定稿请求要写篇号（定稿 NN）'
        if 跑(['放行口子核查.py', '--定稿', n]): return f'用户还没说定稿 {n}（用户同意记录.json 没有原话，画19/流7）：不发'
        if 跑(['证据.py', '--查', n, '定稿']): return f'第 {n} 篇草稿的机制证据不全（G60）：不发'
    return ''
尾分 = 35   # 门变异合并以后：主演练 + 两个印章 + 彩排，约几分钟（v5/v6 实测粗估）
def 估时提示(e):
    """交接 ③：改门推送发前估时。e = 门变异.py --估时 的结果；墙钟 = 门变异（总机器分钟 ÷ 20 + 最慢片，声音 4 片同时跑）+ 尾分。超 60 分钟先报"""
    w = e['墙钟'] + 尾分; s = f"估时：门变异 {e['片']} 片、{e['机器分钟']} 机器分钟，墙钟约 {w} 分钟（门变异 {e['墙钟']} + 演练彩排 {尾分}；最慢 {e['最慢'][0]} 约 {e['最慢'][1]} 分钟）"
    return ('【估时超 60 分钟，先报主会话】' + s) if w > 60 else s
def 补丁行(rel, 行):
    return ' '.join([f'改门推送 补丁={rel}'] + 行.split()[1:])   # 第五棒：快跑=… 跟着走（原来只剩 补丁=，快跑悄悄变全量）
def 乱序(行):
    """K59/K60：带补丁的 彩排、主演练、声音演练 单独发就是手排印章（彩排先跑白跑、印章互等死锁）：一律走 改门推送"""
    w = 行.split()
    return f'“{w[0]} 补丁=…”不许单独发（K59/K60：门变异、演练、彩排的顺序只认 改门推送 一条命令）：python3 视频/工具/推请求.py <名字> 改门推送' if w and w[0] in ('彩排', '主演练', '声音演练') and any(x.startswith('补丁=') for x in w) else ''
def _段(t, name):
    i = t.find(f'\n  {name}:\n')   # 带换行：defaults 下面的 “run: {shell: bash}” 不算 run 这一步
    if i < 0: return ''
    m = re.search(r'\n  [A-Za-z_]+:\n', t[i + 1:])
    return t[i:i + 1 + m.start()] if m else t[i:]
def _有序(g, seq):
    pos = [g.find(x) for x in seq]
    return min(pos) >= 0 and pos == sorted(pos), [x for x, p_ in zip(seq, pos) if p_ < 0]
def 排序问题(t):
    """drill.yml 的 改门推送 链（K59/K60）：plan 发门变异分片 + 声音演练 4 片（⓪′ 在 run 里同时跑）→ merge（needs run）收齐、合并、查基线 →
    drill（needs merge 且 merge 成功）打补丁+合并清单再主演练 → gate（needs merge、drill）收齐演练（含 run 里的声音 4 片）、两个印章、彩排、写回"""
    e = []
    for k in ("job == '改门推送'", "('主演练', '0', '主演练')", "'job': '声音分片'", "'nd': len(drill) + 4", "'--分片表', '--受影响'", "startswith('快跑=')", "'base': 快[0], 'breq': 快[1]", "'base': '', 'breq': rid"):
        if k not in _段(t, 'plan'): e.append(f'plan 少了：{k}')
    for name, need, seq in (('run', 'needs: plan', ['声音分片)', '执行效应声音演练.py --分片=', "matrix.it.gate == '2'", '/tmp/sgate/rc_$A', "name: '演练_${{ matrix.it.req }}_${{ matrix.it.an }}'"]),
                            ('merge', 'needs: [plan, run]', ['gh run download "$BASE"', '"结果_${BREQ}_*"', '/tmp/a/gate/rc_*', '--合并结果', '/tmp/a/gate/*@*.json', '--查基线', '合并.diff']),
                            ('drill', 'needs: [plan, merge]', ["needs.merge.result == 'success'", '合并.diff', '执行效应演练.py']),
                            ('gate', 'needs: [plan, merge, drill]', ['"演练_${BREQ}_声音*"', '② 门变异合并、查基线通过', '/tmp/a/rc_*', '[ ! -s /tmp/a/主演练.diff ]', '主演练.diff', '--合并印章', '彩排.sh', '收尾快跑：全过', '改门推送：全过', '视频/云端/结果/'])):
        g = _段(t, name)   # 没有这一步：g 为空，下面两条都报
        if need not in g: e.append(f'{name} 没有或没等前一步（{need}）')
        ok, miss = _有序(g, seq)
        if not ok: e.append(f'{name} 少了或顺序错了（{" → ".join(seq)}；少：{"、".join(miss) or "无"}）')
    return e + 依赖问题(t)
依赖步 = 'pip install -q -r .github/核查依赖.txt'
def 依赖问题(t):
    """K61/K67：checkout 后跑 python3 的 job，第一次 python3 之前必须先装 .github/核查依赖.txt（零散 pip 两次漏装：plan 缺 numpy、gate 缺 numpy）"""
    e = []
    for name in re.findall(r'\n  ([A-Za-z_]+):\n', t):
        g = _段(t, name)
        if 'actions/checkout' not in g or 'python3' not in g: continue
        i = g.find(依赖步)
        if i < 0 or i > g.find('python3'): e.append(f'{name} 跑 python3 前没装核查依赖（{依赖步}；K61/K67）')
    return e
def _FAST查():
    """改门推送前当场跑 规则执行核查 的全部当场自检（K60v2 实测：印章没盖时 规则执行核查 只报印章、不跑自检，放行口子没登记到 GitHub 主演练才发现）"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 规则执行核查 as R
    return R.当场自检(R.程序表())
不进补丁 = [':(exclude)视频/制作记录/方法进化', ':(exclude)视频/制作记录/丝滑']   # 钩子每轮自动写的会话记录：不是门的改动，写了也不该让 --收 对不上（2026-10-27 K60改门推送v2 实测）
def 做补丁(名字, repo=P, out=None):
    """主仓库相对 HEAD 的全部改动（含新文件）→ 补丁文件；返回补丁路径（相对镜像）"""
    subprocess.run(['git', '-C', repo, 'add', '-A', '-N', '视频', 'CLAUDE.md'], capture_output=True)
    d = subprocess.run(['git', '-C', repo, 'diff', '--binary', 'HEAD', '--', '视频', 'CLAUDE.md', *不进补丁], capture_output=True).stdout
    rel = f'视频/云端/待演练/{名字}.diff'; open(out or f'{L}/{rel}', 'wb').write(d); return rel, d
def 收(名字, 说明, repo=P, run=True):
    """改门推送回来：结果全过、补丁就是主仓库现在的改动，才打上结果补丁并推送两仓库"""
    if run: g('pull', '-q', '--no-rebase', '--no-edit', 'origin', B)
    R = f'{L}/视频/云端/结果/{名字}.结果'; pf = f'{L}/视频/云端/待演练/{名字}.diff'
    if not os.path.exists(R + '.txt'): return f'GitHub 还没写回 {名字} 的结果（视频/云端/结果/{名字}.结果.txt）'
    t = open(R + '.txt').read()
    if '改门推送：全过' not in t or '退出码 0' not in t: return '改门推送没全过：' + ' '.join(l for l in t.splitlines() if '【' in l or '不过' in l)[:300]
    import hashlib
    if f'sha256 {hashlib.sha256(open(pf, "rb").read()).hexdigest()[:16]}' not in t: return '结果对应的补丁不是现在这份补丁文件（补丁推完又改过）'
    _, d = 做补丁(名字, repo, out=os.devnull)
    if d != open(pf, 'rb').read(): return '主仓库的改动和推上去的补丁不一样了（推完又改过）：重新 改门推送'
    r = subprocess.run(['git', '-C', repo, 'apply', R + '.diff'], capture_output=True, text=True) if os.path.getsize(R + '.diff') else None
    if r and r.returncode: return '结果补丁打不上：' + r.stderr[-200:]
    if not run: return ''
    r = subprocess.run(['bash', f'{repo}/视频/工具/推送两仓库.sh', 说明])
    return '' if r.returncode == 0 else '推送两仓库.sh 停了（结果补丁已打上，修好后重跑 推送两仓库.sh）'
def 自检_main():
    """main 的每一道停：在临时仓库（本地 bare 当远端）里真跑 main，造错必须返回 1、不推；好请求必须推上去"""
    global L, P, 工作流, 账, 本地慢印章, _FAST查
    f = []; d = tempfile.mkdtemp(prefix='推请求main自检_'); sh = lambda c, w=d: subprocess.run(c, shell=True, cwd=w, capture_output=True, text=True)
    old = (L, P, 工作流, 账, 本地慢印章, _FAST查); import io, contextlib
    def 跑(*a):
        with contextlib.redirect_stdout(io.StringIO()) as o: r = main(list(a))
        return r, o.getvalue()
    try:
        sh(f'git init -q --bare r.git && git init -q -b {B} L && cd L && mkdir -p 视频/云端/待演练 && echo a > 视频/x.txt && git add -A && git -c user.name=t -c user.email=t@t commit -qm 0 && git remote add origin ../r.git && git push -q origin {B}')
        sh('git init -q P && cd P && mkdir 视频 && echo a > 视频/x.txt && git add -A && git -c user.name=t -c user.email=t@t commit -qm 0')
        for r_ in ('L', 'P'): sh('git config user.name t && git config user.email t@t', f'{d}/{r_}')
        L, P, 账 = f'{d}/L', f'{d}/P', f'{d}/账.json'; 本地慢印章 = lambda 行: ''; _FAST查 = lambda: []
        open(f'{d}/好.yml', 'w').write(open(old[2]).read() if os.path.exists(old[2]) else ''); 工作流 = f'{d}/好.yml'
        if 排序问题(open(工作流).read()): f.append('main 自检：现行 drill.yml 改门推送链就不对，下面几项测不了'); return f
        open(f'{L}/视频/云端/待演练/好.diff', 'w').write('--- a/视频/x.txt\n+++ b/视频/x.txt\n@@ -1 +1 @@\n-a\n+b\n'); open(f'{L}/视频/云端/待演练/坏.diff', 'w').write('--- a/视频/x.txt\n+++ b/视频/x.txt\n@@ -1 +1 @@\n-zz\n+b\n')
        def 停(why, *a, 字='【停止】'):
            r, o = 跑(*a)
            if r != 1 or 字 not in o: f.append(f'main 没停：{why}')
            if os.path.exists(f'{L}/视频/云端/请求/{a[0]}.txt') and a[0] != '重名': f.append(f'main 停了却留下请求文件：{why}')
        停('带补丁的彩排单独发（K59 乱序）', 'a1', '彩排 补丁=视频/云端/待演练/好.diff')
        open(f'{d}/坏.yml', 'w').write(open(工作流).read().replace('--合并印章', '--合_并')); 工作流 = f'{d}/坏.yml'
        停('drill.yml 改门推送链缺一步（K60）', 'a2', '改门推送 补丁=视频/云端/待演练/好.diff'); 工作流 = f'{d}/好.yml'
        停('主仓库没改动还改门推送', 'a3', '改门推送', 字='没有改动')
        for a_ in (['--收', 'x'], ['只有名字']):
            if 跑(*a_)[0] != 1: f.append(f'main 参数不够没停：{a_}')
        本地慢印章 = lambda 行: '印章过期'; 停('本地慢自检印章过期（K35）', 'a4', '改门推送 补丁=视频/云端/待演练/好.diff'); 本地慢印章 = lambda 行: ''
        _FAST查 = lambda: ['自检不通过：x']; 停('当场自检没全过还改门推送（K60v2）', 'a8', '改门推送 补丁=视频/云端/待演练/好.diff', 字='当场自检'); _FAST查 = lambda: []
        停('补丁在工作分支上打不上（K43）', 'a5', '改门推送 补丁=视频/云端/待演练/坏.diff')
        os.makedirs(f'{L}/视频/云端/请求', exist_ok=True); open(f'{L}/视频/云端/请求/重名.txt', 'w').write('x\n'); sh('git add -A && git commit -qm r && git push -q origin HEAD', L)
        停('请求重名', '重名', '主演练')
        open(f'{L}/.git/hooks/pre-commit', 'w').write('#!/bin/sh\nexit 1\n'); os.chmod(f'{L}/.git/hooks/pre-commit', 0o755)
        停('提交没成功', 'a6', '主演练'); os.remove(f'{L}/.git/hooks/pre-commit')
        sh('git remote set-url origin ../没有.git', L); 停('推送没成功', 'a7', '主演练'); sh('git remote set-url origin ../r.git', L)
        停('--收 结果没写回', '--收', '没这个', 'x')
        open(f'{P}/视频/x.txt', 'w').write('b\n'); r, o = 跑('好请求', '改门推送')
        if r != 0 or 'origin/' and '好请求' not in sh(f'git --git-dir=r.git log -1 --name-only {B}').stdout: f.append(f'main 好请求没推上去：{o[-120:]}')
    finally:
        L, P, 工作流, 账, 本地慢印章, _FAST查 = old; shutil.rmtree(d, ignore_errors=True)
    return f
def 自检():
    f = []
    d = tempfile.mkdtemp(prefix='推请求自检_'); sh = lambda c: subprocess.run(c, shell=True, cwd=d, capture_output=True)
    sh('git init -q && printf "a\\nb\\n" > x.txt && git add x.txt && git -c user.name=t -c user.email=t@t commit -qm 0')
    open(f'{d}/好.diff', 'w').write('--- a/x.txt\n+++ b/x.txt\n@@ -1,2 +1,2 @@\n a\n-b\n+c\n'); open(f'{d}/坏.diff', 'w').write('--- a/x.txt\n+++ b/x.txt\n@@ -1,2 +1,2 @@\n a\n-zzz\n+c\n')
    if not 补丁打不上('门变异 x 补丁=坏.diff', d): f.append('没抓到：补丁在工作分支上打不上还让推（K43）')
    if 补丁打不上('门变异 x 补丁=好.diff', d) or 补丁打不上('主演练', d): f.append('误报：补丁打得上或没有补丁也拦（K43）')
    if 待提交补丁('门变异 x 补丁=好.diff', d) != ['好.diff']: f.append('没抓到：补丁文件没提交，请求照样推（K50）')
    sh('git add 好.diff && git -c user.name=t -c user.email=t@t commit -qm 1')
    if 待提交补丁('门变异 x 补丁=好.diff', d) or 待提交补丁('主演练', d): f.append('误报：补丁已提交或没有补丁也要再提交（K50）')
    shutil.rmtree(d, ignore_errors=True)
    if 定稿前提('定稿 26', lambda c: 0) or not 定稿前提('定稿 26', lambda c: c[0] == '放行口子核查.py') or not 定稿前提('定稿 26', lambda c: c[0] == '证据.py') or not 定稿前提('定稿', lambda c: 0) or 定稿前提('草稿 27', lambda c: 1):
        f.append('阶段 B：定稿请求没有用户原话、证据不全、没篇号不拦，或误拦了')
    for x in ('彩排 补丁=a.diff', '主演练 补丁=a.diff', '声音演练 补丁=a.diff'):
        if not 乱序(x): f.append(f'没抓到：{x} 单独发（K59/K60 乱序手排印章）')
    if 乱序('改门推送 补丁=a.diff') or 乱序('主演练') or 乱序('门变异 a.py@1@1 补丁=a.diff'): f.append('误拦：改门推送、不带补丁的主演练、门变异分片也拦了')
    t = open(工作流).read() if os.path.exists(工作流) else ''
    if 排序问题(t): f.append('drill.yml 改门推送链本身不对：' + '；'.join(排序问题(t)))
    else:
        def 改段(name, a_, b_): g_ = _段(t, name); return t.replace(g_, g_.replace(a_, b_, 1), 1)
        for name, a_, b_, why in (('gate', '彩排.sh', '彩_排', 'gate 里彩排排到演练印章前面'), ('gate', '--合并印章', '--合_并', 'gate 少了声音演练合并印章（缺一步）'),
                                  ('gate', 依赖步, 'pip install -q numpy', 'gate 没走装核查依赖这一步（K67：v5 合并印章 ModuleNotFoundError）'),
                                  ('plan', 依赖步, 'pip install -q numpy', 'plan 没走装核查依赖这一步（K61）'), ('merge', 依赖步, '#', 'merge 没装核查依赖'),
                                  ('drill', 依赖步, 'pip install -q x', 'drill 没装核查依赖'), ('run', 依赖步, 'true', 'run 没装核查依赖'),
                                  ('gate', '[ ! -s /tmp/a/主演练.diff ] || ', '', '主演练没写改动时空结果补丁 git apply 报错（K68：v6 实测）'),
                                  ('gate', 'needs: [plan, merge, drill]', 'needs: [plan, merge]', 'gate 不等演练全完就跑'), ('merge', '/tmp/a/gate/rc_*', '/tmp/a/rc_*', 'merge 到错的目录收门变异分片（K60v3：run 上传多个路径，结果在 /tmp/a/gate/）'),
                                  ('merge', '--查基线', '--查_基线', 'merge 不查门变异基线'), ('drill', "needs.merge.result == 'success'", 'true', '门变异没过也演练（K60v3：演练要合并后的清单）'),
                                  ('drill', 'needs: [plan, merge]', 'needs: [plan]', '演练不等门变异合并'), ('plan', "'job': '声音分片'", "'job': '声音_分片'", 'plan 不发声音演练分片（缺一步）'),
                                  ('plan', "'nd': len(drill) + 4", "'nd': len(drill)", 'gate 收演练份数没算 run 里的声音 4 片（⓪′：收齐数对不上必停）'),
                                  ('run', "matrix.it.gate == '2'", "matrix.it.gate == '9'", '声音分片的结果没留给 gate（⓪′）'),
                                  ('merge', 'gh run download "$BASE"', 'true "$BASE"', '收尾快跑不从底运行收分片结果（第五棒）'), ('gate', '"演练_${BREQ}_声音*"', '"演练_x_声音*"', '收尾快跑不收底运行的声音 4 片（第五棒）'),
                                  ('plan', "'base': 快[0], 'breq': 快[1]", "'base': '', 'breq': rid", '收尾快跑没记底运行（第五棒）'),
                                  ('gate', '收尾快跑：全过', '改门推送：全_过', '收尾快跑也写“改门推送：全过”能 --收（第五棒）')):
            if 'gate 里彩排排到' in why: x = 改段('gate', '彩排.sh', '彩_排'); x = x.replace("'改门推送：全过'", "'改门推送：全过' 彩排.sh", 1)
            else: x = 改段(name, a_, b_)
            if not 排序问题(x): f.append(f'没抓到：{why}')
    d = tempfile.mkdtemp(prefix='推请求收自检_'); sh = lambda c, w=d: subprocess.run(c, shell=True, cwd=w, capture_output=True)
    try:   # --收：结果没全过、补丁改过、主仓库改动和补丁不一样，都不许打上
        os.makedirs(f'{d}/L/视频/云端/结果'); os.makedirs(f'{d}/L/视频/云端/待演练'); os.makedirs(f'{d}/P/视频')
        sh('git init -q && echo a > 视频/x.txt && git add -A && git -c user.name=t -c user.email=t@t commit -qm 0', f'{d}/P'); open(f'{d}/P/视频/x.txt', 'w').write('b\n')
        global L; L0 = L; L = f'{d}/L'
        try:
            做补丁('t', f'{d}/P'); import hashlib; h = hashlib.sha256(open(f'{L}/视频/云端/待演练/t.diff', 'rb').read()).hexdigest()[:16]
            open(f'{L}/视频/云端/结果/t.结果.diff', 'w').write('')
            def 结(x): open(f'{L}/视频/云端/结果/t.结果.txt', 'w').write(x)
            结(f'补丁 sha256 {h}\n退出码 1\n【改门推送不过】④ 彩排\n')
            if not 收('t', '', f'{d}/P', run=False): f.append('没抓到：改门推送没全过也打上结果补丁')
            结(f'补丁 sha256 {h}\n退出码 0\n收尾快跑：全过（门变异结论来自底运行，不能 --收）\n')
            if not 收('t', '', f'{d}/P', run=False): f.append('没抓到：收尾快跑的结果也让 --收（门变异结论是底运行的）')
            结(f'补丁 sha256 0000\n退出码 0\n改门推送：全过\n')
            if not 收('t', '', f'{d}/P', run=False): f.append('没抓到：结果对应的补丁不是这份也打上')
            结(f'补丁 sha256 {h}\n退出码 0\n改门推送：全过\n'); open(f'{d}/P/视频/x.txt', 'w').write('c\n')
            if not 收('t', '', f'{d}/P', run=False): f.append('没抓到：推完又改了主仓库还打上旧结果')
            open(f'{d}/P/视频/x.txt', 'w').write('b\n'); os.makedirs(f'{d}/P/视频/制作记录/方法进化'); open(f'{d}/P/视频/制作记录/方法进化/s.json', 'w').write('{}')
            if 收('t', '', f'{d}/P', run=False): f.append('误拦：全过、补丁没变也不让收（钩子写的会话记录不算改动）')
        finally: L = L0
    finally: shutil.rmtree(d, ignore_errors=True)
    f += 自检_main()
    if '快跑=1@a@2@全量' not in 补丁行('x.diff', '改门推送 快跑=1@a@2@全量'): f.append('没抓到：改门推送 自动做补丁时把 快跑= 丢了（悄悄变全量）')
    if '【估时超 60 分钟' not in 估时提示({'片': 120, '机器分钟': 1900, '墙钟': 135, '最慢': ['x', 85]}): f.append('没抓到：估时超 60 分钟没先报（交接 ③）')
    if '【估时超' in 估时提示({'片': 10, '机器分钟': 100, '墙钟': 15, '最慢': ['x', 10]}): f.append('误报：估时不到 60 分钟也报超')
    if not 本地慢印章('主演练 补丁=视频/云端/待演练/x.diff', lambda p: p == '执行效应演练.py'): f.append('没抓到：出片守门自检印章过期还让推带补丁的主演练（K35）')
    if 本地慢印章('主演练 补丁=视频/云端/待演练/x.diff', lambda p: p != '彩排.sh', 缺口数=0): f.append('误拦：只有彩排印章过期就不让推主演练（彩排要先有主演练印章，两头互等，K60）')
    if not 本地慢印章('主演练 补丁=视频/云端/待演练/x.diff', lambda p: True, 缺口数=99): f.append('没抓到：演练缺口变多还让推带补丁的主演练')
    if 本地慢印章('主演练 补丁=视频/云端/待演练/x.diff', lambda p: p != '执行效应演练.py', 缺口数=0) or 本地慢印章('声音演练 补丁=x', lambda p: False): f.append('误报：印章有效或不是主演练也拦（K35）')
    return f
def main(a=None):
    a = sys.argv[1:] if a is None else a
    if a[:1] == ['--自检']: e = 自检(); print('\n'.join(e) or '推请求 自检通过（本地慢自检印章过期时带补丁的主演练必停，K35；补丁文件没提交随请求提交，K50；乱序发、缺一步、彩排排前、不等收齐必拒，没全过或补丁改过不许收，K59/K60）'); return 1 if e else 0
    if a[:1] == ['--收']:
        if len(a) < 3: print(__doc__); return 1
        e = 收(a[1], a[2], P); print('【停止】' + e if e else f'改门推送 {a[1]}：结果补丁已打上、两仓库已推送'); return 1 if e else 0
    if len(a) < 2: print(__doc__); return 1
    名字, 行 = a[0], a[1]; 注 = a[2] if len(a) > 2 else ''
    e = 乱序(行)
    if e: print('【停止】' + e); return 1
    if 行.split()[:1] == ['改门推送']:
        e = 排序问题(open(工作流).read())
        if e: print('【停止】drill.yml 的改门推送链不对：' + '；'.join(e)); return 1
        if '补丁=' not in 行:
            g('pull', '-q', '--no-rebase', '--no-edit', 'origin', B); rel, d_ = 做补丁(名字, P)
            if not d_.strip(): print('【停止】主仓库没有改动，不用改门推送'); return 1
            行 = 补丁行(rel, 行)
    e = 本地慢印章(行) or 定稿前提(行)
    if e: print('【停止】' + e); return 1
    if 行.startswith('改门推送'):
        r = subprocess.run(['python3', f'{os.path.dirname(os.path.abspath(__file__))}/门变异.py', '--估时'], capture_output=True, text=True)
        try: 估 = f'估时：收尾快跑约 {尾分} 分钟（门变异、声音 4 片拿底运行的结果）' if '快跑=' in 行 else 估时提示(json.loads(r.stdout.strip().splitlines()[-1])); print(估); 注 = (注 + '；' if 注 else '') + 估
        except Exception: print('【停止】门变异.py --估时 算不出（发前估时，交接 ③）：' + (r.stderr or r.stdout)[-300:]); return 1
        e = _FAST查()
        if e: print('【停止】当场自检没全过，GitHub 上主演练、彩排必然不过：' + '；'.join(e)[:400]); return 1
    f = f'视频/云端/请求/{名字}.txt'
    g('pull', '-q', '--no-rebase', '--no-edit', 'origin', B)
    e = 补丁打不上(行, L)
    if e: print('【停止】' + e); return 1
    if os.path.exists(f'{L}/{f}'): print(f'【停止】请求 {f} 已经有了（只认新加的文件）：换个名字'); return 1
    os.makedirs(f'{L}/视频/云端/请求', exist_ok=True)
    open(f'{L}/{f}', 'w').write((f'# {注}\n' if 注 else '') + 行 + '\n')
    H0 = g('rev-parse', 'HEAD').stdout.strip()
    g('add', f, *待提交补丁(行, L)); c = g('commit', '-qm', f'GitHub 请求：{名字}（{行[:60]}）\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')   # K50：补丁文件一起提交
    if c.returncode:
        g('reset', '-q', '--', f); os.remove(f'{L}/{f}')   # 提交没成功：请求文件收回，改好了用同一个名字再推
        print('【停止】提交没成功：' + (c.stdout + c.stderr)[-300:]); return 1
    for _ in range(3):
        if g('push', '-q', 'origin', B).returncode == 0: break
        g('pull', '-q', '--no-rebase', '--no-edit', 'origin', B)
    else:
        g('reset', '-q', H0); os.path.exists(f'{L}/{f}') and os.remove(f'{L}/{f}')   # 推不上：提交撤回、请求文件收回，好了用同一个名字再推
        print('【停止】推送没成功'); return 1
    t = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    try: d = json.load(open(账))
    except Exception: d = {}
    d.setdefault('请求', []).append({'名字': 名字, '行': 行, '时刻': t, '提交': g('rev-parse', '--short', 'HEAD').stdout.strip()})
    json.dump(d, open(账, 'w'), ensure_ascii=False)
    if 行.startswith('改门推送'): print(f'改门推送 {名字} 已发：GitHub 走完写回结果后 python3 视频/工具/推请求.py --收 {名字} "提交说明"（订阅 PR #7 等唤醒，不轮询）')
    print(f'已推请求 {名字}（{t}）。【必须】现在 send_later 约 20 分钟后叫回自己：GitHub 写回结果不会唤醒会话（K34）；结果在 {L}/视频/云端/结果/')
    return 0
if __name__ == '__main__': sys.exit(main())
