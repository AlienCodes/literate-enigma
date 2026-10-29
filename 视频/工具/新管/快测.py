#!/usr/bin/env python3
"""快测：改规则、改程序后唯一要过的测试（印章对不上时 做.sh、定稿.sh、提交、推送自动跑它）。本地并行，目标 ≤5 分钟。
  ① 规则表.json（规矩的唯一来源，新规矩 = 一行 + 坏样本 + 好样本）读得出；每条规则的坏样本都有程序跑
  ② 每条规则：它的坏样本必须抓到、好样本必须放过 = 跑它的自检程序（现有 --自检，就是造坏样本、放好样本）
     文本/画面/流程类：FAST 快自检；声音类：在工作目录用 27 跑各声音核查的 --自检
  ③ 挂钩检查（A26/A42）：核查程序挂钩的出片程序原文还在
  ④ 27 回归：缓存重建，a.wav、分段.json 逐字节同基准；每一屏重画，像素哈希同基准
用法：python3 新管/快测.py [--只文本] [--记基准]
环境：XG_TOOLS=检查程序目录（默认 视频/工具）  XG_WORK=出片工作目录（默认 准备机器.sh 搭的 <scratchpad>/video）"""
import sys, os, json, subprocess, hashlib, time, glob
from concurrent.futures import ThreadPoolExecutor
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
T = os.environ.get('XG_TOOLS') or (R if os.path.exists(f'{R}/交付核查.py') else f'{R}/视频/工具'); W = os.environ.get('XG_WORK', '')
NO = os.environ.get('XG_NO', '27'); 基准 = f'{H}/回归基准_{NO}.json'
sys.path.insert(0, T)
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
env0 = {**{k: v for k, v in os.environ.items() if not k.startswith('GIT_')}, 'XG_QUICKTEST': '1'}   # XG_QUICKTEST：收工记录、补对照记录不写主仓库的制作记录（只写临时目录）

def 跑(cmd, cwd, t=900):
    t0 = time.time()
    try: r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env0, timeout=t)
    except subprocess.TimeoutExpired: return 1, f'超时 {t}s', time.time() - t0
    return r.returncode, (r.stdout + r.stderr).strip(), time.time() - t0

def 规则表():
    表 = json.load(open(f'{H}/规则表.json')); bad = []
    for e in 表['规则']:
        if not e.get('编号') or not e.get('状态'): bad.append(f'规则表一行缺编号或状态：{str(e)[:80]}')
    return bad, 表

# 文本/画面/流程类自检（造坏样本必抓、好样本必放）。2026-10-29 删除旧看门：门变异、用上核查、证据、丝滑、演练、会话开工、推请求、
# 放行口子扫码、规则执行核查、开工必读/音频首要法则 文档对文档核对 一律删掉（用户：不看视频本身的检查一律砍掉）
FAST = [['生成文本.py', '--自检'], ['配音缓存核对.py', '--自检'], ['余音删法核对.py', '--自检'], ['确认按位置迁移.py', '--自检'], ['方法进化表.py', '--自检'],
        ['破折号.py', '--自检'], ['区间作废.py', '--自检'], ['同步自检.py'], ['流程自检.py'], ['踩坑核查.py', '自检'], ['check_all.py', '--自检'], ['钩子/钩子自检.py'],
        ['排版自检.py'], ['推送自检.py'], ['译文核查.py', '--自检'], ['出片指纹.py', '--自检'], ['结尾句接点.py', '--自检'], ['句内响度.py', '--自检'],
        ['开工记录.py', '--自检'], ['逐词对齐.py', '--自检'], ['停顿位置精确核对.py', '--自检'], ['响度一致性核对.py', '--确认自检'], ['机器复听.py', '--比较自检'],
        ['纯人声核对.py', '--确认自检'], ['高亮同步核对.py', '--确认自检'], ['颜色核对.py', '--自检'], ['缓存进仓库核对.py', '--自检'], ['速查表.py'], ['报坑.py', '--自检'],
        ['意思个数.py'], ['疑点清单.py', '--自检'], ['新管/分流.py'], ['新管/合回镜像.py', '--自检']]

