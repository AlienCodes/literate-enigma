#!/usr/bin/env python3
"""快测：改规则、改程序后唯一要过的门（替代 门变异 / 执行效应演练 / 声音演练 / 彩排 的拦人作用）。本地并行，目标 ≤5 分钟。
  ① 规则表是最新的（从现有表重新生成，版本一致）；没搬的规则 0 条或有说明
  ② 每条搬进新管的规则：它的坏样本必须抓到、好样本必须放过 = 跑它的自检程序（现有 --自检，就是造坏样本、放好样本）
     文本/画面/流程类：FAST 快自检（与 规则执行核查 当场自检同一张清单）；声音类：在工作目录用 27 跑各声音核查的 --自检
  ③ 挂钩检查（A26/A42）：核查程序挂钩的出片程序原文还在
  ④ 27 回归：缓存重建，a.wav、分段.json 逐字节同基准；每一屏重画，像素哈希同基准
用法：python3 新管/快测.py [--只文本] [--记基准]
环境：XG_TOOLS=检查程序目录（默认 视频/工具）  XG_WORK=出片工作目录（默认 准备机器.sh 搭的 <scratchpad>/video）"""
import sys, os, json, subprocess, hashlib, time, glob
from concurrent.futures import ThreadPoolExecutor
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
T = os.environ.get('XG_TOOLS') or (R if os.path.exists(f'{R}/交付核查.py') else f'{R}/视频/工具'); W = os.environ.get('XG_WORK', '')
NO = os.environ.get('XG_NO', '27'); 基准 = f'{H}/回归基准_{NO}.json'
sys.path.insert(0, T)
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
env0 = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}

def 跑(cmd, cwd, t=900):
    t0 = time.time()
    try: r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env0, timeout=t)
    except subprocess.TimeoutExpired: return 1, f'超时 {t}s', time.time() - t0
    return r.returncode, (r.stdout + r.stderr).strip(), time.time() - t0

def 看门程序():
    import importlib.util
    s = importlib.util.spec_from_file_location('生成规则表', f'{H}/生成规则表.py'); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m, set(m.阶段表['看门'])

def 规则表新鲜():
    m, _ = 看门程序(); 表 = json.load(open(f'{H}/规则表.json'))
    r = subprocess.run(['python3', f'{H}/生成规则表.py'], capture_output=True, text=True, env={**env0, 'XG_TOOLS': T})
    bad = [l for l in r.stdout.splitlines() if l.strip().startswith('没搬')]
    tmp = f'{H}/.规则表.新'; subprocess.run(['python3', f'{H}/生成规则表.py', '--写入', '--到', tmp], capture_output=True, env={**env0, 'XG_TOOLS': T})
    新 = json.load(open(tmp)) if os.path.exists(tmp) else {}; os.path.exists(tmp) and os.remove(tmp)
    if 新.get('版本') != 表.get('版本'): bad.append(f'规则表.json 不是最新的（{表.get("版本")} → {新.get("版本")}）：python3 新管/生成规则表.py --写入')
    return bad, 表

停跑 = {'门变异.py', '用上核查.py', '证据.py', '丝滑.py', '演练镜像.py', '执行效应声音演练.py', '推请求.py', '会话开工.py', '方法进化表.py'}

def 文本自检(看门):
    import 规则执行核查 as RZ
    cmds = [c for c in RZ.FAST if c[0] not in 停跑]   # 只停真正退役的看门程序；放行口子核查、开工必读 的自检仍是 G24/G55 的坏样本
    with ThreadPoolExecutor(8) as ex:
        rs = list(ex.map(lambda c: (c, 跑(['python3', f'{T}/{c[0]}', *c[1:]], T, 300)), cmds))
    return [f'自检不通过：{" ".join(c)} → {o.splitlines()[-1][:160] if o else "无输出"}' for c, (rc, o, _) in rs if rc], len(cmds)

