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
# A21 词尾除阻：脚本里写了"词尾除阻"的句子，标准答案（原始合成）在同一位置放进同一段供体（出片程序的 _graft，同一个函数）——
# 复核把它当原始声音的一部分，其余部分照旧逐样本比对；移植本身（位置、强度）由 词尾辅音核对.py 把关。
from clean import clean_tail, SR
import hashlib as _hl
SPEED = 0.95
exec(_src[_src.index('SIL_DB=-55'):_src.index('def _purify(x):')])
exec(_src[_src.index('def _head_offset(raw,w):'):_src.index('LAST={}')])
exec(_src[_src.index('DONOR={'):_src.index('def sentence_audio(sent,pieces,gaps):')])


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
    # A23 读音改正：标准答案（原始合成）与成片用同一份读音改正表（读错的词按正确音标合成），复核其余部分照旧逐样本比对
    KT = k; _a = _src.index('# A23 读音改正'); _b = _src.index('k.create=_pron(k.create)')
    exec(_src[_a:_b] + 'k.create=_pron(k.create)\n')
    V = np.load(S + '/tts/voice_mb.npy')
    meta = {}
    # A22 淡入淡出的位置：出片程序写在 work_NN/淡入淡出.json（原始合成里的样本位置：淡出起点、切点、淡入终点）
    FADES = {no: (json.load(open(f'{S}/video/work_{no}/淡入淡出.json')) if os.path.exists(f'{S}/video/work_{no}/淡入淡出.json') else {}) for no in sys.argv[1:]}
    for no in sys.argv[1:]:
        d, items = texts_for(no)
        meta[no] = []
        for it in items:
            idx = it[1]
            text = it[2]
            gr = d.get('词尾除阻', {}).get('标题' if idx < 0 else f'S{idx + 1}')
            en_ = d.get('结尾句', {}).get(f'S{idx + 1}') if idx >= 0 else None
            # 标准答案的缓存键 = 这一句实际合成用的全部输入（音标含读音改正、移植、结尾句参数）的指纹：
            # 任何一项变了就重新合成（2026-10-10：07 S4 读音改正后仍用了旧读音的缓存，复核整篇对不上）
            fd_ = FADES.get(no, {}).get(f'S{idx + 1}', []) if idx >= 0 else []
            key_ = _hl.md5(repr((phonemes_of(spoken(text)), gr, en_, fd_, 0.95)).encode()).hexdigest()[:10]
            fn = f'{OUT}/{no}_{"T" if idx < 0 else "%02d" % idx}_{key_}.npy'
            if not os.path.exists(fn):
                if en_: a, sr = _ending_raw(text, en_), 24000     # 结尾句：两遍合成在接点接起来（与出片同一个函数，接点两侧必须是静音）
                else: a, sr = k.create(spoken(text), voice=V, speed=0.95, lang='en-us')
                assert sr == 24000
                a = np.asarray(a, np.float32)
                if gr:
                    w0 = clean_tail(a); st = _head_offset(a, w0); wg = _graft(_keep_tail(a, w0, st), gr, text)
                    end = max(len(a), st + max(int(round(float(sec) * SR)) + len(_donor(kd)) for sec, kd in gr.values()))
                    a = np.concatenate([a, np.zeros(end - len(a), np.float32)])
                    for sec, kd in gr.values():
                        p0 = int(round(float(sec) * SR)); n0 = len(_donor(kd)); a[st + p0:st + p0 + n0] = wg[p0:p0 + n0]
                for s0, c0, e0 in fd_:      # A22：连读处插停顿的淡出/淡入（与出片同一条曲线、同一位置；其余样本照旧逐样本比对）
                    a[s0:c0] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, c0 - s0))).astype(np.float32)
                    a[c0:e0] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, e0 - c0))).astype(np.float32)
                np.save(fn, a)
            meta[no].append({'idx': idx, 'text': text, 'file': fn,
                             'para': it[3] if len(it) > 3 else None,
                             'chunks': it[4] if len(it) > 4 else [text]})
            print(no, idx, text[:70], flush=True)
        json.dump(meta[no], open(f'{OUT}/{no}_meta.json', 'w'), indent=1, ensure_ascii=False)
