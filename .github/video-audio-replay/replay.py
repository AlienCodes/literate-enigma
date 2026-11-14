#!/usr/bin/env python3
"""Read-only replay of an already public failed video's exact private PCM.

This never creates an acceptance/final verdict. Only scalar diagnostics leave
the private restored machine; no waveform/cache/model/GT file is published.
"""
import base64
import hashlib
import importlib.util
import json
import os
import pickle
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import soundfile as sf
import numpy as np

ROOT = Path.cwd()
TASK = ROOT / '.github/video-audio-replay'
NO = os.environ['ARTICLE_NO'].zfill(2)
assert NO in {'10', '11', '12', '44', '51'}
M = Path(os.environ['RUNNER_TEMP']) / 'completion-machine'
W = M / 'video'
T = ROOT / '视频/工具'
OUT = ROOT / f'audio-replay-{NO}-public'
OUT.mkdir(exist_ok=True)
PRIVATE_LOG = M / f'readonly-audio-replay-{NO}'
PRIVATE_LOG.mkdir(exist_ok=True)
ENV = {k: v for k, v in os.environ.items() if k not in {
    'GH_TOKEN', 'GITHUB_TOKEN', 'OLD_IV_VOID', 'AUDIO_ONLY', 'VIDEO_S', 'VOICE', 'AFFILE'}}
ENV.update({'STRICT_CACHE': '1', 'XG_NOPUSH': '1', 'VIDEO_ROOT': str(M),
            'QC_DIR': str(M / 'qc_independent'), 'XG_P': str(ROOT), 'XG_TOOLS': str(T)})
ENV['CACHE_LOG'] = str(PRIVATE_LOG / 'actual-maker-cache-keys.txt')
status = {'article': NO, 'purpose': 'read-only exact failed-draft PCM replay for diagnosis',
          'passed': False, 'quality_acceptance': False, 'final_deliverable': False,
          'original_quality_thresholds_changed': False, 'private_GT_cache_model_PCM_exported': False,
          'source_failed_run': 43522684973, 'replay_run': os.environ['GITHUB_RUN_ID']}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save():
    (OUT / f'{NO}-readonly-replay-status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')


def run(args, label, *, audio_only=False):
    status['stage'] = label
    save()
    path = PRIVATE_LOG / (label + '.log')
    env = {**ENV, **({'AUDIO_ONLY': '1'} if audio_only else {})}
    with path.open('w') as stream:
        process = subprocess.run(list(map(str, args)), cwd=W, env=env,
                                 stdout=stream, stderr=subprocess.STDOUT)
    lines = path.read_text(errors='replace').splitlines()
    status.setdefault('original_processes', {})[label] = {
        'exit': process.returncode,
        'public_scalar_error_lines': [line[:1100].replace(str(M), '<private-machine>') for line in lines
                                      if any(mark in line for mark in (
                                          '【停止】', 'Error', 'Exception', 'cut tail=', 'edit raw ',
                                          'A10 edge violations', 'extra non-zero runs'))][-60:]}
    save()
    return process.returncode


def api(path, data=None, method='GET'):
    args = ['gh', 'api', 'repos/AlienCodes/literate-enigma/' + path]
    if method != 'GET':
        args += ['-X', method]
    if data is not None:
        args += ['--input', '-']
    raw = subprocess.check_output(args, input=None if data is None else json.dumps(data).encode())
    return json.loads(raw)


