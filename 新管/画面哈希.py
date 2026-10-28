#!/usr/bin/env python3
"""每一屏重画（与 定稿视频核对 同一个 render_screens，与 make_video.build 同一套画法），打印每屏像素哈希的 JSON 列表。
在出片工作目录运行：python3 新管/画面哈希.py NN"""
import sys, os, json, hashlib, tempfile
T = os.environ.get('旧工具', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '视频', '工具'))
sys.path.insert(0, T)
import 定稿视频核对 as DH
no = sys.argv[1].zfill(2); d = json.load(open(f'scripts/{no}.json')); d.setdefault('no', no)
with tempfile.TemporaryDirectory() as td:
    out = DH.render_screens(d, td)
print(json.dumps([f'{n}:{hashlib.sha256(g.tobytes()).hexdigest()[:16]}' for n, g in out], ensure_ascii=False))
