#!/usr/bin/env python3
"""门变异演练（G79，用户 2026-10-27：“要一直不停的去发现……这套机制的问题和漏洞，然后不断的去进化和升级，直到做到绝对完美为止”）。
机制自己找自己的漏洞：把正式入口里每一道“停”的门挨个拆掉（字留着、动作没了，和 K37 一样：|| stop 写进注释，门的字还在、门没了），
在仓库镜像里跑探测（规则执行核查 去掉印章那一项后的全部当场自检 + 流程自检；--全 再加执行效应演练），
拆了没有任何东西发现 = 漏洞。门写在注释后面（死门）直接算漏洞。
  python3 门变异.py                       沙盒：只拆 git 改动里的入口文件的门（没有改动就只列门数）
  python3 门变异.py 定稿流水线.sh ...     只拆这几个文件
  python3 门变异.py --全量                全部入口（慢，放 GitHub：推请求.py 门变异）
  python3 门变异.py --全量 --写清单       写 制作记录/门变异清单.md、门变异缺口基线.json（只许减少）
  python3 门变异.py --查基线              规则执行核查用：清单里的漏洞数不许比基线多、清单要对得上现行门（门变了没重跑就停）
  python3 门变异.py --自检                K37 重放：K37 那一行（|| stop 在注释后）必须列为漏洞；门真被拆掉、拆门后探测报出要算“发现”
"""
import os, sys, re, ast, json, subprocess, hashlib, shutil, tempfile
from concurrent.futures import ThreadPoolExecutor
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
BASE = f'{T}/门变异缺口基线.json'; 清单 = f'{V}/制作记录/门变异清单.md'
# 正式入口（机制清单的入口 + 每个机制的门程序）：.sh 全部；.py 按机制清单
def 入口文件():
    m = json.load(open(f'{T}/机制清单.json'))
    fs = {x for st in m.get('步骤', {}).values() for x in st.get('入口', [])}
    for mech in m.get('机制', []) + m.get('管执行', []):   # H：管执行的机制也拆（看门的也要被看）
        fs |= {x for x in mech.get('包含', []) if isinstance(x, str)}
    fs |= {os.path.relpath(f, T) for f in __import__('glob').glob(f'{T}/*.sh')}
    return sorted(f for f in fs | {'githooks/pre-commit'} if os.path.isfile(f'{T}/{f}') and (f.endswith(('.sh', '.py')) or f == 'githooks/pre-commit'))


# ---------- 列门 ----------
def _代码注释(l):
    """(代码部分, 注释起点)：引号里的 # 不算注释（同 流程自检.sh毛病）"""
    code = re.sub(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"", lambda m: '"' + 'x' * (len(m.group(0)) - 2) + '"', l)
    m = re.search(r'(?:^|\s);?#(?![!{])', code)
    return (m.start() if m else len(l))
STOP_SH = re.compile(r'(?<![\w$-])(?:stop\s+["\'$]|exit\s+[1-9])')
def 门_sh(txt):
    """[(行号, 列, 原文, 死门)]：每个 stop "…" / exit 非0；注释后面的是死门"""
    out = []
    for i, l in enumerate(txt.splitlines(), 1):
        if l.lstrip().startswith('#') or re.match(r'\s*stop\s*\(\)', l): continue
        c = _代码注释(l)
        for m in STOP_SH.finditer(l): out.append((i, m.start(), l.strip()[:120], m.start() >= c))
    return out
def 变异_sh(txt, i, col):
    ls = txt.split('\n'); ls[i - 1] = ls[i - 1][:col] + ': ' + ls[i - 1][col:]   # 字留着，动作没了（: 吃掉参数）
    return '\n'.join(ls)

ERRS = re.compile(r'^(fails?|errs?|errors?|bad|gl|e|err|out|问题|毛病|不过|缺|停|res|new|hits?|msgs?|probs?)$')
泛名 = {'res', 'out', 'new', 'hits', 'hit', 'msgs'}   # 这些名字也常用来收集普通结果：只有收的是“说明文字”才算记不通过（读音核对 res.append((标签, 抓到没有))、放行口子核查 out += [(类, 键, 值)] 不是门）
def _长消息(x):
    if isinstance(x, ast.Constant): return isinstance(x.value, str) and len(x.value) >= 6
    if isinstance(x, ast.BinOp): return _长消息(x.left) or _长消息(x.right)
    return False
def _是消息(v):
    if isinstance(v, ast.Tuple):   # (名, False, 说明)、(行, '中文变量展开…')：带 False 或带一句说明文字的才是记不通过
        return any(isinstance(x, ast.Constant) and x.value is False for x in v.elts) or any(_长消息(x) for x in v.elts)
    if isinstance(v, (ast.List, ast.Set)): return bool(v.elts) and all(_是消息(x) for x in v.elts)
    if isinstance(v, ast.Constant): return isinstance(v.value, str)
    if isinstance(v, ast.JoinedStr): return True
    if isinstance(v, ast.BinOp): return _是消息(v.left) or _是消息(v.right)
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr in ('format', 'join'): return True
    return False
