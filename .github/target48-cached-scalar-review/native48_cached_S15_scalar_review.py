"""Read only cached original S15; expose numbers, never raw arrays or a final claim."""
from pathlib import Path
import argparse, ast, copy, hashlib, importlib.util, json, math, os, sys, tempfile, traceback

p = argparse.ArgumentParser()
for key in ('tools', 'video-root', 'request', 'output', 'public-output'):
    p.add_argument('--' + key, type=Path, required=True)
a = p.parse_args()
T, root = a.tools.resolve(), a.video_root.resolve()
W, cache = root / 'video', root / 'tts/cache_tts'
pub = a.public_output
pub.mkdir(parents=True, exist_ok=True)
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
REQUEST = '547d5934a21304911f6e2ed5d81a78ea3b43554f371eb51a00730a5766986da7'
FILES = {
    '3d2776ec4567d58a25236c22d669506f238edb1d.pkl': '72dac0c779f56e73c33d4c6d2f7992acab2483d4b1f3b96e69f96e0bccc8a148',
    '3d2776ec4567d58a25236c22d669506f238edb1d.pkl.单线程': '9a314c4af977b027421a08fa66018bbfee4dd8a721b193a32184bd1cd9e5707c',
    '2e780fe5d9534eaf29b922271342d8f40cf7d5e6.pkl': '8cb96a1a2ec756d7976ed4cc831df0468912d0c0e287962b8d1a013e2610e737',
    '2e780fe5d9534eaf29b922271342d8f40cf7d5e6.pkl.单线程': 'dea2bd5574d1dfc959d0053b0b0109e1d9213196375dfb353d417ad5c6a265a2',
    '调平_d3ee28c1a0d096e2302fb782cbd15f5b853f1116.json': '97a5f23cc0e52dfaecc16f35e57b6adcf5c6c538b0c45f4bf2974e471f332be2',
}
assert os.environ.get('STRICT_CACHE') == '1'
assert os.environ.get('XG_NOPUSH') == '1'
assert sha(a.request) == REQUEST
assert {name: sha(cache / name) for name in FILES} == FILES
assert sha(W / 'make_video.py') == '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
MODEL_FILES = {'kokoro-v1.0.onnx': '7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5',
    'kokoro-v1.0-timed.onnx': 'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
    'voices-v1.0.bin': 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d',
    'voice_mb.npy': '1f97658bb5a4280cc3f6c01dc644dff471bf57c970fc8b99f3049d6991c4f6c8'}
assert {name: sha(root/'tts'/name) for name in MODEL_FILES} == MODEL_FILES
inventory = lambda: {path.name: sha(path) for path in cache.iterdir() if path.is_file()}
cache_before = inventory()
wav_before = {str(path): sha(path) for path in W.glob('work_*/a.wav')}
request = json.loads(a.request.read_text())
source = W / 'scripts/48.json'
source.parent.mkdir(exist_ok=True)
prior = source.read_bytes() if source.exists() else None
source.write_bytes(a.request.read_bytes())
report = {'article': '48', 'sentence': 'S15', 'kind': 'strict-cached-original-S15-scalar-review',
          'request_sha256': REQUEST, 'helper_sha256': sha(__file__), 'quality_acceptance': False,
          'new_inference_forbidden': True, 'formal_source_or_GEN_modified': False,
          'raw_GT_models_not_exported': True, 'required_private_cache_files': FILES}

