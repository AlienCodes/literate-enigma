#!/usr/bin/env python3
"""规则执行机器（CLAUDE.md 第16条）。
用户 2026-10-23 原话：“不论是立的新规矩，还是踩过的坑，这些所有东西都要实施起来……你不要说靠记忆了，你弄一个机器来跑这件事儿”
“这个机器它一定是一个完整机器，不要设置那种瑕疵的机器……一定要确保这些所有的东西都能跑起来……靠你是没有用的……你总会去忘记”。

规矩从三处自动抽（新写进去的规矩自动被发现，不靠记）：
  CLAUDE.md 每一条（守则N）、《制作硬性标准与踩坑总结》踩坑总表每一行（A1、T12……）、
  各节硬性标准每一条（铁N 最高铁律、法N 现行做法、音N 音频、画N 画面、文N 文字、流N 流程）。
每条规矩必须在 规则执行表.json 登记：
  门   [程序, 锚]：在哪个程序的哪一句拦住（锚 = 那一句里的一段原文，不能是注释）；
  自检 [程序, 锚]：故意造错、必须抓到的样本在哪里；
  同   [编号…]：与别的规矩同一道门（继承它们的门和自检）；
  类   "程序"（默认，程序判对错）或 "确认"（只有人能判：程序逐句点名要求核对，没核对就停）。
机器逐条查：
  ① 登记齐全：文档里有、登记表里没有的（新规矩、新坑）→ 停；登记表里有、文档里没有的 → 停；
  ② 门在：程序存在，锚还在程序里、不在注释里；
  ③ 门接上：程序从流程入口（定稿流水线、交付核查、生成文本、推送两仓库、git 提交钩子、Claude 钩子）调用得到；
  ④ 有自检，而且自检会被跑到（流程里有“程序 + 自检”的调用，或程序每次运行都先自检）；
  ⑤ 踩坑总表只有一份（就是《制作硬性标准与踩坑总结》里的表）；
  ⑥ Claude 钩子都配上了（.claude/settings.json）；
  ⑦ 能当场跑的自检当场跑（按 工具/ 的指纹缓存，程序没改不重跑）。
任何一条不过 → 退出码 1：git 提交、推送两仓库、交付核查、定稿流水线一律停。
机器自己也有自检：造“新坑没登记、新守则没登记、新标准没登记、锚被删、程序不存在、程序没接上、没有自检、
自检没人跑、出现第二份总表”九种错，必须全部抓到；原样必须通过。
用法：python3 规则执行核查.py          全查（不过就停）
      python3 规则执行核查.py --状态   一行状态（开工钩子用）
      python3 规则执行核查.py --自检   只做机器自检
      python3 规则执行核查.py --清单   每条规矩的门和自检（给人看）
"""
import re, os, sys, json, glob, hashlib, subprocess

T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
STD = f'{V}/制作硬性标准与踩坑总结.md'
REG = f'{T}/规则执行表.json'
BASE = f'{T}/规则执行缺口基线.json'
CACHE = '/tmp/规则执行自检缓存.json'
SECP = {'〇、': '铁', '〇之': '法', '一、': '音', '二、': '画', '三、': '文', '四、': '流'}
# 流程入口：这些程序本身由别的机器强制（git 钩子、Claude 钩子、发文件闸门要交付核查回执、定稿只能走流水线）
ENTRY = ['定稿流水线.sh', '交付核查.py', '生成文本.py', '推送两仓库.sh', 'githooks/pre-commit', '开工提醒.sh',
         'token进行中.sh', '规则执行核查.py']
