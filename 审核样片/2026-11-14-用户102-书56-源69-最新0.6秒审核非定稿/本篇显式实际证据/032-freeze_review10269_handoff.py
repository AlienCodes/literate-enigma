from pathlib import Path
import copy,json,sys
O=Path(__file__).parent;E=O/'code';W=Path('/dev/shm/source69-review102-hold18-20261114');V=O/'validated/69';sys.path.insert(0,str(E));import review18_contract as C
sys.path.insert(0,'/dev/shm/native-inline-engine-review69-v25-actual102-layout');import delivery as D

def spec(p):p=Path(p).resolve();return dict(path=str(p),bytes=p.stat().st_size,sha256=D.digest(p))
h=D.load(V/'review-handoff.json');r=D.load(V/'validated-article-record.json');raw=D.load(W/'book56-source69-raw-report.json');profile=D.load(E/'normal18-actual-final-frozen-producer-profile.json');source=Path('/dev/shm/review69-sourceQA/43633739728/archive-handoff.json');prior=D.load(source);layout=next(x for x in D.load(prior['global_approved_evidence']['video_layout_approval']['path'])['articles']if x['source_id']=='69');book=next(x for x in D.load(prior['global_approved_evidence']['book_illustrations']['path'])['illustrations']if x['source_id']=='69');normalized={k:raw['output_preview_hold_validation'][v]for k,v in profile['decoder_keys'].items()}
def check(q,article='69'):
 return C.actual_normal_tail(q,article=article,new_id='56',expected_kind=profile['output_kind'],expected_program_sha=profile['helper']['sha256'],actual_hold=normalized,layout_row=layout,book_row=book,request_json_sha256='64fa9930086fd21f78556265b724344ea85a891ff5992ddfe3bbdd6ef2f91f67')
g=check(raw);tests=[]
for name,changed,n in [('production_promotion',dict(raw,production_delivery_eligible=True),'69'),('wrong_authority',dict(raw,specific_review_authorization_sha256='0'*64),'69'),('wrong_article',raw,'65')]:
 try:check(changed,n)
 except ValueError as e:tests.append(dict(case=name,rejected=True,reason=str(e)))
 else:raise AssertionError(name)
t=O/'actual-review10269-positive-and-three-required-eligibility-negatives.json';D.write(t,dict(actual_real_contract_passed=True,negatives=tests,original_physical_thresholds_and_media_not_changed=True))
up=Path(D.load(W/'ready-book56-source69.json')['upstream_record']);ap=up.with_name('69-review18-upstream-with-actual-source-V3-reference.json')
assert h['preview_only']is True and h['preview_delivery_eligible']is True and h['production_delivery_eligible']is False and h['active_final_replacement_authorized']is False and h['articles'][0]['passed_per_article']is False and h['articles'][0]['preview_passed']is True
assert r['id']=='69' and r['new_id']=='56' and r['preview_only']is True and r['production_delivery_eligible']is False and r['actual_probe']['frames']==4939 and r['actual_audio_chain']['packet_count']==7595 and r['tail']['extra_body_hold_frames']==18
extras=[up,Path(D.load(up)['inherited_actual_native_QA_record']),W/'ready-book56-source69.json',t,Path('/dev/shm/prepare_review69_hold18_consumer.py'),Path(__file__),O/'actual-consumer-preparation.json'];item=h['articles'][0]['section'];known={x['path']for x in item['evidence']}
for p in extras:
 s=spec(p)
 if s['path']not in known:item['evidence'].append(s);known.add(s['path'])
h.update(review_only=True,review_delivery_eligible=True,user_individual_finalization_authorized=False,normal70_final_assembly_eligible=False,specific_review_authorization_id='102',original_producer_prior_deliveryV3_claim=False,current_source_fullV3_actually_bound=True,no_temporal_order_claim_between_sourceQA_and_producer_claim=True,original_native_inline_sourceQA_handoff_unchanged=spec(source),handoff_frozen_after_final_serialization=True)
inp=D.load(V/'actual-sample-input.json');inp['articles']=[item];D.write(V/'actual-sample-input.json',inp);rep=D.load(V/'report.json');rep.update(review_only=True,user_individual_finalization_authorized=False,original_raw_producer_inheritance_record=spec(up),original_raw_claim_prior_full_deliveryV3=False,source_QA_actual_binding_without_chronology_claim=True);D.write(V/'report.json',rep)
for row in h['validation_files']:
 if row['path']in {str(V/'actual-sample-input.json'),str(V/'report.json')}:row.update(spec(row['path']))
known={x['path']for x in h['validation_files']}
for i,p in enumerate(extras):
 s=spec(p)
 if s['path']not in known:h['validation_files'].append(dict(s,relative_validation_path='actual-review10269-role-and-authority/'+str(i)+'-'+p.name));known.add(s['path'])
for row in h['validation_files']:assert spec(row['path'])=={k:row[k]for k in ('path','bytes','sha256')},row['path']
assert all(x['video_sha256']==r['sha256']for x in item['stills']);D.write(V/'review-handoff.json',h);print(json.dumps(dict(handoff=spec(V/'review-handoff.json'),record=spec(V/'validated-article-record.json'),actual_probe=r['actual_probe'],audio=r['actual_audio_chain'],tail=r['tail'],review_only=h['review_only'],production_delivery_eligible=h['production_delivery_eligible']),ensure_ascii=False))
