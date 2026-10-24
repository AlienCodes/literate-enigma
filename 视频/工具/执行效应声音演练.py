#!/usr/bin/env python3
"""执行效应·声音演练（CLAUDE.md 第19条；执行效应补全 A 类）：声音核查的门，在真实流程里把坏声音挡下来才算数。
做法：用现行脚本只出声音（AUDIO_ONLY，配音缓存命中几秒钟）做底稿；每一场拷一份，按历史事故的样子把声音弄坏一处
（句子里硬塞一段静音、剪掉句尾辅音、一句突然变轻、句间塞呼吸声、削波、句首吃掉、时间表错开一块……），
或把脚本改成事故的样子（数字、引号、多音词），然后在临时“仓库镜像”里真跑 交付核查.py NN 出片前/出片后（cwd = 这一场的工作目录），
必须在对应的那一步新报出 ✘。只看比原样新多出来的 ✘，所以本篇原有的待改项不干扰。真仓库 git status 不许变。
声音演练慢（一场 1–2 分钟），单独盖印章 工具/执行效应声音演练通过.json，只盖声音核查程序的指纹：这些程序一改就要重演（规则执行核查 查印章）。
在视频工作目录下运行：python3 <工具目录>/执行效应声音演练.py        全部声音演练
                      python3 <工具目录>/执行效应声音演练.py 编号…  只演练这几场（不盖印章）"""
import os, sys, json, re, shutil, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import numpy as np, soundfile as sf
import 执行效应演练 as Y

NO = '20'   # 最短的已定稿篇目之一（17 句），只出声音 8 秒
STAMP = f'{T}/执行效应声音演练通过.json'
声音被演练 = ['交付核查.py', '标点停顿核对.py', '句首句尾与停顿位置核对.py', '读音核对.py', '词尾辅音核对.py', '停顿位置精确核对.py', '无标点停顿核对.py',
          'audio_qc.py', '响度一致性核对.py', '纯人声核对.py', '句间停顿核对.py', '高亮同步核对.py', 'make_video.py', '执行效应声音演练.py', '执行效应演练.py']   # 规则执行表 每次主演练都会改写“演练”字段，不盖进声音印章
指纹 = Y.指纹


# —— 声音上动手（长度不变：时间表、配音指纹都还对得上，只有声音本身坏了）
def 段(a, sr, gap=0.5):
    """按整段的数字静音（a == 0，句间停顿）切出说话段 [(起, 止)]（采样点）"""
    z = np.append(np.insert((a == 0).astype(np.int8), 0, 0), 0); d = np.diff(z); st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    sil = [(s, e) for s, e in zip(st, en) if e - s >= gap * sr]
    out, prev = [], 0
    for s, e in sil:
        if s > prev: out.append((prev, s))
        prev = e
    if prev < len(a): out.append((prev, len(a)))
    return [(s, e) for s, e in out if e - s > 0.8 * sr], sil
def 中间静音(a, sr):   # A4：句子里没有标点的地方硬停 0.35 秒（行与行之间停顿太多，像机器人）
    s, e = max(段(a, sr)[0], key=lambda x: x[1] - x[0]); m = (s + e) // 2; a[m - int(0.175 * sr):m + int(0.175 * sr)] = 0; return a
def 剪句尾(a, sr):     # A6/A21：句尾词尾辅音被切掉（每句最后 90 毫秒）
    for s, e in 段(a, sr)[0]: a[e - int(0.09 * sr):e] = 0
    return a
