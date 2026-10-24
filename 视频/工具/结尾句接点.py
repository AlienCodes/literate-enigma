#!/usr/bin/env python3
"""结尾句接点（自动找）：全篇最后一句按结尾句标准两遍合成（前段语速、最后一段语速），在最后一个标点后的静音里各找一个接点。
接点要求与出片程序 _ending_parts 相同：接点所在的 5 ms 帧和两侧各一帧都低于 -55 dB；取最后一个标点后、下一个词开口前最长的那段静音的正中间。
标准语速那一遍逗号处连读、静音不足 15 ms 时，依次试相邻语速（前段 0.88、0.92、0.86，最后一段 0.80、0.76），写明用了哪个、为什么（02 结尾句 0.80→0.83 是先例）。08 之前是手工找的，09 起用本程序（现行做法：能交给程序的全交给程序）。
在视频工作目录下运行：python3 <工具目录>/结尾句接点.py NN [前段语速 最后一段语速 最后一段前停顿]（默认 0.90 0.78 0.70，07 定下的标准）
  --写入：把 结尾句 写进 scripts/NN.json（已有就覆盖这一句的设置）。"""
import sys, os, re, json
import numpy as np
# G31（2026-10-24 25 草稿）：--写入 整句覆盖，把手写的“前段增益dB”（25 S17 -2.5 dB）冲掉了。只覆盖本程序算出的字段，别的原样保留；
# 接点变了，前段音调的“范围”（按接点算的）作废，出片程序会停下要求重跑 --写前段音调范围
算的 = ('前段语速', '最后一段语速', '最后一段前停顿', '接点', '前段单独合成', '依据')
def 合并(old, e):
    keep = {k: v for k, v in (old or {}).items() if k not in 算的}
    if old and old.get('接点') != e['接点'] and isinstance(keep.get('前段音调'), dict) and '范围' in keep['前段音调']:
        keep['前段音调'] = {k: v for k, v in keep['前段音调'].items() if k != '范围'}
    return {**e, **keep}
def 自检():
    f = []; e = {'前段语速': 0.9, '最后一段语速': 0.78, '最后一段前停顿': 0.7, '接点': [100, 200], '依据': '新'}
    old = {'前段语速': 0.88, '接点': [100, 200], '依据': '旧', '前段增益dB': -2.5, '前段单独合成': True, '前段音调': {'半音': -1, '范围': [0.1, 0.4]}}
    m = 合并(old, e)
    if m.get('前段增益dB') != -2.5: f.append('没抓到：重跑接点 --写入 把“前段增益dB”冲掉了（G31 重放 25 S17）')
    if m.get('前段音调', {}).get('范围') != [0.1, 0.4]: f.append('接点没变却丢了前段音调范围')
    if m['前段语速'] != 0.9 or m['依据'] != '新' or '前段单独合成' in m: f.append('本程序算的字段没按新算的覆盖')
    if '范围' in 合并(old, dict(e, 接点=[150, 200]))['前段音调']: f.append('没抓到：接点变了，按旧接点算的前段音调范围还留着')
    return ['结尾句接点 自检：' + x for x in f]
if '--自检' in sys.argv:
    e = 自检(); print('\n'.join(e) or '结尾句接点 自检通过（重跑 --写入 保留前段增益dB 等手写字段；接点变了作废前段音调范围）'); sys.exit(1 if e else 0)
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


ALONE = '--前段单独合成' in sys.argv     # 10 S17：前段（If so,）单独合成，so 才拖得长（见 make_video._ending_front）；接点在前段末尾的静音里
def find(speed, front=False):
    txt_ = _ending_front(sent_) if front and ALONE else sent_
    r_, _ = k.create(spoken(txt_), voice=V, speed=speed, lang='en-us'); r_ = np.asarray(r_, np.float32)
    tb_, _, ts_ = KT.create_timed(spoken(txt_), voice=V, speed=speed, lang='en-us', clause_pause=0, sentence_pause=0); sc_ = len(r_) / len(tb_)
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
    if n_ * 5 < 15: return None
    m_ = (s_ + n_ // 2) * F5 + F5 // 2
    seg_ = e_[max(0, m_ // F5 - 1):m_ // F5 + 2]
    assert seg_.max() < -55
    return m_, n_ * 5, len(r_)


why_ = []
def pick(sp0, alts, nm):
    for sp in [sp0] + alts:
        r = find(sp, nm == '前段')
        if r: 
            if sp != sp0: why_.append(f'{nm}标准语速 {sp0} 那一遍最后一个标点处连读（-55 dB 静音不足 15 ms），改用 {sp}')
            return sp, r
    sys.exit(f'{nm}在语速 {[sp0] + alts} 下最后一个标点后都找不到 ≥15 ms 的 -55 dB 静音，要人看')
spF, (mF, nF, LF) = pick(spF, [0.88, 0.92, 0.86], '前段'); spS, (mS, nS, LS) = pick(spS, [0.80, 0.76], '最后一段')
e_ = {'前段语速': spF, '最后一段语速': spS, '最后一段前停顿': gap_, '接点': [int(mF), int(mS)], **({'前段单独合成': True} if ALONE else {}),
      '依据': f'全篇结尾句按 07 定下的标准（用户 2026-10-10 同意并要求所有视频统一）：前段 {spF}、最后一段“{tail_}” {spS}、前面停 {gap_} 秒。'
              f'接点由 结尾句接点.py 自动找：{spF} 那遍最后一个标点后最长静音（{nF} ms）的正中 {mF / SR:.3f} s，{spS} 那遍（{nS} ms）的正中 {mS / SR:.3f} s，'
              f'所在帧和两侧各 5 ms 都低于 -55 dB（程序以 08 校准：与人工核实的接点落在同一段静音里）' + ('；' + '；'.join(why_) if why_ else '')
              + ('；前段单独合成（“' + _ending_front(sent_) + '”单独一遍，so 自然拖长、音调落下；接点在这一遍末尾的静音里）' if ALONE else '')}
if '--写前段音调范围' in sys.argv:   # 前段音调要改的浊音段写死在脚本里（出片程序不现测，保证同一个脚本出的声音逐样本相同）
    eo_ = d_['结尾句'][f'S{si_}']; rF_, _ = k.create(spoken(sent_), voice=V, speed=float(eo_['前段语速']), lang='en-us')
    a_, b_ = _tone_span(np.asarray(rF_, np.float32), int(eo_['接点'][0])); eo_['前段音调']['范围'] = [round(a_, 3), round(b_, 3)]
    json.dump(d_, open(js_, 'w'), ensure_ascii=False, indent=1); print(f'  前段音调 范围 {a_:.3f}–{b_:.3f} 秒，已写进 {js_}'); sys.exit(0)
print(f'第{no_}篇 S{si_}：“{sent_}”')
print(f'  最后一段：“{tail_}”')
print(f'  前段 {spF}：接点样本 {mF}（{mF / SR:.3f} 秒，所在静音 {nF} ms）；最后一段 {spS}：接点样本 {mS}（{mS / SR:.3f} 秒，所在静音 {nS} ms）')
print('  结尾句 = ' + json.dumps({f'S{si_}': e_}, ensure_ascii=False))
if '--写入' in sys.argv:
    d_.setdefault('结尾句', {})[f'S{si_}'] = 合并(d_.get('结尾句', {}).get(f'S{si_}'), e_)   # G31：手写的前段增益dB 等原样保留
    json.dump(d_, open(js_, 'w'), ensure_ascii=False, indent=1); print(f'  已写进 {js_}')
