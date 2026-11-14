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
import time

ROOT = Path.cwd()
TASK = ROOT / '.github/video-revision-batch'
NO = os.environ.get('ARTICLE_NO', '12').zfill(2)
ALLOWED = {f'{n:02d}' for n in range(1, 71)}
A21_AUDIO_REPAIRS = {'15', '17', '18', '30'}
CONTROLLED_AUDIO_REPAIRS = {'05', '16', '27', '62', '67'}
APPROVED_AUDIO_REPAIRS = {'10', '12', '44', '51'} | A21_AUDIO_REPAIRS | CONTROLLED_AUDIO_REPAIRS
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
status = {'article': NO, 'passed': False, 'stage': 'start',
          'original_audit_and_quality_thresholds_unchanged': True, 'original_maker_unchanged': True,
          'core_repairs': [],
          'strict_production_cache': True, 'pdf_requested': False}
PRODUCTION_STARTED_NS = None
BASELINE_AUDIO_FILES = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save():
    (OUT / f'{NO}-status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')


def install_certified_core_repairs():
    """Install the reviewed certified repair with its actual original full stamp."""
    folder = TASK / 'certified-core'
    manifest_file = folder / 'manifest.json'
    if not manifest_file.is_file():
        return
    manifest = json.loads(manifest_file.read_text())
    assert manifest['kind'] in {'actual-original-fastcheck-certified-three-core-repair',
                                'actual-original-fastcheck-certified-four-core-repair',
                                'actual-original-fastcheck-certified-five-core-repair',
                                'actual-original-fastcheck-certified-five-core-reviewed-cuts-repair',
                                'actual-original-fastcheck-certified-six-core-case-consistent-producer-repair'}
    allowed = {'视频/工具/草稿声音.sh','视频/工具/句内响度.py','视频/工具/独立复核/synth.py'}
    keep_ending = manifest['kind'] != 'actual-original-fastcheck-certified-three-core-repair'
    if keep_ending:
        allowed.add('视频/工具/结尾句接点.py')
    keep_cuts = manifest['kind'] in {'actual-original-fastcheck-certified-five-core-reviewed-cuts-repair',
                                    'actual-original-fastcheck-certified-six-core-case-consistent-producer-repair'}
    if manifest['kind'] in {'actual-original-fastcheck-certified-five-core-repair',
                            'actual-original-fastcheck-certified-five-core-reviewed-cuts-repair',
                            'actual-original-fastcheck-certified-six-core-case-consistent-producer-repair'}:
        allowed.add('视频/工具/读音核对.py')
    if manifest['kind'] == 'actual-original-fastcheck-certified-six-core-case-consistent-producer-repair':
        allowed.add('视频/工具/make_video.py')
    assert {item['target'] for item in manifest['core_files']} == allowed
    for item in manifest['core_files']:
        source = folder / item['file']
        target = ROOT / item['target']
        assert sha(source) == item['patched_sha256'] and sha(target) == item['original_sha256']
        shutil.copyfile(source, target)
    data = manifest['reviewed_regression_resource']
    assert data['target'] == '视频/工具/新管/回归基准_27.json'
    assert sha(folder / data['file']) == data['sha256']
    shutil.copyfile(folder / data['file'], ROOT / data['target'])
    stamp = manifest['actual_native_fastcheck_stamp']
    assert stamp['target'] == '视频/工具/新管/快测通过.json'
    assert sha(folder / stamp['file']) == stamp['sha256']
    shutil.copyfile(folder / stamp['file'], ROOT / stamp['target'])
    # The unchanged original verifier checks every program's stamp entry;
    # no synthetic or manually constructed stamp is accepted here.
    checked(['python3',T / '新管/印章.py'], 'certified-core-original-stamp-verification.log')
    ENV['XG_KEEP_REVIEWED_GAIN'] = '1'
    if keep_ending:
        ENV['XG_KEEP_REVIEWED_ENDING'] = '1'
    if keep_cuts:
        assert manifest['environment_for_revision_jobs']['XG_KEEP_REVIEWED_CUTS'] == '1'
        ENV['XG_KEEP_REVIEWED_CUTS'] = '1'
    status['core_repairs'] = manifest['core_files']
    status['original_maker_unchanged'] = not any(item['target'] == '视频/工具/make_video.py'
                                               for item in manifest['core_files'])
    status['actual_native_core_certification'] = manifest['actual_native_certification']
    status['actual_native_fastcheck_stamp'] = stamp
    status['reviewed_regression_resource'] = data
    status['core_repair_manifest_sha256'] = sha(manifest_file)
    status['reviewed_gain_preservation_mode'] = True
    status['reviewed_existing_ending_preservation_mode'] = keep_ending
    status['reviewed_existing_physical_cuts_preservation_mode'] = keep_cuts
    save()


