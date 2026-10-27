#!/usr/bin/env python3
"""用上核查（G83，用户 2026-10-27 第三次原话：“要有这么一个机制，就是专门检查我们的所有的东西都有没有用上……不是定期检查，就每次都要检查，
看看我们所有的这些东西都有没有用起来”）。一份“用上报告”，三块：
  ① 孤儿：视频/工具/ 每个程序、两个仓库 .github/workflows/ 每个工作流，必须 登记在 机制清单.json，或被正式入口调用（静态查调用链），
     或是本篇数据（初稿生成/genNN.py），或在 草稿流程.md 里点名（手工步骤入口），或登记“辅助”（写用途）/“下线”（只认用户同意记录）。都不是 = 孤儿。
  ② 管执行的机制接线：规则执行核查、执行效应演练、声音演练、报坑登记、会话开工、改门锁、证据链、闲置报警、门变异、机制漏洞记录、用上核查自己，
     每个必须接在它该接的正式入口上（锚在、不在注释里）；拆掉任何一处 = 没用上。
  ③ 该用没用（按时间）：门变异清单记录后门程序又改了或超过 1 天没全量跑；G71 闲置报警（做视频的机制连续两篇该用没用）。
每次都跑：会话开工（开头打印，读完才记指纹）、开工提醒、提交前钩子/推送两仓库/交付核查/定稿流水线 ⓪（都经 规则执行核查：①② 不过就停）、
定稿流水线 ⓪ 和 交付核查 再跑 --严（③ 也停）、主会话核对.sh。28 起定稿流水线最后打印“本篇执行报告”（--报告 NN）。
  python3 用上核查.py            打印用上报告；①② 有问题退出 1
  python3 用上核查.py --严       ③ 也算（定稿、出片前用）
  python3 用上核查.py --报告 NN  本篇执行报告（开工必读 ⑤ 每一步证据 + 每个登记机制）
  python3 用上核查.py --淘汰 [--写入]  P（用户 2026-10-27 第五次原话：完全不用的直接淘汰）：列 完全不用/老做法冲突/重复；--写入 把完全不用的挪进 已淘汰/、记“下线 <名>”、写 制作记录/淘汰清单.md
  python3 用上核查.py --自检"""
import os, sys, re, json, glob, subprocess, datetime, tempfile, shutil, hashlib
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V); L = '/home/user/literate-enigma'
清单F = f'{T}/机制清单.json'
不算程序 = re.compile(r'(^|/)(演练样本|历史版本|fonts|__pycache__|已淘汰)/')
正式根 = ['会话开工.py', '开工提醒.sh', '推送两仓库.sh', '主会话核对.sh', '钩子/闸门.py', '规则执行核查.py', 'githooks/pre-commit', '定稿流水线.sh', '交付核查.py']

# ② 管执行的机制：(机制, 文件, 锚)；文件相对 视频/工具
接线 = [
    ('规则执行核查', 'githooks/pre-commit', '规则执行核查.py" ||'), ('规则执行核查', '推送两仓库.sh', '规则执行核查.py'),
    ('规则执行核查', '定稿流水线.sh', 'python3 $T/规则执行核查.py >'), ('规则执行核查', '交付核查.py', "run(['python3', f'{T}/规则执行核查.py'])"),
    ('执行效应演练', '规则执行核查.py', "STAMPED['执行效应演练.py'] = ('执行效应演练通过.json'"), ('声音演练', '规则执行核查.py', "STAMPED['执行效应声音演练.py'] = ('执行效应声音演练通过.json'"),
    ('报坑登记', '定稿流水线.sh', 'python3 $T/报坑.py --查 --严 || stop'), ('报坑登记', '规则执行核查.py', '_BK.判(std, _BK.读本地())'),
    ('会话开工', 'githooks/pre-commit', '会话开工.py" --提交前 ||'), ('改门锁', '会话开工.py', 'err += K.锁问题('),
    ('证据链', '定稿流水线.sh', 'python3 $T/证据.py --查 $no 定稿 || stop'), ('证据链', '交付核查.py', '_ze = _ZJ.查(no, stage)'),
    ('闲置报警', '定稿流水线.sh', 'python3 $T/证据.py --闲置 || stop'), ('闲置报警', '开工提醒.sh', '证据.py --闲置'),
    ('门变异', '规则执行核查.py', '_me, _mw = _MB.查基线()'), ('门变异', '规则执行核查.py', "['门变异.py', '--自检']"), ('门变异', '流程自检.py', 'def sh门真跑(txt):'),
    ('机制漏洞记录', '踩坑核查.py', "err.append(f'[G79] 制作记录/{no}.md 没有"), ('机制漏洞记录', '方法进化表.py', '写报告进篇(no, 节); 写漏洞节(no, 行)'),
    ('丝滑记录', '定稿流水线.sh', 'python3 "$T/丝滑.py" 记 定稿流水线'), ('丝滑记录', '交付核查.py', "_SH.记('交付核查'"), ('新容器彩排', '规则执行核查.py', "STAMPED['彩排.sh'] = ('彩排通过.json'"),
    ('用上核查', '会话开工.py', '用上核查.py'), ('用上核查', '开工提醒.sh', '用上核查.py'), ('用上核查', '规则执行核查.py', '_YS.问题()'),
    ('用上核查', '定稿流水线.sh', 'python3 $T/用上核查.py --严 || stop'), ('用上核查', '交付核查.py', "/用上核查.py', '--严'])"), ('用上核查', '主会话核对.sh', '用上核查.py'),
]


