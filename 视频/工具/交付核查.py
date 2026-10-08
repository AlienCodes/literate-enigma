#!/usr/bin/env python3
"""每篇视频的交付核查（硬性条件：不通过不得交付）。在视频工作目录（含 make_video.py、scripts/、work_NN/）下运行：
  python3 <工具目录>/交付核查.py NN 出片前     # 合成配音前：数字读法、标点停顿、句首句尾、无标点停顿
  python3 <工具目录>/交付核查.py NN 出片后     # 出片后：自动音频检查、独立复核（逐样本比对原始合成）、生成标点试听
对应踩坑：A8 分段合成发闷、A9 停顿放错、A10/A10b 词尾被切、A11 数字读错、A12 连读处停顿越界、L13 换行。"""
import sys, os, re, json, subprocess
T = os.path.dirname(os.path.abspath(__file__)); no, stage = sys.argv[1].zfill(2), sys.argv[2]
ok = True; out = []
def run(cmd, env=None):
    r = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    return r.returncode, r.stdout + r.stderr
def step(name, passed, detail=''):
    global ok
    ok &= passed; out.append(f"{'✔' if passed else '✘'} {name}" + (f"\n    {detail}" if detail else ''))

if stage == '出片前':
    # 1 数字读法（A11）：列出全文所有数字及配音实际读法，供人工逐个核对；出现未处理的格式即不合格
    src = open('make_video.py').read(); exec(src[src.index('# 朗读用的数字读法'):src.index('def say(t):')])
    d = json.load(open(f'scripts/{no}.json'))
    texts = [d['title_en']] + [' '.join(re.sub(r'\*\*|\{\{.*?\}\}', '', c['en']).strip() for c in s['chunks']) for s in d['sentences']]
    rows = []; odd = []
    for x in texts:
        for m in re.finditer(r"\S*\d\S*", x):
            ctx = x[max(0, m.start()-12):m.end()+12]
            rows.append(f"{m.group(0):>14}  →  {spoken(ctx)}")
            if re.search(r'\d+\.\d+|%|\$|£|€|\d+/\d+', m.group(0)): odd.append(m.group(0))
    step('数字读法清单（请人工逐个确认读法）', not odd, '\n    '.join(rows) + (f"\n    未处理的数字格式：{odd}" if odd else ''))
    # 2–4 停顿与词尾
    c, o = run(['python3', f'{T}/标点停顿核对.py', no]); step('标点停顿核对（A9/A10：停顿时长、不切词）', '问题数 0' in o, '' if '问题数 0' in o else '\n    '.join(l for l in o.splitlines() if 'BAD' in l or 'FAIL' in l))
    c, o = run(['python3', f'{T}/句首句尾与停顿位置核对.py', no]); step('句首句尾与停顿位置核对', '问题数 0' in o, '' if '问题数 0' in o else '\n    '.join(l for l in o.splitlines() if 'BAD' in l))
    c, o = run(['python3', f'{T}/无标点停顿核对.py', no])
    long = [l for l in o.splitlines() if re.search(r'停顿 (\d+\.\d+)s', l) and float(re.search(r'停顿 (\d+\.\d+)s', l).group(1)) > 0.22]
    step('无标点处停顿 ≤ 0.22 秒', not long, '\n    '.join(long))
elif stage == '出片后':
    c, o = run(['python3', f'{T}/audio_qc.py', f'{no}.mp4'])
    step('自动音频检查（削波、电流音、停顿超长、响度骤降）', c == 0, o.strip() + ('\n    → 标出的位置必须剪成试听交用户确认' if c else ''))
    env = {'VIDEO_ROOT': os.path.abspath('..')}
    for sc in ('synth.py', 'labels.py'):
        c, o = run(['python3', f'{T}/独立复核/{sc}', no], env); 
        if c: step(f'独立复核准备 {sc}', False, o[-500:])
    c, o = run(['python3', f'{T}/独立复核/audit.py', no], env)
    cuts = re.findall(r'cut tail=([\d.]+)ms onset=([\d.]+)ms', o); bad = [x for x in cuts if float(x[0]) > 0 or float(x[1]) > 0]
    extra = re.findall(r'extra non-zero runs not explained by raw copies: (\d+)', o)
    step(f'独立复核：{len(cuts)} 处改动，词尾/词头被切 = {len(bad)}，多余声音 = {extra}', c == 0 and not bad and extra == ['0'], o[-800:] if bad or extra != ['0'] else '')
    # 标点试听（交用户逐处听）
    import numpy as np, soundfile as sf, imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe(); a, sr = sf.read(f'work_{no}/a.wav')
    subprocess.run([FF, '-v', 'error', '-y', '-i', f'{no}.mp4', '-vn', '-ac', '1', '-ar', str(sr), f'work_{no}/final.wav'], check=True)
    f, _ = sf.read(f'work_{no}/final.wav'); z = np.append((a == 0).astype(np.int8), 0); runs = []; st = None
    for i, v in enumerate(z):
        if v and st is None: st = i
        if not v and st is not None:
            if 0.1 <= (i - st) / sr <= 0.5 and st / sr > 1.0: runs.append((st / sr, i / sr))
            st = None
    beep = 0.15 * np.sin(2 * np.pi * 880 * np.arange(int(0.12 * sr)) / sr) * np.hanning(int(0.12 * sr)); parts = []
    for s0, s1 in runs: parts += [f[int((s0 - 1.6) * sr):int((s1 + 0.7) * sr)], np.zeros(int(0.35 * sr)), beep, np.zeros(int(0.35 * sr))]
    if parts:
        sf.write(f'work_{no}/punct.wav', np.concatenate(parts), sr)
        subprocess.run([FF, '-v', 'error', '-y', '-i', f'work_{no}/punct.wav', '-c:a', 'libmp3lame', '-b:a', '192k', f'标点试听_{no}.mp3'], check=True)
    step(f'生成标点试听 标点试听_{no}.mp3（{len(runs)} 处，需交用户试听）', True)
print(f'第{no}篇 {stage}核查：\n' + '\n'.join(out) + f"\n{'全部通过' if ok else '【不通过，不得交付】'}")
sys.exit(0 if ok else 1)
