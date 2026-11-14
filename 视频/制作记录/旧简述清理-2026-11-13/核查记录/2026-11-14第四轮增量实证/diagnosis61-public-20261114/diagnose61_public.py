"""Replay the exact failed61 public-MP4 diagnosis; no quality/source changes."""
import csv
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import numpy as np

from probe61_native_onset import measure

HERE = Path(__file__).resolve().parent
ORIGINAL = Path('/workspace/work/video-audit70-20261113/readonly-failed54-61-66-69-43543967031/61')
TOOLS = Path('/workspace/work/audit-repo/视频/工具')
ACCEPTED_REF = '64621068034f8b6e09836a6d97210a0e9b2f1ed6'
GIT = Path('/workspace/work/github-publication/target')
SR = 48000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def proc(args):
    return subprocess.check_output(args)


def decoded(path):
    return proc(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-ac', '1',
                 '-ar', str(SR), '-c:a', 'pcm_f32le', '-f', 'f32le', '-'])


def packets(path):
    data = json.loads(proc(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_packets',
                           '-show_data_hash', 'sha256', '-of', 'json', str(path)]))
    # pos is the byte offset in each MP4 container; 1080p/4K interleaving differs.
    # It is not sound or clock. Retain every other field, including priming side data.
    return [{k: v for k, v in p.items() if k != 'pos'} for p in data['packets']]


status = json.loads((ORIGINAL / '61-native-outer-status.json').read_text())
assert status['article'] == '61' and status['passed'] is False
archive = ORIGINAL / 'article61-original-output.zip'
assert sha(archive.read_bytes()) == '1a275f33ae6dbde1403be886baf4a7fb7583ff21d26e6d896e2a8706e54f2d8f'
new = HERE / '61-failed-draft.mp4'
if not new.exists():
    with zipfile.ZipFile(archive) as z:
        new.write_bytes(z.read('61-failed-draft.mp4'))
assert sha(new.read_bytes()) == status['failed_current_video']['sha256']
old = HERE / '61-accepted4K.mp4'
if not old.exists():
    old.write_bytes(proc(['git', '-C', str(GIT), 'show', ACCEPTED_REF + ':' + status['accepted_source']['path']]))
assert sha(old.read_bytes()) == status['accepted_source']['sha256']
old_source_path = HERE / '61-exact-old-accepted-source.json'
old_source_raw = proc(['git', '-C', str(GIT), 'show', ACCEPTED_REF + ':视频/脚本/61.json'])
if not old_source_path.exists():
    old_source_path.write_bytes(old_source_raw)
assert old_source_path.read_bytes() == old_source_raw
old_source = json.loads(old_source_raw)
working_path = ORIGINAL / 'public-original-metadata/61-failed-working-source.json'
working = json.loads(working_path.read_text())
diagnostic_path = ORIGINAL / 'public-original-metadata/61-reference-gain-diagnostic.json'
diagnostic = json.loads(diagnostic_path.read_text())
checker = TOOLS / '高亮同步核对.py'

before, after = decoded(old), decoded(new)
before_packets, after_packets = packets(old), packets(new)
packet_comparison = before_packets == after_packets
aac = proc(['ffmpeg', '-v', 'error', '-i', str(new), '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])
assert sha(aac) == status['accepted_source']['aac_adts_sha256']
assert before == after
assert packet_comparison
a = np.frombuffer(after, '<f4').astype(float)
rows = measure(a, SR, checker)
write('public-G45-scalar-scan.json', {'signal_and_clock': 'decoded public MP4 AAC at 48000Hz; NOT native a.wav',
                                    'original_checker_sha256': sha(checker.read_bytes()),
                                    'original_pure_functions_executed': ['是开口', '确认可收'],
                                    'quality_acceptance': False, 'confirmation_created': False,
                                    'rows': rows})
fine_passes = [r['time_s'] for r in rows if r['unchanged_original_G45_accepts']]

levels = []
for tick in range(10600, 11200, 10):
    t = tick / 1000
    i, F = round(t * SR), round(.01 * SR)
    seg = a[i:i + F]
    w = a[max(0, i - 2 * SR):i + 2 * SR]
    n = len(w) // F
    ref = np.sqrt(np.mean(w[:n * F].reshape(n, F) ** 2, axis=1)).max() + 1e-12
    db = float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) / ref + 1e-12))
    power = abs(np.fft.rfft(seg * np.hanning(F))) ** 2
    freqs = np.fft.rfftfreq(F, 1 / SR)
    centroid = float(np.sum(power * freqs) / (np.sum(power) + 1e-30))
    levels.append({'public_MP4_start_s': t, 'end_s': round(t + .01, 3),
                   'RMS_relative_to_local_4s_peak10ms_dB': db,
                   'Hann_window_power_spectral_centroid_Hz': centroid})