# 每次运行都先做自检的程序（不需要别人带“自检”参数调用）
ALWAYS_SELFTEST = {'踩坑核查.py', 'check_all.py', '规则执行核查.py', '交付核查.py'}   # 交付核查 出片后 每次先跑核查程序自检、高亮自检
# 机器当场跑的自检（不依赖工作目录、几秒内完成）
FAST = [['生成文本.py', '--自检'], ['破折号.py', '--自检'], ['区间作废.py', '--自检'], ['放行口子核查.py', '--自检'], ['同步自检.py'], ['流程自检.py'], ['踩坑核查.py', '自检'], ['check_all.py', '--自检'], ['钩子/钩子自检.py'], ['排版自检.py'], ['推送自检.py'], ['译文核查.py', '--自检'], ['演练镜像.py', '--自检'], ['出片指纹.py', '--自检'], ['结尾句接点.py', '--自检'], ['句内响度.py', '--自检'], ['开工记录.py', '--自检'], ['停顿位置精确核对.py', '--自检'], ['响度一致性核对.py', '--确认自检'], ['音频首要法则.py', '--自检'], ['音频首要法则.py'], ['机器复听.py', '--比较自检']]
摘要 = lambda s: re.sub(r'\*\*|`', '', s).strip()[:60]
# 要在工作目录（有模型、声音）里才能跑的慢自检：通过时写下所测程序的指纹（印章）；程序一改指纹对不上，就当“自检没跑”，提交、推送停
STAMPED = {'出片守门自检.py': ('出片守门自检通过.json', ['make_video.py', 'render.py', '出片守门自检.py'])}
# 执行效应（CLAUDE.md 第19条）：端到端演练，被演练的程序或规矩一改，印章对不上，提交、推送、交付核查、定稿流水线一律停
sys.path.insert(0, T); import 执行效应演练 as _YL; STAMPED['执行效应演练.py'] = ('执行效应演练通过.json', _YL.被演练); import 执行效应声音演练 as _SY; STAMPED['执行效应声音演练.py'] = ('执行效应声音演练通过.json', _SY.声音被演练)   # 被演练的程序清单只在演练程序里写一份


def 印章有效(p):
    f, progs = STAMPED[p]
    try: st = json.load(open(f'{T}/{f}'))
    except Exception: return False
    return all(st.get(x) == (hashlib.sha256(open(f'{T}/{x}', 'rb').read()).hexdigest() if os.path.exists(f'{T}/{x}') else '无') for x in progs)


def 坑行(text=None):
    """踩坑总表每一行：(编号, 出过的问题, 以后怎么防)。唯一来源：《制作硬性标准与踩坑总结》里的表。"""
    text = open(STD).read() if text is None else text
    out = []
    for line in text.splitlines():
        m = re.match(r'^\| *([A-Z]\d+b?) *\|(.*)\|\s*$', line)
        if m:
            cells = [c.strip() for c in m.group(2).split('|')]
            out.append((m.group(1), cells[0], cells[-1] if len(cells) > 1 else ''))
    return out


def 规矩(std_text, claude_text):
    """{编号: 摘要}；编号重复的放进 '__重复__'"""
    R, dup = {}, []
    def add(k, v):
        if k in R: dup.append(k)
        R[k] = 摘要(v)
    for m in re.finditer(r'^(\d+)\. (.+)$', claude_text, re.M): add(f'守则{m.group(1)}', m.group(2))
    for i, q, _ in 坑行(std_text): add(i, q)
    sec = sub = None
    for line in std_text.splitlines():
        if line.startswith('## '): sec, sub = SECP.get(line[3:5]), None; continue
        if line.startswith('### '): sub = line[4:].strip(); continue
        m = re.match(r'^(\d+)\. (.+)', line)
        if sec and m and (sec in ('铁', '法') or sub == '硬性标准'): add(f'{sec}{m.group(1)}', m.group(2))
    if '## 附：交付前检查单' in std_text:   # 检查单每一项（单1、单2……）
        for k, m in enumerate(re.finditer(r'^- \[ \] (.+)$', std_text.split('## 附：交付前检查单', 1)[1], re.M), 1): add(f'单{k}', m.group(1))
    if dup: R['__重复__'] = dup
    return R


def 程序表():
    """{相对 工具/ 的路径: 原文}（不含历史版本、各篇 genNN 数据、缓存）"""
    out = {}
    for f in glob.glob(f'{T}/**/*', recursive=True):
        r = os.path.relpath(f, T)
        if not os.path.isfile(f) or '历史版本' in r or '__pycache__' in r or re.search(r'gen\d+\.py$', r): continue
        if r.endswith(('.py', '.sh')) or r.startswith('githooks/'):
            out[r] = open(f, errors='ignore').read()
    return out


def 有效行(text):
    return [l for l in text.splitlines() if l.strip() and not l.strip().startswith('#')]


def 调用图(files):
    names = list(files)
    g = {}
    for a, t in files.items():
        body = '\n'.join(有效行(t))
        imps = set(re.findall(r'(?:^|;)\s*(?:import|from)\s+([\w一-鿿]+)', body, re.M))
        g[a] = {b for b in names if b != a and (os.path.basename(b) in body or b in body
                or (b.endswith('.py') and os.path.basename(b)[:-3] in imps))}
    return g


def 可达(files, entry=ENTRY):
    g = 调用图(files); seen = set(); st = [e for e in files if e in entry or e.startswith('钩子/')]
    while st:
        x = st.pop()
        if x in seen: continue
        seen.add(x); st += g.get(x, ())
    return seen


