#!/usr/bin/env python3
"""机械错误的标准修法（只做不改意思的事；改了什么全部列进报告给用户看）：
  破折号（T36/守则18）：中文、说明 → “，”；英文 → “, ”（文章一致性检查已认这个例外）。改完复核 D2（align 拼回来要等于原文），不等就退回、交人改
  L19/L16 说明折行：调现有 说明分行.py NN --写入
  T38 形容词重点词的“的”并进标色：**不便**(inconvenient)的 → **不便的**(inconvenient)（只认文章速查表本文词性 adj. 的重点词）
用法（在出片工作目录）：python3 修.py NN   打印改了的每一处；返回 0；python3 修.py --自检"""
import sys, os, re, json, subprocess, copy
H = os.path.dirname(os.path.abspath(__file__))
T = os.environ.get('XG_TOOLS') or (os.path.dirname(H) if os.path.exists(f'{os.path.dirname(H)}/交付核查.py') else f'{os.path.dirname(H)}/视频/工具')
sys.path.insert(0, T)
import 破折号 as PZ

ZH = re.compile(r'\s*(?:(?!(?<=\d)–(?=\d))[—–―─⸺⸻﹘－]+|--)\s*')
EN = re.compile(r'\s*(?:(?!(?<=\d)–(?=\d))[—–―─⸺⸻﹘－]+|--|(?<=\s)-(?=\s))\s*')
ns = lambda x: re.sub(r'[\*\s]', '', re.sub(r'\{\{.*?\}\}', '', x))

def 破折号(d):
    改 = []
    for k in ('title_zh',):
        if ZH.search(d.get(k, '')): n = ZH.sub('，', d[k]); 改.append(f'标题中文：{d[k]} → {n}'); d[k] = n
    for i, s in enumerate(d['sentences'], 1):
        for j, c in enumerate(s['chunks'], 1):
            old = copy.deepcopy(c)
            if c.get('note') and ZH.search(c['note']): c['note'] = ZH.sub('，', c['note'])
            if ZH.search(c.get('zh', '')) or EN.search(c.get('en', '')):
                al = []
                for e, z in c['align']:
                    e2 = EN.sub(', ', e).strip() if e != '\n' else e; z2 = ZH.sub('，', z)
                    if al and al[-1][1].endswith('，') and z2.startswith('，'): z2 = z2[1:]
                    if e2 == ',' and al: al[-1][0] += ','; e2 = ''
                    if e2 or z2: al.append([e2, z2])
                c['align'] = al; c['zh'] = ''.join(z for _, z in al); c['en'] = EN.sub(', ', c['en']).strip()
                ok = ns(' '.join(a for a, _ in al if a != '\n')) == ns(c['en'])
                if not ok: s['chunks'][j - 1] = old; 改.append(f'S{i}-{j} 破折号没能自动换（对齐对不上），交人改'); continue
            if c != old: 改.append(f'S{i}-{j} 破折号换成逗号：' + '；'.join(f'{f} “{old.get(f, "")[:24]}” → “{c.get(f, "")[:24]}”' for f in ('en', 'zh', 'note') if old.get(f) != c.get(f)))
    return 改

DE = re.compile(r'\*\*([^*]+?)\*\*\(([^)]+)\)的(?![确话])')
def 形容词(md):
    """文章速查表里本文词性是 adj. 的词（小写）"""
    import 速查表 as SC
    out = set()
    for w, x in SC.行(md):
        m = re.search(r'本文：[^|]*?；\s*' + SC.POS, x) or re.match(r'\s*' + SC.POS, x)
        if m and m.group(1) == 'adj': out.add(w.strip().lower())
    return out
def 的并进(d, adj):
    """T38（用户 2026-11-04：“记住以后我们这个标标注这个形容形容词的这个意思的时候，最好把那个白勺的也给标上，ok，不要每次我都提醒。”）：
    形容词重点词后面紧跟的“的”并进标色：**不便**(inconvenient)的旅程 → **不便的**(inconvenient)旅程；“的”在下一段对齐开头也并过来。
    名词、动词后面的“的”（**水手**(sailor)的）不动；的确、的话 不动"""
    ok = lambda m: m.group(2).lower() in adj and not m.group(1).endswith('的')
    sub = lambda z: DE.sub(lambda m: f'**{m.group(1)}的**({m.group(2)})' if ok(m) else m.group(0), z)
    改 = []; 不并 = (d.get('核对确认') or {}).get('的不并', {})   # 主会话 2026-11-07（56 S10“他**幼子**(infant)的生命”）：所属的“的”不是形容词的“的”，写了确认的那段不并
    for i, s in enumerate(d['sentences'], 1):
        for j, c in enumerate(s['chunks'], 1):
            if f'S{i}-{j}' in 不并: continue
            z0 = c.get('zh', ''); al = c.get('align') or []
            if not al: c['zh'] = sub(z0)
            for k in range(len(al)):
                al[k][1] = sub(al[k][1])
                m = re.search(r'\*\*([^*]+?)\*\*\(([^)]+)\)$', al[k][1])
                if m and ok(m) and k + 1 < len(al) and re.match(r'的(?![确话])', al[k + 1][1]):
                    al[k][1] = al[k][1][:m.start()] + f'**{m.group(1)}的**({m.group(2)})'; al[k + 1][1] = al[k + 1][1][1:]
            if al: c['zh'] = ''.join(z for _, z in al)
            if c['zh'] != z0: 改.append(f'S{i}-{j} 形容词的“的”并进标色（T38）：' + '、'.join(f'**{a}的**({b})' for a, b in DE.findall(z0) if b.lower() in adj and not a.endswith('的')))
    return 改
