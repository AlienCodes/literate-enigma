#!/usr/bin/env python3
"""破折号禁用（T36，CLAUDE.md 第18条，24 起）。
用户 2026-10-24 原话：“以后我们坚决不可以使用破折号，知道吗？就是破折号以后我们坚决不用在视频里面……把这个定为绝对的规矩啊……
而且一定一定一定要保证这个规矩绝对要跑起来，在以后所有的视频里面。当前现在所有的这个视频先不要去乱改了。”
范围：视频里出现的一切文字（英文正文、中文译文、说明、结尾解说、标题）和配音读的文字。
禁用：— – ― ─ ⸺ ⸻ ﹘ － ——、“--”、两边带空格的“ - ”。单词内连字符（well-known、3,008-metre）不算。
英文原文有破折号：英文不得改动的第三个例外，换成逗号、冒号或括号，同步文章，记进 核对确认.破折号（英文一致() 认这个例外）。
  python3 破折号.py --自检
  python3 破折号.py --清单 01 23   列出这些篇定稿脚本里的破折号（只列不改）"""
import re, sys, os, json
起 = 24
DASH = re.compile(r'[—–―─⸺⸻﹘－]+|--|(?<=\s)-(?=\s)')
_PH = '\x00'
_DASH_SP = re.compile(r'\s*(?:[—–―─⸺⸻﹘－]+|--|(?<=\s)-(?=\s))\s*')


def 字段(d):
    """(位置, 文字)：画面上出现、配音读到的每一段文字（核对确认里记的原文不算）"""
    out = [('标题英文', d.get('title_en', '')), ('标题中文', d.get('title_zh', ''))]
    for i, s in enumerate(d.get('sentences', []), 1):
        for k, c in enumerate(s['chunks'], 1):
            for f in ('en', 'zh', 'note'):
                if c.get(f): out.append((f'S{i}-{k} {f}', c[f]))
    return out


def 查(d, no=None):
    if no is not None and str(no).isdigit() and int(no) < 起: return []
    out = []
    for pos, t in 字段(d):
        for m in DASH.finditer(t):
            out.append(f'[T36] {pos} 有破折号“{m.group(0)}”：{t[max(0, m.start() - 12):m.end() + 12]}  ← 用户 2026-10-24：“以后我们坚决不可以使用破折号”；中文按意思换成“，”“：”或括号（字义不改），英文换成逗号、冒号或括号并同步文章、记进 核对确认.破折号')
    return out


def 英文一致(script_en, art_en):
    """脚本英文与文章英文逐字一致（去掉空白、*）；唯一放宽：文章里的破折号在脚本里换成了逗号、冒号、分号或括号（T36 例外）"""
    ns = lambda x: re.sub(r'[\*\s]', '', x)
    if ns(script_en) == ns(art_en): return True
    if not _DASH_SP.search(art_en): return False
    parts = [re.escape(ns(p)) for p in _DASH_SP.split(art_en)]
    return re.fullmatch(r'[,:;()]{1,2}'.join(parts), ns(script_en)) is not None


def 自检():
    fails = []
    ok = {'no': '24', 'title_en': 'Survival', 'title_zh': '冰海求生', 'sentences': [{'chunks': [{'en': 'a well-known 3,008-metre wreck', 'zh': '一艘著名的、位于3,008米深处的沉船', 'note': '（简述：沉船，找到了）'}]}]}
    if 查(ok): fails.append('T36 误报：单词内连字符被报出')
    import copy
    for bad, why in [('zh', '他们——全体船员'), ('note', '（简述：沉船—找到了）'), ('en', 'the ship -- lost'), ('en', 'the ship - lost'), ('en', 'the ship – lost'), ('zh', '他们－全体')]:
        b = copy.deepcopy(ok); b['sentences'][0]['chunks'][0][bad] = why
        if not 查(b): fails.append(f'没抓到：{bad} 里的破折号“{why}”（T36）')
    b = copy.deepcopy(ok); b['title_zh'] = '冰海——求生'
    if not 查(b): fails.append('没抓到：标题里的破折号（T36）')
    b = copy.deepcopy(ok); b['no'] = '23'; b['sentences'][0]['chunks'][0]['zh'] = '他们——全体'
    if 查(b, '23'): fails.append('T36 误报：24 以前已定稿篇目被报出（用户：当前的视频先不要乱改）')
    if not 查(b, '24'): fails.append('没抓到：24 起的破折号（T36）')
    art = 'They sailed on — all of them — into the ice.'
    if not 英文一致('They sailed on, all of them, into the ice.', art): fails.append('英文一致 误报：破折号换成逗号（T36 例外）被判成英文改了')
    if not 英文一致('They sailed on (all of them) into the ice.', art): fails.append('英文一致 误报：破折号换成括号被判成英文改了')
    if 英文一致('They sailed on, all of us, into the ice.', art): fails.append('没抓到：换破折号时顺带改了词（D3）')
    if 英文一致('They sailed, on all of them into the ice.', 'They sailed on all of them into the ice.'): fails.append('没抓到：文章没有破折号却多了标点（D3）')
    return fails


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--清单':
        V = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); lo, hi = int(a[1]), int(a[2]); tot = 0
        for n in range(lo, hi + 1):
            p = f'{V}/脚本/{n:02d}.json'
            if not os.path.exists(p): continue
            d = json.load(open(p)); hits = [(pos, m.group(0), t[max(0, m.start() - 14):m.end() + 14].replace('\n', ' ')) for pos, t in 字段(d) for m in DASH.finditer(t)]
            tot += len(hits)
            print(f'\n## {n:02d} {d.get("title_zh", "")}（{len(hits)} 处）')
            for pos, ch, ctx in hits: print(f'- {pos}：“{ch}” …{ctx}…')
        print(f'\n合计 {tot} 处'); sys.exit(0)
    f = 自检(); print('破折号自检：' + ('通过（造出来的破折号全部抓到，单词内连字符、24 以前篇目不误报，换标点的例外认得）' if not f else '失灵！' + '；'.join(f))); sys.exit(1 if f else 0)
