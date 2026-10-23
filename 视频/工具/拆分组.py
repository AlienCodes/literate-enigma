#!/usr/bin/env python3
"""拆分组（T34，2026-10-23）：一组里两个以上重点词、中文先后和英文一样的，自动拆开，每个重点词的中文放在它自己的英文正下方。
英文按空格切（拼回去一字不差），中文只切不改（D2）；拿不准的中间部分不单独成组（中文跟前一个重点词，英文跟后一个）。
拆完逐组看一眼（逐句确认 21 起会逼着看），再出片。
在视频工作目录下运行：python3 <工具目录>/拆分组.py NN [--写入]（不写 --写入 只列出来）"""
import os, sys, json, re
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); sys.path.insert(0, T)
import 译文核查 as Y
原话 = '用户 2026-10-23 原话：“这个避免它还是没有完美的对应到这个avert的下面……才智也没有非常非常就是非常精准的放到这个intellect的下面……你认认真真的处理一下这件事儿，立一道闸好不好？”'
no = sys.argv[1].zfill(2); p = f'scripts/{no}.json'; pp = f'{V}/脚本/{no}.json'
d = json.load(open(p)); 同步仓库 = os.path.exists(pp) and open(pp).read() == open(p).read()
改, 句 = 0, set()
for i, s in enumerate(d['sentences'], 1):
    for c in s['chunks']:
        new = []
        for a, b in c['align']:
            r = Y.拆(a, b) if a != '\n' else None
            if r: 改 += 1; 句.add(i); print(f'S{i}  ' + ' ‖ '.join(f'{x}→{y}' for x, y in r))
            new += r or [[a, b]]
        c['align'] = new
print(f'第{no}篇：拆 {改} 组（{" ".join(f"S{i}" for i in sorted(句)) or "无"}）' + ('' if '--写入' in sys.argv or not 改 else '；看过没问题加 --写入'))
if '--写入' in sys.argv and 改:
    ok = d.setdefault('换行变更已获同意', {})
    for i in sorted(句): ok.setdefault(f'S{i}', 原话 + '（T34：同序的重点词拆开，中文字不改）')
    json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
    if 同步仓库: json.dump(d, open(pp, 'w'), ensure_ascii=False, indent=1)
    q = f'{V}/制作记录/{no}_待改清单.md'; qt = open(q).read() if os.path.exists(q) else f'# 第{no}篇待改清单\n'
    if 'T34' not in qt:
        n = len(re.findall(r'^\d+\. ', qt, re.M)) + 1
        qt = qt.rstrip('\n') + f'\n{n}. 同序重点词拆开（T34，2026-10-23）：{原话}\n   - 已改：{" ".join(f"S{i}" for i in sorted(句))} 共 {改} 组拆开，每个重点词的中文放在它自己的英文正下方；中文字一个不改，只切分组。\n'
        open(q, 'w').write(qt)
    print('已写入' + ('（工作目录和仓库两处）' if 同步仓库 else '（只写了工作目录：仓库那份本来就不一样，先核对）'))