def 自检():
    f = []; adj = 形容词('## 速查表\n| 词 | 释义 | 段 |\n|---|---|---|\n| inconvenient | adj. 不方便的 | 2 |\n| prudent | 本文：谨慎的；adj. 谨慎的，审慎的 | 5 |\n| sailor | n. 水手 | 3 |\n| necessary | adj. 必要的 | 1 |\n')
    if adj != {'inconvenient', 'prudent', 'necessary'}: f.append(f'速查表认形容词不对：{sorted(adj)}')
    d = {'sentences': [{'chunks': [
        {'zh': '**不便**(inconvenient)的旅程', 'align': [['inconvenient journeys', '**不便**(inconvenient)的旅程']]},
        {'zh': '**谨慎**(prudent)的人', 'align': [['prudent', '**谨慎**(prudent)'], ['people', '的人']]},
        {'zh': '**水手**(sailor)的船，**谨慎**(prudent)地，**必要的**(necessary)，**必要**(necessary)的确', 'align': []}]}]}
    改 = 的并进(d, adj); c = d['sentences'][0]['chunks']
    if c[0]['zh'] != '**不便的**(inconvenient)旅程' or c[0]['align'][0][1] != c[0]['zh']: f.append(f'没并进：**不便**(inconvenient)的旅程 → {c[0]["zh"]}（T38）')
    if c[1]['align'] != [['prudent', '**谨慎的**(prudent)'], ['people', '人']] or c[1]['zh'] != '**谨慎的**(prudent)人': f.append(f'“的”在下一段对齐开头没并过来：{c[1]["align"]}（T38）')
    if c[2]['zh'] != '**水手**(sailor)的船，**谨慎**(prudent)地，**必要的**(necessary)，**必要**(necessary)的确': f.append(f'误改：名词的“的”、“地”、已并好的、的确 不该动：{c[2]["zh"]}（T38）')
    if len(改) != 2: f.append(f'报告条数不对：{改}')
    d2 = {'核对确认': {'的不并': {'S1-1': '所属的“的”'}}, 'sentences': [{'chunks': [{'zh': '他**幼子**(infant)的生命', 'align': []}, {'zh': '**幼小**(infant)的孩子', 'align': []}]}]}
    的并进(d2, {'infant'}); c2 = d2['sentences'][0]['chunks']
    if c2[0]['zh'] != '他**幼子**(infant)的生命': f.append(f'写了 核对确认.的不并 的段照样并了：{c2[0]["zh"]}')
    if c2[1]['zh'] != '**幼小的**(infant)孩子': f.append(f'没写确认的段没并：{c2[1]["zh"]}')
    return f

def main():
    if sys.argv[1:] == ['--自检']:
        f = 自检(); print('\n'.join(f) or '修 自检通过（T38：形容词的“的”并进标色、跨对齐段也并；名词的“的”、“地”、的确、已并好的不动）'); sys.exit(1 if f else 0)
    no = sys.argv[1].zfill(2); js = f'scripts/{no}.json'; d = json.load(open(js)); 改 = []
    if PZ.查(d, no):
        改 += 破折号(d); json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
    已发 = os.path.exists(f'{os.path.dirname(T)}/脚本/已发版本/{no}.json')
    if int(no) >= 25 and not 已发 and '（简述：' in (d['sentences'][-1]['chunks'][-1].get('note') or ''):   # G35 常规：简述按整屏字号最大折行；只给第一稿（发过的版式是用户看过的，不自动动，L13）
        r = subprocess.run(['python3', f'{T}/说明分行.py', no, '--整屏', '--写入'], capture_output=True, text=True)
        if '已写入' in r.stdout: 改 += [f'结尾简述整屏折行（G35）：{l.strip()[:80]}' for l in r.stdout.splitlines() if '结尾简述' in l]
    import glob
    md = glob.glob(f'{os.path.dirname(os.path.dirname(T))}/新版定稿/{no}-*.md')
    if md:
        d = json.load(open(js)); 改_ = 的并进(d, 形容词(open(md[0]).read()))
        if 改_: json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1); 改 += 改_
    r = subprocess.run(['python3', f'{T}/说明分行.py', no, '--写入'], capture_output=True, text=True)
    if '已写入' in r.stdout: 改 += [f'说明折行（L19）：{l.strip()[:90]}' for l in r.stdout.splitlines() if '超宽' in l]
    if '【停止】' in r.stdout: 改 += [f'错：{l.strip()}' for l in r.stdout.splitlines() if '【停止】' in l]
    print('\n'.join(改))

if __name__ == '__main__': main()
