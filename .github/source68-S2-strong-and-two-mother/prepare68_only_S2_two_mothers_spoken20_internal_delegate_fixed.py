"""Exact one-source/target two-mother preparation; never whole audio or quality acceptance.

Requires a new real 110-program code certificate and a separately pinned root
execution adoption. Unknown post-pron inputs/cache identities are observed at
runtime and written before the only two permitted original model calls.
"""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import traceback

sys.dont_write_bytecode = True
SOURCE = 'e122c817946c4ed6e7cd1394749879276ef2afe9d01ad691b4142c6bbd9ec9b4'
SOURCE_NO = '68'
BOOK_ORDER = 53
TARGET = 'S2'
SENTENCE_COUNT = 19
RETIRE_COUNT = 1
SCHEMA_ADDED = False
CERTIFICATE_SHA = '50a3abb8d8388ba4587eed0baab4eed5b57afad9fc73cbdb1aa4b48bbaa56c01'
STAMP_SHA = '7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41'
SHADOW = '23df02656c126fc55a9d6d5601793f4370742ca3a7acdbf01a8d9d2565d2f262'
PROFILE_SHA = '42332c98fa59a880e747782e15a004e63c9e78a36a9ae6e61e1c5c62876fa771'
MAKER = '0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
PROVIDER_SOURCE_SHA = '32602bee21b14ed161fdfd3c8b921b267782ad143a49c3ebd256c16c473808f5'
DELEGATE_GUARD_SHA = '8f94c2ffbcdc981c177c4f8547bbf0bb7481628b9d8355165cd04db4bf5b6521'
AUTH = 'c61ac0483b54f6c6c2092d27e3e697ebea63ee23b95e85e33f2ff1a509f027d0'
DICT = '5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
CTX = '142686fb2a4764dba90834ecf3ed5cfced2723872a6a84500229e4f2061e6ec6'
OLDREG = '91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
VOICE = '1f97658bb5a4280cc3f6c01dc644dff471bf57c970fc8b99f3049d6991c4f6c8'
MODELS = {
    'kokoro-v1.0.onnx': '7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5',
    'kokoro-v1.0-timed.onnx': 'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
    'voices-v1.0.bin': 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d',
}
DISPLAY = 'Its amenities included a lounge and, that year, a grand piano.'
PROJECTED = 'Its amenities included a lounge and that year, a grand piano.'
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
    require(str(request.get('no')) == SOURCE_NO and len(request['sentences']) == SENTENCE_COUNT,
            'Wrong independent source/sentence count')
    require(history['source_id'] == SOURCE_NO and history['book_order'] == BOOK_ORDER and
            history['target_sentence'] == TARGET and
            history['before_source']['sha256'] == SOURCE and
            history['schema_added_in_private_shadow'] is SCHEMA_ADDED,
            'Wrong independent target retirement provenance')
    restored = copy.deepcopy(shadow)
    rows = history['retired_entries']
    require(len(rows) == RETIRE_COUNT and len({tuple(x['JSON_path']) for x in rows}) == RETIRE_COUNT,
            'Exact independent target retirement count/paths required')
    for row in rows:
        parent = restored
        for key in row['JSON_path'][:-1]:
            parent = parent[key]
        key = row['JSON_path'][-1]
        require(key not in parent, 'Retired explicit old target leaf still active')
        parent[key] = row['exact_old_value']
    expected_spec = {'篇号': int(SOURCE_NO), '原文': DISPLAY, '逗号序号': [1]}
    require(shadow.get('朗读删逗号', {}).get(TARGET) == expected_spec, 'Exact target schema required')
    if SCHEMA_ADDED:
        require('朗读删逗号' not in request and restored.get('朗读删逗号') == {TARGET: expected_spec},
                'Only this originally absent target schema may be added')
        restored.pop('朗读删逗号')
    require(restored == request, 'Exact retirement/schema inverse must reconstruct entire immutable request')
    require(request['sentences'] == shadow['sentences'], 'Private retirement changed display text')
    require(not shadow.get('结尾句', {}).get(TARGET), 'Target is not an ending-splice sentence')
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
    scratch = Path(tempfile.mkdtemp(prefix='_single_target_mother_namespace_', dir=work.parent))
    backup = scratch / 'original-scripts-inode'
    moved = False
    try:
        if existed:
            os.replace(scripts, backup)
            moved = True
        scripts.mkdir()
        for name, data in snapshots.items():
            (scripts / name).write_bytes(data)
        (scripts / (SOURCE_NO + '.json')).write_bytes(shadow_bytes)
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


