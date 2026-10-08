"""Synthesize ground-truth raw Kokoro audio for title + every sentence of articles 01-03.
Text rule (from the task): title_en first; then per sentence: for each chunk strip ** and {{...}},
strip whitespace, join chunks with single spaces."""
import sys, json, re, os, numpy as np
import os
S = os.environ.get('VIDEO_ROOT', os.path.abspath(os.path.join(os.getcwd(), '..')))  # 工作根目录：其下有 video/ 与 tts/
W = os.environ.get('QC_DIR', S + '/qc_independent')
OUT = W + '/gt'
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, S + '/tts')
from kokoro_onnx import Kokoro
_src=open(S+'/video/make_video.py').read(); exec(_src[_src.index('# 朗读用的数字读法'):_src.index('def say(t):')])  # 与成片相同的数字读法（A11）


def texts_for(no):
    d = json.load(open(f'{S}/video/scripts/{no}.json'))
    out = [('title', -1, d['title_en'])]
    for si, s in enumerate(d['sentences']):
        parts = []
        for c in s['chunks']:
            t = re.sub(r'\{\{.*?\}\}', '', c['en'])
            t = t.replace('**', '').strip()
            parts.append(t)
        out.append(('sent', si, ' '.join(parts), s['para'], [p for p in parts]))
    return d, out


if __name__ == '__main__':
    k = Kokoro(S + '/tts/kokoro-v1.0.onnx', S + '/tts/voices-v1.0.bin')
    V = np.load(S + '/tts/voice_mb.npy')
    meta = {}
    for no in sys.argv[1:]:
        d, items = texts_for(no)
        meta[no] = []
        for it in items:
            idx = it[1]
            text = it[2]
            fn = f'{OUT}/{no}_{"T" if idx < 0 else "%02d" % idx}.npy'
            if spoken(text)!=text or not os.path.exists(fn):
                a, sr = k.create(spoken(text), voice=V, speed=0.95, lang='en-us')
                assert sr == 24000
                np.save(fn, np.asarray(a, np.float32))
            meta[no].append({'idx': idx, 'text': text, 'file': fn,
                             'para': it[3] if len(it) > 3 else None,
                             'chunks': it[4] if len(it) > 4 else [text]})
            print(no, idx, text[:70], flush=True)
        json.dump(meta[no], open(f'{OUT}/{no}_meta.json', 'w'), indent=1, ensure_ascii=False)
