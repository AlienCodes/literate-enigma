#!/usr/bin/env python3
"""流程自检（规则执行机器当场跑）：
  G10 同一篇同时只能跑一条定稿流水线：占着锁再启动，必须停；
  画17/守则9 定稿流水线的步骤顺序固定：⓪ 规则执行核查 → ① 出片前核查 → ② 出 4K → ③ 出片后核查 → ④ 对照文本、文章同步 → ⑤ 归档 → ⑥ 推送；
  顺序被改乱必须报出（造一个调换了的样本）。"""
import os, sys, re, subprocess, tempfile, fcntl, shutil
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T); fails = []
ORDER = ['⓪ 规则执行核查', '① 出片前核查', '② 出 4K', '③ 出片后核查', '④ 对照文本', '⑤ 归档', '⑥ 存记录、推送']
def 顺序(txt):
    pos = [txt.find(f'step "{s}') for s in ORDER]
    return [] if all(p >= 0 for p in pos) and pos == sorted(pos) else [f'定稿流水线步骤缺了或顺序乱了：{[s for s, p in zip(ORDER, pos) if p < 0] or "顺序不对"}']
src = open(f'{T}/定稿流水线.sh').read()
if 顺序(src): fails.append('原样就报：' + 顺序(src)[0])
sw = src.replace('step "② 出 4K', 'step "TMP').replace('step "③ 出片后核查', 'step "② 出 4K').replace('step "TMP', 'step "③ 出片后核查')
if not 顺序(sw): fails.append('没抓到：定稿流水线步骤顺序乱了（画17）')
def 推送锁(txt):   # G17：⑥ 的提交、镜像同步、推送要占 推送两仓库 的锁
    ls = txt.splitlines(); i = [k for k, l in enumerate(ls) if '镜像同步.py' in l and not l.lstrip().startswith('#')]
    j = [k for k, l in enumerate(ls) if re.match(r'exec 7>.*推送两仓库\.lock.*; flock 7', l)]
    u = [k for k, l in enumerate(ls) if l.strip() == 'flock -u 7']
    return [] if i and j and u and j[0] < i[0] < u[0] else ['⑥ 镜像同步没在推送锁里（G17）']
if 推送锁(src): fails.append('原样就报：' + 推送锁(src)[0])
if not 推送锁(re.sub(r'(?m)^exec 7>.*\n', '', src)): fails.append('没抓到：⑥ 不占推送锁（G17）')
import 工作稿核对 as _G; _d = tempfile.mkdtemp(); _w, _p = f'{_d}/w.json', f'{_d}/p.json'   # G19：工作稿比仓库旧必停
open(_w, 'w').write('旧'); open(_p, 'w').write('新'); os.utime(_w, (1, 1))
if not _G.旧了(_w, _p): fails.append('没抓到：工作目录脚本比仓库旧（G19）')
open(_p, 'w').write('旧')
if _G.旧了(_w, _p): fails.append('误报：工作稿与仓库一致（G19）')
shutil.rmtree(_d, ignore_errors=True)
import importlib.util as _iu   # 铁4：改了出片程序没全篇重查，必须算“欠着”
_s = _iu.spec_from_file_location('_qp', f'{T}/全篇核查.py'); _d = tempfile.mkdtemp(); _st = f'{_d}/s.json'
_src = open(f'{T}/全篇核查.py').read(); _ns = {'__file__': f'{T}/全篇核查.py', '__name__': '_qp'}
exec(compile(_src.split("if sys.argv[1:2] == ['--欠着']")[0], '全篇核查', 'exec'), _ns)
import json as _j; _j.dump({'篇': {'01': 'x-1-1'}}, open(_st, 'w'))
if not _ns['欠着'](_st, {'01': 'y-1-1'}): fails.append('没抓到：改了出片程序没全篇重查（铁4）')
if _ns['欠着'](_st, {'01': 'x-1-1'}): fails.append('误报：全篇重查指纹一致却算欠着（铁4）')
if _ns['欠着'](_st, {'01': 'x-1-1', '02': 'x-2-2'}) != ['02']: fails.append('没抓到：新出片的篇目没重查（铁4）')
shutil.rmtree(_d, ignore_errors=True)
import 补对照记录 as _B; _d = tempfile.mkdtemp(); _r = f'{_d}/99.md'   # 补对照记录：程序把关的坑自动补，只有人能判的（T7、G6……）不许补
open(_r, 'w').write('# x\n## 踩坑对照记录\n| 编号 | 坑 | 涉及 | 做法 |\n| A1 | x | 涉及 | y |\n'); _B.补('99', _r); _x = open(_r).read()
if '| A2 |' not in _x: fails.append('没抓到：程序把关的新坑没自动补进对照记录')
if '| T7 |' in _x or '| G6 |' in _x: fails.append('误补：只有人能判的坑（T7/G6）被自动补成“程序把关”')
shutil.rmtree(_d, ignore_errors=True)
import 重查记录 as _RC   # G22：已定稿的篇目欠重出，踩坑核查当场提醒
if not _RC.定稿提醒('21', {'21': 'x.mp4'}, ['21']): fails.append('没抓到：改了已定稿篇目的脚本没提醒重出 4K（G22）')
if _RC.定稿提醒('23', {'21': 'x.mp4'}, ['21']) or _RC.定稿提醒('21', {'21': 'x.mp4'}, []): fails.append('误报：没定稿或已重查过的篇目也提醒（G22）')
_l = [l for l in src.splitlines() if '生成文本.py' in l and not l.lstrip().startswith('#')]   # 守则17：默认不出 Word/PDF
if not _l or '--只核查' not in _l[0] or '要文本' not in _l[0]: fails.append('没抓到：定稿流水线默认还在出 Word/PDF（守则17）')
if '只核查 = ' not in open(f'{T}/生成文本.py').read(): fails.append('没抓到：生成文本没有只核查用法（守则17）')
td = tempfile.mkdtemp(); lk = open(f'{td}/.定稿流水线_99.lock', 'w'); fcntl.flock(lk, fcntl.LOCK_EX)
r = subprocess.run(['bash', f'{T}/定稿流水线.sh', '99'], capture_output=True, text=True, cwd=td, timeout=60)
if r.returncode == 0 or '已经有一条定稿流水线在跑' not in r.stdout + r.stderr: fails.append('没抓到：同一篇同时跑两条定稿流水线（G10）')
lk.close(); shutil.rmtree(td, ignore_errors=True)
print('流程自检：' + ('通过（占着锁再启动定稿流水线必停；步骤顺序被调换必报）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