def validate_execution_adoption(adopted, helper_sha):
    require(adopted.get('source_id') == SOURCE_NO and adopted.get('book_order') == BOOK_ORDER and
            adopted.get('target_sentence') == TARGET and
            adopted.get('target_two_original_model_calls_authorized') is True and
            adopted.get('helper_sha256') == helper_sha and
            adopted.get('request_sha256') == SOURCE and adopted.get('shadow_sha256') == SHADOW and
            adopted.get('actual20_certificate_sha256') == CERTIFICATE_SHA and
            adopted.get('actual20_stamp_sha256') == STAMP_SHA,
            'Actual root execution adoption must bind this independent source/target/helper/inputs/certificate')
    require(adopted.get('root_actual_scope_sha256') == ROOT_SCOPE_SHA and
            adopted.get('real_CPU_contract_sha256') == CONTRACT_SHA and
            adopted.get('new_context_sha256') == CTX, 'Derived executable binding must cite actual ROOT727f and exact context/CPU contract')
    return True


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
    require(sha(stamp_path) == STAMP_SHA, 'Actual certified20 stamp7d7ebf required')
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


ROOT_SCOPE_SHA = '727f4eb413cdb48d215200f2260d40ba46b00867119ff2ae2842cfaa95353547'
CONTRACT_SHA = '15b5138123144a4c31cb557272788cb9c28901728b5633cfa66921ff349e5b82'
PRIOR_CTX = 'ef53a5cc5795929b5477b40550cab61ee709156112a0f2bc7a2deb071845552c'
GUARDS_SHA = '88195ddc08a502b59d081220a443597ffc532f71f33f320df8db17b83a822cbb'


def validate_scope_and_contract(a):
    require(sha(a.root_execution_scope) == ROOT_SCOPE_SHA, 'Actual ROOT727f scope is mandatory')
    root = read(a.root_execution_scope)
    scope = root['authorized_actual_new_synthesis_scope']
    require(scope['source'] == SOURCE_NO and scope['book_order'] == BOOK_ORDER and
            scope['sentence'] == TARGET and scope['display'] == DISPLAY and scope['utterance'] == PROJECTED and
            scope['new_context_SHA256'] == CTX and scope['private_shadow_SHA256'] == SHADOW,
            'Wrong actual finite ROOT source/context/mother scope')
    require(sha(a.contract) == CONTRACT_SHA and sha(a.contract_guards) == GUARDS_SHA and
            sha(a.prior_context) == PRIOR_CTX and sha(a.new_context) == CTX,
            'Exact immutable CPU/context contract files required')
    modspec = importlib.util.spec_from_file_location('_exact_S2_contract_guards', a.contract_guards)
    guards = importlib.util.module_from_spec(modspec); modspec.loader.exec_module(guards)
    contract = read(a.contract)
    guards.validate_data(a.request.read_bytes(), a.shadow.read_bytes(),
                         a.prior_context.read_bytes(), a.new_context.read_bytes(), contract)
    return contract, guards


@contextlib.contextmanager
def exact_context_namespace(tools, work, old_bytes, new_bytes, restoration):
    paths = [Path(tools) / '发音词典/按语境读音.json', Path(work) / '按语境读音.json']
    require(hashlib.sha256(old_bytes).hexdigest() == PRIOR_CTX and
            hashlib.sha256(new_bytes).hexdigest() == CTX, 'Wrong bounded context payloads')
    require(len({str(p.resolve()) for p in paths}) == 2 and
            all(p.is_file() and not p.is_symlink() and p.read_bytes() == old_bytes for p in paths),
            'Both declared oldef53 paths must be genuine identical regular files before any write')
    installed = []
    try:
        for p in paths:
            fd, tmp = tempfile.mkstemp(prefix='.exact-S2-ctx-', dir=p.parent)
            try:
                with os.fdopen(fd, 'wb') as out: out.write(new_bytes)
                require(sha(tmp) == CTX, 'Staged new context checksum mismatch')
                os.replace(tmp, p); installed.append(p)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
        require(all(p.read_bytes() == new_bytes for p in paths), 'Two exact new context paths required')
        yield
    finally:
        for p in installed:
            fd, tmp = tempfile.mkstemp(prefix='.restore-S2-ctx-', dir=p.parent)
            try:
                with os.fdopen(fd, 'wb') as out: out.write(old_bytes)
                require(sha(tmp) == PRIOR_CTX, 'Restored old context checksum mismatch')
                os.replace(tmp, p)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
        require(all(p.read_bytes() == old_bytes for p in paths), 'Original oldef53 context restore failed')
        restoration['both_T_and_W_original_ef53_context_bytes_restored'] = True


