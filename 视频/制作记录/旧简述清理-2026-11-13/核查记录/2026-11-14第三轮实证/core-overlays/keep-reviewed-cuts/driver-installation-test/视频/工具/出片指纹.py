#!/usr/bin/env python3
"""出片指纹（G26、G27，2026-10-24 24 第三稿两处漏洞）：
G27 工作目录要拷的出片程序清单不再手写：从 make_video.py 的 import 递归找全本仓库模块（这次漏了 对正量.py，第一次出片 ModuleNotFoundError）。
    准备机器.sh 用 --拷，定稿流水线、演练用 --核对工作目录（每个模块都在、都与仓库一致）。
G26 出片后核对视频是不是现行脚本、现行程序出的：make_video 出完片在视频旁边写 NN.mp4.指纹.json（视频、脚本、配音 a.wav、
    每个出片模块的指纹）；交付核查 出片后 逐项与现行的比，没有指纹或任何一项对不上就停（那次出片失败，09:18 的旧 24.mp4 照样“全部通过”）。
用法：python3 出片指纹.py NN                 在视频工作目录下核对 NN.mp4
      python3 出片指纹.py --核对工作目录 [W]   W 里每个出片模块都在、与仓库一致
      python3 出片指纹.py --拷 <目录>          把出片模块拷进 <目录>（准备机器.sh）
      python3 出片指纹.py --清单 | --自检"""
import os, sys, ast, json, hashlib, shutil, tempfile
T = os.path.dirname(os.path.abspath(__file__))
入口 = 'make_video.py'


def _sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()[:16]


def _找(m, 搜):
    return next((f'{d}/{m}.py' for d in 搜 if os.path.isfile(f'{d}/{m}.py')), None)


