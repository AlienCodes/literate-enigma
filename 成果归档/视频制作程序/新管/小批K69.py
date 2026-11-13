#!/usr/bin/env python3
"""小批 K69 / K74 / K75（精简第八棒，主会话 2026-10-29 00:00 交办；安装那趟落地后发，目标 07:10 前落地）。底 = 装好新管后的 main。
  K75 开工记录：开工() 里补做事对照记录那一行 open(f,'w').write(补(open(f).read())) 先清空再读（G46 同类，28 起才走到，G46 自检没走这条路）→ 先读后写；
       自检走这条路（补对照=True）；开工记录 查上一篇 G65 时 写=False（不再往上一篇 NN.md 插“## 方法进化”，K75 后半、K88 同类）
  K74 方法进化表 落地查：只认本篇开工时刻之后的登记（K 按登记时刻、G 按取号时刻）和提交（提交时刻）；所有“## 方法复盘”节都读
  K69 规则执行核查：印章对不上时写出是哪几个文件变了；推请求.py --撤 <补丁>：撤补丁、删掉补丁新建的文件、列出残留
用法：python3 小批K69.py <工具目录>   （可重复打；锚找不到就停）"""
import sys, os

补丁 = [
    ('开工记录.py', "def 开工(V, no, 记当前=True, 根=None):", "def 开工(V, no, 记当前=True, 根=None, 补对照=False):"),
    ('开工记录.py', "    if no.isdigit() and int(no) >= _KB.起 and 记当前: open(f, 'w').write(_KB.补(no, open(f).read())[0])",
     "    if no.isdigit() and int(no) >= _KB.起 and (记当前 or 补对照): _t = open(f).read(); open(f, 'w').write(_KB.补(no, _t)[0])   # K75：先读后写（原来 open(f,'w') 先清空再读，28 新容器整份被冲成只剩做事对照记录）"),
    ('开工记录.py', "        msg, c = 开工(V, '98', 记当前=False, 根=r); t1 = open(f'{V}/制作记录/98.md').read()",
     "        msg, c = 开工(V, '98', 记当前=False, 根=r, 补对照=True); t1 = open(f'{V}/制作记录/98.md').read()   # K75：补做事对照记录这条路也要走到"),
    ('开工记录.py', "    import 方法进化表 as _JH; _e, _ = _JH.门(f'{int(_no) - 1:02d}')",
     "    import 方法进化表 as _JH; _e, _ = _JH.门(f'{int(_no) - 1:02d}', 写=False)   # K75 后半：查上一篇不写上一篇的 NN.md"),
    ('方法进化表.py', """def 落地查(txt, repos=None, 号=None):
    m = re.search(r'^## 方法复盘[^\\n]*\\n([\\s\\S]*?)(?=^## |\\Z)', txt, re.M)
    hs = re.findall(r'进化落地[：:]\\s*([^\\n]+)', m.group(1)) if m else []
    if 号 is None:
        try: 号 = {k['号'] for k in json.load(open(f'{REC}/坑登记.json')).get('登记', [])} | set(json.load(open(f'{T}/规则执行表.json')))
        except Exception: 号 = set()
    ok = []
    for h in hs:
        for x in re.findall(r'\\b([0-9a-f]{7,40}|[GK]\\d+)\\b', h):
            if x[0] in 'GK' and x in 号: ok.append(x)
            elif x[0] not in 'GK' and any(subprocess.run(['git', '-C', r, 'cat-file', '-e', x + '^{commit}'], capture_output=True).returncode == 0 for r in (repos or [P, '/home/user/literate-enigma']) if os.path.isdir(r)): ok.append(x)
    return ok""", """def 落地查(txt, repos=None, 号=None):
    \"\"\"K74：只认本篇开工时刻之后落成的：K 按登记时刻、G 按取号时刻、提交按提交时刻；所有“## 方法复盘”节都读（27.md 第一节是空的）\"\"\"
    hs = [h for m in re.finditer(r'^## 方法复盘[^\\n]*\\n([\\s\\S]*?)(?=^## |\\Z)', txt, re.M) for h in re.findall(r'进化落地[：:]\\s*([^\\n]+)', m.group(1))]
    a = re.search(r'开工时刻[：:]\\s*(\\d{4}-\\d\\d-\\d\\dT\\d\\d:\\d\\d)', txt); 起 = a.group(1) if a else ''
    if 号 is None:
        try:
            d = json.load(open(f'{REC}/坑登记.json'))
            号 = {k['号']: k.get('时刻', '') for k in d.get('登记', [])}; 号.update({r['编号']: r.get('时刻', '') for r in d.get('预留', []) if r.get('编号')})
            号.update({k: '' for k in json.load(open(f'{T}/规则执行表.json')) if k not in 号})   # 表里早就有、查不到时刻的：开工后不算
        except Exception: 号 = {}
    新 = lambda t: not 起 or (bool(t) and t[:16] >= 起)   # 时刻都是 UTC 'YYYY-MM-DDTHH:MM'
    ok = []
    for h in hs:
        for x in re.findall(r'\\b([0-9a-f]{7,40}|[GK]\\d+)\\b', h):
            if x[0] in 'GK':
                if x in 号 and (not isinstance(号, dict) or 新(号[x])): ok.append(x)
                continue
            for r in (repos or [P, '/home/user/literate-enigma']):
                if not os.path.isdir(r): continue
                c = subprocess.run(['git', '-C', r, 'log', '-1', '--format=%cI', x], capture_output=True, text=True)
                if c.returncode == 0 and c.stdout.strip():
                    t = __import__('datetime').datetime.fromisoformat(c.stdout.strip()).astimezone(__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H:%M')
                    if 新(t): ok.append(x)
                    break
    return ok"""),
    ('方法进化表.py', "    行2 = {'28': {'K': ['K1（程序）'], '机制漏洞': 1, '手工重复': 0}}\n", """    _t74 = '## token 记录\\n- 开工时刻：2026-10-28T12:00（UTC）\\n\\n## 方法复盘\\n\\n## 方法复盘\\n- 进化落地：{}\\n'   # K74：只认开工后落成的；两个复盘节都读
    _h74 = {'K900': '2026-10-28T13:00Z', 'K899': '2026-10-27T00:00Z', 'G900': '2026-10-28T12:30Z', 'G899': ''}
    if 落地查(_t74.format('K900'), 号=_h74) != ['K900']: f.append('K74：开工后登记的 K 没认（或第二个方法复盘节没读）')
    if 落地查(_t74.format('K899'), 号=_h74): f.append('K74 没抓到：开工前就登记的 K 算成了进化落地')
    if 落地查(_t74.format('G899'), 号=_h74): f.append('K74 没抓到：表里早就有、没有取号时刻的 G 算成了进化落地')
    if 落地查(_t74.format('G900'), 号=_h74) != ['G900']: f.append('K74：开工后取号的 G 没认')
    _d74 = tempfile.mkdtemp(prefix='K74_'); _g = lambda *c_, **e_: subprocess.run(['git', '-C', _d74, '-c', 'user.name=t', '-c', 'user.email=t@t', *c_], capture_output=True, text=True, env={**os.environ, **e_})
    _g('init', '-q'); open(f'{_d74}/a', 'w').write('1'); _g('add', 'a'); _g('commit', '-qm', '旧', GIT_COMMITTER_DATE='2026-10-01T00:00:00Z', GIT_AUTHOR_DATE='2026-10-01T00:00:00Z')
    _old = _g('rev-parse', '--short=9', 'HEAD').stdout.strip(); open(f'{_d74}/a', 'w').write('2'); _g('commit', '-qam', '新', GIT_COMMITTER_DATE='2026-10-28T15:00:00Z', GIT_AUTHOR_DATE='2026-10-28T15:00:00Z')
    _new = _g('rev-parse', '--short=9', 'HEAD').stdout.strip()
    if 落地查(_t74.format(_old), repos=[_d74], 号={}): f.append('K74 没抓到：开工前的旧提交算成了进化落地')
    if 落地查(_t74.format(_new), repos=[_d74], 号={}) != [_new]: f.append('K74：开工后的提交没认')
    行2 = {'28': {'K': ['K1（程序）'], '机制漏洞': 1, '手工重复': 0}}
"""),
    ('规则执行核查.py', "def 印章有效(p):", """def 印章差(p):
    \"\"\"K69：印章对不上时到底是哪几个文件变了（没有印章文件就是全部）\"\"\"
    f, progs = STAMPED[p]
    try: st = json.load(open(f'{T}/{f}'))
    except Exception: return list(progs)
    return [x for x in progs if st.get(x) != (hashlib.sha256(open(f'{T}/{x}', 'rb').read()).hexdigest() if os.path.exists(f'{T}/{x}') else '无')]


def 印章有效(p):"""),
    ('规则执行核查.py', "        if not 印章有效(p): gl.append(f'{STAMPED[p][1]} 改过、慢自检的印章对不上：",
     "        if not 印章有效(p): gl.append(f'{STAMPED[p][1]} 改过（这次变了：{\"、\".join(印章差(p)[:6])}；撤过补丁的先 python3 {os.path.relpath(T, P)}/推请求.py --撤 <补丁> 撤干净，K69）、慢自检的印章对不上："),
    ('规则执行核查.py', "        _sh2.rmtree(_d, ignore_errors=True)\n    return fails\n", """        _sh2.rmtree(_d, ignore_errors=True)
    _k = '出片守门自检.py'   # K69：印章对不上要写出是哪个文件变了
    if _k in STAMPED:
        _f, _ps = STAMPED[_k]; _st = {x: (hashlib.sha256(open(f'{T}/{x}', 'rb').read()).hexdigest() if os.path.exists(f'{T}/{x}') else '无') for x in _ps}
        _st[_ps[0]] = '别的指纹'; _bk = STAMPED[_k]; _tmpf = f'{T}/.K69自检印章.json'; json.dump(_st, open(_tmpf, 'w'))
        try:
            STAMPED[_k] = ('.K69自检印章.json', _ps)
            if 印章差(_k) != [_ps[0]]: fails.append(f'K69 没抓到：印章对不上时没写出变了的文件（应为 {_ps[0]}，得 {印章差(_k)}）')
        finally: STAMPED[_k] = _bk; os.remove(_tmpf)
    return fails
"""),
    ('推请求.py', "def main(a=None):", """def 撤(补丁, repo=P):
    \"\"\"K69：撤掉本地打过的补丁（git apply -R），删掉补丁新建的文件，列出撤完还没跟踪的残留\"\"\"
    t = open(补丁).read(); 新 = re.findall(r'^--- /dev/null\\n\\+\\+\\+ b/(.+)$', t, re.M)
    r = subprocess.run(['git', '-C', repo, 'apply', '-R', 补丁], capture_output=True, text=True)
    if r.returncode: return f'撤不掉（补丁没打上或已经撤过）：{r.stderr.strip()[:120]}'
    for x in 新:
        if os.path.exists(f'{repo}/{x}'): os.remove(f'{repo}/{x}')
    自 = os.path.relpath(os.path.abspath(补丁), os.path.abspath(repo))
    残 = [l[3:] for l in subprocess.run(['git', '-C', repo, '-c', 'core.quotepath=off', 'status', '--porcelain'], capture_output=True, text=True).stdout.splitlines() if l and l[3:] != 自]
    return ('撤完还有残留（不是这个补丁的改动，要人看）：' + '、'.join(残[:8])) if 残 else ''


def main(a=None):"""),
    ('推请求.py', "    if a[:1] == ['--收']:", """    if a[:1] == ['--撤']:   # K69：撤补丁要有正式命令（撤干净、列残留）
        if len(a) < 2: print(__doc__); return 1
        e = 撤(a[1]); print('【停止】' + e if e else f'已撤：{a[1]}（工作树干净）'); return 1 if e else 0
    if a[:1] == ['--收']:"""),
    ('推请求.py', "    if not 补丁打不上('门变异 x 补丁=坏.diff', d): f.append('没抓到：补丁在工作分支上打不上还让推（K43）')\n",
     """    if not 补丁打不上('门变异 x 补丁=坏.diff', d): f.append('没抓到：补丁在工作分支上打不上还让推（K43）')
    d2 = tempfile.mkdtemp(prefix='推请求撤自检_'); sh2 = lambda c: subprocess.run(c, shell=True, cwd=d2, capture_output=True)   # K69：撤补丁撤干净（单独的仓库，不动上面 K50 的样本）
    sh2('git init -q && printf "a\\nb\\n" > x.txt && git add x.txt && git -c user.name=t -c user.email=t@t commit -qm 0')
    pd = tempfile.mkdtemp(prefix='推请求撤补丁_') + '/加.diff'; open(pd, 'w').write('--- a/x.txt\\n+++ b/x.txt\\n@@ -1,2 +1,2 @@\\n a\\n-b\\n+c\\n--- /dev/null\\n+++ b/新.txt\\n@@ -0,0 +1 @@\\n+n\\n')
    sh2(f'git apply {pd}')
    if 撤(pd, d2) or os.path.exists(f'{d2}/新.txt') or open(f'{d2}/x.txt').read() != 'a\\nb\\n': f.append('K69 没抓到：--撤 没撤干净（改动或补丁新建的文件还在）')
    sh2(f'git apply {pd}'); open(f'{d2}/残留.txt', 'w').write('r')
    if '残留.txt' not in 撤(pd, d2): f.append('K69 没抓到：撤完的残留没列出来')
"""),
]

def main():
    t = sys.argv[1]; bad = []
    for f, a, b in 补丁:
        p = f'{t}/{f}'; s = open(p).read()
        if b in s: continue
        if s.count(a) != 1: bad.append(f'{f}：锚出现 {s.count(a)} 次：{a[:60]}'); continue
        open(p, 'w').write(s.replace(a, b))
    print('\n'.join(bad) or f'小批 K69/K74/K75：{len(补丁)} 处已打'); sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