def _是停(n):
    """这一句是不是“停/记一条不通过”"""
    if isinstance(n, ast.Raise): return True
    if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant) and n.value.value in (1, False) and n.value.value is not True: return n.value.value == 1
    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
        f = n.value.func
        if isinstance(f, ast.Attribute) and f.attr == 'exit' and getattr(f.value, 'id', '') == 'sys':
            a = n.value.args; return not a or not (isinstance(a[0], ast.Constant) and a[0].value in (0, None))
        if isinstance(f, ast.Name) and f.id in ('stop', '停'): return True
        if isinstance(f, ast.Attribute) and f.attr in ('append', 'extend') and isinstance(f.value, ast.Name) and ERRS.match(f.value.id):
            return f.value.id not in 泛名 or bool(n.value.args) and _是消息(n.value.args[0])
    if isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name) and ERRS.match(n.target.id):
        return n.target.id not in 泛名 or _是消息(n.value)
    return False
def 自检门(txt, n, fn):
    """自检自己的断言（“没抓到/误报/失灵”、自检函数里）不是门：拆它要靠“自检的自检”，不在这里查"""
    if '自检' in fn or fn.startswith('_t') : return True
    body = ''.join(ast.get_source_segment(txt, b) or '' for b in n.body if _是停(b))
    if re.search(r'失灵', ''.join(ast.get_source_segment(txt, b) or '' for b in n.body)): return True   # “自检失灵就停”（踩坑核查 if fails: 失灵）
    return bool(re.search(r'没抓到|误报|失灵|自检|拆门|重放', body))
_ARGV = {'a', 'argv', 'args', 'A', 'av'}
def _是argv(x):
    if isinstance(x, ast.Subscript): x = x.value
    return (isinstance(x, ast.Name) and x.id in _ARGV) or (isinstance(x, ast.Attribute) and x.attr == 'argv')
def _派发(t):
    """按命令行参数或 __name__ 分派的 if（里面 sys.exit(main())）不是门（G79 交接①）"""
    def 守(v):   # a、len(a) > 1 这类只防越界的
        if _是argv(v): return True
        if isinstance(v, ast.Compare) and isinstance(v.left, ast.Call) and getattr(v.left.func, 'id', '') == 'len' and v.left.args and _是argv(v.left.args[0]): return True
        return False
    if isinstance(t, ast.BoolOp): return all(_派发(v) or 守(v) for v in t.values) and any(_派发(v) for v in t.values)
    if isinstance(t, ast.Compare) and len(t.ops) == 1:
        l, r = t.left, t.comparators[0]
        if any(isinstance(x, ast.Name) and x.id == '__name__' for x in (l, r)): return True
        if any(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in (l, r)) and any(_是argv(x) for x in (l, r)): return True
    return False
def 门_py(txt):
    """[(行号, (起行, 起列字节, 止行, 止列字节), 原文, False)]：if 判断、分支里直接有“停/记不通过”的"""
    try: tree = ast.parse(txt)
    except SyntaxError: return []
    out = []; fn_of = {}
    for f in ast.walk(tree):
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for x in ast.walk(f): fn_of.setdefault(id(x), f.name)
    for n in ast.walk(tree):
        if isinstance(n, ast.If) and not _派发(n.test) and any(_是停(b) for b in n.body) and not 自检门(txt, n, fn_of.get(id(n), '')):
            t = n.test; out.append((n.lineno, (t.lineno, t.col_offset, t.end_lineno, t.end_col_offset), txt.splitlines()[n.lineno - 1].strip()[:120], False))
    return sorted(out)
def 变异_py(txt, pos):
    a, ac, b, bc = pos; ls = [l.encode() for l in txt.split('\n')]
    if a == b: ls[a - 1] = ls[a - 1][:ac] + b'(False and (' + ls[a - 1][ac:bc] + b'))' + ls[a - 1][bc:]
    else: ls[b - 1] = ls[b - 1][:bc] + b'))' + ls[b - 1][bc:]; ls[a - 1] = ls[a - 1][:ac] + b'(False and (' + ls[a - 1][ac:]
    return b'\n'.join(ls).decode()
def 列门(rel, txt):
    return [(rel,) + g for g in (门_sh(txt) if 是sh(rel) else 门_py(txt))]
def 变异(rel, txt, g):
    return 变异_sh(txt, g[1], g[2]) if 是sh(rel) else 变异_py(txt, g[2])
def 是sh(rel): return rel.endswith('.sh') or rel == 'githooks/pre-commit'
def 门号(g):   # 稳定编号：文件 + 这一行的原文 + 同一行第几个（行号会挪，不进编号）
    return f'{g[0]}|{hashlib.sha1(g[3].encode()).hexdigest()[:10]}|{g[2] if 是sh(g[0]) else 0}'


