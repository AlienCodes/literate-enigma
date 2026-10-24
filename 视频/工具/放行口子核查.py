#!/usr/bin/env python3
"""放行口子核查（G24，CLAUDE.md 第16条补充；用户 2026-10-24：“做着做着你就完完全全不按照我教给你的这个方式来做了，你又去自由发挥了……
一定要严格制定这么一个机制或者这么一个程序……所有立的这个规矩……全都要严格去执行起来”）。
根因：门上的“放行口子”（核对确认.<类>、特批字段、环境变量开关、“NN 起才查”）只看写了没有，不看写的结论是不是违背规矩；
T18 就是这样漏的（22 S3、24 S8/S10 写“英式写法、不改”放行）。
  ① 每个口子登记在 放行口子表.json：属于哪条规矩、允许的结论（白名单）、禁止的结论；
  ② 24 起逐条查脚本里的每一条确认、特批：不合白名单或命中禁止结论 → 错误、停（踩坑核查 文本/出片 阶段调用 查篇）；
  ③ 保留违规、放宽、特批的例外只认用户原话：结论里要引“……”，而这句话在 用户同意记录.json 里有（AI 自己写的例外一律不认）；
  ④ 代码里出现没登记的新口子（新的确认类别、特批/放宽字段、环境变量开关、“NN 起才查”）→ 停（规则执行核查 每次跑本程序 --自检）；
  ⑤ 每个口子配绕过样本：写一条违背规矩的确认，必须被抓到。
用法：python3 放行口子核查.py --自检         自检 + 扫代码里的口子是否都登记（规则执行核查 每次跑）
      python3 放行口子核查.py --体检 01 24  把这些篇现有的确认按登记表过一遍，写 制作记录/放行口子体检.md（只列不改）
      python3 放行口子核查.py NN            查一篇（24 起不合格就停）"""
import os, re, sys, json, glob
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
表 = json.load(open(f'{T}/放行口子表.json'))
起 = 表['_起']


def 同意():
    return json.load(open(f'{T}/用户同意记录.json'))['记录']


_ns = lambda x: re.sub(r'[\s，。、；：:,.;!?！？…“”"\'（）()—\-]', '', x)


def 有原话(text, rec=None):
    """结论里引的“……”在 用户同意记录.json 里有（至少一句、去标点后 ≥4 字、是某条原话的一段）"""
    rec = 同意() if rec is None else rec; ys = [_ns(r['原话']) for r in rec]
    for q in re.findall(r'“([^”]{4,})”', text):
        q = _ns(q)
        if len(q) >= 4 and any(q[:30] in y for y in ys): return True
    return False


def 判(cat, val, rec=None, 规=None):
    """一条确认/特批：合格返回 None，否则返回问题"""
    规 = 表['确认'] if 规 is None else 规
    sp = 规.get(cat)
    if sp is None: return f'没登记的口子类别“{cat}”（先在 放行口子表.json 登记规矩、允许、禁止）'
    text = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)
    backed = 有原话(text, rec)
    if sp['类'] == '用户' and not backed:
        return '这是保留违规/放宽/特批，只认用户原话：结论里引“用户原话”，且这句话已记进 用户同意记录.json（AI 自己写的理由不算）'
    if sp.get('禁止') and re.search(sp['禁止'], text) and not backed:
        return f'结论违背规矩（命中“{re.search(sp["禁止"], text).group(0)}”）：{sp["规矩"]} 不许写例外，要例外先拿到用户原话'
    if sp.get('允许') and not re.search(sp['允许'], text) and not backed:
        return f'结论不合格式（只认：{sp["允许说明"]}）'
    return None


def 条目(d):
    """(类别, 键, 值)：核对确认 每一条 + 顶层特批字段"""
    out = []
    for cat, v in d.get('核对确认', {}).items():
        if isinstance(v, dict): out += [(cat, k, x) for k, x in v.items()]
        elif isinstance(v, list): out += [(cat, x, x) for x in v]
        else: out.append((cat, '', v))
    for k, sp in 表['特批字段'].items():
        if sp.get('数据字段') and k in d:
            v = d[k]
            if isinstance(v, dict): out += [(k, s, x) for s, x in v.items()]
            else: out.append((k, '', v))
    return out


def 查篇(d, no, rec=None, 强制=False):
    if not 强制 and (not str(no).isdigit() or int(no) < 起): return []
    out = []
    for cat, k, v in 条目(d):
        p = 判(cat, v, rec)
        if p: out.append(f'[口子] {cat} {str(k)[:40]}：{p}')
    return out


