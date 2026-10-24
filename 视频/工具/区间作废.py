#!/usr/bin/env python3
"""改了读音或语速，旧的区间、除阻、确认自动作废（A45，24 草稿会话报的共用程序问题，2026-10-24）。
非人声区间、词尾除阻、除阻加强、停顿处除阻、停顿删除区间、停顿插入点都是这一句原始合成 w 里的秒；读音、语速一改，w 就变了，
旧位置全部不对（可能落在词上，也可能落在静音里却已不是那个呼吸声）。出片程序记下每句 w 的指纹（work_NN/句子声音指纹.json），
脚本的“区间声音指纹”是写区间时的指纹：对不上 → 出片程序停（A45）；草稿声音.sh 里带 OLD_IV_VOID=1，出片程序跳过这句的旧区间，
本程序再从脚本里删掉它们和对应的旧确认，交给 自动切点 / 词尾辅音核对 重找。
在视频工作目录下：python3 区间作废.py NN            清掉作废句的旧区间、旧确认
                  python3 区间作废.py NN --记指纹   把这一轮的指纹记进 区间声音指纹（草稿声音.sh 最后一步）
                  python3 区间作废.py --自检"""
import sys, json, copy
键 = ['非人声区间', '词尾除阻', '除阻加强', '停顿处除阻', '停顿删除区间', '停顿插入点']
确认键 = ['删除段', '停顿位置', '停顿删除']


def 清(d, 作废):
    out = []
    for S in 作废:
        for k in 键:
            if S in d.get(k, {}): d[k].pop(S); out.append(f'{S} {k}')
        for k in 确认键:
            v = d.get('核对确认', {}).get(k, {})
            for x in [x for x in v if x.startswith(S + ' ')]: v.pop(x); out.append(f'{S} 核对确认.{k} {x}')
        d.get('区间声音指纹', {}).pop(S, None)
    return out


def 记(d, 指纹):
    fp = {S: v for S, v in 指纹.items() if v and any(S in d.get(k, {}) for k in 键)}
    if fp: d['区间声音指纹'] = fp
    else: d.pop('区间声音指纹', None)
    return fp


def 自检():
    fails = []
    d = {'非人声区间': {'S6': [[7.6, 7.9, '紧贴词头']], 'S7': [[4.9, 5.3]]}, '词尾除阻': {'S6': {'句末': [5.36, 't']}},
         '停顿插入点': {'S6': {'1': 2.3}}, '核对确认': {'删除段': {'S6 raw 1.0-1.2': 'x', 'S16 raw 1.0-1.2': 'y'}, '停顿位置': {'S6 a, / b @3.2': 'x'}},
         '区间声音指纹': {'S6': 'aaa', 'S7': 'bbb'}}
    e = copy.deepcopy(d); out = 清(e, ['S6'])
    if 'S6' in e['非人声区间'] or 'S6' in e['词尾除阻'] or 'S6' in e['停顿插入点'] or 'S6 raw 1.0-1.2' in e['核对确认']['删除段'] or e['核对确认']['停顿位置']:
        fails.append('没清掉：读音改过的句子（S6）旧区间、旧确认还在（A45）')
    if 'S7' not in e['非人声区间'] or 'S16 raw 1.0-1.2' not in e['核对确认']['删除段']: fails.append('A45 误删：没改读音的句子（S7、S16）的区间或确认被清掉')
    记(e, {'S6': 'ccc', 'S7': 'ddd', 'S8': 'eee'})
    if e.get('区间声音指纹') != {'S7': 'ddd'}: fails.append(f'A45 记指纹不对：只记有区间的句子，得到 {e.get("区间声音指纹")}')
    return fails


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--自检':
        f = 自检(); print('区间作废自检：' + ('通过（读音改过的句子旧区间、旧确认清掉，别的句子不动，指纹只记有区间的句子）' if not f else '失灵！' + '；'.join(f))); sys.exit(1 if f else 0)
    no = a[0].zfill(2); js = f'scripts/{no}.json'; d = json.load(open(js)); r = json.load(open(f'work_{no}/句子声音指纹.json'))
    if '--记指纹' in a:
        fp = 记(d, r['指纹']); print(f'区间声音指纹：记了 {len(fp)} 句')
    else:
        out = 清(d, r['作废'])
        print(f'读音/语速改过的句子 {" ".join(r["作废"])}：旧区间、旧确认清掉 {len(out)} 条，交给 自动切点、词尾辅音核对 重找' if r['作废'] else '区间作废：没有读音/语速改过的句子')
    json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
