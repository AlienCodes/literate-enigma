#!/usr/bin/env python3
"""Exact user148/current54 identity only; never executes or waives any quality gate."""
import argparse, copy, hashlib, json, subprocess, tempfile
from fractions import Fraction
from pathlib import Path

EXPECTED_REFERENCE_SHA256 = 'a8b77c7df2cd2b421fbb239aed8e24de2ea37569ded2ded890ba615fbff5815e'

def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def command(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def actual_aac(path):
    """Hash copied ADTS plus exact rational timestamp/payload/priming projection. Never rebase PTS."""
    raw = json.loads(command(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_streams', '-show_packets', '-show_data_hash', 'sha256', '-of', 'json', str(path)]))
    require(len(raw.get('streams', [])) == 1, f'No unique actual audio stream: {path}')
    stream = raw['streams'][0]; require(stream['codec_name'] == 'aac', f'Expected copied AAC: {path}')
    timebase = Fraction(stream['time_base']); packets = []
    for pkt in raw['packets']:
        timing = []
        for key in ('pts', 'dts', 'duration'):
            require(key in pkt, f'Cannot prove exact packet {key}: {path}')
            value = int(pkt[key]) * timebase
            timing.append([value.numerator, value.denominator])
        side = [{k: s[k] for k in sorted(s) if k != 'side_data_size'} for s in pkt.get('side_data_list', [])]
        require(pkt.get('data_hash'), f'No actual packet payload hash: {path}')
        packets.append({'timing_rationals': timing, 'size': int(pkt['size']), 'payload_sha256': pkt['data_hash'], 'side_data': side})
    codec = {k: stream.get(k) for k in ('codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout')}
    projection = {'codec': codec, 'packets': packets}
    encoded = json.dumps(projection, sort_keys=True, separators=(',', ':')).encode()
    with tempfile.TemporaryDirectory(prefix='actual-aac-') as td:
        adts = Path(td) / 'audio.aac'
        command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-vn', '-c:a', 'copy', '-f', 'adts', str(adts)])
        return {'aac_adts_sha256': digest(adts), 'packet_projection_sha256': hashlib.sha256(encoded).hexdigest(),
                'packet_count': len(packets), 'projection': projection}


def read_reference(path):
    require(digest(path) == EXPECTED_REFERENCE_SHA256, 'Exact identity54 reference differs')
    return json.loads(Path(path).read_text())


def file_measurement(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f'Missing regular actual identity file: {path}')
    return {'bytes': path.stat().st_size, 'sha256': digest(path)}


def validate_values(values, reference):
    """Pure binding predicates. Synthetic success is not acoustic or media acceptance."""
    p = reference
    checks = []
    def add(name, value):
        checks.append({'name': name, 'passed': bool(value)})
    def matches(actual, expected):
        return (isinstance(actual, dict)
                and all(actual.get(k) == v for k, v in expected.items()))
    add('only_exact54_user148_reference', p['source_id'] == '54' and p['book_order'] == '47'
        and p['user_feedback'] == '148')
    add('actual_original_canonical_pipeline_passed_before_identity',
        values.get('canonical_pipeline_passed') is True)
    for rel, expected in p['request_files'].items():
        add('actual_request_file_exact:' + rel, matches(values.get('request_files', {}).get(rel), expected))
    requested = values.get('requested_source')
    add('actual_current_source_deep_equals_exact_request_including_all_CF',
        isinstance(requested, dict) and requested.get('no') == '54'
        and values.get('current_source') == requested)
    authorization = values.get('authorization', {})
    add('actual_native_authorization_file_exact', matches(values.get('authorization_file'), p['authorization']))
    add('actual_user148_final_authorized_not_prior_review102',
        authorization.get('篇') == '54' and authorization.get('source_id') == '54'
        and authorization.get('book_order') == '47'
        and authorization.get('review_only') is False
        and authorization.get('user_individual_finalization_authorized') is True
        and authorization.get('inherited_feedback_ids') == [147, 148])
    for key in ('root_actual_S6_decision', 'actual_S6_report', 'core_manifest'):
        add('actual_file_exact:' + key, matches(values.get(key), p[key]))
    for rel, expected in p['runtime_files'].items():
        add('actual_runtime_file_exact:' + rel, matches(values.get('runtime_files', {}).get(rel), expected))
    current, legacy = values.get('current_audio', {}), values.get('legacy_audio', {})
    expected = p['current_audio']
    add('actual_entire_current_WAV_exact', current.get('whole_WAV_sha256') == expected['whole_WAV_sha256'])
    add('actual_entire_current_AAC_exact', current.get('AAC_ADTS_sha256') == expected['AAC_ADTS_sha256'])
    add('actual_current_absolute_packet_payload_side_and_rational_clock_exact',
        current.get('absolute_packet_projection_sha256') == expected['absolute_packet_projection_sha256'])
    add('actual_current_packet_count_exact', current.get('packets') == expected['packets'])
    add('actual_legacy_video_and_AAC_exact_historical_provenance',
        legacy.get('video_sha256') == p['legacy_provenance']['video_sha256']
        and legacy.get('AAC_ADTS_sha256') == p['legacy_provenance']['AAC_ADTS_sha256'])
    add('current_is_distinct_from_legacy_and_not_relabelled_as_accepted_whole',
        current.get('AAC_ADTS_sha256') != legacy.get('AAC_ADTS_sha256'))
    return {
        'kind': 'source54-user148-specific-current-native-final-identity-only',
        'article': '54', 'book_order': '47',
        'identity_binding_passed': all(row['passed'] for row in checks), 'checks': checks,
        'formal_quality_acceptance': False, 'repair_applied': False,
        'current_reference_not_formally_accepted_whole': True,
        'user148_final_authorized': True, 'review_only': False,
        'user_individual_finalization_authorized': True,
        'original_complete_pipeline_passed_before_identity_binding': values.get('canonical_pipeline_passed') is True,
        'no_original_gate_threshold_audio_or_confirmation_waiver': True,
        'actual_source_and_final_media_V3_still_required': True,
        'legacy_accepted_table_and_failure_history_preserved': True,
    }


def bind(request_dir, current, wav_path, canonical_video, legacy_video, tools, task,
         canonical_pipeline_passed):
    """Read genuine files and PCM/packet identities after the driver's true original gate success."""
    request_dir, tools, task = Path(request_dir), Path(tools), Path(task)
    p = read_reference(task / 'identity54_user148_current-reference.json')
    authorization_path = request_dir / 'user-authorization.json'
    values = {
        'canonical_pipeline_passed': canonical_pipeline_passed,
        'request_files': {rel: file_measurement(request_dir / rel) for rel in p['request_files']},
        'requested_source': json.loads((request_dir / '视频/脚本/54.json').read_text()),
        'current_source': current,
        'authorization_file': file_measurement(authorization_path),
        'authorization': json.loads(authorization_path.read_text()),
        'root_actual_S6_decision': file_measurement(task / 'root-source54-actual-S6-onset-and-levels-no-audio-change-finding-decision.json'),
        'actual_S6_report': file_measurement(task / '54-S6-cached-raw-onset-observations.json'),
        'core_manifest': file_measurement(task / 'certified-core/manifest.json'),
        'runtime_files': {rel: file_measurement(tools / rel) for rel in p['runtime_files']},
    }
    # All scalar/static prerequisites fail before decoding; a failed original pipeline
    # cannot use this identity checker as an alternative admission path.
    require(canonical_pipeline_passed is True, 'Original canonical pipeline must actually pass before identity')
    require(values['request_files'] == p['request_files'], 'Actual exact five request files differ')
    require(values['current_source'] == values['requested_source'], 'Actual current source differs, including CF or note')
    require(values['authorization_file'] == p['authorization'], 'Actual exact user148 authorization differs')
    for key in ('root_actual_S6_decision', 'actual_S6_report', 'core_manifest'):
        require(values[key] == p[key], 'Actual exact prerequisite file differs: ' + key)
    for rel, expected in p['runtime_files'].items():
        require(values['runtime_files'][rel]['sha256'] == expected['sha256'], 'Actual original runtime differs: ' + rel)
    current_chain, legacy_chain = actual_aac(canonical_video), actual_aac(legacy_video)
    values['current_audio'] = {
        'whole_WAV_sha256': digest(wav_path),
        'AAC_ADTS_sha256': current_chain['aac_adts_sha256'],
        'absolute_packet_projection_sha256': current_chain['packet_projection_sha256'],
        'packets': current_chain['packet_count'],
    }
    values['legacy_audio'] = {'video_sha256': digest(legacy_video),
                              'AAC_ADTS_sha256': legacy_chain['aac_adts_sha256']}
    evidence = validate_values(values, p)
    require(evidence['identity_binding_passed'], 'Exact54 user148/current identity predicates failed: '
            + ', '.join(row['name'] for row in evidence['checks'] if not row['passed']))
    evidence.update({
        'reference_sha256': digest(task / 'identity54_user148_current-reference.json'),
        'program_sha256': digest(__file__), 'request_files': values['request_files'],
        'native_user_authorization': values['authorization_file'],
        'root_actual_S6_decision': values['root_actual_S6_decision'],
        'actual_S6_report': values['actual_S6_report'],
        'actual_core_manifest': values['core_manifest'], 'actual_runtime_files': values['runtime_files'],
        'actual_current_audio': values['current_audio'], 'actual_legacy_audio': values['legacy_audio'],
        'actual_canonical_video_sha256': digest(canonical_video),
    })
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('request-dir', 'actual-source', 'wav', 'canonical-video', 'legacy-video', 'tools', 'task', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--original-canonical-pipeline-passed', action='store_true')
    args = parser.parse_args()
    evidence = bind(args.request_dir, json.loads(args.actual_source.read_text()), args.wav,
                    args.canonical_video, args.legacy_video, args.tools, args.task,
                    args.original_canonical_pipeline_passed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