# ---------- 探测 ----------
# 入口 → 程序（执行效应演练 仓库跑/跑 的入口）；一道门由“引用闭包里有它所在文件”的自检和演练场景来查
演练入口 = {'出片': '踩坑核查.py', '读音': '读音核对.py', '踩坑出片': '踩坑核查.py', '踩坑文本': '踩坑核查.py', '排版': '排版自检.py', '生成文本': '生成文本.py',
           '归档': '归档定稿视频.py', '清点': '定稿视频核对.py', '规则核查': '规则执行核查.py', '演练入口': '执行效应演练.py', '欠着': '全篇核查.py',
           '开工提醒': '开工提醒.sh', '报坑自检': '报坑.py', '配音缓存自检': '配音缓存核对.py', '会话开工查': '会话开工.py', '开工记录': '开工记录.py',
           '初稿': '初稿生成/核对.py', '流水线': '定稿流水线.sh'}
元程序 = {'规则执行核查.py', '执行效应演练.py', '执行效应声音演练.py', '开工必读.py', '证据.py', '会话开工.py', '演练镜像.py', '出片守门自检.py', '放行口子核查.py', '开工提醒.sh', '镜像同步.py'}
_闭 = {}
def 闭包(prog):
    """prog 引用到的工具文件（import、python3 $T/x.py、x.sh），一直往下"""
    if prog in _闭: return _闭[prog]
    seen, todo = set(), [prog]
    while todo:
        x = todo.pop()
        if x in seen or not os.path.isfile(f'{T}/{x}'): continue
        seen.add(x)
        if x in 元程序 and x != prog: continue   # 元程序（点名全部程序的）不往下展开：它们跑的自检这里直接跑
        t = open(f'{T}/{x}', errors='ignore').read()
        t = '\n'.join(l.split('#')[0] if x.endswith('.sh') else l for l in t.splitlines())
        for m in set(re.findall(r'([\w一-龥]+\.(?:py|sh))\b', t)) | {m + '.py' for m in re.findall(r'(?m)^\s*(?:import|from)\s+([\w一-龥]+)', t)} | {m + '.py' for m in re.findall(r'import ([\w一-龥]+) as', t)}:
            for c in (m, f'钩子/{m}', f'初稿生成/{m}'):
                if os.path.isfile(f'{T}/{c}'): todo.append(c)
    _闭[prog] = seen; return seen
def 相关(rel):
    """(自检命令, 演练场景号)：闭包里有 rel 的"""
    sys.path.insert(0, T); import 规则执行核查 as R, 执行效应演练 as Y
    cmds = [c for c in R.FAST if rel in 闭包(c[0])]
    if rel.endswith('.py') and os.path.exists(f'{T}/{rel}') and "'--自检'" in open(f'{T}/{rel}').read() and [rel, '--自检'] not in cmds: cmds.append([rel, '--自检'])   # 文件自己的自检总是相关（2026-10-27：规则执行核查 --自检 不在 FAST，自己的门没人探）
    sids = [s[0] for s in Y.场景 if rel in 闭包(演练入口.get(s[1], ''))] + [s[0] for s in Y.仓库场景 if rel in 闭包(演练入口.get(s[1], ''))]
    if rel in 闭包('钩子/闸门.py'): sids += [s[0] for s in Y.钩子场景]
    return cmds, sids
