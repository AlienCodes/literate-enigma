#!/usr/bin/env python3
"""会话开工（G61 会话角色闸门 + G63 开工先读、没读不能提交）。
用户 2026-10-26 原话：“开工的时候一定要严格的知道从头到尾应该去做什么，所有的注意事项，所有的踩坑……以及虹吸效应，进化方法等等……
会话开始之前第一件事应该先去知道先去做什么……一定要保证这些事情严格的遵守。”“不要随随便便去乱发挥……一定要坚决按照指令去执行的机制”
  开工：python3 视频/工具/会话开工.py <角色> [--会话 ID] [--任务 制作记录/改门_xxx.md]
        角色：出稿 / 改稿 / 改门 / 主会话（改门要写 --任务，指向主会话交给它的改门文件）。
        打印 五条总纲 + 开工必读要点 + 步骤表（读），记下本会话角色和 开工必读.md 的指纹（~/.会话开工.json）。
  重读：python3 视频/工具/会话开工.py --重读      开工必读更新了：只打印新增的行，记下新指纹
  提交前（githooks/pre-commit 调）：没开工记录、开工必读指纹旧了 → 不许提交；
        出稿、改稿会话提交改门程序（视频/工具/ 下的 .py .sh、钩子、githooks、演练样本、规则执行表等登记表，.github/workflows、.claude/settings.json）→ 不许提交（G25）。
        合并进来的别人的改动（和远端 main 或 MERGE_HEAD 逐字节相同）不算本会话改的。
用法另有 --查（定稿流水线开头调）、--自检。"""
import os, sys, json, re, hashlib, datetime, subprocess
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
记录F = [os.path.expanduser('~/.会话开工.json')]   # 每个会话一个容器；自检换成临时文件
必读F = f'{V}/开工必读.md'
角色们 = ('出稿', '改稿', '改门', '主会话')
总纲 = [
    '① 虹吸：先想最巧、最省的办法，能交给程序的全交给程序；任何一步 30 分钟拿不出成果立刻换方法（守则2）。',
    '② token 发挥 150%：不派子代理/工作流、少调用、输出短、每篇新开会话；每个 token 都要换来成果（守则12/T29，用户 2026-10-26：“一个token，一定要发挥150%的功率”）。',
    '③ GitHub 优先：纯程序性的工作能在 GitHub 上跑就在 GitHub 上跑，不在沙盒里花 token 干等；做得不好的小程序报坑，由改门会话淘汰或进化。',
    '④ 严格按流程，不乱发挥：照 开工必读 ⑤ 步骤表一步一步用正式入口做，证据链少一步就停；觉得流程不好，写进方法复盘、报坑，由改门会话改程序（G60/G61）。',
    '⑤ 方法进化：每做完一件事回头看哪里还能更省、更好，当场改成程序，记进方法升级记录；踩过的坑绝不再踩（守则2/12/13）。',
]

# 三大主义（O，用户 2026-10-27 第五次原话：“执行主义是最重要的……还有一个就是绝对的丝滑，还有一个就是虹吸主义”）：每个会话开工第一屏，按这个顺序
三大主义 = [
    '① 执行主义（最重要）：做出来的机制都要跑起来、用上，每次都查，漏跑就停——用上核查（G83）、门变异（G79）、证据链（G60）、执行效应演练（守则19）。',
    '② 丝滑主义：流程中间不许有 bug、冲突、要重跑的地方——会话开工 环境检查（M/G90）、丝滑记录 不丝滑次数（K/G91）、GitHub 新容器彩排（L/G92）；停下不是稿子的问题当场报坑。',
    '③ 虹吸主义：程序能做的全交给程序，不花或少花 token——不派子代理、少调用、输出短、每篇新开会话（T29）；30 分钟没成果立刻换方法（守则2）。',
]
def 打印三大主义():
    print('【三大主义（每个会话开工第一屏，用户 2026-10-27）】'); [print('  ' + x) for x in 三大主义]


def 指纹(): return hashlib.sha256(open(必读F, 'rb').read()).hexdigest()[:12] if os.path.exists(必读F) else ''


def 读记录():
    try: return json.load(open(记录F[0]))
    except Exception: return None


def 打印总纲():
    print('【五条总纲（每个会话开工第一件事，用户 2026-10-26）】'); [print('  ' + x) for x in 总纲]


def 节(txt, head):
    m = re.search(rf'^## {head}[^\n]*\n[\s\S]*?(?=^## |\Z)', txt, re.M); return m.group(0).rstrip() if m else ''


