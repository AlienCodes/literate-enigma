#!/usr/bin/env python3
"""重查记录（铁4/G9/G22）：存的视频是不是还和现行程序、现行脚本一致。按篇记在 工具/全篇重查通过.json：
键 = 程序指纹 + 这一篇存的视频 + 现行脚本，三样都没变，上次的重查结论就还算数；任何一样变了就“欠着”。
全篇核查.py --视频 逐篇重查并记；踩坑核查 文本阶段对已有定稿 4K 的篇目欠着时提醒（G22）。"""
import os, json, hashlib
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
STAMP = f'{T}/全篇重查通过.json'
def 程序指纹(t=T):   # 铁4：出片程序、排版程序（配音处理、停顿规则都在 make_video.py 里）；G27：make_video 递归 import 的全部模块（对正量、片头等）
    import sys; sys.path.insert(0, T); import 出片指纹 as Z
    return hashlib.sha256(b''.join(open(p, 'rb').read() for _, p in sorted(Z.清单([t]).items()))).hexdigest()[:16]
def _sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
def 已出片():
    P = os.path.dirname(V); out = {}
    for f in sorted(os.listdir(f'{P}/最终版4K视频')):
        if f.endswith('.mp4') and f[:2].isdigit(): out[f[:2]] = f'{P}/最终版4K视频/{f}'
    return out
def 键(no, mp4, fp=None):   # 程序 + 这一篇存的视频 + 现行脚本：三样都没变，上次的重查结论就还算数
    js = f"{V}/脚本/{no}.json"; return f'{fp or 程序指纹()}-{_sha(mp4)}-{_sha(js) if os.path.exists(js) else "无"}'   # 演练镜像里冻结样本没有新归档篇目的脚本：按“无”算（和 演练镜像.仓库底稿 一致）
def 定稿提醒(no, 已, 欠):
    """G22：已有定稿 4K 的篇目，现行脚本或程序和存的视频对不上 → 提醒必须重出 4K（2026-10-23 我改了已定稿的 21 没重出，全篇重查才查出来）"""
    if no in 已 and no in 欠:
        return f'★ [G22] 第{no}篇已有定稿 4K，现行脚本或程序和存的视频对不上（或还没重查过）：改完必须 bash 视频/工具/定稿流水线.sh {no} 重出 4K、归档（G9）'
def 欠着(stamp=STAMP, keys=None):
    """还没用现行程序重查过的已出片篇目（铁4/音29/画21：改一处，全部重查）；按篇记，查一篇记一篇，中途停了不白查"""
    if keys is None: fp = 程序指纹(); keys = {no: 键(no, p, fp) for no, p in 已出片().items()}
    try: st = json.load(open(stamp)).get('篇', {})
    except Exception: st = {}
    return [no for no, k in sorted(keys.items()) if st.get(no) != k]