覆盖图 = f'{T}/门变异覆盖.json'
SITE = """import os
if os.environ.get('门变异覆盖'):
    try:
        import coverage, atexit
        _w = os.getcwd(); _b = os.path.basename(_w)
        _t = os.environ.get('门变异标签', '') + '|' + (os.path.basename(os.path.dirname(_w)) + '_' + _b if _b == 'video' else _b)   # 声音演练每场的工作目录都叫 video：带上一级（演练_声_<场景>）
        _c = coverage.Coverage(data_file=os.path.join(os.environ['门变异覆盖'], _t.replace('/', '_') + '.' + str(os.getpid())), omit=['*/site-packages/*', '*/lib/python3*'])
        _c.start(); atexit.register(lambda: (_c.stop(), _c.save()))
    except Exception: pass
"""
def 覆盖(部分, out):
    """GitHub 上（视频工作目录）：带行覆盖跑一遍探测，记下每道 .py 门（if 那一行）被哪些自检、演练场景走到。
    部分 = 自检（FAST 每条 + 出片守门自检）/ 主（执行效应演练全部）/ 声（执行效应声音演练全部）"""
    import coverage
    d = tempfile.mkdtemp(prefix='门变异覆盖_'); site = f'{d}/site'; data = f'{d}/data'; os.makedirs(site); os.makedirs(data)
    open(f'{site}/sitecustomize.py', 'w').write(SITE)
    env = {**os.environ, 'PYTHONPATH': site + os.pathsep + os.environ.get('PYTHONPATH', ''), '门变异覆盖': data}
    sys.path.insert(0, T); import 规则执行核查 as R
    if 部分 == '自检':
        for i, c in enumerate(R.FAST):
            subprocess.run(['python3', f'{T}/{c[0]}', *c[1:]], cwd=T, env={**env, '门变异标签': f'F{i}'}, capture_output=True, timeout=1800)
        if os.path.exists('make_video.py'): subprocess.run(['python3', f'{T}/出片守门自检.py'], env={**env, '门变异标签': 'G'}, capture_output=True, timeout=5400)
    else:
        prog = '执行效应演练.py' if 部分 == '主' else '执行效应声音演练.py'
        r = subprocess.run(['python3', '-c', f"import sys;sys.path.insert(0,{T!r});import 规则执行核查 as R;R.印章有效=lambda p:True;import runpy;sys.argv=[{prog!r}];runpy.run_path({T + '/' + prog!r},run_name='__main__')"],
                           env={**env, '门变异标签': 部分}, capture_output=True, text=True, timeout=8000)
        print((r.stdout + r.stderr)[-600:])
    gates = {}
    for rel in 入口文件():
        if rel.endswith('.py'):
            for g in 列门(rel, open(f'{T}/{rel}').read()): gates.setdefault(rel, {})[g[1]] = 门号(g)
    hit = {}
    for f in os.listdir(data):
        cd = coverage.CoverageData(basename=f'{data}/{f}'); cd.read(); tag = f.rsplit('.', 1)[0]
        for mf in cd.measured_files():
            m = re.search(r'/视频/工具/(.+)$', mf); rel = m.group(1) if m else os.path.basename(mf)   # 出片程序在工作目录里的副本（make_video.py 等）按文件名认
            if rel not in gates: continue
            for ln in cd.lines(mf) or []:
                k = gates[rel].get(ln)
                if k: hit.setdefault(k, set()).add(tag)
    json.dump({'部分': 部分, '全集': sorted(x for g in gates.values() for x in g.values()), '门': {k: sorted(v) for k, v in hit.items()}}, open(out, 'w'), ensure_ascii=False, indent=0)
    shutil.rmtree(d, ignore_errors=True); print(f'门变异覆盖（{部分}）：{len(hit)} 道 .py 门被走到，写进 {out}')
def 探测命令(M, 全, rel, 门=None):
    """.sh：本文件相关的自检（流程自检真跑每道门）。.py 且有覆盖图：只跑走到这道门的自检、演练场景；没覆盖图：相关自检"""
    tool = f'{M}/视频/工具'; sys.path.insert(0, T); import 规则执行核查 as R, 执行效应演练 as Y, 执行效应声音演练 as S
    图 = json.load(open(覆盖图)) if os.path.exists(覆盖图) else {}
    if 是sh(rel) or 门 is None or 门 not in set(图.get('全集', [])):   # 覆盖图以后新加、改过的门：先用相关自检查，下次全量覆盖再补
        cmds, sids = 相关(rel)
        if 是sh(rel) and ['流程自检.py'] not in cmds: cmds = cmds + [['流程自检.py']]   # .sh 型门固定带 流程自检（sh门真跑 真跑每道门；pre-commit 没后缀闭包认不到，G79 交接③）
        return [['python3', f'{tool}/{c[0]}', *c[1:]] for c in cmds]
    tags = 图['门'].get(门, []); fs = R.FAST
    cs = [['python3', f'{tool}/{fs[int(t[1:].split("|")[0])][0]}', *fs[int(t[1:].split("|")[0])][1:]] for t in sorted({t.split('|')[0] for t in tags if re.match(r'F\d+$', t.split('|')[0])}, key=lambda x: int(x[1:]))]
    if any(t.startswith('G|') for t in tags): cs.append(['python3', f'{tool}/出片守门自检.py'])
    ids = {s[0] for s in Y.场景} | {s[0] for s in Y.仓库场景}
    主 = sorted({x for t in tags if t.startswith('主|') for x in [re.sub(r'^(演练_)?(原样)?(仓库_)?', '', t[2:])] if x in ids})   # 工作目录名 演练_仓库_<场景>、演练_<场景>
    声 = sorted({sid for t in tags if t.startswith('声|') for sid in [s[0] for s in S.声音场景] if re.sub(r'^演练_声_|_video$', '', t[2:]) == sid})
    if not cs and not 主 and not 声 and any(t.startswith('声|') for t in tags): return [['待声音归属']]   # 只有声音演练走到、归属不到场景（旧覆盖图）：下次覆盖再测
    胶 = "import sys;sys.path.insert(0,{tool!r});import 规则执行核查 as R;R.印章有效=lambda p:True;import runpy;sys.argv=[{p!r}]+{a!r};runpy.run_path({tool!r}+'/'+{p!r},run_name='__main__')"
    if 全 and 主: cs.append(['python3', '-c', 胶.format(tool=tool, p='执行效应演练.py', a=主)])
    if 全 and 声: cs.append(['python3', '-c', 胶.format(tool=tool, p='执行效应声音演练.py', a=声)])
    return cs