def prepare_accepted_pcm_continuity(baseline_bytes, accepted_aac):
    """Rebuild genuine old PCM privately for exact confirmation comparisons."""
    global BASELINE_AUDIO_FILES
    expected = {'10':'15f47fa51add', '11':'5da69def8d01', '12':'04f94362f377',
                '44':'21efe6263229', '51':'ff0728857c2d',
                '15':'7e5ea2bdb6d3', '17':'0ef19e50999f',
                '18':'76b99c620981', '30':'93a277750d35', '02':None,
                '69':'8b8618454b80', '05':'1e25fbe69f6f',
                '67':'c34294a522a7', '16':'630cbdf1eae2', '27':'79f315bb8b44', '62':None}
    exact_old_pcm = {'02':'c21872d4db894f37b1b8b5db752917f9f6ef60680834ca4cccef9b806b5c1c52',
                     '69':'d04e5e1b057dfaa788bf86dcd6fe7da7b88fc1a254f8abd0a695621f074c2837',
                     '05':'4c20eb528b935e7a315e3f41b3f4168fe82cd5e26e0b33d16ea4bfce2609cb64',
                     '67':'39f7defdcfad7a4dae00c9677c7998d8f70c984247583e136e09e6efe9392bae',
                     '16':'3a2239772fe1941d4a5de28be034ff49670fedcf6ced0d1c0e61e5476912b93d',
                     '27':'e15a2d05428e3219216ac8d10780669007f903071b0fcfc3c6bf377c517b8d7f',
                     '62':'f7348a62d6b00aa9cf74ad7c26f83bd3c4c98ff6621e3875dbced7bcfd0ac2c0'}
    prior_public_aac = {'69':'2b15b4811866afd03ef5962f6ce99717d28d7e97704750d9ede91bd7799eed15',
                        '67':'d5d57519d6b60e31eeb92bd1bf0b0505192b49ee9c1e34ae02b5c9ddc9532856'}
    if NO not in expected:
        return
    # These reviewed prior-source snapshots contain the exact approved old
    # audio inputs. Re-prove the complete real accepted PCM and AAC below
    # before attempting any original exact-sample confirmation migration.
    if NO in {'05', '16', '27', '62'}:
        reference_source = TASK / 'accepted-pcm-source-reference' / f'{NO}.json'
        reference_contract = json.loads(reference_source.with_name(f'{NO}-proof.json').read_text())
        assert reference_contract['article'] == NO
        assert sha(reference_source) == reference_contract['source_sha256']
        assert reference_contract['internal_pcm_sha256'] == exact_old_pcm[NO]
        assert reference_contract['aac_adts_sha256'] == accepted_aac
        baseline_bytes = reference_source.read_bytes()
    script = W / f'scripts/{NO}.json'
    current = script.read_bytes()
    old_source = LOG / 'accepted-prior-source.json'
    old_source.write_bytes(baseline_bytes)
    proof = {'article':NO, 'purpose':'diagnostic old accepted PCM reconstruction only; not a QC verdict',
             'quality_acceptance':False, 'old_source_sha256':sha(old_source),
             'expected_accepted_pcm_md5_first12':expected[NO] if NO not in prior_public_aac else None,
             'expected_accepted_pcm_sha256':exact_old_pcm.get(NO) if NO not in prior_public_aac else None,
             'old_pcm_matches_accepted_confirmation_fingerprint':False,
             'private_PCM_or_cache_exported':False}
    if NO in prior_public_aac:
        proof.update({'purpose':'diagnostic exact prior public native PCM for original confirmation migration; not a QC verdict',
                      'reference_kind':'actual_prior_public_native_render_not_the_accepted_voice',
                      'original_public_run_id':43543967031,
                      'expected_prior_public_native_pcm_md5_first12':expected[NO],
                      'expected_prior_public_native_pcm_sha256':exact_old_pcm[NO],
                      'expected_prior_public_native_aac_adts_sha256':prior_public_aac[NO]})
    proof_file = OUT / f'{NO}-accepted-prior-pcm-probe.json'
    private_reference_inputs = {}
    try:
        script.write_bytes(baseline_bytes)
        if NO == '16':
            # This isolated reference subprocess alone uses the real historical
            # pronunciation inputs which produced the exact accepted voice.
            # Restore the current correct Origin inputs before any current
            # production, and never alter ROOT dictionaries or the maker.
            assert sha(W / 'make_video.py') == '6945e9bee6db143029bace6c04b4f4df7110c41ba647eee7236b0d0e5ed75203'
            inputs = reference_contract['pronunciation_inputs']
            assert set(inputs) == {'读音改正.json', '按语境读音.json'}
            proof['historical_pronunciation_reference_inputs'] = inputs
            for name, item in inputs.items():
                source = reference_source.parent / item['file']
                target = W / name
                assert target.is_file() and sha(source) == item['sha256']
                private_reference_inputs[target] = target.read_bytes()
                target.write_bytes(source.read_bytes())
        output = W / f'_accepted-prior-diagnostic-{NO}.m4a'
        with (LOG / 'accepted-prior-pcm-probe.log').open('w') as stream:
            process = subprocess.run(['python3', str(W / 'make_video.py'), str(script), str(output)],
                                     cwd=W, env={**ENV, 'AUDIO_ONLY':'1'}, stdout=stream, stderr=subprocess.STDOUT)
        proof['original_maker_exit'] = process.returncode
        if process.returncode == 0:
            wav = W / f'work_{NO}/a.wav'
            old_wav, old_segments = LOG / 'accepted-prior-a.wav', LOG / 'accepted-prior-segments.json'
            shutil.copyfile(wav, old_wav)
            shutil.copyfile(W / f'work_{NO}/分段.json', old_segments)
            actual_fp = hashlib.md5(old_wav.read_bytes()).hexdigest()[:12]
            proof.update({'actual_old_pcm_md5_first12':actual_fp, 'actual_old_pcm_sha256':sha(old_wav),
                          'old_pcm_matches_accepted_confirmation_fingerprint':actual_fp == expected[NO] and NO not in prior_public_aac,
                          'old_pcm_matches_existing_confirmation_fingerprint':actual_fp == expected[NO],
                          'old_reconstructed_aac_adts_sha256':aac_hash(output),
                          'accepted_prior_aac_adts_sha256':accepted_aac,
                          'old_reconstructed_aac_exactly_matches_accepted':aac_hash(output) == accepted_aac,
                          'old_segment_metadata_sha256':sha(old_segments)})
            old_pcm_bound = (sha(old_wav) == exact_old_pcm[NO]) if NO in exact_old_pcm else actual_fp == expected[NO]
            proof['old_pcm_matches_independently_bound_reference'] = old_pcm_bound
            proof['old_pcm_matches_independently_bound_accepted_reference'] = (
                old_pcm_bound and proof['old_reconstructed_aac_exactly_matches_accepted'])
            BASELINE_AUDIO_FILES = {'old_wav':old_wav, 'old_source':old_source,
                                    'old_segments':old_segments, 'proof':proof_file}
    except Exception as exc:
        proof['diagnostic_error'] = {'type':type(exc).__name__, 'message':str(exc).replace(str(M), '<private-machine>')[:600]}
    finally:
        for path, original_bytes in private_reference_inputs.items():
            path.write_bytes(original_bytes)
            assert path.read_bytes() == original_bytes
        if private_reference_inputs:
            proof['current_pronunciation_inputs_exactly_restored_before_current_production'] = True
        script.write_bytes(current)
        proof_file.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
        status['accepted_prior_pcm_probe'] = proof
        save()
    if not BASELINE_AUDIO_FILES or not proof.get('old_pcm_matches_independently_bound_reference', False):
        return
    if NO in prior_public_aac:
        bound = proof.get('old_reconstructed_aac_adts_sha256') == prior_public_aac[NO]
        proof['old_reconstructed_aac_exactly_matches_prior_public_native'] = bound
        proof_file.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
        if not bound:
            proof['migration_not_attempted'] = 'Prior native reconstruction did not reproduce its actual public AAC.'
            proof_file.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
            save()
            return
    if NO in A21_AUDIO_REPAIRS | {'02', '05', '16', '27', '62'} and not proof.get('old_reconstructed_aac_exactly_matches_accepted', False):
        proof['migration_not_attempted'] = 'Old reconstruction did not exactly reproduce the accepted AAC.'
        proof_file.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
        save()
        return
    if NO == '16':
        # The original migration assumes unchanged raw mothers when migrating
        # deletion confirmations. S15's approved Origin raw mother does change;
        # the actual source has no deletion confirmation in that sentence.
        # A future such entry requires separate actual evidence, not this path.
        deletes = json.loads(current).get('核对确认', {}).get('删除段', {})
        if any(re.match(r'^S15(?:\s|$)', key) for key in deletes):
            proof['migration_not_attempted'] = 'Changed S15 raw mother has a deletion confirmation requiring separate actual evidence.'
            proof_file.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
            save()
            return
    # Original precise confirmations may refer to a previously public failed
    # draft (12's reviewed highlight), as well as the accepted prior voice.
    # Reconstruct that exact input privately and require its complete PCM SHA.
    originals = [BASELINE_AUDIO_FILES['old_wav']]
    supplemental = TASK / 'public-failed-audio-reference' / f'{NO}.json'
    contract_file = supplemental.with_name(NO + '-proof.json')
    if supplemental.is_file() and contract_file.is_file():
        contract = json.loads(contract_file.read_text())
        record = {'source_sha256':sha(supplemental), 'exact_public_failed_pcm_reproduced':False}
        try:
            assert sha(supplemental) == contract['source_sha256']
            script.write_bytes(supplemental.read_bytes())
            with (LOG / 'prior-public-failed-audio-probe.log').open('w') as stream:
                result = subprocess.run(['python3', str(W / 'make_video.py'), str(script),
                                         str(W / f'_prior-public-failed-{NO}.m4a')], cwd=W,
                    env={**ENV, 'AUDIO_ONLY':'1'}, stdout=stream, stderr=subprocess.STDOUT)
            record['original_maker_exit'] = result.returncode
            if result.returncode == 0:
                wav = W / f'work_{NO}/a.wav'
                record['actual_pcm_sha256'] = sha(wav)
                if sha(wav) == contract['internal_pcm_sha256']:
                    extra = LOG / 'prior-public-failed-a.wav'
                    shutil.copyfile(wav, extra)
                    originals.append(extra)
                    record['exact_public_failed_pcm_reproduced'] = True
        except Exception as exc:
            record['diagnostic_error'] = type(exc).__name__
        finally:
            script.write_bytes(current)
            status['prior_public_failed_audio_probe'] = record
    # Use the unchanged factory's exact-sample migration, before the regular
    # 草稿声音 pipeline. It never changes audio, and every original QC still runs.
    with (LOG / 'current-PCM-before-original-confirmation-migration.log').open('w') as stream:
        result = subprocess.run(['python3', str(W / 'make_video.py'), str(script), str(W / f'{NO}.mp4')],
                                cwd=W, env={**ENV, 'AUDIO_ONLY':'1'}, stdout=stream, stderr=subprocess.STDOUT)
    status['original_confirmation_migration'] = {'actual_current_audio_only_exit':result.returncode,
        'unchanged_original_program_sha256':sha(T / '确认平移.py'), 'attempts':[],
        'new_quality_gate':False, 'audio_modified_by_migration':False}
    if result.returncode == 0:
        if NO == '62':
            assert sha(W / 'work_62/a.wav') == 'c5330026dbc9f81d0c7546a1716b9dade9960f44311862a5feb3e4aa0749d7c3'
            assert aac_hash(W / '62.mp4') == 'b85f7e4c45784077f227b29a24b7cd72cef6c6160aa3783747ba708f8fda6348'
        actual_fp = hashlib.md5((W / f'work_{NO}/a.wav').read_bytes()).hexdigest()[:12]
        for index, old_wav in enumerate(originals):
            old_fp = hashlib.md5(old_wav.read_bytes()).hexdigest()[:12]
            if old_fp == actual_fp:
                continue
            with (LOG / f'original-confirmation-migration-{index}.log').open('w') as stream:
                migrated = subprocess.run(['python3', str(T / '确认平移.py'), NO, str(old_wav), '--写入'],
                                         cwd=W, env=ENV, stdout=stream, stderr=subprocess.STDOUT)
            status['original_confirmation_migration']['attempts'].append({
                'old_pcm_md5_first12':old_fp, 'actual_pcm_md5_first12':actual_fp, 'exit':migrated.returncode})
    save()


