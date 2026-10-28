#!/usr/bin/env python3
"""验收 ③：三个会话同一时刻各自推送，零冲突、零 G2 停。在临时目录建两个假远端（主仓库 P、镜像 L），
三个会话各自克隆，各自：往共享的 丝滑/会话.jsonl 追加一行、往 用户同意记录.json 追加一条、写自己篇号的记录和草稿片，然后同时推。
查：三个都退出 0；远端 P、L 的 视频/ 逐文件一致；三行、三条、三个文件都在；JSON 合法。
用法：python3 并发测.py <装着 推送两仓库.sh 的工具目录> [--旧]  （--旧：直接跑 推送两仓库.sh，不经 新管/推送.sh，作对照）  [--轮 N]"""
import sys, os, json, subprocess, tempfile, shutil, time, threading
H = os.path.dirname(os.path.abspath(__file__)); TOOLS = os.path.abspath(sys.argv[1]); 旧 = '--旧' in sys.argv
轮 = int(sys.argv[sys.argv.index('--轮') + 1]) if '--轮' in sys.argv else 3
G = ['git', '-c', 'user.name=并发测', '-c', 'user.email=t@example.com', '-c', 'init.defaultBranch=main', '-c', 'core.quotepath=off']
ENV = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
def git(*a, cwd=None): return subprocess.run(G + list(a), cwd=cwd, capture_output=True, text=True, env=ENV)
def 写(p, s, mode='w'):
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, mode).write(s)

def 一轮(k):
    tmp = tempfile.mkdtemp(prefix='并发测_')
    git('init', '-q', '--bare', f'{tmp}/P.git'); git('init', '-q', '--bare', f'{tmp}/L.git')
    S0 = f'{tmp}/种子'; git('clone', '-q', f'{tmp}/P.git', S0)
    工 = f'{S0}/视频/工具'
    写(f'{工}/规则执行核查.py', 'import sys; sys.exit(0)\n'); 写(f'{工}/报坑.py', 'import sys; sys.exit(0)\n')
    写(f'{工}/新管/印章.py', 'import sys; sys.exit(0)\n'); shutil.copy(f'{H}/合并追加.py', f'{工}/新管/合并追加.py')
    if os.path.exists(f'{TOOLS}/管道.py'): shutil.copy(f'{TOOLS}/管道.py', f'{工}/管道.py'); 写(f'{工}/管道.json', '{"看门": "停用"}')
    写(f'{S0}/视频/制作记录/丝滑/会话.jsonl', '{"会话": "种子"}\n')
    写(f'{工}/用户同意记录.json', json.dumps({'说明': '假', '记录': [{'篇': '00', '原话': '种子'}]}, ensure_ascii=False, indent=1) + '\n')
    写(f'{S0}/.gitignore', '__pycache__/\n'); 写(f'{S0}/CLAUDE.md', '守则\n'); 写(f'{S0}/新版定稿/x.md', 'x\n'); 写(f'{S0}/最终版4K视频/y.mp4', 'v\n')
    git('add', '-A', cwd=S0); git('commit', '-qm', 'init', cwd=S0); git('push', '-q', '-u', 'origin', 'HEAD:main', cwd=S0)
    L0 = f'{tmp}/L种子'; git('clone', '-q', f'{tmp}/L.git', L0); git('checkout', '-q', '-b', 'tb', cwd=L0)
    for f in ('视频', 'CLAUDE.md', '新版定稿', '最终版4K视频'): subprocess.run(['cp', '-r', f'{S0}/{f}', f'{L0}/'])
    git('add', '-A', cwd=L0); git('commit', '-qm', 'init', cwd=L0); git('push', '-q', '-u', 'origin', 'tb', cwd=L0)
    会话 = []
    for i in range(3):
        P, L = f'{tmp}/P{i}', f'{tmp}/L{i}'
        git('clone', '-q', f'{tmp}/P.git', P); git('clone', '-q', '-b', 'tb', f'{tmp}/L.git', L)
        for r in (P, L): git('config', 'user.name', f'会话{i}', cwd=r); git('config', 'user.email', 't@example.com', cwd=r)
        n = f'{29 + i}'
        写(f'{P}/视频/制作记录/丝滑/会话.jsonl', json.dumps({'会话': i, '篇': n}, ensure_ascii=False) + '\n', 'a')
        d = json.load(open(f'{P}/视频/工具/用户同意记录.json')); d['记录'].append({'篇': n, '原话': f'会话{i} 的原话'})
        写(f'{P}/视频/工具/用户同意记录.json', json.dumps(d, ensure_ascii=False, indent=1) + '\n')
        写(f'{P}/视频/制作记录/{n}.md', f'# {n}\n'); 写(f'{P}/视频/视频/草稿1080p/{n}_1080p.mp4', f'片{n}\n')
        会话.append((i, P, L))
    结果 = {}; t0 = time.time() + 1.0
    def 推(i, P, L):
        time.sleep(max(0, t0 - time.time()))
        cmd = ['bash', f'{TOOLS}/推送两仓库.sh', f'会话{i}'] if 旧 else ['bash', f'{H}/推送.sh', f'会话{i}']
        r = subprocess.run(cmd, cwd=P, capture_output=True, text=True, timeout=300,
                           env={**ENV, 'PUSH_P': P, 'PUSH_L': L, 'PUSH_B': 'tb', 'PUSH_LOCK': f'{tmp}/锁{i}', 'XG_TOOLS': TOOLS})
        结果[i] = (r.returncode, (r.stdout + r.stderr).strip().splitlines()[-2:]); open(f'/tmp/并发测_会话{i}.log', 'w').write(r.stdout + r.stderr)
    ts = [threading.Thread(target=推, args=s) for s in 会话]; [t.start() for t in ts]; [t.join() for t in ts]
    # 远端终态
    F = f'{tmp}/终P'; git('clone', '-q', f'{tmp}/P.git', F); FL = f'{tmp}/终L'; git('clone', '-q', '-b', 'tb', f'{tmp}/L.git', FL)
    bad = [f'会话{i} 退出 {c}：{" / ".join(o)[:160]}' for i, (c, o) in sorted(结果.items()) if c]
    lp = git('ls-tree', '-r', 'HEAD', '视频', cwd=F).stdout; ll = git('ls-tree', '-r', 'HEAD', '视频', cwd=FL).stdout
    if lp != ll: bad.append('远端 P、L 的 视频/ 不一致（G2）')
    j = open(f'{F}/视频/制作记录/丝滑/会话.jsonl').read()
    if any(f'"篇": "{29 + i}"' not in j for i in range(3)): bad.append('会话.jsonl 少了行')
    try:
        d = json.load(open(f'{F}/视频/工具/用户同意记录.json'))
        if sorted(x['篇'] for x in d['记录']) != ['00', '29', '30', '31']: bad.append(f'用户同意记录 条目不对：{[x["篇"] for x in d["记录"]]}')
    except Exception as e: bad.append(f'用户同意记录.json 坏了：{e}')
    if any(not os.path.exists(f'{F}/视频/制作记录/{29 + i}.md') for i in range(3)): bad.append('有会话的记录没推上去')
    shutil.rmtree(tmp, ignore_errors=True)
    return bad

if __name__ == '__main__':
    tot = []
    for k in range(轮):
        b = 一轮(k); tot += b; print(f'第{k + 1}轮：' + ('三会话同时推，全过' if not b else '；'.join(b)))
    print(f'{"旧" if 旧 else "新管"} 并发测 {轮} 轮：' + ('零冲突、零 G2 停' if not tot else f'{len(tot)} 处不过')); sys.exit(1 if tot else 0)
