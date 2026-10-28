#!/usr/bin/env python3
"""机制使用核查（G60）：机制必须真跑起来，证据只能由正式入口写。
用户 2026-10-26 原话：“我们要求已经去执行的这些机制一定要跑起来，一定要跑起来，必须必须必须必须必须必须必须得跑起来”
“一定要严格严格，非常非常非常非常非常严格的按照我们要求的这个流程来做，不要随随便便的去乱发挥。”
  证据：视频/制作记录/证据/NN.jsonl，一步一行：步、入口、入口指纹（入口程序的 git blob 号）、脚本指纹、结果、时刻、会话、前一行的号、本行的号。
        只由正式入口写：开工记录.py、生成文本.py、草稿声音.sh、交付核查.py、定稿流水线.sh（机制清单.json 的“步骤”）。
        手写、临时脚本、改过的入口写不出对得上的证据；证据文件被手改（号对不上、断链）就停。命令闸门拦 Bash 写证据目录。
  查：  交付核查 出片前 / 出片后、定稿流水线 开头按 机制清单.json 的“阶段”查本篇证据链：少一步、顺序不对、结果不是通过 → 停（28 起）。
  清单：规则执行核查 每次查 草稿声音.sh、定稿流水线.sh、交付核查.py 调的程序、.github/workflows 的工作流都在机制清单里（新机制不进清单就停）。
用法：python3 证据.py --记 NN 步（只给 .sh 入口用，父进程必须是那个入口）| --查 NN 阶段 | --状态 NN | --自检
  G71：--闲置 [--提醒]（机制连续两篇该用没用、或建好后第一篇就没用上 → 停）| --全查（28 起各篇证据链，ci.yml 每次推送跑）
      “真用上”= 证据链里有那一步的通过行；每篇要跑的 GitHub 工作流 = 证据详情“工作流”或 视频/云端/结果/ 里有“工作流 X”和“篇 NN”两行"""
import os, sys, json, re, hashlib, datetime, subprocess
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
清单F = f'{T}/机制清单.json'
目录 = [f'{V}/制作记录/证据']   # 自检换成临时目录
起 = 28   # 27 已在做，不回头卡（和 开工必读 做事对照 同一起始篇）
闲置从 = 28   # G71：机制闲置报警从哪篇起算（演练改它重放）
云端结果 = [f'{V}/云端/结果']


def 清单(): return json.load(open(清单F))
def blob(path):
    b = open(path, 'rb').read(); return hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()
def 号(rec): return hashlib.sha256(json.dumps({k: v for k, v in rec.items() if k != '本'}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
def 文件(no): return f'{目录[0]}/{no}.jsonl'


def 读(no):
    f = 文件(no)
    if not os.path.exists(f): return []
    return [json.loads(l) for l in open(f) if l.strip()]


def 会话():
    try:
        import 会话开工 as K; r = K.读记录(); return (r or {}).get('会话', '')
    except Exception: return ''


def 脚本指纹(no):
    for f in (f'scripts/{no}.json', f'{V}/脚本/{no}.json'):
        if os.path.exists(f): return hashlib.sha256(open(f, 'rb').read()).hexdigest()[:16]
    return ''


def _写(no, rec):
    rs = 读(no); rec['前'] = rs[-1]['本'] if rs else '0'; rec['本'] = 号(rec)
    os.makedirs(目录[0], exist_ok=True)
    with open(文件(no), 'a') as f: f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + '\n')
    return rec


def 记(no, 步, 结果='通过', 详情=None, 入口=None):
    """正式入口调用：python 入口不传 入口（取 sys.argv[0]）；.sh 入口经 --记，由父进程认定"""
    no = str(no).zfill(2); S = 清单()['步骤']
    if not no.isdigit() or int(no) < 起: return None
    if 步 not in S: raise SystemExit(f'【停止】证据：没有这一步：{步}（机制清单.json 的“步骤”）')
    入口 = 入口 or os.path.basename(sys.argv[0])
    if 入口 not in S[步]['入口']: raise SystemExit(f'【停止】证据：“{步}”只能由 {"、".join(S[步]["入口"])} 写，不能由 {入口} 写（G60：不许手写、不许绕过正式入口）')
    rec = {'步': 步, '入口': 入口, '入口指纹': blob(f'{T}/{入口}'), '脚本指纹': 脚本指纹(no), '结果': 结果,
           '时刻': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), '会话': 会话(), '详情': 详情 or {}}
    return _写(no, rec)


