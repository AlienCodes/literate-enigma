#!/usr/bin/env python3
"""开工必读 = 踩坑指南 + 做事指南（用户 2026-10-26：“每次你要去开始去做一个项目……都要有这么一个踩坑指南和别人要去做的事情指南，
就是先先去读这些，先去读这些东西，然后再根据这些东西去做”）。照 音频首要法则.py 的路子：程序生成、机器核对、开工打印、出片前查。
视频/开工必读.md 由本程序从 规则执行核查 抽的全部规矩（CLAUDE.md 守则、踩坑总表每个坑、各节硬性标准、交付前检查单）+ 规则执行表 的门自动生成：
  踩坑指南：每个坑 → 怎么防 → 哪道门挡；做事指南：每条做法 → 哪道门查；程序判不了的标“人判”。
规则执行核查 每次核对：文件和现行规矩对不上（漏一条、改了没重新生成）就停。
28 起 制作记录/NN.md 要有“## 做事对照记录”：记下读过的开工必读条目（指南新加了条目就要 --补 读新条目），人判的每条写“本篇：怎么做的”；踩坑核查 出片/文本查。
用法：python3 开工必读.py [--写入|--要点|--补 NN|--自检]（不带参数 = 核对）"""
import os, re, sys, json, hashlib
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
OUT = f'{V}/开工必读.md'; STD = f'{V}/制作硬性标准与踩坑总结.md'; CL = f'{P}/CLAUDE.md'; REG = f'{T}/规则执行表.json'
sys.path.insert(0, T); import 规则执行核查 as RG
起 = 28
组 = [('守则', 'CLAUDE.md 守则'), ('铁', '最高铁律'), ('法', '现行做法'), ('音', '一、音频 硬性标准'), ('画', '二、画面与视频 硬性标准'),
     ('文', '三、文字 硬性标准'), ('流', '四、流程、保存与沟通 硬性标准'), ('单', '交付前检查单')]
短 = lambda x, n: re.sub(r'\s+', ' ', re.sub(r'\*\*|`', '', x)).strip()[:n] + ('…' if len(re.sub(r'\s+', ' ', x)) > n else '')


def 人判(reg, k):
    return RG.只靠人(reg, k) or bool(reg.get(k, {}).get('部分靠人')) or bool(reg.get(k, {}).get('做事对照'))


def 门(reg, k):
    if 人判(reg, k): return '人判：写进 NN.md 做事对照记录' + ('（程序另管一部分）' if reg.get(k, {}).get('部分靠人') else '')
    g, _ = RG.解析(reg, k)
    return '；'.join(f'{os.path.basename(p)}「{短(a, 18)}」' for p, a in g[:2]) or '（没登记门：规则执行核查会停）'


def 条目(std, cl, reg):
    """[(编号, 组名, 一行)]：和 规则执行核查 用同一个抽法，规矩一条不漏"""
    R = RG.规矩(std, cl); R.pop('__重复__', None); 防 = {i: f for i, _, f in RG.坑行(std)}; 问 = {i: q for i, q, _ in RG.坑行(std)}
    out = []
    for k in R:
        if k in 问: out.append((k, '坑', f'- **{k}** {短(问[k], 70)} → {短(防[k], 90)} ｜{门(reg, k)}'))
        else:
            g = next(n for p, n in 组 if k.startswith(p))
            out.append((k, g, f'- **{k}** {R[k]} ｜{门(reg, k)}'))
    return out


def 版本(items): return hashlib.sha256(' '.join(k for k, _, _ in items).encode()).hexdigest()[:8]


