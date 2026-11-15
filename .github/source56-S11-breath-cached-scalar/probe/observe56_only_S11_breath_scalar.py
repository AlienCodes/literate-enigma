"""CODE ONLY: one exact cached S11; original acoustic algorithms, scalar output.

The caller initializes a NEW isolated W with the frozen source bytes. This probe
never installs or writes a source, creates audio, runs a whole build, accepts a
cut, synthesizes, or computes missing gain mathematics.
"""
from pathlib import Path
import argparse, ast, contextlib, copy, gc, hashlib, importlib.util, io, json
import math, os, sys, traceback

PROFILE_SHA256 = '1dd0651c9c27bb34977334bb9bc7410b3b54dce978f2f971e46c7a1605dc7fc7'
SOURCE_NO, BOOK_ORDER, TARGET = '56', 65, 'S11'
DISPLAY = 'The compromise, struck without Wallace, may have kept rivalry over precedence at bay.'
PROJECTED = 'The compromise struck without Wallace, may have kept rivalry over precedence at bay.'
ENVELOPE = [1.95, 2.70]
MATH_NAME = '调平_22842078959011da4b6986b549453b7eafee80d9.json'
MATH_SHA = '98c2e92f9fe36307e60e0a857a97d5595015278b2add1fed2bcea10248eb43d6'
FLAGS = ['STRICT_CACHE', 'XG_NOPUSH', 'AUDIO_ONLY', 'XG_KEEP_REVIEWED_GAIN',
         'XG_KEEP_REVIEWED_ENDING', 'XG_KEEP_REVIEWED_CUTS']
OVERRIDES = ['VOICE', 'AFFILE', 'OLD_IV_VOID', 'ONLY', 'BREATH_FRAC', 'CACHE_LOG']


def require(value, message):
    if not value:
        raise AssertionError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def typed(value):
    if isinstance(value, dict):
        return ('dict', tuple((key, typed(item)) for key, item in value.items()))
    if isinstance(value, (tuple, list)):
        return (type(value).__name__, tuple(typed(item) for item in value))
    return (type(value).__name__, value)


def real_file(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), 'A pinned input must be a regular non-symlink file: ' + str(p))
    return p


def inventory(path):
    p = Path(path)
    require(p.is_dir() and not p.is_symlink(), 'Inventory requires an existing real directory')
    return {x.name: digest(real_file(x)) for x in p.iterdir() if x.is_file()}


def directory_snapshot(path):
    p = Path(path)
    if not os.path.lexists(p):
        return {'exists': False}
    require(p.is_dir() and not p.is_symlink(), 'Snapshot directory must be real')
    files = {}
    for x in sorted(p.rglob('*')):
        require(not x.is_symlink(), 'Do not follow a work/source symlink')
        if x.is_file():
            files[str(x.relative_to(p))] = {'bytes': x.stat().st_size, 'sha256': digest(x)}
    return {'exists': True, 'inode': p.stat().st_ino, 'files': files}


def load_module(name, path):
    require(name not in sys.modules, 'Fresh diagnostic module name required')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bind_inputs(folder, profile):
    bound = {}
    for role, row in profile['inputs'].items():
        rel = Path(row['file'])
        require(not rel.is_absolute() and '..' not in rel.parts, 'Input escaped frozen namespace')
        p = real_file(Path(folder) / rel)
        require(p.stat().st_size == row['bytes'] and digest(p) == row['sha256'], 'Wrong frozen input ' + role)
        bound[role] = p
    return bound


def runtime_local_paths(T, M, W, expected):
    """Use original G27 precedence (../tts, W); pin full bytes before import."""
    result = {}
    for name, wanted in expected.items():
        require(name and '/' not in name and '\\' not in name and '.' not in name, 'Only finite local module basenames')
        require(digest(real_file(Path(T) / (name + '.py'))) == wanted, 'Original T runtime module differs: ' + name)
        choices = [Path(W) / (name + '.py')] if name == 'make_video' else [Path(M) / 'tts' / (name + '.py'), Path(W) / (name + '.py')]
        actual = next((p for p in choices if os.path.lexists(p)), None)
        require(actual is not None and digest(real_file(actual)) == wanted, 'Actual original G27 runtime module missing/changed: ' + name)
        result[name] = actual.resolve()
    return result


def verify_loaded_local_modules(paths, expected):
    result = {}
    for name, path in paths.items():
        if name == 'make_video' or name not in sys.modules:
            continue
        module = sys.modules[name]
        actual = real_file(getattr(module, '__file__', ''))
        require(actual.resolve() == path and digest(actual) == expected[name], 'Loaded actual module path/bytes differ: ' + name)
        result[name] = {'file': str(actual), 'sha256': digest(actual)}
    return result