def 自检会跑(files, reach):
    """会被跑到自检的程序：每次运行先自检的，或流程里有“程序名 + 自检”同一行调用的，或机器当场跑的"""
    out = set(ALWAYS_SELFTEST) | {f[0] for f in FAST} | {p for p in STAMPED if 印章有效(p)}
    for a in reach:
        for l in 有效行(files.get(a, '')):
            if '自检' in l:
                for b in files:
                    if os.path.basename(b) in l: out.add(b)
    return out


HUMAN = {('译文核查.py', '[逐句确认]'), ('踩坑核查.py', 'import 译文核查 as _YW'), ('踩坑核查.py', '只有人能判，要写明本篇具体怎么做的')}


def 只靠人(reg, k):
    """门全是“人来确认”（逐句确认、对照记录写明做法）的规矩"""
    g, _ = 解析(reg, k)
    return bool(g) and all(tuple(x) in HUMAN for x in g)


def 解析(reg, rid, seen=()):
    e = reg.get(rid) or {}
    gates, tests = [tuple(x) for x in e.get('门', [])], [tuple(x) for x in e.get('自检', [])]
    for o in e.get('同', []):
        if o not in seen and o != rid:
            g, t = 解析(reg, o, seen + (rid,)); gates += g; tests += t
    return gates, tests


def 核查(std_text, claude_text, reg, files, settings=None, extra_tables=()):
    """返回 (按规矩的问题 {编号: [问题]}, 全局问题 [问题])。纯函数，供自检造错。"""
    R = 规矩(std_text, claude_text); per, glob_ = {}, []
    if '__重复__' in R: glob_.append(f'规矩编号重复：{" ".join(R.pop("__重复__"))}')
    for k in R:
        if k not in reg: per.setdefault(k, []).append(f'没登记执行门（新规矩/新坑要同时配门：程序门 + 自检）——“{R[k]}”')
    for k in reg:
        if k not in R and not k.startswith('_'): glob_.append(f'登记表里的 {k} 在文档里找不到（删掉或改名了？）')
    reach = 可达(files); run = 自检会跑(files, reach)
    def 查锚(k, prog, anc, what):
        if prog not in files: per.setdefault(k, []).append(f'{what}程序不存在：{prog}'); return False
        if not any(anc in l for l in 有效行(files[prog])):
            per.setdefault(k, []).append(f'{what}的锚不在 {prog} 里（或只在注释里）：“{anc[:40]}”'); return False
        return True
    for k in R:
        if k not in reg: continue
        if reg[k].get('文') and not R[k].startswith(reg[k]['文']):   # 按位置编号的条文（标准、检查单）：中间插了一条，编号就对不上原来的内容
            per.setdefault(k, []).append(f'编号对应的条文变了（登记时是“{reg[k]["文"]}”，现在是“{R[k][:16]}”）：重新登记它的门和自检')
        gates, tests = 解析(reg, k)
        if 只靠人(reg, k) and len(reg[k].get('为什么程序判不了', '')) < 10:   # 2026-10-23 T9 对齐粗细能量却被登记成“逐句确认”，12–23 篇越做越粗
            per.setdefault(k, []).append('这条只靠人确认：写明“为什么程序判不了”；能用程序量的（数量、比例、模式）必须写成程序门')
        if not gates: per.setdefault(k, []).append('没有门')
        if not tests: per.setdefault(k, []).append('没有自检（故意造错、必须抓到的样本）')
        for prog, anc in gates:
            if 查锚(k, prog, anc, '门') and prog not in reach:
                per.setdefault(k, []).append(f'门所在程序没接进流程（从流程入口调用不到）：{prog}')
        for prog, anc in tests:
            if 查锚(k, prog, anc, '自检') and prog not in run:
                per.setdefault(k, []).append(f'自检没人跑（流程里没有“{os.path.basename(prog)} 自检”的调用）：{prog}')
    glob_ += 挂钩检查(files)
    for name, txt in extra_tables:
        if re.search(r'^\| *[A-Z]\d+b? *\|', txt, re.M): glob_.append(f'出现第二份踩坑总表：{name}（总表只能有一份）')
    if settings is not None:
        need = [('SessionStart', '', '开工提醒.sh'), ('Stop', '', '闸门.py" 收工'), ('PreToolUse', 'Agent', '闸门.py" 子代理'),
                ('PreToolUse', 'Workflow', '闸门.py" 子代理'), ('PreToolUse', 'SendUserFile', '闸门.py" 发文件'), ('PreToolUse', 'Bash', '闸门.py" 命令'), ('PostToolUse', 'SendUserFile', '闸门.py" 发文件后')]
        hk = settings.get('hooks', {})
        for ev, mt, cmd in need:
            if not any(mt in (x.get('matcher') or '') and any(cmd in (y.get('command') or '') for y in x.get('hooks', [])) for x in hk.get(ev, [])):
                glob_.append(f'Claude 钩子没配上：{ev} {mt} → {cmd}（.claude/settings.json）')
        for ev, xs in hk.items():   # G14：钩子不许锁死——闸门程序必须存在，python 命令必须带 || true
            for x in xs:
                for y in x.get('hooks', []):
                    cm = y.get('command') or ''
                    for pth in re.findall(r'视频/工具/([^"\s]+\.(?:py|sh))', cm):
                        if pth not in files: glob_.append(f'钩子会锁死：{ev} 指向的程序不存在：{pth}')
                    if cm.startswith('python3') and '|| true' not in cm:
                        glob_.append(f'钩子会锁死：钩子命令没有“程序缺失时放行”（|| true）：{cm[-50:]}')
    return per, glob_