def 程序们(t=T):
    fs = glob.glob(f'{t}/**/*.py', recursive=True) + glob.glob(f'{t}/**/*.sh', recursive=True) + [f'{t}/githooks/pre-commit']
    return sorted({os.path.relpath(f, t) for f in fs if os.path.isfile(f) and not 不算程序.search(os.path.relpath(f, t))})
def 工作流们():
    return sorted({(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(f)))), os.path.basename(f)) for d in (P, L) for f in glob.glob(f'{d}/.github/workflows/*.yml')})
def _引用(t, x):
    try: s = open(f'{t}/{x}', errors='ignore').read()
    except OSError: return set()
    ns = set(re.findall(r'([\w一-龥]+\.(?:py|sh))\b', s)) | {m + '.py' for m in re.findall(r'(?m)^\s*(?:import|from)\s+([\w一-龥]+)', s)} \
        | {m + '.py' for m in re.findall(r'\bimport ([\w一-龥]+) as\b', s)} | {m + '.py' for m in re.findall(r'[;,]\s*([\w一-龥]+) as _', s)}
    return {c for n in ns for c in (n, f'钩子/{n}', f'初稿生成/{n}', f'环境/{n}', f'独立复核/{n}', f'发音词典/{n}') if os.path.isfile(f'{t}/{c}')}
def 走得到(t=T, 清单=None):
    m = 清单 or json.load(open(f'{t}/机制清单.json'))
    roots = set(正式根) | {x for st in m.get('步骤', {}).values() for x in st.get('入口', [])} | {x for me in m.get('机制', []) + m.get('管执行', []) for x in me.get('包含', [])}
    for d in (P, L):
        for y in glob.glob(f'{d}/.github/workflows/*.yml'): roots |= set(re.findall(r'工具/([\w一-龥/]+\.(?:py|sh))', open(y).read()))
    seen, todo = set(), [r for r in roots if os.path.isfile(f'{t}/{r}')]
    while todo:
        x = todo.pop()
        if x not in seen: seen.add(x); todo += list(_引用(t, x))
    return seen
def 孤儿(t=T, 清单=None, 流程=None, 同意=None):
    """[(程序, 原因)]"""
    m = 清单 or json.load(open(f'{t}/机制清单.json')); 辅 = m.get('辅助', {}); 下 = m.get('下线', {})
    流程 = 流程 if 流程 is not None else (open(f'{t}/草稿流程.md').read() if os.path.exists(f'{t}/草稿流程.md') else '')
    同意 = 同意 if 同意 is not None else json.dumps(json.load(open(f'{t}/用户同意记录.json')), ensure_ascii=False) if os.path.exists(f'{t}/用户同意记录.json') else ''
    ok = 走得到(t, m); out = []
    for p in 程序们(t):
        if p in ok or re.fullmatch(r'初稿生成/gen\d\d\.py', p) or os.path.basename(p) in 流程: continue
        if p in 辅 and len(str(辅[p])) >= 10: continue
        if p in 下 and f'下线 {p}' in 同意: continue
        out.append((p, '下线没有用户原话（用户同意记录里要有“下线 文件”）' if p in 下 else '没登记、没有正式入口调用、草稿流程没点名、没登记辅助用途'))
    wf = m.get('工作流', {})
    for repo, y in 工作流们():
        if y not in wf: out.append((f'.github/workflows/{y}（{repo}）', '工作流没登记进 机制清单.json 工作流'))
    return out


