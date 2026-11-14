from pathlib import Path
import json,hashlib
O=Path(__file__).parent;V=O/'validated/29';W=Path('/dev/shm/book39-source29-user110-hold06-20261114')
def load(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def spec(p):
 p=Path(p).resolve();s=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):s.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=s.hexdigest())
h=load(V/'archive-handoff.json');r=load(V/'validated-article-record.json');ready=load(W/'ready-book39-source29.json');assert r['id']=='29' and r['new_id']=='39' and r['sha256']==ready['sha256'] and r['bytes']==ready['bytes'] and r['actual_probe']['frames']==4282
assert r['tail']['extra_body_hold_frames']==18 and r['tail']['illustration_start_frame']==4162 and r['tail']['summary_start_frame']==4222 and r['audio_repaired'] is False and r['actual_audio_chain']['packet_count']==6568
extras=[O/'actual-current29-source-GEN-MD-full-invariance-and-roundtrip-proof.json',O/'consumer110-preparation.json',O/'recheck_existing29_source_and_run_final110.py',Path(__file__),Path('/dev/shm/prepare_review39_consumer110.py'),W/'ready-book39-source29.json',W/'29-actual-native-full-QA-private-input-inheritance.json',W/'old-actual-body-current-PAY-and-110-scope-binding.json',W/'source29-original-status-schema-inheritance-receipt.json',W/'actual-five-boundary-visual-review.json',Path(ready['upstream_record']),O/'finalize110.log',O/'finalize110-real-upstream-neighbors.log',*sorted((O/'fresh-source-rederivation').rglob('*'))]
extras=[p for p in extras if p.is_file()];item=h['articles'][0]['section'];paths={e['path'] for e in item['evidence']}
for p in extras:
 s=spec(p)
 if s['path'] not in paths:item['evidence'].append(s);paths.add(s['path'])
auth=spec('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-110.json');h.update(kind='authorized-existing-full-V3-source29-user110-normal18-tail-only',source_and_voice_generation_rerun=False,source_original_request_and_already_validated_final_roles_preserved=True,fresh_original_helper_full_JSON_and_GENDigest_exact=True,fresh_source_GEN_MD_proof=spec(O/'actual-current29-source-GEN-MD-full-invariance-and-roundtrip-proof.json'),original_producer_prior_full_delivery_V3_claimed=True,actual_current_final_normal18_verified=True,specific_authorization_id='110',specific_authorization=auth,delivery_scope='permanent-dual-cloud-only-no-individual-release',handoff_frozen_after_final_serialization=True)
inp=load(V/'actual-sample-input.json');inp['kind']=h['kind'];inp['articles']=[item];write(V/'actual-sample-input.json',inp)
report=load(V/'report.json');report.update(fresh_source_GEN_MD_proof=h['fresh_source_GEN_MD_proof'],original_actual_source_request_role_preserved=True,original_status_schema_not_rewritten=True,source_or_voice_not_regenerated=True,specific_authorization=auth,second_actual_boundary_visual_review=spec(W/'actual-five-boundary-visual-review.json'));write(V/'report.json',report)
for x in h['validation_files']:
 if Path(x['path']) in {V/'actual-sample-input.json',V/'report.json'}:x.update(spec(x['path']))
paths={x['path'] for x in h['validation_files']}
for i,p in enumerate(extras):
 s=spec(p)
 if s['path'] not in paths:h['validation_files'].append(dict(s,relative_validation_path='actual-user110-inheritance-and-source/'+str(i)+'-'+p.name));paths.add(s['path'])
for x in h['validation_files']:assert spec(x['path'])=={k:x[k] for k in ('path','bytes','sha256')},x['path']
assert all(x['video_sha256']==r['sha256'] for x in item['stills']);write(V/'archive-handoff.json',h)
print(json.dumps(dict(handoff=spec(V/'archive-handoff.json'),record=spec(V/'validated-article-record.json'),actual_probe=r['actual_probe'],actual_audio_chain=r['actual_audio_chain'],tail=r['tail']),ensure_ascii=False))
