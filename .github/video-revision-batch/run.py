#!/usr/bin/env python3
"""Affected articles only: official cached draft/final pipeline and exact end cards."""
import copy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path.cwd()
TASK = ROOT / '.github/video-revision-batch'
NO = os.environ.get('ARTICLE_NO', '12').zfill(2)
ALLOWED = {f'{n:02d}' for n in range(1, 71)}
SELECTED = json.loads((TASK / 'articles.json').read_text())
assert NO in ALLOWED and NO in SELECTED, f'Article {NO} is outside the pinned revision scope.'
M = Path(os.environ['RUNNER_TEMP']) / 'completion-machine'
W = M / 'video'
T = ROOT / '视频/工具'
OUT = ROOT / f'article{NO}-delivery'
OUT.mkdir(exist_ok=True)
LOG = M / f'article{NO}-local-logs'
LOG.mkdir(parents=True, exist_ok=True)
ENV = {**os.environ, 'XG_P': str(ROOT), 'XG_TOOLS': str(T), 'XG_WORK': str(W),
       'VIDEO_ROOT': str(M), 'XG_NOPUSH': '1', 'STRICT_CACHE': '1'}
for key in ('YAOWENBEN', 'OLD_IV_VOID', 'AUDIO_ONLY', 'VIDEO_S'):
    ENV.pop(key, None)
status = {'article': NO, 'passed': False, 'stage': 'start', 'checks_unchanged': True,
          'strict_production_cache': True, 'pdf_requested': False}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save():
    (OUT / f'{NO}-status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')


def git_bytes(path):
    return subprocess.check_output(['git', 'show', 'HEAD:' + str(path)], cwd=ROOT)


def run(args, log, cwd=W):
    status['stage'] = log
    save()
    destination = LOG / log
    print(NO + ': ' + log, flush=True)
    with destination.open('w') as stream:
        result = subprocess.run(list(map(str, args)), cwd=cwd, env=ENV,
                                stdout=stream, stderr=subprocess.STDOUT)
    text = destination.read_text(errors='replace')
    status.setdefault('check_summaries', {})[log] = [
        line.strip()[:900] for line in text.splitlines()
        if line.startswith(('✔', '✘', f'第{NO}篇', '①', '②', '③', '④', '⑤', '⑥', '【'))
        or ' BAD ' in line][-50:]
    if result.returncode:
        status['failure_details'] = {'step': log, 'exit': result.returncode,
                                     'tail': text.splitlines()[-25:]}
        save()
    return result.returncode, text


def checked(args, log, cwd=W):
    code, _ = run(args, log, cwd)
    if code:
        raise RuntimeError(f'{log}: exit {code}')


