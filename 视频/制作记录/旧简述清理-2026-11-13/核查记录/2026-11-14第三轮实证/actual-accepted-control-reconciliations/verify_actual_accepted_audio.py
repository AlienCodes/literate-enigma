"""Prove exact public accepted audio for original-locator splice metadata reconciliation."""
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

B = Path('/workspace/work/video-audit70-20261113')
D = Path('/workspace/work/video-revision-delivery')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from delivery import source_invariants
spec = importlib.util.spec_from_file_location('original_tail_packets', B / 'illustrated-tail/illustrated_tail.py')
tail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tail)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def data_sha(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())

def decoded(path):
    return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                                    '-vn', '-c:a', 'pcm_f32le', '-f', 'f32le', '-'])

profiles = {}
for n in ('03', '04', '08'):
    root = B / f'next-passed-native/43543967031/{n}/artifact-files'
    status = json.loads(next(root.rglob(n + '-status.json')).read_text())
    accepted = status['accepted_source']
    assert status['passed'] is True and status['accepted_prior_aac_identical'] is True
    old = OUT / (n + '-accepted4K.mp4')
    if not old.exists():
        raw = subprocess.check_output(['git', 'show', '64621068034f8b6e09836a6d97210a0e9b2f1ed6:' + accepted['path']], cwd='/workspace/work/github-publication/target')
        assert sha(raw) == accepted['sha256']
        old.write_bytes(raw)
    assert sha(old.read_bytes()) == accepted['sha256']
    final = next(root.rglob(status['final_video_file']))
    before_packets = tail.packets(old, 'a:0', True)
    after_packets = tail.packets(final, 'a:0', True)
    assert before_packets == after_packets
    before_pcm, after_pcm = decoded(old), decoded(final)
    assert before_pcm == after_pcm
    collection = json.loads(next(root.rglob(n + '-actual-source-collection.json')).read_text())
    files = {k: next(root.rglob(v['file'])) for k, v in collection['files'].items()}
    request = json.loads(files['request_json'].read_text())
    actual = json.loads(files['actual_working_source'].read_text())
    key = 'S' + str(len(request['sentences']))
    before, after = request['结尾句'][key], actual['结尾句'][key]
    assert {k: v for k, v in before.items() if k not in {'接点', '依据'}} == {k: v for k, v in after.items() if k not in {'接点', '依据'}}
    normalized = copy.deepcopy(actual)
    normalized['结尾句'][key] = copy.deepcopy(before)
    remaining = source_invariants(request, normalized, n)
    report = {'source_id': n, 'kind': 'actual_accepted_whole_audio_identical_original_locator_metadata_reconciliation',
              'old_accepted_video': accepted, 'old_accepted_video_git_ref': '64621068034f8b6e09836a6d97210a0e9b2f1ed6',
              'new_native_final_sha256': sha(final.read_bytes()),
              'request_json_sha256': sha(files['request_json'].read_bytes()),
              'final_json_sha256': sha(files['actual_working_source'].read_bytes()),
              'request_structural_sha256': data_sha(request), 'final_structural_sha256': data_sha(actual),
              'actual_packet_count': len(before_packets),
              'all_packet_payload_absolute_pts_dts_duration_flags_and_side_data_exact': True,
              'packet_projection_sha256': data_sha(before_packets),
              'whole_public_decoded_float32_values': len(before_pcm) // 4,
              'whole_public_decoded_float32_bit_identical': True, 'whole_public_decoded_sha256': sha(before_pcm),
              'ending_key': key, 'request_ending': before, 'actual_original_locator_ending': after,
              'all_other_effective_controls_deep_equal': True, 'remaining_source_invariants': remaining,
              'source_or_video_or_audio_changed': False, 'private_PCM_GT_or_TTS_cache_exported': False}
    path = OUT / (n + '-actual-accepted-voice-equivalence-proof.json')
    if path.exists():
        history = OUT / 'history'
        history.mkdir(exist_ok=True)
        (history / (path.stem + '-' + sha(path.read_bytes()) + '.json')).write_bytes(path.read_bytes())
    raw = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode()
    path.write_bytes(raw)
    profiles[n] = {'request_structural_sha256': data_sha(request), 'final_structural_sha256': data_sha(actual),
                   'ending_key': key, 'old_join': before['接点'], 'new_join': after['接点'],
                   'actual_accepted_AAC_SHA256': accepted['aac_adts_sha256'],
                   'whole_public_decoded_sha256': sha(before_pcm), 'proof_sha256': sha(raw)}
(OUT / 'root-reviewed-exact-control-profiles.json').write_text(json.dumps(profiles, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'actual_verified_accepted_audio_equivalent_articles': list(profiles)}))
