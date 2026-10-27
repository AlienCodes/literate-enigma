#!/usr/bin/env python3
"""流程自检（规则执行机器当场跑）：
  G10 同一篇同时只能跑一条定稿流水线：占着锁再启动，必须停；
  画17/守则9 定稿流水线的步骤顺序固定：⓪ 规则执行核查 → ① 出片前核查 → ② 出 4K → ③ 出片后核查 → ④ 对照文本、文章同步 → ⑤ 归档 → ⑥ 推送；
  顺序被改乱必须报出（造一个调换了的样本）。"""
import os, sys, re, subprocess, tempfile, fcntl, shutil, json
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
# K37（25 定稿撞到）：定稿流水线 ④ 写 ${要文本:+--出文档}，bash 不认中文变量名直接 bad substitution，|| stop 又写在 # 注释后面，
# 生成文本.py 没跑、失败也不停，文本门从 2026-10-24 起被静默跳过。两道静态查（全部 .sh）+ 真跑 ④ 那两行（假 生成文本.py 失败必须停、参数对）
def sh毛病(txt):
    """[(行号, 毛病)]：中文变量展开（$名 / ${名…}，bash 只认 ASCII 变量名）；注释吞掉 || / &&（# 后面还有 || {、&& {、|| stop）"""
    out = []
    for i, l in enumerate(txt.splitlines(), 1):
        if l.lstrip().startswith('#'): continue
        code = re.sub(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"", lambda m: m.group(0) if '$' in m.group(0) else '""', l)
        m = re.search(r'(?:^|\s);?#(?![!{])', code)
        if re.search(r'\$\{?[#!]?[^\x00-\x7F]', code[:m.start()] if m else code): out.append((i, '中文变量展开（bash 只认 ASCII 变量名：${名} 是 bad substitution，$名 是字面量）'))
        if m and re.search(r'(\|\||&&)\s*(\{|stop\b|exit\b)', code[m.end():]): out.append((i, '注释吞掉了后面的 || / &&（失败不停）'))
    return out
for _f in sorted(__import__('glob').glob(f'{T}/**/*.sh', recursive=True)):
    if '演练样本' in _f: continue
    for _i, _m in sh毛病(open(_f).read()): fails.append(f'{os.path.relpath(_f, T)} 第 {_i} 行：{_m}（K37）')
for _bad in ('python3 x.py ${要文本:+--出文档} > a 2>&1', 'python3 x.py $([ -z "$要文本" ] && echo y)', 'python3 x.py > a 2>&1   # 注释 || { tail a; stop "x"; }'):
    if not sh毛病(_bad): fails.append(f'没抓到：{_bad}（K37 重放）')
for _ok in ('echo "第${no}篇"', 'exec 9>"${PUSH_LOCK:-/tmp/推送两仓库.lock}"; flock 9', 'x=1   # 说明：失败就 || 停'):
    if sh毛病(_ok): fails.append(f'误报：{_ok} 被当成 K37 毛病')
def 跑文本门(要文本, 退出码, txt=src):
    """把 定稿流水线 ④ 生成文本那两行（YAOWENBEN= 和 python3 $T/生成文本.py）拿出来真跑：假 生成文本.py 记下参数、按 退出码 退出"""
    ls_ = [l for l in txt.splitlines() if not l.lstrip().startswith('#') and ('生成文本.py' in l or l.startswith('YAOWENBEN='))]
    d = tempfile.mkdtemp(); open(f'{d}/生成文本.py', 'w').write(f'import sys; open(sys.argv[0] + ".参数", "w").write(" ".join(sys.argv[1:])); sys.exit({退出码})\n')
    sh = f'stop() {{ echo 【停止】$1; exit 1; }}\nno=99; T={d}; LOG={d}\n' + '\n'.join(ls_) + '\necho 走过了\n'
    env = {k: v for k, v in os.environ.items() if k not in ('要文本', 'YAOWENBEN')}
    if 要文本: env['要文本'] = '1'
    r = subprocess.run(['bash', '-c', sh], capture_output=True, text=True, env=env, timeout=30)
    a = open(f'{d}/生成文本.py.参数').read() if os.path.exists(f'{d}/生成文本.py.参数') else None; shutil.rmtree(d, ignore_errors=True)
    return a, '【停止】' in r.stdout and '走过了' not in r.stdout, r.stderr.strip()