# ⑤ 做视频流程（G62，用户 2026-10-26：“他首先第一件事要知道这个做视频的流程，第一步该干嘛？第二步该干嘛？第三步该干嘛……一定要去严格按照这个流程去执行”）：
# 由程序从 草稿流程.md（〇 … 四、改稿）和 定稿流水线.sh（⓪–⑦）生成编号步骤表；脚本改了步骤表不跟，开工必读核对就停（规则执行核查当场跑）
流程F = f'{T}/草稿流程.md'; 流水线F = f'{T}/定稿流水线.sh'; 机制F = f'{T}/机制清单.json'
_净 = lambda x: re.sub(r'\s+', ' ', re.sub(r'\*\*|`', '', x)).strip()
_程序 = re.compile(r'(?:python3|bash)\s+(?:\$T/|\$P/工具/|视频/工具/|<工具目录>/|<工具>/)?((?:[\w一-鿿]+/)?[\w一-鿿]+\.(?:py|sh))((?:\s+(?:NN|S#|S\d+|\$no|--[\w一-鿿]+|[一-鿿]+(?![\w一-鿿]*\.)))*)')


def 步骤表(流程=None, 流水线=None, C=None, reg=None):
    流程 = open(流程F).read() if 流程 is None else 流程; 流水线 = open(流水线F).read() if 流水线 is None else 流水线
    C = json.load(open(机制F)) if C is None else C; reg = reg or {}
    入口步 = {}
    for k, v in C['步骤'].items():
        for e in v['入口']: 入口步.setdefault(e, []).append(k)
    含 = {os.path.basename(x): m for m in C['机制'] for x in m.get('包含', [])}
    门 = {}
    for k, v in reg.items():
        if k.startswith('_') or not isinstance(v, dict): continue
        for p, _ in v.get('门', []) or []: 门.setdefault(os.path.basename(p), []).append(k)
    rows = []
    def 加(段, 做, 文):
        m = _程序.search(文.replace('$no', 'NN')); prog = os.path.basename(m.group(1)) if m else ''
        cmd = (f'{m.group(1)}{m.group(2)}'.strip() if m else '—')[:40]
        ss = 入口步.get(prog, []); 步 = next((x for x in ss if x in cmd), ss[0] if len(ss) == 1 else None); mm = 含.get(prog)
        证 = f'证据“{步}”' if 步 else (f'含在“{mm["证据"]}”的证据里' if mm else '—')
        在 = (mm or {}).get('在', '会话') if prog else '会话'
        g = ' '.join(dict.fromkeys(门.get(prog, []))) ; g = ' '.join(g.split()[:5]) or '—'
        rows.append((段, 做, cmd, 在, 证, g))
    段 = None
    for l in 流程.splitlines():
        h = re.match(r'^## ([〇一二三四五六七八九十]+(?:之二)?)、([^（(\n]*)', l)
        if h: 段 = h.group(1) + ' ' + h.group(2).strip(); continue
        if l.startswith('## '): 段 = None; continue
        m = re.match(r'^(\d+)\.\s+(.*)', l)
        if 段 and m:
            x = m.group(2); x = re.sub(r'^`[^`]*`[\s：:，,]*', '', x) if x.startswith('`') else x
            t = _净(x); 做 = re.split(r'[：。；]|（', t, maxsplit=1)[0][:36] or ('跑 ' + (_程序.search(m.group(2)).group(1) if _程序.search(m.group(2)) else '这条命令'))
            加(段, 做, m.group(2))
    ls = 流水线.splitlines()
    for i, l in enumerate(ls):
        m = re.match(r'^step "([^"]+)"(.*)', l.strip())
        if not m: continue
        后 = [m.group(2)]
        for x in ls[i + 1:i + 4]:
            if x.strip().startswith('step "'): break
            后.append(x)
        加('定稿 bash 定稿流水线.sh NN', _净(m.group(1))[:36], next((x for x in 后 if _程序.search(x)), ''))
    return rows


def 步骤节(reg):
    rows = 步骤表(reg=reg)
    L = [f'## ⑤ 做视频流程（{len(rows)} 步，严格照做、不乱发挥；由 工具/开工必读.py 从 草稿流程.md、定稿流水线.sh、机制清单.json 生成）', '',
         '用户 2026-10-26：“要有一个严格的做视频的流程，一定要去严格按照这个流程去执行……能在GitHub上做的就在GitHub上做”。每一步只用“正式入口”做；“证据”那一列的步骤跑完会留下带指纹的使用证据，出片前、出片后、定稿按证据链查，少一步或顺序不对就停（G60）。', '',
         '| 第几步 | 阶段 | 做什么 | 正式入口 | 在哪做 | 留下的证据 | 门 |', '|---|---|---|---|---|---|---|']
    L += [f'| {i} | {a} | {b} | {c} | {d} | {e} | {g} |' for i, (a, b, c, d, e, g) in enumerate(rows, 1)]
    return L


