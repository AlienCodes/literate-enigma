#!/usr/bin/env python3
"""出片守门自检（规则执行机器，CLAUDE.md 第16条）：出片程序 make_video.py 里每一道“停止”守门，都在真实脚本的副本上
故意改坏一处、只出声音，出片程序必须停下并报出对应的编号；原样的一份必须完整出完（不误拦）。
出片程序从工作目录 scripts/ 下所有脚本读设置（按句子原文对应），所以每一项都在并排的隔离工作区 ../守门自检/ 里跑：
模型、字体、缓存等一律链接回原工作目录，scripts/ 里只放这一份改坏的脚本，work_NN 也是隔离的，不碰正式篇目。
在视频工作目录下运行：python3 <工具目录>/出片守门自检.py
全部通过 → 把 make_video.py、render.py 和本程序的指纹写进 工具/出片守门自检通过.json（规则执行机器核对：出片程序一改，
指纹对不上，提交、推送一律停，直到重跑本自检通过）。"""
import os, sys, json, copy, subprocess, hashlib, shutil, time
T = os.path.dirname(os.path.abspath(__file__)); STAMP = f'{T}/出片守门自检通过.json'
指纹 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def 改(d, path, val):
    x = d
    for k in path[:-1]: x = x.setdefault(k, {})
    x[path[-1]] = val(x.get(path[-1])) if callable(val) else val


CASES = [   # (编号, 篇, 改法说明, 改法, 环境变量, 停止信息里必须有的字)
    ('原样', '20', '不改（不得误拦）', lambda d: None, {}, None),
    ('T36', '20', '24 起中文里出现破折号', lambda d: (改(d, ['no'], '24'), d['sentences'][0]['chunks'][0].__setitem__('zh', d['sentences'][0]['chunks'][0]['zh'] + '——')), {}, '（T36）'),
    ('A45', '20', '区间声音指纹对不上（读音/语速改过，旧区间没作废）', lambda d: 改(d, ['区间声音指纹'], {k: '000000000000' for k in d.get('非人声区间', {})}), {}, '（A45）'),
    ('A45放行', '20', '指纹对不上但带 OLD_IV_VOID=1（草稿声音.sh）：跳过旧区间、完整出完', lambda d: 改(d, ['区间声音指纹'], {k: '000000000000' for k in d.get('非人声区间', {})}), {'OLD_IV_VOID': '1'}, None),
    ('A45开关', '20', 'OLD_IV_VOID=1 却出正式视频（不是只出声音）', lambda d: None, {'OLD_IV_VOID': '1', 'AUDIO_ONLY': ''}, '（A45 开关）'),
    ('A30', '20', '停顿插入点写成第 99 个标点', lambda d: 改(d, ['停顿插入点', 'S1'], {'99': 1.0}), {}, '个标点超出'),
    ('音21', '20', '句子增益写 2 dB', lambda d: 改(d, ['句子增益dB'], {'S1': 2.0}), {}, '句子增益dB 只许'),
    ('A3', '20', '环境变量换音色', lambda d: None, {'VOICE': 'voice_mf.npy'}, '（A3/A7）'),
    ('A7', '20', '环境变量换降噪', lambda d: None, {'AFFILE': 'AF.txt'}, '（A3/A7）'),
    ('A27', '02', '结尾句语速改回会丢 /z/ 的 0.80', lambda d: 改(d, ['结尾句', 'S16', '整句语速'], 0.80), {}, '（A27）'),
    ('A33', '10', '前段音调去掉“范围”', lambda d: 改(d, ['结尾句', 'S17', '前段音调'], lambda v: {k: x for k, x in (v or {'拉长': 1.0}).items() if k != '范围'}), {}, '前段音调没有写 范围'),
    ('A40', '20', 'S3 除阻加强增益写 7 dB（超过 6 dB）', lambda d: 改(d, ['除阻加强', 'S3', '1'], lambda v: [v[0], v[1], 7.0]), {}, '除阻加强的位置或增益不对'),
    ('A39', '20', 'S11 连读处补除阻挪进下一个词 0.3 秒', lambda d: 改(d, ['停顿处除阻', 'S11', '2'], lambda v: [v[0] + 0.3, v[1] + 0.3, v[2]]), {}, '连读处补除阻的位置不对'),
    ('A10', '20', 'S5 第1个标点的停顿删除区间写在句首（删到词的声音）', lambda d: 改(d, ['停顿删除区间', 'S5'], {'1': [0.10, 0.20]}), {}, '停顿删除区间不在该标点处'),
    ('A12', '04', '连读处 S7 的人工插入点挪进下一个词 0.35 秒（重放 01 The unskilled, the）', lambda d: 改(d, ['停顿插入点', 'S7', '1'], lambda v: v + 0.35), {}, 'A15'),
    ('A15', '04', 'S7 人工插入点挪进词里 0.35 秒', lambda d: 改(d, ['停顿插入点', 'S7', '1'], lambda v: v + 0.35), {}, 'A15'),
    ('A28', '04', 'S17 人工插入点挪进词里 0.35 秒', lambda d: 改(d, ['停顿插入点', 'S17', '1'], lambda v: v + 0.35), {}, 'A15'),
    ('A42', '19', 'S2 交界插入点写法错', lambda d: 改(d, ['停顿插入点', 'S2', '2'], lambda v: [v[0], '交界错']), {}, '（A42）'),
    ('A25', '07', '去掉 S16 放慢版在 /i/→/s/ 交界的人工插入点', lambda d: d['停顿插入点'].pop('S16'), {}, '（A25）'),
    ('A32', '10', '结尾句接点挪出最后一个标点的停顿', lambda d: 改(d, ['结尾句', 'S17', '接点'], lambda v: [v[0] + 2400, v[1] + 2400]), {}, '结尾句的接点'),
]