def _代码有(t, f, anchor):
    try: s = open(f'{t}/{f}').read()
    except OSError: return False
    for l in s.splitlines():
        if anchor in l:
            i = l.find(anchor); code = l[:i]
            if not code.lstrip().startswith('#') and not re.search(r'(?:^|\s)#', re.sub(r"'[^']*'|\"[^\"]*\"", '', code)): return True
    return False
def 没接上(t=T):
    return [(机, f, a) for 机, f, a in 接线 if not _代码有(t, f, a)]


def 该用没用():
    """③ 按时间：[说明]"""
    out = []
    sys.path.insert(0, T)
    try:
        import 门变异 as MB
        if not os.path.exists(MB.清单): out.append('门变异：还没有门变异清单（GitHub 全量跑一遍）')
        else:
            nw = [x for x in MB.新门() if not x.split('|')[0].endswith('.sh')]
            c = subprocess.run(['git', '-C', P, 'log', '-1', '--format=%cI', '--', MB.清单], capture_output=True, text=True).stdout.strip()
            age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(c)).total_seconds() / 3600 if c else 0
            if nw: out.append(f'门变异：清单记录以后 {len(nw)} 道 .py 门新加或改过，还没全量重跑（推请求.py 门变异）')
            if age > 24: out.append(f'门变异：{age:.0f} 小时没全量跑（每天一次，推请求.py 门变异）')
    except Exception as e: out.append(f'门变异：读不了（{e!r}）')
    try:
        import 证据 as ZJ; out += [f'闲置（G71）：{x}' for x in ZJ.闲置问题()]
    except Exception as e: out.append(f'闲置报警：读不了（{e!r}）')
    return out


淘汰词 = re.compile(r'一次性|不再用|原型|留着备查')
def 淘汰(t=T, 清单=None):
    """P：{类: [(对象, 说明)]}。完全不用 = 登记“辅助”且自己写着一次性/不再用/原型/备查、没有正式入口走到、别的程序和演练都不引用；
    老做法冲突 = 草稿流程、主会话交接、改门_*.md 里点名的程序已经不存在；重复 = 两个程序内容一模一样，或 X_旧/X_old/X_vN 和现行 X 并存"""
    m = 清单 or json.load(open(f'{t}/机制清单.json')); 辅 = m.get('辅助', {}); out = {'完全不用': [], '老做法冲突': [], '重复': []}
    progs = 程序们(t); ok = 走得到(t, m)
    演 = ''.join(open(f'{t}/{x}', errors='ignore').read() for x in ('执行效应演练.py', '执行效应声音演练.py') if os.path.exists(f'{t}/{x}'))
    文 = {q: open(f'{t}/{q}', errors='ignore').read() for q in progs}
    for p in progs:
        if p in ok or p not in 辅 or not 淘汰词.search(str(辅[p])) or os.path.basename(p) in 演: continue
        if any(os.path.basename(p) in 文[q] for q in progs if q != p): continue
        out['完全不用'].append((p, str(辅[p])[:60]))
    vd = os.path.dirname(t)
    for d in sorted(glob.glob(f'{t}/草稿流程.md') + glob.glob(f'{vd}/制作记录/主会话交接.md') + glob.glob(f'{vd}/制作记录/改门_*.md')):
        for x in sorted(set(re.findall(r'(?:视频/工具/|\$T/|工具/)([\w一-龥/]+\.(?:py|sh))', open(d).read()))):
            if 'NN' not in x and not os.path.exists(f'{t}/{x}'): out['老做法冲突'].append((os.path.relpath(d, vd), f'点名的 {x} 已不存在'))
    h = {}
    for q in progs:
        if os.path.getsize(f'{t}/{q}') > 0: h.setdefault(hashlib.sha256(open(f'{t}/{q}', 'rb').read()).hexdigest(), []).append(q)
    out['重复'] += [('、'.join(v), '内容一模一样') for v in h.values() if len(v) > 1]
    for q in progs:
        mm = re.match(r'(.+?)(?:_旧|_old|_v\d+|旧版)\.(py|sh)$', q)
        if mm and f'{mm.group(1)}.{mm.group(2)}' in progs: out['重复'].append((q, f'旧版，现行 {mm.group(1)}.{mm.group(2)}'))
    return out
