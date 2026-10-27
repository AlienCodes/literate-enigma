#!/usr/bin/env python3
"""演练镜像（执行效应演练、执行效应声音演练共用）：演练样本冻结（用户 2026-10-24：“你专门另外开这么一个对话去演练，你别在这儿演练，
我着急要用这个24的这个稿子”）。
坑：演练拿 视频/脚本/24.json 等现稿当样本，24 一改稿，注入点对不上，改稿会话被演练拖住（重写演练、重演 15 分钟）。
做法：演练用到的脚本、文章、制作记录、对照文本、初稿程序数据一律取 工具/演练样本/ 里的冻结拷贝（取自 commit a45a66a3，印章有效的那版），
镜像里这些路径都指向冻结拷贝；演练程序一处读了现稿就停（查读现稿）。改稿只改现稿，演练、印章、规则执行核查都不受影响；
演练只在改门的会话里做。冻结拷贝要换版本：python3 演练镜像.py --冻结 <commit>（在仓库里跑），然后整套重演。
      python3 演练镜像.py --自检   造错自检（规则执行核查每次当场跑）"""
import os, sys, json, re, shutil, subprocess, hashlib, tempfile
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
样本根 = f'{T}/演练样本'; 清单 = f'{样本根}/清单.json'
冻结整目录 = ('视频/脚本', '新版定稿', '视频/制作记录')                 # 整个目录都用冻结拷贝（现稿里新出现的文件也看不见）
冻结单个 = ('视频/对照文本/23-', '视频/对照文本/24-', '视频/工具/原稿重点词.json', '视频/工具/初稿生成/gen23.py', '视频/工具/初稿生成/gen24.py')
指纹 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else '无'


def 样(rel): return f'{样本根}/{rel}'
def 读样(rel, b=False): return open(样(rel), 'rb' if b else 'r').read()
def _全(rel): return any(rel == d or rel.startswith(d + '/') for d in 冻结整目录)
def 样本文件():
    out = []
    for dp, dn, fn in os.walk(样本根):
        out += [os.path.relpath(f'{dp}/{x}', 样本根) for x in fn if f'{dp}/{x}' != 清单]
    return sorted(out)


def 冻结(commit, repo=P):
    """从 repo 的 commit 取冻结拷贝（只在改门的会话里用；换了版本要整套重演）"""
    ls = subprocess.run(['git', '-c', 'core.quotepath=off', 'ls-tree', '-r', '--name-only', commit], cwd=repo, capture_output=True, text=True, check=True).stdout.splitlines()
    take = [x for x in ls if _全(x) or any(x.startswith(s) for s in 冻结单个)]
    shutil.rmtree(样本根, ignore_errors=True)
    for x in take:
        os.makedirs(os.path.dirname(样(x)), exist_ok=True)
        open(样(x), 'wb').write(subprocess.run(['git', 'show', f'{commit}:{x}'], cwd=repo, capture_output=True, check=True).stdout)
    json.dump({'_来源': commit, **{x: 指纹(样(x)) for x in 样本文件()}}, open(清单, 'w'), ensure_ascii=False, indent=1)
    return len(take)


def 块(d, si, k=0): return d['sentences'][si]['chunks'][k]
def _读(f, k): return f[k] if k in f else (读样(k) if os.path.isfile(样(k)) else open(f'{P}/{k}').read())   # 现稿路径一律读冻结拷贝
def _改文(f, k, old, new):
    t = _读(f, k); assert old in t, old; f[k] = t.replace(old, new, 1)
def _改json(f, k, fn):
    o = json.loads(_读(f, k)); fn(o); f[k] = json.dumps(o, ensure_ascii=False, indent=1)


def _rec(no): return f'视频/制作记录/{no}.md'
def _改行(f, no, i, v): f[_rec(no)] = re.sub(rf'^(\| *{i} *\|.*\| *(?:涉及|不涉及) *\|).*\|\s*$', lambda m: m.group(1) + f' {v} |', f[_rec(no)], count=1, flags=re.M)


