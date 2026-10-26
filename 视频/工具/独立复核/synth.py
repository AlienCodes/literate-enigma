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
    import onnxruntime as _ort, pickle as _pk
    TTS = S + '/tts'; _CACHE = TTS + '/cache_tts'
    exec(_src[_src.index('def _portable_mid(model):'):_src.index('def _cached(obj,meth,model):')])   # 与出片程序同一套：缓存钥匙、老条目指纹清单、条目核对（G72）
    _so = _ort.SessionOptions(); _so.intra_op_num_threads = 1; _so.inter_op_num_threads = 1   # 单线程：新条目在任何机器上逐样本可复现
    k = Kokoro.from_session(_ort.InferenceSession(TTS + '/kokoro-v1.0.onnx', _so, providers=['CPUExecutionProvider']), TTS + '/voices-v1.0.bin')
    _mid = _portable_mid(TTS + '/kokoro-v1.0.onnx'); _raw_create = k.create
    def _按缓存(text, voice, speed=1.0, lang='en-us', **kw):
        # 主会话 2026-10-26 定：老条目（多线程合成、在老条目指纹清单里）别的机器无法逐样本重合成 → 标准答案 = 核过指纹的缓存本身；
        # 新条目（带 .单线程 标记）→ 单线程现场重合成，真独立；指纹不符、没标记又不在清单 → 停（_条目核对）
        vh = _hl.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest() if not isinstance(voice, str) else voice
        p = f"{_CACHE}/{_hl.sha1(repr(('create', _mid, text, vh, float(speed), lang, sorted(kw.items()))).encode()).hexdigest()}.pkl"
        if os.path.exists(p):
            _条目核对(p)
            if not os.path.exists(p + '.单线程'):
                with open(p, 'rb') as f: return _pk.load(f)
        return _raw_create(text, voice=voice, speed=speed, lang=lang, **kw)
    k.create = _按缓存
    # A23 读音改正：标准答案（原始合成）与成片用同一份读音改正表（读错的词按正确音标合成），复核其余部分照旧逐样本比对
    KT = k; _a = _src.index('# A23 读音改正'); _b = _src.index('k.create=_pron(k.create)')
    exec(_src[_a:_b] + 'k.create=_pron(k.create)\n')
    V = np.load(S + '/tts/voice_mb.npy')
    meta = {}
    # A22 淡入淡出的位置：出片程序写在 work_NN/淡入淡出.json（原始合成里的样本位置：淡出起点、切点、淡入终点）
    FADES = {no: (json.load(open(f'{S}/video/work_{no}/淡入淡出.json')) if os.path.exists(f'{S}/video/work_{no}/淡入淡出.json') else {}) for no in sys.argv[1:]}
    SEGS = {no: (json.load(open(f'{S}/video/work_{no}/分段.json')) if os.path.exists(f'{S}/video/work_{no}/分段.json') else {}) for no in sys.argv[1:]}
    for no in sys.argv[1:]:
        d, items = texts_for(no)
        meta[no] = []
        for it in items:
            idx = it[1]
            text = it[2]
            gr = d.get('词尾除阻', {}).get('标题' if idx < 0 else f'S{idx + 1}')
            pg = d.get('停顿处除阻', {}).get(f'S{idx + 1}') if idx >= 0 else None
            bo = d.get('除阻加强', {}).get('标题' if idx < 0 else f'S{idx + 1}')
            en_ = d.get('结尾句', {}).get(f'S{idx + 1}') if idx >= 0 else None
            # 标准答案的缓存键 = 这一句实际合成用的全部输入（音标含读音改正、移植、结尾句参数）的指纹：
            # 任何一项变了就重新合成（2026-10-10：07 S4 读音改正后仍用了旧读音的缓存，复核整篇对不上）
            fd_ = FADES.get(no, {}).get(f'S{idx + 1}', []) if idx >= 0 else []
            sg_ = float(d.get('句子增益dB', {}).get(f'S{idx + 1}', 0)) if idx >= 0 else 0.0   # 2026-10-21 单句增益（与出片同一个数，整句乘）
            pn_ = d.get('分段增益dB', {}).get(f'S{idx + 1}') if idx >= 0 else None   # 2026-10-25 句内分段增益：同一个数，乘在原始合成里出片程序记下的那一段（work_NN/分段.json）
            pr_ = []
            if pn_:
                sr_ = SEGS.get(no, {}).get(f'S{idx + 1}')
                if not sr_: raise SystemExit(f'【停止】脚本写了分段增益dB，出片程序却没有记下分段位置（work_{no}/分段.json）：S{idx + 1}')
                pr_ = [(r['原始'][0], r['原始'][1], float(pn_[str(r['段'])])) for r in sr_ if str(r['段']) in pn_]
                if len(pr_) != len(pn_): raise SystemExit(f'【停止】分段增益dB 的段号在分段记录里找不到：S{idx + 1}')
            sr2_ = SEGS.get(no, {}).get(f'S{idx + 1}') if idx >= 0 else None
            if sr2_ and any('增益' in r for r in sr2_):   # G36 源头调平（26 起）：出片程序自动算的增益 + 脚本写的，记在分段.json 的“增益”里；有它就以它为准
                pr_ = [(r['原始'][0], r['原始'][1], float(r['增益'])) for r in sr2_ if r.get('增益')]
                if pn_ and any(abs(float(r.get('增益', 0)) - float(pn_.get(str(r['段']), 0))) > 1e-6 for r in sr2_) and not (str(d.get('no', no)).isdigit() and int(d.get('no', no)) >= 26):
                    raise SystemExit(f'【停止】分段记录的增益与脚本 分段增益dB 对不上（26 前没有自动调平）：S{idx + 1}')
            key_ = _hl.md5(repr((phonemes_of(spoken(text)), gr, en_, fd_, 0.95) + ((pg,) if pg else ()) + ((('加强', bo),) if bo else ()) + ((('增益', sg_),) if sg_ else ()) + ((('分段增益', pr_),) if pr_ else ()) + ((('合成标点', d.get('合成标点', {}).get(f'S{idx + 1}')),) if idx >= 0 and d.get('合成标点', {}).get(f'S{idx + 1}') else ())).encode()).hexdigest()[:10]
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
                if bo:      # A21 弱除阻加强：同一个函数（出片程序的 _boost），在原始合成的同一位置
                    a0_ = np.asarray(_ending_raw(text, en_) if en_ else k.create(spoken(text), voice=V, speed=0.95, lang='en-us')[0], np.float32)
                    a = _boost(a, bo, text, off=_head_offset(a0_, clean_tail(a0_)))
                for s0, c0, e0 in fd_:      # A22：连读处插停顿的淡出/淡入（与出片同一条曲线、同一位置；其余样本照旧逐样本比对）
                    a[s0:c0] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, c0 - s0))).astype(np.float32)
                    a[c0:e0] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, e0 - c0))).astype(np.float32)
                if pg:      # A21 连读处补除阻：原始合成里 w[p:q) 换成同一段供体（出片程序的 _pdonor，同一个函数）；停顿插在供体之后，复核照常认插入的静音
                    a0 = np.asarray(_ending_raw(text, en_) if en_ else k.create(spoken(text), voice=V, speed=0.95, lang='en-us')[0], np.float32)
                    w0 = clean_tail(a0); st = _head_offset(a0, w0); w0 = _keep_tail(a0, w0, st)
                    for p_, q_, kd in sorted(pg.values(), key=lambda v: -float(v[0])):
                        p0 = st + int(round(float(p_) * SR)); q0 = st + int(round(float(q_) * SR))
                        a = np.concatenate([a[:p0], _pdonor(w0, kd), a[q0:]])
                for p0_, p1_, g_ in pr_: a[p0_:min(p1_, len(a))] *= np.float32(10 ** (g_ / 20))
                if sg_: a = a * np.float32(10 ** (sg_ / 20))
                np.save(fn, a)
            meta[no].append({'idx': idx, 'text': text, 'file': fn,
                             'para': it[3] if len(it) > 3 else None, '分段增益': pr_,
                             'chunks': it[4] if len(it) > 4 else [text]})
            print(no, idx, text[:70], flush=True)
        json.dump(meta[no], open(f'{OUT}/{no}_meta.json', 'w'), indent=1, ensure_ascii=False)