_a, _st, _e = 跑文本门(False, 1)
if _a is None: fails.append(f'定稿流水线 ④ 生成文本.py 根本没跑（K37）：{_e[:120]}')
elif not _st: fails.append('定稿流水线 ④ 生成文本.py 失败了流水线没停（K37：|| stop 被注释吞掉？）')
elif '--只核查' not in _a.split(): fails.append(f'定稿流水线 ④ 默认没带 --只核查（守则17）：参数“{_a}”')
_a, _st, _e = 跑文本门(True, 0)
if _a is None or '--出文档' not in _a.split() or _st: fails.append(f'定稿流水线 ④ env 要文本=1 没出文档或不该停：参数“{_a}”{_e[:80]}')
# G79（门变异演练找出来的）：.sh 里每一道门都要真能停。把每一行有 stop/exit 非0 的代码单独拿出来真跑：外部命令一律失败（PATH 指向空目录，
# command_not_found_handle 返回 1）、变量分别取空和 "1" 两种，任一种必须停在这一行（退出码非 0、走不到这一行后面）。
# 拆掉的门（stop 前加 :、写进注释、|| true、exit 1 被吃掉）两种都走过去 = 死门。演练只跑到 ⓪，① 以后的门以前没有任何东西查。
def sh门真跑(txt):
    import 门变异 as _MB
    out = []
    for i, col, l, dead in _MB.门_sh(txt):
        ls_ = txt.splitlines(); a = b = i - 1   # 整条逻辑行：续行 \\、下一行以 && || | 开头的连上
        while a > 0 and (ls_[a - 1].rstrip().endswith('\\') or re.match(r'\s*(&&|\|\|?)', ls_[a])): a -= 1
        while b + 1 < len(ls_) and (ls_[b].rstrip().endswith('\\') or re.match(r'\s*(&&|\|\|?)', ls_[b + 1])): b += 1
        line = re.sub(r';?\s*\b(fi|done|esac)\s*$', '', '\n'.join(ls_[a:b + 1]))
        if subprocess.run(['/bin/bash', '-n', '-c', line], capture_output=True).returncode:
            out.append((i, '单独拿出来语法不对，真跑不了：' + ls_[i - 1].strip()[:50])); continue
        vs = sorted(set(re.findall(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)', line)) - {'T', 'P', 'L', 'W', 'LOG', 'no', 'BR'})
        ok = False
        for v in ('', '1'):
            d = tempfile.mkdtemp(); e = ''.join(f'export {x}={v!r}\n' if v else f'unset {x}\n' for x in vs)
            sh = (f'set -o pipefail\nstop() {{ echo 【停止】; exit 1; }}\nstep() {{ :; }}\npush() {{ return 1; }}\ncd() {{ return 1; }}\ncommand_not_found_handle() {{ return 1; }}\n'
                  f'no=99; T={d}; P={d}; L={d}; W={d}; LOG={d}; BR=x\n{e}PATH={d}/空\n{line}\necho 走过了\n')
            try: r = subprocess.run(['/bin/bash', '-c', sh], capture_output=True, text=True, timeout=20, cwd=d)
            except subprocess.TimeoutExpired: r = None
            shutil.rmtree(d, ignore_errors=True)
            if r is not None and r.returncode != 0 and '走过了' not in r.stdout: ok = True; break
        if not ok: out.append((i, line.strip()[:70]))
    return out
for _f in sorted(__import__('glob').glob(f'{T}/**/*.sh', recursive=True)) + [f'{T}/githooks/pre-commit']:   # H：提交前钩子也真跑
    if '演练样本' in _f: continue
    for _i, _m in sh门真跑(open(_f).read()): fails.append(f'{os.path.relpath(_f, T)} 第 {_i} 行的门真跑停不下来（G79 死门）：{_m}')
for _bad in ('x || : stop "拆了"', 'a \\\n  && b || { echo x; : exit 1; }', 'if x; then\n  y || { echo x; : exit 1; }; fi', 'x || true   # || stop "注释吞了"', 'flock -n 9 || { echo "【停止】已经在跑"; : exit 1; }', '[ -n "$Z" ] && : stop "拆了"'):
    if not sh门真跑(_bad): fails.append(f'没抓到：拆掉的门 {_bad}（G79 门变异重放）')
for _ok in ('x || stop "好门"', '[ -n "$Z" ] && stop "好门"', 'flock -n 9 || { echo "【停止】"; exit 1; }', 'md=$(ls a 2>/dev/null | head -1); [ -n "$md" ] || stop "好门"'):
    if sh门真跑(_ok): fails.append(f'误报：好门 {_ok} 被当成死门（G79）')
# K38：钩子自检必须在隔离的请求账里跑：HOME 里放一份“推了请求、没约唤醒”的真实账，钩子自检照样要通过
_h = tempfile.mkdtemp(prefix='K38_HOME_'); json.dump({'请求': [{'名字': '演练', '时刻': '2099-01-01T00:00:00Z'}]}, open(f'{_h}/.云端请求.json', 'w'))
_r = subprocess.run(['python3', f'{T}/钩子/钩子自检.py'], capture_output=True, text=True, env={**{k: v for k, v in os.environ.items() if not k.startswith('GIT_')}, 'HOME': _h})
if _r.returncode: fails.append('钩子自检读了真实的 ~/.云端请求.json（K38 重放：推了请求没约唤醒时自检报失灵）：' + (_r.stdout + _r.stderr).strip()[-120:])
shutil.rmtree(_h, ignore_errors=True)
# K31：GitHub 工作流 run 里的 shell 也不许用中文变量名（export 正例=… 是 not a valid identifier，第一轮 48 个任务全挂）
def yml中文变量(txt): return [i for i, l in enumerate(txt.splitlines(), 1) if re.search(r'(?:^|[\s;])export\s+[^\x00-\x7F]|\$\{?[^\x00-\x7F\s{(]', l)]
for _f in [x for d in (os.path.dirname(os.path.dirname(T)), '/home/user/literate-enigma') for x in __import__('glob').glob(f'{d}/.github/workflows/*.yml')]:
    for _i in yml中文变量(open(_f).read()): fails.append(f'{_f} 第 {_i} 行：工作流 shell 用了中文变量名（K31）')
if not yml中文变量('        run: export 正例=/tmp/正例') or not yml中文变量('  run: echo ${正例}') or yml中文变量('  run: echo ${{ matrix.it.no }} $N ${N#覆盖@}'): fails.append('K31 自检：工作流中文变量名没抓到或误报')
def drill写回(txt):   # K41：几十个分片同时写回，put() 遇 409 不重试就丢结果；artifact 名字带 /（githooks/pre-commit）上传报错
    e = []
    if 'put() {' in txt:
        p = txt[txt.index('put() {'):]; p = p[:p.find('\n          PY\n') if '\n          PY\n' in p else len(p)]
        if not ('409' in p and 'for ' in p and 'sleep' in p): e.append('写回 put() 遇 409 不重试（K41）')
    if re.search(r"name: '结果_\$\{\{ matrix\.it\.req \}\}_\$\{\{ matrix\.it\.no \}\}'", txt): e.append('artifact 名字直接用 matrix.it.no（带 / 就上传失败，K41）')
    return e
for _f in __import__('glob').glob('/home/user/literate-enigma/.github/workflows/drill.yml'):
    fails += [f'drill.yml：{x}' for x in drill写回(open(_f).read())]
_k41 = "          put() { python3 - <<'PY'\n          r=subprocess.run(['gh','api','-X','PUT'])\n          PY\n        with: {name: '结果_${{ matrix.it.req }}_${{ matrix.it.no }}', path: x}\n"
if len(drill写回(_k41)) != 2: fails.append(f'没抓到：drill.yml 写回不重试、artifact 名字带 /（K41 重放）：{drill写回(_k41)}')
# G79 门变异：执行效应演练 开跑前两道门（不在视频工作目录、工作目录的出片程序是旧的）拆了没人发现：真跑，必须停在对的话上
_ew = tempfile.mkdtemp(prefix='演练门_')
_r = subprocess.run(['python3', f'{T}/执行效应演练.py'], cwd=_ew, capture_output=True, text=True)
if '请在视频工作目录' not in _r.stdout + _r.stderr: fails.append('执行效应演练 不在视频工作目录也开跑了（G79 门变异）：' + (_r.stdout + _r.stderr).strip()[-80:])
os.makedirs(f'{_ew}/scripts'); open(f'{_ew}/make_video.py', 'w').write('# 旧\n')
_r = subprocess.run(['python3', f'{T}/执行效应演练.py'], cwd=_ew, capture_output=True, text=True)
if '出片指纹.py --拷' not in _r.stdout + _r.stderr: fails.append('执行效应演练 工作目录的出片程序是旧的也开跑了（G27/G79 门变异）：' + (_r.stdout + _r.stderr).strip()[-80:])
shutil.rmtree(_ew, ignore_errors=True)
# G79 门变异：会话开工 角色乱写要打印用法停下；证据.py --记 不是正式入口调用必停（G60）
_r = subprocess.run(['python3', f'{T}/会话开工.py', '乱写'], capture_output=True, text=True, env={**os.environ, 'HOME': tempfile.mkdtemp(prefix='开工门_')})
if _r.returncode == 0 or '会话开工（G61' not in _r.stdout + _r.stderr: fails.append('会话开工.py 角色乱写没打印用法停下（G79 门变异）')
_r = subprocess.run(['python3', f'{T}/证据.py', '--记', '99', '出片前'], capture_output=True, text=True)
if _r.returncode == 0 or '只能由正式入口' not in _r.stdout + _r.stderr: fails.append('证据.py --记 手写证据没停（G60/G79 门变异）')
_r = subprocess.run(['python3', f'{T}/交付核查.py', '03', '对照表'], capture_output=True, text=True)   # 03 已有踩坑对照记录：必须不覆盖、停下（G79 门变异）
if _r.returncode == 0 or '不覆盖' not in _r.stdout + _r.stderr: fails.append('交付核查 对照表 把已有的踩坑对照记录又追加了一份（G79 门变异）')
def 有重建(txt):   # K36：新容器没有 work_NN/a.wav，① 音频体检 ffmpeg 254 崩；① 之前没有 a.wav 必须先只出声音重建
    i = txt.find('[ -f "work_$no/a.wav" ] ||'); j = txt.find('step "① 出片前核查')
    return 0 <= i < j and 'AUDIO_ONLY=1 python3 make_' in txt[i:j]   # 只出声音重建
if not 有重建(src): fails.append('定稿流水线 ① 之前没有“没有 work_NN/a.wav 就只出声音重建”（K36）')
if 有重建(src.replace('[ -f "work_$no/a.wav" ] ||', '')): fails.append('没抓到：拿掉 a.wav 重建那一行（K36 重放）')
if subprocess.run(['python3', f'{T}/推请求.py', '--自检'], capture_output=True).returncode: fails.append('推请求.py --自检 不过（K35）')
_旧 = 'python3 $T/生成文本.py $no ${要文本:+--出文档} $([ -z "$要文本" ] && echo --只核查) > "$LOG/文本.log" 2>&1   # 守则17 || { tail -15 "$LOG/文本.log"; stop "对照文本生成或文本核查不通过"; }'
_a, _st, _e = 跑文本门(False, 1, _旧)
if _a is not None and _st: fails.append('没抓到：K37 原样那一行（中文变量 + 注释吞 ||）重放，真跑没发现文本门没跑、不停')
td = tempfile.mkdtemp(); lk = open(f'{td}/.定稿流水线_99.lock', 'w'); fcntl.flock(lk, fcntl.LOCK_EX)
r = subprocess.run(['bash', f'{T}/定稿流水线.sh', '99'], capture_output=True, text=True, cwd=td, timeout=60)
if r.returncode == 0 or '已经有一条定稿流水线在跑' not in r.stdout + r.stderr: fails.append('没抓到：同一篇同时跑两条定稿流水线（G10）')
lk.close(); shutil.rmtree(td, ignore_errors=True)
# 24 草稿会话报的三个共用程序问题（2026-10-24）
sys.path.insert(0, T); import 开工记录 as _KG   # G23 开工记录.py 已有的 NN.md 只追加、不覆盖
_o = _KG.合成('# 第99篇制作记录\n\n## 方法设计\n- 交接：主对话写的方法设计\n', '99', ['| A1 | x | 涉及 | y |'], 'T')
if '交接：主对话写的方法设计' not in _o or '| A1 |' not in _o or _o.count('## 方法设计') != 1: fails.append('没抓到：开工记录.py 覆盖了已有的 制作记录/NN.md、方法设计被清空（G23）')
import 区间作废 as _QJ; fails += _QJ.自检()       # A45 改了读音/语速，旧区间、旧确认自动作废（出片程序那一半在 出片守门自检.py 的 A45）
if 'OLD_IV_VOID=1' not in open(f'{T}/草稿声音.sh').read() or '区间作废.py $no --记指纹' not in open(f'{T}/草稿声音.sh').read(): fails.append('没抓到：草稿声音.sh 没接上 区间作废（A45）')
sys.path.insert(0, f'{T}/初稿生成'); import 核对 as _HD   # T37 核对.py 多词重点词误报“缺”
if _HD.缺的重点词(['**hinge on**', '**dead reckoning**'], ['hinge on', 'dead reckoning']): fails.append('T37 误报：多词重点词（hinge on、dead reckoning）整体在却报“缺”')
if _HD.缺的重点词(['**dead reckoning**'], ['dead', 'reckoning']): fails.append('T37 误报：多词重点词每个词都加粗了却报“缺”')
if _HD.缺的重点词(['**vast**', '**hinge on**'], ['hinge on']) != ['vast']: fails.append('没抓到：文章重点词在对照里真的缺了（T37）')
def 管道解压(txt):   # K54：curl 下载直接管道给 tar 解压，下载被截断就留半截文件、重跑跳过下载；必须先下到文件、解压成功才算
    return [l.strip()[:80] for l in txt.splitlines() if not l.lstrip().startswith('#') and re.search(r'curl\b[^|#]*\|\s*tar\b', l)]
if 管道解压(open(f'{T}/环境/准备机器.sh').read()): fails.append(f'准备机器.sh 又用 curl 管道直接 tar 解压（K54）：{管道解压(open(f"{T}/环境/准备机器.sh").read())[0]}')
if not 管道解压('A=1; [ -f x ] || { curl -sSL https://e/x.tar.bz2 | tar xj -C ~/asr; }\n'): fails.append('没抓到：curl | tar 管道解压（K54 重放）')
print('流程自检：' + ('通过（占着锁再启动定稿流水线必停；步骤顺序被调换必报；④ 文本门真跑失败必停、.sh 中文变量和注释吞 || 必报（K37）；① 前没有 a.wav 先重建（K36）；本地慢印章过期不许推主演练补丁（K35）；全部 .sh 每道门真跑能停（G79 门变异）；钩子自检不读真实请求账（K38）；工作流不用中文变量名（K31））' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
