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
    return old.rstrip('\n') + '\n\n' + rec + ''.join('\n' + v for k, v in tail.items() if not 有节(old, k))   # G46：只认行首整行标题


def 有节(t, h): return re.search(rf'^{re.escape(h)}[^\n]*$', t or '', re.M) is not None   # G46：只认行首整行标题（正文里提到“## 方法设计”不算）
def 开工(V, no, 记当前=True, 根=None):
    """G46（25、26 都中过）：原来 open(f,'w').write(合成(open(f).read() …)) 先清空文件再读，读到空串，方法设计被冲成空模板。先读后写"""
    f = f'{V}/制作记录/{no}.md'; old = open(f).read() if os.path.exists(f) else None
    if 有节(old, '## 踩坑对照记录'): return f'{f} 已有踩坑对照记录，不覆盖', 1
    rows = []
    for l in open(f'{V}/制作硬性标准与踩坑总结.md'):   # 总表只有一份（规则执行机器 ⑤）
        m = re.match(r'\| (\w+) \| ([^|]{0,40})', l)
        if m and m.group(1) not in ('编号',) and re.match(r'[A-Z]\d', m.group(1)):
            rows.append(f'| {m.group(1)} | {m.group(2).strip()} | 涉及 | ' + ('待填（只有人能判：写明本篇具体怎么做的）' if m.group(1) in ('G6', 'C3', 'C4') else '按现行做法由程序把关（踩坑总表“拦住”），本篇核查通过') + ' |')
    new = 合成(old, no, rows, __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M'))
    open(f, 'w').write(new)
    if 记当前: open(f'{V}/制作记录/当前篇.txt', 'w').write(no); open(os.path.expanduser('~/.当前篇'), 'w').write(no)   # 本容器自己的当前篇优先（钩子先读它）   # 钩子据此每轮更新这篇的 token 记录（T31）
    import subprocess   # J（用户 2026-10-25）：开工就把本篇撞车提醒写进制作记录并打印，发草稿时告诉用户
    out = subprocess.run(['python3', f'{os.path.dirname(os.path.abspath(__file__))}/check_all.py', '--写提醒', no] + (['--根', 根] if 根 else []), capture_output=True, text=True).stdout.strip()
    return f'{f}：{len(rows)} 条\n{out}', 0
def 方法设计节(t):
    m = re.search(r'^## 方法设计[^\n]*\n[\s\S]*?(?=^## |\Z)', t, re.M); return m.group(0) if m else ''
def 自检():
    """G46 造坑：方法设计写全、正文里提到“## 撞车提醒”“## 方法设计”字样；跑 开工 和 --写提醒 后方法设计一字不变、撞车提醒只有一节"""
    import tempfile, shutil
    V0 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); r = tempfile.mkdtemp(prefix='开工记录自检_'); f = []
    try:
        V = f'{r}/视频'; os.makedirs(f'{V}/制作记录'); os.makedirs(f'{r}/新版定稿'); shutil.copy(f'{V0}/制作硬性标准与踩坑总结.md', V)
        open(f'{r}/新版定稿/98-x.md', 'w').write('## 英文\nA **glacier** here.\n## 中文\n'); open(f'{r}/新版定稿/97-y.md', 'w').write('## 英文\nThe **glaciers**.\n## 中文\n')
        md = ('# 第98篇\n\n## 方法设计\n- 步骤：照草稿流程；下面“## 撞车提醒”是程序写的，“## 方法设计”这一节别冲掉\n- 预计调用：50–70 次\n- 预计 token：约 2M\n'
              '- 为什么有效：先例\n\n## token 记录\n- 开工时刻：x\n')
        open(f'{V}/制作记录/98.md', 'w').write(md); a0 = 方法设计节(md)
        msg, c = 开工(V, '98', 记当前=False, 根=r); t1 = open(f'{V}/制作记录/98.md').read()
        if 方法设计节(t1) != a0: f.append('没抓到：跑 开工记录 后方法设计变了（G46：先清空再读，冲成空模板）')
        if len(re.findall(r'^## 撞车提醒', t1, re.M)) != 1 or 'glacier' not in t1.split('## 撞车提醒')[-1]: f.append('开工后撞车提醒节不对（应恰好一节、列出撞车词）')
        import subprocess
        subprocess.run(['python3', f'{os.path.dirname(os.path.abspath(__file__))}/check_all.py', '--写提醒', '98', '--根', r], capture_output=True)
        t2 = open(f'{V}/制作记录/98.md').read()
        if 方法设计节(t2) != a0 or len(re.findall(r'^## 撞车提醒', t2, re.M)) != 1: f.append('没抓到：重跑 --写提醒 冲掉了方法设计或多出一节（G46：正文提到“## 撞车提醒”被当成标题）')
        if not any(x in 合成('# x\n\n正文提到“## 方法设计”\n', '98', [], 'now') for x in ('\n## 方法设计（T31',)): f.append('没抓到：正文提到“## 方法设计”就不补方法设计节（G46）')
    finally: shutil.rmtree(r, ignore_errors=True)
    return ['开工记录 自检：' + x for x in f]
if __name__ == '__main__':
    if '--自检' in sys.argv:
        e = 自检(); print('\n'.join(e) or '开工记录 自检通过（已有方法设计一字不变、正文提到标题字样不误认、撞车提醒只写一节）'); sys.exit(1 if e else 0)
    V = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); msg, c = 开工(V, sys.argv[1].zfill(2)); print(msg); sys.exit(c)
