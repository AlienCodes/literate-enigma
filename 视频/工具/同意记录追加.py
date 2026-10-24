#!/usr/bin/env python3
"""用户同意记录.json 只许追加（2026-10-24 主对话报的流程冲突）：主对话要往里追加用户原话，但它被执行效应演练印章盖住，
一追加印章就失效、规则执行核查就停，而主对话没有视频工作目录跑不了演练。改成：演练印章只盖“印章当时的那几条”（条数 + 指纹），
之后只追加新记录（旧记录逐字不变、新记录字段齐全：篇/日期/原话/用于/来源）印章照样有效；改旧记录、删记录、新记录缺字段照样停。
规则执行核查 每次跑 查() 和 自检()。"""
import os, json, hashlib, copy
T = os.path.dirname(os.path.abspath(__file__)); F = f'{T}/用户同意记录.json'
字段 = ('篇', '日期', '原话', '用于', '来源')
def 前缀(o, n):
    return hashlib.sha256(json.dumps({**{k: v for k, v in o.items() if k != '记录'}, '记录': o['记录'][:n]}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
def 印(o=None):
    o = o or json.load(open(F)); return {'条数': len(o['记录']), '指纹': 前缀(o, len(o['记录']))}
def 查(o=None, st=None):
    o = o if o is not None else json.load(open(F)); st = st if st is not None else (lambda s: s.get('_同意记录前缀'))(json.load(open(f'{T}/执行效应演练通过.json')))
    if not st: return ['执行效应演练印章里没有用户同意记录的前缀：在视频工作目录重跑 执行效应演练.py']
    n = st['条数']; R = o.get('记录', [])
    if len(R) < n or 前缀(o, n) != st['指纹']: return [f'用户同意记录.json 只许追加：印章时的前 {n} 条（或说明）被改过或删过（用户原话逐字不许动）']
    bad = [f'第{i + 1}条' for i, r in enumerate(R[n:], n) if not all(isinstance(r.get(k), str) and len(r[k].strip()) >= 2 for k in 字段)]
    return [f'用户同意记录.json 新追加的 {"、".join(bad)} 字段不齐（{"/".join(字段)} 都要写）'] if bad else []
def 自检():
    o = {'_说明': 'x', '记录': [{k: k * 2 for k in 字段} for _ in range(3)]}; st = 印(o); f = []
    a = copy.deepcopy(o); a['记录'].append({k: '新的' for k in 字段})
    if 查(a, st): f.append('误报：只追加一条齐全的新记录')
    b = copy.deepcopy(o); b['记录'][1]['原话'] = '改过'
    if not 查(b, st): f.append('没抓到：改了旧记录的原话')
    c = copy.deepcopy(o); c['记录'].pop(0)
    if not 查(c, st): f.append('没抓到：删了一条旧记录')
    d = copy.deepcopy(a); d['记录'][-1].pop('原话')
    if not 查(d, st): f.append('没抓到：新追加的记录缺原话')
    return ['用户同意记录只追加 自检：' + x for x in f]
if __name__ == '__main__':
    e = 查() + 自检(); print('\n'.join(e) or '用户同意记录只追加：通过（旧记录逐字未动、新记录字段齐全；自检通过）'); raise SystemExit(1 if e else 0)