def collect_confirmation_continuity():
    """Export all confirmation categories as scalar evidence, with no renewal."""
    if not BASELINE_AUDIO_FILES or PRODUCTION_STARTED_NS is None:
        return
    wav = W / f'work_{NO}/a.wav'
    segments = W / f'work_{NO}/分段.json'
    if not wav.is_file() or not segments.is_file() or wav.stat().st_mtime_ns < PRODUCTION_STARTED_NS:
        return
    output = OUT / f'{NO}-confirmation-continuity.json'
    args = ['python3', TASK / 'collect-confirmation-continuity.py',
            '--old-wav', BASELINE_AUDIO_FILES['old_wav'], '--actual-wav', wav,
            '--old-source', BASELINE_AUDIO_FILES['old_source'], '--actual-source', W / f'scripts/{NO}.json',
            '--old-segments', BASELINE_AUDIO_FILES['old_segments'], '--actual-segments', segments,
            '--baseline-proof', BASELINE_AUDIO_FILES['proof'], '--dossier', W / f'dossier_{NO}.json',
            '--output', output]
    result = subprocess.run(list(map(str,args)), cwd=W, env=ENV, capture_output=True, text=True, errors='replace', timeout=120)
    record = {'diagnostic_only':True, 'automatic_renewals':False, 'exit':result.returncode}
    if output.is_file():
        record.update({'file':output.name,'sha256':sha(output)})
    else:
        record['diagnostic_error_type'] = 'ScalarCollectionFailed'
    status['confirmation_continuity'] = record


def prepare_approved_a21_derived_level(source_video, accepted_aac):
    """Only30's newly approved raw release needs a new original level-cache key."""
    if NO == '62':
        program = TASK / 'prepare-derived-level62.py'
        output = OUT / '62-derived-level-preparation.json'
        checked(['python3', program, '--video-root', M, '--repository', ROOT,
                 '--accepted-video', source_video, '--output', output],
                'approved62-derived-level-preparation.log', W)
        evidence = json.loads(output.read_text())
        assert evidence['derived_reference_prepared'] is True
        assert evidence['private_PCM_GT_cache_arrays_or_models_exported'] is False
        assert aac_hash(source_video) == accepted_aac
        status['approved_derived_level_preparation'] = evidence
        status['approved_derived_level_preparation_program_sha256'] = sha(program)
        save()
        return
    if NO != '30':
        return
    program = TASK / 'prepare-derived-level30.py'
    output = OUT / '30-derived-level-preparation.json'
    checked(['python3', program, '--video-root', M, '--repository', ROOT,
             '--accepted-video', source_video, '--output', output],
            'approved30-derived-level-preparation.log', W)
    evidence = json.loads(output.read_text())
    assert evidence['derived_reference_prepared'] is True
    assert evidence['private_PCM_GT_cache_arrays_or_models_exported'] is False
    assert aac_hash(source_video) == accepted_aac
    status['approved_derived_level_preparation'] = evidence
    status['approved_derived_level_preparation_program_sha256'] = sha(program)
    save()


def verify_correct_origin_reference_cache(request, after_references=False):
    """16 alone uses its exact certified normal-cache mothers, never fresh inference."""
    if NO != '16':
        return
    assert status['original_maker_unchanged'] is False
    program = TASK / 'verify_native16_cache.py'
    contract = TASK / 'native16-Origin-cache-contract.json'
    suffix = '' if after_references else '-before-references'
    output = OUT / f'16-native-correct-Origin-cache-readback{suffix}.json'
    args = ['python3', program, '--video-root', M,
             '--request', request / '视频/脚本/16.json', '--contract', contract,
             '--output', output]
    if after_references:
        args.append('--verify-ordinary-next-mother')
    checked(args, f'16-native-correct-Origin-cache-readback{suffix}.log')
    result = json.loads(output.read_text())
    assert result['exact_certified_internal_reference_cache_verified'] is True
    assert result['audio_inference_performed'] is False
    assert result['private_cache_or_source_modified'] is False
    if after_references:
        assert result['ordinary_next_exact_accepted_text_mother_verified'] is True
    status['correct_Origin_native_reference_cache' + ('_before_references' if not after_references else '')] = {
        'verified': True, 'file': output.name, 'sha256': sha(output),
        'program_sha256': sha(program), 'contract_sha256': sha(contract),
        'quality_acceptance': False, 'original_current_quality_gates_still_required': True}
    save()


