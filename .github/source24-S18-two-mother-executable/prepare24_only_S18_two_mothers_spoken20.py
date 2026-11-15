"""Exact source24 S18 two-mother preparation; never whole audio or quality acceptance.

Requires a new real 110-program code certificate and a separately pinned root
execution adoption. Unknown post-pron inputs/cache identities are observed at
runtime and written before the only two permitted original model calls.
"""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import traceback

sys.dont_write_bytecode = True
SOURCE = '533d34bb3261935549042a5863a1fa4e65c816bbb218964e017bc9867bc72c16'
SHADOW = 'e31e54fddbb46d3b7852891d676655fde985005376e5b93ac0534d685aaca2b2'
PROFILE_SHA = '09220008514da9972ed7f6d4b956f69494ffa5b87b06597796fd0b649e34b892'
MAKER = '0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
AUTH = 'a5615c07b6cef6b46dd1a98b69734015d62e9cf674c9a2fb31748c759fe275b9'
DICT = '5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
CTX = '4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
OLDREG = '91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
VOICE = '1f97658bb5a4280cc3f6c01dc644dff471bf57c970fc8b99f3049d6991c4f6c8'
MODELS = {
    'kokoro-v1.0.onnx': '7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5',
    'kokoro-v1.0-timed.onnx': 'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
    'voices-v1.0.bin': 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d',
}
DISPLAY = 'Precision put six ashore within reach of help and, a century on, brought their ship back into view.'
PROJECTED = 'Precision put six ashore within reach of help and a century on, brought their ship back into view.'
FLAGS = ('STRICT_CACHE', 'XG_NOPUSH', 'XG_KEEP_REVIEWED_GAIN',
         'XG_KEEP_REVIEWED_ENDING', 'XG_KEEP_REVIEWED_CUTS')


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def inventory(directory):
    return {p.name: sha(p) for p in Path(directory).iterdir() if p.is_file()}


def verify_request(request, shadow, history):
    require(str(request.get('no')) == '24' and len(request['sentences']) == 18,
            'Wrong source/sentence count')
    restored = copy.deepcopy(shadow)
    rows = history['retired_entries']
    require(len(rows) == 9, 'Exactly nine old S18 leaves must be retired')
    require(len({tuple(x['JSON_path']) for x in rows}) == 9, 'Duplicate retirement path')
    for row in rows:
        parent = restored
        for key in row['JSON_path'][:-1]:
            parent = parent[key]
        key = row['JSON_path'][-1]
        require(key not in parent, 'Retired old target leaf still active')
        parent[key] = row['exact_old_value']
    require(restored == request, 'Nine-leaf inverse must reconstruct entire immutable request')
    require(request['sentences'] == shadow['sentences'], 'Retirement changed display text')
    require(not shadow.get('结尾句', {}).get('S18'), 'No S18 ENDING is permitted')
    return True


def input_key(method, mid, text, voice_id, speed, lang, kwargs):
    return hashlib.sha1(repr((method, mid, text, voice_id, float(speed),
                              lang, sorted(kwargs.items()))).encode()).hexdigest() + '.pkl'


def validate_model_input(method, text, voice_id, speed, lang, kwargs, expected):
    require(method in expected, 'Unexpected model method')
    e = expected[method]
    require((text, voice_id, float(speed), lang, kwargs) ==
            (e['text'], e['voice_id'], .95, 'en-us', e['kwargs']),
            'Non-target model tuple rejected')
    return e


@contextlib.contextmanager
def source_namespace(work, shadow_bytes, restoration=None):
    """Rename the original scripts inode, including directory links, and restore it."""
    work = Path(work)
    scripts = work / 'scripts'
    existed = os.path.lexists(scripts)
    original_inode = scripts.lstat().st_ino if existed else None
    snapshots = {p.name: p.read_bytes() for p in scripts.glob('*.json')} if existed else {}
    scratch = Path(tempfile.mkdtemp(prefix='_source24_only_S18_namespace_', dir=work.parent))
    backup = scratch / 'original-scripts-inode'
    moved = False
    try:
        if existed:
            os.replace(scripts, backup)
            moved = True
        scripts.mkdir()
        for name, data in snapshots.items():
            (scripts / name).write_bytes(data)
        (scripts / '24.json').write_bytes(shadow_bytes)
        yield
    finally:
        if moved or not existed:
            if os.path.lexists(scripts):
                if scripts.is_symlink() or scripts.is_file():
                    scripts.unlink()
                else:
                    shutil.rmtree(scripts)
            if moved:
                os.replace(backup, scripts)
        shutil.rmtree(scratch)
        require(os.path.lexists(scripts) == existed, 'Scripts existence was not restored')
        if existed:
            require(scripts.lstat().st_ino == original_inode, 'Scripts inode not restored')
            require({p.name: p.read_bytes() for p in scripts.glob('*.json')} == snapshots,
                    'Original normal source scripts changed')
        if restoration is not None:
            restoration['normal_scripts_namespace_restored'] = True