def 父入口():
    """--记 的调用者：父进程命令行里那个 .sh 必须就是本工具目录下的正式入口"""
    try: a = open(f'/proc/{os.getppid()}/cmdline', 'rb').read().split(b'\0')
    except Exception: return None
    for x in a[:3]:
        x = x.decode(errors='ignore')
        if x and not os.path.isabs(x): x = os.path.join(os.path.realpath(f'/proc/{os.getppid()}/cwd'), x)
        if x.endswith('.sh') and os.path.exists(x) and os.path.realpath(os.path.dirname(x)) == os.path.realpath(T): return os.path.basename(x)
    return None


_历史 = {}
def 认得(入口, fp):
    """入口指纹是这个入口的现行版本或 git 里提交过的版本"""
    p = f'{T}/{入口}'
    if os.path.exists(p) and blob(p) == fp: return True
    return fp in 历史(入口, T)


def 历史(入口, T_):
    """入口在 git 里提交过的各版本 blob。K89：浅克隆（CI 检出、会话 --depth 1）看不到旧版本，误判“不是正式入口写的”：
    是浅克隆就先往回拉 400 个提交再找（拉不下来照样找不到，照停，不放宽）"""
    k = (入口, T_)
    if k not in _历史:
        g = lambda *x: subprocess.run(['git', '-C', T_, *x], capture_output=True, text=True).stdout
        if g('rev-parse', '--is-shallow-repository').strip() == 'true': g('fetch', '-q', '--deepen=400', 'origin')
        r = g('log', '--format=', '--raw', '--no-abbrev', '-n', '400', '--', 入口)
        _历史[k] = {l.split()[3] for l in r.splitlines() if l.startswith(':') and len(l.split()) > 4}
    return _历史[k]


def 查(no, 阶段, rs=None, C=None):
    """返回问题列表（空 = 证据链完整）"""
    no = str(no).zfill(2)
    if not no.isdigit() or int(no) < 起: return []
    C = C or 清单(); rs = 读(no) if rs is None else rs; err = []
    前 = '0'
    for i, r in enumerate(rs):
        if r.get('前') != 前 or r.get('本') != 号(r): err.append(f'[G60] 证据/{no}.jsonl 第 {i + 1} 行被手改或断链（证据只能由正式入口写）'); break
        前 = r['本']
        if r.get('入口') not in C['步骤'].get(r.get('步'), {}).get('入口', []) or not 认得(r['入口'], r.get('入口指纹', '')):
            err.append(f'[G60] 证据/{no}.jsonl 第 {i + 1} 行（{r.get("步")}）不是正式入口写的（入口 {r.get("入口")} 的指纹对不上现行或提交过的版本）'); break
    if err: return err
    need = C['阶段'][阶段]; bound = len(rs); 后 = None
    for s in reversed(need):
        i = next((j for j in range(bound - 1, -1, -1) if rs[j]['步'] == s and rs[j]['结果'] == '通过'), None)
        if i is None:
            有 = any(r['步'] == s and r['结果'] == '通过' for r in rs)
            err.append(f'[G60] 第{no}篇{阶段}要先有“{s}”的证据（{C["步骤"][s]["做什么"][:24]}…，正式入口 {"、".join(C["步骤"][s]["入口"])}）'
                       + (f'：有，但在“{后}”之后，顺序不对，按步骤表重跑' if 有 and 后 else '：少了这一步，按步骤表补跑'))
            return err
        后 = s; bound = i
    for m in C['机制']:
        k = m.get('详情')
        if not k or m['证据'] not in need: continue
        r = next((x for x in reversed(rs) if x['步'] == m['证据'] and x['结果'] == '通过'), {})
        if not r.get('详情', {}).get(k): err.append(f'[G60] 机制“{m["名"]}”没留下使用证据（{m["证据"]} 的 {k}）：重跑 {"、".join(C["步骤"][m["证据"]]["入口"])}')
    return err


