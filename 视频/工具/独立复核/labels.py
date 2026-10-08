"""Approximate word timings in RAW sentence time, for labeling only (not used for pass/fail).
Uses the timed model's phoneme timings scaled to the raw length, and a proportional
char mapping from individually phonemized text words onto the sentence phoneme stream."""
import sys, json, re, numpy as np
import os
S = os.environ.get('VIDEO_ROOT', os.path.abspath(os.path.join(os.getcwd(), '..')))  # 工作根目录：其下有 video/ 与 tts/
W = os.environ.get('QC_DIR', S + '/qc_independent'); os.makedirs(W, exist_ok=True)
from kokoro_onnx import Kokoro
_src=open(S+'/video/make_video.py').read(); exec(_src[_src.index('# 朗读用的数字读法'):_src.index('def say(t):')])  # 与成片相同的数字读法
V = np.load(S + '/tts/voice_mb.npy')
KT = Kokoro(S + '/tts/kokoro-v1.0-timed.onnx', S + '/tts/voices-v1.0.bin')
SKIP = set("ˈˌ ,.;:!?—…\"'()-“”")

for no in sys.argv[1:]:
    meta = json.load(open(f'{W}/gt/{no}_meta.json'))
    out = []
    for it in meta:
        text = it['text']
        raw = np.load(it['file'])
        tb, _, sp = KT.create_timed(spoken(text), voice=V, speed=0.95, lang='en-us', clause_pause=0, sentence_pause=0)
        sc = len(raw) / len(tb)
        # phoneme char stream with times
        chars = [(t.phoneme, t.start * sc, t.end * sc) for t in sp if t.phoneme not in SKIP and t.phoneme.strip()]
        words = re.findall(r'\S+', text)
        lens = []
        for w in words:
            p = KT.tokenizer.phonemize(w, 'en-us')
            lens.append(max(1, sum(1 for c in p if c not in SKIP and c.strip())))
        tot_w = sum(lens); tot_c = len(chars)
        res = []; cum = 0
        for w, l in zip(words, lens):
            a = int(round(cum * tot_c / tot_w)); b = int(round((cum + l) * tot_c / tot_w)) - 1
            a = min(a, tot_c - 1); b = max(a, min(b, tot_c - 1))
            res.append((w, chars[a][1], chars[b][2]))
            cum += l
        out.append({'idx': it['idx'], 'words': res,
                    'phon': [(t.phoneme, t.start * sc, t.end * sc) for t in sp]})
        print(no, it['idx'], flush=True)
    json.dump(out, open(f'{W}/gt/{no}_labels.json', 'w'), ensure_ascii=False)