def verify_unchanged_review_audio_packets(accepted_video, canonical_video):
    """Pure visual13/14/26 revisions preserve their own accepted audio packets."""
    if NO not in {'13', '14', '26', '33'}:
        return
    status['stage'] = f'{NO}-accepted-audio-packet-preservation'
    save()
    helper_path = TASK / 'illustrated_tail.py'
    spec = importlib.util.spec_from_file_location('article' + NO + '_existing_packet_reader', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    old_packets = helper.packets(accepted_video, 'a:0', payload=True)
    new_packets = helper.packets(canonical_video, 'a:0', payload=True)
    keys = ('codec_name', 'profile', 'codec_tag_string', 'sample_fmt', 'sample_rate',
            'channels', 'channel_layout', 'time_base')
    streams = []
    for video in (accepted_video, canonical_video):
        row = next(s for s in helper.probe(video)['streams'] if s['codec_type'] == 'audio')
        streams.append({key: row.get(key) for key in keys})
    encode = lambda rows: json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()
    evidence = {'article': NO, 'scope': f'This{NO} revision changes focus colours and Chinese explanations only.',
                'accepted_video_sha256': sha(accepted_video), 'canonical_video_sha256': sha(canonical_video),
                'accepted_packet_count': len(old_packets), 'canonical_packet_count': len(new_packets),
                'accepted_packet_records_sha256': hashlib.sha256(encode(old_packets)).hexdigest(),
                'canonical_packet_records_sha256': hashlib.sha256(encode(new_packets)).hexdigest(),
                'AAC_payload_side_data_and_absolute_PTS_DTS_duration_identical': old_packets == new_packets,
                'codec_parameters_identical': streams[0] == streams[1], 'codec_parameters': streams,
                'existing_packet_reader_sha256': sha(helper_path), 'private_PCM_or_cache_read': False}
    output = OUT / f'{NO}-accepted-audio-packet-preservation.json'
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    status['accepted_prior_audio_packet_preservation'] = {'file': output.name, 'sha256': sha(output), **evidence}
    save()
    assert old_packets and old_packets == new_packets, f'{NO} canonical AAC payload or absolute clock differs from the accepted voice.'
    assert streams[0] == streams[1], f'{NO} canonical audio codec parameters differ from the accepted voice.'


def collect_actual_public_sources(request, current_source):
    """Archive actual source files honestly; this creates no extra QC verdict."""
    manifest = {'article': NO, 'kind': 'actual-production-source-collection',
                'new_quality_gate': False, 'files': {}}
    paths = [('request_json', request / f'视频/脚本/{NO}.json', f'{NO}-request-source.json'),
             ('request_generator', request / f'视频/工具/初稿生成/gen{NO}.py', f'{NO}-request-gen.py'),
             ('used_generator', T / f'初稿生成/gen{NO}.py', f'{NO}-used-gen.py'),
             ('actual_working_source', current_source, f'{NO}-actual-working-source.json')]
    request_md = next((request / '新版定稿').glob(f'{NO}-*.md'))
    paths += [('request_manuscript', request_md, f'{NO}-request-manuscript.md'),
              ('actual_working_manuscript', ROOT / '新版定稿' / request_md.name,
               f'{NO}-actual-working-manuscript.md')]
    for role, source, name in paths:
        destination = OUT / name
        shutil.copyfile(source, destination)
        manifest['files'][role] = {'file': name, 'sha256': sha(destination),
                                   'origin': 'actual_production_filesystem' if role.startswith(('used_', 'actual_')) else 'immutable_request'}
    log = W / f'做_{NO}/生成.log'
    observed = bool(log.is_file() and PRODUCTION_STARTED_NS is not None
                    and log.stat().st_mtime_ns >= PRODUCTION_STARTED_NS)
    manifest['generator_execution_observed'] = observed
    manifest['generator_execution_evidence'] = 'fresh official 做/生成.log' if observed else 'No fresh generator execution log; do not claim this GEN was executed during rendering.'
    if observed:
        shutil.copyfile(log, OUT / f'{NO}-used-generator-execution.log')
    def changes(before, after, path=''):
        if type(before) is not type(after):
            return [{'path': path or '/', 'request': before, 'actual': after}]
        if isinstance(before, dict):
            rows = []
            for key in sorted(set(before) | set(after)):
                part = path + '/' + key.replace('~', '~0').replace('/', '~1')
                if key not in before:
                    rows.append({'path': part, 'added_actual_value': after[key]})
                elif key not in after:
                    rows.append({'path': part, 'removed_request_value': before[key]})
                else:
                    rows += changes(before[key], after[key], part)
            return rows
        if isinstance(before, list) and len(before) == len(after):
            return [row for i, (a, b) in enumerate(zip(before, after)) for row in changes(a, b, path + '/' + str(i))]
        return [] if before == after else [{'path': path or '/', 'request': before, 'actual': after}]
    diff = {'article': NO, 'kind': 'observed-request-to-actual-source-differences',
            'quality_verdict': None,
            'changes': changes(json.loads((request / f'视频/脚本/{NO}.json').read_text()),
                               json.loads(current_source.read_text()))}
    diff_file = OUT / f'{NO}-actual-source-differences.json'
    diff_file.write_text(json.dumps(diff, ensure_ascii=False, indent=2) + '\n')
    manifest['source_differences'] = {'file': diff_file.name, 'sha256': sha(diff_file)}
    (OUT / f'{NO}-actual-source-collection.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    status['actual_source_collection'] = manifest


def add_approved_illustrated_tail(request, final, verification):
    """Keep the genuine passed body/AAC, then approved book art60 + summary60."""
    helper = TASK / 'illustrated_tail.py'
    # The upstream verdict is genuine and complete before this independent
    # packet-preserving composition step; preserve it as a separate record.
    upstream_status = OUT / f'{NO}-canonical-summary-passed-status.json'
    shutil.copyfile(OUT / f'{NO}-status.json', upstream_status)
    resource_spec = importlib.util.spec_from_file_location('approved_illustration_resource', TASK / 'approved_illustration_resource.py')
    resource_module = importlib.util.module_from_spec(resource_spec)
    resource_spec.loader.exec_module(resource_module)
    image, image_receipt = resource_module.resolve(NO, ROOT / '.approved-publication-illustrations', TASK)
    status['approved_illustration_resource'] = image_receipt
    output = OUT / f'{NO}-4K-正文-书中插图2秒-简述2秒.mp4'
    report = OUT / f'{NO}-illustrated-tail-verification.json'
    checked(['python3', helper, '--source-id', NO, '--input', final,
             '--verification', verification, '--illustration-manifest', TASK / 'illustration-manifest70.json',
             '--order-manifest', TASK / 'book-order-manifest.json', '--crop-review', TASK / 'illustration-crop-review70.json',
             '--illustration', image, '--summary-image', OUT / f'{NO}-简述.png',
             '--layout-approval', TASK / 'approved-video-layouts70.json', '--output', output,
             '--report', report, '--status', upstream_status, '--source-script', request / f'视频/脚本/{NO}.json',
             '--work', M / f'{NO}-illustrated-tail', '--preview-dir', OUT / f'{NO}-illustrated-tail-previews',
             '--prepared-illustration-output', OUT / f'{NO}-批准插图4K.png'], 'approved-illustrated-tail.log', ROOT)
    proof = json.loads(report.read_text())
    assert proof['passed'] is True and aac_hash(output) == status['canonical_aac_adts_sha256']
    assert proof['production_delivery_eligible'] is True and proof['source_kind'] == 'new-canonical-4K'
    assert proof['input_video_sha256'] == sha(final) and proof['video_sha256'] == sha(output)
    status.update({'passed': True, 'stage': 'final4K-passed', 'video_sha256': sha(output),
                   'final_video_file': output.name, 'illustration_frames': 60, 'illustration_seconds': 2,
                   'summary_start_seconds': proof['summary_start_seconds'],
                   'illustration_start_frame': proof['illustration_start_frame'],
                   'illustration_start_seconds': proof['illustration_start_seconds'],
                   'summary_start_frame': proof['summary_start_frame'],
                   'output_frames': proof['output_frames'], 'output_seconds': proof['output_seconds'],
                   'first_tail_page': 'illustration',
                   'final_decoded_frame_previews': proof.get('decoded_frame_previews', []),
                   'illustrated_tail_verification': {'file': report.name, 'sha256': sha(report)}})
    # The predecessor and its actual passed proof remain archived for lineage.
    return output


def install_reviewed_context(request):
    """Use one exact frozen source context for cross-article checks."""
    context = TASK / 'context'
    manifest_file = context / 'manifest.json'
    if not manifest_file.is_file():
        status['reviewed_cross_article_context'] = {'provided': False}
        return
    manifest = json.loads(manifest_file.read_text())
    expected_ids = [f'{n:02d}' for n in range(1, 71)]
    assert manifest['kind'] == 'exact_reviewed_cross_article_source_context'
    assert manifest['article_ids'] == expected_ids
    files = manifest['files_sha256']
    assert len(files) == 140
    scripts = {f'视频/脚本/{no}.json' for no in expected_ids}
    assert scripts <= set(files)
    manuscript_ids = []
    for relative, expected_hash in files.items():
        assert (relative in scripts or re.fullmatch(r'新版定稿/\d{2}-[^/]+\.md', relative)), relative
        assert re.fullmatch(r'[0-9a-f]{64}', expected_hash)
        path = context / relative
        assert path.is_file() and not path.is_symlink() and sha(path) == expected_hash, relative
        if relative.startswith('新版定稿/'):
            manuscript_ids.append(Path(relative).name[:2])
        else:
            assert json.loads(path.read_text())['no'] == Path(relative).stem
    assert sorted(manuscript_ids) == expected_ids
    target_json = f'视频/脚本/{NO}.json'
    target_md = next(name for name in files if name.startswith(f'新版定稿/{NO}-'))
    assert (context / target_json).read_bytes() == (request / target_json).read_bytes()
    assert (context / target_md).read_bytes() == (request / target_md).read_bytes()
    # No tools, authorization records, accepted MP4s or unlisted files copied.
    for relative in sorted(files):
        destination = ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(context / relative, destination)
        if relative in scripts:
            working = W / 'scripts' / Path(relative).name
            working.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(context / relative, working)
    status['reviewed_cross_article_context'] = {
        'provided': True, 'manifest_sha256': sha(manifest_file), 'files_sha256': files,
        'source_file_count': 140, 'working_script_count': 70,
        'target_request_exactly_matches_context': True}
    save()


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


def clear_temporary_video():
    """Discard only the restored working output, never a repository video."""
    global PRODUCTION_STARTED_NS
    assert W.resolve().is_relative_to(M.resolve())
    assert not W.resolve().is_relative_to(ROOT.resolve())
    removed = []
    for path in (W / f'{NO}.mp4', W / f'{NO}.mp4.指纹.json'):
        if path.exists() or path.is_symlink():
            assert path.parent.resolve() == W.resolve()
            st = path.lstat()
            removed.append({'name': path.name, 'mtime_ns': st.st_mtime_ns,
                            'bytes': st.st_size, 'was_symlink': path.is_symlink()})
            path.unlink()
    PRODUCTION_STARTED_NS = time.time_ns()
    status['temporary_output_reset'] = {'removed': removed,
                                         'production_started_ns': PRODUCTION_STARTED_NS,
                                         'repository_outputs_modified': False}
    save()


def clear_current_reference_cache():
    """Rebuild only this article's temporary GT with the approved raw loader."""
    qc = Path(ENV.get('QC_DIR', str(M / 'qc_independent')))
    assert qc.resolve().is_relative_to(M.resolve()) and not qc.resolve().is_relative_to(ROOT.resolve())
    removed = []
    for path in sorted((qc / 'gt').glob(NO + '_*')):
        assert path.is_file() and not path.is_symlink()
        removed.append({'name': path.name, 'sha256': sha(path)})
        path.unlink()
    status['fresh_current_article_reference'] = {'article': NO, 'removed_temporary_gt_files': removed,
        'processed_pcm_or_raw_mother_cache_modified': False,
        'purpose': 'Original synth/labels/audit rebuild fresh for this production; no old CPU GT reuse.'}
    save()


def activate_read_only_failure_probe():
    if NO not in {'06','54','57','67'}:
        return
    probe = TASK / 'read-only-scalar-probe'
    result = subprocess.run(['python3','-c',
        "import importlib.util,json; s=importlib.util.find_spec('sitecustomize'); print(json.dumps(s.origin if s else None))"],
        cwd=W, env=ENV, capture_output=True, text=True)
    existing = json.loads(result.stdout) if result.returncode == 0 else 'Existing customization could not be inspected.'
    if existing:
        status['read_only_failure_scalar_probe'] = {'enabled':False,'existing_customization_preserved':True,
                                                   'reason':'An existing sitecustomize was preserved.'}
        return
    ENV.update({'PYTHONPATH':str(probe)+(os.pathsep+ENV['PYTHONPATH'] if ENV.get('PYTHONPATH') else ''),
                'VIDEO_SAFE_SCALAR_DIR':str(OUT), 'VIDEO_SAFE_SCALAR_ARTICLE':NO,
                'VIDEO_SAFE_SCALAR_MAKER':str(W / 'make_video.py'),
                'VIDEO_SAFE_SCALAR_SOURCE':str(W / f'scripts/{NO}.json'),
                'VIDEO_SAFE_SCALAR_SEGS':str(W / f'work_{NO}/分段.json')})
    status['read_only_failure_scalar_probe'] = {'enabled':True,'no_original_exception_or_result_changed':True,
        'hook_sha256':{name:sha(probe/name) for name in ('sitecustomize.py','safe_scalar_probe.py')}}
    save()


def assert_reviewed_gain_controls(requested, stage):
    if ENV.get('XG_KEEP_REVIEWED_GAIN') != '1':
        return
    def gains(value, path=''):
        if isinstance(value, dict):
            rows = {}
            for key, item in value.items():
                pointer = path + '/' + key.replace('~', '~0').replace('/', '~1')
                if '增益' in key:
                    rows[pointer] = item
                else:
                    rows.update(gains(item, pointer))
            return rows
        if isinstance(value, list):
            return {key: item for index, child in enumerate(value)
                    for key, item in gains(child, path + '/' + str(index)).items()}
        return {}
    before = gains(requested)
    after = gains(json.loads((W / f'scripts/{NO}.json').read_text()))
    same = before == after
    status.setdefault('reviewed_gain_control_preservation', []).append({
        'stage': stage, 'requested_gain_controls': before, 'actual_gain_controls': after,
        'exactly_preserved': same})
    save()
    assert same, 'Reviewed source gain controls changed during production.'


def failure_audio_diagnostics():
    """Read private reference data internally; export diagnostic scalars only."""
    if NO not in ALLOWED:
        return
    program = TASK / 'diagnose_reference_gain.py'
    qc = Path(ENV.get('QC_DIR', str(M / 'qc_independent')))
    meta = qc / 'gt' / f'{NO}_meta.json'
    wav = W / f'work_{NO}/a.wav'
    post_logs = [W / group / '出片后.log' for group in (f'做_{NO}', f'定稿_{NO}')]
    current_logs = [path for path in post_logs if PRODUCTION_STARTED_NS is not None
                    and path.is_file() and path.stat().st_mtime_ns >= PRODUCTION_STARTED_NS]
    post_log = max(current_logs, key=lambda path: path.stat().st_mtime_ns) if current_logs else None
    current_post_check = post_log is not None
    record = {'acceptance': False, 'diagnostic_only': True,
              'program_present': program.is_file(), 'reference_meta_present': meta.is_file(),
              'actual_pcm_present': wav.is_file(), 'current_post_check_present': current_post_check}
    status['reference_gain_failure_diagnostic'] = record
    if not all((program.is_file(), meta.is_file(), wav.is_file(), current_post_check)):
        return
    output = OUT / f'{NO}-reference-gain-diagnostic.json'
    result = subprocess.run(
        ['python3', str(program), '--video-root', str(M), '--qc-dir', str(qc),
         '--no', NO, '--tools', str(T), '--post-log', str(post_log),
         '--out', str(output)], cwd=W, env=ENV, capture_output=True,
        text=True, errors='replace', timeout=240)
    record.update({'exit': result.returncode, 'program_sha256': sha(program)})
    if output.is_file():
        data = json.loads(output.read_text())
        assert data.get('article') == NO and 'passed' not in data
        record.update({'file': output.name, 'sha256': sha(output),
                       'anchor_summary': data.get('anchor_summary'),
                       'diagnostic_error': data.get('diagnostic_error')})
    elif result.returncode:
        record['error'] = 'Scalar diagnostic did not create its JSON output.'


def export_failed_current_video():
    """Export a newly completed public MP4, with strict provenance, as failed."""
    record = {'exported': False, 'passed': False, 'acceptance': False,
              'purpose': 'failed current-attempt video for diagnosis; not a final deliverable'}
    status['failed_current_video'] = record
    if PRODUCTION_STARTED_NS is None:
        record['reason'] = 'Production has not started.'
        return
    candidate = W / f'{NO}.mp4'
    fingerprint = Path(str(candidate) + '.指纹.json')
    source = W / f'scripts/{NO}.json'
    wav = W / f'work_{NO}/a.wav'
    if not all(path.is_file() and not path.is_symlink()
               for path in (candidate, fingerprint, source, wav)):
        record['reason'] = 'No complete current working video and official fingerprint.'
        return
    if any(path.stat().st_mtime_ns < PRODUCTION_STARTED_NS for path in (candidate, fingerprint)):
        record['reason'] = 'Working video or fingerprint predates this production attempt.'
        return
    fp = json.loads(fingerprint.read_text())
    hashes = {'视频': sha(candidate), '脚本': sha(source), '配音': sha(wav)}
    # The unchanged official fingerprint stores exactly the first 16 hex
    # characters of SHA256; keep full hashes separately in the public proof.
    expected_official_hashes = {key: value[:16] for key, value in hashes.items()}
    if (fp.get('只出声音') is not False
            or any(not isinstance(fp.get(key), str) or not re.fullmatch(r'[0-9a-f]{16}', fp[key])
                   for key in expected_official_hashes)
            or any(fp.get(key) != value for key, value in expected_official_hashes.items())):
        record['reason'] = 'Official fingerprint is audio-only or does not match current video/source/PCM.'
        record['fingerprint_hash_format'] = 'official SHA256 first 16 hex characters'
        record['mismatched_fingerprint_fields'] = [
            key for key, value in expected_official_hashes.items() if fp.get(key) != value]
        return
    # Independent metadata proves that the completed render has picture and audio.
    info = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(candidate)]))
    videos = [s for s in info['streams'] if s.get('codec_type') == 'video']
    audios = [s for s in info['streams'] if s.get('codec_type') == 'audio']
    if len(videos) != 1 or not audios or (videos[0].get('width'), videos[0].get('height')) not in {
            (1920, 1080), (3840, 2160)}:
        record['reason'] = 'Candidate is not a completed 1080p/4K render with audio.'
        return
    duration = float(info['format']['duration'])
    if not 0 < duration < 1800:
        record['reason'] = 'Unexpected duration.'
        return
    render_logs = {}
    for group in (f'做_{NO}', f'定稿_{NO}'):
        render_log = W / group / '出片.log'
        if render_log.is_file() and render_log.stat().st_mtime_ns >= PRODUCTION_STARTED_NS:
            render_logs[f'{group}/出片.log'] = {'sha256': sha(render_log),
                                               'mtime_ns': render_log.stat().st_mtime_ns}
    if not render_logs:
        record['reason'] = 'No current official picture-render stage log.'
        return
    video_out = OUT / f'{NO}-failed-draft.mp4'
    shutil.copyfile(candidate, video_out)
    assert sha(video_out) == hashes['视频']
    # No private GT, TTS cache, model, raw a.wav, or raw speech arrays leave M.
    public_fp = OUT / f'{NO}-failed-draft-fingerprint.json'
    shutil.copyfile(fingerprint, public_fp)
    source_out = OUT / f'{NO}-failed-working-source.json'
    shutil.copyfile(source, source_out)
    windows = {
        '10': [('last-sentence', max(0.0, duration - 15), duration)],
        '12': [('title', 0.0, 6.0), ('s5-highlight', 29.5, 36.5)],
        '44': [('norway-finland', 32.5, 46.5)],
        '51': [('opening-ok', 0.0, 9.0), ('oll-wright', 18.0, 24.5),
               ('ending', max(0.0, duration - 13), duration)],
    }.get(NO, [])
    clips = []
    for label, begin, end in windows:
        begin, end = max(0.0, begin), min(duration, end)
        if end <= begin:
            continue
        destination = OUT / f'{NO}-failed-draft-{label}.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(begin), '-i', str(video_out),
                        '-t', str(end - begin), '-map', '0:a:0', '-vn', '-c:a', 'pcm_s16le',
                        str(destination)], check=True, capture_output=True)
        clips.append({'file': destination.name, 'sha256': sha(destination),
                      'source_video_sha256': hashes['视频'], 'start_seconds': begin,
                      'end_seconds': end, 'derived_from_public_mp4': True})
    # ffprobe's filename is an internal absolute path; use only the public name.
    info['format']['filename'] = video_out.name
    proof = {'article': NO, 'passed': False, 'acceptance': False,
             'production_started_ns': PRODUCTION_STARTED_NS,
             'video_mtime_ns': candidate.stat().st_mtime_ns,
             'fingerprint_mtime_ns': fingerprint.stat().st_mtime_ns,
             'failed_stage': status.get('stage'), 'failure_step': status.get('failure_details', {}).get('step'),
             'official_fingerprint_matches_current_video_source_and_pcm': True,
             'official_fingerprint_hash_format': 'SHA256 first 16 hex characters',
             'official_current_render_stage_logs': render_logs,
             'official_fingerprint_sha256': sha(public_fp),
             'source_sha256': hashes['脚本'], 'internal_pcm_sha256': hashes['配音'],
             'video_sha256': hashes['视频'], 'aac_adts_sha256': aac_hash(video_out),
             'ffprobe': info, 'public_mp4_derived_clips': clips}
    proof_out = OUT / f'{NO}-failed-draft-proof.json'
    proof_out.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    record.update({'exported': True, 'file': video_out.name, 'sha256': hashes['视频'],
                   'width': videos[0]['width'], 'height': videos[0]['height'],
                   'proof': proof_out.name, 'proof_sha256': sha(proof_out),
                   'derived_clip_count': len(clips)})