def validate_data(profile, source, actual):
    require((profile['source_id'], profile['book_order'], profile['target_sentence']) ==
            (SOURCE_NO, BOOK_ORDER, TARGET), 'Wrong exact target profile')
    require(str(source.get('no')) == SOURCE_NO and len(source['sentences']) == 17, 'Wrong source or sentence count')
    sent = ' '.join(c['en'].replace('**', '') for c in source['sentences'][10]['chunks'])
    require(sent == DISPLAY, 'Exact unmodified S11 display and both commas required')
    require(typed(source.get('朗读删逗号', {}).get(TARGET)) == typed(
        {'篇号': 56, '原文': DISPLAY, '逗号序号': [1]}), 'Only first spoken comma may be removed')
    require(profile['probe_envelope_w_seconds'] == ENVELOPE and profile['BREATH_FRAC'] == .70,
            'No envelope or original threshold change is authorized')
    # The complete source SHA is bound before this function. This additional
    # equality makes unknown target DSP fail independently of known-key loops.
    target = {k: copy.deepcopy(v.get(TARGET)) for k, v in source.items()
              if isinstance(v, dict) and TARGET in v}
    require(typed(target) == typed(profile['all_source_top_dict_target_entries']), 'Unknown or changed target controls')
    require(actual['source_id'] == SOURCE_NO and actual['book_order'] == BOOK_ORDER and
            actual['diagnostic_completed'] is True and actual['errors'] == [], 'Real completed actual native reference required')
    phase = actual['phases']['selected']
    require(phase['source_sha256'] == profile['inputs']['source']['sha256'], 'Actual reference is for a different source')
    require(phase['actual_complete_WAV']['file_sha256'] == profile['actual_whole_WAV_sha256'] and
            phase['actual_complete_WAV']['file_md5'] == profile['actual_whole_WAV_md5'], 'Wrong existing whole evidence role')
    require(typed(phase['observed_sentences'][TARGET]) == typed(profile['actual_target_observation']),
            'Exact current native target evidence required')
    require(typed(profile['existing_G36']) == typed({'name': MATH_NAME, 'sha256': MATH_SHA}), 'Only one existing original G36 key')
    return sent, phase


def require_existing_math(cache, key):
    require(key is not None and '调平_' + key + '.json' == MATH_NAME, 'Unknown G36 key; never calculate')
    p = real_file(Path(cache) / MATH_NAME)
    require(digest(p) == MATH_SHA, 'Missing/changed original G36; never calculate')
    return p


def validate_model_tuple(m, np, text, voice, speed, lang, kw, method, sent):
    require(os.environ.get('STRICT_CACHE') == '1' and text == m.spoken(sent) == DISPLAY and
            type(speed) is float and speed == .95 and lang == 'en-us' and
            np.array_equal(voice, m.V), 'Only the exact current S11 cache tuple is authorized')
    expected = {} if method == 'create' else {'clause_pause': 0, 'sentence_pause': 0}
    require(method in ('create', 'create_timed') and typed(kw) == typed(expected), 'Wrong exact target typed kwargs')


def target_model_guard(m, cache, method, model, original, sent, entries, used):
    np = m.np
    def guarded(text, voice, speed=1.0, lang='en-us', **kw):
        validate_model_tuple(m, np, text, voice, speed, lang, kw, method, sent)
        seen = []
        def capture(actual_text, voice, speed=1.0, lang='en-us', **actual_kw):
            row = entries[method]
            mid = m._portable_mid(str(Path(cache).parent / model))
            vh = hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
            key = hashlib.sha1(repr((method, mid, actual_text, vh, float(speed), lang,
                                       sorted(actual_kw.items()))).encode()).hexdigest() + '.pkl'
            require(key == row['name'] and actual_text == PROJECTED, 'Unexpected post-pron cache key/text')
            p, marker = real_file(Path(cache) / key), real_file(Path(cache) / row['marker_name'])
            require(digest(p) == row['pkl_SHA256'] and digest(marker) == row['marker_SHA256'] and
                    marker.read_text().strip() == row['marker_value'], 'Only exact saved mother and marker may be read')
            m._条目核对(str(p))
            seen.append({'method': method, 'name': key, 'pkl_sha256': digest(p),
                         'post_pron_input_sha256': hashlib.sha256(actual_text.encode()).hexdigest(),
                         'kwargs': actual_kw})
        m._pron(capture)(text, voice=voice, speed=speed, lang=lang, **kw)
        require(len(seen) == 1, 'Original pronunciation capture ABI changed')
        value = original(text, voice=voice, speed=speed, lang=lang, **kw)
        row = entries[method]
        array = value[0]
        require(str(array.dtype) == row['dtype'] and len(array) == row['samples'] and
                hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest() == row['array_SHA256'],
                'Existing cached mother ndarray differs')
        if method == 'create_timed':
            require(len(value) == 3 and len(value[2]) == row['timed_token_count'], 'Cached timed-token ABI changed')
        used.append(seen[0])
        return value
    return guarded