def 清单(搜=None):
    """{模块名: 路径}：入口 make_video.py 和它（递归）import 的本目录模块；搜 = 按 import 先后的目录（工作目录是 ../tts 在前）"""
    搜 = 搜 or [T]; out = {}; todo = [入口[:-3]]
    while todo:
        m = todo.pop()
        if m in out: continue
        p = _找(m, 搜)
        if not p: continue   # 第三方库、标准库
        out[m] = p
        for n in ast.walk(ast.parse(open(p, encoding='utf-8').read())):
            if isinstance(n, ast.Import): todo += [a.name.split('.')[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level: todo.append(n.module.split('.')[0])
    return out


def 工作目录搜(W):   # make_video.py 先 sys.path.insert(0,'../tts')：../tts 在前，工作目录在后
    W = os.path.abspath(W); return [os.path.join(os.path.dirname(W), 'tts'), W]


def 核对工作目录(W='.', t=T):
    """G27：仓库清单里每个出片模块，工作目录里按 import 先后找到的那份必须在、且与仓库逐字节相同"""
    搜 = 工作目录搜(W); bad = []
    for m, p in 清单([t]).items():
        q = _找(m, 搜)
        if not q: bad.append(f'工作目录缺 {m}.py（出片会 ModuleNotFoundError）')
        elif _sha(q) != _sha(p): bad.append(f'工作目录的 {m}.py 与仓库不一致')
    return bad


def 拷(dst, t=T):
    os.makedirs(dst, exist_ok=True); L = 清单([t])
    for p in L.values(): shutil.copy2(p, dst)
    return sorted(L)


def 指纹路径(out): return f'{out}.指纹.json'


def 写(js, out, work, 搜=None):
    """make_video 出完片调用：记下这个视频是哪份脚本、哪份配音、哪些程序出的"""
    真 = 搜 is None
    if 真:
        main = getattr(sys.modules.get('__main__'), '__file__', None)
        搜 = [os.path.abspath('../tts'), os.path.dirname(os.path.abspath(main)) if main else os.getcwd()]
    mods = {}
    for m, p in 清单(搜).items():
        f = getattr(sys.modules.get(m), '__file__', None) if 真 and m != 入口[:-3] else None   # 已经 import 的按真用的那份算
        mods[m] = _sha(f if f and os.path.isfile(f) else p)
    rec = {'视频': _sha(out), '脚本': _sha(js), '配音': _sha(f'{work}/a.wav'), '只出声音': bool(os.environ.get('AUDIO_ONLY')), '程序': mods}
    json.dump(rec, open(指纹路径(out), 'w'), ensure_ascii=False, indent=1)


def 核(no, W='.', t=T):
    """G26：NN.mp4 必须是现行脚本、现行程序出的；返回问题（空 = 通过）"""
    out = f'{W}/{no}.mp4'; fp = 指纹路径(out)
    if not os.path.exists(out): return [f'没有 {no}.mp4']
    try: r = json.load(open(fp))
    except Exception: return [f'{no}.mp4 没有出片指纹（不是现行出片程序出的，或出片中途失败、留下的是旧视频）：重新 python3 make_video.py scripts/{no}.json {no}.mp4']
    bad = []
    if r.get('视频') != _sha(out): bad.append(f'{no}.mp4 不是写指纹那次出的片（被覆盖或换了）')
    if r.get('脚本') != _sha(f'{W}/scripts/{no}.json'): bad.append(f'旧视频配新脚本：出片以后 scripts/{no}.json 又改了')
    if not os.path.exists(f'{W}/work_{no}/a.wav') or r.get('配音') != _sha(f'{W}/work_{no}/a.wav'): bad.append(f'work_{no}/a.wav 不是这个视频的配音（之后又出过片或被改）')
    now = {m: _sha(p) for m, p in 清单([t]).items()}; old = r.get('程序', {})
    diff = sorted(m for m in set(now) | set(old) if now.get(m) != old.get(m))
    if diff: bad.append(f'出片以后出片程序改了（或出片用的不是仓库现行程序）：{"、".join(diff)}')
    return bad


def 自检():
    fails = []; root = tempfile.mkdtemp(prefix='出片指纹自检_')
    try:
        t = f'{root}/工具'; W = f'{root}/video'; os.makedirs(t); os.makedirs(f'{root}/tts'); os.makedirs(f'{W}/scripts'); os.makedirs(f'{W}/work_99')
        open(f'{t}/make_video.py', 'w').write('import os, render\nfrom clean import x\ndef build():\n    import 新模块 as N\n')
        open(f'{t}/render.py', 'w').write('import re\n'); open(f'{t}/clean.py', 'w').write('x = 1\n'); open(f'{t}/新模块.py', 'w').write('import render\n')
        if set(清单([t])) != {'make_video', 'render', 'clean', '新模块'}: fails.append(f'没抓到：新加的被 import 的模块不在清单里（G27，得到 {sorted(清单([t]))}）')
        拷(W, t); os.remove(f'{W}/新模块.py'); shutil.move(f'{W}/clean.py', f'{root}/tts/clean.py')
        if not any('缺 新模块' in x for x in 核对工作目录(W, t)): fails.append('没抓到：工作目录缺一个出片模块（G27 重放 对正量.py）')
        拷(W, t); os.remove(f'{W}/clean.py')
        if 核对工作目录(W, t): fails.append('误报：工作目录模块齐全（clean 在 ../tts）还报缺')
        open(f'{W}/scripts/99.json', 'w').write('{"no": "99"}'); open(f'{W}/work_99/a.wav', 'wb').write(b'wav'); open(f'{W}/99.mp4', 'wb').write(b'video')
        写(f'{W}/scripts/99.json', f'{W}/99.mp4', f'{W}/work_99', 工作目录搜(W))
        if 核('99', W, t): fails.append(f'误报：刚出的片对得上还报 {核("99", W, t)}')
        def 造(name, do, undo, want):
            do()
            if not any(want in x for x in 核('99', W, t)): fails.append(f'没抓到：{name}（G26）')
            undo()
        造('旧视频配新脚本', lambda: open(f'{W}/scripts/99.json', 'w').write('{"no": "99", "改": 1}'), lambda: open(f'{W}/scripts/99.json', 'w').write('{"no": "99"}'), '旧视频配新脚本')
        造('出片以后程序改了', lambda: open(f'{t}/新模块.py', 'a').write('# 改\n'), lambda: open(f'{t}/新模块.py', 'w').write('import render\n'), '出片程序改了')
        造('视频被覆盖', lambda: open(f'{W}/99.mp4', 'wb').write(b'old video'), lambda: open(f'{W}/99.mp4', 'wb').write(b'video'), '不是写指纹那次')
        造('配音被换', lambda: open(f'{W}/work_99/a.wav', 'wb').write(b'wav2'), lambda: open(f'{W}/work_99/a.wav', 'wb').write(b'wav'), '不是这个视频的配音')
        造('没有指纹（出片失败留下旧视频）', lambda: os.rename(指纹路径(f'{W}/99.mp4'), f'{root}/fp'), lambda: os.rename(f'{root}/fp', 指纹路径(f'{W}/99.mp4')), '没有出片指纹')
        if 核('99', W, t): fails.append('误报：样本复原后还报')
        if '对正量' not in 清单() or 'title_anim' not in 清单(): fails.append(f'仓库清单没找全（缺 对正量 或 title_anim）：{sorted(清单())}')
    finally: shutil.rmtree(root, ignore_errors=True)
    return ['出片指纹 自检：' + x for x in fails]


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--自检' in a:
        e = 自检(); print('\n'.join(e) or '出片指纹 自检通过（旧视频配新脚本、程序改了、视频被覆盖、配音被换、没有指纹都停；新模块自动进清单，缺模块必停）'); sys.exit(1 if e else 0)
    if '--清单' in a: print(' '.join(f'{m}.py' for m in sorted(清单()))); sys.exit(0)
    if '--拷' in a: print('拷了', ' '.join(拷(a[a.index('--拷') + 1]))); sys.exit(0)
    if '--核对工作目录' in a:
        i = a.index('--核对工作目录'); e = 核对工作目录(a[i + 1] if len(a) > i + 1 else '.')
        print('\n'.join('【停止】' + x for x in e) or '工作目录出片程序齐全、与仓库一致'); sys.exit(1 if e else 0)
    e = 核(a[0].zfill(2)); print('\n'.join('【停止】' + x for x in e) or f'{a[0]}.mp4 是现行脚本、现行程序出的'); sys.exit(1 if e else 0)