def 机制节():
    C = json.load(open(机制F))
    L = [f'## ④ 机制清单（{len(C["机制"])} 个机制 + {len(C.get("工作流", {}))} 个 GitHub 工作流：每个都要真跑起来、留下使用证据，G60）', '',
         '阶段要的证据链：' + '；'.join(f'{k}要先有 {" → ".join(v)}' for k, v in C['阶段'].items()) + '。证据只能由正式入口写（' + '、'.join(sorted({e for v in C['步骤'].values() for e in v['入口']})) + '），手写、临时脚本、改过的入口都对不上指纹。', '']
    L += [f'- **{m["名"]}** → 证据“{m["证据"]}”{("（" + m["详情"] + "）") if m.get("详情") else ""}，{m["查于"]}时查，在{m["在"]}跑；程序：{"、".join(m.get("包含", []))}' for m in C['机制']]
    L += [f'- GitHub 工作流 **{w}**：{"每篇要跑，证据 = 运行号" if v.get("每篇") else v.get("说明", "")}' for w, v in C.get('工作流', {}).items()]
    return L + ['']


def 总纲节():
    import 会话开工 as _HK
    return ['## ⓪ 五条总纲（每个会话开工第一件事：python3 视频/工具/会话开工.py <出稿|改稿|改门|主会话>，读完才能提交，G63）', '', *[f'- {x}' for x in _HK.总纲], '']


def 生成(std, cl, reg):
    it = 条目(std, cl, reg); 坑 = [x for x in it if x[1] == '坑']; 判 = [x for x in it if 人判(reg, x[0])]
    L = ['# 开工必读（每次开工先读，再照它做；本文件由 工具/开工必读.py --写入 生成，不要手改）', '',
         '用户 2026-10-26 原话：“一定要保证，一定要有一个机制，绝对的机制去保证我们踩过的这个坑，绝对不能再犯……每只要每次去开始做一个项目，都要有这么一个踩坑指南和别人要去做的事情指南，但就就是先先去读这些，先去读这些东西，然后再根据这些东西去做，ok。”', '',
         f'版本 {版本(it)}：坑 {len(坑)} 个、做法 {len(it) - len(坑)} 条，其中人判 {len(判)} 条。音频另见 视频/音频首要法则.md（首要法则）；每条全文见《制作硬性标准与踩坑总结》、CLAUDE.md。',
         f'{起} 起 开工记录 在 制作记录/NN.md 生成“## 做事对照记录”（记下读过的条目）；指南新加了条目，跑 `python3 视频/工具/开工必读.py --补 NN` 读新条目；人判的每条写“本篇：怎么做的”，没写踩坑核查就停。', '',
         *总纲节(),
         f'## ① 踩坑指南（{len(坑)} 个坑：出过的问题 → 怎么防 → 哪道门挡）', '', *[x[2] for x in 坑], '',
         f'## ② 做事指南（{len(it) - len(坑)} 条：怎么做 → 哪道门查）', '']
    for p, n in 组:
        xs = [x for x in it if x[1] == n]
        if xs: L += [f'### {n}（{len(xs)} 条）', '', *[x[2] for x in xs], '']
    L += [f'## ③ 人判清单（{len(判)} 条：程序判不了，每篇在 NN.md 做事对照记录里写本篇怎么做的）', '', *[f'- **{k}** {短(s.split("** ", 1)[-1], 80)}' for k, _, s in 判], '']
    L += 机制节() + 步骤节(reg) + ['']
    return '\n'.join(L)


def 现行(): return open(STD).read(), open(CL).read(), json.load(open(REG))


def 节(txt):
    m = re.search(r'^## 做事对照记录[^\n]*\n[\s\S]*?(?=^## |\Z)', txt or '', re.M); return m.group(0) if m else None