def 程序名(txt):
    return set(re.findall(r'\$T/((?:[\w一-鿿]+/)?[\w一-鿿]+\.(?:py|sh))', txt)) | set(re.findall(r"f'\{T\}/([\w一-鿿/]+\.(?:py|sh))'", txt))


def 清单问题(C=None, 入口文=None, 工作流=None):
    """规则执行核查 每次调：新机制（新调用的程序、新工作流）不进清单就停；正式入口里写证据的那一句还在"""
    C = C or 清单()
    if 入口文 is None:
        入口文 = {f: open(f'{T}/{f}').read() for f in ('草稿声音.sh', '定稿流水线.sh', '交付核查.py') if os.path.exists(f'{T}/{f}')}
    if 工作流 is None:
        工作流 = sorted({w for d in (f'{P}/.github/workflows', '/home/user/literate-enigma/.github/workflows') if os.path.isdir(d) for w in os.listdir(d)})   # 两个仓库的工作流
    包含 = {os.path.basename(x) for m in C['机制'] + C.get('管执行', []) for x in m.get('包含', [])}   # G83：管执行的机制也是登记过的
    err = []
    for f, t in 入口文.items():
        for p in sorted(程序名(t)):
            if os.path.basename(p) not in 包含 and os.path.basename(p) != '证据.py':
                err.append(f'[G60] {f} 调用的 {p} 不在机制清单里（新机制要登记：机制清单.json 的“机制”写它的使用证据、在哪一步查）')
    for w in 工作流:
        if w.endswith(('.yml', '.yaml')) and w not in C.get('工作流', {}):
            err.append(f'[G60] GitHub 工作流 {w} 不在机制清单里（写它每篇是否要跑、证据 = 运行号）')
    for s, v in C['步骤'].items():
        for e in v['入口']:
            t = 入口文.get(e) if e in 入口文 else (open(f'{T}/{e}').read() if os.path.exists(f'{T}/{e}') else None)
            if t is None: err.append(f'[G60] 步骤“{s}”的正式入口 {e} 不存在'); continue
            anc = '证据.py --记' if e.endswith('.sh') else '_ZJ.记('
            if not any(anc in l and not l.strip().startswith('#') for l in t.splitlines()):
                err.append(f'[G60] 正式入口 {e} 里没有写证据的那一句（{anc}）：这一步跑了也留不下证据')
    for m in C['机制']:
        if m['证据'] not in C['步骤']: err.append(f'[G60] 机制“{m["名"]}”的证据步“{m["证据"]}”不在步骤里')
    return err


def 状态(no):
    rs = 读(no); C = 清单()
    if not rs: return f'【机制证据】第{no}篇还没有证据（{"28 起出片前要有" if int(no) >= 起 else "27 以前不查"}）'
    last = {}
    for r in rs: last[r['步']] = r
    done = [s for s in C['阶段']['定稿'] + ['定稿'] if s in last]
    缺 = [s for s in C['阶段']['定稿'] + ['定稿'] if s not in last]
    return f'【机制证据】第{no}篇已留：{" → ".join(done) or "无"}；还没有：{" ".join(缺) or "无"}'