def collect_original_asr_target_evidence():
    """A failed original ASR check remains failed; collect the two actual texts."""
    if NO not in {'46', '49', '55', '66'} or not status.get('failed_current_video', {}).get('exported'):
        return
    output = OUT / f'{NO}-original-ASR-target-evidence.json'
    process = subprocess.run(list(map(str, ['python3', TASK / 'collect_asr_target_evidence.py',
        '--article', NO, '--work', W, '--tools', T,
        '--public-video', OUT / f'{NO}-failed-draft.mp4', '--proof', OUT / f'{NO}-failed-draft-proof.json',
        '--output', output])), cwd=W, env=ENV, capture_output=True, text=True, errors='replace', timeout=240)
    record = {'diagnostic_only': True, 'acceptance': False, 'automatic_confirmation': False,
              'exit': process.returncode}
    if output.is_file():
        record.update({'file': output.name, 'sha256': sha(output)})
    status['original_asr_target_evidence'] = record


def collect_actual_current62_dual_ASR_contexts():
    # Readonly evidence in the same real native job, regardless of its verdict.
    # It never adds/renews a confirmation or replaces an original quality result.
    if NO != '62':
        return
    output = OUT / '62-current-S15-original-dual-ASR-contexts.json'
    try:
        result = subprocess.run(['python3', str(TASK / 'collect_original_asr62.py'),
            '--work', str(W), '--tools', str(T), '--output', str(output)],
            cwd=W, env=ENV, capture_output=True, text=True, errors='replace', timeout=300)
        (LOG / 'current62-original-dual-ASR-contexts.log').write_text(result.stdout + '\n' + result.stderr)
        status['current62_actual_dual_ASR_context_evidence'] = {
            'diagnostic_only':True, 'acceptance':False, 'automatic_confirmation_or_renewal':False,
            'exit':result.returncode, 'original_pipeline_verdict_not_replaced':True}
        if output.is_file():
            status['current62_actual_dual_ASR_context_evidence'].update(file=output.name, sha256=sha(output))
    except Exception as exc:
        status['current62_actual_dual_ASR_context_evidence'] = {'diagnostic_only':True,
            'acceptance':False, 'error_type':type(exc).__name__, 'original_pipeline_verdict_not_replaced':True}
    save()


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
            previous = status.pop('failure_details', None)
            if previous:
                status.setdefault('recovered_attempt_history', []).append(previous)
                save()
            return
        for group in (f'做_{NO}', f'定稿_{NO}'):
            for path in (W / group).glob('*.log'):
                text += '\n' + path.read_text(errors='replace')
        missing = re.findall(r'缺(?:配音|调平)缓存\s+([A-Za-z0-9_\u4e00-\u9fff.-]+\.(?:pkl|json))', text)
        if missing:
            # Keep the real unchanged-checker reason even if the repository
            # has no such public cache and git show itself subsequently fails.
            failure = status.setdefault('failure_details', {})
            failure['reported_missing_public_cache_entries'] = sorted(set(missing))
            failure['original_checker_diagnostics_before_cache_restore'] = [
                line[:1600] for line in text.splitlines()
                if any(mark in line for mark in ('✘', ' BAD ', '缺配音缓存', '缺调平缓存', '【停止】'))][-120:]
            save()
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
                    if source.name == '声音.log':
                        # Preserve actual early exits (for example a final sentence
                        # without an inner comma) even when the legacy summary
                        # only prints lines containing a QA counter.
                        diagnostics[f'{group}/{source.name}:actual_text_tail'] = [
                            line[:2000].replace(str(M), '<private-machine>') for line in lines[-180:]
                            if not any(marker in line for marker in
                                       ('onnxruntime:', 'VerifyEachNodeIsAssignedToAnEp'))]
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
                                       ('BAD', 'FAIL', 'Error', 'Exception', '问题数', '插入',
                                        '【停止】', '缺配音缓存', '缺调平缓存', '指纹不符'))]
                    evidence += lines[exceptions:][-18:]
                    # A bare SystemExit can have no traceback or BAD line.
                    # These are text diagnostics, never cache/GT/model bytes.
                    tail = [line[:1600] for line in lines
                            if not any(mark in line for mark in ('onnxruntime:', 'VerifyEachNodeIsAssignedToAnEp'))][-30:]
                    diagnostics[name] = {'exit': result.returncode, 'actual_output': evidence,
                                         'actual_final_text_lines': tail}
                    text += '\n' + '\n'.join(lines)
            status.setdefault('failure_details', {})['public_checker_diagnostics'] = diagnostics
            save()
            # Restore only the exact existing public cache entry actually named
            # by the direct unchanged checker; keep STRICT_CACHE for every retry.
            missed = re.findall(r'缺(?:配音|调平)缓存\s+([A-Za-z0-9_\u4e00-\u9fff.-]+\.(?:pkl|json))', text)
            recovered = [cache_entry(name) for name in sorted(set(missed))]
            if any(recovered):
                continue
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