def 查记录(txt, no, std=None, cl=None, reg=None):
    """28 起：做事对照记录 读过全部现行条目、人判的每条写了本篇怎么做的"""
    if not str(no).isdigit() or int(no) < 起: return []
    if std is None: std, cl, reg = 现行()
    it = 条目(std, cl, reg); s = 节(txt)
    if s is None: return [f'[开工必读] 制作记录/{no}.md 没有“## 做事对照记录”：先读 视频/开工必读.md，再 python3 视频/工具/开工必读.py --补 {no}']
    m = re.search(r'读过的条目：([^\n]*)', s); seen = set(m.group(1).split()) if m else set()
    new = [k for k, _, _ in it if k not in seen]; err = []
    if new: err.append(f'[开工必读] 指南新加了条目 {" ".join(new[:12])}{"……" if len(new) > 12 else ""}（读过的版本旧了）：python3 视频/工具/开工必读.py --补 {no} 读新条目、补人判行')
    rows = {m.group(1): m.group(2).strip() for m in re.finditer(r'^\| *(\S+) *\|[^|\n]*\|([^|\n]*)\|\s*$', s, re.M)}
    bad = [k for k, _, _ in it if 人判(reg, k) and not re.match(r'^本篇[：:].{6,}', rows.get(k, ''))]
    if bad: err.append(f'[开工必读] 做事对照记录 人判的 {" ".join(bad)} 要写“本篇：怎么做的”（至少 6 个字，不许留待填）')
    return err


def 补(no, txt=None, items=None, reg=None):
    """打印新条目，追加人判行，更新“读过的条目”；已有的行一字不动（G23/G46：只追加）"""
    f = f'{V}/制作记录/{no}.md'
    if txt is None: txt = open(f).read() if os.path.exists(f) else f'# 第{no}篇制作记录\n'
    if items is None: std, cl, reg = 现行(); items = 条目(std, cl, reg)
    s = 节(txt); m = re.search(r'读过的条目：([^\n]*)', s or ''); seen = set(m.group(1).split()) if m else set()
    new = [x for x in items if x[0] not in seen]
    line = '- 读过的条目：' + ' '.join(k for k, _, _ in items)
    rows = ''.join(f'| {k} | {短(t.split("** ", 1)[-1].split(" ｜")[0], 30)} | 待填（本篇：怎么做的） |\n' for k, _, t in new if 人判(reg, k))
    if s is None:
        sec = f'## 做事对照记录（开工必读，{起} 起；人判的每条写“本篇：怎么做的”）\n\n{line}\n\n| 编号 | 做法（摘要） | 本篇怎么做的 |\n|---|---|---|\n{rows}'
        out = txt.rstrip('\n') + '\n\n' + sec
    else:
        s2 = (s.replace(m.group(0), line[2:], 1) if m else s.rstrip('\n') + '\n' + line + '\n').rstrip('\n') + '\n' + rows
        ws = s[len(s.rstrip('\n')):]; out = txt.replace(s, s2.rstrip('\n') + (ws if len(ws) > 1 else '\n'), 1)
    return out, new