with (HERE / 'public-10ms-level-and-centroid.csv').open('w') as f:
    writer = csv.DictWriter(f, fieldnames=list(levels[0]))
    writer.writeheader()
    writer.writerows(levels)

gray = proc(['ffmpeg', '-v', 'error', '-i', str(new), '-vf',
             "select='between(n,321,333)',scale=320:180,format=gray", '-vsync', '0',
             '-c:v', 'rawvideo', '-f', 'rawvideo', '-'])
frames = np.frombuffer(gray, np.uint8).reshape(-1, 180, 320)
visual = [{'frame_index': 322 + i, 'public_MP4_seconds': (322 + i) / 30,
           'mean_absolute_gray_change_from_prior_frame': float(np.mean(abs(frames[i+1].astype(float) - frames[i])))}
          for i in range(len(frames) - 1)]
max_transition = max(visual, key=lambda r: r['mean_absolute_gray_change_from_prior_frame'])
write('public-rendered-frame-transition.json', {'method': 'actual decoded 320x180 grayscale frame differences, no media modification',
                                              'rows': visual, 'largest_actual_transition': max_transition})


def changed(a, b, path=''):
    if type(a) != type(b):
        return [path]
    if isinstance(a, dict):
        return sum((changed(a.get(k), b.get(k), path + '/' + str(k)) for k in sorted(a.keys() | b.keys())), [])
    if isinstance(a, list):
        return sum((changed(a[i] if i < len(a) else None, b[i] if i < len(b) else None, path + '/' + str(i))
                    for i in range(max(len(a), len(b)))), [])
    return [path] if a != b else []