def 文本自检():
    cmds = FAST
    with ThreadPoolExecutor(8) as ex:
        rs = list(ex.map(lambda c: (c, 跑(['python3', f'{T}/{c[0]}', *c[1:]], T, 300)), cmds))
    return [f'自检不通过：{" ".join(c)} → {o.splitlines()[-1][:160] if o else "无输出"}' for c, (rc, o, _) in rs if rc], len(cmds)

def 声音():
    """交付核查 出片前 / 出片后（看门停用后只剩真检查，内含每个声音核查的 --自检、数字读法自检、独立复核造 5 处瑕疵、高亮自检）
    + 出片守门自检（出片程序每道守门造错必停），三个并行。回归篇只出了声音时，只放过 G12 那一行实查（它的自检照样要过）"""
    import shutil
    if not os.path.exists(f'{W}/{NO}.mp4'):   # 回归篇还没出过片：先只出声音（出片后核查要 NN.mp4）
        subprocess.run(['python3', 'make_video.py', f'scripts/{NO}.json', f'{NO}.mp4'], capture_output=True, cwd=W, env={**env0, 'AUDIO_ONLY': '1'})
    cmds = [['交付核查.py', NO, '出片前'], ['交付核查.py', NO, '出片后'], ['出片守门自检.py']]
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(lambda c: (c, 跑(['python3', f'{T}/{c[0]}', *c[1:]], W, 1800)), cmds))
    bad = []
    for c, (rc, o, dt) in rs:
        x = [l for l in o.splitlines() if l.startswith('✘') and not l.startswith('✘ 成片有画面（G12')]
        if rc and not x and '成片有画面（G12' not in o: x = [o.splitlines()[-1] if o else '无输出']
        bad += [f'{" ".join(c)}（{dt:.0f}s）：{l[:150]}' for l in x]
    return bad, len(cmds)

def 覆盖(表):
    """每条搬进新管的规则，至少一个自检程序会被快测跑到（坏样本必抓）"""
    import re
    跑到 = {c[0] for c in FAST} | {'交付核查.py', '出片守门自检.py'}
    src = open(f'{T}/交付核查.py').read(); 跑到 |= set(re.findall(r"f'\{T\}/([^']+?\.py)'", src))
    定稿时 = {'定稿视频核对.py'}
    没 = [e['编号'] for e in 表 if e['状态'].startswith('搬') and (not e['自检'] or not ({x[0] for x in e['自检']} & (跑到 | 定稿时 | {'新管/快测.py'})))]
    return 没