def 淘汰写入(t=T):
    """完全不用的挪进 已淘汰/（git 历史保留），机制清单 辅助 去掉，用户同意记录 每项一条“下线 <名>”引用 2026-10-27 总同意条，写 淘汰清单.md"""
    r = 淘汰(t); m = json.load(open(f'{t}/机制清单.json')); 同 = json.load(open(f'{t}/用户同意记录.json'))
    总 = next(x for x in 同['记录'] if '完全不用的那些东西就可以直接被淘汰掉' in x.get('原话', ''))
    day = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'); done = []
    for p, why in r['完全不用']:
        os.makedirs(os.path.dirname(f'{t}/已淘汰/{p}'), exist_ok=True)
        if subprocess.run(['git', '-C', t, 'mv', p, f'已淘汰/{p}'], capture_output=True).returncode: shutil.move(f'{t}/{p}', f'{t}/已淘汰/{p}')
        m.get('辅助', {}).pop(p, None); done.append((p, why))
        同['记录'].append({'篇': '全部', '日期': day, '原话': 总['原话'], '用于': f'下线 {p}（完全不用：{why}；挪进 视频/工具/已淘汰/）', '来源': f'引用 {总["日期"]} 总同意条（{总["来源"][:40]}）；用上核查.py --淘汰 --写入'})
    json.dump(m, open(f'{t}/机制清单.json', 'w'), ensure_ascii=False, indent=1); json.dump(同, open(f'{t}/用户同意记录.json', 'w'), ensure_ascii=False, indent=1)
    vd = os.path.dirname(t); f = f'{vd}/制作记录/淘汰清单.md'; old = open(f).read() if os.path.exists(f) else '# 淘汰清单（用上核查.py --淘汰 --写入 生成；P，用户 2026-10-27：“完全不用的那些东西就可以直接被淘汰掉了”）\n\n| 日期 | 程序 | 原因 | 去向 |\n|---|---|---|---|\n'
    open(f, 'w').write(old + ''.join(f'| {day} | {p} | {why} | 视频/工具/已淘汰/{p} |\n' for p, why in done))
    return done, r


def 问题(t=T):
    """①② 结构问题 + P 淘汰：规则执行核查用（提交、推送、交付核查、定稿 ⓪）"""
    tt = 淘汰(t)
    return [f'孤儿：{p}（{w}）' for p, w in 孤儿(t)] + [f'没接上：{m} 没接在 {f}（锚“{a[:40]}”）' for m, f, a in 没接上(t)] \
        + [f'{k}（P 淘汰）：{x}（{w}）——python3 视频/工具/用上核查.py --淘汰 --写入，老做法冲突改文档指向现行入口' for k, v in tt.items() for x, w in v]


def 报告(no):
    sys.path.insert(0, T); import 方法进化表 as F, 证据 as ZJ
    节 = F.机制报告(no); m = json.load(open(清单F)); rs = ZJ.读(no); 有 = {r['步'] for r in rs if r.get('结果') == '通过'}
    L_ = [f'【本篇执行报告 {no}（G83：开工必读 ⑤ 每一步 + 每个登记机制）】'] + [x for x in 节 if x.startswith('- ')]
    for me in m.get('机制', []):
        L_.append(f'  {"✔" if me.get("证据") in 有 else "✘"} {me["名"][:40]}：证据“{me.get("证据")}”{"在" if me.get("证据") in 有 else "缺"}（{me.get("在", "")}跑）')
    bad = 没接上(); L_.append(f'  管执行的机制：{len({x[0] for x in 接线})} 个，' + ('全部接上' if not bad else '没接上 ' + '、'.join(sorted({x[0] for x in bad}))))
    w = 该用没用(); L_.append('  该用没用：' + ('无' if not w else '；'.join(w)))
    return '\n'.join(L_)


