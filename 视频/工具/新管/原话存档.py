#!/usr/bin/env python3
"""用户原话存档：CLAUDE.md 压成一页前，把旧 CLAUDE.md 全文（每条守则连同用户原话）一字不删搬进 视频/用户原话.md；
检查：旧 CLAUDE.md 里每一段“……”引号原话，在存档里都找得到（一句都不许丢）。
  python3 原话存档.py --写入 <旧CLAUDE.md> <存档.md>    生成存档（按守则分节，正文原样）
  python3 原话存档.py --查 <旧CLAUDE.md> <存档.md>      丢了哪句就列出、返回 1
  python3 原话存档.py --自检"""
import sys, re, os, tempfile

def 原话(t):
    return [q for q in re.findall(r'“([^”]{6,})”', t)]

def 写入(src, dst, 额外=()):
    t = open(src).read(); out = ['# 用户原话存档（旧 CLAUDE.md 全文，一字不删；CLAUDE.md 一页版每条规矩带编号指向这里）', '']
    parts = re.split(r'(?m)^(?=\d+\. )', t)
    out += ['## 开头', parts[0].strip(), '']
    for p in parts[1:]:
        n = re.match(r'(\d+)\. ', p).group(1); out += [f'## 守则{n}', p.strip(), '']
    for x in 额外: out += [open(x).read().strip(), '']
    open(dst, 'w').write('\n'.join(out) + '\n')

def 查(src, dst):
    a = open(dst).read(); return [q for q in 原话(open(src).read()) if q not in a]

def 自检():
    d = tempfile.mkdtemp(); s, z = f'{d}/c.md', f'{d}/z.md'
    open(s, 'w').write('# x\n0. 规矩（用户原话：“音频坚决不可以出现任何问题”）\n1. 另一条（用户：“不要把简单的事情复杂化”）\n')
    写入(s, z); f = []
    if 查(s, z): f.append('误报：原样存档被说丢了原话')
    open(z, 'w').write(open(z).read().replace('复杂化', '复杂'))
    if not 查(s, z): f.append('没抓到：存档里少了一句原话的一个字')
    return f

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == '--自检': f = 自检(); print('原话存档 自检：' + ('通过' if not f else '；'.join(f))); sys.exit(1 if f else 0)
    if a[0] == '--写入': 写入(a[1], a[2], a[3:])
    miss = 查(a[1], a[2]); n = len(原话(open(a[1]).read()))
    print(f'原话 {n} 段，存档里找不到 {len(miss)} 段' + ''.join(f'\n  ✘ “{q[:60]}”' for q in miss)); sys.exit(1 if miss else 0)