def 私工作区(M, rel, txt):
    """演练把镜像写在工作目录的上一级：每个变异一个私有工作目录（链接真工作目录；被拆的文件若是出片程序，写真副本）"""
    W = f'{M}_w/w'; os.makedirs(W); up = os.path.dirname(os.path.abspath('.'))
    for x in os.listdir(up):   # 工作目录的兄弟（../tts 配音模型等）也要在：出片程序按 ../tts 找模型（G79 交接②：出片守门自检在私有工作目录里 NoSuchFile）
        if x != os.path.basename(os.path.abspath('.')) and not x.startswith(('演练_', '守门自检', '门变异_')) and not os.path.exists(f'{M}_w/{x}'): os.symlink(f'{up}/{x}', f'{M}_w/{x}')
    for x in os.listdir('.'):
        if x.startswith('演练_'): continue
        if txt is not None and x == os.path.basename(rel): open(f'{W}/{x}', 'w').write(txt)
        else: os.symlink(os.path.abspath(x), f'{W}/{x}')
    return W
def 探测(M, cs, rel, txt=None, 略=()):
    """[(第几个探测, 摘要)]：退出码非 0 的探测（略 = 原样就不过的，不算）"""
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}; env['CLAUDE_PROJECT_DIR'] = M; out = []
    for i, c in enumerate(cs):
        if i in 略: continue
        c = [x.replace('{M}', M) for x in c]; yl = '执行效应' in ' '.join(c) or '出片守门自检' in ' '.join(c)
        wd = 私工作区(M, rel, txt) if yl else f'{M}/视频/工具'
        try:
            r = subprocess.run(c, capture_output=True, text=True, cwd=wd, env=env, timeout=3600)
            if r.returncode != 0:
                ls = [l.strip() for l in (r.stdout + r.stderr).splitlines() if re.search(r'✘|【|Error|失灵|没抓到', l)]
                out.append((i, (re.search(r'([\w一-龥]+\.py)', ' '.join(c)) or [''])[0] + '：' + (ls[0] if ls else (r.stdout + r.stderr).strip()[-100:])[:150]))
        except subprocess.TimeoutExpired: out.append((i, '探测超时（算报出）'))
        finally: shutil.rmtree(f'{M}_w', ignore_errors=True)
        if out: break
    return out
def _并行(探, 并行):
    """K44：探测里有演练（执行效应演练、声音演练）的，一份就占满 GitHub 机器，并行几份 runner 被关、结果全丢：一次只跑一道门"""
    return 1 if any('执行效应' in ' '.join(c) for cs in 探.values() for c in cs) else 并行
def 镜(files, root, name):
    sys.path.insert(0, T); import 演练镜像 as J
    return J.镜像(f'{root}/{name}', files)
def 跑(rels, 全=False, 并行=4, 底=None, 只门=None, 分片=None):
    """返回 [(门, 结论, 摘要)]：结论 = 发现 / 漏洞 / 死门 / 没人走到；底 = 额外替换进镜像的文件（K37 证明用旧版程序）"""
    底 = dict(底 or {}); root = tempfile.mkdtemp(prefix='门变异_'); 镜底 = {f'视频/工具/{k}': v for k, v in 底.items()}
    try:
        jobs = []
        for rel in rels:
            txt = 底.get(rel) or open(f'{T}/{rel}').read()
            jobs += [(rel, txt, g) for g in 列门(rel, txt) if not 只门 or 门号(g) in 只门]
        if 分片: i, n = 分片; jobs = jobs[i - 1::n]
        R0 = root + '/原样'; 探 = {}
        for rel, txt, g in jobs: 探[门号(g)] = [[x.replace(R0, '{M}') for x in c] for c in 探测命令(R0, 全, rel, 门号(g))]
        坏 = set(); M0 = 镜(镜底, root, '原样')
        for c in {json.dumps(c) for cs in 探.values() for c in cs if c != ['待声音归属']}:   # 原样先跑一遍：原样就不过的探测不算
            b = 探测(M0, [[x.replace('{M}', M0) for x in json.loads(c)]], 'x.py')
            if b: 坏.add(c); print(f'  原样就不过、不算：{b[0][1][:110]}')
        shutil.rmtree(M0, ignore_errors=True)
        def one(j):
            rel, txt, g = j
            if g[4]: return g, '死门', '门写在注释后面（|| stop 被 # 吞掉，K37）'
            if 探[门号(g)] == [['待声音归属']]: return g, '待声音归属', '只有声音演练走到，覆盖图归属不到场景'
            cs = [c for c in 探[门号(g)] if json.dumps(c) not in 坏]
            if not cs: return g, '没人走到', '没有任何自检、演练场景走到这道门'
            k = re.sub(r'\W', '_', 门号(g))[-60:]; mt = 变异(rel, txt, g); M = 镜({**镜底, f'视频/工具/{rel}': mt}, root, k)
            hit = 探测(M, cs, rel, mt); shutil.rmtree(M, ignore_errors=True)
            return g, ('发现' if hit else '漏洞'), (hit[0][1] if hit else '')
        with ThreadPoolExecutor(_并行(探, 并行)) as ex: return list(ex.map(one, jobs))
    finally: shutil.rmtree(root, ignore_errors=True)