def 自检():
    f = []
    d = tempfile.mkdtemp(prefix='用上自检_'); t = f'{d}/视频/工具'; os.makedirs(f'{t}/githooks')
    m = {'步骤': {'a': {'入口': ['入口.py']}}, '机制': [], '工作流': {}, '辅助': {'辅.py': '标定用的一次性小程序，留着备查'}, '下线': {'旧.py': '不用了'}}
    open(f'{t}/入口.py', 'w').write('import 被调\n'); open(f'{t}/被调.py', 'w').write('x=1\n'); open(f'{t}/新.py', 'w').write('x=1\n')
    open(f'{t}/辅.py', 'w').write(''); open(f'{t}/旧.py', 'w').write(''); open(f'{t}/手工.py', 'w').write('')
    os.makedirs(f'{t}/初稿生成'); open(f'{t}/初稿生成/gen99.py', 'w').write('')
    o = [p for p, _ in 孤儿(t, m, '照 手工.py 做', '')]
    if '新.py' not in o: f.append('没抓到：新程序没登记、没人调用（孤儿）')
    if '旧.py' not in o: f.append('没抓到：下线没有用户原话')
    if any(x in o for x in ('被调.py', '入口.py', '辅.py', '手工.py', '初稿生成/gen99.py')): f.append(f'误报：登记了、被调用、辅助、流程点名、本篇数据的也算孤儿：{o}')
    if '旧.py' in [p for p, _ in 孤儿(t, m, '', '{"原话": "下线 旧.py"}')]: f.append('误报：下线有用户原话还算孤儿')
    tt = 淘汰(t, m)   # P：辅助里写着一次性/备查、没人引用 = 完全不用；文档点名不存在的程序 = 老做法冲突；同内容、X_旧 = 重复
    if '辅.py' not in [x for x, _ in tt['完全不用']]: f.append('没抓到：一次性小程序没人用（P 完全不用）')
    os.makedirs(f'{d}/视频/制作记录'); open(f'{d}/视频/制作记录/主会话交接.md', 'w').write('跑 python3 视频/工具/早没了.py\n')
    open(f'{t}/被调_旧.py', 'w').write('y=2\n'); open(f'{t}/抄的.py', 'w').write('x=1\n')
    tt = 淘汰(t, m)
    if not any('早没了.py' in w for _, w in tt['老做法冲突']): f.append('没抓到：文档点名的程序已不存在（P 老做法冲突）')
    if not any('被调_旧.py' == x for x, _ in tt['重复']) or not any('抄的.py' in x for x, _ in tt['重复']): f.append(f'没抓到：旧版并存、内容一样（P 重复）：{tt["重复"]}')
    if any(x in [y for y, _ in tt['完全不用']] for x in ('被调.py', '入口.py', '手工.py')): f.append('误报：用着的程序当成完全不用（P）')
    os.remove(f'{t}/被调_旧.py'); os.remove(f'{t}/抄的.py')
    for _, fn, a in 接线:   # 把真程序拷进假目录，拆掉一处接线必须报出
        os.makedirs(os.path.dirname(f'{t}/{fn}'), exist_ok=True)
        if os.path.exists(f'{T}/{fn}'): shutil.copy(f'{T}/{fn}', f'{t}/{fn}')
    base = 没接上(t)
    if base: f.append(f'原样就报没接上：{base[:2]}')
    for 机, fn, a in (接线[0], 接线[9], next(x for x in 接线 if x[0] == '用上核查' and x[1] == '会话开工.py'), next(x for x in 接线 if x[0] == '门变异')):
        s = open(f'{t}/{fn}').read(); open(f'{t}/{fn}', 'w').write('\n'.join('# ' + l if a in l else l for l in s.split('\n')))   # 整行注释掉（K37 式拆门）
        if (机, fn, a) not in 没接上(t): f.append(f'没抓到：{机} 从 {fn} 拆掉（管执行的机制被拆）')
        open(f'{t}/{fn}', 'w').write(s)
    shutil.rmtree(d, ignore_errors=True)
    return f


def 打印(严=False):
    q = 问题(); w = 该用没用()
    n = len(程序们()); nw = len(工作流们()); nm = len({x[0] for x in 接线})
    print(f'【用上核查（G83，每次都查）】程序 {n} 个、工作流 {nw} 个、管执行的机制 {nm} 个：' + ('全部用上' if not q else f'{len(q)} 处没用上') + ('' if not w else f'；该用没用 {len(w)} 处'))
    for x in q[:15]: print('  ✘', x[:170])
    for x in w[:8]: print('  ' + ('✘' if 严 else '△'), x[:170])
    return q + (w if 严 else [])


def main():
    a = sys.argv[1:]
    if '--自检' in a:
        e = 自检(); print('用上核查 自检：' + ('通过（新程序没登记、下线没用户原话必报；登记的、被调用的、辅助、流程点名、本篇数据不误报；拆掉规则执行核查/改门锁/开工打印/门变异的接线必报）' if not e else '【失灵】' + '；'.join(e)))
        return 1 if e else 0
    if '--报告' in a: print(报告(a[a.index('--报告') + 1])); return 0
    if '--淘汰' in a:
        if '--写入' in a:
            done, r = 淘汰写入(); print(f'淘汰：挪进 已淘汰/ {len(done)} 个：' + '、'.join(p for p, _ in done))
        r = 淘汰(); n = sum(len(v) for v in r.values()); print(f'【淘汰（P）】完全不用 {len(r["完全不用"])}、老做法冲突 {len(r["老做法冲突"])}、重复 {len(r["重复"])}')
        for k, v in r.items():
            for x, w in v: print(f'  ✘ {k}：{x}（{w}）'[:170])
        return 1 if n else 0
    bad = 打印('--严' in a)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
