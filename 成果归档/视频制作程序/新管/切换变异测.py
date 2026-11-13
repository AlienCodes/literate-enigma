#!/usr/bin/env python3
"""切换补丁的本地门变异：每一行新门单独拆掉（换回原文），对应的确定性场景必须发现（场景从“过”变成“不过”）。
推送两仓库.sh 的新门在假远端里真跑；G35、K97 由 快测 的常规规则样本判。等价变异（拆了哪个场景都看不出）的行不许进切换补丁。
用法：python3 切换变异测.py <干净的旧工具目录（视频/工具）>"""
import sys, os, json, subprocess, tempfile, shutil, importlib.util
H = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(sys.argv[1])
G = ['git', '-c', 'user.name=变异测', '-c', 'user.email=t@example.com', '-c', 'init.defaultBranch=main', '-c', 'core.quotepath=off']
ENV = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
def git(*a, cwd=None): return subprocess.run(G + list(a), cwd=cwd, capture_output=True, text=True, env=ENV)
def 写(p, s, mode='w'): os.makedirs(os.path.dirname(p), exist_ok=True); open(p, mode).write(s)
spec = importlib.util.spec_from_file_location('qh', f'{H}/切换.py'); QH = importlib.util.module_from_spec(spec); spec.loader.exec_module(QH)

def 工具(变异=None):
    """打好切换补丁的工具副本；变异=(文件, 新文) → 把这一处补丁换回原文"""
    t = tempfile.mkdtemp(prefix='切换变异_'); shutil.copytree(SRC, f'{t}/视频/工具', symlinks=True, ignore=shutil.ignore_patterns('__pycache__', '演练样本', '历史版本'))
    for d in ('脚本', '制作记录'): os.symlink(f'{os.path.dirname(SRC)}/{d}', f'{t}/视频/{d}')   # 快测样本读 27/24/29 的脚本、各篇制作记录
    t = f'{t}/视频'; subprocess.run(['python3', f'{H}/切换.py', f'{t}/工具', '--停用'], capture_output=True)
    if 变异:
        f, a, b = 变异; p = f'{t}/工具/{f}'; s = open(p).read(); assert s.count(b) == 1, (f, b[:40]); open(p, 'w').write(s.replace(b, a))
    return f'{t}/工具'

def 假仓库(tmp, 印章退出=0):
    git('init', '-q', '--bare', f'{tmp}/P.git'); git('init', '-q', '--bare', f'{tmp}/L.git'); S0 = f'{tmp}/种子'; git('clone', '-q', f'{tmp}/P.git', S0); 工 = f'{S0}/视频/工具'
    写(f'{S0}/.gitignore', '__pycache__/\n'); 写(f'{工}/规则执行核查.py', 'import sys; sys.exit(0)\n'); 写(f'{工}/报坑.py', 'import sys; sys.exit(0)\n')
    写(f'{工}/新管/印章.py', f'import sys; sys.exit({印章退出})\n'); shutil.copy(f'{H}/合并追加.py', f'{工}/新管/合并追加.py')
    写(f'{工}/管道.py', QH.管道); 写(f'{工}/管道.json', '{"看门": "停用"}')
    写(f'{S0}/视频/制作记录/丝滑/会话.jsonl', '{"会话": "种子"}\n'); 写(f'{S0}/视频/a.md', '一行\n')
    写(f'{S0}/CLAUDE.md', '守则\n'); 写(f'{S0}/新版定稿/x.md', 'x\n'); 写(f'{S0}/最终版4K视频/y.mp4', 'v\n')
    git('add', '-A', cwd=S0); git('commit', '-qm', 'init', cwd=S0); git('push', '-q', '-u', 'origin', 'HEAD:main', cwd=S0)
    L0 = f'{tmp}/L种子'; git('clone', '-q', f'{tmp}/L.git', L0); git('checkout', '-q', '-b', 'tb', cwd=L0)
    for f in ('视频', 'CLAUDE.md', '新版定稿', '最终版4K视频'): subprocess.run(['cp', '-r', f'{S0}/{f}', f'{L0}/'])
    git('add', '-A', cwd=L0); git('commit', '-qm', 'init', cwd=L0); git('push', '-q', '-u', 'origin', 'tb', cwd=L0)
def 会话(tmp, i):
    P, L = f'{tmp}/P{i}', f'{tmp}/L{i}'; git('clone', '-q', f'{tmp}/P.git', P); git('clone', '-q', '-b', 'tb', f'{tmp}/L.git', L)
    for r in (P, L): git('config', 'user.name', f'会话{i}', cwd=r); git('config', 'user.email', 't@example.com', cwd=r)
    return P, L
def 推(工具目录, tmp, P, L, i):
    r = subprocess.run(['bash', f'{工具目录}/推送两仓库.sh', f'会话{i}'], cwd=P, capture_output=True, text=True, timeout=300,
                       env={**ENV, 'PUSH_P': P, 'PUSH_L': L, 'PUSH_B': 'tb', 'PUSH_LOCK': f'{tmp}/锁{i}'})
    return r.returncode, r.stdout + r.stderr
def 远端(tmp, f, br='main'):
    d = tempfile.mkdtemp(); git('clone', '-q', '-b', br, f'{tmp}/{"P" if br == "main" else "L"}.git', d); return open(f'{d}/{f}').read() if os.path.exists(f'{d}/{f}') else ''