@contextlib.contextmanager
def process_state(work, support, restoration, module_names=()):
    """Restore process state even when an original diagnostic or guard raises."""
    modules, env = dict(sys.modules), dict(os.environ)
    cwd, path, trace, bytecode = Path.cwd(), list(sys.path), sys.gettrace(), sys.dont_write_bytecode
    try:
        require(trace is None, 'Do not replace an unknown active trace hook')
        sys.dont_write_bytecode = True
        for name in set(('render', 'title2', 'clean', '出片指纹', '响度一致性核对')) | set(module_names):
            sys.modules.pop(name, None)
        with support.environment_and_cwd(work, restoration):
            yield
    finally:
        sys.settrace(trace)
        os.chdir(cwd)
        sys.path[:] = path
        os.environ.clear(); os.environ.update(env)
        sys.dont_write_bytecode = bytecode
        for name in set(sys.modules) - set(modules):
            sys.modules.pop(name, None)
        sys.modules.update(modules)
        restoration['all_process_modules_restored'] = (set(sys.modules) == set(modules) and
            all(sys.modules[k] is v for k, v in modules.items()))
        restoration['trace_cwd_path_environment_bytecode_restored'] = (sys.gettrace() is trace and
            Path.cwd() == cwd and sys.path == path and dict(os.environ) == env and sys.dont_write_bytecode is bytecode)


def original_dossier_parts(path, expected_sha, np, SR, env5, aud_db):
    require(digest(path) == expected_sha, 'Wrong original dossier bytes')
    tree = ast.parse(Path(path).read_text())
    names = {'to_w', 'words', 'per', 'spec', 'breath_after'}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require(len(nodes) == len(names), 'Original dossier function ABI changed')
    candidates = [n for n in tree.body if isinstance(n, ast.For) and
                  isinstance(n.target, ast.Name) and n.target.id == 'it' and
                  isinstance(n.iter, ast.Name) and n.iter.id == 'info']
    require(len(candidates) == 1, 'Unique original A19 candidate loop required')
    ns = {'np': np, 'SR': SR, 'F5': int(.005 * SR), '_env5': env5, 'AUD_DB': aud_db,
          'BREATH_GAP': .10}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    return ns, candidates[0]


def original_auto_loop(path, expected_sha):
    require(digest(path) == expected_sha, 'Wrong original automatic-cut bytes or threshold')
    tree = ast.parse(Path(path).read_text())
    loops = [n for n in tree.body if isinstance(n, ast.For) and
             isinstance(n.target, ast.Tuple) and [x.id for x in n.target.elts] == ['n_', 'c']]
    require(len(loops) == 1, 'Unique original candidate loop required')
    loop = loops[0]
    gates = [n for n in ast.walk(loop) if isinstance(n, ast.If) and any(
        isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == 'get' and
        x.args and isinstance(x.args[0], ast.Constant) and x.args[0].value == 'BREATH_FRAC'
        for x in ast.walk(n.test))]
    require(len(gates) == 1, 'Unique original unchanged breath gate required')
    # Compilation uses the original AST unchanged; trace only reads its state.
    require(ast.dump(loop, include_attributes=True) == ast.dump(loops[0], include_attributes=True), 'AST inverse differs')
    return loop, gates[0].lineno


def frame_profile(np, SR, w, ns, start, stop, ref):
    rows = []
    for i in range(start, stop - 60, 60):
        x = w[i:i + 60]
        centroid, low = ns['spec'](w[max(0, i - 90):i + 150])
        periodicity = ns['per'](w[max(0, i - 210):i + 270])
        level = float(20 * np.log10(np.sqrt(np.mean(x ** 2)) / ref + 1e-9))
        zc = [(i + j) / SR for j in range(1, len(x)) if x[j - 1] * x[j] <= 0]
        rows.append({'sample': i, 'w_s': i / SR, 'dB_2p5ms': level,
            'centroid_Hz': centroid, 'below150Hz_dB': low, 'periodicity20ms': periodicity,
            'audible_original_gt_minus50dB': bool(level > -50),
            'breath_original_predicate': bool(1800 < centroid < 3800 and low < -10 and periodicity < .35),
            'all_zero_crossing_w_s': zc})
    return rows


