#!/usr/bin/env python3
"""把旧工具目录接上“看门开关”。每处只加一个判断，读 <工具>/管道.json 的 {"看门": "停用"|"启用"}；
切换 = 改这一个配置（停用由主会话写 用户同意记录 后再改）。补丁可重复打（已打过的跳过），锚找不到就停。
用法：python3 新管/切换.py <工具目录> [--停用|--启用]"""
import sys, os, json
H = os.path.dirname(os.path.abspath(__file__))
G = "__import__('管道').看门停用()"
补丁 = [   # (文件, 原文, 新文)：原文必须正好出现一次
    ('交付核查.py', "if stage in ('出片前', '出片后'):   # G60", f"if stage in ('出片前', '出片后') and not {G}:   # G60"),
    ('交付核查.py', "    c, o = run(['python3', f'{T}/规则执行核查.py']); step('规则执行核查（守则16：每条规矩都有门、接进流程、有自检，机器自检通过）', c == 0, '' if c == 0 else o.strip()[-600:])\n    c, o = run(['python3', f'{T}/用上核查.py', '--严'])",
     f"    if not {G}: c, o = run(['python3', f'{{T}}/规则执行核查.py']); step('规则执行核查（守则16：每条规矩都有门、接进流程、有自检，机器自检通过）', c == 0, '' if c == 0 else o.strip()[-600:])\n    if not {G}: c, o = run(['python3', f'{{T}}/用上核查.py', '--严'])"),
    ('交付核查.py', "elif stage == '出片后':\n    c, o = run(['python3', f'{T}/规则执行核查.py'])", f"elif stage == '出片后':\n    if not {G}: c, o = run(['python3', f'{{T}}/规则执行核查.py'])"),
    ('交付核查.py', "    c, o = run(['python3', f'{T}/收工记录.py', no]); step(", f"    if not {G}: c, o = run(['python3', f'{{T}}/收工记录.py', no]); step("),
    ('交付核查.py', "if ok and stage in ('出片前', '出片后'): _ZJ.记(no, stage)", f"if ok and stage in ('出片前', '出片后') and not {G}: _ZJ.记(no, stage)"),
    ('交付核查.py', "if not ok:   # K 丝滑记录", f"if not ok and not {G}:   # K 丝滑记录"),
    ('草稿声音.sh', "python3 $T/方法进化表.py --上下文 || exit 1", "[ \"$(python3 -c \"import sys;sys.path.insert(0,'$T');print(__import__('管道').看门停用())\")\" = True ] || python3 $T/方法进化表.py --上下文 || exit 1"),
    ('草稿声音.sh', "python3 $T/证据.py --记 $no 草稿声音", "[ \"$(python3 -c \"import sys;sys.path.insert(0,'$T');print(__import__('管道').看门停用())\")\" = True ] || python3 $T/证据.py --记 $no 草稿声音"),
    ('生成文本.py', "_m = subprocess.run(['python3', f'{T}/规则执行核查.py'], capture_output=True, text=True)", f"_m = subprocess.run(['true'] if (sys.path.insert(0, T) or {G}) else ['python3', f'{{T}}/规则执行核查.py'], capture_output=True, text=True)"),
]
管道 = '''import json, os
def 看门停用():
    """新管开关：<工具>/管道.json 写 {"看门": "停用"} 时，8 套看门机制（证据、闲置、用上核查、门变异、放行口子、规则执行核查、演练、丝滑）不再当门"""
    try: return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '管道.json'))).get('看门') == '停用'
    except Exception: return False
'''

def main():
    t = sys.argv[1]; bad = []
    open(f'{t}/管道.py', 'w').write(管道)
    for f, a, b in 补丁:
        p = f'{t}/{f}'; s = open(p).read()
        if b in s: continue
        if s.count(a) != 1: bad.append(f'{f}：锚出现 {s.count(a)} 次：{a[:50]}'); continue
        open(p, 'w').write(s.replace(a, b))
    if '--停用' in sys.argv or '--启用' in sys.argv:
        json.dump({'看门': '停用' if '--停用' in sys.argv else '启用'}, open(f'{t}/管道.json', 'w'), ensure_ascii=False)
    print('\n'.join(bad) or f'补丁 {len(补丁)} 处已打；开关 {t}/管道.json')
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