# ---------- ④ 扫代码里的口子 ----------
def 扫码(files=None):
    """{类: {名字: [程序]}}：确认类别、特批字段、环境变量开关、“NN 起才查”"""
    if files is None:
        files = {}
        for f in glob.glob(f'{T}/**/*', recursive=True):
            r = os.path.relpath(f, T)
            if os.path.isfile(f) and r.endswith(('.py', '.sh')) and '历史版本' not in r and not re.search(r'gen\d+\.py$', r) and r != '放行口子核查.py':
                files[r] = open(f, errors='ignore').read()
    got = {'确认': {}, '特批字段': {}, '开关': {}, '起查': {}}
    add = lambda k, n, f: got[k].setdefault(n, set()).add(f)
    for f, t in files.items():
        for l in t.splitlines():
            if l.strip().startswith('#'): continue
            for m in re.finditer(r"核对确认['\"]?\]?\s*(?:,\s*\{\}\))?\s*(?:\.get\(|\[)\s*['\"]([^'\"]+)['\"]", l): add('确认', m.group(1), f)
            for m in re.finditer(r"\bask\('([^']+)'", l): add('确认', m.group(1), f)
            for m in re.finditer(r"['\"]([^'\"\s]{0,12}(?:特批|放宽|豁免|已获同意)[^'\"\s]{0,8})['\"]\s*(?:\)|\]|,\s*\{|,\s*''|in\b)", l): add('特批字段', m.group(1), f)
            for m in re.finditer(r"environ(?:\.get\(|\[)\s*['\"]([A-Za-z_一-鿿]+)['\"]", l): add('开关', m.group(1), f)
            for m in re.finditer(r"int\((?:no|[^()]*\(\s*['\"]no['\"][^()]*\))\)\s*>=\s*(\d+)", l): add('起查', f'{os.path.basename(f)}:{m.group(1)}', f)
            for m in re.finditer(r"^\s*([\w一-鿿]*起)\s*=\s*(\d+)", l): add('起查', f'{os.path.basename(f)}:{m.group(2)}', f)
    return got


def 没登记(got=None, 表_=None):
    got = 扫码() if got is None else got; 表_ = 表 if 表_ is None else 表_
    out = []
    for k, names in got.items():
        for n, fs in names.items():
            if n not in 表_[k]: out.append(f'代码里有没登记的{k}口子“{n}”（{"、".join(sorted(fs))}）：先在 放行口子表.json 登记（规矩、允许/禁止或用途），没登记提交不了')
    return out


def 自检():
    fails = []
    rec = [{'篇': '99', '日期': '2026-10-24', '原话': '这个地方可以不加，我同意', '用于': '自检'}]
    # ⑤ 每个确认类别的绕过样本：AI 写的“例外/放宽/不改”必须抓到
    for cat, sp in 表['确认'].items():
        bad = '例外：英式写法，不改，先放宽' if sp['类'] != '核实' else {'配音指纹': 'x', '依据': '放宽：听不出来，例外'}
        if 判(cat, bad, rec) is None: fails.append(f'没抓到：{cat} 写“例外/不改/放宽”的确认被放行（G24 绕过样本）')
    for k in [k for k, sp in 表['特批字段'].items() if sp.get('数据字段')]:
        if 判(k, 'AI 觉得可以放宽一点', rec) is None: fails.append(f'没抓到：{k} 没有用户原话的特批被放行（G24）')
    if 判('牛津逗号', '文章英文是英式写法，三项并列不用牛津逗号；不改', rec) is None: fails.append('没抓到：牛津逗号“英式写法、不改”（T35 重放）')
    if 判('牛津逗号', '不是三项并列：upright and intact 是两项', rec): fails.append('G24 误报：牛津逗号“不是三项并列：……”被报出')
    if 判('引号', '用户 2026-10-24：“这个地方可以不加，我同意”', rec): fails.append('G24 误报：引了用户同意记录里原话的例外被报出')
    if 判('引号', '用户 2026-10-24：“我编的一句话不在记录里”', rec) is None: fails.append('没抓到：引的“原话”不在用户同意记录里（AI 编的）')
    if 判('非人声', {'配音指纹': 'c81ce56b1f49', '依据': '2026-10-09 实际声音（逐 5 ms 电平）'}, rec): fails.append('G24 误报：正常的非人声核实被报出')
    if 判('新类别XYZ', '随便', rec) is None: fails.append('没抓到：没登记的确认类别')
    if 定稿同意('24', rec): fails.append('没抓到：用户没说定稿就跑定稿流水线（画19/流7）')
    if not 定稿同意('24', rec + [{'篇': '24', '日期': '2026-10-24', '原话': '可以，定稿吧', '用于': '定稿 24'}]): fails.append('定稿门 误报：用户同意记录里有“定稿 24”')
    if not 定稿同意('20', rec): fails.append('定稿门 误报：24 以前已定稿的篇目')
    if 查篇({'核对确认': {'牛津逗号': {'S1 a, b and': '英式写法，不改'}}}, '23', rec): fails.append('G24 误报：24 以前已定稿篇目被报出（只列不改）')
    if not 查篇({'核对确认': {'牛津逗号': {'S1 a, b and': '英式写法，不改'}}}, '24', rec): fails.append('没抓到：24 起的“英式写法、不改”（G24）')
    # ④ 代码里新长出来的口子
    fake = {'假程序.py': "ok = d.get('核对确认', {}).get('新口子类', {})\nif os.environ.get('SKIP_ALL'): pass\nif int(no) >= 99: x = 1\nif d.get('读音放宽特批') : pass\n"}
    g = 扫码(fake); nb = 没登记(g)
    for want in ('新口子类', 'SKIP_ALL', '假程序.py:99', '读音放宽特批'):
        if not any(f'“{want}”' in x for x in nb): fails.append(f'没抓到：代码里没登记的新口子 {want}（G24）')
    return fails