def 常规规则():
    """新管改成常规的规则（用户已说过“以后都这样”的）：坏样本必抓、好样本必放。
    G35：25 起结尾简述没写特批也整屏；24 不给；中间句不给"""
    import copy, glob
    if not open(f'{T}/render.py').read().count('G35 常规规则'): return ['G35 常规规则：render.py 没打补丁（python3 新管/切换.py <工具>）']
    r = subprocess.run(['python3', '-c', '''
import sys, json, copy, glob; sys.path.insert(0, sys.argv[1]); import render as R
V = sys.argv[2]; d27 = json.load(open(f"{V}/脚本/27.json")); d27["no"] = "27"; d24 = json.load(open(f"{V}/脚本/24.json")); d24["no"] = "24"
key = lambda d, i: " ".join(p[0] for c in d["sentences"][i]["chunks"] for p in c["align"])
bad = []
a = copy.deepcopy(d27); a.pop("说明放宽特批", None); R.apply_script(a)
if R.NOTE_WIDE.get(key(a, -1)) != "整屏": bad.append("没抓到：27 去掉特批后结尾简述不整屏")
R.apply_script(d24)
if R.NOTE_WIDE.get(key(d24, -1)) == "整屏": bad.append("误放：24（25 前）没特批也整屏了")
b = copy.deepcopy(d27); b.pop("说明放宽特批", None); b["sentences"][-1]["chunks"][-1]["note"] = "（结局：x）"; R.apply_script(b)
if R.NOTE_WIDE.get(key(b, -1)) == "整屏": bad.append("误放：最后一句不是简述也整屏了")
print("\\n".join(bad))''', T, os.path.dirname(T)], capture_output=True, text=True, cwd=T, env=env0)
    out = [f'G35 常规规则：{x}' for x in (r.stdout.strip().splitlines() if r.returncode == 0 else [r.stderr.strip()[-200:]])]
    # G65 方法进化（用户原话立的规矩，照跑）+ K97 误拦修正：排队中的篇不拦；变差没写进化落地必拦
    r = subprocess.run(['python3', '-c', '''
import sys, copy, glob, os; sys.path.insert(0, sys.argv[1]); import 方法进化表 as J
bad = []
if not hasattr(J, "出过片"): print("方法进化表.py 没打 K97 补丁"); sys.exit()
行 = J.汇总(); 排 = next((n for n in sorted(map(lambda f: os.path.basename(f)[:2], glob.glob(J.REC + "/[0-9][0-9].md")), reverse=True) if not J.出过片(n)), None)
if 排 and J.门(排, 行=行, 写=False)[0]: bad.append(f"误拦：{排} 还在排队（没出过片）也被 G65 拦（K97）")
import tempfile, json as _j
_r = tempfile.mkdtemp(); _m = tempfile.mkdtemp()
open(_r + "/90.md", "w").write("## token 记录\\n- 进行中\\n"); open(_r + "/91.md", "w").write("## token 记录\\n- 收工 2026-10-28T00:00（UTC）：等效 1M\\n")
for _n in ("90", "91"): _j.dump({"篇": _n, "会话": "s" + _n, "调用": 1, "等效": 1, "平均上下文": 1}, open(_m + "/" + _n + ".json", "w"))
_h = J.汇总(rec=_r, 目录=_m)
if "90" in _h or "91" not in _h: bad.append(f"K97：比较基线要只算出过片的篇（90 排队、91 出过片），现在算进了 {sorted(_h)}")
行2 = copy.deepcopy(行)
if "27" in 行2:
    for k in 行2["27"]:
        if isinstance(行2["27"][k], (int, float)) and not isinstance(行2["27"][k], bool): 行2["27"][k] = 行2["27"][k] * 10 + 100
    if not J.门("27", 行=行2, txt="## 方法复盘\\n- 无\\n", 写=False, 号=set())[0]: bad.append("没抓到：27 比前三篇中位数贵十倍、没写进化落地（G65）")
print("\\n".join(bad))''', T], capture_output=True, text=True, cwd=T, env=env0)
    out += [f'G65：{x}' for x in (r.stdout.strip().splitlines() if r.returncode == 0 else [r.stderr.strip()[-200:]])]
    return out

def 读音自检样本():
    """K102：29 Europe 不误停（读音核对 29 --自检 必过）；把 make_video 的读音改正拆掉（PRON_WORDS 不生效）29 自检必停"""
    import shutil, tempfile
    if not W or not os.path.exists(f'{W}/make_video.py'): return []
    if not os.path.exists(f'{W}/scripts/29.json') and os.path.exists(f'{os.path.dirname(T)}/脚本/29.json'): shutil.copy(f'{os.path.dirname(T)}/脚本/29.json', f'{W}/scripts/29.json')
    if not os.path.exists(f'{W}/scripts/29.json'): return ['K102：没有 29 的脚本']
    bad = []; rc, o, _ = 跑(['python3', f'{T}/读音核对.py', '29', '--自检'], W, 600)
    if rc: bad.append(f'K102 误停：29 读音核对自检 → {o.splitlines()[-1][:120] if o else ""}')
    with tempfile.TemporaryDirectory(dir=os.path.dirname(W)) as td:   # 和工作目录同级：../tts 照样找得到
        for f in os.listdir(W):
            if f.endswith('.py') or f in ('scripts', 'fonts'): (shutil.copytree if os.path.isdir(f'{W}/{f}') else shutil.copy)(f'{W}/{f}', f'{td}/{f}')
        mv = open(f'{td}/make_video.py').read(); a = '    for w_,good in PRON_WORDS.items():'
        if a not in mv: return bad + ['K102：make_video.py 里找不到读音改正那一行（坏样本造不出）']
        open(f'{td}/make_video.py', 'w').write(mv.replace(a, '    for w_,good in {}.items():'))
        rc, o, _ = 跑(['python3', f'{T}/读音核对.py', '29', '--自检'], td, 600)
        if rc == 0: bad.append('K102 没抓到：读音改正拆掉（PRON_WORDS 不生效）29 自检照样通过')
    return bad