def 挂钩检查(files):
    """A26/A42：核查程序靠出片程序（make_video.py、render.py）的原文挂钩（src.index/split/replace 的那一句），
    出片程序一改、那一句没了，核查程序就会崩或悄悄失效。逐个查：每个挂钩的原文都必须还在出片程序里。"""
    out = []
    for f, t in files.items():
        if f in ('make_video.py', 'render.py', '规则执行核查.py') or 'make_video.py' not in t: continue
        tg = set(re.findall(r"open\([^)]*?([\w\u4e00-\u9fff]+\.py)", t))   # 它用 open() 读进来的那些程序
        base = ''.join(files[g] for g in files if g != f and os.path.basename(g) in tg)
        for l in 有效行(t):
            for anc in re.findall(r"""(?:_?src|read\(\))\.(?:index|split|replace)\(\s*(['"])(.+?)\1""", l):
                if anc[1] not in base: out.append(f'{f} 挂钩的出片程序原文没了：“{anc[1][:40]}”（A26/A42：改出片程序后核查程序要跟着改）')
    return out


def 读设置():
    for c in (os.environ.get('CLAUDE_PROJECT_DIR', ''), '/home/user/literate-enigma', P):
        f = f'{c}/.claude/settings.json'
        if c and os.path.exists(f): return json.load(open(f))
    return None


def 其他总表():
    return [(os.path.relpath(f, V), open(f).read()) for f in glob.glob(f'{V}/*.md')
            if os.path.basename(f) == '踩坑总表.md']


def 当场自检(files):
    key = hashlib.sha256(''.join(k + files[k] for k in sorted(files)).encode() + open(STD, 'rb').read()).hexdigest()
    try: c = json.load(open(CACHE))
    except Exception: c = {}
    if c.get('key') == key: return []
    bad = []
    for cmd in FAST:
        if cmd[0] not in files: bad.append(f'当场自检的程序不存在：{cmd[0]}'); continue
        r = subprocess.run(['python3', f'{T}/{cmd[0]}', *cmd[1:]], capture_output=True, text=True, cwd=T)
        if r.returncode != 0:
            tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            bad.append(f'自检不通过：{" ".join(cmd)} → {" / ".join(tail)[:200]}')
    if not bad:
        try: json.dump({'key': key}, open(CACHE, 'w'))
        except Exception: pass
    return bad