def 仓库底稿(no, entry=''):
    """镜像里要改的文件的底稿（一律取冻结拷贝；篇号 25 用 24 的副本；G6/C3/C4 先填合格的固定格式，原样就不报这一格）"""
    src = '24' if no == '25' else no
    f = {_rec(no): 读样(_rec(src)), f'视频/脚本/{no}.json': 读样(f'视频/脚本/{src}.json')}
    for i in ('G6', 'C3', 'C4'): _改行(f, no, i, '本篇无：演练底稿，用户没有提互相冲突的要求，没有插话，没有多版本设计稿')
    f['.claude/settings.json'] = open(f'{P}/.claude/settings.json').read() if os.path.exists(f'{P}/.claude/settings.json') else open('/home/user/literate-enigma/.claude/settings.json').read()   # 钩子配置
    sys.path.insert(0, T); import 重查记录 as RC   # 底稿：全篇重查都算通过（现行程序、存的视频、冻结脚本），注入的改动才会“欠着”
    fp = RC.程序指纹(); f['视频/工具/全篇重查通过.json'] = json.dumps({'篇': {n: f'{fp}-{RC._sha(p)}-{RC._sha(样(f"视频/脚本/{n}.json")) if os.path.exists(样(f"视频/脚本/{n}.json")) else "无"}' for n, p in RC.已出片().items()}}, ensure_ascii=False)
    if entry == '生成文本':   # 生成文本 写 对照文本/、脚本/、已发版本/：这些做成副本
        for x in ('docx', 'html', 'pdf'): f[f'视频/对照文本/{no}-文本.{x}'] = 读样(f'视频/对照文本/{no}-文本.{x}', True)
        k = f'视频/脚本/已发版本/{no}.json'; f[k] = 读样(k) if os.path.exists(样(k)) else f[f'视频/脚本/{no}.json']
    if entry == '归档':   # 归档会写 README、删草稿/试听：这些目录做成真目录（里面是链接，删的只是链接）
        f['最终版4K视频/README.md'] = open(f'{P}/最终版4K视频/README.md').read(); f['视频/视频/草稿1080p/.演练'] = ''; f['视频/试听/.演练'] = ''
    return _工具副本(f)


def 镜像(M, files):
    """M = 仓库镜像根：冻结的路径指向 演练样本/，其余符号链接到真仓库，files 里的写成副本（父目录变成真目录）"""
    shutil.rmtree(M, ignore_errors=True); os.makedirs(M); files = _工具副本(files)
    real = {'/'.join(k.split('/')[:i]) for k in files for i in range(1, len(k.split('/')))}
    sdirs = {'/'.join(k.split('/')[:i]) for k in 样本文件() for i in range(1, len(k.split('/')))}
    def fill(rel):
        base = 样(rel) if _全(rel) else (f'{P}/{rel}' if rel else P)
        for x in sorted(os.listdir(base)):
            r = f'{rel}/{x}' if rel else x
            if x in ('.git', '__pycache__') or r in files: continue
            if r in real: os.makedirs(f'{M}/{r}'); fill(r)
            elif _全(r) or os.path.isfile(样(r)): (shutil.copytree if os.path.isdir(样(r)) else shutil.copy)(样(r), f'{M}/{r}')   # 复制、不链接：镜像里的程序（如 补对照记录）写进去也改不到冻结拷贝
            elif r in sdirs: os.makedirs(f'{M}/{r}'); fill(r)
            else: os.symlink(f'{P}/{r}', f'{M}/{r}')
    fill('')
    for k, t in files.items():
        os.makedirs(os.path.dirname(f'{M}/{k}'), exist_ok=True)
        if isinstance(t, tuple): os.symlink(t[1], f'{M}/{k}')          # ('链接', 真文件)：只读的大文件（视频）
        elif isinstance(t, bytes): open(f'{M}/{k}', 'wb').write(t)
        else: open(f'{M}/{k}', 'w').write(t)
    return M


def _工具副本(files):
    """镜像里的 视频/工具 整份复制（fonts、历史版本、演练样本 只读，链接）；工具里的现稿数据（原稿重点词、初稿程序）用冻结拷贝"""
    out = dict(files)
    for dp, dn, fn in os.walk(T):
        dn[:] = [x for x in dn if x not in ('fonts', '历史版本', '__pycache__', '演练样本')]
        for x in fn:
            k = os.path.relpath(f'{dp}/{x}', P)
            if k not in out: out[k] = 读样(k, True) if k.startswith('视频/工具/') and os.path.isfile(样(k)) else open(f'{dp}/{x}', 'rb').read()
    for k in ('视频/制作记录/门变异清单.md',):   # G79：机制文件不是样本，放在冻结的 制作记录 里也用现行的（否则演练里永远“还没有门变异清单”）
        if k not in out and os.path.isfile(f'{P}/{k}'): out[k] = open(f'{P}/{k}', 'rb').read()
    for x in ('fonts', '历史版本', '演练样本'): out.setdefault(f'视频/工具/{x}', ('链接', f'{T}/{x}'))
    return out