def 印章坏样本():
    """改一个工具程序不重跑快测 → 印章必须对不上（提交、推送、做、定稿都停）"""
    import tempfile, shutil
    rc, o, _ = 跑(['python3', f'{H}/印章.py'], R, 60)
    if rc: return [f'印章：刚盖完就对不上：{o[:120]}']
    with tempfile.TemporaryDirectory() as td:
        t2 = f'{td}/工具'; subprocess.run(['cp', '-rs', T, t2]); f = f'{t2}/交付核查.py'; x = open(f).read(); os.remove(f); open(f, 'w').write(x + '\n# 改一行\n')
        r = subprocess.run(['python3', f'{H}/印章.py'], capture_output=True, text=True, env={**env0, 'XG_TOOLS': t2})
        if r.returncode == 0: return ['印章没抓到：改了 交付核查.py 没重跑快测，印章照样对得上']
    return []

def 程序表():
    """{相对 工具/ 的路径: 原文}（不含历史版本、各篇 genNN 数据、缓存）"""
    import re
    out = {}
    for f in glob.glob(f'{T}/**/*', recursive=True):
        r = os.path.relpath(f, T)
        if not os.path.isfile(f) or '历史版本' in r or '__pycache__' in r or re.search(r'gen\d+\.py$', r): continue
        if r.endswith(('.py', '.sh')) or r.startswith('githooks/'): out[r] = open(f, errors='ignore').read()
    return out

def 挂钩检查(files):
    """A26/A42：核查程序靠出片程序（make_video.py、render.py）的原文挂钩（src.index/split/replace 的那一句），
    出片程序一改、那一句没了，核查程序就会崩或悄悄失效。逐个查：每个挂钩的原文都必须还在出片程序里。"""
    import re
    out = []
    for f, t in files.items():
        if f in ('make_video.py', 'render.py') or 'make_video.py' not in t: continue
        tg = set(re.findall(r"open\([^)]*?([\w\u4e00-\u9fff]+\.(?:py|sh))", t))   # 它用 open() 读进来的那些程序
        base = ''.join(files[g] for g in files if g != f and os.path.basename(g) in tg)
        for l in [x for x in t.splitlines() if x.strip() and not x.strip().startswith('#')]:
            for anc in re.findall(r"""(?:_?src|read\(\))\.(?:index|split|replace)\(\s*(['"])(.+?)\1""", l):
                if anc[1] not in base: out.append(f'{f} 挂钩的出片程序原文没了：“{anc[1][:40]}”（A26/A42：改出片程序后核查程序要跟着改）')
    return out

