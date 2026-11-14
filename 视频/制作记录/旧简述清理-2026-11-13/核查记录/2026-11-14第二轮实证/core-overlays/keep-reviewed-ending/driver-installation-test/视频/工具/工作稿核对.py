#!/usr/bin/env python3
"""工作稿核对（G19，2026-10-23）：别的会话（每篇新开会话）直接改了仓库里的 视频/脚本/NN.json 并推送，
视频工作目录里的 scripts/NN.json 还是旧的——拿旧稿出片就会出成旧版（13、16、18、20 篇这次都差点）。
仓库里的比工作目录新、内容又不同 → 停。在视频工作目录下运行：python3 <工具目录>/工作稿核对.py NN"""
import os, sys, filecmp
V = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def 旧了(w, p):
    """工作稿 w 比仓库稿 p 旧且内容不同（工作稿不存在也算）"""
    if not os.path.exists(p): return False
    if not os.path.exists(w): return True
    return not filecmp.cmp(w, p, shallow=False) and os.path.getmtime(p) > os.path.getmtime(w)
if __name__ == '__main__':
    no = sys.argv[1].zfill(2)
    if 旧了(f'scripts/{no}.json', f'{V}/脚本/{no}.json'):
        sys.exit(f'【停止】工作目录 scripts/{no}.json 比仓库 视频/脚本/{no}.json 旧（别的会话改过并推送了）：先核对再拷过来，不许拿旧稿出片（G19）')