@contextlib.contextmanager
def environment_and_cwd(work, restoration=None):
    keys = set(FLAGS) | {'CACHE_LOG', 'AUDIO_ONLY', 'VOICE', 'AFFILE', 'OLD_IV_VOID'}
    prior = {k: os.environ.get(k) for k in keys}
    cwd, path = Path.cwd(), list(sys.path)
    try:
        os.chdir(work)
        sys.path.insert(0, str(work))
        os.environ['STRICT_CACHE'] = '1'
        os.environ['XG_NOPUSH'] = '1'
        os.environ['AUDIO_ONLY'] = '1'
        os.environ.pop('CACHE_LOG', None)
        yield
    finally:
        os.chdir(cwd)
        sys.path[:] = path
        for key, value in prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        require(all(os.environ.get(k) == v for k, v in prior.items()), 'Environment restore failed')
        if restoration is not None:
            restoration['environment_cwd_sys_path_restored'] = True


def closure_cell(fn, name):
    cells = dict(zip(fn.__code__.co_freevars, fn.__closure__ or ()))
    require(name in cells, 'Original cached/pron closure ABI changed')
    return cells[name]


def validate_certificate(tools, manifest, certificate):
    require(len(manifest['files']) == 17, 'Expected exact 17 runtime files')
    require(certificate.get('overlay_manifest') == manifest and
            len(certificate.get('source68_code_adoption_SHA256', '')) == 64 and
            len(certificate.get('source35_code_adoption_SHA256', '')) == 64,
            'Actual combined20 certificate must bind this runtime contract and separate68/35 code adoption')
    for row in manifest['files']:
        rel = Path(row['path']).relative_to('视频/工具')
        require(sha(tools / rel) == row['patch_SHA256'], 'Runtime contract mismatch: ' + str(rel))
    stamp_path = tools / '新管/快测通过.json'
    stamp = read(stamp_path)
    require(len(stamp['程序']) == 110 and stamp['程序']['make_video.py'] == MAKER[:16],
            'A new actual 110-program stamp for0e6c4 spoken20 is required')
    require(sha(stamp_path) != '3c251c77fb58b775ae1389a52ce31467686201ba98b842af545f2923357a6c32',
            'Old17 stamp is historical only')
    require(certificate.get('passed') is True and
            certificate.get('original_full_fastcheck_passed') is True and
            certificate.get('new_actual_110_program_stamp_created_after_full_quickcheck') is True and
            certificate.get('real_fastcheck_stamp_SHA256') == sha(stamp_path),
            'Actual new fullquick certificate/stamp mismatch')
    checks = certificate.get('checks', [])
    require(any(x.get('name') == 'original-full-fastcheck' and x.get('exit') == 0 for x in checks),
            'Original fullquick successful execution record missing')
    require(certificate.get('production_audio_or_video_acceptance') is False,
            'Code certificate must not claim article acceptance')
    return sha(stamp_path)


