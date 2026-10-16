#!/usr/bin/env python3
"""发音词典带锁写入（2026-10-16，几篇同时做时防互相覆盖）：python3 写入.py 表名 '{"词": {...}}'
表名：已核实读音 / 读音改正 / 多音词核对。只增改给出的键，其余不动。"""
import json, sys, fcntl, os
D = os.path.dirname(os.path.abspath(__file__)); name, patch = sys.argv[1], json.loads(sys.argv[2])
f = f'{D}/{name}.json'
with open(f'{D}/.写入.lock', 'w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX); d = json.load(open(f)); d.update(patch)
    tmp = f + '.tmp'; json.dump(d, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, f)
print(f'{name}：写入 {len(patch)} 条')
