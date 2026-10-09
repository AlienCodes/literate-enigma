#!/usr/bin/env python3
"""把 postgraduate-vocabulary（main）的 视频/、新版定稿/、最终版4K视频/、考研英语精读-70篇.html、CLAUDE.md 镜像到 literate-enigma（工作分支）：
按 md5 只复制变了的文件，并删掉 literate-enigma 里这些位置上多出来的文件（P 里已删的草稿、中间进度等，G7）。
用法：python3 视频/工具/镜像同步.py [P 路径] [L 路径]；之后在 L 里 git add -A 这些位置、提交、推送，再用 diff -rq 核对两边一致。"""
import os, shutil, hashlib, sys
P = sys.argv[1] if len(sys.argv) > 1 else '/home/user/postgraduate-vocabulary'
L = sys.argv[2] if len(sys.argv) > 2 else '/home/user/literate-enigma'
TOPS = ['视频', '新版定稿', '最终版4K视频', '考研英语精读-70篇.html', 'CLAUDE.md']
def md5(f):
    h = hashlib.md5()
    with open(f, 'rb') as x:
        for b in iter(lambda: x.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def files(root):
    if os.path.isfile(root): return {'': root}
    out = {}
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d != '__pycache__']
        for f in fs:
            if f.endswith('.part'): continue
            p = os.path.join(r, f); out[os.path.relpath(p, root)] = p
    return out
nc = nd = 0
for top in TOPS:
    src, dst = os.path.join(P, top), os.path.join(L, top)
    if not os.path.exists(src): continue
    fs, fd = files(src), (files(dst) if os.path.exists(dst) else {})
    for rel, s in fs.items():
        d = os.path.join(dst, rel) if rel else dst
        if os.path.exists(d) and os.path.getsize(s) == os.path.getsize(d) and md5(s) == md5(d): continue
        os.makedirs(os.path.dirname(d), exist_ok=True); tmp = d + '.part'
        shutil.copyfile(s, tmp); os.replace(tmp, d); nc += 1; print('复制', os.path.relpath(d, L))
    for rel, d in fd.items():
        if rel not in fs:
            os.remove(d); nd += 1; print('删除', os.path.relpath(d, L))
    for r, ds, _ in os.walk(dst, topdown=False):              # 删掉空文件夹
        for x in ds:
            q = os.path.join(r, x)
            if os.path.isdir(q) and not os.listdir(q): os.rmdir(q)
print(f'复制 {nc} 个，删除 {nd} 个')
