#!/usr/bin/env python3
"""推送时 git pull 撞冲突（.jsonl、.json、视频/制作记录/ 下的 .md）：几个会话都往里追加的共享记录（.jsonl、.json）自动合并，然后提交合并；别的文件冲突照旧停（真冲突要人看）。
  .jsonl：按行合并（我的在前，别人新加的行接在后面，不重复）
  .json ：三方合并（共同祖先 / 我的 / 别人的）：字典逐键合并；列表 = 我的（去掉别人删了的）+ 别人新加的；同一个值两边改得不一样 → 停
在仓库里运行（git pull 失败之后）：python3 合并追加.py   返回 0 = 合并好并已提交；1 = 有真冲突，已 git merge --abort"""
import sys, os, json, subprocess

def g(*a, inp=None): return subprocess.run(['git', '-c', 'core.quotepath=off', *a], capture_output=True, text=True, input=inp, errors='replace')
def 版本(stage, f):
    r = subprocess.run(['git', 'show', f':{stage}:{f}'], capture_output=True)
    if r.returncode: return None
    try: return r.stdout.decode('utf-8')
    except UnicodeDecodeError: raise 真冲突('二进制文件')

class 真冲突(Exception): pass

def 合json(b, o, t):
    if o == t: return o
    if o == b: return t
    if t == b: return o
    if isinstance(o, dict) and isinstance(t, dict):
        b = b if isinstance(b, dict) else {}; out = {}
        for k in list(o) + [k for k in t if k not in o]:
            if k in o and k in t: out[k] = 合json(b.get(k), o[k], t[k])
            elif k in o:
                if k in b and b[k] == o[k]: continue   # 别人删了、我没动
                out[k] = o[k]
            else:
                if k in b and b[k] == t[k]: continue   # 我删了、别人没动
                out[k] = t[k]
        return out
    if isinstance(o, list) and isinstance(t, list):
        b = b if isinstance(b, list) else []
        return [x for x in o if not (x in b and x not in t)] + [x for x in t if x not in o and x not in b]
    raise 真冲突(f'同一个值两边改得不一样：{str(o)[:40]} / {str(t)[:40]}')

def 缩进(s):
    for l in s.splitlines()[1:3]:
        n = len(l) - len(l.lstrip(' '))
        if n: return n
    return None if '\n' not in s.strip() else 0

def 合(f):
    b, o, t = 版本(1, f), 版本(2, f), 版本(3, f)
    if o is None or t is None: raise 真冲突('一边删了文件')
    if f.endswith('.jsonl') or (f.startswith('视频/制作记录/') and f.endswith('.md')):   # K100：制作记录 NN.md 几个会话都往后追加
        ol = o.splitlines(); seen = set(ol); bl = set((b or '').splitlines())
        out = [l for l in ol if not (l in bl and l not in t.splitlines())] + [l for l in t.splitlines() if l not in seen and l not in bl]
        return '\n'.join(out) + '\n'
    if f.endswith('.json'):
        r = 合json(json.loads(b) if b else None, json.loads(o), json.loads(t)); ind = 缩进(o)
        return json.dumps(r, ensure_ascii=False, indent=ind) + ('\n' if o.endswith('\n') else '')
    raise 真冲突('不是追加型记录')

def main():
    fs = [l for l in g('diff', '--name-only', '--diff-filter=U').stdout.splitlines() if l]
    if not fs: print('【停止】git pull 失败，但没有冲突文件（网络或别的原因）'); return 1
    bad = []
    for f in fs:
        try: open(f, 'w').write(合(f)); g('add', '--', f)
        except Exception as e: bad.append(f'{f}：{e}')
    if bad:
        g('merge', '--abort'); print('【停止】推送撞上真冲突（不是追加型记录，要人看）：' + '；'.join(bad)); return 1
    r = g('commit', '-q', '--no-edit')
    print(f'自动合并追加型记录 {len(fs)} 个：' + '、'.join(fs)); return r.returncode

if __name__ == '__main__': sys.exit(main())