def witness_nontarget_inputs(m, request, prior_context, current_context, voice_id, portable):
    """Real original tokenizer/_pron projections only; no native/cached model methods called."""
    source_utterances = [('title', request['title_en'])] + [
        ('S' + str(i), ' '.join(c['en'] for c in s['chunks']))
        for i, s in enumerate(request['sentences'], 1) if i != 2]
    require(len(source_utterances) == 19, 'Title plus18 nonS2 sentences required')
    initial_context, initial_fix = m.PRON_CTX, copy.deepcopy(m.PRON_FIX)
    try:
        phases = []
        for ctx in (prior_context, current_context):
            m.PRON_CTX = ctx
            rows = []
            for sid, display in source_utterances:
                logical = m.spoken(display)
                ending = request.get('结尾句', {}).get(sid, {})
                require(not ending.get('前段单独合成'), 'This finite68 witness requires the actually selected full-sentence ending input')
                speeds = sorted({.95} | {float(ending[k]) for k in ('前段语速', '最后一段语速', '整句语速') if k in ending})
                for actual_speed in speeds:
                    for method, model, kw in [
                        ('create', 'kokoro-v1.0.onnx', {}),
                        ('create_timed', 'kokoro-v1.0-timed.onnx', {'clause_pause': 0, 'sentence_pause': 0})]:
                        captured = []
                        def capture(text, voice, speed=1.0, lang='en-us', **kwargs):
                            vh = hashlib.sha1(m.np.ascontiguousarray(voice).tobytes()).hexdigest()
                            captured.append((text, vh, float(speed), lang, dict(kwargs)))
                        m._pron(capture)(logical, voice=m.V, speed=actual_speed, lang='en-us', **kw)
                        require(len(captured) == 1, 'One pure nonTarget projection required')
                        text, vh, speed, lang, kwargs = captured[0]
                        require(vh == voice_id, 'Unexpected nonTarget voice witness')
                        rows.append({'sentence': sid, 'method': method, 'text': text, 'voice_sha1': vh,
                            'speed': speed, 'lang': lang, 'kwargs': kwargs,
                            'cache_key': input_key(method, portable[model], text, vh, speed, lang, kwargs)})
            phases.append(rows)
        require(phases[0] == phases[1], 'NonS2 original postpron tuple/key changed')
        return {'title_plus18_nontarget_original_postpron_rows': phases[1],
                'before_after_context_all_exact': True, 'actual_model_methods_called': 0,
                'not_claiming_native_whole_or_nontarget_audio_replayed': True}
    finally:
        m.PRON_CTX = initial_context
        m.PRON_FIX.clear(); m.PRON_FIX.update(initial_fix)