模块 = {'soundfile': 'soundfile', 'numpy': 'numpy', 'imageio_ffmpeg': 'imageio-ffmpeg', 'PIL': 'pillow', 'wordfreq': 'wordfreq',
        'scipy': 'scipy', 'parselmouth': 'praat-parselmouth', 'pyloudnorm': 'pyloudnorm', 'kokoro_onnx': 'kokoro-onnx',
        'onnxruntime': 'onnxruntime', 'phonemizer': 'phonemizer', 'fitz': 'pymupdf', 'docx': 'python-docx', 'sherpa_onnx': 'sherpa-onnx'}
def 缺包(mods=None):
    import importlib.util; importlib.invalidate_caches()
    return [m for m in (mods or 模块) if importlib.util.find_spec(m) is None]
def _装(缺, mods):
    pip = [sys.executable, '-m', 'pip', 'install', '-q']
    subprocess.run(pip + ['-r', f'{T}/环境/requirements.txt'], capture_output=True)
    subprocess.run(pip + ['--break-system-packages', '-r', f'{T}/环境/requirements.txt'], capture_output=True)
    subprocess.run(pip + [mods[m] for m in 缺], capture_output=True)
def _ff():
    import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
def 环境检查(mods=None, 装=None, ff取=None):
    """M（用户 2026-10-27 丝滑主义；K42 新容器缺 soundfile/imageio_ffmpeg/wordfreq，推送三次才过）：开工先查 Python 包和 ffmpeg，
    缺了自动装（requirements.txt），装不上才停并说清缺什么"""
    mods = mods or 模块; 缺 = 缺包(mods)
    if 缺:
        print(f'【环境】缺 {"、".join(缺)}：自动装（M/K42）'); (装 or _装)(缺, mods); 缺 = 缺包(mods)
        if 缺 and 装 is None: import 丝滑; 丝滑.记('会话开工', '-', f'环境缺包，自动装不上：{缺}', '不丝滑')   # K
        if 缺: sys.exit(f'【停止】环境缺包，自动装不上：{"、".join(缺)}（手工 pip install {" ".join(mods[m] for m in 缺)}；M/K42）')
    if 'imageio_ffmpeg' in mods or ff取:
        try:
            ff = (ff取 or _ff)()
            if not os.path.exists(ff): raise FileNotFoundError(ff)
        except Exception as e: sys.exit(f'【停止】环境缺 ffmpeg（imageio_ffmpeg 找不到：{e}；M）')
    print('【环境】Python 包、ffmpeg 齐（M；work_NN 缺 a.wav 由 定稿流水线 ①前 自动重建，K36）')


def 开工(角色, 会话='', 任务=''):
    if 角色 not in 角色们: sys.exit(f'【停止】角色只能是 {"、".join(角色们)}')
    if 角色 == '改门' and not (任务 and os.path.exists(任务 if os.path.isabs(任务) else f'{V}/{任务}')):
        sys.exit('【停止】改门会话要写 --任务 制作记录/改门_xxx.md（主会话交给你的改门文件；G25：出稿、改稿会话不改门）')
    打印三大主义()   # O：第一屏
    环境检查()   # M：环境先齐，后面的用上报告、开工必读才跑得动
    打印总纲()
    r = subprocess.run(['python3', f'{T}/用上核查.py'], capture_output=True, text=True); print(r.stdout.strip())   # G83：开头先打印用上报告，读完才记指纹
    r = subprocess.run(['python3', f'{T}/开工必读.py', '--要点'], capture_output=True, text=True); print(r.stdout.strip())
    t = open(必读F).read() if os.path.exists(必读F) else ''
    s = 节(t, '⑤')
    if s: print(s)
    rec = {'角色': 角色, '会话': 会话, '任务': 任务, '开工必读指纹': 指纹(),
           '时刻': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}
    json.dump(rec, open(记录F[0], 'w'), ensure_ascii=False); open(记录F[0] + '.md', 'w').write(t)
    print(f'【会话开工】已记下：角色 {角色}，开工必读 指纹 {rec["开工必读指纹"]}（没记下不能提交；开工必读更新了先 --重读）')
    return rec


def 重读():
    rec = 读记录()
    if not rec: sys.exit('【停止】还没开工：python3 视频/工具/会话开工.py <角色>')
    old = open(记录F[0] + '.md').read().splitlines() if os.path.exists(记录F[0] + '.md') else []
    new = open(必读F).read(); 旧 = set(old); add = [l for l in new.splitlines() if l.strip() and l not in 旧]
    print(f'【开工必读 更新】新增或改了 {len(add)} 行：'); [print('  ' + l[:170]) for l in add[:80]]
    if len(add) > 80: print(f'  ……另 {len(add) - 80} 行见 视频/开工必读.md')
    rec['开工必读指纹'] = 指纹(); json.dump(rec, open(记录F[0], 'w'), ensure_ascii=False); open(记录F[0] + '.md', 'w').write(new)
    print(f'已记下新指纹 {rec["开工必读指纹"]}')


