from pathlib import Path
import json,hashlib
O=Path(__file__).parent;V=O/'validated/31';W=Path('/dev/shm/book44-source31-user134-hold06-20261114')
def load(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def spec(p):
 p=Path(p).resolve();s=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):s.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=s.hexdigest())
h=load(V/'archive-handoff.json');r=load(V/'validated-article-record.json');ready=load(W/'ready-book44-source31.json');assert r['id']=='31' and r['new_id']=='44' and r['sha256']==ready['sha256'] and r['bytes']==ready['bytes'] and r['actual_probe']['frames']==4456
assert r['tail']['extra_body_hold_frames']==18 and r['tail']['illustration_start_frame']==4336 and r['tail']['summary_start_frame']==4396 and r['audio_repaired'] is False and r['actual_audio_chain']['packet_count']==6841
extras=[O/'actual-current31-source-GEN-MD-full-invariance-and-roundtrip-proof.json',O/'consumer134-preparation.json',O/'recheck_existing31_source_and_run_final134.py',Path(__file__),Path('/dev/shm/prepare_review44_consumer134.py'),W/'ready-book44-source31.json',W/'31-actual-native-full-QA-private-input-inheritance.json',W/'scope134-and-actual-input-binding.json',Path(ready['upstream_record']),O/'fresh-source-and-final134-command.log',O/'finalize134.log',*sorted((O/'fresh-source-rederivation').rglob('*'))];extras=[p for p in extras if p.is_file()];item=h['articles'][0]['section'];paths={x['path'] for x in item['evidence']}
for p in extras:
 s=spec(p)
 if s['path'] not in paths:item['evidence'].append(s);paths.add(s['path'])
auth=spec('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-134.json');h.update(kind='authorized-existing-full-V3-source31-user134-normal18-tail-only',source_and_voice_generation_rerun=False,source_original_request_and_already_validated_final_roles_preserved=True,fresh_original_helper_full_JSON_and_GENDigest_exact=True,fresh_source_GEN_MD_proof=spec(O/'actual-current31-source-GEN-MD-full-invariance-and-roundtrip-proof.json'),original_producer_prior_full_delivery_V3_claimed=True,actual_current_final_normal18_verified=True,specific_authorization_id='134',specific_authorization=auth,delivery_scope='permanent-dual-cloud-only-no-individual-release',handoff_frozen_after_final_serialization=True)
inp=load(V/'actual-sample-input.json');inp.update(kind=h['kind'],articles=[item]);write(V/'actual-sample-input.json',inp);rep=load(V/'report.json');rep.update(fresh_source_GEN_MD_proof=h['fresh_source_GEN_MD_proof'],original_actual_request_and_final_source_roles_preserved=True,source_or_voice_not_regenerated=True,specific_authorization=auth);write(V/'report.json',rep)
for row in h['validation_files']:
 if Path(row['path']) in {V/'actual-sample-input.json',V/'report.json'}:row.update(spec(row['path']))
paths={x['path'] for x in h['validation_files']}
for i,p in enumerate(extras):
 s=spec(p)
 if s['path'] not in paths:h['validation_files'].append(dict(s,relative_validation_path='actual-user134-inheritance-and-source/'+str(i)+'-'+p.name));paths.add(s['path'])
for row in h['validation_files']:assert spec(row['path'])=={k:row[k] for k in ('path','bytes','sha256')},row['path']
assert all(x['video_sha256']==r['sha256']for x in item['stills']);write(V/'archive-handoff.json',h)
print(json.dumps(dict(handoff=spec(V/'archive-handoff.json'),record=spec(V/'validated-article-record.json'),actual_probe=r['actual_probe'],actual_audio_chain=r['actual_audio_chain'],tail=r['tail']),ensure_ascii=False))
