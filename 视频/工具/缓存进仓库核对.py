#!/usr/bin/env python3
"""缓存进仓库核对（G51，2026-10-25：撞车会话的容器重查 26，声音和现行脚本重出的差 -39.6 dB；26 是第一篇用源头调平的，
调平增益靠 ffmpeg 量响度，换机器会翻档。修法：算过的增益存成 配音缓存/调平_*.json 进仓库。这道门保证每篇定稿用到的
配音缓存、调平缓存都已在 git 里、已推送，别的机器按仓库重出逐样本相同）。
用法（视频工作目录，定稿流水线推送后自动跑）：python3 缓存进仓库核对.py NN；--自检
做法：严格缓存模式（不现合成、不重算调平）只出声音，记下用到的每条缓存，逐个查 git ls-files 和 origin/main。"""
import os, sys, subprocess, tempfile
T = os.path.dirname(os.path.abspath(__file__)); P = os.path.dirname(os.path.dirname(T))
def 缺(用到, 已跟踪, 已推送):
    return [n for n in 用到 if n not in 已跟踪], [n for n in 用到 if n in 已跟踪 and n not in 已推送]
def 自检():
    e = []; a, b = 缺(['x.pkl', '调平_1.json', 'y.pkl'], {'x.pkl', 'y.pkl', '调平_1.json'}, {'x.pkl', 'y.pkl'})
    if a or b != ['调平_1.json']: e.append(f'没抓到：调平缓存在 git 里但没推送（{a}，{b}）')
    a, b = 缺(['x.pkl', '调平_2.json'], {'x.pkl'}, {'x.pkl'})
    if a != ['调平_2.json']: e.append('没抓到：用到的调平缓存不在 git 里（G51 重放 26）')
    if any(缺(['x.pkl'], {'x.pkl'}, {'x.pkl'})): e.append('误报：都在、都推送了也报')
    return e
if __name__ == '__main__':
    if sys.argv[1:2] == ['--自检']:
        e = 自检(); print('\n'.join(e) or '缓存进仓库核对 自检通过（不在 git 里、在 git 里没推送都报；都推送了不报）'); sys.exit(1 if e else 0)
    no = sys.argv[1]
    with tempfile.TemporaryDirectory() as td:
        lg = f'{td}/用到.txt'; out = f'{td}/{no}.mp4'
        r = subprocess.run(['python3', 'make_video.py', f'scripts/{no}.json', out], env={**os.environ, 'AUDIO_ONLY': '1', 'STRICT_CACHE': '1', 'CACHE_LOG': lg}, capture_output=True, text=True)
        if r.returncode: print('【停止】严格缓存模式出不了声音（缓存不全，别的机器重出会不同）：' + (r.stdout + r.stderr).strip().splitlines()[-1][:200]); sys.exit(1)
        用到 = sorted(set(open(lg).read().split()))
    g = lambda *a: subprocess.run(['git', '-C', P, '-c', 'core.quotepath=off', *a], capture_output=True, text=True).stdout
    subprocess.run(['git', '-C', P, 'fetch', '-q', 'origin', 'main'], capture_output=True)
    已跟踪 = {os.path.basename(x) for x in g('ls-files', '视频/配音缓存').split('\n') if x}
    已推送 = {os.path.basename(x) for x in g('ls-tree', '-r', '--name-only', 'origin/main', '视频/配音缓存').split('\n') if x}
    a, b = 缺(用到, 已跟踪, 已推送)
    if a or b: print(f'【停止】第{no}篇用到的缓存没进仓库（G51）：不在 git 里 {len(a)} 条（如 {a[:3]}），没推送 {len(b)} 条（如 {b[:3]}）'); sys.exit(1)
    print(f'缓存进仓库核对：第{no}篇用到的 {len(用到)} 条缓存（配音 {sum(n.endswith(".pkl") for n in 用到)}、调平 {sum(n.startswith("调平_") for n in 用到)}）都已在 git 里、已推送')