def same_summary_content(expected, actual):
    """Allow only added line-leading ▹ wrappers; preserve every other glyph."""
    if expected.count('▸') != 5 or actual.count('▸') != 5:
        return False
    want = ''.join(char for char in expected if not char.isspace())
    index = 0
    at_line_start = True
    for char in actual:
        leading_wrap_marker = char == '▹' and at_line_start
        if char == '\n':
            at_line_start = True
        elif not char.isspace():
            at_line_start = False
        if char.isspace():
            continue
        if index < len(want) and char == want[index]:
            index += 1
        elif leading_wrap_marker:
            # An intentional marker already in expected must match above;
            # removed/changed expected text is never ignored.
            continue
        else:
            return False
    return index == len(want)


try:
    # Check the exact publication resource before any costly voice or video work.
    checked(['python3', TASK / 'approved_illustration_resource.py', '--source-id', NO,
             '--checkout', ROOT / '.approved-publication-illustrations', '--task', TASK,
             '--out', OUT / f'{NO}-approved-illustration-resource.json'],
            'approved-illustration-resource.log', ROOT)
    assert (M / 'tts/kokoro-v1.0.onnx').exists(), 'Original warm machine cache was not restored.'
    W.mkdir(parents=True, exist_ok=True)
    install_certified_core_repairs()
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
    confirmations = request / f'视频/制作记录/逐句确认/{NO}.json'
    if confirmations.is_file():
        files.append((confirmations, ROOT / f'视频/制作记录/逐句确认/{NO}.json'))
    # Keep the accepted original English baseline before installing updated
    # cross-article context; context cannot erase this invariant.
    baseline_bytes = (ROOT / script_rel).read_bytes()
    baseline = json.loads(baseline_bytes)
    install_reviewed_context(request)
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
    if NO == '62':
        supplement = request / '真实用户同意补充.json'
        assert sha(supplement) == '1d9fb3903cbba3b3e276f987412487d182536ea0ae1a13dc745fc4ee5f5134ca'
        attached = json.loads(supplement.read_text())
        assert attached['article'] == NO
        for actual_record in attached['records']:
            assert actual_record['篇'] == NO and actual_record['原话'].strip()
            if actual_record not in records['记录']:
                records['记录'].append(actual_record)
        status['actual_original_user_consent_supplement_sha256'] = sha(supplement)
    supplied_agreement = request / '视频/工具/用户同意记录.json'
    if supplied_agreement.is_file():
        supplied_records = json.loads(supplied_agreement.read_text())
        assert {k: v for k, v in supplied_records.items() if k != '记录'} == {
            k: v for k, v in records.items() if k != '记录'}
        assert all(row in supplied_records['记录'] for row in records['记录'])
        added_records = [row for row in supplied_records['记录'] if row not in records['记录']]
        assert added_records and all(row == authorization for row in added_records), (
            'Only the exact attached current user authorization may update the consent registry.')
        agreement.write_bytes(supplied_agreement.read_bytes())
        records = supplied_records
        status['request_source_sha256']['视频/工具/用户同意记录.json'] = sha(supplied_agreement)
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
    verify_correct_origin_reference_cache(request)
    status['accepted_source'] = {**reference, 'aac_adts_sha256': accepted_aac}
    start_wav = sha(W / f'work_{NO}/a.wav') if (W / f'work_{NO}/a.wav').exists() else None
    if NO in ALLOWED:
        # Enumerate the original checker's complete punctuation-slice calls for
        # any selected article. Prepare only missing references privately;
        # official production and every checker remain STRICT_CACHE=1.
        reference_helper = TASK / 'prepare-checker-reference.py'
        reference_evidence = OUT / f'{NO}-checker-reference-preparation.json'
        reference_env = {k: v for k, v in ENV.items() if k != 'STRICT_CACHE'}
        status['stage'] = 'checker-reference-preparation'
        save()
        result = subprocess.run(
            ['python3', str(reference_helper), '--article', NO, '--video-root', str(M),
             '--repository', str(ROOT), '--accepted-video', str(source_video),
             '--output', str(reference_evidence)], cwd=W, env=reference_env,
            capture_output=True, text=True, errors='replace', timeout=600)
        (LOG / 'checker-reference-preparation.log').write_text(result.stdout + '\n' + result.stderr)
        if result.returncode:
            # Text errors only; never emit the reference arrays or cache bytes.
            status['checker_reference_preparation_failure'] = {
                'exit': result.returncode,
                'diagnostics': [line[:1200].replace(str(M), '<private-machine>')
                                for line in (result.stdout + '\n' + result.stderr).splitlines()
                                if any(mark in line for mark in ('Error', 'Exception', '【停止】'))][-12:]}
        assert result.returncode == 0, 'Original checker reference preparation failed; production remains strict.'
        evidence = json.loads(reference_evidence.read_text())
        assert evidence.get('reference_prepared') is True and evidence.get('private_cache_exported') is False
        assert aac_hash(source_video) == accepted_aac
        assert (sha(W / f'work_{NO}/a.wav') if (W / f'work_{NO}/a.wav').is_file() else None) == start_wav
        status['checker_reference_preparation'] = evidence
        status['checker_reference_preparation_program_sha256'] = sha(reference_helper)
        save()
    verify_correct_origin_reference_cache(request, after_references=True)
    prepare_approved_a21_derived_level(source_video, accepted_aac)
    prepare_accepted_pcm_continuity(baseline_bytes, accepted_aac)
    clear_current_reference_cache()
    clear_temporary_video()
    activate_read_only_failure_probe()
    official(['bash', T / '新管/做.sh', NO, '--不推'], 'canonical-draft')
    assert_reviewed_gain_controls(requested, 'canonical-draft')
    official(['bash', T / '新管/定稿.sh', NO], 'canonical-final4K')
    assert_reviewed_gain_controls(requested, 'canonical-final4K')
    collect_confirmation_continuity()
    checked(['python3', T / '新管/印章.py'], 'original-stamp-after-production.log')
    current = json.loads((W / f'scripts/{NO}.json').read_text())
    assert same_summary_content(requested_summary, summary(current)), (
        'Canonical summary changed words, punctuation or the five main points.')
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
    if NO in APPROVED_AUDIO_REPAIRS:
        # Root supplies actual approved audio-change validation. No gain/overlay implementation is assumed here.
        helper_name = ('audio05-tail-qc.py' if NO == '05' else
                       'audio16-origin-qc.py' if NO == '16' else
                       'audio27-controlled-qc.py' if NO == '27' else
                       'audio62-controlled-qc.py' if NO == '62' else
                       'audio-controlled-qc.py' if NO in CONTROLLED_AUDIO_REPAIRS else
                       'audio-a21-qc.py' if NO in A21_AUDIO_REPAIRS else 'audio-qc.py')
        audio_qc = TASK / helper_name
        assert audio_qc.exists(), f'Root must attach approved audio QC for article {NO}.'
        evidence = OUT / f'{NO}-approved-audio-qc.json'
        checked(['python3', audio_qc, '--article', NO, '--accepted-source', source_video,
                 '--canonical-video', canonical, '--work', W, '--request', request,
                 '--output', evidence], 'approved-audio-qc.log', ROOT)
        audio_evidence = json.loads(evidence.read_text())
        assert audio_evidence.get('article') == NO and audio_evidence.get('passed') is True
        status['approved_audio_qc'] = audio_evidence
        status['approved_audio_qc_program_sha256'] = sha(audio_qc)
        if NO in A21_AUDIO_REPAIRS:
            status['approved_audio_repair_scope'] = {
                'kind': 'one-root-approved-original-release-instead-of-grafted-release',
                'request_source_sha256': sha(request / f'视频/脚本/{NO}.json'),
                'reference_file_sha256': sha(TASK / 'audio-a21-qc-reference.json'),
                'original_A21_five_phase_checks_required': True,
                'untouched_voice_waveform_level_pitch_and_controls_required': True}
        elif NO in CONTROLLED_AUDIO_REPAIRS:
            assert audio_evidence.get('kind') in {'controlled_audio_repair',
                                                 'root-approved-current-source-controlled-audio-repair',
                                                 'exact-two-approved-opening-pieces-controlled-audio-repair'}
            if NO == '27':
                assert audio_evidence.get('kind') == 'exact-two-approved-opening-pieces-controlled-audio-repair'
            else:
                assert audio_evidence.get('kind') != 'exact-two-approved-opening-pieces-controlled-audio-repair'
            assert audio_evidence.get('repair_applied') is True
            if NO != '05':
                assert audio_evidence.get('diagnostic_only') is False
                assert audio_evidence.get('production_delivery_eligible') is True
            reference_file = TASK / ('audio05-tail-qc-reference.json' if NO == '05' else
                                     'audio16-origin-qc-reference.json' if NO == '16' else
                                     'audio27-controlled-qc-reference.json' if NO == '27' else
                                     'audio62-controlled-qc-reference.json' if NO == '62' else
                                     'audio-controlled-qc-reference.json')
            status['approved_audio_repair_scope'] = {
                'kind': 'controlled_audio_repair', 'repair_applied': True,
                'request_source_sha256': sha(request / f'视频/脚本/{NO}.json'),
                'reference_file_sha256': sha(reference_file),
                'actual_original_full_pipeline_passed_first': True,
                'whole_track_actual_audio_and_approved_unchanged_regions_required': True}
    else:
        assert canonical_aac == accepted_aac, 'Canonical AAC differs from the accepted prior voice.'
    verify_unchanged_review_audio_packets(source_video, canonical)
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
    if NO not in APPROVED_AUDIO_REPAIRS:
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
    collect_actual_public_sources(request, W / f'scripts/{NO}.json')
    save()
    final = add_approved_illustrated_tail(request, final, OUT / f'{NO}-summary-verification.json')
    save()
    print(json.dumps(status, ensure_ascii=False), flush=True)
except Exception as exc:
    status['passed'] = False
    status['error'] = str(exc)
    for collector in (collect_confirmation_continuity, failure_audio_diagnostics, export_failed_current_video,
                      collect_original_asr_target_evidence):
        try:
            collector()
        except Exception as collection_error:
            # Evidence collection must not hide the original official failure.
            status.setdefault('failure_evidence_collection_errors', []).append({
                'collector': collector.__name__, 'type': type(collection_error).__name__,
                'message': str(collection_error).replace(str(M), '<private-machine>')[:700]})
    save()
    print(json.dumps(status, ensure_ascii=False), flush=True)
    raise

finally:
    collect_actual_current62_dual_ASR_contexts()
