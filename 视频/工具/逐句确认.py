#!/usr/bin/env python3
"""逐句确认（规则执行机器；译文核查 [逐句确认] 要求）：一句是新的或改过，逐条核对 T2/T3 词性、T4 方向、T5 不横跨、
T7 通顺、T8 读者看得懂、T9 对齐粗细、T13 整句读通、T21 重点词贴合语境 之后，把结论和这一句的指纹记下来；
这一句再改，指纹对不上，就要重新核对。
25 起结论逐项写：“T1没加信息：……。T3词性：<本句重点词>……。T6不生硬：……。T7通顺：……。T8看得懂：……。T21贴合语境：……”（最后一句加“T33简述讲全：……”），译文核查 [逐句格式] 查。
  python3 逐句确认.py NN S3 "核对结论（写清核了什么）"
  python3 逐句确认.py NN 全部 "依据"        （只用于已经用户审定的现状，依据里要写清楚）
脚本：工作目录有 scripts/NN.json 就用它，否则用仓库 视频/脚本/NN.json。"""
import sys, os, json, time
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); sys.path.insert(0, T)
from 译文核查 import 指纹
no, which, why = sys.argv[1].zfill(2), sys.argv[2], ' '.join(sys.argv[3:]).strip()
if len(why) < 6: sys.exit('【停止】核对结论太短：写清楚逐条核了什么')
js = f'scripts/{no}.json' if os.path.exists(f'scripts/{no}.json') else f'{V}/脚本/{no}.json'
d = json.load(open(js)); f = f'{V}/制作记录/逐句确认/{no}.json'; os.makedirs(os.path.dirname(f), exist_ok=True)
rec = json.load(open(f)) if os.path.exists(f) else {}
ids = range(1, len(d['sentences']) + 1) if which == '全部' else [int(which.lstrip('Ss'))]
for i in ids: rec[f'S{i}'] = {'指纹': 指纹(d['sentences'][i - 1]), '结论': why, '时间': time.strftime('%Y-%m-%dT%H:%M')}
json.dump(rec, open(f, 'w'), ensure_ascii=False, indent=1); print(f'第{no}篇 逐句确认已记：{", ".join(f"S{i}" for i in ids)}')
