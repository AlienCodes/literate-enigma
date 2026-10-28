#!/usr/bin/env python3
"""丝滑记录（K，用户 2026-10-27 丝滑主义：“一定要确保这个流程的运行，中间非常的丝滑，没有任何的bug，没有任何的问题，也没有任何程序上之间的冲突”）。
正式入口（会话开工、草稿声音.sh、交付核查、定稿流水线、推送两仓库）每次停下记一条到 制作记录/丝滑/NN.jsonl（没篇号记 会话.jsonl）：
  内容问题 = 门在干活（稿子、声音、画面有毛病被挡下，正常）；
  不丝滑   = 程序毛病、环境缺东西、会话间冲突、要重读重跑、手工绕过（目标 0，每条都要报坑 G54）。
方法进化表 每篇加“不丝滑次数”，比前三篇中位数变差沿用 G65（方法复盘要写查得到的进化落地）。
用法：python3 视频/工具/丝滑.py 记 <入口> <NN|-> "<停下的原因>" [不丝滑|内容问题]
      python3 视频/工具/丝滑.py --次数 NN      python3 视频/工具/丝滑.py --自检
      python3 视频/工具/丝滑.py --未闭环 [--严]   （K56：每条不丝滑都要对上一个报坑登记号 K#；记的时候自动登记，同入口同原因 24 小时内沿用同一个 K#；
                                                  --严 有没对上 K# 的就停）
      python3 视频/工具/丝滑.py --对上 K# <时刻>     （登记没成功的那条手工对上）
      python3 视频/工具/丝滑.py --会话次数 <会话ID>   （K57：会话级不丝滑按会话计）"""
import os, sys, re, json, datetime, tempfile, shutil
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
目录 = [f'{V}/制作记录/丝滑']
不丝滑式 = re.compile(r'Traceback|ModuleNotFound|ImportError|No such file|NoSuchFile|找不到|缺包|缺 ffmpeg|环境|bad substitution|syntax error|'
                    r'锁|冲突|超时|timeout|Timeout|网络|连接|重读|印章|过期|没开工|会话开工|角色闸门|打不上|409|403|Permission|权限|'
                    r'一致（G2|白名单外|镜像|推送|失灵|崩|出错|异常|工作目录|work_\d\d/a\.wav')


接线 = {'定稿流水线.sh': 'python3 "$T/丝滑.py" 记 定稿流水线', '草稿声音.sh': 'python3 $T/丝滑.py 记 草稿声音', '推送两仓库.sh': '丝滑.py" 记 推送两仓库',
        '交付核查.py': "_SH.记('交付核查'", '会话开工.py': "丝滑.记('会话开工'"}


def 分类(说明):
    return '不丝滑' if 不丝滑式.search(说明 or '') else '内容问题'


def 记(入口, 篇, 说明, 类=None):
    类 = 类 or 分类(说明); 篇 = 篇 if re.fullmatch(r'\d\d', 篇 or '') else '会话'
    os.makedirs(目录[0], exist_ok=True)
    r = {'时刻': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), '入口': 入口, '类': 类, '说明': (说明 or '')[:300], '会话': 会话()}
    if 类 == '不丝滑':   # K56：当场登记（同入口同原因 24 小时内沿用同一个 K#），登记不上就留空，--未闭环 --严 停
        r['K'] = 沿用(入口, r['说明']) or 登记[0](f'{篇 if 篇 != "会话" else ""} {入口} 不丝滑（丝滑.py 自动登记）：{r["说明"][:200]}')
    with open(f'{目录[0]}/{篇}.jsonl', 'a') as f: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    if 类 == '不丝滑':
        print(f'【不丝滑（丝滑主义 K）】{入口} 停下不是稿子的问题：{r["说明"][:120]}\n  ' + (f'已登记 {r["K"]}（G54：进踩坑总表、配门、演练）' if r['K'] else
              f'自动登记没成功：python3 视频/工具/报坑.py "{篇 if 篇 != "会话" else ""} {入口}：{r["说明"][:60]}"，再 python3 视频/工具/丝滑.py --对上 K# {r["时刻"]}（K56）'))
    return r