def 自检():
    std, cl, reg = 现行(); f = []
    t0 = 生成(std, cl, reg); i0 = RG.坑行(std)[0][0]
    std2 = '\n'.join(l for l in std.splitlines() if not re.match(rf'^\| *{i0} *\|', l))
    if 生成(std2, cl, reg) == t0: f.append(f'没抓到：踩坑总表删掉 {i0}，开工必读没变（漏一条发现不了）')
    k0 = next(k for k in reg if k.startswith('文') and not 人判(reg, k) and reg[k].get('门'))
    if 生成(std, cl, {**reg, k0: {**reg[k0], '门': [['自检造的.py', '改了门']]}}) == t0: f.append('没抓到：门改了开工必读没变')
    items = 条目(std, cl, reg); 判 = [k for k, _, _ in items if 人判(reg, k)]
    if not 判: f.append('自检前提不成立：没有人判条目')
    if not 查记录('# 第98篇\n', '98', std, cl, reg): f.append('没抓到：没有做事对照记录')
    t1, new = 补('98', '# 第98篇\n\n## 方法设计\n- 预计调用：50\n', items, reg)
    if '## 方法设计\n- 预计调用：50' not in t1 or len(new) != len(items): f.append('补 冲掉了已有内容或没列全条目')
    if not any('人判' in e for e in 查记录(t1, '98', std, cl, reg)): f.append('没抓到：人判的留着待填')
    t2 = re.sub(r'待填（本篇：怎么做的）', '本篇：逐条照做，具体写在改稿记录', t1)
    if 查记录(t2, '98', std, cl, reg): f.append(f'误报：填完的做事对照记录被判不合格：{查记录(t2, "98", std, cl, reg)}')
    items2 = items + [('Z99', '坑', '- **Z99** 自检造的新坑')]
    if not any('新加了条目' in e for e in 查记录(t2, '98', std + '\n| Z99 | 自检造的新坑 | x | y |\n', cl, {**reg, 'Z99': {'门': reg[k0]['门']}})): f.append('没抓到：指南新加了条目、对照记录读的是旧版')
    t4, new4 = 补('98', t2, items2, reg)
    if [x[0] for x in new4] != ['Z99'] or 'Z99' not in re.search(r'读过的条目：([^\n]*)', t4).group(1) or '本篇：逐条照做' not in t4: f.append('补 新条目没列出、没记下，或改动了已填的行')
    if 查记录('# x\n', '27', std, cl, reg): f.append('误报：28 以前不查')
    if 步骤表(流水线=open(流水线F).read() + '\nstep "⑧ 自检造的新步骤"\n', reg=reg) == 步骤表(reg=reg): f.append('没抓到：定稿流水线加了一步，步骤表没变（G62）')
    if 步骤表(流程=open(流程F).read().replace('\n## 禁止', '\n9. 自检造的新步骤 `python3 $T/x.py NN`\n\n## 禁止', 1), reg=reg) == 步骤表(reg=reg): f.append('没抓到：草稿流程加了一步，步骤表没变（G62）')
    return ['开工必读 自检：' + x for x in f]


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--自检' in a:
        e = 自检(); print('\n'.join(e) or '开工必读 自检通过（删一个坑、改一道门必被发现；没有做事对照、指南新加条目没读、人判待填必停；补 只追加）'); sys.exit(1 if e else 0)
    std, cl, reg = 现行(); t = 生成(std, cl, reg)
    if '--写入' in a: open(OUT, 'w').write(t); print(f'已写 {OUT}'); sys.exit(0)
    if '--补' in a:
        no = a[a.index('--补') + 1].zfill(2); out, new = 补(no)
        open(f'{V}/制作记录/{no}.md', 'w').write(out)
        print(f'开工必读：新读 {len(new)} 条（写进 制作记录/{no}.md 做事对照记录）'); [print(' ', x[2][:150]) for x in new[:60]]
        if len(new) > 60: print(f'  ……另 {len(new) - 60} 条见 视频/开工必读.md')
        sys.exit(0)
    if '--要点' in a:
        import 会话开工 as _HK; _HK.打印总纲()   # G63：五条总纲每个会话开工第一屏
        it = 条目(std, cl, reg); 判 = [k for k, _, _ in it if 人判(reg, k)]
        print(f'【开工必读（用户 2026-10-26：先读踩坑指南和做事指南，再照着做）】先读 视频/开工必读.md：坑 {sum(1 for x in it if x[1] == "坑")} 个、做法 {sum(1 for x in it if x[1] != "坑")} 条；人判 {len(判)} 条（NN.md 做事对照记录逐条写本篇怎么做）：{" ".join(判)}'); sys.exit(0)
    if not os.path.exists(OUT) or open(OUT).read() != t:
        print('【停止】视频/开工必读.md 与现行规矩（CLAUDE.md、踩坑总表、硬性标准、检查单、规则执行表的门）对不上（漏了或改了没重新生成）：python3 视频/工具/开工必读.py --写入'); sys.exit(1)
    print(f'开工必读 与现行规矩一致（版本 {版本(条目(std, cl, reg))}）')