try:
    os.chdir(W)
    sys.path.insert(0, str(W))
    spec = importlib.util.spec_from_file_location('cached48_original_maker_scalar', W / 'make_video.py')
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    m._REPO_CACHE = str(root / 'forbid-native48-public-cache-export')
    assert not Path(m._REPO_CACHE).exists()
    np, SR = m.np, m.SR
    sent = ' '.join(m.R.strip_gloss(c['en']).replace('**', '').strip() for c in request['sentences'][14]['chunks'])
    expected = "Yuan Longping, who shared the 2004 World Food Prize with Sierra Leone's Monty Jones, died in Changsha on 22 May 2021, aged 91."
    assert sent == expected
    calls = []
    for method, obj in (('create', m.k), ('create_timed', m.KT)):
        original = getattr(obj, method)
        def guarded(text, *args, _fn=original, _method=method, **kwargs):
            assert text == m.spoken(sent), ('unexpected model input', _method, text)
            calls.append(_method)
            return _fn(text, *args, **kwargs)
        setattr(obj, method, guarded)
    raw, _ = m.k.create(m.spoken(sent), voice=m.V, speed=m.SPEED, lang='en-us')
    timed, _, tokens = m.KT.create_timed(m.spoken(sent), voice=m.V, speed=m.SPEED, lang='en-us', clause_pause=0, sentence_pause=0)
    assert hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest() == 'e78bd7defdc2063a4402c4138a9157094a97f855d88f8da2fd39226c4fbc93c8'
    assert hashlib.sha256(np.ascontiguousarray(timed).tobytes()).hexdigest() == '73b8b9bc554e9aa4a422c8c3226c8299d5b53a5b1982d3c576f96dd722caf156'
    w = m.clean_tail(raw)
    kept = m._keep_tail(raw, w, m._head_offset(raw, w))
    assert hashlib.md5(np.ascontiguousarray(kept).tobytes()).hexdigest()[:12] == '1e7b42ae3b36'
    report['original_clean_tail_and_keep_tail_arrays_equal'] = bool(np.array_equal(w, kept))
    head, scale = m._head_offset(raw, w), len(raw) / len(timed)
    # Extract the unchanged original scalar functions, without running its CLI/model setup.
    original_window = T / '逐段看声音.py'
    tree = ast.parse(original_window.read_text())
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('per', 'spec')]
    ns = {'np': np, '__builtins__': __builtins__}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(original_window), 'exec'), ns)
    per, spectrum = ns['per'], ns['spec']
    F5 = int(0.005 * SR)
    ref = float(np.sqrt(np.mean(w[:len(w)//F5*F5].reshape(-1, F5)**2, axis=1)).max())
    def lv(x):
        return float(20*np.log10(np.sqrt(np.mean(x**2))/ref+1e-9)) if len(x) else -99.0
    report['original_window_program_sha256'] = sha(original_window)
    report['raw_w_fingerprint'] = '1e7b42ae3b36'
    report['raw_clean_w_seconds'] = len(w) / SR
    report['scalar_windows'] = []
    for start, end in ((0.75, 1.25), (6.25, 7.4), (10.95, 11.85)):
        near = [{'phoneme': token.phoneme, 'start_s': (token.start*scale*SR-head)/SR,
                 'end_s': (token.end*scale*SR-head)/SR} for token in tokens
                if token.phoneme.strip() and (token.end*scale*SR-head)/SR > start-.2
                and (token.start*scale*SR-head)/SR < end+.2]
        rows = []
        for t in np.arange(start, end, .0025):
            i = int(round(float(t)*SR))
            x = w[i:i+60]
            centroid, low = spectrum(w[max(0, i-90):i+150]) if i > 90 else (0, 0)
            rows.append({'w_s': round(float(t), 6), 'dB_relative_max5ms': lv(x),
                         'previous5ms_dB': lv(w[max(0,i-120):i]), 'next5ms_dB': lv(w[i:i+120]),
                         'periodicity20ms': per(w[max(0,i-210):i+270]),
                         'low150Hz_fraction_dB': low, 'centroid10ms_Hz': centroid,
                         'zero_crossings_w_s': [round((i+j)/SR, 6) for j in range(1,len(x)) if x[j-1]*x[j]<=0][:4]})
        report['scalar_windows'].append({'window_w_s': [start, end], 'nearby_timed_phonemes': near,
                                         'timed_estimate_error_s': 0.05, 'rows': rows})
    # Apply only original A45 invalidation inside this diagnostic module, never on formal source.
    os.environ['OLD_IV_VOID'] = '1'
    pieces, gaps, p0, listing = [], [], 0, m.list_commas(sent)
    for mm in m.re.finditer(r'[,;:](?=\s)', sent):
        pieces.append((p0, mm.end()))
        p0 = mm.end()+1
        gaps.append(m.P_LIST if mm.start() in listing else m.P_COMMA)
    pieces.append((p0, len(sent)))
    clips, tmap = m.sentence_audio(sent, pieces, gaps)
    base_clips = [x.copy() for x in clips]
    base, base_wave, base_auto, base_manual = m.句增益(request, '48', 14, sent, pieces, gaps,
                                                     [x.copy() for x in base_clips], tmap, np.concatenate(base_clips))
    candidate = copy.deepcopy(request)
    assert not candidate.get('分段增益dB', {}).get('S15')
    candidate.setdefault('分段增益dB', {})['S15'] = {'1': 1.0}
    new, new_wave, new_auto, new_manual = m.句增益(candidate, '48', 14, sent, pieces, gaps,
                                               [x.copy() for x in base_clips], tmap, np.concatenate(base_clips))
    assert base_auto == new_auto == {1: -6.0}
    assert len(base_wave) == len(new_wave)
    report['diagnostic_only_A45_voided'] = m.VOIDED
    report['old_NV_not_reused'] = sent not in m.NONVOICE
    report['baseline_and_plus1_piece_levels'] = []
    for i, (c0,c1,t0,t1) in enumerate(tmap):
        row = {'piece': i+1, 'text': sent[c0:c1], 'span_s': [t0,t1]}
        for label, wave in (('baseline', base_wave), ('only_piece1_plus1dB', new_wave)):
            x = wave[round(t0*SR):round(t1*SR)].astype(float)
            row[label] = {'RMS_dBFS': 20*math.log10(float(np.sqrt(np.mean(x*x)))+1e-20),
                          'peak_dBFS': 20*math.log10(float(np.max(np.abs(x)))+1e-20)}
        row['piece_samples_exact_between_candidates'] = bool(np.array_equal(base[2*i], new[2*i]))
        report['baseline_and_plus1_piece_levels'].append(row)
    diff = np.flatnonzero(base_wave != new_wave)
    first_end = round(tmap[0][3]*SR)
    assert len(diff) and int(diff[-1]) < first_end
    assert np.array_equal(base_wave[first_end:], new_wave[first_end:])
    report['changed_samples_only_first_piece'] = {'count': len(diff), 'first_sample': int(diff[0]),
        'last_sample': int(diff[-1]), 'first_piece_end_sample': first_end,
        'all_later_samples_exact': True, 'processed_samples': len(base_wave)}
    report['raw_punctuation_cuts_unchanged'] = [list(x) for x in m.LAST['cuts']]
    report['automatic_gains_unchanged'] = {str(k): v for k,v in base_auto.items()}
    report['diagnostic_manual_plus1_only'] = new_manual
    # Two real original EBU meter calls in private temporary space, identical reference.
    loud_spec = importlib.util.spec_from_file_location('only48_original_loudness_scalar', T/'响度一致性核对.py')
    LQ = importlib.util.module_from_spec(loud_spec)
    loud_spec.loader.exec_module(LQ)
    common_peak = max(float(np.max(np.abs(base_wave))), float(np.max(np.abs(new_wave))))
    assert common_peak == float(np.max(np.abs(base_wave))) == float(np.max(np.abs(new_wave)))
    report['original_LU_meter_comparison'] = {'program_sha256': sha(T/'响度一致性核对.py'),
        'two_actual_ffmpeg_calls': True, 'same_reference_peak': common_peak,
        'original_source48_short_equivalent_mode': LQ.短起('48'),
        'original_adjacent_limit_LU_unchanged': LQ.IN_ADJ, 'not_whole_track_gate': True, 'candidates': {}}
    with tempfile.TemporaryDirectory(prefix='_48scalarLU_', dir=W) as temporary:
        for label, wave in (('baseline', base_wave), ('only_piece1_plus1dB', new_wave)):
            path = Path(temporary)/(label+'.wav')
            padded = np.concatenate([np.zeros(round(.5*SR),np.float32),wave,np.zeros(round(.5*SR),np.float32)])
            m.sf.write(path, padded/common_peak*.89, SR)
            TM = LQ.momentary(str(path))
            values = []
            for i, (_,_,t0,t1) in enumerate(tmap):
                value = LQ.等效(LQ.段响度(TM,.5+t0,.5+t1),t0,t1,LQ.短起('48'))
                _, peak400 = LQ.段量(TM,.5+t0,.5+t1)
                values.append({'piece': i+1, 'original_BS1770_gated_LUFS': float(value) if value is not None else None,
                               'original_maximum400ms_LUFS': float(peak400)})
            deltas = [values[i]['original_BS1770_gated_LUFS']-values[i-1]['original_BS1770_gated_LUFS']
                      if values[i]['original_BS1770_gated_LUFS'] is not None and values[i-1]['original_BS1770_gated_LUFS'] is not None
                      else None for i in range(1,len(values))]
            report['original_LU_meter_comparison']['candidates'][label] = {'pieces': values,
                'adjacent_LU_differences': deltas,
                'all_adjacent_within_original_2_5_LU': all(v is not None and abs(v)<=LQ.IN_ADJ for v in deltas)}
    # Original isolated sentence scanner is diagnostic context, not whole-track acceptance.
    pv_spec = importlib.util.spec_from_file_location('only48_original_purevoice_scalar', T/'纯人声核对.py')
    pv = importlib.util.module_from_spec(pv_spec)
    pv_spec.loader.exec_module(pv)
    local = base_wave / max(1e-12, float(np.max(np.abs(base_wave)))) * .89
    findings = pv.scan(local)
    report['original_sentence_only_purevoice_scan'] = {'program_sha256': sha(T/'纯人声核对.py'),
        'not_whole_track_gate': True, 'findings': [list(x) for x in findings]}
    # Every original raw punctuation delete is independently described by actual scalar envelope.
    report['punctuation_deleted_raw_regions'] = []
    env = m._env5(w)
    for left, right, gap in m.LAST['cuts']:
        i0, i1 = int(left)//F5, int(right)//F5
        report['punctuation_deleted_raw_regions'].append({'raw_sample_span':[left,right],
            'raw_seconds':[left/SR,right/SR], 'inserted_gap_s':gap,
            'maximum5ms_relative_dB': float(env[i0:i1].max()) if i1>i0 else None,
            'first_kept_next5ms_relative_dB':float(env[i1]) if i1<len(env) else None})
    report['original_cache_only_model_calls'] = calls
    report['all_other_sentences_not_requested'] = True
    report['scalar_diagnostic_completed'] = True
except BaseException as e:
    report['scalar_diagnostic_completed'] = False
    report['error'] = {'type': type(e).__name__, 'detail': str(e)}
    traceback.print_exc()
finally:
    assert inventory() == cache_before, 'private cache changed during strictly cached read-only diagnostic'
    assert {path: sha(path) for path in wav_before} == wav_before
    if prior is None:
        source.unlink()
    else:
        source.write_bytes(prior)
    report['all_private_cache_files_exact_before_after'] = True
    report['all_existing_work_PCM_exact_before_after'] = True
    report['formal_request_and_source_bytes_restored_exact'] = True
    out = json.dumps(report, ensure_ascii=False, indent=2, default=lambda x: x.item())+'\n'
    a.output.write_text(out)
    (pub/'48-cached-S15-scalar-review.json').write_text(out)
    print(json.dumps({k:v for k,v in report.items() if k not in ('scalar_windows','required_private_cache_files')}, ensure_ascii=False, default=lambda x: x.item()))
sys.exit(0 if report.get('scalar_diagnostic_completed') else 1)