def 机器自检():
    std, cl, reg, files = open(STD).read(), open(f'{P}/CLAUDE.md').read(), json.load(open(REG)), 程序表()
    fails = []
    def bad(name, std_=std, cl_=cl, reg_=reg, files_=files, extra=(), want=None):
        per, gl = 核查(std_, cl_, reg_, files_, extra_tables=extra)
        hit = [f'{kk}：{m}' for kk, v in per.items() for m in v] + gl
        if not any((want or '') in m for m in hit) or not hit: fails.append(f'没抓到：{name}')
    # 先取一条门和自检都在、原样完整的规矩做样本
    per0, gl0 = 核查(std, cl, reg, files)
    ok = [k for k in reg if not k.startswith('_') and k not in per0 and reg[k].get('门') and reg[k].get('自检')]
    if not ok: return ['机器自检找不到一条完整的规矩做样本']
    k = ok[0]; prog, anc = reg[k]['门'][0]
    bad('新坑没登记', std_=std.replace('\n| A1 |', '\n| Z9 | 自检造的坑 | x | y |\n| A1 |', 1), want='Z9')
    bad('新守则没登记', cl_=cl.rstrip('\n') + '\n99. 自检造的守则\n', want='没登记')
    i = std.index('### 硬性标准'); j = std.index('\n1. ', i)
    bad('新标准没登记', std_=std[:j] + '\n98. 自检造的标准' + std[j:], want='没登记')
    if '## 附：交付前检查单' in std:
        i2 = std.index('## 附：交付前检查单'); j2 = std.index('\n- [ ] ', i2)
        per9, _ = 核查(std[:j2] + '\n- [ ] 自检造的检查项' + std[j2:], cl, reg, files)
        if not any(k.startswith('单') and any(('没登记' in m or '条文变了' in m) for m in v) for k, v in per9.items()): fails.append('没抓到：检查单新加一项没登记')
    r2 = json.loads(json.dumps(reg)); r2[k]['门'][0] = [prog, anc + '（自检改坏的锚）']
    bad('锚被删', reg_=r2, want='锚不在')
    r3 = json.loads(json.dumps(reg)); r3[k]['门'][0] = ['自检造的不存在.py', anc]
    bad('程序不存在', reg_=r3, want='程序不存在')
    iso = '自检造的' + '孤立程序.py'   # 拼出来的名字：不能原样出现在本程序里，否则会被当成“有人调用”
    f4 = dict(files); f4[iso] = f'x = "{anc}"\n'
    r4 = json.loads(json.dumps(reg)); r4[k]['门'][0] = [iso, anc]
    bad('程序没接进流程', reg_=r4, files_=f4, want='没接进流程')
    r5 = json.loads(json.dumps(reg)); r5[k]['自检'] = []; r5[k].pop('同', None)
    bad('没有自检', reg_=r5, want='没有自检')
    nobody = '自检造的' + '没人跑.py'
    f6 = dict(files); f6[nobody] = 'fails.append("没抓到：自检造的")\n'
    r6 = json.loads(json.dumps(reg)); r6[k]['自检'] = [[nobody, '自检造的']]; r6[k].pop('同', None)
    bad('自检没人跑', reg_=r6, files_=f6, want='自检没人跑')
    hk = next((x for x in reg if not x.startswith('_') and 只靠人(reg, x)), None)
    if hk:
        r10 = json.loads(json.dumps(reg)); r10[hk].pop('为什么程序判不了', None)
        bad('只靠人确认、没写为什么程序判不了', reg_=r10, want='为什么程序判不了')
    bad('第二份总表', extra=[('踩坑总表.md', '| A1 | x | y | z |\n')], want='第二份')
    f9 = dict(files); hk_ = next((x for x in re.findall(r"src\.index\('([^']+)'", files.get('交付核查.py', ''))), None)
    if hk_: f9['make_video.py'] = files['make_video.py'].replace(hk_, hk_[:len(hk_) // 2] + '※自检改掉※' + hk_[len(hk_) // 2:])
    if not hk_ or not any('挂钩' in g for g in 核查(std, cl, reg, f9)[1]): fails.append('没抓到：核查程序挂钩的出片程序原文被改掉（A26/A42）')
    st = 读设置()
    if st:
        s2 = json.loads(json.dumps(st))
        for xs in s2['hooks'].values():
            for x in xs:
                for y in x['hooks']: y['command'] = y['command'].replace(' || true', '')
        per7, gl7 = 核查(std, cl, reg, files, s2)
        if not any('钩子会锁死' in g for g in gl7): fails.append('没抓到：钩子会锁死（G14）')
        s3 = json.loads(json.dumps(st)); s3['hooks']['PreToolUse'][0]['hooks'][0]['command'] = 'python3 "$CLAUDE_PROJECT_DIR/视频/工具/钩子/不存在.py" x || true'
        per8, gl8 = 核查(std, cl, reg, files, s3)
        if not any('不存在.py' in g for g in gl8): fails.append('没抓到：钩子指向的程序不存在（G14）')
    # 原样不得误报（基线里的缺口除外，由 main 处理）
    return fails


def main():
    a = sys.argv[1:]
    if '--自检' in a:
        f = 机器自检()
        print('规则执行机器自检：' + ('通过（新坑、新守则、新标准没登记，锚被删，程序不存在，没接进流程，没有自检，自检没人跑，第二份总表，钩子会锁死，挂钩原文被改——造的错全部抓到）' if not f else '失灵！' + '；'.join(f)))
        return 1 if f else 0
    std, cl = open(STD).read(), open(f'{P}/CLAUDE.md').read()
    reg = json.load(open(REG)) if os.path.exists(REG) else {}
    files = 程序表()
    per, gl = 核查(std, cl, reg, files, 读设置(), 其他总表())
    R = 规矩(std, cl); R.pop('__重复__', None)
    base = set(json.load(open(BASE))) if os.path.exists(BASE) else set()
    # 基线只许减少：已经完整的自动从基线删掉；基线外的缺口一律停
    done = sorted(k for k in base if k in R and k not in per)
    gone = sorted(k for k in base if k not in R)
    if (done or gone) and os.path.exists(BASE):
        json.dump(sorted(base - set(done) - set(gone)), open(BASE, 'w'), ensure_ascii=False, indent=0)
        base -= set(done) | set(gone)
    try:   # 基线只许减少：不许比上一次提交多出任何一条（防止往基线里塞缺口来绕过）
        head = subprocess.run(['git', '-C', V, 'show', f'HEAD:视频/工具/{os.path.basename(BASE)}'], capture_output=True, text=True)
        if head.returncode == 0:
            more = sorted(base - set(json.loads(head.stdout)))
            if more: gl.append(f'缺口基线只许减少，这次多了：{" ".join(more)}（给它们配好门和自检，不许塞进基线）')
    except Exception: pass
    import 同意记录追加 as _TY; gl += _TY.查() + _TY.自检()   # 用户同意记录只许追加（带自检）
    for p in STAMPED:
        if not 印章有效(p): gl.append(f'{STAMPED[p][1]} 改过、慢自检的印章对不上：在视频工作目录跑 python3 {os.path.relpath(T, P)}/{p}，通过后再提交（A26/A42：改出片程序后必须先过守门自检）')
    new = {k: v for k, v in per.items() if k not in base}
    n = {p: sum(1 for k in R if k.startswith(p)) for p in ('守则', '铁', '法', '音', '画', '文', '流', '单')}
    npit = len(R) - sum(n.values())
    部分 = [k for k in R if reg.get(k, {}).get("部分靠人")]   # 门只管得了一部分的规矩，如实列出（2026-10-23 覆盖审查）
    if '--状态' in a:
        print(f'【规则执行机器】规矩 {len(R)} 条：已由程序执行 {len(R) - len(per)} 条，'
              f'缺口 {len(per)} 条（只许减少，目标 0）；只能靠人判的 {sum(只靠人(reg, k) for k in R)} 条：{" ".join(k for k in R if 只靠人(reg, k))}；程序只管一部分、其余靠逐句确认或用户把关的 {len(部分)} 条：{" ".join(部分)}；判断靠人、但由程序逐条点名且只认固定格式的 {sum(1 for k in R if reg.get(k, {}).get("固定格式确认"))} 条' + (f'；基线外问题 {len(new) + len(gl)} 处，提交和推送会被拦住' if new or gl else ''))
        return 0
    if '--清单' in a:
        for k in R:
            g, t = 解析(reg, k)
            print(k, R[k][:30], '| 门:', '；'.join(f'{p}「{x[:20]}」' for p, x in g) or '无', '| 自检:', '；'.join(f'{p}' for p, _ in t) or '无',
                  '| 缺口' if k in per else '')
        return 0
    if not new and not gl:
        gl += 当场自检(files)
        sf = 机器自检()
        if sf: gl.append('规则执行机器自检失灵：' + '；'.join(sf))
    if new or gl:
        print(f'【停止】规则执行核查不通过（CLAUDE.md 第16条）：{len(new)} 条规矩没有完整执行，另有 {len(gl)} 处问题')
        for m in gl[:20]: print('  ✘', m)
        for k, v in list(new.items())[:30]: print(f'  ✘ {k}：{"；".join(v)[:220]}')
        if len(new) > 30: print(f'  ……还有 {len(new) - 30} 条（python3 {os.path.relpath(__file__, P)} 看全部）')
        return 1
    print(f'规则执行核查：通过——规矩 {len(R)} 条（守则 {n["守则"]}、坑 {npit}、标准 {len(R) - npit - n["守则"] - n["单"]}、检查单 {n["单"]}），'
          f'{len(R) - len(per)} 条门在、接进流程、有自检' + (f'；缺口 {len(per)} 条在基线里（只许减少，目标 0）' if per else '；缺口 0') + '；机器自检通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
