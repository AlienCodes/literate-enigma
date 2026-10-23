#!/usr/bin/env python3
"""文章同步自检（规则执行机器当场跑）：在临时副本上真跑 sync_article.py（视频脚本 → 文章英文、中文、速查表）：
  S1/文32 脚本里改了的中文，同步后文章里必须是新的；S3 同步能重复运行（连跑两遍结果一样，不依赖“原始状态”）；
  S5 被隔开的意思按整句连（10 S16 elevated … to：本文：把……抬高到了……的地位）；已定稿的文章同步后不变。"""
import os, sys, json, subprocess, tempfile, shutil, glob
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); ROOT = os.path.dirname(V)
fails = []; td = tempfile.mkdtemp()
def 同步(js, md):
    r = subprocess.run(['python3', f'{T}/sync_article.py', js, md], capture_output=True, text=True)
    if r.returncode: fails.append(f'同步出错：{(r.stdout + r.stderr).strip()[-120:]}')
    return open(md).read()
try:
    d = json.load(open(f'{V}/脚本/10.json')); md0 = open(glob.glob(f'{ROOT}/新版定稿/10-*.md')[0]).read()
    js, md = f'{td}/10.json', f'{td}/10.md'; json.dump(d, open(js, 'w'), ensure_ascii=False); open(md, 'w').write(md0)
    r1 = 同步(js, md); r2 = 同步(js, md)
    if r1 != md0: fails.append('没抓到：已定稿的文章同步后变了（视频脚本和文章不一致，S1）')
    if r2 != r1: fails.append('没抓到：同步不能重复运行（连跑两遍结果不一样，S3）')
    if '本文：把……抬高到了……的地位' not in r1: fails.append('没抓到：被隔开的意思没按整句连（S5，10 S16 elevated … to）')
    c = next(c for s in d['sentences'] for c in s['chunks'] if '蒙娜丽莎' in c['zh'])
    c['zh'] = c['zh'].replace('蒙娜丽莎', '蒙娜丽莎自检改'); c['align'] = [[a, b.replace('蒙娜丽莎', '蒙娜丽莎自检改')] for a, b in c['align']]
    json.dump(d, open(js, 'w'), ensure_ascii=False)
    if '蒙娜丽莎自检改' not in 同步(js, md).split('## 中文', 1)[1].split('## 速查表', 1)[0]: fails.append('没抓到：脚本改了的中文没同步进文章（S1/文32）')
except Exception as e:
    fails.append(f'同步自检本身出错：{e}')
finally:
    shutil.rmtree(td, ignore_errors=True)
print('文章同步自检：' + ('通过（定稿文章同步后不变、重复运行结果一样、改了的中文同步进文章、被隔开的意思整句连）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
