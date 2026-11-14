#!/usr/bin/env python3
"""余音删法核对（K27，2026-10-26 27 S6 contamination, and：/n/ 衰减到 -55 dB 以下 5 ms 后又回升到 -43 dB 的余音 20 ms，
出片程序从第一个 -55 dB 帧起删停顿，把余音切掉 10 ms，独立复核报词尾被切）。28 起出片程序删标点停顿用 _余音两头()：
衰减后 10 ms 内又能听见的算这个词的余音、下一个词头前 10 ms 内的弱起音算词头，都留着；停顿里隔得远的底噪照旧删。
本程序不导入配音模型：从 make_video.py 原文取出 _余音两头 和 余音自检 单独跑（规则执行核查每次当场跑）。
用法：python3 余音删法核对.py --自检"""
import ast, os, sys
import numpy as np
T = os.path.dirname(os.path.abspath(__file__))

def 取(src=None):
    src = src or open(os.path.join(T, 'make_video.py')).read(); tree = ast.parse(src); g = {'np': np, 'AUD_DB': -55}
    fs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for nm in ('_余音两头', '余音自检'):
        if nm not in fs: return None, f'make_video.py 里没有 {nm}()'
        exec(compile(ast.Module([fs[nm]], []), 'make_video.py', 'exec'), g)
    sa = ast.get_source_segment(src, fs['sentence_audio']) if 'sentence_audio' in fs else ''
    if '_余音两头(e,a,b)' not in sa: return None, 'sentence_audio 删停顿时没调 _余音两头（门被拆了）'
    return g, None

def 自检():
    g, err = 取()
    if err: return [err]
    f = list(g['余音自检']())
    # 造坑：把余音两头换成旧删法（原样返回），余音自检必须报
    g2 = dict(g); exec('def _余音两头(e,a,b,gap=2): return (a,b)', g2)
    g2['余音自检'].__globals__['_余音两头'] = g2['_余音两头']
    if not g2['余音自检'](): f.append('没抓到：换回旧删法（从第一个 -55 dB 帧起删），余音自检没报')
    g2['余音自检'].__globals__['_余音两头'] = g['_余音两头']
    return f

if __name__ == '__main__':
    if '--自检' in sys.argv:
        e = 自检(); print(('✘ 余音删法 自检：' + '；'.join(e)) if e else '✔ 余音删法 自检：衰减后 10 ms 内回升的余音、词头弱起音必留，停顿底噪照删，换回旧删法必报（K27）'); sys.exit(1 if e else 0)
    print(__doc__)