def cache_entry(name):
    assert re.fullmatch(r'[A-Za-z0-9_\u4e00-\u9fff.-]+\.(pkl|json)', name), name
    destination = M / 'tts/cache_tts' / name
    if destination.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(git_bytes('视频/配音缓存/' + name))
    marker = '视频/配音缓存/' + name + '.单线程'
    exists = subprocess.run(['git', 'cat-file', '-e', 'HEAD:' + marker], cwd=ROOT,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if exists:
        Path(str(destination) + '.单线程').write_bytes(git_bytes(marker))
    status.setdefault('individual_public_cache_entries_restored', []).append(name)
    save()
    return True


def official(args, label):
    # Retry only the specific cache misses reported by the unchanged producer.
    for attempt in range(100):
        code, text = run(args, f'{label}-{attempt:02}.log')
        if not code:
            return
        for group in (f'做_{NO}', f'定稿_{NO}'):
            for path in (W / group).glob('*.log'):
                text += '\n' + path.read_text(errors='replace')
        missing = re.findall(r'缺(?:配音|调平)缓存\s+([A-Za-z0-9_\u4e00-\u9fff.-]+\.(?:pkl|json))', text)
        restored = [cache_entry(name) for name in sorted(set(missing))]
        if not any(restored):
            # The legacy delivery wrapper drops checker exceptions unless they
            # contain BAD. Preserve actual public diagnostics; never waive them.
            diagnostics = {}
            if (W / f'scripts/{NO}.json').exists():
                shutil.copyfile(W / f'scripts/{NO}.json', OUT / f'{NO}-failed-working-source.json')
            for group in (f'做_{NO}', f'定稿_{NO}'):
                for source in (W / group).glob('*.log'):
                    lines = source.read_text(errors='replace').splitlines()
                    selected = [line[:1600] for line in lines
                                if any(mark in line for mark in
                                       ('✘', 'BAD', 'FAIL', 'Error', 'Exception',
                                        '问题数', '缺配音缓存', '缺调平缓存', '指纹不符'))]
                    if selected:
                        diagnostics[f'{group}/{source.name}'] = selected[-100:]
            if '停顿位置核对' in text and (W / f'work_{NO}/a.wav').exists():
                for name in ('停顿位置精确核对.py', '标点停顿核对.py'):
                    result = subprocess.run(['python3', str(T / name), NO], cwd=W,
                                            env=ENV, capture_output=True, text=True,
                                            errors='replace', timeout=240)
                    lines = (result.stdout + '\n' + result.stderr).splitlines()
                    exceptions = next((i for i, line in enumerate(lines)
                                       if line.startswith('Traceback')), len(lines))
                    evidence = [line[:1600] for line in lines
                                if any(mark in line for mark in
                                       ('BAD', 'FAIL', 'Error', 'Exception', '问题数', '插入'))]
                    evidence += lines[exceptions:][-18:]
                    diagnostics[name] = {'exit': result.returncode, 'actual_output': evidence}
            status.setdefault('failure_details', {})['public_checker_diagnostics'] = diagnostics
            save()
            raise RuntimeError(f'{label}: official quality check failed; see article status JSON')
    raise RuntimeError('Too many individual public cache misses.')


def aac_hash(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                                   '-c:a', 'copy', '-f', 'adts', '-'])
    return hashlib.sha256(raw).hexdigest()


def summary(data):
    note = data['sentences'][-1]['chunks'][-1].get('note', '')
    assert note.count('（简述：') == 1
    value = note[note.index('（简述：'):]
    assert value.count('▸') == 5 and value.rstrip().endswith('）')
    return value