def run(a):
    report = {'kind': 'source24_S18_only_two_original_model_mothers', 'source_id': '24',
              'book_order': 49, 'quality_acceptance': False, 'formal_acceptance': False,
              'whole_audio_or_ASR_or_GT_or_encoding_run': False,
              'source_or_GEN_or_MD_or_CF_written': False, 'completed': False,
              'model_calls': [], 'cache_entries': []}
    T, M = a.tools.resolve(), a.video_root.resolve()
    W, C = M / 'video', M / 'tts/cache_tts'
    before = None
    pcm_before = public_before = input_pins = None
    expected = {}
    restoration = {}
    try:
        require(sha(a.profile) == PROFILE_SHA, 'Wrong immutable input profile')
        profile = read(a.profile)
        for label, path in [('request', a.request), ('shadow', a.shadow), ('history', a.history),
                            ('authority', a.authority), ('code_adoption', a.code_adoption),
                            ('GEN', a.GEN), ('MD', a.MD), ('overlay', a.overlay),
                            ('text_supplement_H', a.text_supplement_H),
                            ('pending_text', a.pending_text), ('sentence_confirmations', a.sentence_confirmations)]:
            require(sha(path) == profile['file_sha256'][label], 'Wrong pinned input: ' + label)
        require(sha(a.request) == SOURCE and sha(a.shadow) == SHADOW and sha(a.authority) == AUTH,
                'Exact source/shadow/user authorization required')
        require(len(a.execution_adoption_sha256) == 64 and
                sha(a.execution_adoption) == a.execution_adoption_sha256,
                'Launcher must pin separate root executable/mother-scope adoption')
        require(sha(T / 'make_video.py') == sha(W / 'make_video.py') == MAKER,
                'Candidate spoken20 must be physically installed in tools and work')
        stamp_sha = validate_certificate(T, read(a.overlay), read(a.certification_report))
        require(os.environ.get('STRICT_CACHE') == '1' and os.environ.get('XG_NOPUSH') == '1',
                'Begin under strict cache and no-push')
        require(all(os.environ.get(k) == '1' for k in FLAGS[2:]), 'Original reviewed modes required')
        require(not any(os.environ.get(k) for k in ('VOICE', 'AFFILE', 'OLD_IV_VOID')),
                'Voice/filter/invalidation overrides forbidden')
        require(Path('/home/user/postgraduate-vocabulary').resolve() == T.parent.parent,
                'Canonical original repository alias required')
        require(sha(T / '发音词典/读音改正.json') == DICT and
                sha(T / '发音词典/按语境读音.json') == CTX, 'Wrong original dictionaries')
        portable = {k: k + ':' + v[:16] for k, v in MODELS.items()}
        for registry in (T / '环境/模型校验码.json', W / '环境/模型校验码.json'):
            require(all(read(registry).get(k) == v for k, v in portable.items()),
                    'Original portable model registry is missing or different')
        require({k: sha(M / 'tts' / k) for k in MODELS} == MODELS and
                sha(M / 'tts/voice_mb.npy') == VOICE, 'Wrong full model/voice bytes')
        request, shadow, history = read(a.request), read(a.shadow), read(a.history)
        verify_request(request, shadow, history)
        before = inventory(C)
        pcm_before = {str(p): sha(p) for p in W.glob('work_*/a.wav')}
        public_cache = T.parent / '配音缓存'
        public_before = inventory(public_cache)
        input_pins = {str(p): sha(p) for p in (a.request, a.shadow, a.GEN, a.MD)}
        report.update({'actual_new_code_certificate_SHA256': sha(a.certification_report),
                       'actual_new_110_stamp_SHA256': stamp_sha,
                       'execution_adoption_SHA256': a.execution_adoption_sha256,
                       'request_SHA256': SOURCE, 'shadow_SHA256': SHADOW,
                       'dictionary_SHA256': DICT, 'context_SHA256': CTX,
                       'models_SHA256': MODELS, 'voice_SHA256': VOICE})
        with environment_and_cwd(W, restoration):
            try:
                with source_namespace(W, a.shadow.read_bytes(), restoration):
                    name = '_source24_S18_two_mothers_exact'
                    require(name not in sys.modules, 'Fresh module namespace required')
                    spec = importlib.util.spec_from_file_location(name, W / 'make_video.py')
                    m = importlib.util.module_from_spec(spec)
                    sys.modules[name] = m
                    try:
                        spec.loader.exec_module(m)
                        m._SPOKEN_SOURCE_NO = '24'
                        require(m._OLDF and sha(m._OLDF) == OLDREG, 'Original G72 registry required')
                        require(sha(m._cand) == DICT and m._CTX_PATH and sha(m._CTX_PATH) == CTX,
                                'Fresh maker loaded a different dictionary context')
                        require(str(m.SENT_NO.get(DISPLAY)) == '24', 'Source must be installed before import')
                        rule = m._speech_rule(DISPLAY)
                        require(rule and rule['projected'] == PROJECTED and
                                rule['needs_mother_binding'] is False, 'Exact fresh S18 rule required')
                        for table in (m.NONVOICE, m.INSERT_AT, m.VFP):
                            require(DISPLAY not in table, 'Old S18 physical data must stay retired')
                        require(DISPLAY not in m.ENDING, 'No old/new S18 ending splice')
                        require(m.SPEED == .95 and m.SR == 24000, 'Original voice rate required')
                        for obj in (m.k, m.KT):
                            sessions = [v for v in vars(obj).values() if hasattr(v, 'get_session_options')]
                            require(bool(sessions), 'Actual model session required')
                            for session in sessions:
                                options = session.get_session_options()
                                require(options.intra_op_num_threads == options.inter_op_num_threads == 1,
                                        'Original model inference must be single-thread')
                        forbidden_public = M / '_forbid_source24_public_cache_export'
                        require(not forbidden_public.exists(), 'Public-export sentinel must be absent')
                        m._REPO_CACHE = str(forbidden_public)
                        np = m.np
                        voice_id = hashlib.sha1(np.ascontiguousarray(m.V).tobytes()).hexdigest()
                        logical_text = m.spoken(DISPLAY)
                        require(m._speech_spoken_projection(logical_text) == m.spoken(PROJECTED),
                                'Exact first comma projection failed')
                        for method, obj, model, kwargs in [
                            ('create', m.k, 'kokoro-v1.0.onnx', {}),
                            ('create_timed', m.KT, 'kokoro-v1.0-timed.onnx',
                             {'clause_pause': 0, 'sentence_pause': 0})]:
                            captured = []
                            def capture(text, voice, speed=1.0, lang='en-us', **kw):
                                captured.append((text, hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest(), float(speed), lang, dict(kw)))
                            m._pron(capture)(logical_text, voice=m.V, speed=.95, lang='en-us', **kwargs)
                            require(len(captured) == 1, 'Each logical call must project once')
                            text, vh, speed, lang, kw = captured[0]
                            require(vh == voice_id and speed == .95 and lang == 'en-us', 'Unexpected actual tuple')
                            require({k: v for k, v in kw.items() if k != 'is_phonemes'} == kwargs,
                                    'Unexpected projected kwargs')
                            mid = m._portable_mid(str(M / 'tts' / model))
                            require(mid == portable[model], 'Portable key identity changed')
                            key = input_key(method, mid, text, vh, speed, lang, kw)
                            path, marker = C / key, C / (key + '.单线程')
                            require(not marker.exists() or path.exists(), 'Orphan target marker')
                            if path.exists():
                                m._条目核对(str(path))
                                require(marker.is_file() and marker.read_text().strip() == sha(path)[:16],
                                        'Existing target must have genuine single-thread provenance')
                            else:
                                native_model_path = '../tts/' + model
                                stat = Path(native_model_path).stat()
                                oldmid = native_model_path + ':' + str(stat.st_size) + ':' + str(int(stat.st_mtime))
                                legacy_path = C / input_key(method, oldmid, text, vh, speed, lang, kw)
                                require(not legacy_path.exists(), 'Unresolved old-path target entry; do not migrate or infer')
                            expected[method] = {'text': text, 'voice_id': vh, 'kwargs': kw,
                                                'logical_kwargs': kwargs, 'model': model, 'key': key,
                                                'preexisted': path.exists(), 'portable_mid': mid}
                        require(expected['create']['text'] == expected['create_timed']['text'],
                                'Raw/timed post-pron input must match')
                        report['actual_planned_input_witness'] = [
                            {'method': method, 'actual_post_pron_input': e['text'],
                             'actual_post_pron_SHA256': hashlib.sha256(e['text'].encode()).hexdigest(),
                             'portable_mid': e['portable_mid'], 'exact_native_cache_key': e['key'],
                             'voice_sha1': e['voice_id'], 'voice_npy_SHA256': VOICE,
                             'speed': .95, 'lang': 'en-us', 'kwargs': e['kwargs'],
                             'cache_preexisted': e['preexisted']}
                            for method, e in expected.items()]
                        report['planned_input_witness_written_before_possible_inference'] = True
                        save(a.output, report)
                        originals, changed_cells = {}, []
                        native_counts = {'create': 0, 'create_timed': 0}
                        try:
                            for method, obj in [('create', m.k), ('create_timed', m.KT)]:
                                outer = getattr(obj, method)
                                cached = closure_cell(outer, 'fn').cell_contents
                                require(cached.__code__.co_filename == str(W / 'make_video.py'),
                                        'Original maker cached wrapper required')
                                cell = closure_cell(cached, 'fn')
                                native = cell.cell_contents
                                def native_guard(text, voice, speed=1.0, lang='en-us',
                                                 _method=method, _native=native, **kw):
                                    vh = hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                                    e = validate_model_input(_method, text, vh, speed, lang, kw, expected)
                                    require(not os.environ.get('STRICT_CACHE'), 'Native inference under STRICT forbidden')
                                    require(not e['preexisted'] and not (C / e['key']).exists(),
                                            'Existing target cache cannot be regenerated')
                                    require(native_counts[_method] == 0, 'At most one original call per target method')
                                    native_counts[_method] += 1
                                    return _native(text, voice=voice, speed=speed, lang=lang, **kw)
                                changed_cells.append((cell, native))
                                cell.cell_contents = native_guard
                                originals[(id(obj), method)] = (obj, method, outer)
                                def logical_guard(text, voice, speed=1.0, lang='en-us',
                                                  _method=method, _outer=outer, **kw):
                                    require(text == logical_text and speed == .95 and lang == 'en-us' and
                                            kw == expected[_method]['logical_kwargs'] and
                                            np.array_equal(voice, m.V), 'Non-target logical model call forbidden')
                                    report['model_calls'].append({'method': _method, 'strict_cache': os.environ.get('STRICT_CACHE') == '1'})
                                    return _outer(text, voice=voice, speed=speed, lang=lang, **kw)
                                setattr(obj, method, logical_guard)
                            def forbidden(*args, **kwargs):
                                raise AssertionError('Unlisted model method is forbidden')
                            for obj, method in [(m.k, 'create_timed'), (m.KT, 'create')]:
                                if hasattr(obj, method):
                                    originals[(id(obj), method)] = (obj, method, getattr(obj, method))
                                    setattr(obj, method, forbidden)
                            values = {}
                            for method, obj in [('create', m.k), ('create_timed', m.KT)]:
                                e = expected[method]
                                try:
                                    if not e['preexisted']:
                                        os.environ.pop('STRICT_CACHE', None)
                                    value = getattr(obj, method)(logical_text, voice=m.V, speed=.95,
                                                                lang='en-us', **e['logical_kwargs'])
                                finally:
                                    os.environ['STRICT_CACHE'] = '1'
                                require(isinstance(value, tuple) and len(value) == (3 if method == 'create_timed' else 2),
                                        'Original tuple schema required')
                                wave = value[0]
                                require(value[1] == 24000 and wave.dtype == np.float32 and wave.ndim == 1 and
                                        len(wave) > 0 and bool(np.all(np.isfinite(wave))), 'Invalid actual model array')
                                path, marker = C / e['key'], C / (e['key'] + '.单线程')
                                m._条目核对(str(path))
                                require(marker.is_file() and marker.read_text().strip() == sha(path)[:16],
                                        'Actual original single-thread marker missing/mismatched')
                                values[method] = value
                                report['cache_entries'].append({'method': method, 'name': path.name,
                                    'pkl_SHA256': sha(path), 'marker_name': marker.name, 'marker_SHA256': sha(marker),
                                    'marker_value': marker.read_text().strip(), 'preexisted': e['preexisted'],
                                    'actual_original_model_inference_calls': native_counts[method],
                                    'samples': len(wave), 'SR': int(value[1]), 'dtype': str(wave.dtype),
                                    'array_SHA256': hashlib.sha256(np.ascontiguousarray(wave).tobytes()).hexdigest(),
                                    'timed_token_count': len(value[2]) if method == 'create_timed' else None})
                            for method, obj in [('create', m.k), ('create_timed', m.KT)]:
                                value = getattr(obj, method)(logical_text, voice=m.V, speed=.95,
                                                            lang='en-us', **expected[method]['logical_kwargs'])
                                require(np.array_equal(value[0], values[method][0]) and value[1] == values[method][1] and (method != 'create_timed' or m._pk.dumps(value[2]) == m._pk.dumps(values[method][2])),
                                        'Original strict cache readback differs')
                            report['actual_native_original_inference_count'] = sum(native_counts.values())
                            require(report['actual_native_original_inference_count'] <= 2, 'Inference scope exceeded')
                            report['both_original_STRICT_cache_readbacks_exact'] = True
                            report['completed'] = True
                        finally:
                            for obj, method, original in originals.values():
                                setattr(obj, method, original)
                            for cell, native in changed_cells:
                                cell.cell_contents = native
                    finally:
                        sys.modules.pop(name, None)
            finally:
                report.update(restoration)
        report.update(restoration)
        require(all(Path(p).is_file() and sha(p) == h for p, h in pcm_before.items()), 'Existing PCM changed')
        require(inventory(public_cache) == public_before, 'Public repository cache changed')
        require(all(sha(p) == h for p, h in input_pins.items()), 'Immutable request/GEN/MD changed')
        report['existing_PCM_exact'] = report['public_repository_cache_exact'] = report['immutable_inputs_exact'] = True
    except BaseException as error:
        report['completed'] = False
        report['error'] = {'type': type(error).__name__, 'detail': str(error)}
        traceback.print_exc()
    finally:
        report.update(restoration)
        if before is not None:
            report['existing_PCM_exact'] = all(Path(p).is_file() and sha(p) == h for p, h in pcm_before.items())
            report['public_repository_cache_exact'] = inventory(public_cache) == public_before
            report['immutable_inputs_exact'] = all(sha(p) == h for p, h in input_pins.items())
            report['original_runtime_maker_dict_models_voice_exact_after'] = (
                sha(T / 'make_video.py') == sha(W / 'make_video.py') == MAKER and
                sha(T / '发音词典/读音改正.json') == DICT and sha(T / '发音词典/按语境读音.json') == CTX and
                {k: sha(M / 'tts' / k) for k in MODELS} == MODELS and sha(M / 'tts/voice_mb.npy') == VOICE)
            if not all(report[k] for k in ('existing_PCM_exact', 'public_repository_cache_exact', 'immutable_inputs_exact', 'original_runtime_maker_dict_models_voice_exact_after')):
                report['completed'] = False
            after = inventory(C)
            allowed = {name for e in expected.values() for name in (e['key'], e['key'] + '.单线程')}
            report['all_existing_private_cache_files_exact'] = all(after.get(k) == v for k, v in before.items())
            report['only_actual_two_mother_four_private_files_added'] = set(after) - set(before) <= allowed
            report['new_private_files'] = [{'name': k, 'SHA256': after[k]} for k in sorted(set(after) - set(before))]
            if not report['all_existing_private_cache_files_exact'] or not report['only_actual_two_mother_four_private_files_added']:
                report['completed'] = False
        try:
            if report['completed']:
                names = sorted({x for e in expected.values() for x in (e['key'], e['key'] + '.单线程')})
                require(len(names) == 4, 'Exactly four actual private leaves required')
                runid = os.environ.get('GITHUB_RUN_ID', '')
                require(runid.isdigit(), 'Actual native Actions run id required for private transport')
                proposed_key = 'Linux-native24-exact-S18-first-spoken-comma-' + runid
                fixture = {'kind': 'source24_S18_two_original_mother_private_cache_identity_not_quality_acceptance',
                           'source_id': '24', 'book_order': 49, 'request_SHA256': SOURCE, 'shadow_SHA256': SHADOW,
                           'maker_SHA256': MAKER, 'actual_native_run': runid, 'actual_native_head': os.environ.get('GITHUB_SHA'),
                           'actual_new_code_certificate_SHA256': report['actual_new_code_certificate_SHA256'],
                           'actual_new_110_stamp_SHA256': report['actual_new_110_stamp_SHA256'],
                           'private_Actions_cache_key_proposed_for_following_save_step': proposed_key,
                           'cache_save_success_not_claimed': True,
                           'actual_four_private_files': {name: sha(C / name) for name in names},
                           'actual_normal_cache_paths': [str(C / name) for name in names],
                           'actual_inputs': report['actual_planned_input_witness'], 'cache_entries': report['cache_entries'],
                           'models_SHA256': MODELS, 'voice_SHA256': VOICE,
                           'quality_acceptance': False, 'new_physical_controls_or_CF_created': False,
                           'whole_audio_QC_ASR_and_final4K_not_run': True}
                fixture_path = a.output.parent / '24-S18-two-mother-private-cache-identity.json'
                save(fixture_path, fixture)
                report['private_fixture'] = {'file': fixture_path.name, 'SHA256': sha(fixture_path)}
                with a.cache_path_output.open('a') as out:
                    out.write('cache_key=' + proposed_key + '\ncache_paths<<SOURCE24PRIVATE\n' +
                              '\n'.join(str(C / name) for name in names) + '\nSOURCE24PRIVATE\n')
        except BaseException as error:
            report['completed'] = False
            report['private_fixture_or_transport_error'] = {'type': type(error).__name__, 'detail': str(error)}
        save(a.output, report)
    return 0 if report['completed'] else 1


def main():
    p = argparse.ArgumentParser()
    for key in ('tools', 'video-root', 'profile', 'request', 'shadow', 'history', 'GEN', 'MD',
                'authority', 'code-adoption', 'execution-adoption', 'overlay', 'certification-report',
                'text-supplement-H', 'pending-text', 'sentence-confirmations', 'output', 'cache-path-output'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--execution-adoption-sha256', required=True)
    return run(p.parse_args())


if __name__ == '__main__':
    sys.exit(main())
