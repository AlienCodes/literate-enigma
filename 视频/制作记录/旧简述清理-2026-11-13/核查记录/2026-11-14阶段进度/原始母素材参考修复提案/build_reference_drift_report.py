"""Summarize public native-run scalar evidence and a proposed raw-mother fix."""
import hashlib
import json
from pathlib import Path

B = Path('/workspace/work/video-audit70-20261113')
O = B / 'core-overlays/reference-reproducibility'
OLD = B / 'ci-relayed-43522684973'
NEW = B / 'ci-direct-43526354790-51'

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def differences(a, b, path=''):
    if type(a) is not type(b): return [path]
    if isinstance(a, dict):
        return sum((differences(a.get(k), b.get(k), path + '/' + k)
                    for k in sorted(set(a) | set(b))), [])
    if isinstance(a, list):
        return sum((differences(x, y, path + '/' + str(i))
                    for i, (x, y) in enumerate(zip(a, b))), []) + ([path + '/length'] if len(a) != len(b) else [])
    return [] if a == b else [path]

a = read(OLD / '51-reference-gain-diagnostic.json')
b = read(NEW / '51-reference-gain-diagnostic.json')
ap = read(OLD / '51-checker-reference-preparation.json')
bp = read(NEW / '51-checker-reference-preparation.json')
af = read(OLD / '51-failed-draft-proof.json')
bf = read(NEW / '51-failed-draft-proof.json')
mother = read(O / '51-raw-mother-provenance.json')
gt_changes = [{'text_index': x['text_index'], 'old_sha256': x['gt_sha256'],
               'new_sha256': y['gt_sha256'], 'equal': x['gt_sha256'] == y['gt_sha256']}
              for x, y in zip(a['texts'], b['texts'])]