source_diff = changed(old_source, working)
assert source_diff == ['/sentences/19/chunks/0/note']
assert old_source.get('核对确认', {}).get('高亮') is None
assert working.get('核对确认', {}).get('高亮') is None
assert old_source.get('高亮开始') == working.get('高亮开始') == {'S19 第2块': 134.64}
report = {
    'article': '61', 'kind': 'actual_failed_public_media_and_original_highlight_rule_diagnosis',
    'quality_acceptance': False, 'source_audio_checker_or_confirmations_modified': False,
    'workflow_launched': False, 'subjective_listening_claimed': False,
    'original_job': {'run': 43543967031, 'job': 132290751061, 'conclusion': 'failure',
                     'artifact': 14095365090, 'ZIP_bytes': archive.stat().st_size, 'ZIP_sha256': sha(archive.read_bytes())},
    'failed_stage': status['stage'], 'original_actual_failure': status['failure_details']['tail'],
    'exact_old_accepted_ref': ACCEPTED_REF, 'exact_old_accepted_media': status['accepted_source'],
    'exact_old_accepted_source_sha256': sha(old_source_raw),
    'actual_failed_working_source_sha256': sha(working_path.read_bytes()),
    'old_source_to_failed_source_changed_leaf_paths': source_diff,
    'all_highlight_and_audio_control_fields_deep_equal': True,
    'old_and_new_S1_highlight_confirmation': None,
    'no_old_S1_highlight_confirmation_exists_to_transfer': True,
    'old_and_new_existing_visual_overrides': working['高亮开始'],
    'actual_failed_media': status['failed_current_video'],
    'new_actual_ADTS_sha256': sha(aac),
    'actual_old_and_new_packet_count': len(before_packets),
    'all_public_AAC_packet_payloads_and_absolute_PTS_DTS_duration_side_data_exact': packet_comparison,
    'only_ignored_packet_field': 'pos: MP4 container byte offset, not payload or presentation time',
    'packet_projection_sha256': sha(json.dumps(before_packets, sort_keys=True, separators=(',', ':')).encode()),
    'whole_old_and_new_public_float32_bit_identical': before == after,
    'whole_public_float32_sha256': sha(after), 'whole_public_sample_count': len(a),
    'public_sample_rate': SR,
    'public_original_G45_1ms_and_5ms_grid_acceptance_times_s': fine_passes,
    'public_opening_10ms_levels': [r for r in levels if 10.84 <= r['public_MP4_start_s'] <= 11.05],
    'actual_public_video_largest_local_frame_transition': max_transition,
    'producer_public_timeline_S1_segments': diagnostic['public_producer_timing_metadata']['segments']['S1'],
    'original_native_WAV_md5_first12_from_actual_failure_log': '7499cce91ea3',
    'native_raw_onset_scalars_in_artifact': diagnostic['raw_highlight_onset_scalars'],
    'printed_alignment_values_are_rounded_not_exact': {'visual': 10.84, '乙': 10.85, '甲': 10.99, 'limit_s': .15},
    'original_highlight_auto_average_applicable': False,
    'proposal_only': {
        'visual_override_key': '高亮开始.S1 第2块', 'candidate_s': 10.9,
        'candidate_is_NOT_a_confirmation_or_audio_edit': True,
        'reason': 'This visual time is near the measured public /s/ onset and well inside both printed route estimates; printed routes differ by 0.14s, so their automatic-mean rule is unavailable. Original source/whole voice are otherwise unchanged.',
        'before_any_source_write': 'Run probe61_native_onset.py on the actual native a.wav to publish original G45 scalar results and exact native fingerprint; read original full-precision route values/list.txt. Root/audio owner must review concrete timing against these facts. Do not insert 开始读=10.9 as if it were a verified opening.',
        'must_not_do': ['Do not change audio gain/tempo/cut/cache to repair a visual-only boundary.',
                        'Do not manufacture old confirmation or listening approval.',
                        'Do not equate public 48k AAC time to native 24k a.wav time.',
                        'Do not relax original LIMIT or G45 or average routes that disagree beyond0.05s.'],
        'after_authorized_visual_change': 'Re-run actual original full draft/4K highlight and media QC; require accepted AAC packet/time preservation, then the actual illustrated-tail/V3 process.'},
    'clock_scope': 'All measured level, centroid, G45 and decoded-frame values in this report are PUBLIC MP4 absolute-clock diagnostics. Original raw a.wav is not present, decoded AAC has processing/codec effects, and these samples must never be used with the native7499cce91ea3 fingerprint as a fabricated native onset confirmation.',
    'tools_sha256': {n: sha((TOOLS / n).read_bytes()) for n in ['高亮同步核对.py', '高亮对齐.py', 'make_video.py']},
    'evidence_files': ['public-G45-scalar-scan.json', 'public-10ms-level-and-centroid.csv', 'public-rendered-frame-transition.json',
                       '61-exact-old-accepted-source.json', 'probe61_native_onset.py', 'diagnose61_public.py'],
}
write('diagnosis61-reviewable-report.json', report)
print(json.dumps({'report': str(HERE / 'diagnosis61-reviewable-report.json'), 'quality_acceptance': False,
                  'same_whole_public_PCM': before == after, 'same_packet_absolute_clock': packet_comparison,
                  'actual_packet_count': len(before_packets), 'public_G45_accepts_range': [min(fine_passes), max(fine_passes)],
                  'largest_video_transition': max_transition}, ensure_ascii=False))
