#!/usr/bin/env python3
"""结尾句接点（自动找）：全篇最后一句按结尾句标准两遍合成（前段语速、最后一段语速），在最后一个标点后的静音里各找一个接点。
接点要求与出片程序 _ending_parts 相同：两侧各 10 ms 的 5 ms 帧都低于 -55 dB；取最后一个标点后、下一个词开口前最长的那段静音的正中间
（静音不足 30 ms 就停下，说明这一遍逗号后没有停顿，要人看）。08 之前是手工找的，09 起用本程序（现行做法：能交给程序的全交给程序）。
在视频工作目录下运行：python3 <工具目录>/结尾句接点.py NN [前段语速 最后一段语速 最后一段前停顿]（默认 0.90 0.78 0.70，07 定下的标准）
  --写入：把 结尾句 写进 scripts/NN.json（已有就覆盖这一句的设置）。"""
import sys, os, re, json
import numpy as np
sys.path.insert(0, '.')
exec(open('make_video.py').read().split("if __name__")[0])
args = [a for a in sys.argv[1:] if not a.startswith('--')]; no_ = args[0].zfill(2)
spF, spS, gap_ = (float(x) for x in (args[1:4] if len(args) >= 4 else ('0.90', '0.78', '0.70')))
js_ = f'scripts/{no_}.json'; d_ = json.load(open(js_)); si_ = len(d_['sentences'])
sent_ = ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in d_['sentences'][-1]['chunks'])
puncts_ = [m.end() for m in re.finditer(r'[,;:](?=\s)', sent_)]
if not puncts_: sys.exit(f'第{no_}篇最后一句没有句中标点：用 {{"整句语速": 0.80}}（01、02 的写法），不用接点')
cut_ = puncts_[-1]; tail_ = sent_[cut_:].strip()
F5 = int(0.005 * SR)


def find(speed):
    r_, _ = k.create(spoken(sent_), voice=V, speed=speed, lang='en-us'); r_ = np.asarray(r_, np.float32)
    tb_, _, ts_ = KT.create_timed(spoken(sent_), voice=V, speed=speed, lang='en-us', clause_pause=0, sentence_pause=0); sc_ = len(r_) / len(tb_)
    # 最后一个标点在带时长模型里的位置：按顺序数标点记号（, ; :），取最后一个
    pi_ = [i for i, t_ in enumerate(ts_) if t_.phoneme in (',', ';', ':')]
    if not pi_: sys.exit(f'带时长模型里找不到标点（语速 {speed}）')
    p_ = ts_[pi_[-1]]; nxt_ = next((t_ for t_ in ts_[pi_[-1] + 1:] if t_.phoneme.strip() and t_.phoneme not in (',', ';', ':', '.')), None)
    a_ = int(ts_[pi_[-1] - 1].end * sc_ * SR) if pi_[-1] > 0 else int(p_.start * sc_ * SR)
    b_ = int(nxt_.start * sc_ * SR) if nxt_ else len(r_)
    e_ = _env5(r_); lo_, hi_ = max(0, a_ // F5 - 6), min(len(e_), b_ // F5 + 6)
    best_ = (0, None)
    i_ = lo_
    while i_ < hi_:
        if e_[i_] < -55:
            j_ = i_
            while j_ < hi_ and e_[j_] < -55: j_ += 1
            if j_ - i_ > best_[0]: best_ = (j_ - i_, i_)
            i_ = j_
        else: i_ += 1
    n_, s_ = best_
    if n_ * 5 < 30: sys.exit(f'语速 {speed}：最后一个标点后找不到 ≥30 ms 的 -55 dB 静音（最长 {n_ * 5} ms），要人看')
    m_ = (s_ + n_ // 2) * F5
    seg_ = e_[max(0, (m_ - int(0.01 * SR)) // F5):(m_ + int(0.01 * SR)) // F5 + 1]
    assert seg_.max() < -55
    return m_, n_ * 5, len(r_)


mF, nF, LF = find(spF); mS, nS, LS = find(spS)
e_ = {'前段语速': spF, '最后一段语速': spS, '最后一段前停顿': gap_, '接点': [int(mF), int(mS)],
      '依据': f'全篇结尾句按 07 定下的标准（用户 2026-10-10 同意并要求所有视频统一）：前段 {spF}、最后一段“{tail_}” {spS}、前面停 {gap_} 秒。'
              f'接点由 结尾句接点.py 自动找：{spF} 那遍最后一个标点后最长静音（{nF} ms）的正中 {mF / SR:.3f} s，{spS} 那遍（{nS} ms）的正中 {mS / SR:.3f} s，'
              f'两侧 10 ms 都低于 -55 dB（程序以 08 校准：与人工核实的接点落在同一段静音里）'}
print(f'第{no_}篇 S{si_}：“{sent_}”')
print(f'  最后一段：“{tail_}”')
print(f'  前段 {spF}：接点样本 {mF}（{mF / SR:.3f} 秒，所在静音 {nF} ms）；最后一段 {spS}：接点样本 {mS}（{mS / SR:.3f} 秒，所在静音 {nS} ms）')
print('  结尾句 = ' + json.dumps({f'S{si_}': e_}, ensure_ascii=False))
if '--写入' in sys.argv:
    d_.setdefault('结尾句', {})[f'S{si_}'] = e_
    json.dump(d_, open(js_, 'w'), ensure_ascii=False, indent=1); print(f'  已写进 {js_}')