# ---------- 清单、基线 ----------
def 现行门():
    return {门号(g): g for rel in 入口文件() for g in 列门(rel, open(f'{T}/{rel}').read())}
def 写清单(res):
    holes = [(g, c, m) for g, c, m in res if c not in ('发现',)]
    n = {}
    for g, c, _ in res: n[c] = n.get(c, 0) + 1
    L = ['# 门变异清单（门变异.py --合并结果 生成，不要手改；G79）', '',
         f'门 {len(res)} 道：' + '，'.join(f'{k} {v}' for k, v in sorted(n.items())) + '。漏洞 = 拆了没有任何探测报出；未测 = 还没有变异结果（算漏洞、进基线）；没人走到 = 没有任何自检、演练场景走到这道门；死门 = 门写在注释后面。', '',
         '## 漏洞（每个补一个演练场景或自检，补完重跑必须“发现”；基线只许减少）', '', '| 门号 | 文件:行 | 这道门 | 结论 |', '|---|---|---|---|']
    L += [f'| {门号(g)} | {g[0]}:{g[1]} | `{g[3][:80].replace("|", "¦").replace("`", "")}` | {c} |' for g, c, _ in sorted(holes, key=lambda x: (x[0][0], x[0][1]))]
    L += ['', '## 门全集（记录时的现行门；门改了、新加了，下次全量重跑）', '', '```'] + sorted(门号(g) for g, _, _ in res) + ['```', '']
    open(清单, 'w').write('\n'.join(L))
    hs = sorted(门号(g) for g, _, _ in holes); b = json.load(open(BASE))['漏洞'] if os.path.exists(BASE) else None
    if b is None or len(hs) <= len(b): json.dump({'说明': '门变异漏洞基线（G79）：只许减少，目标 0；规则执行核查查清单漏洞数不比它多', '漏洞': hs}, open(BASE, 'w'), ensure_ascii=False, indent=1)
    return hs
def 查基线():
    """规则执行核查用：(问题, 提示)。漏洞比基线多就停；门改了、新加了只提示（全量放 GitHub 重跑；.sh 新门由 流程自检 sh门真跑 当场查）"""
    if not os.path.exists(BASE) or not os.path.exists(清单): return ['没有门变异清单/基线（G79）：GitHub 跑 门变异 覆盖、分片，再 python3 视频/工具/门变异.py --合并结果 …'], []
    b = json.load(open(BASE))['漏洞']; t = open(清单).read(); e = []
    hs = re.findall(r'^\| (\S+\|[0-9a-f]{10}\|\d+) \|', t, re.M)
    if len(hs) > len(b): e.append(f'门变异漏洞变多（{len(hs)} > 基线 {len(b)}）：新漏洞补演练场景或自检，补完重跑必须“发现”')
    nw = [x for x in 新门(t) if not 是sh(x.split('|')[0])]
    return e, ([f'门变异：{len(nw)} 道 .py 门是清单记录以后新加或改过的（{"、".join(sorted({x.split("|")[0] for x in nw}))[:80]}），找时间 GitHub 全量重跑'] if nw else [])
def 新门(t=None):
    t = t if t is not None else (open(清单).read() if os.path.exists(清单) else '')
    m = re.search(r'## 门全集[^\n]*\n\n```\n(.*?)```', t, re.S); old = set(m.group(1).split()) if m else set()
    return sorted(set(现行门()) - old)


