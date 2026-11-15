#!/usr/bin/env python3
"""Read-only, single-sentence original-cache diagnostic. Never synthesizes or builds video.

Run ONLY in the approved native cache runtime, after installing the exact current
source54 before fresh maker import. Output JSON contains scalar observations only;
no raw mother, processed audio, or model outputs are written/exported.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

SOURCE_SHA = '22da36911cc96e2fb42e33333e95c78b89af24bef8726f7e0fcf3ba6f40d7909'
MAKER_SHA = '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
VOICE_SHA = '1f97658bb5a4280cc3f6c01dc644dff471bf57c970fc8b99f3049d6991c4f6c8'
RAW_KEY = 'a737a6bd81c222f4a912323556cc656f7dbde97f.pkl'
RAW_PKL_SHA = '799e58a14fdc8953ae6fc52d855a4565a39c757c7c28ea8f4463600becd0af66'
RAW_ARRAY_SHA = '724010c16e1896c7c02f1385a70ed2717adc15dcbfe7a954a059b5ad04bbe02e'
TIMED_KEY = 'c305b1ea7890f64a199fd5b56ed85be8768e68d6.pkl'
INPUT_SHA = '575665755d9c8ffa6a9e59c441697f492f45c1d26e9c94e32536553261fead92'
SENTENCE = ('Tsunamis, reportedly over 30 metres high in places, '
            'swamped coastal settlements on Java and Sumatra.')
MODELS = {
    'kokoro-v1.0.onnx': '7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5',
    'kokoro-v1.0-timed.onnx': 'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
    'voices-v1.0.bin': 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d',
}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def inventory(p):
    return sorted(str(x.relative_to(p)) for x in p.rglob('*') if x.is_file())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runtime-work', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    work = Path(args.runtime_work).resolve()
    out = Path(args.out).resolve()
    maker = work.parent / 'make_video.py'
    tts = work.parent / 'tts'
    cache = tts / 'cache_tts'
    source = work / 'scripts/54.json'
    assert work.is_dir() and cache.is_dir(), 'Use the existing approved native runtime'
    assert sha_file(source) == SOURCE_SHA, 'Install actual current22da source54 before fresh import'
    assert sha_file(maker) == MAKER_SHA, 'Original maker only; no helper overlay'
    assert sha_file(tts / 'voice_mb.npy') == VOICE_SHA
    for name, expected in MODELS.items():
        assert sha_file(tts / name) == expected, name
    assert sha_file(cache / RAW_KEY) == RAW_PKL_SHA
    for name in (RAW_KEY, TIMED_KEY):
        p = cache / name
        assert p.is_file(), name
        assert Path(str(p) + '.单线程').read_text().strip() == sha_file(p)[:16], name
    assert os.environ.get('STRICT_CACHE') == '1', 'STRICT_CACHE=1 is mandatory'
    assert os.environ.get('CUTS') == '1', 'Use the current CUTS=1 contract'
    assert not any(os.environ.get(k) for k in ('OLD_IV_VOID', 'NEW_CACHE', 'AUDIO_ONLY'))
    scripts_before = {p.name: sha_file(p) for p in sorted((work / 'scripts').glob('*.json'))}
    assert len(scripts_before) >= 70, 'Preserve all other source scripts/context'
    cache_before = inventory(cache)
    out.parent.mkdir(parents=True, exist_ok=True)
    cache_log = out.parent / '54-S6-used-original-cache-keys.log'
    assert not cache_log.exists(), 'Use a fresh isolated output directory'
    os.environ['CACHE_LOG'] = str(cache_log)
    os.chdir(work)
    sys.path.insert(0, str(work.parent))
    sys.path.insert(0, str(work))
    # Original maker performs fresh source-first import, original timed cache,
    # original punctuation cuts, purification, and the cached G36 levels.
    spec = importlib.util.spec_from_file_location('source54_cached_onset_original_maker', maker)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    import numpy as np
    assert m.SR == 24000 and m.SPEED == .95
    assert 'afftdn=nf=-40:nr=4' in m.AF
    assert np.array_equal(m.V, np.load(tts / 'voice_mb.npy'))
    d = json.loads(source.read_text())
    texts = [re.sub(r'\*\*', '', m.R.strip_gloss(c['en'])).strip()
             for c in d['sentences'][5]['chunks']]
    sent = ' '.join(texts)
    assert sent == SENTENCE and str(d['no']) == '54'
    # This diagnostic is intentionally S6 only. Other sentences retain their
    # existing independent whole-native gates; no all-article replay here.
    assert sent not in m.ENDING and sent not in m.NONVOICE
    assert all(sent not in x for x in (m.GRAFT, m.PGRAFT, m.BOOST))
    assert not d.get('分段增益dB', {}).get('S6')
    assert not d.get('段内渐变dB', {}).get('S6')
    assert not d.get('句子增益dB', {}).get('S6')
    inp = m.spoken(sent)
    # The exact resulting cached key below additionally binds the original
    # pronunciation wrapper, full sentence, voice, speed, and original model.
    assert hashlib.sha256(inp.encode()).hexdigest() == INPUT_SHA
    raw, sr = m.k.create(inp, voice=m.V, speed=m.SPEED, lang='en-us')
    raw = np.asarray(raw)
    assert sr == 24000 and raw.dtype == np.float32 and raw.shape == (179712,)
    assert hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest() == RAW_ARRAY_SHA
    assert cache_log.read_text().splitlines() == [RAW_KEY]
    clean = m.clean_tail(raw)
    clean_head = m._head_offset(raw, clean)
    kept = m._keep_tail(raw, clean, clean_head)
    lst = m.list_commas(sent)
    pieces, gaps, p0 = [], [], 0
    for mm in re.finditer(r'[,;:](?=\s)', sent):
        pieces.append((p0, mm.end()))
        p0 = mm.end() + 1
        gaps.append(m.P_LIST if mm.start() in lst else m.P_COMMA)
    pieces.append((p0, len(sent)))
    clips, tmap = m.sentence_audio(sent, pieces, gaps)
    before_gain = [np.array(x, copy=True) for x in clips]
    last = copy.deepcopy(m.LAST)
    clips, final, agn, pgn = m.句增益(d, '54', 5, sent, pieces, gaps, clips, tmap,
                                  np.concatenate(clips))

    def arrsha(x):
        return hashlib.sha256(np.ascontiguousarray(x, np.float32).tobytes()).hexdigest()

    def db(x):
        return float(20 * np.log10(np.sqrt(np.mean(np.asarray(x, np.float64) ** 2)) + 1e-20)) if len(x) else None

    def frames(x, step_ms=5, end_ms=None):
        n = round(m.SR * step_ms / 1000)
        end = min(len(x), round(m.SR * end_ms / 1000)) if end_ms else len(x)
        return [{'ms': round(i / m.SR * 1000, 4), 'dbfs': db(x[i:i+n])}
                for i in range(0, end-n+1, n)]

    def scalar(x):
        fs = frames(x)
        return {'samples': int(len(x)), 'sha256_f32le': arrsha(x), 'rms_dbfs': db(x),
                'peak': float(np.max(np.abs(x))) if len(x) else 0,
                'first_200ms_5ms_frames': frames(x, end_ms=200),
                'peak_5ms_dbfs': max(z['dbfs'] for z in fs) if fs else None}

    used = cache_log.read_text().splitlines()
    assert RAW_KEY in used and TIMED_KEY in used
    assert set(k for k in used if k.endswith('.pkl')) == {RAW_KEY, TIMED_KEY}
    used_proofs = []
    for name in sorted(set(used)):
        assert (cache / name).is_file(), name
        p = cache / name
        r = {'name': name, 'bytes': p.stat().st_size, 'sha256': sha_file(p)}
        if name.endswith('.pkl'):
            r['single_thread_marker'] = Path(str(p) + '.单线程').read_text().strip()
            assert r['single_thread_marker'] == r['sha256'][:16]
        elif name.startswith('调平_'):
            r['existing_cached_gain_map'] = json.loads(p.read_text())
        used_proofs.append(r)
    assert cache_before == inventory(cache), 'Cache inventory changed: diagnostic must not create entries'
    assert scripts_before == {p.name: sha_file(p) for p in sorted((work / 'scripts').glob('*.json'))}
    # Report the original firstword onset, processing head positions, and
    # equal-duration RMS before/after G36; these are observations, not a gain fix.
    rg = frames(raw)
    maxr = max(z['dbfs'] for z in rg)
    first = {str(t): next((z['ms'] for z in rg if z['dbfs'] >= maxr+t), None)
             for t in (-55, -45, -35, -25)}
    report = {
        'article': 54, 'book_order': 47, 'user_requests': [147, 148],
        'purpose': 'Strict original-cache S6 Tsunamis onset diagnostic; no generation/fix/acceptance',
        'source_sha256': sha_file(source), 'maker_sha256': sha_file(maker),
        'fixed_voice_sha256': VOICE_SHA, 'model_sha256': MODELS,
        'strict_cache': os.environ['STRICT_CACHE'], 'cuts': os.environ['CUTS'],
        'sentence': sent, 'spoken_input_sha256': INPUT_SHA,
        'cache_inventory_unchanged': True, 'source_scripts_unchanged': True,
        'used_original_cache_proofs': used_proofs,
        'original_filter_chain': m.AF, 'raw_first_5ms_onsets_relative_to_peak_db': first,
        'clean_removed_head_samples': clean_head,
        'clean_removed_head_5ms_max_dbfs': max((z['dbfs'] for z in frames(raw[:clean_head])), default=None),
        'raw_mother': scalar(raw), 'after_clean_tail': scalar(clean),
        'after_keep_tail': scalar(kept), 'first_piece_before_gain': scalar(before_gain[0]),
        'first_piece_after_gain': scalar(clips[0]), 'whole_S6_after_existing_gain': scalar(final),
        'punctuation_pieces': [{'text': sent[a:b], 'before_gain': scalar(before_gain[2*i]),
                                'after_gain': scalar(clips[2*i])}
                               for i, (a, b) in enumerate(pieces)],
        'cached_auto_gain_db': agn, 'manual_gain_db': pgn,
        'timemap': tmap, 'original_processing': {
            k: last[k] for k in ('head', 'segs', 'total', 'cuts', 'grafts', 'gaps', 'fades', 'hs')},
        'first_timed_phonemes': [{'phoneme': t.phoneme, 'start': float(t.start), 'end': float(t.end)}
                                for t in last['toks'][:35]],
        'new_gain_applied': False, 'video_built': False,
        'raw_mother_written_or_exported': False, 'public_pcm_exported': False,
        'human_listening_claim': False, 'final_acceptance': False,
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2,
                              default=lambda x: x.item() if isinstance(x, np.generic) else str(x)) + '\n')
    print(json.dumps({'report': str(out), 'bytes': out.stat().st_size,
                      'sha256': sha_file(out), 'final_acceptance': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