def observe_original_automatic(path, expected_sha, np, SR, info, cands, dossier_ns, nonvoice):
    loop, gate_line = original_auto_loop(path, expected_sha)
    ns = dict(dossier_ns, np=np, SR=SR, F5=int(.005 * SR), info=info, cands=cands,
              no=SOURCE_NO, os=os, ONLY=[], auto={}, human=[], _nonvoice=nonvoice)
    observed, old_trace, observed_ids = [], sys.gettrace(), set()
    require(old_trace is None and not any(os.environ.get(k) for k in ['ONLY', 'BREATH_FRAC']), 'No breath threshold or trace override')
    def trace(frame, event, arg):
        if (event == 'line' and frame.f_code.co_filename == str(path) and frame.f_globals is ns and
                frame.f_code.co_name == '<module>' and frame.f_lineno == gate_line and
                frame.f_locals.get('n_') not in observed_ids):
            v = frame.f_locals
            observed_ids.add(v['n_'])
            w, ref, aud = v['w'], v['ref_'], list(v['aud'])
            x0, x1 = int(v['x0']), int(v['x1'])
            require(int(ENVELOPE[0] * SR) <= x0 < x1 <= int(ENVELOPE[1] * SR), 'Automatic interval escaped bounded diagnostic envelope')
            features = frame_profile(np, SR, w, dossier_ns, x0, x1, ref)
            actual_breath = [bool(v['breathy'](i)) for i in aud]
            observed.append({'local_candidate_index': int(v['n_']), 'kind': v['c']['kind'],
                'automatic_x0_x1_samples_halfopen': [x0, x1], 'automatic_w_seconds': [x0 / SR, x1 / SR],
                'left_touches_word': bool(v['tl']), 'right_touches_word': bool(v['tr']),
                'preceding_loud5ms_frame_indices': [int(i) for i in v['pl']],
                'following_loud5ms_frame_indices': [int(i) for i in v['nl']],
                'audible_frame_start_samples': aud, 'breath_boolean_at_original_audible_frames': actual_breath,
                'audible_count': len(aud), 'breath_count': sum(actual_breath),
                'exact_breath_fraction': float(np.mean(actual_breath)) if aud else None,
                'unchanged_threshold': .70, 'original_gate_passes': bool(not aud or np.mean(actual_breath) >= .70),
                'original_ref_peak5ms_RMS': float(ref), 'automatic_interval_frames': features})
        return trace
    try:
        sys.settrace(trace)
        exec(compile(ast.Module(body=[loop], type_ignores=[]), str(path), 'exec'), ns)
    finally:
        sys.settrace(old_trace)
    require(len(observed) == len(cands) == 4 and not ns['auto'] and len(ns['human']) == 4,
            'Actual native S11 four original automatic rejections did not reproduce')
    require(all(not r['original_gate_passes'] and format(r['exact_breath_fraction'], '.0%') == '69%' for r in observed),
            'Original actual 69% rejection changed; do not accept a new acoustic state')
    require(all('不到七成（69%）' in row[3] for row in ns['human']), 'Original rejection reason changed')
    return {'unchanged_original_loop_AST_sha256': hashlib.sha256(ast.dump(loop, include_attributes=True).encode()).hexdigest(),
            'original_human_rejections': ns['human'], 'observed_before_original_70_percent_gate': observed,
            'no_merge_writer_or_interval_adoption_executed': True}


