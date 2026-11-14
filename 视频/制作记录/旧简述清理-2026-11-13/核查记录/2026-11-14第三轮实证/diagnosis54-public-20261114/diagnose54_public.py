"""Read-only diagnosis of actual54 output; never changes producer data or quality gates."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ORIGINAL = Path('/workspace/work/video-audit70-20261113/readonly-failed54-61-66-69-43543967031/54')
TOOLS = Path('/workspace/work/audit-repo/视频/工具')
SR = 48000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def decoded(path, codec, fmt):
    return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                                    '-vn', '-ac', '1', '-ar', str(SR), '-c:a', codec, '-f', fmt, '-'])


def original_dip_measurements(path):
    # Same 48k PCM16 decode and exact RMS/silence/segment equations as original audio_qc.py.
    raw = decoded(path, 'pcm_s16le', 's16le')
    a = np.frombuffer(raw, dtype='<i2').astype('float64') / 32768
    h = int(.01 * SR)
    rms = np.array([np.sqrt(np.mean(a[i:i+h] ** 2)) for i in range(0, len(a)-h, h)])
    q = 20 * np.log10(rms / (rms.max() + 1e-9) + 1e-9) < -45
    runs, st = [], None
    for i, v in enumerate(q):
        if v and st is None:
            st = i
        if not v and st is not None:
            runs.append((st / 100, (i-st) / 100))
            st = None
    segs, prev = [], 0
    for t, duration in runs:
        if t-prev > .4:
            segs.append((prev, t))
        prev = t+duration
    levels = [20*np.log10(np.sqrt(np.mean(a[int(x*SR):int(y*SR)] ** 2)) + 1e-9)
              for x, y in segs]
    median = float(np.median(levels))
    dips = [{'exact_MP4_clock_seconds': [x, y], 'original_formatted_key': f'{x:.1f}–{y:.1f}s',
             'RMS_dBFS': float(v), 'segment_median_dBFS': median,
             'dip_dB': median-float(v), 'original_reported_dB': float(f'{median-v:.1f}')}
            for (x, y), v in zip(segs, levels) if v < median-6.0]
    return {'segment_count': len(segs), 'median_dBFS': median, 'dips': dips,
            'decoded_PCM16_sha256': hashlib.sha256(raw).hexdigest()}


status = json.loads((ORIGINAL / '54-native-outer-status.json').read_text())
source_path = ORIGINAL / 'public-original-metadata/54-failed-working-source.json'
source = json.loads(source_path.read_text())
diagnostic_path = ORIGINAL / 'public-original-metadata/54-reference-gain-diagnostic.json'
diagnostic = json.loads(diagnostic_path.read_text())
old, new = HERE / '54-accepted4K.mp4', HERE / '54-failed-draft.mp4'
assert sha(old) == status['accepted_source']['sha256']
assert sha(new) == status['failed_current_video']['sha256']
result = subprocess.run(['/workspace/work/video-venv/bin/python', str(TOOLS / 'audio_qc.py'), str(new)],
                        capture_output=True, text=True)
write('original-audio-qc-reproduction-result.json',
      {'original_program': str(TOOLS / 'audio_qc.py'), 'program_sha256': sha(TOOLS / 'audio_qc.py'),
       'source_video_sha256': sha(new), 'actual_exit': result.returncode,
       'actual_stdout': result.stdout, 'actual_stderr': result.stderr,
       'purpose': 'Specific original failed check reproduction, not full acceptance'})
assert result.returncode == 1
measurements = {'old_accepted': original_dip_measurements(old), 'new_failed': original_dip_measurements(new)}
write('original-rule-dip-measurements.json', measurements)
assert [row['original_formatted_key'] for row in measurements['new_failed']['dips']] == ['95.6–96.0s', '118.3–118.8s']

x_raw, y_raw = decoded(old, 'pcm_f32le', 'f32le'), decoded(new, 'pcm_f32le', 'f32le')
x, y = np.frombuffer(x_raw, '<f4'), np.frombuffer(y_raw, '<f4')
assert len(x) == len(y)
mask = x != y
starts = np.flatnonzero(mask & np.r_[True, ~mask[:-1]])
ends = np.flatnonzero(mask & np.r_[~mask[1:], True]) + 1
ranges = []
if len(starts):
    left, right = int(starts[0]), int(ends[0])
    for ns, ne in zip(starts[1:], ends[1:]):
        if ns-right <= SR*.1:
            right = int(ne)
        else:
            ranges.append([left/SR, right/SR])
            left, right = int(ns), int(ne)
    ranges.append([left/SR, right/SR])
windows = [('S11 dip', 95.58, 96.02), ('S13 dip', 118.35, 118.78),
           ('full processed S11 first punctuation group', 94.04, 96.06),
           ('full processed S13', 114.91, 121.865)]
target_metrics = []
for name, start, end in windows:
    a, b = x[int(start*SR):int(end*SR)], y[int(start*SR):int(end*SR)]
    target_metrics.append({'name': name, 'absolute_public_MP4_clock_seconds': [start, end],
                           'public_decoded_sample_count': len(a), 'float32_bit_identical': bool(np.array_equal(a, b)),
                           'max_abs_difference': float(np.max(np.abs(a-b)))})
assert all(row['float32_bit_identical'] for row in target_metrics)
current_fingerprint = diagnostic['official_abnormal_edit_scalars']['current_pcm_md5_first12']
assert current_fingerprint == 'd9e2abbede1a'
policy_code = (TOOLS / '响度一致性核对.py').read_text()
tree = ast.parse(policy_code)
policy_nodes = [node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == '骤降确认可收'
                or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '骤降确认上限'
                                                       for t in node.targets)]
env = {}
exec(compile(ast.Module(body=policy_nodes, type_ignores=[]), str(TOOLS / '响度一致性核对.py'), 'exec'), env)
confirmations = []
for row in measurements['new_failed']['dips']:
    key = row['original_formatted_key']
    original = source['核对确认']['响度骤降'][key]
    confirmations.append({'key': key, 'original_confirmation_retained_exactly': original,
                          'current_original_runtime_PCM_fingerprint': current_fingerprint,
                          'stored_confirmation_fingerprint_matches': original['配音指纹'] == current_fingerprint,
                          'same_time_key': True,
                          'current_dB_within_original_confirmed_dB_plus_0_3': row['original_reported_dB'] <= original['低']+.3,
                          'original_policy_accepts_this_article_and_dB': env['骤降确认可收']('54', row['original_reported_dB'])})
assert all(not row['stored_confirmation_fingerprint_matches'] and
           row['current_dB_within_original_confirmed_dB_plus_0_3'] and
           row['original_policy_accepts_this_article_and_dB'] for row in confirmations)

report = {
    'kind': 'read_only_actual54_public_MP4_loudness_and_legacy_confirmation_diagnosis',
    'quality_acceptance': False, 'workflow_launched': False,
    'original_source_checker_or_media_modified': False, 'subjective_listening_claimed': False,
    'actual_old_accepted_Git_ref': '64621068034f8b6e09836a6d97210a0e9b2f1ed6',
    'old_accepted_source': status['accepted_source'], 'new_failed_media': status['failed_current_video'],
    'original_tools_sha256': {name: sha(TOOLS / name) for name in ['audio_qc.py', '交付核查.py', '响度一致性核对.py', 'make_video.py']},
    'original_audio_qc_actual_reproduced_exit': result.returncode,
    'original_audio_qc_actual_reproduced_stdout': result.stdout,
    'original_measurements': measurements,
    'actual_public_float32_sample_count_each': len(x),
    'actual_public_float32_comparison_without_any_alignment_shift': True,
    'old_public_float32_sha256': hashlib.sha256(x_raw).hexdigest(),
    'new_public_float32_sha256': hashlib.sha256(y_raw).hexdigest(),
    'whole_public_float32_identical': x_raw == y_raw,
    'same_public_float32_sample_count': int(np.count_nonzero(~mask)),
    'target_and_sentence_comparison': target_metrics,
    'remaining_whole_audio_difference_ranges_merged_gap_100ms': ranges,
    'legacy_confirmation_predicates': confirmations,
    'actual_processed_public_timing_metadata': diagnostic['public_producer_timing_metadata'],
    'clock_scope': 'All displayed times are actual decoded public MP4 absolute clock. Producer segment scalars are processed public timeline metadata, not original raw-mother timing. No raw-mother gain/cut interval is inferred or written.',
    'existing_manual_gain_controls': {key: source[key] for key in source if '增益' in key},
    'proposal_for_root_and_audio_owner': [
        'The two flagged syllable/sentence regions are sample-for-sample identical to the exact previously accepted public MP4. Do not raise their gain merely to silence this stale-fingerprint alert.',
        'The two existing confirmation time keys, original documented dB, historical wording and original permission quotation remain intact. If this exact audio survives the independent whole-audio issue below, root may approve transferring only the matching confirmation fingerprint to the actual final PCM fingerprint with this exact public-voice equality evidence. This is not a new user listening confirmation.',
        'Current d9e2abbede1a belongs only to this failed attempt. After any real audio repair, measure its new original PCM fingerprint and repeat the applicable local equality/clock check; do not blindly reuse this fingerprint.',
        'Independently resolve old/new whole AAC identity. Public float32 shows three short groups about +2 dB plus codec-neighbor residual changes, outside both alarm regions. Audio owner should replay the actual original G72/K134 cache/control path before choosing an approved repair or exact old-voice restoration. Do not speculate that CPU or gain alone is the proven cause.',
        'Only after source/audio stabilizes should official full draft/4K checks, the original loudness confirmation policy, and accepted-prior AAC identity or an expressly approved actual repair QC all pass. Updating these two confirmation records alone is not delivery acceptance.'
    ],
    'limitations': ['No new human/auditory listening is claimed.',
                    'Original private raw PCM, GT arrays, TTS mother/cache and raw-mother interval mapping are not exported or inferred.',
                    'The complete new failed artifact remains a failure and must not enter the accepted-film ledger.'],
    'program_sha256': sha(__file__),
    'original_artifact_zip': {'path': str(ORIGINAL / 'article54-original-output.zip'),
                              'sha256': sha(ORIGINAL / 'article54-original-output.zip')},
    'source_JSON': {'path': str(source_path), 'sha256': sha(source_path)},
    'original_reference_diagnostic': {'path': str(diagnostic_path), 'sha256': sha(diagnostic_path)},
}
write('diagnosis54-reviewable-report.json', report)
print(json.dumps({'quality_acceptance': False,
                  'actual_original_qc_dips_reproduced': len(measurements['new_failed']['dips']),
                  'both_dip_and_full_sentence_regions_bit_identical_to_old_accepted': True,
                  'only_failed_existing_confirmation_predicate_is_PCM_fingerprint': True,
                  'whole_audio_equality_still_unresolved': True,
                  'report_sha256': sha(HERE / 'diagnosis54-reviewable-report.json')}))
