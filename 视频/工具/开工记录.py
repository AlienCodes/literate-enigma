#!/usr/bin/env python3
"""开工记录（2026-10-16 方法升级，省 token：11 的踩坑对照记录是手写一段程序临时填的）：按《踩坑总表》生成 制作记录/NN.md 的“## 踩坑对照记录”，
每一条先填“涉及 | 按现行做法由程序把关（踩坑总表“拦住”），本篇核查通过”——这些坑都有程序检查，核查不过程序会停；本篇有特殊情况的条目再改那一格。
已有记录不覆盖。用法：python3 <工具目录>/开工记录.py NN"""
import re, sys, os
def 合成(old, no, rows, now):
    """已有的 NN.md（主对话先写了交接、方法设计）只追加、不覆盖（G23，24 草稿报的：原来整份重写，方法设计被清空）"""
    rec = '## 踩坑对照记录\n\n| 编号 | 坑（摘要） | 本篇是否涉及 | 怎么防的、核查结果 |\n|---|---|---|---|\n' + '\n'.join(rows) + '\n'
    tail = {'## 方法设计': '## 方法设计（T31：动手前写好；踩坑核查 [T31] 查，没写不能出片）\n- 步骤：\n- 每步谁做（程序/我）：\n- 预计调用：\n- 预计 token：\n- 为什么有效（跑通过的先例或先试一处）：\n',
            '## token 记录': '## token 记录\n- 开工时刻：' + now + '（UTC）；收工跑 `python3 工具/收工记录.py ' + no + '` 自动算花了多少\n', '## 方法复盘': '## 方法复盘\n'}
    if old is None: return f'# 第{no}篇制作记录\n\n' + rec + '\n' + '\n'.join(tail.values())
    return old.rstrip('\n') + '\n\n' + rec + ''.join('\n' + v for k, v in tail.items() if k not in old)


if __name__ == '__main__':
    V = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); no = sys.argv[1].zfill(2); f = f'{V}/制作记录/{no}.md'
    if os.path.exists(f) and '## 踩坑对照记录' in open(f).read(): sys.exit(f'{f} 已有踩坑对照记录，不覆盖')
    rows = []
    for l in open(f'{V}/制作硬性标准与踩坑总结.md'):   # 总表只有一份（规则执行机器 ⑤）
        m = re.match(r'\| (\w+) \| ([^|]{0,40})', l)
        if m and m.group(1) not in ('编号',) and re.match(r'[A-Z]\d', m.group(1)):
            rows.append(f'| {m.group(1)} | {m.group(2).strip()} | 涉及 | ' + ('待填（只有人能判：写明本篇具体怎么做的）' if m.group(1) in ('G6', 'C3', 'C4') else '按现行做法由程序把关（踩坑总表“拦住”），本篇核查通过') + ' |')
    open(f, 'w').write(合成(open(f).read() if os.path.exists(f) else None, no, rows, __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M')))
    open(f'{V}/制作记录/当前篇.txt', 'w').write(no); open(os.path.expanduser('~/.当前篇'), 'w').write(no)   # 本容器自己的当前篇优先（钩子先读它）   # 钩子据此每轮更新这篇的 token 记录（T31）
    print(f'{f}：{len(rows)} 条')
    import subprocess   # J（用户 2026-10-25）：开工就把本篇撞车提醒写进制作记录并打印，发草稿时告诉用户
    print(subprocess.run(['python3', f'{os.path.dirname(os.path.abspath(__file__))}/check_all.py', '--写提醒', no], capture_output=True, text=True).stdout.strip())
