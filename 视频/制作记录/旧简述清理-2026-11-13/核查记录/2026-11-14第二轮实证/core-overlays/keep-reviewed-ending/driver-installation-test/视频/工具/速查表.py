#!/usr/bin/env python3
"""速查表（G52，2026-10-25 26 定稿：定稿流水线 ④ 同步文章时给新重点词加的速查表行只有“本文：……”，缺词性和词义，当时没停、进了仓库，
下一次 check_all 才拦下，26 会话手工补了 8 行）。check_all 和 sync_article 共用这里的判断；sync_article 写完速查表当场查，缺了就停在 ④。
新词没有旧行时，先从 70 篇文章速查表里同一个词的“词性 + 词义”自动填，找不到的才停下列出来让会话补。"""
import re, glob, os
POS = r'(adj|adv|n|v|vt|vi|phr|prep|conj|pron|num|det|abbr|int|interj|aux|modal|art|短语|习语|固定搭配)\.'
def 行(t):
    """速查表每一行 (词, 释义列)"""
    if '## 速查表' not in t: return []
    out = []
    for line in t.split('## 速查表', 1)[1].split('\n## ', 1)[0].split('\n'):
        m = re.match(r'^\|\s*([^|]+?)\s*\|\s*([^|]*)\|', line)
        if m and m.group(1) not in ('词', '---'): out.append((m.group(1), m.group(2)))
    return out
def 缺词性(t):
    """只有“本文：”、没有“；词性. 词义”的词"""
    return [w for w, x in 行(t) if '本文：' in x and not re.search(r'本文：[^|]*?；\s*' + POS, x)]
def 词典(root):
    """70 篇文章速查表里每个词的“词性. 词义……”（本文义后面那一段），同一个词取最先出现的"""
    d = {}
    for f in sorted(glob.glob(os.path.join(root, '新版定稿', '[0-9][0-9]-*.md'))):
        for w, x in 行(open(f).read()):
            m = re.search(r'本文：[^|]*?；\s*(' + POS + r'[^|]*)', x)
            if m: d.setdefault(w.lower(), m.group(1).strip())
    return d
def 自检():
    e = []
    if 缺词性('## 速查表\n| 词 | 释义 | 段 |\n| zzz | 本文：只有本文 | 1 |\n') != ['zzz']: e.append('没抓到：速查表一行只有“本文：”、缺词性和词义（G52 重放 26）')
    if 缺词性('## 速查表\n| linguist | 本文：语言学家；n. 语言学家 | 4 |\n'): e.append('误报：有词性和词义的也报了')
    return e
if __name__ == '__main__':
    import sys
    e = 自检(); print('\n'.join(e) or '速查表 自检通过（只有“本文：”的行必报，有词性词义的不报）'); sys.exit(1 if e else 0)
