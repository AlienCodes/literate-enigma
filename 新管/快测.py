#!/usr/bin/env python3
"""快测：改规则、改程序后唯一要过的门（替代 门变异 / 执行效应演练 / 声音演练 / 彩排 的拦人作用）。本地并行，目标 ≤5 分钟。
  ① 规则表是最新的（从现有表重新生成，版本一致）；没搬的规则 0 条或有说明
  ② 每条搬进新管的规则：它的坏样本必须抓到、好样本必须放过 = 跑它的自检程序（现有 --自检，就是造坏样本、放好样本）
     文本/画面/流程类：FAST 快自检（与 规则执行核查 当场自检同一张清单）；声音类：在工作目录用 27 跑各声音核查的 --自检
  ③ 挂钩检查（A26/A42）：核查程序挂钩的出片程序原文还在
  ④ 27 回归：缓存重建，a.wav、分段.json 逐字节同基准；每一屏重画，像素哈希同基准
用法：python3 新管/快测.py [--只文本] [--记基准]
环境：旧工具=检查程序目录（默认 视频/工具）  工作目录=出片工作目录（默认 准备机器.sh 搭的 <scratchpad>/video）"""
import sys, os, json, subprocess, hashlib, time, glob
from concurrent.futures import ThreadPoolExecutor
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
T = os.environ.get('旧工具', f'{R}/视频/工具'); W = os.environ.get('工作目录', '')
NO = os.environ.get('回归篇', '27'); 基准 = f'{H}/回归基准_{NO}.json'
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
    r = subprocess.run(['python3', f'{H}/生成规则表.py'], capture_output=True, text=True, env={**env0, '旧工具': T})
    bad = [l for l in r.stdout.splitlines() if l.strip().startswith('没搬')]
    tmp = f'{H}/.规则表.新'; subprocess.run(['python3', f'{H}/生成规则表.py', '--写入', '--到', tmp], capture_output=True, env={**env0, '旧工具': T})
    新 = json.load(open(tmp)) if os.path.exists(tmp) else {}; os.path.exists(tmp) and os.remove(tmp)
    if 新.get('版本') != 表.get('版本'): bad.append(f'规则表.json 不是最新的（{表.get("版本")} → {新.get("版本")}）：python3 新管/生成规则表.py --写入')
    return bad, 表

def 文本自检(看门):
    import 规则执行核查 as RZ
    cmds = [c for c in RZ.FAST if c[0] not in 看门 and c[0] not in ('同步自检.py',)]   # 看门程序停用，不再当门
    with ThreadPoolExecutor(8) as ex:
        rs = list(ex.map(lambda c: (c, 跑(['python3', f'{T}/{c[0]}', *c[1:]], T, 300)), cmds))
    return [f'自检不通过：{" ".join(c)} → {o.splitlines()[-1][:160] if o else "无输出"}' for c, (rc, o, _) in rs if rc], len(cmds)

声音自检 = [   # 交付核查 出片前/出片后 里的声音核查自检（造坏声音必须抓到），在工作目录用回归篇跑
    ['标点停顿核对.py', NO, '--自检'], ['句首句尾与停顿位置核对.py', NO, '--自检'], ['读音核对.py', NO, '--自检'],
    ['词尾辅音核对.py', NO, '--自检'], ['无标点停顿核对.py', NO, '--自检'], ['纯人声核对.py', NO, '--自检'], ['句间停顿核对.py', NO, '--自检'],
    ['音频体检.py', '--自检', f'work_{NO}/a.wav', NO],
]
声音自检_成片 = [   # 要成片 NN.mp4 的
    ['audio_qc.py', f'{NO}.mp4', '--自检'], ['响度一致性核对.py', f'{NO}.mp4', '--自检'], ['机器复听.py', '--带自检', NO],
]

def 声音(有成片):
    cmds = 声音自检 + (声音自检_成片 if 有成片 else [])
    with ThreadPoolExecutor(6) as ex:
        rs = list(ex.map(lambda c: (c, 跑(['python3', f'{T}/{c[0]}', *c[1:]], W, 1200)), cmds))
    bad = []
    for c, (rc, o, _) in rs:
        if c[0] == '机器复听.py': rc = 1 if rc == 2 else 0   # 2 = 自检失灵；1 = 查出问题（回归篇本身不该有，但那是 ④ 的事）
        if rc: bad.append(f'声音自检不通过：{" ".join(c)} → {o.splitlines()[-1][:160] if o else "无输出"}')
    return bad, len(cmds)

def 挂钩():
    import 规则执行核查 as RZ
    return [f'挂钩：{x}' for x in RZ.挂钩检查(RZ.程序表())]

def 回归(记):
    """缓存重建回归篇：只出声音（AUDIO_ONLY，与正式出片同一套程序），比 a.wav、分段.json；每屏重画比像素哈希"""
    e = {**env0, 'AUDIO_ONLY': '1'}
    r = subprocess.run(['python3', 'make_video.py', f'scripts/{NO}.json', f'_回归{NO}.mp4'], capture_output=True, text=True, cwd=W, env=e)
    if r.returncode: return [f'回归：重建失败 {(r.stdout + r.stderr).strip()[-200:]}'], {}
    cur = {'a.wav': md5(f'{W}/work_{NO}/a.wav'), '分段.json': md5(f'{W}/work_{NO}/分段.json')}
    r = subprocess.run(['python3', f'{H}/画面哈希.py', NO], capture_output=True, text=True, cwd=W, env={**env0, '旧工具': T})
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
    b, n = 文本自检(看门); bad += b; out.append(f'② 文本/画面/流程 快自检 {n} 个程序：{"全过" if not b else f"{len(b)} 个不过"}（{time.time() - t0:.0f}s）')
    b = 挂钩(); bad += b; out.append(f'③ 挂钩检查：{"在" if not b else "断了"}')
    if '--只文本' not in a:
        if not W or not os.path.exists(f'{W}/make_video.py'): bad.append('没有出片工作目录（工作目录=…/video）：先 bash 视频/工具/环境/准备机器.sh')
        else:
            b, cur = 回归('--记基准' in a); bad += b; out.append(f'④ {NO} 回归：{"记了基准" if "--记基准" in a else ("逐字节、逐屏一致" if not b else "不一致")}（{time.time() - t0:.0f}s）')
            b, n = 声音(os.path.exists(f'{W}/{NO}.mp4')); bad += b; out.append(f'② 声音核查自检 {n} 个：{"全过" if not b else f"{len(b)} 个不过"}（{time.time() - t0:.0f}s）')
    print('\n'.join(out + [f'  ✘ {x}' for x in bad] + [f'快测{"通过" if not bad else "不通过"}，用时 {time.time() - t0:.0f} 秒']))
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