def verify_eight_original_modules(tools, video_root):
    expected = {'make_video': '0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36', 'title_anim': 'c46ad2ac19434c1b4031235273bc57080e53e2c14cafcea956d3bbd7ddeabf12', 'title2': '681f5fff1f17174f3d3d627c9ce27077977c2cc02b6de79181bb43db9a540011', 'render': '477a516f7100ac05dab15d3b176e2d8c49779aa4bd8713087b737f4d25833b67', '对正量': 'd6adf6ba7a628614a88278c461f753584e5242a8d12995ca42f18ecfbd9ef97f', '出片指纹': 'ef589d2ad0bc9e1806a37161c81e727b7f900d4de490d05d4c74755b392b91a9', '响度一致性核对': '2bb89e427ec014a7fc1b4cc46ea6a11f91a786930f91e8cec720e0307940b85b', 'clean': '86b3872cbca83437e24da2c7ada5fffd916f06cacdd2b32fee2a78c9b134178d'}
    work = Path(video_root) / 'video'
    actual = {}
    for name, digest in expected.items():
        canonical = Path(tools) / (name + '.py')
        runtime = next((p for p in (Path(video_root) / 'tts' / (name + '.py'), work / (name + '.py')) if p.is_file()), None)
        require(runtime is not None and sha(canonical) == sha(runtime) == digest,
                'Original G27 eight-module physical identity changed: ' + name)
        actual[name] = {'canonical_SHA256': sha(canonical), 'runtime_SHA256': sha(runtime)}
    return actual


def run_with_exact_context(a):
    restoration = {}
    rc = 1
    modules_before = None
    try:
        modules_before = verify_eight_original_modules(a.tools, a.video_root)
        validate_scope_and_contract(a)
        with exact_context_namespace(a.tools, a.video_root / 'video',
                                     a.prior_context.read_bytes(), a.new_context.read_bytes(), restoration):
            rc = run(a)
    except BaseException as error:
        traceback.print_exc()
        report = read(a.output) if a.output.exists() else {'completed': False, 'quality_acceptance': False}
        report['completed'] = False
        report['outer_context_or_contract_error'] = {'type': type(error).__name__, 'detail': str(error)}
        save(a.output, report)
    finally:
        report = read(a.output) if a.output.exists() else {'completed': False, 'quality_acceptance': False}
        report.update(restoration)
        if modules_before is not None:
            try:
                modules_after = verify_eight_original_modules(a.tools, a.video_root)
                require(modules_after == modules_before, 'Original G27 module bytes changed')
                report['all_original_G27_eight_module_files_exact_before_after'] = True
            except BaseException as error:
                report['completed'] = False
                report['original_G27_restore_error'] = str(error)
        report['root_actual727f_scope_SHA256'] = ROOT_SCOPE_SHA
        report['new_context_SHA256'] = CTX
        report['original_restored_context_SHA256'] = PRIOR_CTX
        if not restoration.get('both_T_and_W_original_ef53_context_bytes_restored'):
            report['completed'] = False
        save(a.output, report)
    return 0 if rc == 0 and report['completed'] else 1