try:
    assert (M / 'tts/kokoro-v1.0.onnx').exists(), 'Original warm machine cache was not restored.'
    W.mkdir(parents=True, exist_ok=True)
    # Keep restored historical logs internal; report only this run's checks.
    for name in (f'做_{NO}', f'定稿_{NO}'):
        old = W / name
        if old.exists():
            history = LOG / ('restored-' + name)
            if history.exists():
                shutil.rmtree(history)
            shutil.move(str(old), str(history))
    fonts = ROOT / '视频/资源/字体'
    if not fonts.exists():
        fonts.parent.mkdir(parents=True, exist_ok=True)
        fonts.symlink_to(T / 'fonts', target_is_directory=True)
    alias = Path('/home/user/postgraduate-vocabulary')
    if not alias.exists():
        subprocess.run(['sudo', 'mkdir', '-p', str(alias.parent)], check=True)
        subprocess.run(['sudo', 'ln', '-s', str(ROOT), str(alias)], check=True)
    assert alias.resolve() == ROOT.resolve(), 'Canonical repository alias points elsewhere.'
    if not (W / 'fonts').exists():
        (W / 'fonts').symlink_to(T / 'fonts', target_is_directory=True)
    checked(['python3', T / '新管/印章.py'], 'original-restored-stamp.log')
    status['real_restored_stamp_validated'] = True
    checked(['python3', T / '出片指纹.py', '--拷', W], 'canonical-module-copy.log', ROOT)
    request = TASK / 'request' / NO
    script_rel = Path(f'视频/脚本/{NO}.json')
    gen_rel = Path(f'视频/工具/初稿生成/gen{NO}.py')
    manuscripts = list((request / '新版定稿').glob(f'{NO}-*.md'))
    assert len(manuscripts) == 1, 'Attach exactly one revised manuscript for this article.'
    files = [(request / script_rel, ROOT / script_rel),
             (request / gen_rel, ROOT / gen_rel),
             (manuscripts[0], ROOT / '新版定稿' / manuscripts[0].name)]
    pending = request / f'视频/制作记录/{NO}_待改清单.md'
    if pending.exists():
        files.append((pending, ROOT / f'视频/制作记录/{NO}_待改清单.md'))
    baseline = json.loads((ROOT / script_rel).read_text())
    for source, destination in files:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    requested = json.loads((ROOT / script_rel).read_text())
    assert requested['no'] == NO
    assert requested['title_en'] == baseline['title_en']
    def english(data):
        return [re.sub(r'\{\{.*?\}\}', '', ' '.join(c['en'] for c in sentence['chunks']))
                .replace('**', '').split() for sentence in data['sentences']]
    assert english(requested) == english(baseline), 'Spoken English changed.'
    requested_summary = summary(requested)
    status['request_source_sha256'] = {str(dst.relative_to(ROOT)): sha(src) for src, dst in files}
    authorization = json.loads((request / 'user-authorization.json').read_text())
    assert authorization['篇'] == NO and authorization['原话'].strip()
    assert '定稿' in authorization['用于'] and '撤回' not in authorization['用于']
    agreement = T / '用户同意记录.json'
    records = json.loads(agreement.read_text())
    if authorization not in records['记录']:
        records['记录'].append(authorization)
    agreement.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    (OUT / f'{NO}-user-authorization.json').write_text(json.dumps(authorization, ensure_ascii=False, indent=2) + '\n')
    (W / 'scripts').mkdir(exist_ok=True)
    # Write after genNN, so 做.py consumes the exact supplied script and preserves audio confirmations.
    (W / f'scripts/{NO}.json').write_bytes((ROOT / script_rel).read_bytes())
    accepted = json.loads((TASK / 'accepted-videos.json').read_text())['videos']
    reference = next(item for item in accepted if item['id'] == NO)
    source_video = ROOT / reference['path']
    assert source_video.exists(), 'Accepted source MP4 must be sparsely checked out.'
    assert sha(source_video) == reference['sha256'], 'Accepted source MP4 hash mismatch.'
    accepted_aac = aac_hash(source_video)
    status['accepted_source'] = {**reference, 'aac_adts_sha256': accepted_aac}
    start_wav = sha(W / f'work_{NO}/a.wav') if (W / f'work_{NO}/a.wav').exists() else None
    official(['bash', T / '新管/做.sh', NO, '--不推'], 'canonical-draft')
    official(['bash', T / '新管/定稿.sh', NO], 'canonical-final4K')
    checked(['python3', T / '新管/印章.py'], 'original-stamp-after-production.log')
    current = json.loads((W / f'scripts/{NO}.json').read_text())
    assert re.sub(r'\s+', '', summary(current)) == re.sub(r'\s+', '', requested_summary)
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(W / f'{NO}.mp4')]))
    video = next(s for s in info['streams'] if s['codec_type'] == 'video')
    assert (video['width'], video['height']) == (3840, 2160)
    canonical = W / f'{NO}.mp4'
    status['canonical_video_sha256'] = sha(canonical)
    status['canonical_aac_adts_sha256'] = aac_hash(canonical)
    status['canonical_pipeline_passed'] = True
    status['cached_input_wav_sha256'] = start_wav
    status['final_wav_sha256'] = sha(W / f'work_{NO}/a.wav')
    save()
    canonical_aac = aac_hash(canonical)
    if NO in {'10', '12', '51'}:
        # Root supplies actual approved audio-change validation. No gain/overlay implementation is assumed here.
        audio_qc = TASK / 'audio-qc.py'
        assert audio_qc.exists(), f'Root must attach approved audio QC for article {NO}.'
        evidence = OUT / f'{NO}-approved-audio-qc.json'
        checked(['python3', audio_qc, '--article', NO, '--accepted-source', source_video,
                 '--canonical-video', canonical, '--work', W, '--request', request,
                 '--output', evidence], 'approved-audio-qc.log', ROOT)
        audio_evidence = json.loads(evidence.read_text())
        assert audio_evidence.get('article') == NO and audio_evidence.get('passed') is True
        status['approved_audio_qc'] = audio_evidence
        status['approved_audio_qc_program_sha256'] = sha(audio_qc)
    else:
        assert canonical_aac == accepted_aac, 'Canonical AAC differs from the accepted prior voice.'
    status['accepted_prior_aac_identical'] = canonical_aac == accepted_aac
    save()
    # Original tested end_card algorithm, with only its explicit source/summary loader supplied.
    module_file = ROOT / '.github/video-batch/run.py'
    spec = importlib.util.spec_from_file_location('revision_exact_summary', module_file)
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    batch.BASE = commit
    # These videos have just been produced by the current official maker.
    # Historical67/69 references describe old pictures and must not replace them.
    batch.PICTURE_REFERENCES = {}
    batch.OUT = M / f'{NO}-exact-summary'
    batch.OUT.mkdir(exist_ok=True)
    batch.LOCAL_SOURCE = str(canonical)
    batch.LOCAL_SCRIPT = current
    batch.summary = lambda no: requested_summary
    body = inspect.getsource(batch.end_card)
    lo = body.index('    paths = tree_paths()')
    hi = body.index('    info = probe(source)')
    loader = ("    originals = [f'new-canonical-4K:{no}']\n"
              "    source = OUT / f'{no}-original.mp4'\n"
              "    source.write_bytes(Path(LOCAL_SOURCE).read_bytes())\n"
              "    data = copy.deepcopy(LOCAL_SCRIPT)\n"
              "    changed = add_summary(data, no)\n")
    exec(compile(body[:lo] + loader + body[hi:], str(module_file) + '#revision-explicit-source', 'exec'), batch.__dict__)
    os.chdir(ROOT)
    from contextlib import redirect_stdout, redirect_stderr
    with (LOG / 'exact-summary.log').open('w') as log:
        with redirect_stdout(log), redirect_stderr(log):
            batch.end_card(NO)
    processed = list(batch.OUT.glob('*.mp4'))
    assert len(processed) == 1, processed
    timing = json.loads((batch.OUT / f'{NO}-verification.json').read_text())
    assert timing['end_page_frames'] == 60 and timing['end_page_seconds'] == 2
    assert timing['original_audio_identical'] and timing['original_audio_packet_timings_identical']
    assert aac_hash(processed[0]) == canonical_aac, 'Exact-card processing changed the canonical AAC stream.'
    if NO not in {'10', '12', '51'}:
        assert aac_hash(processed[0]) == accepted_aac, 'Final AAC differs from accepted prior voice.'
    final = OUT / f'{NO}-4K-读完即转简述2秒.mp4'
    shutil.copyfile(processed[0], final)
    timing.update({'source_kind': 'new-canonical-4K', 'source_commit': commit,
                   'canonical_source_video_sha256': status['canonical_video_sha256'],
                   'accepted_prior_video_sha256': reference['sha256'],
                   'accepted_prior_aac_adts_sha256': accepted_aac,
                   'canonical_aac_adts_sha256': canonical_aac,
                   'final_canonical_aac_identical': True,
                   'accepted_prior_aac_identical': canonical_aac == accepted_aac, 'canonical_pipeline_passed': True})
    (OUT / f'{NO}-summary-verification.json').write_text(json.dumps(timing, ensure_ascii=False, indent=2) + '\n')
    (OUT / f'{NO}-source.json').write_text(json.dumps(current, ensure_ascii=False, indent=1) + '\n')
    shutil.copyfile(str(canonical) + '.指纹.json', OUT / f'{NO}-canonical-fingerprint.json')
    for name in (f'{NO}-简述.png', f'{NO}-转场前.png', f'{NO}-简述首帧.png', f'{NO}-简述末帧.png'):
        shutil.copyfile(batch.OUT / name, OUT / name)
    status.update({'passed': True, 'stage': 'final4K-passed', 'video_sha256': sha(final),
                   'width': 3840, 'height': 2160, 'accepted_prior_aac_identical': canonical_aac == accepted_aac,
                   'summary_seconds': 2, 'summary_frames': 60,
                   'summary_start_seconds': timing['summary_start_seconds'],
                   'delay_after_voice_seconds': timing['delay_after_voice_seconds']})
    save()
    print(json.dumps(status, ensure_ascii=False), flush=True)
except Exception as exc:
    status['passed'] = False
    status['error'] = str(exc)
    save()
    print(json.dumps(status, ensure_ascii=False), flush=True)
    raise