def 自检():
    import tempfile, shutil
    f = []; old = 目录[0]; tmp = tempfile.mkdtemp(prefix='证据自检_'); 目录[0] = tmp; C = 清单()
    try:
        fp = {e: blob(f'{T}/{e}') for v in C['步骤'].values() for e in v['入口']}
        def 造(no, 步, **k):
            e = C['步骤'][步]['入口'][0]
            return _写(no, {'步': 步, '入口': e, '入口指纹': fp[e], '脚本指纹': 'x', '结果': k.get('结果', '通过'), '时刻': 't', '会话': '自检',
                           '详情': k.get('详情', {'撞车提醒': True, '做事对照': True} if 步 == '开工记录' else {})})
        if not 查('98', '出片前'): f.append('没抓到：一条证据都没有就出片')
        造('98', '开工记录'); 造('98', '草稿声音')
        if not any('文本门' in e for e in 查('98', '出片前')): f.append('没抓到：少了文本门')
        造('98', '文本门')
        if not any('顺序不对' in e for e in 查('98', '出片前')): f.append('没抓到：没过文本门就做了声音（顺序不对）')
        造('98', '草稿声音')
        if 查('98', '出片前'): f.append(f'误报：证据链完整被判不合格：{查("98", "出片前")}')
        if not 查('98', '出片后'): f.append('没抓到：没过出片前就做出片后')
        造('98', '出片前', 结果='不通过')
        if not 查('98', '出片后'): f.append('没抓到：出片前不通过也算数')
        造('98', '出片前')
        if 查('98', '出片后'): f.append('误报：出片后的证据链完整')
        造('97', '开工记录', 详情={'撞车提醒': True}); 造('97', '文本门'); 造('97', '草稿声音')
        if not any('做事对照' in e for e in 查('97', '出片前')): f.append('没抓到：开工记录没写做事对照（机制没留下使用证据）')
        L = open(文件('98')).read().splitlines(); r = json.loads(L[1]); r['结果'] = '通过'; r['时刻'] = '手改'; L[1] = json.dumps(r, ensure_ascii=False)
        open(文件('98'), 'w').write('\n'.join(L) + '\n')
        if not any('手改' in e for e in 查('98', '出片前')): f.append('没抓到：证据文件被手改')
        rs = [dict(x) for x in 读('97')]; rs = [{**x, '入口指纹': '0' * 40} if x['步'] == '文本门' else x for x in rs]
        前 = '0'
        for x in rs: x['前'] = 前; x['本'] = 号(x); 前 = x['本']
        if not any('不是正式入口' in e for e in 查('97', '出片前', rs=rs)): f.append('没抓到：入口指纹对不上（临时脚本冒充正式入口）')
        try: 记('96', '文本门', 入口='自检冒充.py'); f.append('没抓到：不是正式入口也能写证据')
        except SystemExit: pass
        if 查('27', '出片前'): f.append('误报：27 以前不查')
        if not 清单问题(C, {'草稿声音.sh': 'python3 $T/自检造的新机制.py $no\npython3 $T/证据.py --记 $no 草稿声音'}, []): f.append('没抓到：草稿声音.sh 加了新程序没进机制清单')
        if not any('工作流' in e for e in 清单问题(C, {}, ['drill-自检造的.yml'])): f.append('没抓到：新 GitHub 工作流没进机制清单')
        if not any('没有写证据' in e for e in 清单问题(C, {'草稿声音.sh': '# python3 $T/证据.py --记 $no 草稿声音'}, [])): f.append('没抓到：正式入口里写证据的那句被删掉（只剩注释）')
        if 清单问题(): f.append(f'现行清单不全：{清单问题()[:2]}')
        f += [x.replace('证据 闲置自检：', '') for x in 闲置自检(C)]   # G71
    finally:
        目录[0] = old; shutil.rmtree(tmp, ignore_errors=True)
    # K89：浅克隆里入口的旧版本也要认得（先往回拉），从没提交过的照样不认
    d_ = tempfile.mkdtemp(prefix='证据浅克隆_'); G_ = lambda c, *x: subprocess.run(['git', '-C', c, '-c', 'user.name=t', '-c', 'user.email=t@t', *x], capture_output=True, text=True).stdout.strip()
    os.makedirs(f'{d_}/src'); G_(f'{d_}/src', 'init', '-q'); open(f'{d_}/src/x.sh', 'w').write('v1\n'); G_(f'{d_}/src', 'add', '-A'); G_(f'{d_}/src', 'commit', '-qm', '1')
    b1 = G_(f'{d_}/src', 'rev-parse', 'HEAD:x.sh'); open(f'{d_}/src/x.sh', 'w').write('v2\n'); G_(f'{d_}/src', 'commit', '-qam', '2')
    subprocess.run(['git', 'clone', '-q', '--depth', '1', f'file://{d_}/src', f'{d_}/c'], capture_output=True)
    if b1 not in 历史('x.sh', f'{d_}/c'): f.append('没认得：浅克隆里入口提交过的旧版本（K89：CI 误判 28 证据链）')
    if '0' * 40 in 历史('x.sh', f'{d_}/c'): f.append('放得太宽：从没提交过的指纹也认')
    shutil.rmtree(d_, ignore_errors=True)
    return ['证据 自检：' + x for x in f]


