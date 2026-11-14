#!/usr/bin/env python3
"""Export public article source candidates from an immutable restored warm cache.

No synthesis, rendering, source edits, GT access, or private audio export occurs.
Every candidate's old-video/fingerprint/AAC bindings are recorded separately.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4194304), b''):
            h.update(block)
    return h.hexdigest()


def native_fp_matches(value, full):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{16}', value) is not None and value == full[:16]


def aac_sha(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
                                   '-map', '0:a:0', '-vn', '-c:a', 'copy', '-f', 'adts', '-'], stderr=subprocess.PIPE)
    return hashlib.sha256(raw).hexdigest()


def main():
    root = Path.cwd()
    task = root / '.github/warm-source-readonly'
    machine = Path(os.environ['RUNNER_TEMP']) / 'completion-machine'
    work = machine / 'video'
    output = root / 'warm-source-evidence'
    output.mkdir(exist_ok=True)
    reference_file = task / 'accepted-audio-reference70.json'
    refs = json.loads(reference_file.read_text())
    assert refs['count'] == 70 and len(refs['rows']) == 70
    anchors = {row['id']: row for row in refs['rows']}
    assert set(anchors) == {f'{n:02d}' for n in range(1, 71)}
    report = {'kind': 'read-only-restored-warm-cache-public-source-candidates',
              'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'run_id': os.environ.get('GITHUB_RUN_ID'), 'head_commit': os.environ.get('GITHUB_SHA'),
              'immutable_restore_key': 'completion-05-machine-43294745262',
              'restore_cache_hit': os.environ.get('ORIGINAL_CACHE_HIT'),
              'cache_origin': 'Existing fixed GitHub Actions warm-machine archive; not this batch working outputs.',
              'accepted_AAC_anchor_manifest_sha256': sha(reference_file),
              'collector_program_sha256': sha(__file__),
              'synthesis_or_rendering_executed': False, 'source_or_cache_modified': False,
              'GT_TTS_models_private_PCM_or_AAC_bytes_exported': False,
              'quality_acceptance': False,
              'warning': 'Candidates are never applied to approved requests. Only an exact original fingerprint plus accepted AAC binding establishes an accepted voice source.',
              'articles': []}
    assert report['restore_cache_hit'] == 'true'
    for no in sorted(anchors):
        row = {'article': no, 'accepted_anchor': anchors[no], 'eligible_as_accepted_voice_source': False}
        source = work / 'scripts' / f'{no}.json'
        if not source.is_file():
            row['source_present'] = False
            report['articles'].append(row)
            continue
        try:
            assert not source.is_symlink() and source.stat().st_size < 2097152
            original_bytes = source.read_bytes()
            data = json.loads(original_bytes)
            assert str(data['no']).zfill(2) == no and isinstance(data['title_en'], str)
            assert isinstance(data['sentences'], list) and all(isinstance(s['chunks'], list) for s in data['sentences'])
            target = output / f'{no}-restored-cache-source-candidate.json'
            target.write_bytes(original_bytes)
            source_sha = sha(source)
            assert sha(target) == source_sha
            row.update({'source_present': True, 'source_file': target.name, 'source_sha256': source_sha,
                        'source_bytes': len(original_bytes), 'source_top_level_keys': sorted(data),
                        'existing_confirmation_counts': {k: len(v) if isinstance(v, (dict, list)) else None
                                                        for k, v in data.get('核对确认', {}).items()}})
            video, fingerprint = work / f'{no}.mp4', work / f'{no}.mp4.指纹.json'
            row.update({'cached_video_present': video.is_file(), 'cached_fingerprint_present': fingerprint.is_file()})
            if fingerprint.is_file():
                fp = json.loads(fingerprint.read_text())
                row['original_fingerprint_file_sha256'] = sha(fingerprint)
                # Only native scalar provenance fields; never arbitrary arrays.
                row['original_fingerprint_scalars'] = {k: fp[k] for k in
                    ('视频', '脚本', '配音', '程序', '只出声音')
                    if k in fp and isinstance(fp[k], (str, int, float, bool, type(None)))}
                row['source_matches_original_fingerprint'] = native_fp_matches(fp.get('脚本'), source_sha)
                if video.is_file():
                    video_sha = sha(video)
                    observed_aac = aac_sha(video)
                    row.update({'cached_video_sha256': video_sha,
                                'cached_video_AAC_ADTS_sha256': observed_aac,
                                'cached_video_matches_original_fingerprint': native_fp_matches(fp.get('视频'), video_sha),
                                'cached_video_full_bytes_equal_accepted_MP4': video_sha == anchors[no]['accepted_video_sha256'],
                                'cached_AAC_exactly_equal_accepted_AAC': observed_aac == anchors[no]['accepted_AAC_ADTS_SHA256']})
                    row['eligible_as_accepted_voice_source'] = all(row.get(k) is True for k in
                        ('source_matches_original_fingerprint', 'cached_video_matches_original_fingerprint',
                         'cached_AAC_exactly_equal_accepted_AAC'))
                wav = work / f'work_{no}/a.wav'
                row['internal_producer_PCM_present'] = wav.is_file()
                if wav.is_file():
                    pcm_sha = sha(wav)
                    row['internal_producer_PCM_sha256'] = pcm_sha
                    row['internal_producer_PCM_matches_original_fingerprint'] = native_fp_matches(fp.get('配音'), pcm_sha)
            assert source.read_bytes() == original_bytes, 'Read-only collection changed a cached source.'
        except Exception as exc:
            row['diagnostic_error'] = {'type': type(exc).__name__,
                'message': str(exc).replace(str(machine), '<restored-machine>')[:600]}
        report['articles'].append(row)
    report['source_candidates_present'] = sum(row.get('source_present') is True for row in report['articles'])
    report['exact_accepted_voice_source_bindings'] = sum(row['eligible_as_accepted_voice_source'] for row in report['articles'])
    report_path = output / 'restored-source-bindings70.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'source_candidates_present': report['source_candidates_present'],
                      'exact_accepted_voice_source_bindings': report['exact_accepted_voice_source_bindings'],
                      'quality_acceptance': False, 'private_audio_exported': False}))


if __name__ == '__main__':
    main()