assert len(gt_changes) == 20 and not any(x['equal'] for x in gt_changes)
assert a['wav_sha256'] == b['wav_sha256'] == af['internal_pcm_sha256'] == bf['internal_pcm_sha256']
assert af['aac_adts_sha256'] == bf['aac_adts_sha256']
unchanged = ['gt_meta_sha256', 'tool_sha256', 'model_sha256', 'versions', 'segment_record_sha256', 'actual_pcm']
assert all(a[k] == b[k] for k in unchanged)
sd = differences(read(OLD / '51-failed-working-source.json'), read(NEW / '51-failed-working-source.json'))
assert sd == ['/核对确认/非人声/21.93–22.02s']
report = {
    'purpose': '51 cross-CPU raw-reference incompatibility and minimal repair proposal',
    'article': '51', 'acceptance': False, 'source_or_checker_modified_by_this_review': False,
    'evidence_inputs': [{'path': str(p), 'sha256': sha(p)} for p in [
        OLD / '51-reference-gain-diagnostic.json', NEW / '51-reference-gain-diagnostic.json',
        OLD / '51-checker-reference-preparation.json', NEW / '51-checker-reference-preparation.json',
        OLD / '51-failed-draft-proof.json', NEW / '51-failed-draft-proof.json',
        O / '51-raw-mother-provenance.json', O / '51-title-original-mother-vs-reference.json']],
    'actual_outputs': {
        'old_mp4_sha256': af['video_sha256'], 'new_mp4_sha256': bf['video_sha256'],
        'actual_internal_pcm_sha256_unchanged': a['wav_sha256'],
        'actual_aac_adts_sha256_unchanged': af['aac_adts_sha256'],
        'actual_pcm_scalar_metadata': a['actual_pcm'],
        'working_source_differences': sd,
        'audio_controls_and_spoken_content_unchanged': True,
        'both_original_drafts_failed_acceptance': not af['passed'] and not bf['passed'],
    },
    'reference_comparison': {
        'old_cpu': a['execution']['cpu'], 'new_cpu': b['execution']['cpu'],
        'unchanged_fields': {k: a[k] for k in unchanged},
        'old_private_cache_inventory': ap['existing_private_cache_inventory_sha256_after'],
        'new_private_cache_inventory': bp['existing_private_cache_inventory_sha256_after'],
        'private_cache_inventory_unchanged_between_runs': ap['existing_private_cache_inventory_sha256_after'] == bp['existing_private_cache_inventory_sha256_after'],
        'old_public_cache_inventory': ap['public_repository_cache_inventory_sha256'],
        'new_public_cache_inventory': bp['public_repository_cache_inventory_sha256'],
        'old_reference_peak': a['reference_global_peak'], 'new_reference_peak': b['reference_global_peak'],
        'old_gain': a['default_audit_gain'], 'new_gain': b['default_audit_gain'],
        'gt_array_hash_changes': gt_changes,
        'changed_gt_array_count': 20, 'total_gt_array_count': 20,
        'old_anchor_summary': a['anchor_summary'], 'new_anchor_summary': b['anchor_summary'],
        'old_official_audit': a['official_audit'], 'new_official_audit': b['official_audit'],
        'old_official_selftests': a['official_selftest_status_lines'],
        'new_official_selftests': b['official_selftest_status_lines'],
        'interpretation': 'The exact same actual PCM/AAC is compared against 20 different GT arrays on a different CPU. The new checker itself reports self-test failure. Its 100 cut and 125 edge findings cannot be treated as new verified sound defects. The prior 2 cut and 8 edge findings remain unresolved until reproduced with a compatible reference.',
    },
    'root_cause': {
        'producer': 'maker._cached verifies native marker or registered legacy SHA, then returns the original direct create pickle for both classes. The tuple is stored before say/cleaning/grafts/gain/fades/pause cuts/assembly.',
        'independent_synth': 'synth._按缓存 reads only legacy cache. For a valid .单线程 entry it verifies the stored bytes but discards them and calls _raw_create on the current CPU. Single-thread settings do not guarantee identical ONNX floating point across these CPUs.',
        'gt_key_gap': 'GT cache filename/meta binds text, model-derived phonemes and transform parameters, but does not bind raw mother array SHA. Same GT filename/meta can therefore contain different waveform bytes.',
        'raw_mother_schema_proof': {'report': str(O / '51-raw-mother-provenance.json'),
                                    'sha256': sha(O / '51-raw-mother-provenance.json'),
                                    'verified_native_marker_entries': mother['checked_count']},
        'untransformed_title_direct_bit_identity': read(O / '51-title-original-mother-vs-reference.json'),
    },
    'minimal_proposal': {
        'patch': str(O / 'synth-raw-mother-proposal.patch'),
        'patch_sha256': sha(O / 'synth-raw-mother-proposal.patch'),
        'base_synth_sha256': sha(Path('/workspace/work/audit-repo/视频/工具/独立复核/synth.py')),
        'patch_scope': 'Only the synth raw-create input loader: return exact source-verified original create pickle for both marker-verified and registered legacy entries; verify tuple2/float32/1D/finite/24000 schema; missing mother stops.',
        'independence_preserved': 'Reference creation receives original unprocessed model output. Original independent GT graft/gain/fade/ramp/pause processing, labels, sample audit and five deliberate bad-audio selftests execute normally. No actual a.wav or GT array is read to derive the mother.',
        'untouched_controls': ['source JSON and spoken English', 'all gain and boundary metadata', '2.2/32768 sample tolerance', 'original -55/-40 dB boundaries', 'original five bad-sample injections', 'actual source PCM/AAC bytes'],
        'mandatory_native_preflight': [
            'For every actual loader call, compute exact create key from original model ID, full model SHA, voice array SHA1/full voice-file SHA, exact spoken/phoneme input SHA, speed .95, lang, sorted kwargs. Record only these scalar values.',
            'Read a raw create tuple from the pinned repository cache or the original private producer cache with a fullSHA comparison to that pinned raw entry. Keep original marker/registered-legacy checks. Emit actual per-key fullSHA and schema, never pickle/waveform bytes. The local three-entry proof does not itself prove all native private entry bytes.',
            'Use a fresh empty QC_DIR for the first native replay, so existing same-name GT files cannot skip synthesis. For persistent GT reuse, bind the complete mother-manifest SHA in the GT cache namespace or a checked sidecar; reject a different manifest.',
            'Record loaded raw-mother hashes and independently produced GT hashes. Repeat on a second CPU/runtime only after all per-key mother identities match; both should then yield identical independently transformed GT hashes.',
            'Run the original checker selftests and require five of five caught. Verify known good anchors/PCM do not acquire global false residuals. Preserve and inspect all remaining genuine cut/edge findings.',
            'Prove actual internal PCM and AAC fullSHA remain the values recorded in actual_outputs. This is a read-only reference replay; audio controls are not a repair target for CPU drift.',
        ],
        'native_result': 'NOT RUN by this review; root approval and actual native 5/5/unchanged-PCM evidence required before adoption.',
        'current_2cuts_8edges': 'Still blocked; obtain exact current-source times and original amplitudes from a compatible-reference native report before proposing any audio metadata correction.',
    },
}
dest = O / '51-reference-reproducibility-proposal.json'
dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'report': str(dest), 'sha256': sha(dest), 'all_gt_arrays_changed': 20,
                  'actual_pcm_unchanged': a['wav_sha256'], 'proposal_only': True}))