def 工作区(W, root, sid, no, d, 改正=None):
    ws = f'{root}/演练_{sid}'; shutil.rmtree(ws, ignore_errors=True); os.makedirs(f'{ws}/scripts')   # 与工作目录并排（出片程序按 ../tts 找模型）
    for x in os.listdir(W):
        if x == 'scripts' or x.startswith('work_') or x.endswith(('.mp4', '.mp3', '.wav', '.json')): continue
        os.symlink(f'{W}/{x}', f'{ws}/{x}')
    json.dump(d, open(f'{ws}/scripts/{no}.json', 'w'), ensure_ascii=False, indent=1)
    if 改正 is not None: json.dump(改正, open(f'{ws}/读音改正.json', 'w'), ensure_ascii=False, indent=1)
    return ws


def _git状态(): return subprocess.run(['git', '-c', 'core.quotepath=off', 'status', '--porcelain'], cwd=P, capture_output=True, text=True).stdout


# —— G29：演练合成的配音缓存要清干净。出片程序把用到的缓存拷进 make_video.py 写死的 _REPO_CACHE（postgraduate-vocabulary），
#    从 literate-enigma 跑演练时只清了本仓库，那边留下一堆演练缓存（2026-10-24）。开跑前对两处拍快照，结束删掉新出现的
def 缓存目录(t=T):
    ds = {os.path.realpath(f'{os.path.dirname(t)}/配音缓存')}
    m = re.search(r"^_REPO_CACHE='([^']+)'", open(f'{t}/make_video.py').read(), re.M)
    if m: ds.add(os.path.realpath(m.group(1)))
    return sorted(d for d in ds if os.path.isdir(d))
def 缓存快照(ds=None): return {d: set(os.listdir(d)) for d in (缓存目录() if ds is None else ds)}
def 新缓存(s0): return [f'{d}/{x}' for d, names in s0.items() for x in sorted(set(os.listdir(d)) - names)]
def 清新缓存(s0):
    for p in 新缓存(s0):
        if p.endswith(('.pkl', '.pkl.单线程')) or os.path.basename(p).startswith('调平_'): os.remove(p)   # G72：单线程新条目的 .单线程 标记也清（2026-10-26 声音演练留下 7 个，真仓库被碰）   # G53：调平缓存（G51）也要清，以前只清 .pkl，演练的调平缓存留在仓库、被推送进 git
    return 新缓存(s0)


# —— 门：演练程序一处读了现稿就停（执行效应演练、声音演练开跑前调；规则执行核查当场跑 --自检）
_现稿 = [r'\{V\}/' + '(?:脚本|制作记录|对照文本)', r'\{Y\.V\}/' + '(?:脚本|制作记录|对照文本)', r'\{P\}/' + '新版定稿', r'dirname\(V\)\}/' + '新版定稿', r'\{W\}/' + 'scripts',
        r"(?:open|load|指纹)\(f?'" + 'scripts/', r'\{T\}/' + '(?:原稿重点词|初稿生成/gen)', 'postgraduate-vocabulary/' + '新版定稿']
演练程序 = ('执行效应演练.py', '执行效应声音演练.py', '演练镜像.py', '初稿生成/核对.py')
def 查读现稿(texts=None):
    texts = texts if texts is not None else {x: open(f'{T}/{x}').read() for x in 演练程序}
    return [f'{n} 第{i}行读了现稿（演练只许读 工具/演练样本/ 的冻结拷贝）：{l.strip()[:70]}' for n, t in texts.items() for i, l in enumerate(t.splitlines(), 1)
            if not l.lstrip().startswith('#') and any(re.search(p, l) for p in _现稿)]
def 查样本():
    try: c = json.load(open(清单))
    except Exception: return ['演练样本/清单.json 没有：先 python3 演练镜像.py --冻结 <commit>']
    fs = 样本文件(); bad = [x for x in fs if c.get(x) != 指纹(样(x))] + [x for x in c if not x.startswith('_') and x not in fs]
    return [f'演练样本被改过（冻结拷贝不许动，换版本用 --冻结 并整套重演）：{"、".join(bad[:5])}'] if bad else []