# —— G71 机制闲置报警（用户 2026-10-26：“一定要有一个确保执行机制，一定要有一个绝对的，绝对的确保执行机制，而且要严格执行”）
def _已过(记录, 归档, 开了=()):
    """该用机制的篇：归档了定稿视频、证据里有“定稿”，或者后面已经有篇定稿了。
    K93（2026-10-28 用户要 29–40 并行做，主会话先写了 29–31 的交接 NN.md）：以前“后面开了新篇（有 NN.md）”就算前面做完，
    并行做时 28 还在出片、29/30 只有交接，全被报闲置（CI 红、开工记录 不许开新篇）；现在只认定稿：自己定稿了，或后面有篇定稿了"""
    ns = set(记录) | set(归档) | set(开了)
    定 = {n for n in ns if n in 归档 or any(r.get('步') == '定稿' for r in 记录.get(n, []))}
    return sorted(n for n in ns if int(n) >= 闲置从 and (n in 定 or any(m > n for m in 定)))


def _现场():
    import glob
    记录 = {os.path.basename(f)[:2]: 读(os.path.basename(f)[:2]) for f in glob.glob(f'{目录[0]}/[0-9][0-9].jsonl')}
    归档 = {os.path.basename(f)[:2] for f in glob.glob(f'{V}/视频/[0-9][0-9].mp4')}
    云 = '\n'.join(open(f).read() for f in glob.glob(f'{云端结果[0]}/*.结果.txt'))
    开了 = {os.path.basename(f)[:2] for f in glob.glob(f'{V}/制作记录/[0-9][0-9].md')}
    return 记录, 归档, 云, 开了


def _下线(名, 同意=None):
    if 同意 is None:
        try: 同意 = json.load(open(f'{T}/用户同意记录.json')).get('记录', [])
        except Exception: 同意 = []
    return any('下线' in r.get('用于', '') and 名[:6] in r.get('用于', '') and r.get('来源') != '演练' for r in 同意)