def 一句变轻(a, sr):   # A8/A29：一句突然变轻 12 dB
    sg = 段(a, sr)[0]; s, e = sg[len(sg) // 2]; a[s:e] *= 10 ** (-12 / 20); return a
def 塞呼吸(a, sr):     # A2/A3/音2：句间停顿里留了呼吸声（-38 dBFS 的气声）
    s, e = max(段(a, sr)[1], key=lambda x: x[1] - x[0]); m = (s + e) // 2; n = int(0.3 * sr)
    rng = np.random.default_rng(7); w = np.convolve(rng.standard_normal(n), np.ones(6) / 6, 'same'); w *= 10 ** (-38 / 20) / (np.sqrt(np.mean(w ** 2)) + 1e-12)
    a[m - n // 2:m - n // 2 + n] = w * np.hanning(n); return a
def 削波(a, sr):       # A2：削波、电子声（一段放大 8 倍削平）
    s, e = 段(a, sr)[0][1]; m = (s + e) // 2; r = slice(m, m + int(0.25 * sr)); a[r] = np.clip(a[r] * 8, -0.999, 0.999); return a
def 吃句首(a, sr):     # A20/A1：句首被吃掉 0.4 秒（句间停顿变长、词头没了）
    s, e = 段(a, sr)[0][3]; a[s:s + int(0.4 * sr)] = 0; return a
def 改声音(fn):
    def go(ws):
        p = f'{ws}/work_{NO}/a.wav'; a, sr = sf.read(p); a = fn(a.copy(), sr); sf.write(p, a, sr)
        af = open(f'{os.path.dirname(ws)}/tts/AF.txt').read().strip()   # 与出片程序 AUDIO_ONLY 同一套后期，重新做只有声音的 NN.mp4
        subprocess.run([__import__('imageio_ffmpeg').get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-i', p, '-af', af, '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', f'{ws}/{NO}.mp4'], check=True)
    return go
def 错开一块(ws):      # L14/L17：时间表里一块提前 0.4 秒（高亮没跟上朗读），总长不变
    p = f'{ws}/work_{NO}/list.txt'; t = open(p).read(); ds = re.findall(r'duration ([\d.]+)', t); i = len(ds) // 2
    ds[i], ds[i + 1] = f'{float(ds[i]) - 0.4:.3f}', f'{float(ds[i + 1]) + 0.4:.3f}'; it = iter(ds)
    open(p, 'w').write(re.sub(r'duration [\d.]+', lambda m: f'duration {next(it)}', t))


# —— 脚本上动手（重放事故：数字、引号、多音词）
def _加英文(d, en, zh):
    c = Y.块(d, 1); c['en'] += ' ' + en; c['zh'] += zh; c['align'].append([en, zh])
def 改读法(old, new):   # 工作目录的出片程序（交付核查 读它的朗读文字规则）退回事故当时的样子
    def go(ws):
        p = f'{ws}/make_video.py'; t = open(p).read(); assert t.count(old) == 1, old; os.unlink(p); open(p, 'w').write(t.replace(old, new))
    return go
年份退回 = 改读法("    return _n2w(hi)+' '+('oh '", "    return _n2w(hi)+' hundred '+('oh '")          # A11：1995 读成 nineteen hundred ninety-five
时刻退回 = 改读法(r"(1[0-2]|[1-9])[.:]([0-5]\d)([ap])m", r"(1[0-2]|[1-9])[:]([0-5]\d)([ap])m")   # A37：11.40pm 读成 eleven point four zero pm
_mv = open(f'{T}/make_video.py').read(); _qline = next(l for l in _mv.splitlines() if l.strip().startswith("t=re.sub(r'[\"“”‘]"))
引号退回 = 改读法(_qline + '\n    return t', '    return t')   # A17：引号照读（读到引号会拖长、顿一下）
_SA = 'fades=fades_)\n    return clips,tmap'   # sentence_audio 的出口：无标点停顿核对、词尾辅音核对 都用工作目录出片程序的 sentence_audio 重出每句
句中停顿 = 改读法(_SA, 'fades=fades_)\n    clips=[np.concatenate([c[:len(c)//2],np.zeros(int(0.35*SR),c.dtype),c[len(c)//2:]]) for c in clips]\n    return clips,tmap')   # A4：句子中间多停 0.35 秒
_挪1 = 改读法('f=min(range(r0,r1),key=lambda f:e[f]); ca=cb=f*F; keep=max(0,b-a)*F/SR', 'f=min(range(r0,r1),key=lambda f:e[f]); ca=cb=f*F+int(0.15*SR); keep=max(0,b-a)*F/SR')
_挪2 = 改读法('            ca=cb=(cx if cx is not None else f*F); keep=0.0', '            ca=cb=(cx if cx is not None else f*F)+int(0.15*SR); keep=0.0')
def 停顿挪进词里(ws): _挪1(ws); _挪2(ws)   # A9：插入的停顿（只插不删、连读处插入）落到后一个词里 150 毫秒
剪词尾 = 改读法(_SA, 'fades=fades_)\n    clips=[np.concatenate([c[:-int(0.09*SR)],np.zeros(int(0.09*SR),c.dtype)]) for c in clips]\n    return clips,tmap')   # A21：停顿前、句末的词尾 90 毫秒剪掉
def 加引号(f): Y._改json(f, f'视频/脚本/{NO}.json', lambda d: _加英文(d, 'the "best" one', '那个“最好的”'))
def 加多音(f): Y._改json(f, f'视频/脚本/{NO}.json', lambda d: _加英文(d, 'as they read', '正如他们读到的'))  # A24/A35：read 按语境核对读音


# (编号, 阶段, 怎么造, 改脚本, 改工作目录, 必须新报出 ✘ 的那一步（都要有）, 这一场证明的规矩)
声音场景 = [
    ('A4句中硬停', '出片前', '出片程序每句中间（没有标点处）多停 0.35 秒（像机器人）', None, 句中停顿, ['无标点处停顿'], ['A4']),
    ('A21剪句尾辅音', '出片前', '出片程序把停顿前、句末的最后 90 毫秒剪掉（词尾 t/k/p 没了）', None, 剪词尾, ['词尾辅音核对（A21'], ['A21', 'A38', 'A41', 'A43', 'A6']),
    ('A13独立复核剪句尾', '出片后', '每句最后 90 毫秒剪掉（词尾被切），独立复核必须报出', None, 改声音(剪句尾), ['独立复核'], ['A13', 'A14', 'A16', 'A18', 'A22', 'A31', 'A34', 'A10b', '流5']),
    ('A9停顿落在词里', '出片前', '出片程序把只插不删的停顿往后挪 150 毫秒（落在后一个词里）', None, 停顿挪进词里, ['停顿位置核对（A9'], ['A9']),
    ('A8一句变轻', '出片后', '中间一句突然变轻 12 dB', None, 改声音(一句变轻), ['响度一致性（逐句'], ['A8', 'A29']),
    ('A2句间呼吸声', '出片后', '句间停顿里留 0.3 秒气声', None, 改声音(塞呼吸), ['纯人声核对'], ['A2', 'A19']),
    ('A2削波', '出片后', '一段放大 8 倍削平', None, 改声音(削波), ['自动音频检查'], ['A2']),
    ('A20句首被吃', '出片后', '第 4 句开头 0.4 秒没了（句间停顿变长）', None, 改声音(吃句首), ['句间停顿核对'], ['A20', 'A5', 'A1']),
    ('L14高亮错开', '出片后', '时间表里一块提前 0.4 秒', None, 错开一块, ['高亮同步核对（L14'], ['L14', 'L17']),
    ('A11年份读法', '出片前', '年份读法退回事故时（1995 读成 nineteen hundred ninety-five）', None, 年份退回, ['数字读法、引号自检'], ['A11']),
    ('A37时刻读法', '出片前', '时刻读法退回事故时（重放 15：11.40pm 读成 eleven point four zero）', None, 时刻退回, ['数字读法、引号自检'], ['A37']),
    ('A17引号', '出片前', '引号照读（读法退回）、S2 有带引号的 "best"', 加引号, 引号退回, ['数字读法、引号自检', '引号不停顿'], ['A17']),
    ('A24多音词', '出片前', 'S2 加 as they read（多音词没按语境核对）', 加多音, None, ['读音核对（A23'], ['A24', 'A35']),
    ('G12只有声音', '出片后', '重放 21：NN.mp4 被只出声音覆盖（没有画面）', None, None, ['成片有画面（G12'], ['G12']),
]


def 跑(M, ws, stage):
    env = {**os.environ, 'CLAUDE_PROJECT_DIR': M}
    r = subprocess.run(['python3', f'{M}/视频/工具/交付核查.py', NO, stage], cwd=ws, capture_output=True, text=True, timeout=1800, env=env)
    return r.returncode, {l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith('✘')}


def 演练(W, 只=None):
    root = os.path.dirname(os.path.abspath(W)); g0 = Y._git状态()
    r = subprocess.run(['python3', 'make_video.py', f'scripts/{NO}.json', f'{NO}.mp4'], cwd=W, env={**os.environ, 'AUDIO_ONLY': '1'}, capture_output=True, text=True)
    if r.returncode: return [('只出声音底稿', False, r.stdout[-200:] + r.stderr[-200:])]
    def 场(sid, fs=None, fw=None, qc=None):
        """这一场的工作根：R/video（工作目录）、R/tts（模型，链接）、R/qc_independent（独立复核的合成，从原样那一场拷来）——
        独立复核按“工作根/video/work_NN”找声音，工作目录必须叫 video、和真实一样"""
        f = Y.仓库底稿(NO, '声音'); fs and fs(f)
        R = f'{root}/演练_声_{sid}'; shutil.rmtree(R, ignore_errors=True); os.makedirs(R); os.symlink(f'{root}/tts', f'{R}/tts')
        ws0 = Y.工作区(W, R, 'v', NO, json.loads(f[f'视频/脚本/{NO}.json'])); ws = f'{R}/video'; os.rename(ws0, ws)
        shutil.copytree(f'{W}/work_{NO}', f'{ws}/work_{NO}'); shutil.copy(f'{W}/{NO}.mp4', f'{ws}/{NO}.mp4'); fw and fw(ws)
        if qc and os.path.isdir(qc): shutil.copytree(qc, f'{R}/qc_independent', symlinks=True)
        return Y.镜像(f'{root}/演练_镜像_声_{sid}', f), ws
    todo = [s for s in 声音场景 if not 只 or s[0] in 只]
    stages = sorted({s[1] for s in todo}); base = {st: 场(f'原样{st}') for st in stages}
    qc0 = f'{root}/演练_声_原样出片后/qc_independent'   # 独立复核的合成只与脚本有关：原样那一场合成一次，各场拷过去
    with ThreadPoolExecutor(4) as ex:
        bo = dict(zip(stages, ex.map(lambda st: 跑(*base[st], st), stages)))
        def one(s):
            sid, stage, how, fs, fw, want, rules = s
            try: c, o = (跑(*场(sid, fs, fw, qc0 if not fs else None), stage) if (fs or fw) else bo[stage])
            except Exception as e: return sid, False, f'样本找不到：{e!r}'
            new = o - bo[stage][1] if (fs or fw) else o
            miss = [w for w in want if not any(w in l for l in new)]
            return sid, c != 0 and not miss, ('新报出：' + next(l for l in new if want[0] in l)[:80]) if not miss else f'没挡住：{miss}（退出码 {c}，新报出 {"；".join(sorted(new))[:150]}）'
        res = list(ex.map(one, todo))
        if not 只 or '自查拆门_声音' in 只:   # 拆门自查：把 无标点停顿核对 的门拆掉（镜像里改程序），A4 那一场必须报“没挡住”
            s = next(x for x in 声音场景 if x[0] == 'A4句中硬停'); M, ws = 场('拆门', None, s[4], qc0)
            p = f'{M}/视频/工具/交付核查.py'; t = open(p).read(); open(p, 'w').write(t.replace("step('无标点处停顿 ≤ 0.22 秒', not long,", "step('无标点处停顿 ≤ 0.22 秒', True,", 1))
            c, o = 跑(M, ws, s[1]); caught = any('无标点处停顿' in l for l in o - bo[s[1]][1])
            res.append(('自查拆门_声音', not caught, '拆掉 无标点停顿 的门后演练报“没挡住”（演练能发现坏门）' if not caught else '拆掉门后演练还说挡住了：演练失灵'))
    for x in os.listdir(root):
        if x.startswith('演练_'): shutil.rmtree(f'{root}/{x}', ignore_errors=True)
    for l in Y._git状态().splitlines():   # 演练里合成的新缓存（出片程序自动拷进 配音缓存/）不留：只删这次演练新出现、没提交的
        if l.startswith('?? ') and l not in g0 and '.pkl' in l:
            p = os.path.join(os.path.dirname(Y.V), l[3:].strip('"'))
            if os.path.exists(p) and '配音缓存' in p: os.remove(p)
    if Y._git状态() != g0: res.append(('真仓库没被碰', False, '声音演练改了真仓库（git status 变了）：镜像漏了写入的路径'))
    return res


def 印章有效():
    try: st = json.load(open(STAMP))
    except Exception: return False
    return all(st.get(x) == 指纹(f'{T}/{x}') for x in 声音被演练)


def main():
    a = sys.argv[1:]
    if not os.path.exists('make_video.py') or not os.path.isdir('scripts'): sys.exit('【停止】请在视频工作目录（含 make_video.py、scripts/）下运行')
    for x in ('make_video.py', 'render.py'):
        if 指纹(x) != 指纹(f'{T}/{x}'): sys.exit(f'【停止】工作目录的 {x} 与仓库不一致，先拷过来再演练')
    if 指纹(f'scripts/{NO}.json') != 指纹(f'{Y.V}/脚本/{NO}.json'): sys.exit(f'【停止】工作目录的 scripts/{NO}.json 与仓库不一致')
    only = [x for x in a if not x.startswith('--')]
    res = 演练(os.getcwd(), only)
    for sid, ok, msg in res: print(f"{'✔' if ok else '✘'} {sid}：{msg}")
    bad = [s for s, ok, _ in res if not ok]
    if bad or only: print('执行效应声音演练：' + ('【没通过：' + '、'.join(bad) + '】' if bad else '部分演练通过（不盖印章）')); return 1 if bad else 0
    json.dump({**{x: 指纹(f'{T}/{x}') for x in 声音被演练}, '_挡住': [s for s, _, _ in res]}, open(STAMP, 'w'), ensure_ascii=False, indent=1)
    print(f'执行效应声音演练：通过（{len(res)} 场全部挡在对的那一步，拆掉的门被发现；印章已写）'); return 0


if __name__ == '__main__':
    sys.exit(main())