def acoustic_diagnostic(m, T, phase, pcm, w0, profile):
    np, SR = m.np, m.SR
    ns, a19_loop = original_dossier_parts(T / '疑点清单.py', profile['tools']['疑点清单.py'], np, SR, m._env5, m.AUD_DB)
    clock = phase['actual_sample_clock'][TARGET]
    it = {'si': 11, 'sent': DISPLAY, 'off': clock['start_sample'], 'n': len(pcm),
        'segs': [tuple(x[:3]) + (list(x[3]),) for x in m.LAST['segs']],
        'toks': [(x.phoneme, x.start, x.end) for x in m.LAST['toks']],
        'scale': m.LAST['scale'], 'head': m.LAST['head'], 'cuts': m.LAST['cuts'],
        'tmap': copy.deepcopy(profile['original_tmap']), 'w0': w0, 'out': pcm}
    normalize_peak = np.float32(phase['actual_original_mastering']['pre_master_absolute_peak'])
    normalized = pcm / normalize_peak * .89
    sha = lambda x: hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
    require(sha(normalized) == clock['observed_post_master_float_PCM_sha256'], 'Exact ordered native target normalization differs')
    # Original WAV writer quantization, in memory only, with zeros outside this
    # one actual target. This is never a rebuilt whole or whole fingerprint.
    buf = io.BytesIO(); m.sf.write(buf, normalized, SR, format='WAV', subtype='PCM_16'); buf.seek(0)
    quantized, rate = m.sf.read(buf)
    require(rate == SR and len(quantized) == len(pcm), 'Original in-memory PCM16 quantization ABI differs')
    context = np.zeros(phase['actual_complete_WAV']['samples'], float)
    context[clock['start_sample']:clock['end_sample_exclusive']] = quantized
    pv = load_module('_source56_only_S11_original_PV', T / '纯人声核对.py')
    flags = pv.scan(context)
    require(sorted(f[0] for f in flags) == sorted(['呼吸声', '起音前过长', '噗声']), 'Exact actual S11 PV candidate kinds changed')
    cands = [dict(kind=f[0], t0=f[1], t1=f[2], db=f[3], c=f[4], per=f[5], lo=f[6]) for f in flags]
    ns.update(info=[it], cands=cands)
    exec(compile(ast.Module(body=[a19_loop], type_ignores=[]), str(T / '疑点清单.py'), 'exec'), ns)
    require(len(cands) == 4 and sum(c['kind'] == 'A19停顿后吸气' for c in cands) == 1, 'Exact original A19 candidate not reproduced')
    cands.sort(key=lambda c: c['t0'])
    mapped = []
    reported_ids = {'呼吸声': 7, '起音前过长': 8, 'A19停顿后吸气': 9, '噗声': 10}
    for local_id, c in enumerate(cands, 1):
        p0 = ns['to_w'](it, (round(c['t0'] * SR) - it['off']) / SR)
        p1 = ns['to_w'](it, (round(c['t1'] * SR) - it['off'] - 1) / SR)
        require(p0 is not None and p1 is not None and 0 <= p0 <= p1 < len(w0), 'Candidate maps into inserted silence or outside w')
        require(ENVELOPE[0] <= p0 / SR <= (p1 + 1) / SR <= ENVELOPE[1], 'Candidate escaped approved envelope')
        mapped.append({**c, 'local_candidate_index': local_id,
            'previous_native_log_id_by_unique_kind_only': reported_ids[c['kind']],
            'native_id_is_not_recomputed_full_article_number': True,
            'original_to_w_samples_halfopen': [p0, p1 + 1], 'original_to_w_seconds': [p0 / SR, (p1 + 1) / SR]})
    count = len(w0) // int(.005 * SR)
    ref = np.sqrt(np.mean(w0[:count * 120].reshape(count, 120) ** 2, axis=1)).max()
    phones = [{'phoneme': ph, 'w_start_s': (st * it['scale'] * SR - it['head']) / SR,
        'w_end_s': (en * it['scale'] * SR - it['head']) / SR} for ph, st, en in it['toks']
        if ph.strip() and (en * it['scale'] * SR - it['head']) / SR > ENVELOPE[0] - .2 and
        (st * it['scale'] * SR - it['head']) / SR < ENVELOPE[1] + .2]
    automatic = observe_original_automatic(T / '自动切点.py', profile['tools']['自动切点.py'], np, SR, [it], cands, ns, m._nonvoice)
    return {'actual_original_LAST_head_samples': it['head'], 'actual_original_LAST_scale': it['scale'],
        'actual_original_LAST_segs': it['segs'], 'actual_original_timed_phonemes': phones,
        'timed_labels_are_annotations_not_word_boundary_or_noise_verdict': True,
        'raw_clean_tail_float32_sha256': sha(w0), 'actual_original_mapped_candidates': mapped,
        'w_envelope_frames': frame_profile(np, SR, w0, ns, int(ENVELOPE[0] * SR), int(ENVELOPE[1] * SR), ref),
        'original_automatic_observation': automatic,
        'original_PCM16_sparse_context': {'one_target_only_not_whole_reconstruction': True,
            'quantized_target_sha256': sha(quantized), 'no_audio_container_or_array_exported': True},
        'no_cut_selected_or_tested': True, 'A19_fully_removed_not_claimed': True}