# ---------- 自检 ----------
def 自检():
    f = []
    k37 = '#!/bin/bash\nstop() { echo x; exit 1; }\npython3 $T/生成文本.py $no > a 2>&1   # 守则17 || { tail a; stop "对照文本不通过"; }\nx || stop "好门"\n'
    gs = 门_sh(k37)
    if [g[3] for g in gs] != [True, False]: f.append(f'没抓到：K37 那一行（|| stop 在注释后）没列成死门，或好门被当死门：{gs}')
    if 门_sh('stop() { echo "【停止】$1"; exit 1; }\n'): f.append('误报：stop() 定义当成了门')
    if 门_sh('echo "x || stop y"  # 说明 || stop\n'): pass
    m = 变异_sh('a || stop "x"\n', 1, 5)
    if m != 'a || : stop "x"\n': f.append(f'.sh 拆门不对：{m!r}')
    if subprocess.run(['bash', '-c', 'stop() { exit 1; }; false || : stop "x"; echo 走过了'], capture_output=True, text=True).stdout.strip() != '走过了': f.append('.sh 拆门后门还在')
    py = 'import sys\nfails = []\nif len(sys.argv) > 5 and "中文" in "中文":\n    fails.append("停")\nif x:\n    print(1)\n'
    gp = 门_py(py)
    if len(gp) != 1 or gp[0][0] != 3: f.append(f'.py 列门不对（只该列第 3 行的 if）：{gp}')
    else:
        mp = 变异_py(py, gp[0][1]); ns = {'sys': sys}
        if 'False and (len(sys.argv) > 5 and "中文" in "中文")' not in mp: f.append(f'.py 拆门不对（中文字节偏移？）：{mp!r}')
        try: ast.parse(mp)
        except SyntaxError as e: f.append(f'.py 拆门后语法错：{e}')
    pf = "import sys\na = sys.argv[1:]\nif '--自检' in a:\n    sys.exit(main())\nif __name__ == '__main__':\n    sys.exit(main())\nif a and a[0] == '--查': sys.exit(查())\nif bad:\n    sys.exit(1)\n"
    pr = "res = []; out = []\nif t:\n    res.append((f'把 {w} 挪', ok))\nif d:\n    out += [(c, k, x)]\nif bad:\n    res.append(f'不通过：{x}')\nif g:\n    res.append(('真仓库没被碰', False, why))\nif h:\n    out.append((i, '中文变量展开（bash 不认）'))\n"
    if [g[0] for g in 门_py(pr)] != [6, 8, 10]: f.append(f'收普通结果的 res.append((标签, 布尔))、out += [(元组)] 被当成门，或记说明文字的真门漏了：{门_py(pr)}')
    if [g[0] for g in 门_py(pf)] != [8]: f.append(f'派发 if（按命令行参数、__name__ 分派）被当成门，或真门漏了（G79 交接①）：{门_py(pf)}')
    py2 = 'if (a and\n        b):\n    sys.exit(1)\n'
    try: ast.parse(变异_py(py2, 门_py(py2)[0][1]))
    except Exception as e: f.append(f'.py 多行判断拆门坏了：{e!r}')
    if _并行({'a': [['python3', '-c', 'runpy.run_path("x/执行效应声音演练.py")']]}, 4) != 1 or _并行({'a': [['python3', 'x/踩坑核查.py']]}, 4) != 4: f.append('K44：带演练探测的门没降成一次一道，或不带演练的也降了')
    global BASE, 清单   # 清单、基线：漏洞比基线多必停，一样多放行
    ob, oq = BASE, 清单; d = tempfile.mkdtemp(); BASE, 清单 = f'{d}/b.json', f'{d}/q.md'
    try:
        g1, g2 = ('a.py', 3, (3, 3, 3, 4), 'if x:', False), ('a.py', 9, (9, 3, 9, 4), 'if y:', False)
        写清单([(g1, '漏洞', ''), (g2, '发现', '')])
        if 查基线()[0]: f.append('误报：漏洞和基线一样多也停（G79）')
        写清单([(g1, '漏洞', ''), (g2, '没人走到', '')])
        if not 查基线()[0]: f.append('没抓到：门变异漏洞比基线多（G79）')
    finally: BASE, 清单 = ob, oq; shutil.rmtree(d, ignore_errors=True)
    return f