def 自检():
    f = []
    if 查读现稿(): f.append('误报或真有：' + 查读现稿()[0])
    for bad in ("    d0 = json.load(open(f'{W}/" + "scripts/24.json'))", "    rec = open(f'{V}/" + "制作记录/24.md').read()", "    x = glob.glob(f'{P}/" + "新版定稿/24-*.md')", "    a = open(f'{os.path.dirname(V)}/" + "新版定稿/24.md')"):
        if not 查读现稿({'造错.py': bad}): f.append(f'没抓到：演练程序读现稿（{bad.strip()[:30]}）')
    f += 查样本()
    root = tempfile.mkdtemp(prefix='演练镜像自检_')
    try:   # 镜像里现稿路径必须落在冻结拷贝上：现稿改一个字（24.json），镜像和底稿都看不见
        M = 镜像(f'{root}/M', {})
        for k in ('视频/脚本/24.json', '新版定稿/' + os.path.basename(next(iter(__import__('glob').glob(样('新版定稿/24-*.md'))))), '视频/制作记录/24.md', '视频/工具/原稿重点词.json', '视频/对照文本/24-文本.docx'):
            p = os.path.realpath(f'{M}/{k}')
            if not (p.startswith(os.path.realpath(样本根)) or (os.path.isfile(p) and os.path.isfile(样(k)) and 指纹(p) == 指纹(样(k)))): f.append(f'没抓到：镜像里的 {k} 不是冻结拷贝')
        if 仓库底稿('24')['视频/脚本/24.json'] != 读样('视频/脚本/24.json'): f.append('没抓到：底稿不是冻结拷贝')
        h = 指纹(样('视频/制作记录/24.md')); open(f'{M}/视频/制作记录/24.md', 'a').write('\n自检写入\n')   # 镜像里的程序往制作记录补行，不得改到冻结拷贝
        if 指纹(样('视频/制作记录/24.md')) != h: f.append('没抓到：镜像里写制作记录改到了冻结拷贝')
    finally: shutil.rmtree(root, ignore_errors=True)
    c = tempfile.mkdtemp(prefix='演练缓存自检_')   # G29：两处缓存目录拍快照，演练新出的删掉、原有的留着；漏清必须报出
    try:
        a, b = f'{c}/literate', f'{c}/pv'; os.makedirs(a); os.makedirs(b); open(f'{a}/旧.pkl', 'w').write('x'); open(f'{b}/旧.pkl', 'w').write('x')
        s0 = 缓存快照([a, b]); open(f'{b}/演练新.pkl', 'w').write('y'); open(f'{b}/调平_演练新.json', 'w').write('{}'); open(f'{b}/演练新.pkl.单线程', 'w').write('h')
        if not 新缓存(s0): f.append('没抓到：演练在另一个仓库留下的配音缓存（G29）')
        if 清新缓存(s0) or os.path.exists(f'{b}/演练新.pkl'): f.append('没清掉：演练在另一个仓库留下的配音缓存（G29）')
        if os.path.exists(f'{b}/演练新.pkl.单线程'): f.append('没清掉：演练留下的 .单线程 标记（G72：标记留在真仓库，“真仓库没被碰”报错）')
        if os.path.exists(f'{b}/调平_演练新.json'): f.append('没清掉：演练留下的调平缓存（G53：以前只清 .pkl，演练的调平缓存被推送进 git）')
        if not (os.path.exists(f'{a}/旧.pkl') and os.path.exists(f'{b}/旧.pkl')): f.append('误删：演练前就有的配音缓存（G29）')
        m = re.search(r"^_REPO_CACHE='([^']+)'", open(f'{T}/make_video.py').read(), re.M)
        if m and os.path.isdir(m.group(1)) and os.path.realpath(m.group(1)) not in 缓存目录(): f.append('没抓到：清缓存漏了出片程序写死的仓库（G29）')
    finally: shutil.rmtree(c, ignore_errors=True)
    sys.path.insert(0, T); import 同意记录追加 as TY   # 追加一条同意记录，演练印章照样有效
    o = json.load(open(TY.F)); st = TY.印(o); o['记录'].append({k: '自检追加' for k in TY.字段})
    if TY.查(o, st): f.append('误报：追加一条同意记录，演练印章就失效')
    import importlib
    for mod, lst in (('执行效应演练', '被演练'), ('执行效应声音演练', '声音被演练')):   # 印章只盖程序（和样本清单），不盖现稿
        try: L = getattr(importlib.import_module(mod), lst)
        except ImportError: continue   # 声音演练要 soundfile：没装的机器上只查主演练
        if any(x.endswith('.md') or x.startswith(('脚本', '新版定稿')) or x == '用户同意记录.json' for x in L): f.append(f'{mod} 的印章盖了现稿或同意记录')
        if '演练样本/清单.json' not in L: f.append(f'{mod} 的印章没盖演练样本清单（样本换了不重演）')
    if '执行效应演练.py' in getattr(sys.modules.get('执行效应声音演练'), '声音被演练', []): f.append('声音演练印章盖了主演练程序（主演练一改连带声音重演）')
    return ['演练镜像 自检：' + x for x in f]


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--冻结' in a: print(f'冻结 {冻结(a[a.index("--冻结") + 1])} 个文件到 {样本根}'); sys.exit(0)
    if '--自检' in a:
        e = 自检(); print('\n'.join(e) or '演练镜像 自检通过（读现稿必停、镜像只见冻结拷贝、追加同意记录印章不失效）'); sys.exit(1 if e else 0)
    e = 查读现稿() + 查样本(); print('\n'.join(e) or '演练只读冻结拷贝'); sys.exit(1 if e else 0)