def publish_public_scalars():
    """Each article writes its own isolated branch, so parallel jobs cannot race."""
    branch = f'codex/audio-replay-{os.environ["GITHUB_RUN_ID"]}-{NO}'
    assert re.fullmatch(r'codex/audio-replay-\d+-\d{2}', branch)
    assert branch not in {'main', 'master', 'codex/all-deliverables-20261113'}
    master = api('git/ref/heads/master')['object']['sha']
    assert master == '6355a02864ebae616b693200d9d26f74f5da80e9'
    commit = os.environ['GITHUB_SHA']
    prefix = f'public-audio-replay/{os.environ["GITHUB_RUN_ID"]}/{NO}'
    allowed = {f'{NO}-readonly-replay-status.json', f'{NO}-reference-gain-diagnostic.json',
               f'{NO}-native-cache-scalars.json'}
    updates, files = [], []
    for path in sorted(OUT.iterdir()):
        assert path.name in allowed and path.is_file() and not path.is_symlink()
        data = path.read_bytes()
        assert len(data) <= 2 * 1024 * 1024
        json.loads(data)
        blob = api('git/blobs', {'content': base64.b64encode(data).decode(), 'encoding': 'base64'}, 'POST')
        assert blob['sha'] == hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        name = prefix + '/' + path.name
        updates.append({'path': name, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
        files.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    manifest = {'kind': 'public-observation-only-not-quality-acceptance', 'run_id': os.environ['GITHUB_RUN_ID'],
                'source_failed_run': status['source_failed_run'], 'article': NO, 'quality_acceptance': False,
                'private_cache_GT_model_exports': False, 'files': files}
    data = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    blob = api('git/blobs', {'content': base64.b64encode(data).decode(), 'encoding': 'base64'}, 'POST')
    updates.append({'path': prefix + '/manifest.json', 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    previous = subprocess.run(['gh', 'api', 'repos/AlienCodes/literate-enigma/git/ref/heads/' + branch],
                              capture_output=True, text=True)
    if previous.returncode == 0:
        parent = json.loads(previous.stdout)['object']['sha']
    else:
        assert '404' in previous.stderr
        parent = commit
    base = api('git/commits/' + parent)['tree']['sha']
    tree = api('git/trees', {'base_tree': base, 'tree': updates}, 'POST')['sha']
    result = api('git/commits', {'tree': tree, 'parents': [parent],
                                'message': f'Preserve diagnostic-only replay scalars for article{NO} [skip ci]'}, 'POST')['sha']
    if previous.returncode == 0:
        api('git/refs/heads/' + branch, {'sha': result, 'force': False}, 'PATCH')
    else:
        api('git/refs', {'ref': 'refs/heads/' + branch, 'sha': result}, 'POST')
    assert api('git/ref/heads/master')['object']['sha'] == master
    print(json.dumps({'article': NO, 'public_branch': branch, 'commit': result,
                      'quality_acceptance': False, 'public_json_files': len(files)}))


def export_native_cache_scalars():
    """Read only the producer's genuine logged cache entries; export no arrays."""
    key_log = Path(ENV['CACHE_LOG'])
    keys = sorted(set(line for line in key_log.read_text().splitlines()
                      if re.fullmatch(r'[0-9a-f]{40}\.pkl', line)))
    rows = []
    for key in keys:
        path = M / 'tts/cache_tts' / key
        assert path.is_file() and not path.is_symlink()
        marker = path.with_name(path.name + '.单线程')
        item = {'native_key': key, 'pkl_sha256': sha(path), 'single_thread_marker_present': marker.is_file()}
        if marker.is_file():
            item['single_thread_marker_value'] = marker.read_text().strip()
            item['single_thread_marker_matches'] = item['single_thread_marker_value'] == item['pkl_sha256'][:16]
        with path.open('rb') as stream:
            value = pickle.load(stream)
        item['container_type'] = type(value).__name__
        item['container_length'] = len(value)
        if isinstance(value, tuple) and len(value) in (2, 3) and isinstance(value[0], np.ndarray):
            samples = value[0]
            item.update({'unprocessed_array_dtype': str(samples.dtype), 'unprocessed_array_shape': list(samples.shape),
                         'unprocessed_array_sha256': hashlib.sha256(np.ascontiguousarray(samples).tobytes()).hexdigest(),
                         'sample_rate': int(value[1])})
        rows.append(item)
    output = {'purpose': 'native producer cache provenance scalars only; no raw mother material exported',
              'article': NO, 'quality_acceptance': False, 'source_sha256': status['public_failed_binding']['source_sha256'],
              'producer_pcm_sha256': status['actual_private_pcm_sha256'], 'maker_sha256': sha(W / 'make_video.py'),
              'original_cache_key_log_sha256': sha(key_log),
              'models_sha256': {name: sha(M / 'tts' / name) for name in ('kokoro-v1.0.onnx', 'kokoro-v1.0-timed.onnx', 'voices-v1.0.bin', 'voice_mb.npy')},
              'cache_entries': rows}
    (OUT / f'{NO}-native-cache-scalars.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')


def original_independent_selftest():
    """Execute the exact original five-defect block, with its original audit."""
    path = T / '交付核查.py'
    source = path.read_text()
    start = source.index('    # 核查程序自检（阳性对照')
    end = source.index("    c, o = run(['python3', f'{T}/独立复核/audit.py', no], env)", start)
    block = textwrap.dedent(source[start:end])
    steps = []
    lines = []
    def original_run(args, extra=None):
        process = subprocess.run(list(map(str, args)), cwd=W, env={**ENV, **(extra or {})},
                                 capture_output=True, text=True, errors='replace')
        return process.returncode, process.stdout + process.stderr
    def original_step(name, passed, detail=''):
        steps.append({'name': name, 'original_step_passed': bool(passed)})
        lines.append(('✔ ' if passed else '✘ ') + name + '\n' + detail)
    previous = Path.cwd()
    try:
        os.chdir(W)
        exec(compile(block, str(path) + '#unchanged-independent-selftest-block', 'exec'),
             {'os': os, 'no': NO, 'T': str(T), 'run': original_run, 'step': original_step})
    finally:
        os.chdir(previous)
    log = PRIVATE_LOG / 'original-independent-selftest.log'
    log.write_text('\n'.join(lines))
    status['original_independent_selftest'] = {
        'original_checker_sha256': sha(path), 'unmodified_block_sha256': hashlib.sha256(block.encode()).hexdigest(),
        'original_audit_sha256': sha(T / '独立复核/audit.py'), 'steps': steps,
        'all_original_steps_passed': bool(steps) and all(row['original_step_passed'] for row in steps)}
    return log


try:
    request = TASK / 'request' / NO
    status['source_failed_run'] = int(json.loads((request / 'source-run.json').read_text())['run_id'])
    proof = json.loads((request / 'failed-draft-proof.json').read_text())
    fp = json.loads((request / 'failed-draft-fingerprint.json').read_text())
    source = request / 'failed-working-source.json'
    assert proof['article'] == NO and proof['passed'] is False and proof['acceptance'] is False
    assert sha(source) == proof['source_sha256']
    assert fp['脚本'] == proof['source_sha256'][:16]
    assert fp['配音'] == proof['internal_pcm_sha256'][:16]
    assert fp['视频'] == proof['video_sha256'][:16]
    status['public_failed_binding'] = {'source_sha256': sha(source), 'proof_sha256': sha(request / 'failed-draft-proof.json'),
                                       'failed_public_video_sha256': proof['video_sha256'],
                                       'expected_exact_private_pcm_sha256': proof['internal_pcm_sha256']}
    alias = Path('/home/user/postgraduate-vocabulary')
    if not alias.exists():
        subprocess.run(['sudo', 'mkdir', '-p', str(alias.parent)], check=True)
        subprocess.run(['sudo', 'ln', '-s', str(ROOT), str(alias)], check=True)
    assert alias.resolve() == ROOT.resolve()
    W.mkdir(parents=True, exist_ok=True)
    assert run(['python3', T / '出片指纹.py', '--拷', W], 'copy-original-modules') == 0
    # Prove the actual maker modules match those that wrote the failed video.
    spec = importlib.util.spec_from_file_location('original_fingerprint', T / '出片指纹.py')
    fingerprint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fingerprint)
    modules = fingerprint.清单(fingerprint.工作目录搜(str(W)))
    assert set(modules) == set(fp['程序']), 'Original maker module set differs from actual failed video.'
    assert all(sha(path)[:16] == fp['程序'][name] for name, path in modules.items()), 'Original maker module content differs from actual failed video.'
    status['original_failed_maker_modules_match'] = True
    (W / 'scripts').mkdir(exist_ok=True)
    shutil.copyfile(source, W / f'scripts/{NO}.json')
    if not (W / 'fonts').exists():
        (W / 'fonts').symlink_to(T / 'fonts', target_is_directory=True)
    assert run(['python3', W / 'make_video.py', W / f'scripts/{NO}.json',
                W / f'_readonly-replay-{NO}.m4a'], 'exact-cached-audio-replay', audio_only=True) == 0
    actual = sha(W / f'work_{NO}/a.wav')
    status['actual_private_pcm_sha256'] = actual
    assert actual == proof['internal_pcm_sha256'], 'Replayed PCM differs from actual failed-draft proof; no independent diagnosis allowed.'
    assert sha(W / f'scripts/{NO}.json') == proof['source_sha256']
    status['exact_failed_pcm_reproduced'] = True
    export_native_cache_scalars()
    overlay = TASK / 'approved-reference-overlay/synth.py'
    if overlay.is_file():
        contract = json.loads((overlay.parent / 'contract.json').read_text())
        actual = T / '独立复核/synth.py'
        assert sha(actual) == contract['original_sha256'] and sha(overlay) == contract['patched_sha256']
        shutil.copyfile(overlay, actual)
        status['approved_reference_overlay'] = contract
    # Fresh GT only: do not allow a cached, incompatible CPU reference to be reused.
    removed_gt = []
    for path in sorted((M / 'qc_independent/gt').glob(NO + '_*')):
        assert path.is_file() and not path.is_symlink()
        removed_gt.append({'name': path.name, 'sha256': sha(path)})
        path.unlink()
    status['fresh_reference_removed_previous_files'] = removed_gt
    for program in ('synth.py', 'labels.py'):
        assert run(['python3', T / '独立复核' / program, NO], 'original-' + program[:-3]) == 0
    selftest_log = original_independent_selftest()
    # A non-zero audit verdict is expected for a failed candidate and remains a failure.
    run(['python3', T / '独立复核/audit.py', NO], 'original-audit')
    diagnostic = TASK / 'diagnose_reference_gain.py'
    assert run(['python3', diagnostic, '--video-root', M, '--qc-dir', M / 'qc_independent',
                '--no', NO, '--tools', T, '--post-log', selftest_log,
                '--out', OUT / f'{NO}-reference-gain-diagnostic.json'],
               'scalar-diagnostic') == 0
    result = json.loads((OUT / f'{NO}-reference-gain-diagnostic.json').read_text())
    reference = TASK / 'public-aac-reference' / f'{NO}.wav'
    if reference.is_file():
        contract = json.loads(reference.with_suffix('.json').read_text())
        assert sha(reference) == contract['public_derived_wav_sha256']
        a, sr = sf.read(W / f'work_{NO}/a.wav', dtype='float64')
        public, public_sr = sf.read(reference, dtype='float64')
        assert sr == public_sr == 24000
        spec = importlib.util.spec_from_file_location('diagnostic_alignment', diagnostic)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        at, corr = module.ncc_search(a, public, 25 * sr, 26 * sr)
        result['public_aac_to_actual_pcm_timing'] = {**contract, 'actual_pcm_sha256': sha(W / f'work_{NO}/a.wav'),
            'best_actual_pcm_start_seconds': at / sr, 'ncc': corr,
            'actual_pcm_minus_public_aac_seconds': at / sr - contract['public_video_start_seconds']}
        (OUT / f'{NO}-reference-gain-diagnostic.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    assert 'passed' not in result and result['wav_sha256'] == actual and result['source_sha256'] == proof['source_sha256']
    status['scalar_diagnostic_sha256'] = sha(OUT / f'{NO}-reference-gain-diagnostic.json')
    status['scalar_diagnostic_error'] = result.get('diagnostic_error')
    status['stage'] = 'diagnostic-completed-no-acceptance'
except Exception as exc:
    status['error'] = str(exc).replace(str(M), '<private-machine>')[:1200]
finally:
    save()
    print(json.dumps(status, ensure_ascii=False))
    publish_public_scalars()