def main():
    parser = argparse.ArgumentParser()
    for key in ['tools', 'video-root', 'inputs', 'profile', 'output']:
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    T, M = args.tools.resolve(), args.video_root.resolve()
    W, C = M / 'video', M / 'tts/cache_tts'
    output = args.output.resolve()
    report = {'kind': 'source56_only_S11_existing_mothers_original_69percent_A19_bounded_scalar_diagnostic',
        'source_id': SOURCE_NO, 'book_order': BOOK_ORDER, 'target_sentence': TARGET,
        'diagnostic_completed': False, 'quality_acceptance': False, 'human_listening_performed': False,
        'source_or_audio_or_confirmation_written': False, 'new_model_or_TTS_or_math_authorized': False,
        'whole_build_GT_ASR_render_authorized': False, 'errors': [], 'restoration': {}, 'forbidden_model_events': []}
    before = public = scripts = work = frozen = inp = profile = None
    entry_modules = dict(sys.modules)
    m = support = observer = None
    methods = cells = []
    restore = old_auto = old_write = old_build = old_title = None
    log = io.StringIO()
    try:
        require(digest(args.profile) == PROFILE_SHA256, 'Wrong exact closed profile')
        profile = json.loads(args.profile.read_text()); inp = bind_inputs(args.inputs, profile)
        require(not output.exists() and not output.is_relative_to(M), 'Fresh scalar output must be outside private machine')
        source, actual = json.loads(inp['source'].read_text()), json.loads(inp['actual_precheck'].read_text())
        sent, phase = validate_data(profile, source, actual)
        require(all(os.environ.get(k) == '1' for k in FLAGS) and not any(os.environ.get(k) for k in OVERRIDES), 'Exact reviewed strict modes; no overrides')
        require(Path('/home/user/postgraduate-vocabulary').resolve() == T.parent.parent.resolve(), 'Canonical ROOT alias differs')
        require(real_file(W / 'scripts/56.json').read_bytes() == inp['source'].read_bytes(), 'Caller must stage exact same-byte frozen source before probe; probe never writes it')
        require(digest(T / 'make_video.py') == digest(W / 'make_video.py') == profile['maker_sha256'], 'Actual original maker differs')
        for name, expected in profile['tools'].items():
            require(digest(real_file(T / name)) == expected, 'Wrong original pinned diagnostic tool ' + name)
        identity = json.loads(inp['identity'].read_text())
        require(identity['source_id'] == SOURCE_NO and identity['book_order'] == BOOK_ORDER, 'Wrong actual two-mother identity')
        for name, expected in identity['actual_four_private_files'].items():
            require(digest(real_file(C / name)) == expected, 'Exact saved target mother/marker differs')
        require_existing_math(C, '22842078959011da4b6986b549453b7eafee80d9')
        require({name: digest(real_file(M / 'tts' / name)) for name in identity['models_SHA256']} == identity['models_SHA256'] and
                digest(real_file(M / 'tts/voice_mb.npy')) == identity['voice_SHA256'], 'Known original model/voice identity differs')
        support = load_module('_source56_only_S11_support', inp['support'])
        observer = load_module('_source56_only_S11_observer', inp['observer'])
        support.validate_certificate(T, json.loads(inp['overlay'].read_text()), json.loads(inp['certificate'].read_text()))
        local_paths = runtime_local_paths(T, M, W, profile['original_G27_local_module_full_sha256'])
        before, public = inventory(C), inventory(T.parent / '配音缓存')
        scripts, work = directory_snapshot(W / 'scripts'), directory_snapshot(W / 'work_56')
        watch = list(inp.values()) + [args.profile, T / 'make_video.py', W / 'make_video.py'] + [T / n for n in profile['tools']] + list(local_paths.values()) + [T / (n + '.py') for n in local_paths]
        frozen = {str(p): digest(p) for p in watch}
        with process_state(W, support, report['restoration'], local_paths), contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            m = load_module('_source56_only_S11_maker', W / 'make_video.py')
            m._SPOKEN_SOURCE_NO = SOURCE_NO
            sentinel = M / 'forbid-source56-only-S11-breath-probe-public-export'
            require(not sentinel.exists(), 'Private public-export sentinel must be absent')
            m._REPO_CACHE = str(sentinel)
            require(Path(m._CACHE).resolve() == C.resolve() and m.SR == 24000 and type(m.SPEED) is float and m.SPEED == .95, 'Wrong native cache/rate/speed')
            require(m._OLDF and digest(m._OLDF) == profile['old_registry_sha256'] and
                    digest(m._cand) == profile['dictionary_sha256'] and digest(m._CTX_PATH) == profile['context_sha256'] and
                    m.SENT_NO[sent] == SOURCE_NO and m.spoken(sent) == DISPLAY, 'Source-first original context differs')
            # Load the original local gain dependency now, after purging any
            # preexisting module and before evaluating its original key rule.
            importlib.import_module('响度一致性核对')
            loaded_local = verify_loaded_local_modules(local_paths, profile['original_G27_local_module_full_sha256'])
            require({'clean', 'render', 'title2', '响度一致性核对'} <= set(loaded_local), 'Actual original audio dependencies not observed')
            methods = [(obj, name, getattr(obj, name)) for obj in (m.k, m.KT) for name in ('create', 'create_timed')]
            cells = [(support.closure_cell(support.closure_cell(getattr(obj, name), 'fn').cell_contents, 'fn'), None)
                     for obj, name in [(m.k, 'create'), (m.KT, 'create_timed')]]
            cells = [(cell, cell.cell_contents) for cell, _ in cells]
            restore = observer.block_native(m, support, report['forbidden_model_events'])
            entries = {row['method']: row for row in identity['cache_entries']}; used = []
            for method, obj, model in [('create', m.k, 'kokoro-v1.0.onnx'), ('create_timed', m.KT, 'kokoro-v1.0-timed.onnx')]:
                setattr(obj, method, target_model_guard(m, C, method, model, getattr(obj, method), sent, entries, used))
            old_auto = m._auto_level; math_reads = []
            def existing_math(clips, tmap, gaps, no='', rounds=2):
                require(str(no) == SOURCE_NO and type(rounds) is int and rounds == 2 and os.environ.get('STRICT_CACHE') == '1', 'Wrong original math scope')
                current = m._auto_level; m._auto_level = old_auto
                try:
                    key = observer.auto_key(m, clips, tmap, gaps, no)
                finally:
                    m._auto_level = current
                path = require_existing_math(C, key)
                require(not math_reads, 'Only one existing original S11 G36 read is authorized')
                value = old_auto(clips, tmap, gaps, no, rounds)
                require_existing_math(C, key)
                require(typed(value) == typed({1: -1.5, 2: 1.5}) and os.environ.get('STRICT_CACHE') == '1', 'Original cached gain/strict state differs')
                math_reads.append({'name': path.name, 'sha256': digest(path), 'value': value, 'new_math': False})
                return value
            m._auto_level = existing_math
            def forbidden(*a, **kw):
                raise AssertionError('No whole/title/render/audio-file-write or missing-math path is authorized')
            old_build, old_title = m.build, m.title_audio
            m.build = m.title_audio = forbidden
            old_write = m.sf.write
            def in_memory_only(file, *a, **kw):
                require(isinstance(file, io.BytesIO), 'No physical audio file write authorized')
                return old_write(file, *a, **kw)
            m.sf.write = in_memory_only
            try:
                raw, _ = m.k.create(m.spoken(sent), voice=m.V, speed=m.SPEED, lang='en-us')
                w0 = m.clean_tail(raw)
                pieces, gaps, p0 = [], [], 0
                listing = m.list_commas(sent)
                for mark in m._speech_marks(sent):
                    pieces.append((p0, mark.end())); p0 = mark.end() + 1
                    gaps.append(m.P_LIST if mark.start() in listing else m.P_COMMA)
                pieces.append((p0, len(sent)))
                require(len(pieces) == 2 and gaps == [.4], 'Only retained without-Wallace comma pause permitted')
                clips, tmap = m.sentence_audio(sent, pieces, gaps)
                require(typed([list(x) for x in tmap]) == typed(profile['original_tmap']), 'Actual original tmap differs')
                clips, pcm, auto, manual = m.句增益(source, SOURCE_NO, 10, sent, pieces, gaps, clips, tmap, m.np.concatenate(clips))
                sha = lambda x: hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest()
                target = phase['observed_sentences'][TARGET]
                require(sha(pcm) == target['pre_master_PCM_sha256'] and str(pcm.dtype) == 'float32' and len(pcm) == target['samples'], 'Actual current native premaster target differs')
                require(m.SENT_FP[sent] == target['actual_raw_w_fingerprint'] == '5e39565cea68' and
                        [list(x) for x in m.LAST['cuts']] == [[51600, 53880, .38]] and
                        typed(auto) == typed({1: -1.5, 2: 1.5}) and manual is None and not m.VOIDED, 'Unknown target physical state')
                raw_before = sha(w0)
                report['acoustics'] = acoustic_diagnostic(m, T, phase, pcm, w0, profile)
                require(sha(w0) == raw_before and sha(pcm) == target['pre_master_PCM_sha256'], 'Read-only acoustic diagnostics changed an array')
                require(len(used) == 3 and [r['method'] for r in used] == ['create', 'create', 'create_timed'] and len(math_reads) == 1, 'Unexpected cached call cardinality')
                report.update(actual_cached_reads=used, original_existing_G36_read=math_reads,
                    actual_source_sha256=digest(inp['source']), actual_display=sent, actual_spoken_model_text=m.spoken(sent),
                    actual_S11_premaster_sha256=sha(pcm), actual_raw_fingerprint=m.SENT_FP[sent],
                    no_narrower_cut_or_confirmation_selected=True)
                report['actual_original_loaded_local_modules'] = verify_loaded_local_modules(local_paths, profile['original_G27_local_module_full_sha256'])
            finally:
                m.sf.write = old_write; m._auto_level = old_auto
                m.build, m.title_audio = old_build, old_title
                if restore is not None:
                    restore(); restore = None
                for obj, name, value in methods:
                    setattr(obj, name, value)
                for cell, value in cells:
                    cell.cell_contents = value
                report['restoration']['all_four_original_methods_restored'] = all(getattr(obj, name) is value for obj, name, value in methods)
                report['restoration']['all_native_closure_cells_restored'] = all(cell.cell_contents is value for cell, value in cells)
                report['restoration']['original_auto_level_and_soundfile_write_restored'] = m._auto_level is old_auto and m.sf.write is old_write
                report['restoration']['original_build_and_title_methods_restored'] = m.build is old_build and m.title_audio is old_title
        require(not sentinel.exists(), 'Diagnostic attempted public cache export')
        report['diagnostic_completed'] = True
    except BaseException as error:
        report['errors'].append({'type': type(error).__name__, 'detail': str(error)})
        traceback.print_exc()
    finally:
        # Covers failures during guard installation, before the inner try begins.
        if m is not None:
            if old_write is not None: m.sf.write = old_write
            if old_auto is not None: m._auto_level = old_auto
            if old_build is not None: m.build = old_build
            if old_title is not None: m.title_audio = old_title
        if restore is not None: restore()
        for obj, name, value in methods: setattr(obj, name, value)
        for cell, value in cells: cell.cell_contents = value
        for name in set(sys.modules) - set(entry_modules): sys.modules.pop(name, None)
        sys.modules.update(entry_modules)
        report['restoration']['entry_modules_including_support_and_observer_restored'] = (
            set(sys.modules) == set(entry_modules) and all(sys.modules[k] is v for k, v in entry_modules.items()))
        if before is not None:
            report['all_private_cache_bytes_unchanged'] = inventory(C) == before
            report['all_public_cache_bytes_unchanged'] = inventory(T.parent / '配音缓存') == public
            report['all_source_scripts_inode_and_bytes_unchanged'] = directory_snapshot(W / 'scripts') == scripts
            report['all_normal_work_inode_and_bytes_unchanged'] = directory_snapshot(W / 'work_56') == work
            report['all_frozen_inputs_and_programs_unchanged'] = all(digest(p) == h for p, h in frozen.items())
        checks = ['all_private_cache_bytes_unchanged', 'all_public_cache_bytes_unchanged',
                  'all_source_scripts_inode_and_bytes_unchanged', 'all_normal_work_inode_and_bytes_unchanged',
                  'all_frozen_inputs_and_programs_unchanged']
        restored = ['environment_cwd_sys_path_restored', 'all_process_modules_restored',
                    'trace_cwd_path_environment_bytecode_restored', 'all_four_original_methods_restored',
                    'all_native_closure_cells_restored', 'original_auto_level_and_soundfile_write_restored',
                    'original_build_and_title_methods_restored', 'entry_modules_including_support_and_observer_restored']
        report['diagnostic_completed'] = bool(report['diagnostic_completed'] and
            all(report.get(k) is True for k in checks) and
            all(report['restoration'].get(k) is True for k in restored) and not report['forbidden_model_events'])
        report['private_diagnostic_log'] = log.getvalue()
        report['scope_limit'] = 'Scalar observation only; no human listening, quality approval, narrower deletion, interval adoption, source edit, audio export, model execution, new math, whole build, GT, ASR or render.'
        # Parent supplies an exclusive fresh public metadata path. No overwrite.
        require(not output.exists() and not output.is_relative_to(M), 'Never overwrite or write inside private machine')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=lambda x: x.item()) + '\n')
        print(json.dumps({'diagnostic_completed': report['diagnostic_completed'], 'output_sha256': digest(output), 'errors': report['errors']}, ensure_ascii=False))
    return 0 if report['diagnostic_completed'] else 1


if __name__ == '__main__':
    sys.exit(main())