def 声音():
    """交付核查 出片前 / 出片后（看门停用后只剩真检查，内含每个声音核查的 --自检、数字读法自检、独立复核造 5 处瑕疵、高亮自检）
    + 出片守门自检（出片程序每道守门造错必停），三个并行。回归篇只出了声音时，只放过 G12 那一行实查（它的自检照样要过）"""
    import shutil
    if not os.path.exists(f'{W}/{NO}.mp4'):   # 回归篇还没出过片：先只出声音（出片后核查要 NN.mp4）
        subprocess.run(['python3', 'make_video.py', f'scripts/{NO}.json', f'{NO}.mp4'], capture_output=True, cwd=W, env={**env0, 'AUDIO_ONLY': '1'})
    cmds = [['交付核查.py', NO, '出片前'], ['交付核查.py', NO, '出片后'], ['出片守门自检.py']]
    with ThreadPoolExecutor(3) as ex:
        rs = list(ex.map(lambda c: (c, 跑(['python3', f'{T}/{c[0]}', *c[1:]], W, 1800)), cmds))
    bad = []
    for c, (rc, o, dt) in rs:
        x = [l for l in o.splitlines() if l.startswith('✘') and not l.startswith('✘ 成片有画面（G12')]
        if rc and not x and '成片有画面（G12' not in o: x = [o.splitlines()[-1] if o else '无输出']
        bad += [f'{" ".join(c)}（{dt:.0f}s）：{l[:150]}' for l in x]
    return bad, len(cmds)

def 覆盖(表, 看门):
    """每条搬进新管的规则，至少一个自检程序会被快测跑到（坏样本必抓）"""
    import 规则执行核查 as RZ, re
    跑到 = {c[0] for c in RZ.FAST if c[0] not in 停跑} | {'交付核查.py', '出片守门自检.py'}
    src = open(f'{T}/交付核查.py').read(); 跑到 |= set(re.findall(r"f'\{T\}/([^']+?\.py)'", src))
    定稿时 = {'定稿视频核对.py'}
    没 = [e['编号'] for e in 表 if e['状态'].startswith('搬') and e['自检'] and not ({x[0] for x in e['自检']} & (跑到 | 定稿时 | {'规则执行核查.py'}))]
    return 没

def 常规规则():
    """新管改成常规的规则（用户已说过“以后都这样”的）：坏样本必抓、好样本必放。
    G35：25 起结尾简述没写特批也整屏；24 不给；中间句不给"""
    import copy, glob
    if not open(f'{T}/render.py').read().count('G35 常规规则'): return ['G35 常规规则：render.py 没打补丁（python3 新管/切换.py <工具>）']
    r = subprocess.run(['python3', '-c', '''
import sys, json, copy, glob; sys.path.insert(0, sys.argv[1]); import render as R
V = sys.argv[2]; d27 = json.load(open(f"{V}/脚本/27.json")); d27["no"] = "27"; d24 = json.load(open(f"{V}/脚本/24.json")); d24["no"] = "24"
key = lambda d, i: " ".join(p[0] for c in d["sentences"][i]["chunks"] for p in c["align"])
bad = []
a = copy.deepcopy(d27); a.pop("说明放宽特批", None); R.apply_script(a)
if R.NOTE_WIDE.get(key(a, -1)) != "整屏": bad.append("没抓到：27 去掉特批后结尾简述不整屏")
R.apply_script(d24)
if R.NOTE_WIDE.get(key(d24, -1)) == "整屏": bad.append("误放：24（25 前）没特批也整屏了")
b = copy.deepcopy(d27); b.pop("说明放宽特批", None); b["sentences"][-1]["chunks"][-1]["note"] = "（结局：x）"; R.apply_script(b)
if R.NOTE_WIDE.get(key(b, -1)) == "整屏": bad.append("误放：最后一句不是简述也整屏了")
print("\\n".join(bad))''', T, os.path.dirname(T)], capture_output=True, text=True, cwd=T, env=env0)
    return [f'G35 常规规则：{x}' for x in (r.stdout.strip().splitlines() if r.returncode == 0 else [r.stderr.strip()[-200:]])]

def 挂钩():
    import 规则执行核查 as RZ
    return [f'挂钩：{x}' for x in RZ.挂钩检查(RZ.程序表())]

