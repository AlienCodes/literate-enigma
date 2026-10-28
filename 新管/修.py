#!/usr/bin/env python3
"""机械错误的标准修法（只做不改意思的事；改了什么全部列进报告给用户看）：
  破折号（T36/守则18）：中文、说明 → “，”；英文 → “, ”（文章一致性检查已认这个例外）。改完复核 D2（align 拼回来要等于原文），不等就退回、交人改
  L19/L16 说明折行：调现有 说明分行.py NN --写入
用法（在出片工作目录）：python3 修.py NN   打印改了的每一处；返回 0"""
import sys, os, re, json, subprocess, copy
H = os.path.dirname(os.path.abspath(__file__))
T = os.environ.get('XG_TOOLS') or (os.path.dirname(H) if os.path.exists(f'{os.path.dirname(H)}/交付核查.py') else f'{os.path.dirname(H)}/视频/工具')
sys.path.insert(0, T)
import 破折号 as PZ

ZH = re.compile(r'\s*(?:[—–―─⸺⸻﹘－]+|--)\s*')
EN = re.compile(r'\s*(?:[—–―─⸺⸻﹘－]+|--|(?<=\s)-(?=\s))\s*')
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

def main():
    no = sys.argv[1].zfill(2); js = f'scripts/{no}.json'; d = json.load(open(js)); 改 = []
    if PZ.查(d, no):
        改 += 破折号(d); json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
    r = subprocess.run(['python3', f'{T}/说明分行.py', no, '--写入'], capture_output=True, text=True)
    if '已写入' in r.stdout: 改 += [f'说明折行（L19）：{l.strip()[:90]}' for l in r.stdout.splitlines() if '超宽' in l]
    if '【停止】' in r.stdout: 改 += [f'错：{l.strip()}' for l in r.stdout.splitlines() if '【停止】' in l]
    print('\n'.join(改))

if __name__ == '__main__': main()