def main():
    a = sys.argv[1:]
    if '--自检' in a:
        f = 自检()
        print('门变异自检：' + ('通过（K37 注释吞 || stop 列为死门、stop() 定义不当门、.sh/.py 拆门字留着动作没了、中文和多行判断拆门语法对）' if not f else '【失灵】' + '；'.join(f)))
        return 1 if f else 0
    if '--查基线' in a:
        e, w = 查基线(); print('门变异基线：' + ('通过' if not e else '【停止】' + '；'.join(e)) + ''.join('；提示：' + x for x in w)); return 1 if e else 0
    if '--覆盖' in a:
        i = a.index('--覆盖'); 覆盖(a[i + 1], a[i + 2]); return 0
    if '--合并覆盖' in a:   # 三份覆盖（自检、主、声）并成 门变异覆盖.json
        m, 全 = {}, set()
        for f in [x for x in a if x.endswith('.json')]:
            j = json.load(open(f)); 全 |= set(j.get('全集', []))
            if '全集' not in j:   # v1 覆盖没记全集：按 HEAD（覆盖跑的那一版）的入口文件重算
                for rel in 入口文件():
                    r = subprocess.run(['git', '-C', P, 'show', f'HEAD:视频/工具/{rel}'], capture_output=True, text=True)
                    if r.returncode == 0 and rel.endswith('.py'): 全 |= {门号(g) for g in 列门(rel, r.stdout)}
            for k, v in j['门'].items(): m.setdefault(k, set()).update(v)
        json.dump({'说明': '每道 .py 门被哪些探测走到（门变异.py --覆盖，GitHub 跑）', '全集': sorted(全), '门': {k: sorted(v) for k, v in sorted(m.items())}}, open(覆盖图, 'w'), ensure_ascii=False, indent=0)
        print(f'覆盖图：{len(m)} 道门'); return 0
    if '--合并结果' in a:   # GitHub 各分片的结果并起来写清单
        res = {}; 现 = 现行门(); 旧 = 0
        for f in [x for x in a if x.endswith('.json')]:   # 后面的文件盖前面的（补完漏洞在本地重跑的结果放最后）
            for k, rel, ln, t, c, msg in json.load(open(f)):
                if k not in 现: 旧 += 1; continue   # 跑完以后不再算门的（列门规则收紧了）、改过的：不进清单
                res[k] = ((rel, 现[k][1], 现[k][2], t, c == '死门'), c, msg)   # .sh 门号带 g[2]（同一行第几个），写 None 就永远对不上现行门
        if '--未测入基线' in a:   # 主会话 2026-10-27：没结果的门记“未测”进清单和基线（基线只许减少，以后补跑成“发现”才减）
            for k, g in 现.items():
                if k not in res: res[k] = (g, '未测', '')
        res = list(res.values())
        if 旧: print(f'  {旧} 条结果的门现在不算门或已改，不进清单')
        hs = 写清单(res); print(f'门变异清单：{len(res)} 道门，漏洞 {len(hs)}'); return 0
    if '--分片表' in a:   # 按覆盖图：每个文件走到的门数 / 每片约 10 道 → 请求行的 文件@i@n 列表（没走到的门不用跑，一片带完）
        图 = json.load(open(覆盖图)) if os.path.exists(覆盖图) else {'门': {}}; out = []
        for rel in 入口文件():
            gs = 列门(rel, open(f'{T}/{rel}').read()); k = sum(1 for g in gs if 门号(g) in 图['门'] or 是sh(rel) or 门号(g) not in set(图.get('全集', [])))
            if not gs: continue
            演 = sum(1 for g in gs if any('执行效应' in ' '.join(c) for c in 探测命令('/M', True, rel, 门号(g))))   # K44：带演练的门一片最多 2 道（演练只能一份一份跑）
            n = max(1, -(-k // 10), -(-演 // 2)); out += [f'{rel}@{i}@{n}' for i in range(1, n + 1)]
        print(' '.join(out)); return 0
    if '--列' in a:
        g = 现行门(); n = {}
        for x in g.values(): n[x[0]] = n.get(x[0], 0) + 1
        print(f'门 {len(g)} 道：' + '，'.join(f'{k} {v}' for k, v in sorted(n.items()))); return 0
    if '--K37' in a:   # A.5 小规模证明：K37 修好前的 定稿流水线.sh + 流程自检.py 放进镜像，那一行必须列为漏洞
        old = {x: subprocess.run(['git', '-C', '/home/user/literate-enigma', 'show', f'3ae8fa6^:视频/工具/{x}'], capture_output=True, text=True).stdout for x in ('定稿流水线.sh', '流程自检.py')}
        res = 跑(['定稿流水线.sh'], 底=old)
    else:
        files = [x for x in a if not x.startswith('--')] or (入口文件() if '--全量' in a else [])
        if not files:
            print('门变异：没指定文件（--全量 跑全部入口，放 GitHub）'); return 0
        fp = next((x.split('=', 1)[1] for x in a if x.startswith('--分片=')), '')
        rp0 = next((x.split('=', 1)[1] for x in a if x.startswith('--结果=')), '')
        if rp0: json.dump([], open(rp0, 'w'))   # 先写空结果：这一片 0 道门或中途出错，写回步也有文件（G79 交接③）
        res = 跑(files, 全='--全' in a, 分片=tuple(map(int, fp.split('/'))) if fp else None)
    rp = next((x.split('=', 1)[1] for x in a if x.startswith('--结果=')), '')
    if rp: json.dump([[门号(g), g[0], g[1], g[3], c, m] for g, c, m in res], open(rp, 'w'), ensure_ascii=False, indent=0)
    for g, c, m in res:
        if c != '发现': print(f'✘ {c} {g[0]}:{g[1]} {g[3][:70]}')
    holes = [r for r in res if r[1] != '发现']
    print(f'门变异：{len(res)} 道门，拆掉后被发现 {len(res) - len(holes)}，漏洞 {len(holes)}')
    if '--写清单' in a: 写清单(res)
    return 1 if holes and '--写清单' not in a and not rp else 0


if __name__ == '__main__':
    sys.exit(main())