def 回归(记):
    """缓存重建回归篇：只出声音（AUDIO_ONLY，与正式出片同一套程序），比 a.wav、分段.json；每屏重画比像素哈希"""
    e = {**env0, 'AUDIO_ONLY': '1'}; RW = W.rstrip('/') + '_回归'   # 独立副本（共用 ../tts 缓存），不和交付核查抢 work_NN/a.wav
    import shutil; shutil.rmtree(RW, ignore_errors=True)
    shutil.copytree(W, RW, ignore=lambda d, fs: [f for f in fs if d == W and (f.startswith('work_') or f.endswith(('.mp4', '.mp3')))])
    r = subprocess.run(['python3', 'make_video.py', f'scripts/{NO}.json', f'_回归{NO}.mp4'], capture_output=True, text=True, cwd=RW, env=e)
    if r.returncode: return [f'回归：重建失败 {(r.stdout + r.stderr).strip()[-200:]}'], {}
    cur = {'a.wav': md5(f'{RW}/work_{NO}/a.wav'), '分段.json': md5(f'{RW}/work_{NO}/分段.json')}
    r = subprocess.run(['python3', f'{H}/画面哈希.py', NO], capture_output=True, text=True, cwd=RW, env={**env0, 'XG_TOOLS': T})
    if r.returncode: return [f'回归：画面重画失败 {(r.stdout + r.stderr).strip()[-200:]}'], cur
    cur['画面'] = json.loads(r.stdout.strip().splitlines()[-1])
    if 记:
        json.dump(cur, open(基准, 'w'), ensure_ascii=False, indent=0); return [], cur
    if not os.path.exists(基准): return [f'回归：没有基准 {基准}（先 --记基准，基准必须是旧管出的定稿状态）'], cur
    b = json.load(open(基准)); bad = []
    for k in ('a.wav', '分段.json'):
        if cur[k] != b[k]: bad.append(f'回归：{k} 与基准不同（{b[k][:8]} → {cur[k][:8]}）')
    if cur['画面'] != b['画面']:
        bad.append(f'回归：画面与基准不同：{[i for i, (x, y) in enumerate(zip(cur["画面"], b["画面"])) if x != y][:8]}，屏数 {len(b["画面"])}→{len(cur["画面"])}')
    return bad, cur

def main():
    t0 = time.time(); a = sys.argv[1:]; out = []
    bad, 表 = 规则表新鲜(); _, 看门 = 看门程序()
    规 = 表['规则']; 搬 = sum(1 for e in 规 if e['状态'].startswith('搬')); 替 = sum(1 for e in 规 if e['状态'] == '替代')
    out.append(f'① 规则表 {len(规)} 条：搬 {搬}、替代 {替}、没搬 {len(规) - 搬 - 替 - sum(1 for e in 规 if e["状态"].startswith("无门"))}；版本 {表["版本"]}')
    没 = 覆盖(规, 看门); bad += [f'规则的坏样本没人跑：{"、".join(没)}'] if 没 else []
    out.append(f'①b 坏样本覆盖：{len(规) - len(没)} / {len(规)}' + ('' if not 没 else f'，没覆盖 {没[:10]}'))
    全 = '--只文本' not in a
    if 全 and (not W or not os.path.exists(f'{W}/make_video.py')): bad.append('没有出片工作目录（XG_WORK=…/video）：先 bash 视频/工具/环境/准备机器.sh'); 全 = False
    with ThreadPoolExecutor(3) as ex:   # 三路并行：文本快自检、回归、声音（交付核查 + 守门自检）
        ft = ex.submit(文本自检, 看门); fr = ex.submit(回归, '--记基准' in a) if 全 else None; fs = ex.submit(声音) if 全 else None
        b, n = ft.result(); bad += b; out.append(f'② 文本/画面/流程 快自检 {n} 个程序：{"全过" if not b else f"{len(b)} 个不过"}')
        b = 挂钩(); bad += b; out.append(f'③ 挂钩检查：{"在" if not b else "断了"}')
        b = 常规规则(); bad += b; out.append(f'③b 常规规则（G35 简述整屏）坏样本必抓、好样本必放：{"过" if not b else "不过"}')
        if 全:
            b, _ = fr.result(); bad += b; out.append(f'④ {NO} 回归：{"记了基准" if "--记基准" in a else ("a.wav、分段.json 逐字节、每屏像素一致" if not b else "不一致")}')
            b, n = fs.result(); bad += b; out.append(f'⑤ 交付核查 出片前/出片后 + 出片守门自检：{"全过" if not b else f"{len(b)} 处不过"}')
    if not bad and '--只文本' not in a and '--记基准' not in a:
        subprocess.run(['python3', f'{H}/印章.py', '--盖'], env={**env0, 'XG_TOOLS': T}, capture_output=True); out.append('已盖快测印章（程序或规则表再改要重跑）')
    print('\n'.join(out + [f'  ✘ {x}' for x in bad] + [f'快测{"通过" if not bad else "不通过"}，用时 {time.time() - t0:.0f} 秒']))
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