def 场景_印章(t):   # 印章对不上 → 推送必停，远端没有这次提交
    tmp = tempfile.mkdtemp(); 假仓库(tmp, 印章退出=1); P, L = 会话(tmp, 0); 写(f'{P}/视频/b.md', 'b\n')
    c, o = 推(t, tmp, P, L, 0); return c != 0 and not 远端(tmp, '视频/b.md')
def 场景_主仓库拉取(t):   # 别人先推了 会话.jsonl：第一次 pull 撞冲突 → 自动合并，两行都在
    tmp = tempfile.mkdtemp(); 假仓库(tmp); A = 会话(tmp, 0); B = 会话(tmp, 1)
    写(f'{A[0]}/视频/制作记录/丝滑/会话.jsonl', '{"会话": 0}\n', 'a'); 写(f'{B[0]}/视频/制作记录/丝滑/会话.jsonl', '{"会话": 1}\n', 'a')
    git('add', '-A', cwd=B[0]); git('commit', '-qm', 'b', cwd=B[0])   # B 先在本地提交（推送两仓库 的 git pull 之前就有本地提交）
    c0, _ = 推(t, tmp, *A, 0); c1, o = 推(t, tmp, *B, 1); j = 远端(tmp, '视频/制作记录/丝滑/会话.jsonl')
    return c0 == 0 and c1 == 0 and '"会话": 0' in j and '"会话": 1' in j
def 场景_镜像拉取(t):   # 镜像本地有上一遍没推上去的提交、远端镜像被别人推了 → 镜像 pull 撞冲突 → 自动合并
    tmp = tempfile.mkdtemp(); 假仓库(tmp); A = 会话(tmp, 0); B = 会话(tmp, 1)
    写(f'{A[0]}/视频/制作记录/丝滑/会话.jsonl', '{"会话": 0}\n', 'a'); c0, _ = 推(t, tmp, *A, 0)
    写(f'{B[1]}/视频/制作记录/丝滑/会话.jsonl', '{"会话": "1镜像"}\n', 'a'); git('add', '-A', cwd=B[1]); git('commit', '-qm', '上一遍', cwd=B[1])
    写(f'{B[0]}/视频/c.md', 'c\n'); c1, o = 推(t, tmp, *B, 1)
    return c0 == 0 and c1 == 0 and 远端(tmp, '视频/c.md', 'tb') == 'c\n' and '"会话": 0' in 远端(tmp, '视频/制作记录/丝滑/会话.jsonl', 'tb')
def 场景_真冲突(t):   # 两个会话改了同一个普通文件的同一行 → 后推的必须停（不许自动合并），远端保留先推的
    tmp = tempfile.mkdtemp(); 假仓库(tmp); A = 会话(tmp, 0); B = 会话(tmp, 1)
    写(f'{A[0]}/视频/a.md', 'A 改\n'); 写(f'{B[0]}/视频/a.md', 'B 改\n'); git('add', '-A', cwd=B[0]); git('commit', '-qm', 'b', cwd=B[0])
    c0, _ = 推(t, tmp, *A, 0); c1, o = 推(t, tmp, *B, 1)
    return c0 == 0 and c1 != 0 and 远端(tmp, '视频/a.md') == 'A 改\n'

def 快测样本(t, 名):
    r = subprocess.run(['python3', '-c', f'import sys; sys.argv=["快测"]; sys.path.insert(0, "{H}"); import 快测 as K; print("\\n".join(K.常规规则()))'],
                       capture_output=True, text=True, env={**ENV, 'XG_TOOLS': t}, cwd=H)
    return 名 not in (r.stdout + r.stderr)   # True = 这一类样本全过

def main():
    def 找(f, 头):
        hs = [(ff, a, b) for ff, a, b in QH.补丁 if ff == f and a.startswith(头)]
        assert len(hs) == 1, (f, 头, len(hs)); return hs[0]
    项 = [('推送前查印章（推送两仓库.sh）', 找('推送两仓库.sh', 'python3 $P/视频/工具/规则执行核查.py ||'), 场景_印章),
          ('主仓库 pull 自动合并（推送两仓库.sh）', 找('推送两仓库.sh', 'git pull -q --no-rebase --no-edit origin main   # 2026-10-22'), 场景_主仓库拉取),
          ('镜像 pull 自动合并（推送两仓库.sh）', 找('推送两仓库.sh', 'git pull -q --no-rebase --no-edit origin $B)'), 场景_镜像拉取),
          ('G35 简述整屏常规（render.py）', 找('render.py', '    NOTE_RIGHT.clear()'), lambda t: 快测样本(t, 'G35')),
          ('K97 汇总只算出过片（方法进化表.py）', 找('方法进化表.py', "    for no, v in 篇.items():"), lambda t: 快测样本(t, 'G65')),
          ('K97 排队篇不拦（方法进化表.py）', 找('方法进化表.py', "    if no not in 行: return"), lambda t: 快测样本(t, 'G65'))]
    t0 = 工具(); 原样 = {n: s(t0) for n, _, s in 项}; 原样['真冲突必停'] = 场景_真冲突(t0)
    print('原样：' + ('全过' if all(原样.values()) else '不过 ' + '、'.join(k for k, v in 原样.items() if not v)))
    漏 = []
    for n, v, s in 项:
        tm = 工具(v); ok = s(tm); print(f'拆 {n}：' + ('被发现' if not ok else '没人发现')); 漏 += [n] if ok else []
    print('切换补丁门变异：' + (f'{len(项)} 道全被发现' if not 漏 else f'漏 {len(漏)}：' + '、'.join(漏)))
    sys.exit(1 if 漏 or not all(原样.values()) else 0)

if __name__ == '__main__': main()