def main():
    if not os.path.exists('make_video.py') or not os.path.isdir('scripts'):
        sys.exit('【停止】请在视频工作目录（含 make_video.py、scripts/）下运行')
    for f in ('make_video.py', 'render.py'):
        if 指纹(f) != 指纹(f'{T}/{f}'): sys.exit(f'【停止】工作目录的 {f} 与仓库不一致，先拷过来再自检')
    only = sys.argv[1:]; fails = []; t0 = time.time(); W = os.getcwd(); WS = os.path.abspath('../守门自检')
    shutil.rmtree(WS, ignore_errors=True); os.makedirs(f'{WS}/scripts')
    for x in os.listdir(W):
        if x == 'scripts' or x.startswith('work_') or x.endswith(('.mp4', '.mp3', '.wav', '.json')): continue
        os.symlink(f'{W}/{x}', f'{WS}/{x}')
    for rid, no, how, fn, env, want in CASES:
        if only and rid not in only: continue
        d = copy.deepcopy(json.load(open(f'{W}/scripts/{no}.json')))
        try: fn(d)
        except Exception as e: fails.append(f'{rid} 自检样本找不到（{no} {how}）：{e}'); continue
        for p in os.listdir(f'{WS}/scripts'): os.remove(f'{WS}/scripts/{p}')
        json.dump(d, open(f'{WS}/scripts/{no}.json', 'w'), ensure_ascii=False)
        r = subprocess.run(['python3', 'make_video.py', f'scripts/{no}.json', f'守门自检_{rid}.mp4'], capture_output=True, text=True, cwd=WS,
                           env={**os.environ, 'AUDIO_ONLY': '1', **env})
        o = r.stdout + r.stderr; stop = [l for l in o.splitlines() if '【停止】' in l]
        if want is None: ok = r.returncode == 0 and not stop
        else: ok = r.returncode != 0 and any(want in l for l in stop)
        print(f"{'✔' if ok else '✘'} {rid}：第{no}篇 {how} → " + (('完整出完' if r.returncode == 0 else '没出完：' + (stop or o.strip().splitlines()[-1:])[0][:120]) if want is None
              else (stop[0][:110] if stop else f'没停（退出码 {r.returncode}）')))
        if not ok: fails.append(f'没抓到：{rid}（{how}）' if want else f'误拦：{rid}')
    shutil.rmtree(WS, ignore_errors=True)
    if not only or 'A36' in only:   # A36：复合词按它自己那一条读音改正换；所有格的 s 不被吞（注音函数直接测）
        sys.path.insert(0, W); import make_video as MV
        hb, bs = MV.PRON_WORDS.get('Haber-Bosch'), MV.PRON_WORDS.get('BASF')
        p1, p2 = MV.phonemes_of('the Haber-Bosch process'), MV.phonemes_of('BASF’s plant')
        g = MV.PRON_WORDS.pop('Haber-Bosch')
        try: p3 = MV.phonemes_of('the Haber-Bosch process')   # 拿掉复合词这一条：要么停（A23 守门：Haber 没换到），要么读音变了
        except SystemExit: p3 = '（停下）'
        MV.PRON_WORDS['Haber-Bosch'] = g
        ok = bool(hb and bs) and hb in p1 and hb not in p3 and any(bs + x in p2 for x in 'sz')
        print(f"{'✔' if ok else '✘'} A36：Haber-Bosch 按登记读音{'换到' if hb and hb in p1 else '没换到'}、拿掉改正后{'停下' if p3 == '（停下）' else ('变回' if hb and hb not in p3 else '没变')}；BASF’s 结尾 s {'保住' if bs and any(bs + x in p2 for x in 'sz') else '被吞'}")
        if not ok: fails.append('没抓到：复合词读音、所有格 s（A36）')
    if not fails and not only:
        json.dump({'make_video.py': 指纹(f'{T}/make_video.py'), 'render.py': 指纹(f'{T}/render.py'), '出片守门自检.py': 指纹(__file__),
                   '时间': time.strftime('%Y-%m-%dT%H:%M'), '项数': len(CASES)}, open(STAMP, 'w'), ensure_ascii=False, indent=1)
    print(f'出片守门自检：' + ('通过（每一道守门造的错都停下并报对编号，原样完整出完）' if not fails else '失灵！' + '；'.join(fails)) + f'（{time.time() - t0:.0f} 秒）')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