def 草稿路径样本():
    """K109：草稿篇的脚本只在工作目录 scripts/NN.json（仓库 视频/脚本/ 还没有）：音频体检 --自检 要过、语速突变要量得出来。
    以前快测只拿已定稿的 27 回归，草稿篇才走的路径没覆盖（30 的音频体检自检因此失灵）。用假篇号 97（仓库里没有它的脚本）"""
    import shutil, tempfile
    if not os.path.exists(f'{W}/work_{NO}/a.wav'): return [f'K109 样本：没有 work_{NO}/a.wav']
    if os.path.exists(f'{os.path.dirname(T)}/脚本/97.json'): return ['K109 样本：仓库里竟有 视频/脚本/97.json，样本不成立']
    bad = []
    with tempfile.TemporaryDirectory(dir=os.path.dirname(W)) as td:
        os.makedirs(f'{td}/scripts'); shutil.copy(f'{W}/scripts/{NO}.json', f'{td}/scripts/97.json'); os.makedirs(f'{td}/work_97'); shutil.copy(f'{W}/work_{NO}/a.wav', f'{td}/work_97/a.wav')   # 和真草稿同一个位置（../../tts/AF.txt 后期才找得到）
        rc, o, _ = 跑(['python3', f'{T}/音频体检.py', '--自检', 'work_97/a.wav', '97'], td, 600)
        if rc: bad.append(f'K109：脚本只在工作目录时 音频体检 --自检 不过 → {o.splitlines()[-1][:140] if o else "无输出"}')
        rc, o, _ = 跑(['python3', '-c', f"import sys; sys.path.insert(0, {T!r}); import 音频体检 as A; m = A.指标(A.读('work_97/a.wav'), '97'); v = m.get('语速突变'); print(v); sys.exit(0 if v and v[0] is not None else 1)"], td, 600)
        if rc: bad.append(f'K109：脚本只在工作目录时 语速突变 量不出来 → {o.splitlines()[-1][:140] if o else "无输出"}')
    return bad

def 挂钩():
    return [f'挂钩：{x}' for x in 挂钩检查(程序表())]

def 回归(记):
    """缓存重建回归篇：只出声音（AUDIO_ONLY，与正式出片同一套程序），比 a.wav、分段.json；每屏重画比像素哈希"""
    e = {**env0, 'AUDIO_ONLY': '1'}; RW = W.rstrip('/') + '_回归'   # 独立副本（共用 ../tts 缓存），不和交付核查抢 work_NN/a.wav
    import shutil; shutil.rmtree(RW, ignore_errors=True)
    shutil.copytree(W, RW, ignore=lambda d, fs: [f for f in fs if d == W and (f.startswith('work_') or f.endswith(('.mp4', '.mp3')))])
    r = subprocess.run(['python3', 'make_video.py', f'scripts/{NO}.json', f'_回归{NO}.mp4'], capture_output=True, text=True, cwd=RW, env=e)
    if r.returncode: return [f'回归：重建失败 {(r.stdout + r.stderr).strip()[-200:]}'], {}
    cur = {'a.wav': md5(f'{RW}/work_{NO}/a.wav'), '分段.json': md5(f'{RW}/work_{NO}/分段.json')}
    r = subprocess.run(['python3', f'{H}/画面哈希.py', NO], capture_output=True, text=True, cwd=RW, env={**env0, 'XG_TOOLS': T})
    if r.returncode: return [f'回归：画面重画失败 {(r.stdout + r.stderr).strip()[-200:]}'], cur
    cur['画面'] = json.loads(r.stdout.strip().splitlines()[-1])
    if 记:
        json.dump(cur, open(基准, 'w'), ensure_ascii=False, indent=0); return [], cur
    if not os.path.exists(基准): return [f'回归：没有基准 {基准}（先 --记基准，基准必须是旧管出的定稿状态）'], cur
    b = json.load(open(基准)); bad = []
    for k in ('a.wav', '分段.json'):
        if cur[k] != b[k]: bad.append(f'回归：{k} 与基准不同（{b[k][:8]} → {cur[k][:8]}）')
    if cur['画面'] != b['画面']:
        bad.append(f'回归：画面与基准不同：{[i for i, (x, y) in enumerate(zip(cur["画面"], b["画面"])) if x != y][:8]}，屏数 {len(b["画面"])}→{len(cur["画面"])}')
    return bad, cur