def 会话():
    try:
        sys.path.insert(0, T); import 报坑; return 报坑.本会话()
    except Exception: return ''


def _报(现象):
    try:
        sys.path.insert(0, T); import 报坑, contextlib, io
        with contextlib.redirect_stdout(io.StringIO()): return 报坑.报(现象, 报坑.本会话())
    except BaseException: return ''
登记 = [_报]


def 全部():
    out = []
    for f in sorted(os.listdir(目录[0])) if os.path.isdir(目录[0]) else []:
        if f.endswith('.jsonl'):
            for i, l in enumerate(open(f'{目录[0]}/{f}')):
                try: out.append((f, i, json.loads(l)))
                except Exception: pass
    return out


def 沿用(入口, 说明, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    for _, _, r in reversed(全部()):
        try: t0 = datetime.datetime.strptime(r['时刻'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
        except Exception: continue
        if r.get('K') and r.get('入口') == 入口 and r.get('说明') == 说明 and (now - t0).total_seconds() < 86400: return r['K']
    return ''


def 未闭环():
    """K56：没对上报坑登记号的不丝滑（文件、时刻、说明）"""
    return [(f, r.get('时刻', ''), r.get('说明', '')) for f, _, r in 全部() if r.get('类') == '不丝滑' and not re.fullmatch(r'K\d+', str(r.get('K', '')))]


def 对上(k, 时):
    n = 0
    for f in sorted(os.listdir(目录[0])):
        if not f.endswith('.jsonl'): continue
        ls = open(f'{目录[0]}/{f}').read().splitlines(); new = []
        for l in ls:
            try: r = json.loads(l)
            except Exception: new.append(l); continue
            if r.get('类') == '不丝滑' and r.get('时刻') == 时 and not r.get('K'): r['K'] = k; n += 1
            new.append(json.dumps(r, ensure_ascii=False))
        open(f'{目录[0]}/{f}', 'w').write('\n'.join(new) + '\n')
    return n


def 开工(角色, sid='', 任务=''):
    """K57：会话开工记一条（0 次不丝滑的会话也要算进比较）"""
    os.makedirs(目录[0], exist_ok=True)
    r = {'时刻': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), '入口': '会话开工', '类': '开工', '角色': 角色, '会话': sid or 会话(), '任务': 任务}
    with open(f'{目录[0]}/会话.jsonl', 'a') as f: f.write(json.dumps(r, ensure_ascii=False) + '\n')


def 改门比较(V_=None):
    """K57（沿用 G65）：最近一个改门会话的不丝滑次数比前三个改门会话中位数多，它的任务单里要有查得到的“进化落地：<提交号|G##|K##>”，没有就是问题。
    返回 (打印行, 问题)"""
    V_ = V_ or V; ss = []
    for f, _, r in 全部():
        if f == '会话.jsonl' and r.get('类') == '开工' and r.get('角色') == '改门' and r.get('会话') and r['会话'] not in [s for s, _ in ss]: ss.append((r['会话'], r.get('任务', '')))
    ns = [(s, 会话次数(s), t) for s, t in ss]; 行 = '改门会话不丝滑（K57）：' + ('，'.join(f'{s[-8:]} {n}' for s, n, _ in ns[-4:]) or '还没有记录')
    if len(ns) < 4: return 行, ''
    s, n, t = ns[-1]; prev = sorted(x[1] for x in ns[-4:-1]); med = prev[1]
    if n <= med: return 行 + f'（不比前三个中位数 {med} 差）', ''
    p_ = t if os.path.isabs(t) else f'{V_}/{t}'; txt = open(p_).read() if t and os.path.exists(p_) else ''
    节 = [x for x in re.split(r'\n(?=## )', txt) if s[-8:] in x]
    if any(re.search(r'进化落地：\s*(?:[0-9a-f]{7,}|G\d+|K\d+)', x) for x in 节): return 行 + f'（比中位数 {med} 差，已写进化落地）', ''
    return 行, f'改门会话 {s[-8:]} 不丝滑 {n} 次，比前三个改门会话中位数 {med} 差，任务单（{t or "没写"}）里它的交接没有查得到的“进化落地：<提交号|G##|K##>”（K57/G65）'


def 会话次数(sid):
    return sum(1 for f, _, r in 全部() if f == '会话.jsonl' and r.get('类') == '不丝滑' and r.get('会话') == sid)


def 停下数(d=None):
    """K73：彩排数“停下”只数 不丝滑 和 内容问题（会话开工 写的“开工”记录不是停下）"""
    d = d or 目录[0]; n = 0
    for f in (sorted(os.listdir(d)) if os.path.isdir(d) else []):
        if f.endswith('.jsonl'):
            for l in open(f'{d}/{f}'):
                try: n += json.loads(l).get('类') != '开工'
                except Exception: n += 1   # 读不懂的行也算停下（宁停勿放）
    return n


def 次数(篇, 类='不丝滑'):
    f = f'{目录[0]}/{篇}.jsonl'
    if not os.path.exists(f): return 0
    n = 0
    for l in open(f):
        try: n += json.loads(l).get('类') == 类
        except Exception: pass
    return n


def 自检():
    f = []; old = 目录[0]; d = tempfile.mkdtemp(prefix='丝滑自检_'); 目录[0] = d
    try:
        for s in ("ModuleNotFoundError: No module named 'soundfile'", "bad substitution", '改门锁：别人持锁', '开工必读 更新了，--重读',
                  '两仓库 视频/ 不一致（G2）', '新容器没有 work_25/a.wav', '慢自检的印章对不上'):
            if 分类(s) != '不丝滑': f.append(f'没抓到：“{s}”该算不丝滑（K）')
        for s in ('[T36] S3 有破折号', 'S4 词尾辅音 /t/ 听不清', '[L19] 说明比正文宽', '读音核对 问题数 2'):
            if 分类(s) != '内容问题': f.append(f'误判：“{s}”是门在干活，不是不丝滑（K）')
        import contextlib, io
        登记0 = 登记[0]; 登记[0] = lambda x: 'K999'
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            记('定稿流水线', '28', 'ModuleNotFoundError: soundfile'); 记('交付核查', '28', '[T36] 破折号'); 记('推送两仓库', '-', '两仓库 视频/ 不一致（G2）')
        if buf.getvalue().count('已登记 K999') != 2: f.append('不丝滑没当场登记报坑（K56/G54）')
        if 次数('28') != 1 or 次数('28', '内容问题') != 1 or 次数('会话') != 1: f.append(f'计数不对（K）：28 不丝滑 {次数("28")}、内容 {次数("28", "内容问题")}、会话 {次数("会话")}')
        if 未闭环(): f.append(f'登记了还算没闭环（K56）：{未闭环()}')
        with contextlib.redirect_stdout(io.StringIO()):
            登记[0] = lambda x: 'K998'; 记('推送两仓库', '-', '两仓库 视频/ 不一致（G2）')
        if [r.get('K') for _, _, r in 全部() if r.get('入口') == '推送两仓库'] != ['K999', 'K999']: f.append('同入口同原因 24 小时内没沿用同一个 K#（K56：一个原因登记一次）')
        with contextlib.redirect_stdout(io.StringIO()):
            登记[0] = lambda x: ''; r_ = 记('定稿流水线', '28', 'Traceback 新毛病')
        if len(未闭环()) != 1: f.append('自动登记没成功的不丝滑没列进未闭环（K56）')
        if 对上('K997', r_['时刻']) != 1 or 未闭环(): f.append('--对上 没把那条对上 K#（K56）')
        登记[0] = 登记0
        if 会话次数(会话()) != 2 or 会话次数('别的会话') != 0: f.append(f'会话级不丝滑没按会话计（K57）：{会话次数(会话())}')
        with open(f'{d}/会话.jsonl', 'w') as fh:   # K57：四个改门会话，最后一个 3 次 > 前三个中位数 1；任务单没写进化落地必报，写了不报；不差不报
            for sid, n in (('s_aaaaaaa1', 0), ('s_aaaaaaa2', 1), ('s_aaaaaaa3', 2), ('s_aaaaaaa4', 3)):
                fh.write(json.dumps({'类': '开工', '角色': '改门', '会话': sid, '任务': f'{d}/任务.md'}) + '\n')
                for _ in range(n): fh.write(json.dumps({'类': '不丝滑', '会话': sid, 'K': 'K1'}) + '\n')
        open(f'{d}/任务.md', 'w').write('## 交接：会话 aaaaaaa4\n做了 x\n')
        if not 改门比较(d)[1]: f.append('没抓到：改门会话不丝滑比前三个中位数差、没写进化落地（K57）')
        open(f'{d}/任务.md', 'w').write('## 交接：会话 aaaaaaa4\n进化落地：K63\n')
        if 改门比较(d)[1]: f.append('误报：写了进化落地还报（K57）')
        open(f'{d}/任务.md', 'w').write('## 交接：会话 aaaaaaa3\n进化落地：K63\n')
        if not 改门比较(d)[1]: f.append('没抓到：别的会话的进化落地算到这个会话头上（K57）')
        for prog, anc in 接线.items():   # 五个正式入口都接上（拆掉任何一处必须发现）
            if anc not in open(f'{T}/{prog}').read(): f.append(f'没接上：{prog} 停下不记丝滑（K）')
    finally:
        目录[0] = old; shutil.rmtree(d, ignore_errors=True)
    d_ = tempfile.mkdtemp()
    try:   # K73：开工记录不算停下，不丝滑、内容问题、坏行都算
        open(f'{d_}/会话.jsonl', 'w').write(json.dumps({'类': '开工'}) + '\n' + json.dumps({'类': '不丝滑'}) + '\n')
        open(f'{d_}/25.jsonl', 'w').write(json.dumps({'类': '内容问题'}) + '\n坏行\n')
        if 停下数(d_) != 3: f.append(f'彩排停下数不对（K73：开工记录不算、不丝滑/内容问题/坏行都算，应 3 得 {停下数(d_)}）')
    finally: shutil.rmtree(d_, ignore_errors=True)
    return f


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--自检' in a:
        e = 自检(); print('丝滑记录 自检：' + ('通过（程序/环境/冲突/重读重跑算不丝滑，稿子内容问题不算；按篇计数）' if not e else '失灵！' + '；'.join(e))); sys.exit(1 if e else 0)
    if '--停下数' in a: print(停下数(a[a.index('--停下数') + 1] if len(a) > a.index('--停下数') + 1 else None)); sys.exit(0)
    if '--次数' in a: print(次数(a[a.index('--次数') + 1])); sys.exit(0)
    if '--改门比较' in a:
        l, e = 改门比较(); print(l + ('\n【停止】' + e if e else '')); sys.exit(1 if e else 0)
    if '--会话次数' in a: print(会话次数(a[a.index('--会话次数') + 1])); sys.exit(0)
    if '--对上' in a: i = a.index('--对上'); print(f'对上 {对上(a[i + 1], a[i + 2])} 条'); sys.exit(0)
    if '--未闭环' in a:
        u = 未闭环(); print('丝滑记录：' + (f'{len(u)} 条不丝滑没对上报坑登记号（K56）：' + '；'.join(f'{x[0]} {x[1]} {x[2][:50]}' for x in u[:5]) if u else '每条不丝滑都对上了报坑登记号'))
        sys.exit(1 if u and '--严' in a else 0)
    if a and a[0] == '记' and len(a) >= 4: 记(a[1], a[2], a[3], a[4] if len(a) > 4 else None); sys.exit(0)
    sys.exit(__doc__)
