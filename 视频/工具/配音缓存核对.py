#!/usr/bin/env python3
"""配音缓存核对（G72，主会话 2026-10-26 定：合成单线程后，配音缓存两道门）。
  门一：没有 .单线程 标记的缓存条目，必须在 视频/配音缓存/老条目指纹.json 里且指纹相符（老条目被改、被换、损坏 → 停）；
  门二：新条目只能是单线程合成、带 .单线程 标记（标记里是条目指纹），没标记又不在老条目清单里 → 停（防有人用多线程悄悄合成新条目）。
  门本身在出片程序 make_video.py 的 _条目核对()（每次读缓存都核），独立复核/synth.py 同一个函数；本程序借同一段代码：
  python3 配音缓存核对.py --全部    把仓库 视频/配音缓存/ 全部条目核一遍（CI、定稿前用）
  python3 配音缓存核对.py --自检    造坑：改一条老条目、放一条无标记新条目、标记指纹不符，必须都停；原样老条目、带标记新条目不误拦"""
import os, sys, json, glob, tempfile, shutil, hashlib as _hl
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
_src = open(f'{T}/make_video.py').read()
TTS = os.path.expanduser('~/work/tts'); _CACHE = f'{TTS}/cache_tts'
exec(_src[_src.index('def _portable_mid(model):'):_src.index('def _cached(obj,meth,model):')])
def 核(p):
    try: _条目核对(p); return None
    except SystemExit as e: return str(e)
def 自检():
    global _OLD
    f = []; d = tempfile.mkdtemp(); keep = _OLD
    try:
        a = f'{d}/老.pkl'; open(a, 'wb').write(b'old'); _OLD = {'老.pkl': _hl.sha256(b'old').hexdigest()[:16]}
        if 核(a): f.append('误拦：原样老条目')
        open(a, 'wb').write(b'old!')
        if not 核(a): f.append('没抓到：老条目被改（G72）')
        b = f'{d}/新.pkl'; open(b, 'wb').write(b'new')
        if not 核(b): f.append('没抓到：没有 .单线程 标记又不在老条目清单里的新条目（G72）')
        open(b + '.单线程', 'w').write(_hl.sha256(b'new').hexdigest()[:16])
        if 核(b): f.append('误拦：带单线程标记的新条目')
        open(b, 'wb').write(b'new!')
        if not 核(b): f.append('没抓到：新条目与 .单线程 标记指纹不符（G72）')
    finally:
        _OLD = keep; shutil.rmtree(d, ignore_errors=True)
    return f
if __name__ == '__main__':
    if '--自检' in sys.argv:
        e = 自检(); print('配音缓存核对 自检：' + ('；'.join(e) if e else '通过（老条目被改、无标记新条目、标记指纹不符都停；原样老条目、带标记新条目不误拦）')); sys.exit(1 if e else 0)
    if '--全部' in sys.argv:
        ps = sorted(glob.glob(f'{V}/配音缓存/*.pkl')); bad = [x for x in (核(p) for p in ps) if x]
        print(f'配音缓存核对：{len(ps)} 条，老条目 {sum(os.path.basename(p) in _OLD for p in ps)}，新条目（单线程）{sum(os.path.exists(p + ".单线程") for p in ps)}，不过 {len(bad)}')
        for x in bad[:5]: print('  ✘', x)
        sys.exit(1 if bad else 0)
    print(__doc__); sys.exit(1)