def main():
    t0 = time.time(); a = sys.argv[1:]; out = []
    if '--只记基准' in a:   # 基准用旧管（没打补丁的工具）出：回归证明新管和旧管逐字节一致
        b, cur = 回归(True); print('\n'.join(b) or f'{NO} 基准已记：a.wav {cur["a.wav"][:8]}、分段.json {cur["分段.json"][:8]}、{len(cur["画面"])} 屏（{time.time() - t0:.0f} 秒）'); sys.exit(1 if b else 0)
    bad, 表 = 规则表()
    规 = 表['规则']; 搬 = sum(1 for e in 规 if e['状态'].startswith('搬')); 替 = sum(1 for e in 规 if not e['状态'].startswith('搬'))
    out.append(f'① 规则表 {len(规)} 条：有坏样本由快测跑的 {搬}、替代或已删 {替}；版本 {表["版本"]}')
    没 = 覆盖(规); bad += [f'规则的坏样本没人跑：{"、".join(没)}'] if 没 else []
    out.append(f'①b 坏样本覆盖：{len(规) - len(没)} / {len(规)}' + ('' if not 没 else f'，没覆盖 {没[:10]}'))
    全 = '--只文本' not in a
    if 全 and (not W or not os.path.exists(f'{W}/make_video.py')): bad.append('没有出片工作目录（XG_WORK=…/video）：先 bash 视频/工具/环境/准备机器.sh'); 全 = False
    if 全 and 跑(['python3', f'{T}/出片指纹.py', '--核对工作目录', '.'], W, 60)[0]:   # 机械：工作目录的出片程序比工具旧（切换补丁改了 render.py 等），先拷过来（G27）
        跑(['python3', f'{T}/出片指纹.py', '--拷', '.'], W, 120); out.append('（工作目录的出片程序比工具旧，已拷过来，G27）')
    with ThreadPoolExecutor(3) as ex:   # 三路并行：文本快自检、回归、声音（交付核查 + 守门自检）
        ft = ex.submit(文本自检); fr = ex.submit(回归, '--记基准' in a) if 全 else None; fs = ex.submit(声音) if 全 else None
        b, n = ft.result(); bad += b; out.append(f'② 文本/画面/流程 快自检 {n} 个程序：{"全过" if not b else f"{len(b)} 个不过"}')
        b = 挂钩(); bad += b; out.append(f'③ 挂钩检查：{"在" if not b else "断了"}')
        b = 常规规则(); bad += b; out.append(f'③b 常规规则（G35 简述整屏、G65 方法进化 K97）坏样本必抓、好样本必放：{"过" if not b else "不过"}')
        if 全:
            b, _ = fr.result(); bad += b; out.append(f'④ {NO} 回归：{"记了基准" if "--记基准" in a else ("a.wav、分段.json 逐字节、每屏像素一致" if not b else "不一致")}')
            b = 读音自检样本(); bad += b; out.append(f'⑥ K102 读音自检：29 不误停、拆读音改正必停：{"过" if not b else "不过"}')
            b, n = fs.result(); bad += b; out.append(f'⑤ 交付核查 出片前/出片后 + 出片守门自检：{"全过" if not b else f"{len(b)} 处不过"}')
            b = 草稿路径样本(); bad += b; out.append(f'⑦ 草稿篇路径（K109：脚本只在工作目录，音频体检自检过、语速突变量得出）：{"过" if not b else "不过"}')
    if not bad and '--只文本' not in a and '--记基准' not in a:
        subprocess.run(['python3', f'{H}/印章.py', '--盖'], env={**env0, 'XG_TOOLS': T}, capture_output=True)
        try: open(os.path.expanduser('~/.新管工作目录'), 'w').write(W)   # 提交、推送时 印章.py --自动 在这里跑快测
        except OSError: pass
        b = 印章坏样本(); bad += b; out.append('已盖快测印章（程序或规则表再改要重跑）；改程序不重跑必停：' + ('过' if not b else '不过'))
    print('\n'.join(out + [f'  ✘ {x}' for x in bad] + [f'快测{"通过" if not bad else "不通过"}，用时 {time.time() - t0:.0f} 秒']))
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
