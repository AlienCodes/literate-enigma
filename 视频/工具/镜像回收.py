#!/usr/bin/env python3
"""镜像回收：新开的会话拿不到 postgraduate-vocabulary 的权限时，只能把成果推到 literate-enigma 工作分支。
这里按“那一次提交”逐个文件取回（不取工作分支最新状态：别的会话推送 P 时会按 P 覆盖工作分支，提交本身还在历史里），
写进 postgraduate-vocabulary 的同一路径；只收 视频/、新版定稿/、最终版4K视频/。收过的提交记进 制作记录/镜像回收.json，不重复收。
用法：python3 镜像回收.py "重新对齐、重出 4K"     （提交说明里含这几个字的都收）
收完由主会话跑 推送两仓库.sh（规则执行核查、镜像核对照常）。"""
import os, sys, json, subprocess
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
L, B = '/home/user/literate-enigma', 'claude/adoring-hamilton-5qskmm'
REC = f'{V}/制作记录/镜像回收.json'
def g(*a, cwd=L): return subprocess.run(['git', '-c', 'core.quotepath=off', *a], cwd=cwd, capture_output=True, text=True).stdout
key = sys.argv[1]
subprocess.run(['git', 'fetch', '-q', 'origin', B], cwd=L)
done = set(json.load(open(REC))) if os.path.exists(REC) else set()
hs = [h for h in g('log', '--format=%H', '--grep', key, f'origin/{B}').split() if h not in done]
got = []
for h in reversed(hs):
    msg = g('log', '-1', '--format=%s', h).strip()
    for line in g('diff-tree', '--no-commit-id', '-r', '--name-status', f'{h}^', h).splitlines():
        st, path = line.split('\t', 1)[0], line.split('\t')[-1]
        if not path.startswith(('视频/', '新版定稿/', '最终版4K视频/')): continue
        dst = f'{P}/{path}'
        if st.startswith('D'):
            if os.path.exists(dst): os.remove(dst)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            data = subprocess.run(['git', 'show', f'{h}:{path}'], cwd=L, capture_output=True).stdout
            open(dst, 'wb').write(data)
        got.append(path)
    done.add(h); print(f'收回 {h[:8]} {msg[:40]}')
json.dump(sorted(done), open(REC, 'w'), indent=0)
print(f'共收回 {len(hs)} 次提交、{len(set(got))} 个文件' if hs else '没有新的提交要收')
