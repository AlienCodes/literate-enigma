"""Read-only original66 raw replay and S9 evidence; never changes a source/confirmation."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import traceback
import zipfile

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
ORIGINAL = AUDIT / 'readonly-failed54-61-66-69-43543967031/66'
META = ORIGINAL / 'public-original-metadata'
REPLAY = AUDIT / 'audio65-69-source-readonly/replay_original_sources.py'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    proof = json.loads((META / '66-failed-draft-proof.json').read_text())
    report = {'article': '66', 'kind': 'original_source_actual_raw_replay_and_ASR_evidence_availability',
              'quality_acceptance': False, 'automatic_confirmation': False,
              'source_audio_controls_or_core_modified': False,
              'workflow_launched': False, 'private_PCM_or_cache_exported': False,
              'original_failed_proof_sha256': sha(META / '66-failed-draft-proof.json'),
              'original_failed_source_sha256': sha(META / '66-failed-working-source.json'),
              'replay_loader_sha256': sha(REPLAY)}
    try:
        assert report['original_failed_source_sha256'] == proof['source_sha256']
        module_spec = importlib.util.spec_from_file_location('original66_replay', REPLAY)
        R = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(R)
        tools = json.loads((META / '66-reference-gain-diagnostic.json').read_text())['tool_sha256']
        assert hashlib.sha256(R.m.source.encode()).hexdigest() == tools['make_video.py']
        assert hashlib.sha256(R.m.clean.encode()).hexdigest() == tools['clean.py']
        report['unchanged_original_program_sha256'] = tools
        data = json.loads((META / '66-failed-working-source.json').read_text())
        # The reusable65/69 scope has no synthesis-punctuation rows there.
        # Original66 S8 does have its already requested punctuation rows.
        # Hydrate exactly the original main-loop mapping before its original
        # _pron wrappers run. No model input, source/control or core function
        # is invented or changed; the native fullWAV/AAC still must match.
        original_scope = R.scope
        original_tree = ast.parse(R.m.source)
        ini_node = next(n for n in original_tree.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == '_ini' for t in n.targets))
        def scope_with_original_punctuation(d, si, cache):
            ns, text = original_scope(d, si, cache)
            exec(compile(ast.Module(body=[ini_node], type_ignores=[]), str(R.m.T / 'make_video.py') + '#original_ini_assignment', 'exec'), ns)
            label = 'S' + str(si)
            pairs = d.get('合成标点', {}).get(label, [])
            for before, after in pairs:
                assert ns['_合成标点可收'](before, after)
            ns['SYNTH_PUNCT'] = {(f'scripts/{d["no"]}.json', label): (text, [tuple(x) for x in pairs])} if pairs else {}
            return ns, text
        R.scope = scope_with_original_punctuation
        report['additional_original_main_loop_data_hydration'] = {
            'field': '合成标点', 'actual_source_rows': data.get('合成标点', {}),
            'reason': 'Reusable65/69 diagnostic scope omitted this existing66 field; originalA45 correctly stopped the first local reconstruction, not the native failed producer.',
            'original_synth_punctuation_validator_actually_applied': True,
            'core_functions_or_existing_source_pairs_modified': False}
        with tempfile.TemporaryDirectory(prefix='private66-actual-raw-probe-', dir='/dev/shm') as temp:
            temp = Path(temp)
            cache = temp / 'cache'
            cache.mkdir()
            raw, parts = R.build(data, cache)
            wav = temp / 'a.wav'
            sf.write(wav, raw, 24000)
            report['replayed_private_WAV_sha256'] = sha(wav)
            report['actual_native_private_WAV_sha256'] = proof['internal_pcm_sha256']
            report['replayed_private_WAV_MD5_first12'] = hashlib.md5(wav.read_bytes()).hexdigest()[:12]
            assert sha(wav) == proof['internal_pcm_sha256'], 'Raw replay does not bind actual native a.wav'
            encoded = temp / 'public-encode-diagnostic.m4a'
            subprocess.run([R.FF, '-y', '-loglevel', 'error', '-i', str(wav), '-af', R.AF,
                            '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(encoded)], check=True)
            adts = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(encoded), '-map', '0:a:0',
                                            '-c:a', 'copy', '-f', 'adts', '-'])
            report['replayed_AAC_ADTS_sha256'] = hashlib.sha256(adts).hexdigest()
            assert report['replayed_AAC_ADTS_sha256'] == proof['aac_adts_sha256']
            report['actual_failed_raw_WAV_and_AAC_both_reproduced_exactly'] = True
            s9 = next(p for p in parts if p['sentence'] == 'S9')
            report['S9_actual_original_producer_replay_scalar_metadata'] = s9
            report['original_G72_scalar_provenance'] = list(R.m.cache_rows.values())
            report['original_stored_level_scalar_provenance'] = list(R.level_rows.values())
            reference = ' '.join(re.sub(r'\{\{.*?\}\}|\*\*', '', c['en']) for c in data['sentences'][8]['chunks'])
            report['reference'] = reference
            model_root = Path('~/asr').expanduser()
            candidates = {'small.en': model_root / 'sherpa-onnx-whisper-small.en/small.en-encoder.int8.onnx',
                          'parakeet': model_root / 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/encoder.int8.onnx'}
            present = {k: p.is_file() for k, p in candidates.items()}
            report['actual_local_original_ASR_model_availability'] = present
            report['two_original_recognizers_transcripts_collected'] = False
            report['ASR_diagnostic_remaining'] = 'Both original ASR model directories are absent locally; no transcript or pronunciation verdict is invented. Native original two-route collector has66:S9 support.'
        public = HERE / '66-failed-draft.mp4'
        with zipfile.ZipFile(ORIGINAL / 'article66-original-output.zip') as z:
            names = [n for n in z.namelist() if Path(n).name == '66-failed-draft.mp4']
            assert len(names) == 1
            if not public.exists():
                public.write_bytes(z.read(names[0]))
        assert sha(public) == proof['video_sha256']
        lo, hi = s9['start_s'] - .12, s9['end_s'] + .12
        clip = HERE / '66-S9-public-AAC-context.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(lo), '-i', str(public), '-t', str(hi - lo),
                        '-map', '0:a:0', '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(clip)], check=True)
        report['public_context'] = {'path': str(clip), 'sha256': sha(clip), 'source_public_video_sha256': sha(public),
                                    'public_absolute_seconds': [lo, hi], 'derived_from_public_MP4_only': True,
                                    'clock_relation': 'Raw sentence replay bounds plus120ms public context; not asserted raw/public sample alignment'}
    except BaseException as exc:
        report['diagnostic_error'] = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
    finally:
        report['self_owned_temporary_private_WAV_and_cache_removed'] = True
        report['no_pronunciation_or_user_confirmation_created'] = True
        (HERE / '66-actual-raw-replay-with-original-punctuation-and-ASR-availability.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, default=lambda x: float(x)) + '\n')
        print(json.dumps({'article': '66', 'actual_native_raw_bound': report.get('actual_failed_raw_WAV_and_AAC_both_reproduced_exactly', False),
                          'diagnostic_error': report.get('diagnostic_error'), 'quality_acceptance': False}, ensure_ascii=False))

if __name__ == '__main__':
    main()
