#!/usr/bin/env python3
"""快测印章（替代 证据链 / 用上核查 / 规则执行核查 的“拦人”作用）：
快测通过时盖章 = 规则表版本 + 全部检查程序和出片程序的哈希。程序或规则表一改，章就对不上：
提交、推送、做.sh、定稿.sh 都先查章，对不上就停（先跑快测）。数据（各篇脚本、发音词典、制作记录）不进哈希，改它们不用重跑快测。
  python3 印章.py --查     对不上返回 1，并列出改了的程序
  python3 印章.py --盖     （快测通过后由 快测.py 调用）"""
import sys, os, re, json, glob, hashlib
H = os.path.dirname(os.path.abspath(__file__))
def 工具目录():
    p = os.path.dirname(H)
    return p if os.path.exists(f'{p}/交付核查.py') else os.environ.get('XG_TOOLS', f'{os.path.dirname(H)}/视频/工具')
T = os.environ.get('XG_TOOLS') or 工具目录()
章 = f'{H}/快测通过.json'

def 程序哈希():
    fs = []
    for root in (T, H):
        for f in glob.glob(f'{root}/**/*', recursive=True):
            r = os.path.relpath(f, root)
            要 = os.path.isfile(f) and not ('__pycache__' in r or '历史版本' in r or '已淘汰' in r or r.startswith(('演练样本', '发音词典', '新管/')))   # 目录、缓存、历史版本不算程序（不是放行口子：程序一个不漏）
            if 要 and (f.endswith(('.py', '.sh')) or r.startswith('githooks/') or r in ('规则表.json', '管道.json')):
                if re.match(r'gen\d+\.py$', os.path.basename(f)): continue   # 各篇 genNN 是数据
                fs.append((('新管/' if root == H else '') + r, f))
    h = {r: hashlib.sha256(open(f, 'rb').read()).hexdigest()[:16] for r, f in sorted(fs)}
    return h

def 盖():
    表 = json.load(open(f'{H}/规则表.json'))
    json.dump({'规则表版本': 表['版本'], '程序': 程序哈希()}, open(章, 'w'), ensure_ascii=False, indent=0)

def 查():
    if not os.path.exists(章): return ['没有快测印章：先跑 python3 新管/快测.py']
    c = json.load(open(章)); now = 程序哈希(); 表 = json.load(open(f'{H}/规则表.json'))
    bad = [f'规则表版本变了（{c["规则表版本"]} → {表["版本"]}）'] if c['规则表版本'] != 表['版本'] else []
    改 = sorted(k for k in set(now) | set(c['程序']) if now.get(k) != c['程序'].get(k))
    if 改: bad.append(f'快测通过后改了 {len(改)} 个程序：{"、".join(改[:8])}{"……" if len(改) > 8 else ""}；先跑快测')
    return bad

if __name__ == '__main__':
    if '--盖' in sys.argv: 盖(); print('快测印章已盖'); sys.exit(0)
    b = 查(); print('\n'.join(b) or '快测印章对得上'); sys.exit(1 if b else 0)