定稿_起 = 24   # 画19/流7/单22：用户试听确认后才算定稿——定稿流水线先查 用户同意记录 里有这一篇“定稿”的用户原话（24 起）


def 定稿同意(no, rec=None):
    rec = 同意() if rec is None else rec
    if not str(no).isdigit() or int(no) < 定稿_起: return True
    return any(r.get('篇') == no and '定稿' in r.get('用于', '') and len(_ns(r.get('原话', ''))) >= 2 for r in rec)


def 体检(lo, hi):
    rows, n_all = [], 0; rec = 同意()
    for n in range(lo, hi + 1):
        p = f'{V}/脚本/{n:02d}.json'
        if not os.path.exists(p): continue
        d = json.load(open(p)); items = 条目(d); n_all += len(items)
        bad = [(c, k, 判(c, v, rec)) for c, k, v in items]; bad = [x for x in bad if x[2]]
        if bad:
            rows.append(f'\n## {n:02d}（{len(bad)} 条，共 {len(items)} 条确认）')
            rows += [f'- {c} `{str(k)[:50]}`：{p_}' for c, k, p_ in bad]
    return n_all, rows


def main():
    a = sys.argv[1:]
    if a and a[0] == '--自检':
        f = 自检(); nb = 没登记()
        print('放行口子核查自检：' + ('通过（每个口子的绕过样本都抓到，合格结论、用户原话不误报，代码里新长的口子抓到）' if not f else '失灵！' + '；'.join(f)))
        for x in nb: print('  ✘ ' + x)
        if not nb: print(f'代码里的口子全部登记（确认 {len(表["确认"])} 类、特批字段 {len(表["特批字段"])}、开关 {len(表["开关"])}、起查 {len(表["起查"])}）')
        return 1 if f or nb else 0
    if a and a[0] == '--定稿':
        no = a[1].zfill(2); ok = 定稿同意(no)
        print(f'第{no}篇 用户定稿原话：' + ('有' if ok else '【没有】用户试听确认后才算定稿：把用户说定稿的原话（逐字）记进 用户同意记录.json，用于写“定稿 ' + no + '”')); return 0 if ok else 1
    if a and a[0] == '--体检':
        lo, hi = int(a[1]), int(a[2]); n_all, rows = 体检(lo, hi); nb = sum(1 for r in rows if r.startswith('- '))
        out = f'{V}/制作记录/放行口子体检.md'
        open(out, 'w').write(f'# 放行口子体检（{lo:02d}–{hi:02d}，程序列出，只列不改）\n\n用户 2026-10-24：“当前现在所有的这个视频先不要去乱改了。”01–23 只列；24 的进 24_待改清单.md。\n生成：`python3 视频/工具/放行口子核查.py --体检 {lo} {hi}`。共 {n_all} 条确认/特批，不合登记表的 {nb} 条：\n' + '\n'.join(rows) + '\n')
        print(f'体检：{n_all} 条确认，不合格 {nb} 条 → {out}'); return 0
    no = a[0].zfill(2); d = json.load(open(f'{V}/脚本/{no}.json')); out = 查篇(d, no, 强制=True)
    for x in out: print('  ✘ ' + x)
    print(f'第{no}篇 放行口子：' + ('全部合格' if not out else f'{len(out)} 条不合格'))
    return 1 if out and int(no) >= 起 else 0


if __name__ == '__main__':
    sys.exit(main())
