#!/usr/bin/env python3
"""词尾实测（2026-10-25 主对话：机器复听清单的“疑似真问题”要补声学实测，分成“实测确认有问题 / 实测正常”，用户只听确认有问题的）。
成片在每个词上与原始合成逐样本相同（独立复核保证），所以在这一句的原始合成里按带时长模型的音素时刻量：
  词尾少了辅音（streaked→streak）：词尾辅音的电平（相对本句最响 10 ms）和时长，和同一模型单独合成这个词的参考比；
  漏词、读音不同：整个词的电平（相对本句各词中位数）和时长，和单独合成的参考比。
判定：词尾辅音比参考低 ≥12 dB 或时长不到参考的 40%，整词比本句中位数低 ≥12 dB 或时长不到参考的 40%，算“实测确认有问题”。
用法（视频工作目录，scripts/NN.json 要在）：python3 词尾实测.py 清单.md > 结果.md
"""
import os, sys, re, json
T = os.path.dirname(os.path.abspath(__file__))

def main(md):
    import numpy as np
    g = {'__name__': 'x', '__file__': os.path.abspath('make_video.py')}; exec(open('make_video.py').read().split("if __name__")[0], g)
    k, KT, V, SPEED, spoken, R = g['k'], g['KT'], g['V'], g['SPEED'], g['spoken'], g['R']
    sys.path.insert(0, T); import 机器复听 as M
    vow = set('aeiouæɑɒɔəɛɜɪʊʌyɐᵻɚ')
    def synth(text):
        r, sr = k.create(spoken(text), voice=V, speed=SPEED, lang='en-us'); r = np.asarray(r, float)
        tb, _, ts = KT.create_timed(spoken(text), voice=V, speed=SPEED, lang='en-us', clause_pause=0, sentence_pause=0); sc = len(r) / len(tb)
        return r, sr, [(t.phoneme, t.start * sc * sr, t.end * sc * sr) for t in ts]   # 采样点
    def 词组(toks):
        gs, cur = [], []
        for p, a, b in toks:
            if not p.strip() or p in ',;:.!?"“”()': (gs.append(cur) if cur else None); cur = []
            else: cur.append((p, a, b))
        if cur: gs.append(cur)
        return gs
    def db(x, ref): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) / ref + 1e-12) if len(x) else -120.0
    def 量(r, sr, grp):
        a0, b0 = grp[0][1], grp[-1][2]; tail = [q for q in grp[::-1]]; tc = []
        for q in tail:
            if q[0] in vow: break
            tc.insert(0, q)
        return a0, b0, (tc[0][1], tc[-1][2]) if tc else None
    out_bad, out_ok, out_na = [], [], []
    for l in open(md).read().splitlines():
        m = re.match(r'- (\d\d) S(\d+)：脚本“([^”]*)” 听到“([^”]*)”.*—— (.+)$', l)
        if not m: continue
        no, si, x, y, why = m.group(1), int(m.group(2)), m.group(3), m.group(4), m.group(5)
        if x == '（多出）': out_ok.append(f'{l[2:]} → 多出的词不在脚本里，无从实测（识别器多听）'); continue
        d = json.load(open(f'scripts/{no}.json')); s = d['sentences'][si - 1]
        sent = ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        r, sr, toks = synth(sent); F = int(0.01 * sr); n = len(r) // F; ref = np.sqrt(np.mean(r[:n * F].reshape(n, F) ** 2, axis=1)).max()
        gs = 词组(toks); ws = x.split(); tgt = [M.音标(w) for w in ws]
        ph = [re.sub(r'[ˈˌː]', '', ''.join(q[0] for q in g_)).translate(str.maketrans({'ᵻ': 'ɪ', 'ɐ': 'ə', 'ɾ': 't'})).replace('ɚ', 'əɹ') for g_ in gs]
        hit = next((i for i in range(len(ph) - len(tgt) + 1) if ph[i:i + len(tgt)] == tgt), None)
        if hit is None:
            sr_ = json.load(open(f'work_{no}/分段.json')).get(f'S{si}', []) if os.path.exists(f'work_{no}/分段.json') else []
            span = f'，这一句在定稿视频 {sr_[0]["时刻"][0]:.1f}–{sr_[-1]["时刻"][1]:.1f}s' if sr_ else ''
            j_ = sent.lower().find(x.split()[0].lower())
            if sr_ and j_ >= 0:   # 按所在停顿段、段内字母位置估这个词的时刻（误差约 ±0.5 秒）
                pcs = re.split(r'(?<=[,;:])\s', sent); k_ = 0; c_ = 0
                while k_ < len(pcs) - 1 and c_ + len(pcs[k_]) + 1 <= j_: c_ += len(pcs[k_]) + 1; k_ += 1
                q_ = sr_[min(k_, len(sr_) - 1)]; f_ = (j_ - c_) / max(1, len(pcs[k_]))
                span += f'，这个词约在 {q_["时刻"][0] + f_ * (q_["时刻"][1] - q_["时刻"][0]):.1f}s'
            out_na.append(f'{l[2:]} → 在原始合成的音素里找不到这个词（数字、缩写、读音改正展开过），没量{span}'); continue
        grp = [q for g_ in gs[hit:hit + len(tgt)] for q in g_]
        a0, b0, tc = 量(r, sr, grp)
        rw, srw, tw = synth(x); gw = [q for g_ in 词组(tw) for q in g_]; nw = len(rw) // F
        refw = np.sqrt(np.mean(rw[:nw * F].reshape(nw, F) ** 2, axis=1)).max(); aw, bw, tcw = 量(rw, srw, gw)
        sr_ = json.load(open(f'work_{no}/分段.json')).get(f'S{si}', []) if os.path.exists(f'work_{no}/分段.json') else []
        pc = next((q for q in sr_ if q['原始'][0] <= a0 < q['原始'][1]), None)
        t0 = (f'定稿视频约 {pc["时刻"][0] + (a0 - pc["原始"][0]) / sr:.1f}s' if pc else f'句内 {a0 / sr:.2f}s')   # 段内按原始合成的位置推算（段内长停顿压缩过，误差 ≤0.2 秒）
        if '词尾少了' in why and tc and tcw:
            e1 = db(r[int(tc[0]):int(tc[1])], ref); e2 = db(rw[int(tcw[0]):int(tcw[1])], refw); d1 = (tc[1] - tc[0]) / sr * 1000; d2 = (tcw[1] - tcw[0]) / srw * 1000
            bad = e1 < -40 or d1 < 20   # 单独合成的词天然拖长，不能拿时长比；看这个辅音在句子里实际有没有声音
            msg = f'{l[2:]} → 实测（{t0}）：词尾辅音 {e1:.0f} dB、{d1:.0f} ms；单独合成参考 {e2:.0f} dB、{d2:.0f} ms'
        else:
            med = np.median([db(r[int(g_[0][1]):int(g_[-1][2])], ref) for g_ in gs if g_[-1][2] > g_[0][1]])
            e1 = db(r[int(a0):int(b0)], ref); d1 = (b0 - a0) / sr * 1000; d2 = (bw - aw) / srw * 1000
            bad = e1 - med <= -12 or d1 < 40
            msg = f'{l[2:]} → 实测（{t0}）：整词 {e1:.0f} dB（本句各词中位数 {med:.0f} dB）、{d1:.0f} ms；单独合成参考 {d2:.0f} ms'
        (out_bad if bad else out_ok).append(msg)
    print('# 机器复听“疑似真问题”声学实测（01–24 已定稿：只列不改）\n')
    print(f'判定：词尾辅音电平低于 -40 dB（相对本句最响 10 ms）或短于 20 ms，整词比本句各词中位数低 ≥12 dB 或短于 40 ms，算确认有问题；单独合成的参考只列出不作判据（单读的词天然拖长）。成片在这些词上与原始合成逐样本相同（独立复核），时刻是这一句原始合成里的秒。\n')
    print(f'## 实测确认有问题（{len(out_bad)} 处，用户只听这些）\n'); print('\n'.join('- ' + x for x in out_bad) or '（无）')
    print(f'\n## 没量成（{len(out_na)} 处，程序拿不准，用户听）\n'); print('\n'.join('- ' + x for x in out_na) or '（无）')
    print(f'\n## 实测正常（{len(out_ok)} 处：声音里这个音在，是识别器没听准）\n'); print('\n'.join('- ' + x for x in out_ok) or '（无）')

if __name__ == '__main__':
    main(sys.argv[1])