def 查开工(rec=None, fp=None):
    rec = 读记录() if rec is None else rec; fp = 指纹() if fp is None else fp
    if not rec or rec.get('角色') not in 角色们:
        return ['【G63 会话开工】本会话还没开工（没读开工必读、没记角色）：先 python3 视频/工具/会话开工.py <出稿|改稿|改门|主会话>，读完总纲、要点、步骤表再提交']
    if rec.get('开工必读指纹') != fp:
        return [f'【G63 会话开工】开工必读 更新了（读的是 {rec.get("开工必读指纹")}，现行 {fp}）：python3 视频/工具/会话开工.py --重读，读完新增的条目再提交']
    return []


def 门程序(p):
    """出稿、改稿会话不许改的（G25）：门、核查、出片、演练程序和登记表"""
    if p.startswith(('.github/workflows/', '.claude/')): return True
    if not p.startswith('视频/工具/'): return False
    r = p[len('视频/工具/'):]
    if re.match(r'初稿生成/gen\d+\.py$', r): return False   # 出稿会话写本篇的数据程序
    if r.startswith(('githooks/', '钩子/', '演练样本/', '环境/')): return True
    return r.endswith(('.py', '.sh')) or os.path.basename(r) in ('规则执行表.json', '放行口子表.json', '规则执行缺口基线.json', '执行效应缺口基线.json', '机制清单.json')


def 角色问题(角色, staged, 同远端):
    if 角色 not in ('出稿', '改稿'): return []
    bad = [p for p in staged if 门程序(p) and not 同远端(p)]
    if not bad: return []
    return [f'【G61 会话角色闸门】本会话是“{角色}”会话，不许提交改门程序：{"、".join(bad[:5])}{"……" if len(bad) > 5 else ""}'
            '（G25：出稿、改稿只改字、跑正式入口；程序不好写进 NN.md 方法复盘 + python3 视频/工具/报坑.py "现象"，由改门会话改。先 git restore --staged 这些文件）']


def _同远端(repo):
    def f(p):
        try:
            idx = subprocess.run(['git', '-C', repo, 'rev-parse', f':{p}'], capture_output=True, text=True).stdout.strip()
            for ref in ('MERGE_HEAD', 'origin/main'):
                o = subprocess.run(['git', '-C', repo, 'rev-parse', f'{ref}:{p}'], capture_output=True, text=True)
                if o.returncode == 0 and o.stdout.strip() == idx: return True
            if not idx:   # 删掉的文件：远端也没有
                o = subprocess.run(['git', '-C', repo, 'cat-file', '-e', f'origin/main:{p}'], capture_output=True)
                return o.returncode != 0
        except Exception: pass
        return False
    return f


def 提交前():
    err = 查开工()
    repo = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()
    if not err and os.path.basename(repo) == 'postgraduate-vocabulary':   # 镜像仓库只是照抄 P，不另查
        staged = subprocess.run(['git', '-C', repo, '-c', 'core.quotepath=off', 'diff', '--cached', '--name-only'], capture_output=True, text=True).stdout.split('\n')
        同 = _同远端(repo); err += 角色问题(读记录()['角色'], [x for x in staged if x], 同)
        门 = [x for x in staged if x and 门程序(x) and not 同(x)]
        if 门 and not err:   # G66 改门锁：改门程序的会话必须持锁（锁读远端最新的坑登记）
            sys.path.insert(0, T); import 报坑 as K
            subprocess.run(['git', '-C', repo, 'fetch', '-q', 'origin', 'main'], capture_output=True)
            o = subprocess.run(['git', '-C', repo, 'show', 'origin/main:' + K.REL], capture_output=True, text=True)
            try: L = json.loads(o.stdout).get('改门锁') or {}
            except Exception: L = K.读本地().get('改门锁') or {}
            err += K.锁问题(门, (读记录() or {}).get('会话', ''), L)
    for e in err: print(e)
    return 1 if err else 0