def run(a):
    report = {'kind': 'one_independent_target_only_two_original_model_mothers', 'source_id': SOURCE_NO,
              'book_order': BOOK_ORDER, 'quality_acceptance': False, 'formal_acceptance': False,
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
                            ('authority', a.authority), ('raw_audio_authority', a.raw_audio_authority), ('code_adoption', a.code_adoption),
                            ('GEN', a.GEN), ('MD', a.MD), ('overlay', a.overlay),
                            ('input_H', a.input_H),
                            ('pending_text', a.pending_text), ('sentence_confirmations', a.sentence_confirmations), ('certification_report', a.certification_report)]:
            require(sha(path) == profile['file_sha256'][label], 'Wrong pinned input: ' + label)
        require(sha(a.request) == SOURCE and sha(a.shadow) == SHADOW and sha(a.authority) == AUTH,
                'Exact source/shadow/user authorization required')
        require(len(a.execution_adoption_sha256) == 64 and
                sha(a.execution_adoption) == a.execution_adoption_sha256,
                'Launcher must pin separate root executable/mother-scope adoption')
        validate_execution_adoption(read(a.execution_adoption), sha(__file__))
        contract, contract_guards = validate_scope_and_contract(a)
        require(sha(a.certification_report) == CERTIFICATE_SHA, 'Only actual43693920217 combined20 certificate accepted')
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
                    name = '_source' + SOURCE_NO + '_' + TARGET + '_two_mothers_exact'
                    require(name not in sys.modules, 'Fresh module namespace required')
                    spec = importlib.util.spec_from_file_location(name, W / 'make_video.py')
                    m = importlib.util.module_from_spec(spec)
                    sys.modules[name] = m
                    try:
                        spec.loader.exec_module(m)
                        provider_file = Path(inspect.getsourcefile(type(m.k)))
                        require(sha(provider_file) == PROVIDER_SOURCE_SHA, 'Exact original Kokoro0.6.1 class source required for delegated method guard')
                        delegate_file = Path(__file__).with_name('raw_create_delegate_guard.py')
                        require(sha(delegate_file) == DELEGATE_GUARD_SHA, 'Pinned raw internal-delegate guard module required')
                        delegate_spec = importlib.util.spec_from_file_location('_exact_raw_internal_delegate_guard', delegate_file)
                        delegate_module = importlib.util.module_from_spec(delegate_spec); delegate_spec.loader.exec_module(delegate_module)
                        report['original_Kokoro061_class_source_SHA256'] = sha(provider_file)
                        report['native_method_entry_count_is_not_ONNX_session_run_telemetry'] = True
                        m._SPOKEN_SOURCE_NO = SOURCE_NO
                        require(m._OLDF and sha(m._OLDF) == OLDREG, 'Original G72 registry required')
                        require(sha(m._cand) == DICT and m._CTX_PATH and sha(m._CTX_PATH) == CTX,
                                'Fresh maker loaded a different dictionary context')
                        require(str(m.SENT_NO.get(DISPLAY)) == SOURCE_NO, 'Source must be installed before import')
                        rule = m._speech_rule(DISPLAY)
                        require(rule and rule['projected'] == PROJECTED and
                                rule['needs_mother_binding'] is False, 'Exact fresh independent target rule required')
                        for table in (m.NONVOICE, m.GRAFT, m.BOOST, m.PGRAFT, m.DEL_AT, m.INSERT_AT, m.VFP):
                            require(DISPLAY not in table, 'Explicit old target physical data must stay retired')
                        require(DISPLAY not in m.ENDING, 'No target ending splice')
                        require(m.SPEED == .95 and m.SR == 24000, 'Original voice rate required')
                        for obj in (m.k, m.KT):
                            sessions = [v for v in vars(obj).values() if hasattr(v, 'get_session_options')]
                            require(bool(sessions), 'Actual model session required')
                            for session in sessions:
                                options = session.get_session_options()
                                require(options.intra_op_num_threads == options.inter_op_num_threads == 1,
                                        'Original model inference must be single-thread')
                        forbidden_public = M / ('_forbid_source' + SOURCE_NO + '_public_cache_export')
                        require(not forbidden_public.exists(), 'Public-export sentinel must be absent')
                        m._REPO_CACHE = str(forbidden_public)
                        np = m.np
                        voice_id = hashlib.sha1(np.ascontiguousarray(m.V).tobytes()).hexdigest()
                        report['real_nontarget_postpron_input_witness'] = witness_nontarget_inputs(
                            m, request, read(a.prior_context), read(a.new_context), voice_id, portable)
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
                        witness = {'source_id': SOURCE_NO, 'target_sentence': TARGET,
                            'actual_original_post_pron_phones': m.phonemes_of(m._synth_punct(logical_text)),
                            'actual_original_post_pron_calls': [
                                {'method': method, 'portable_mid': e['portable_mid'], 'text': e['text'],
                                 'voice_sha1': e['voice_id'], 'speed': .95, 'lang': 'en-us',
                                 'kwargs': e['kwargs'], 'cache_key': e['key']}
                                for method, e in expected.items()]}
                        contract_guards.validate_preinfer_witness(witness, contract)
                        report['real_CI_original_embedded_tokenizer_and_pron_witness'] = witness
                        report['strict_expected_two_key_witness_passed_before_any_native_model_entry'] = True
                        report['planned_input_witness_written_before_possible_inference'] = True
                        save(a.output, report)
                        originals, changed_cells = {}, []
                        native_counts = {'create': 0, 'create_timed': 0}
                        raw_delegate_state = {'active': False, 'calls': 0}
                        raw_create_native = None
                        try:
                            for method, obj in [('create', m.k), ('create_timed', m.KT)]:
                                outer = getattr(obj, method)
                                cached = closure_cell(outer, 'fn').cell_contents
                                require(cached.__code__.co_filename == str(W / 'make_video.py'),
                                        'Original maker cached wrapper required')
                                cell = closure_cell(cached, 'fn')
                                native = cell.cell_contents
                                if method == 'create': raw_create_native = native
                                def native_guard(text, voice, speed=1.0, lang='en-us',
                                                 _method=method, _native=native, **kw):
                                    vh = hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                                    e = validate_model_input(_method, text, vh, speed, lang, kw, expected)
                                    require(not os.environ.get('STRICT_CACHE'), 'Native inference under STRICT forbidden')
                                    require(not e['preexisted'] and not (C / e['key']).exists(),
                                            'Existing target cache cannot be regenerated')
                                    require(native_counts[_method] == 0, 'At most one original call per target method')
                                    native_counts[_method] += 1
                                    if _method == 'create':
                                        require(not raw_delegate_state['active'], 'Nested raw create is forbidden')
                                        raw_delegate_state['active'] = True
                                        try:
                                            return _native(text, voice=voice, speed=speed, lang=lang, **kw)
                                        finally:
                                            raw_delegate_state['active'] = False
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
                                    if obj is m.k and method == 'create_timed':
                                        setattr(obj, method, delegate_module.make_guard(
                                            raw_create_native, originals[(id(obj), method)][2],
                                            expected['create'], m.V,
                                            lambda voice: hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest(),
                                            raw_delegate_state, report))
                                    else:
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
                                    'actual_original_native_method_entries': native_counts[method],
                                    'samples': len(wave), 'SR': int(value[1]), 'dtype': str(wave.dtype),
                                    'array_SHA256': hashlib.sha256(np.ascontiguousarray(wave).tobytes()).hexdigest(),
                                    'actual_raw_array_fingerprint_first12': hashlib.md5(np.ascontiguousarray(wave).tobytes()).hexdigest()[:12] if method == 'create' else None,
                                    'timed_token_count': len(value[2]) if method == 'create_timed' else None})
                            for method, obj in [('create', m.k), ('create_timed', m.KT)]:
                                value = getattr(obj, method)(logical_text, voice=m.V, speed=.95,
                                                            lang='en-us', **expected[method]['logical_kwargs'])
                                require(np.array_equal(value[0], values[method][0]) and value[1] == values[method][1] and (method != 'create_timed' or m._pk.dumps(value[2]) == m._pk.dumps(values[method][2])),
                                        'Original strict cache readback differs')
                            report['actual_native_original_method_entry_count'] = sum(native_counts.values())
                            require(report['actual_native_original_method_entry_count'] <= 2, 'Original logical model-method entry scope exceeded')
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
                proposed_key = 'Linux-native' + SOURCE_NO + '-exact-' + TARGET + '-strong-and-pronCTX-' + runid
                fixture = {'kind': 'independent_source_target_two_original_mother_private_cache_identity_not_quality_acceptance',
                           'source_id': SOURCE_NO, 'book_order': BOOK_ORDER, 'request_SHA256': SOURCE, 'shadow_SHA256': SHADOW,
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
                fixture_path = a.output.parent / (SOURCE_NO + '-' + TARGET + '-two-mother-private-cache-identity.json')
                save(fixture_path, fixture)
                report['private_fixture'] = {'file': fixture_path.name, 'SHA256': sha(fixture_path)}
                with a.cache_path_output.open('a') as out:
                    out.write('cache_key=' + proposed_key + '\ncache_paths<<EXACTTARGETPRIVATE\n' +
                              '\n'.join(str(C / name) for name in names) + '\nEXACTTARGETPRIVATE\n')
        except BaseException as error:
            report['completed'] = False
            report['private_fixture_or_transport_error'] = {'type': type(error).__name__, 'detail': str(error)}
        save(a.output, report)
    return 0 if report['completed'] else 1


def main():
    p = argparse.ArgumentParser()
    for key in ('tools', 'video-root', 'profile', 'request', 'shadow', 'history', 'GEN', 'MD',
                'authority', 'raw-audio-authority', 'code-adoption', 'execution-adoption', 'overlay', 'certification-report',
                'input-H', 'pending-text', 'sentence-confirmations', 'output', 'cache-path-output',
                'root-execution-scope', 'contract', 'contract-guards', 'prior-context', 'new-context'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--execution-adoption-sha256', required=True)
    return run_with_exact_context(p.parse_args())


if __name__ == '__main__':
    sys.exit(main())
