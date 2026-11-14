from pathlib import Path
import sys,json,difflib
E=Path('/dev/shm/review18-hold18-intake/code');sys.path.insert(0,str(E));import validate_review102_source18_hold18 as V;import review18_contract as C
D=V.D;O=E.parent;P=O/'validated/18';W=Path('/dev/shm/source18-review102-hold18-20261114');h=D.load(P/'review-handoff.json');r=D.load(P/'validated-article-record.json');raw=D.load(W/'book64-source18-raw-report.json');profile=D.load(E/'normal18-actual-final-frozen-producer-profile.json');source=Path('/dev/shm/review18-sourceQA/43644184021/archive-handoff.json');prior=D.load(source);layout=next(x for x in D.load(prior['global_approved_evidence']['video_layout_approval']['path'])['articles']if x['source_id']=='18');book=next(x for x in D.load(prior['global_approved_evidence']['book_illustrations']['path'])['illustrations']if x['source_id']=='18');actual={k:raw['output_preview_hold_validation'][v]for k,v in profile['decoder_keys'].items()}
def check(q,n='18'):return C.actual_normal_tail(q,article=n,new_id='64',expected_kind=profile['output_kind'],expected_program_sha=profile['helper']['sha256'],actual_hold=actual,layout_row=layout,book_row=book,request_json_sha256='534bfa4314daa89036fa58ef264f7868f077262788633e3692c4dbc1a7872426')
check(raw);tests=[]
for name,q,n in [('production-promotion',dict(raw,production_delivery_eligible=True),'18'),('wrong-authority',dict(raw,specific_review_authorization_sha256='0'*64),'18'),('wrong-source',raw,'17')]:
 try:check(q,n)
 except ValueError as e:tests.append(dict(case=name,rejected=True,reason=str(e)))
 else:raise AssertionError(name)
test=O/'actual18-review102-positive-and-three-required-eligibility-negatives.json';D.write(test,dict(actual_real_contract_passed=True,negatives=tests,original_physical_and_acoustic_thresholds_unchanged=True))
assert h['preview_only']is True and h['preview_delivery_eligible']is True and h['production_delivery_eligible']is False and h['active_final_replacement_authorized']is False and h['articles'][0]['passed_per_article']is False
assert r['actual_probe']['frames']==4626 and r['actual_audio_chain']['packet_count']==7106 and r['actual_audio_chain']['aac_adts_sha256']=='f3dc4bbcfee0688dc9d30551944f028d29a11230f27eed51800d6e03eb4047ce'and r['audio_repaired']is True and r['tail']['extra_body_hold_frames']==18
note=O/'historical-template-fields-and-consumer-bootstrap-observation.json';D.write(note,dict(kind='source18-consumer-template-names-only-observation',ready_template_key='all_new_current_reference_68_canonical_audio_packets_and_absolute_clock_preserved_required',template_name_not_an_audio_source=True,actual_source_id='18',actual_AAC_SHA256=r['actual_audio_chain']['aac_adts_sha256'],actual_packet_count=7106,no_source68_or54_audio_or_proof_used=True,original_first_local_import_failure_preserved=str(Path('/dev/shm/review18-hold18-first-consumer-BASE-import-failure.log')),original_second_local_adapter_filename_failure_preserved=str(Path('/dev/shm/review18-hold18-second-consumer-template-adapter-path-failure.log')),failures_occurred_before_media_validation_not_acoustic_failures=True,all_consumed_current_paths_and_nested_SHA_verified_before_handoff=True))
old=Path('/dev/shm/review69-hold18-intake/code/validate_review102_source69_hold18.py').read_text();new=(E/'validate_review102_source18_hold18.py').read_text();(E/'exact-source18-consumer-only.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='mature-review10269',tofile='actual-review10218')))
up=Path(D.load(W/'ready-book64-source18.json')['upstream_record']);extras=[up,Path(D.load(up)['inherited_actual_native_QA_record']),W/'ready-book64-source18.json',W/'review102-source18-scope-and-original-physics-tests.json',test,note,Path('/dev/shm/prepare18_hold18_consumer.py'),Path(__file__),O/'actual-consumer-preparation.json',Path('/dev/shm/review18-hold18-first-consumer-BASE-import-failure.log'),Path('/dev/shm/review18-hold18-second-consumer-template-adapter-path-failure.log')];item=h['articles'][0]['section'];known={x['path']for x in item['evidence']}
for p in extras:
 sp=V.spec(p)
 if sp['path']not in known:item['evidence'].append(sp);known.add(sp['path'])
h.update(review_only=True,review_delivery_eligible=True,user_individual_finalization_authorized=False,normal70_final_assembly_eligible=False,specific_review_authorization_id='102',original_producer_prior_deliveryV3_claim=False,current_source_fullV3_actually_bound=True,no_temporal_order_claim_between_sourceQA_and_producer_claim=True,original_native_sourceQA_handoff_unchanged=V.spec(source),actual_original_A21_fourp5_repair_passed=True,no_additional_acoustic_repair_in_tail_postprocess=True,handoff_frozen_after_final_serialization=True)
i=D.load(P/'actual-sample-input.json');i['articles']=[item];D.write(P/'actual-sample-input.json',i)
for x in h['validation_files']:
 if x['path']==str(P/'actual-sample-input.json'):x.update(V.spec(x['path']))
known={x['path']for x in h['validation_files']}
for j,p in enumerate(extras):
 sp=V.spec(p)
 if sp['path']not in known:h['validation_files'].append(dict(sp,relative_validation_path='actual-review10218-role-and-authority/'+str(j)+'-'+p.name));known.add(sp['path'])
for x in h['validation_files']:assert V.spec(x['path'])=={k:x[k]for k in ('path','bytes','sha256')}
def refs(v,trail=''):
 rows=[]
 if isinstance(v,dict):
  if all(k in v for k in ('path','bytes','sha256'))and str(v['path']).startswith('/')and not str(v['path']).lower().endswith('.pdf'):rows.append((trail,v))
  for k,x in v.items():rows+=refs(x,trail+'/'+str(k))
 elif isinstance(v,list):
  for j,x in enumerate(v):rows+=refs(x,trail+'/'+str(j))
 return rows
rows=refs(h)+refs(i)+refs(D.load(P/'report.json'))
for trail,x in rows:assert V.spec(x['path'])=={k:x[k]for k in ('path','bytes','sha256')},(trail,x['path'])
D.write(O/'recursive-final-input-section-evidence-integrity-before-freeze.json',dict(checked_references=len(rows),all_nested_absolute_file_bytes_and_SHA_exact=True,original_source_handoff=V.spec(source),old_files_and_media_unmodified=True));D.write(P/'review-handoff.json',h);print(json.dumps(dict(handoff=V.spec(P/'review-handoff.json'),record=V.spec(P/'validated-article-record.json'),final=h['articles'][0]['preview_mp4'],audio=r['actual_audio_chain'],tail=r['tail'],review_only=True,production_delivery_eligible=False,nested_refs=len(rows)),ensure_ascii=False))