def 自检():
    import tempfile, shutil
    f = []; old = 记录F[0]; d = tempfile.mkdtemp(prefix='会话开工自检_'); 记录F[0] = f'{d}/r.json'
    try:
        if not 查开工(None): f.append('没抓到：没开工就提交')
        try: 开工('乱写的角色'); f.append('没抓到：角色乱写也开了工（G79 门变异）')
        except SystemExit as e:
            if '角色只能是' not in str(e): f.append(f'角色乱写停错了地方：{e}')
        rec = {'角色': '出稿', '会话': 'x', '开工必读指纹': 'aaa'}
        if not 查开工(rec, 'bbb'): f.append('没抓到：开工必读更新了没重读')
        if 查开工(rec, 'aaa'): f.append('误报：读过现行开工必读')
        no = lambda p: False
        for p in ('视频/工具/踩坑核查.py', '视频/工具/githooks/pre-commit', '视频/工具/规则执行表.json', '视频/工具/钩子/闸门.py', '.claude/settings.json', '.github/workflows/drill.yml', '视频/工具/草稿声音.sh'):
            if not 角色问题('出稿', [p], no): f.append(f'没抓到：出稿会话提交改门程序 {p}')
        for p in ('视频/脚本/27.json', '视频/制作记录/27.md', '视频/工具/初稿生成/gen27.py', '视频/工具/发音词典/已核实读音.json', '视频/工具/用户同意记录.json', '视频/配音缓存/x.pkl'):
            if 角色问题('出稿', [p], no): f.append(f'误拦：出稿会话提交本篇的文件 {p}')
        if 角色问题('改门', ['视频/工具/踩坑核查.py'], no): f.append('误拦：改门会话改门程序')
        if 角色问题('改稿', ['视频/工具/踩坑核查.py'], lambda p: True): f.append('误拦：合并进来的别人的改动（和远端相同）')
        if not 角色问题('改稿', ['视频/工具/踩坑核查.py'], no): f.append('没抓到：改稿会话改门程序')
        try: 环境检查({'不存在的包_m门': 'x-not-exist'}, 装=lambda *a: None); f.append('没抓到：缺包装不上照样开工（M）')
        except SystemExit as e:
            if '自动装不上' not in str(e) or '不存在的包_m门' not in str(e): f.append(f'缺包停错了地方或没说缺什么（M）：{e}')
        装过 = []
        try: 环境检查({'不存在的包_m门': 'x'}, 装=lambda *a: 装过.append(1))
        except SystemExit: pass
        if not 装过: f.append('没抓到：缺包没先自动装（M）')
        try: 环境检查({'json': 'x'}, ff取=lambda: '/不存在/ffmpeg'); f.append('没抓到：ffmpeg 不在照样开工（M）')
        except SystemExit as e:
            if '缺 ffmpeg' not in str(e): f.append(f'ffmpeg 缺停错了地方（M）：{e}')
        try: 环境检查({'json': 'x'}, 装=lambda *a: f.append('误装：包都齐还去装（M）'))
        except SystemExit as e: f.append(f'误停：包都齐（M）：{e}')
        import inspect
        _src = ''.join(l.split('#')[0] for l in inspect.getsource(开工).splitlines())
        if '打印三大主义()' not in _src or _src.find('打印三大主义()') > min(_src.find(x) for x in ('环境检查()', '打印总纲()', '用上核查.py')): f.append('没抓到：开工第一屏不是三大主义（O）')
        if [x[:4] for x in 三大主义] != ['① 执行', '② 丝滑', '③ 虹吸']: f.append('三大主义顺序不对或少了（O）')
        if '环境检查()' not in ''.join(l.split('#')[0] for l in inspect.getsource(开工).splitlines()): f.append('没抓到：开工不先跑环境自检（M）')
        try: 开工('改门', 'x', ''); f.append('没抓到：改门会话没写 --任务')
        except SystemExit: pass
    finally:
        记录F[0] = old; shutil.rmtree(d, ignore_errors=True)
    return ['会话开工 自检：' + x for x in f]


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = lambda k: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else ''
    if '--自检' in a:
        e = 自检(); print('\n'.join(e) or '会话开工 自检通过（没开工、开工必读旧了、出稿/改稿提交改门程序、环境缺包装不上（M）：造的全部拦下；本篇文件、改门会话、合并进来的改动放行）'); sys.exit(1 if e else 0)
    if '--提交前' in a: sys.exit(提交前())
    if '--查' in a:
        e = 查开工(); [print(x) for x in e]; sys.exit(1 if e else 0)
    if '--重读' in a: 重读(); sys.exit(0)
    if '--总纲' in a: 打印三大主义(); 打印总纲(); sys.exit(0)
    if '--状态' in a:
        r = 读记录(); e = 查开工(r)
        print('【会话开工】' + (f'角色 {r["角色"]}，开工必读 {"已读现行版" if not e else "更新了，要 --重读"}' if r else '还没开工：第一件事 python3 视频/工具/会话开工.py <出稿|改稿|改门|主会话>（没开工不能提交）'))
        sys.exit(0)
    if not a or a[0] not in 角色们: sys.exit(__doc__)
    开工(a[0], opt('--会话'), opt('--任务'))