def 闲置(C=None, 记录=None, 归档=None, 云=None, 同意=None, 开了=()):
    """返回 [(名, 最近一次真用上的篇或 None, 该用没用的篇列表, 红)]：每个机制（含每篇要跑的 GitHub 工作流）"""
    C = C or 清单()
    if 记录 is None: 记录, 归档, 云, 开了 = _现场()
    篇们 = _已过(记录, 归档 or set(), 开了); out = []
    项 = [(m['名'], m.get('起', 0), m.get('下线'), lambda rs, n, m=m: any(r.get('步') == m['证据'] and r.get('结果') == '通过' and (not m.get('详情') or (r.get('详情') or {}).get(m['详情'])) for r in rs)) for m in C['机制']]
    项 += [(f'GitHub 工作流 {w}', v.get('起', 0), v.get('下线'), lambda rs, n, w=w: any(w in ((r.get('详情') or {}).get('工作流') or []) for r in rs) or bool(re.search(rf'^工作流 {re.escape(w)}\b[\s\S]*?^篇 {n}\b|^篇 {n}\b[\s\S]*?^工作流 {re.escape(w)}\b', 云 or '', re.M)))
           for w, v in C.get('工作流', {}).items() if v.get('每篇')]
    for 名, 起篇, 下线, 用 in 项:
        ns = [n for n in 篇们 if int(n) >= int(起篇 or 0)]
        if not ns or (下线 and _下线(名, 同意)): continue
        used = [n for n in ns if 用(记录.get(n, []), n)]; last = used[-1] if used else None
        没 = [n for n in ns if not last or n > last]
        out.append((名, last, 没, len(没) >= 2 or (len(没) >= 1 and not last)))
    return out


def 闲置问题(**k):
    return [f'[G71] 机制“{名}”闲置：第{"、".join(没)}篇该用没用（最近一次真用上：{"第" + last + "篇" if last else "建好后一次都没用上"}）'
            f'——查清是机制坏了（修好再开工）还是不该存在（用户同意后在机制清单写“下线”）' for 名, last, 没, 红 in 闲置(**k) if 红]


def 全查(记录=None, C=None):
    """28 起各篇证据链（ci.yml 每次推送跑）：每篇查到它已走到的最远一个阶段"""
    C = C or 清单(); 记录 = 记录 if 记录 is not None else _现场()[0]; err = []
    for n in sorted(记录):
        rs = 记录[n]; 到 = [s for s in ('出片前', '出片后', '定稿') if any(r.get('步') == s for r in rs)]
        err += 查(n, 到[-1] if 到 else '出片前', rs=rs, C=C) if 到 else [e for e in 查(n, '出片前', rs=rs, C=C) if '手改' in e or '不是正式入口' in e]
    return err


