from pathlib import Path
import importlib.util,json,sys,hashlib
BASE=Path('/dev/shm/native-inline-engine-review68-70-v27-exact-current-reference');sys.path.insert(0,str(BASE));import delivery as D

def sp(p):p=Path(p).resolve();return dict(path=str(p),bytes=p.stat().st_size,sha256=D.digest(p))
def declared_refs(value,trail=''):
 rows=[]
 if isinstance(value,dict):
  if all(k in value for k in ('path','bytes','sha256')) and str(value['path']).startswith('/'):
   if not str(value['path']).lower().endswith('.pdf'):rows.append((trail,value))
  for k,v in value.items():rows+=declared_refs(v,trail+'/'+str(k))
 elif isinstance(value,list):
  for i,v in enumerate(value):rows+=declared_refs(v,trail+'/'+str(i))
 return rows
for n,book,frames,packets in [('68','53',4357,6685),('70','50',4291,6583)]:
 O=Path('/dev/shm/review'+n+'-hold18-intake');E=O/'code';V=O/'validated'/n;W=Path('/dev/shm/source'+n+'-review102-hold18-20261114');sys.path.insert(0,str(E));s=importlib.util.spec_from_file_location('contract'+n,E/'review18_contract.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C);h=D.load(V/'review-handoff.json');r=D.load(V/'validated-article-record.json');raw=D.load(W/f'book{book}-source{n}-raw-report.json');profile=D.load(E/'normal18-actual-final-frozen-producer-profile.json');source=Path('/dev/shm/review'+n+'-sourceQA/43638596213/archive-handoff.json');prior=D.load(source);layout=next(x for x in D.load(prior['global_approved_evidence']['video_layout_approval']['path'])['articles']if x['source_id']==n);bookrow=next(x for x in D.load(prior['global_approved_evidence']['book_illustrations']['path'])['illustrations']if x['source_id']==n);normalized={k:raw['output_preview_hold_validation'][v]for k,v in profile['decoder_keys'].items()};req=json.loads((BASE/'exact-review102-current68-70-profiles.json').read_text())[n]['reference_document']['request_json_sha256']
 def check(q,article=n):return C.actual_normal_tail(q,article=article,new_id=book,expected_kind=profile['output_kind'],expected_program_sha=profile['helper']['sha256'],actual_hold=normalized,layout_row=layout,book_row=bookrow,request_json_sha256=req)
 check(raw);tests=[]
 for name,changed,article in [('production_promotion',dict(raw,production_delivery_eligible=True),n),('wrong_authority',dict(raw,specific_review_authorization_sha256='0'*64),n),('wrong_article',raw,'69')]:
  try:check(changed,article)
  except ValueError as e:tests.append(dict(case=name,rejected=True,reason=str(e)))
  else:raise AssertionError(name)
 test=O/f'actual-review102{n}-positive-and-three-required-eligibility-negatives.json';D.write(test,dict(source_id=n,actual_real_contract_passed=True,negatives=tests,original_physical_thresholds_and_media_unchanged=True));up=Path(D.load(W/f'ready-book{book}-source{n}.json')['upstream_record']);ap=up.with_name(n+'-review18-upstream-with-actual-source-V3-reference.json')
 assert h['preview_only']is True and h['preview_delivery_eligible']is True and h['production_delivery_eligible']is False and h['active_final_replacement_authorized']is False and h['articles'][0]['passed_per_article']is False and h['articles'][0]['preview_passed']is True
 assert r['id']==n and r['new_id']==book and r['preview_only']is True and r['production_delivery_eligible']is False and r['actual_probe']['frames']==frames and r['actual_audio_chain']['packet_count']==packets and r['tail']['extra_body_hold_frames']==18 and r['audio_repaired']is False
 extras=[up,Path(D.load(up)['inherited_actual_native_QA_record']),W/f'ready-book{book}-source{n}.json',test,Path('/dev/shm/prepare_review68_70_hold18_consumers.py'),Path(__file__),O/'actual-consumer-preparation.json'];item=h['articles'][0]['section'];known={x['path']for x in item['evidence']}
 for p in extras:
  t=sp(p)
  if t['path']not in known:item['evidence'].append(t);known.add(t['path'])
 h.update(review_only=True,review_delivery_eligible=True,user_individual_finalization_authorized=False,normal70_final_assembly_eligible=False,specific_review_authorization_id='102',original_producer_prior_deliveryV3_claim=False,current_source_fullV3_actually_bound=True,no_temporal_order_claim_between_sourceQA_and_producer_claim=True,original_native_inline_sourceQA_handoff_unchanged=sp(source),current_native_reference_not_formally_accepted_whole=True,original_legacy_accepted_AAC_difference_retained=True,no_new_acoustic_repair_applied=True,handoff_frozen_after_final_serialization=True)
 inp=D.load(V/'actual-sample-input.json');inp['articles']=[item];D.write(V/'actual-sample-input.json',inp);rep=D.load(V/'report.json');rep.update(review_only=True,user_individual_finalization_authorized=False,original_raw_producer_inheritance_record=sp(up),original_raw_claim_prior_full_deliveryV3=False,source_QA_actual_binding_without_chronology_claim=True,current_native_reference_not_formally_accepted_whole=True,old_legacy_AAC_identity_not_claimed=True);D.write(V/'report.json',rep)
 for row in h['validation_files']:
  if row['path']in {str(V/'actual-sample-input.json'),str(V/'report.json')}:row.update(sp(row['path']))
 known={x['path']for x in h['validation_files']}
 for i,p in enumerate(extras):
  t=sp(p)
  if t['path']not in known:h['validation_files'].append(dict(t,relative_validation_path=f'actual-review102{n}-role-and-authority/'+str(i)+'-'+p.name));known.add(t['path'])
 for row in h['validation_files']:assert sp(row['path'])=={k:row[k]for k in ('path','bytes','sha256')},row['path']
 # Check nested section/input declarations too; no stale metadata pointers like historical66.
 for path,v in declared_refs(h)+declared_refs(inp)+declared_refs(rep):assert sp(v['path'])=={k:v[k]for k in ('path','bytes','sha256')},(path,v['path'])
 assert all(x['video_sha256']==r['sha256']for x in item['stills']);D.write(V/'review-handoff.json',h);print(json.dumps(dict(handoff=sp(V/'review-handoff.json'),record=sp(V/'validated-article-record.json'),actual_probe=r['actual_probe'],audio=r['actual_audio_chain'],tail=r['tail'],review_only=True,production_delivery_eligible=False),ensure_ascii=False));sys.path.remove(str(E))