def 闲置自检(C=None):
    C = C or 清单(); f = []
    def rs(*ss): return [{'步': s, '结果': '通过', '详情': {m['详情']: True for m in C['机制'] if m['证据'] == s and m.get('详情')}} for s in ss]
    全 = rs(*C['阶段']['定稿'], '定稿')
    缺 = rs(*[s for s in C['阶段']['定稿'] if s != '草稿声音'], '定稿')
    k = lambda **x: [p for p in 闲置问题(C=C, 同意=[], 云='', 归档=set(), **x)]
    if k(记录={'90': 全, '91': 全}): f.append(f'误报：两篇机制全用上了被报闲置：{k(记录={"90": 全, "91": 全})[:1]}')
    if not any('草稿声音' in p for p in k(记录={'90': 全, '91': 缺, '92': 缺})): f.append('没抓到：连续两篇没跑草稿声音')
    if any('草稿声音' in p for p in k(记录={'90': 全, '91': 缺, '92': 全})): f.append('误报：只隔一篇没用、后面又用上了')
    半 = [r for r in 缺 if r['步'] != '定稿']   # K91：并行做，前面的篇还没定稿、后面只有交接 NN.md，不算闲置；后面有篇定稿了、前面两篇照样没用 → 照报
    if k(记录={'90': 全, '91': 半}, 开了={'92', '93'}): f.append('误报：并行做时还没定稿的篇、只有交接的篇被报闲置（K93）')
    if not any('草稿声音' in p for p in k(记录={'90': 全, '91': 半, '92': 缺}, 开了=set())): f.append('没抓到：后面 92 定稿了，91、92 都没跑草稿声音（K93 不许放宽）')
    if not any('建好后一次都没用上' in p for p in k(记录={'90': 缺, '91': []})): f.append('没抓到：建好后第一篇就没用上')
    if any('90' in p for p in k(记录={'90': rs('开工记录')})): f.append('误报：正在做的篇（没定稿、后面没开新篇）也算该用没用')
    C2 = json.loads(json.dumps(C)); C2['工作流']['自检造的.yml'] = {'每篇': True}
    if not any('自检造的.yml' in p for p in 闲置问题(C=C2, 记录={'90': 全, '91': 全}, 归档=set(), 云='', 同意=[])): f.append('没抓到：每篇要跑的 GitHub 工作流两篇都没跑')
    if any('自检造的.yml' in p for p in 闲置问题(C=C2, 记录={'90': 全, '91': 全}, 归档=set(), 云='工作流 自检造的.yml\n篇 91\n', 同意=[])): f.append('误报：GitHub 运行记录里有第91篇')
    C3 = json.loads(json.dumps(C)); next(m for m in C3['机制'] if m['证据'] == '草稿声音')['下线'] = True
    名 = next(m['名'] for m in C3['机制'] if m['证据'] == '草稿声音')
    if not any('草稿声音' in p for p in 闲置问题(C=C3, 记录={'90': 缺, '91': 缺}, 归档=set(), 云='', 同意=[])): f.append('没抓到：写了“下线”却没有用户原话')
    if any('草稿声音' in p for p in 闲置问题(C=C3, 记录={'90': 缺, '91': 缺}, 归档=set(), 云='', 同意=[{'用于': f'下线 {名}', '来源': '用户消息'}])): f.append('误报：用户同意下线了还报')
    坏 = [dict(r, 前='0', 本='x') for r in 全]
    if not 全查(记录={'90': 坏}, C=C): f.append('没抓到：全查（ci.yml）漏了被手改的证据文件')
    return ['证据 闲置自检：' + x for x in f]


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--自检' in a:
        e = 自检(); print('\n'.join(e) or '证据 自检通过（少一步、顺序不对、不通过、手改、冒充入口、机制没留证据、新机制没进清单：造的全部抓到；完整的不误报）'); sys.exit(1 if e else 0)
    if '--记' in a:
        no, 步 = a[a.index('--记') + 1].zfill(2), a[a.index('--记') + 2]; e = 父入口()
        if not e: sys.exit('【停止】证据.py --记 只能由正式入口（.sh）调用，不许手写证据（G60）')
        记(no, 步, 入口=e); print(f'证据：第{no}篇 {步} 已记（{e}）'); sys.exit(0)
    if '--查' in a:
        no, 阶段 = a[a.index('--查') + 1].zfill(2), a[a.index('--查') + 2]; e = 查(no, 阶段)
        for x in e: print('  ✘', x)
        print(f'第{no}篇 {阶段} 机制证据：' + ('【不全，停】按 视频/开工必读.md ⑤ 步骤表补跑' if e else '齐全')); sys.exit(1 if e else 0)
    if '--闲置' in a:   # G71：开工提醒第一屏、开工记录开下一篇、定稿流水线 ⓪、ci.yml 每次推送
        e = 闲置问题()
        if '--提醒' in a:
            if e: print('\033[1;31m【机制闲置报警（G71）】' + '；'.join(e) + '\033[0m')
            else: print('【机制闲置（G71）】' + ('；'.join(f'{名} 最近用上 第{last}篇' for 名, last, _, _ in 闲置() if last)[:200] or '28 起还没有做完的篇，没有闲置'))
            sys.exit(0)
        for x in e: print('  ✘', x)
        print('机制闲置：' + ('【有闲置，停】' if e else '无')); sys.exit(1 if e else 0)
    if '--全查' in a:
        e = 全查()
        for x in e: print('  ✘', x)
        print('28 起各篇机制证据链：' + ('不全' if e else '齐全')); sys.exit(1 if e else 0)
    if '--状态' in a: print(状态(a[a.index('--状态') + 1].zfill(2))); sys.exit(0)
    e = 清单问题()
    for x in e: print('  ✘', x)
    print('机制清单：' + ('不全' if e else '齐全')); sys.exit(1 if e else 0)
