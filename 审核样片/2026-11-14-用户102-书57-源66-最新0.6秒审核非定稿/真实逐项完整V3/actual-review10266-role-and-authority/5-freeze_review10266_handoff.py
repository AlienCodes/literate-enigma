from pathlib import Path
import copy,hashlib,json,sys
O=Path(__file__).parent;E=O/'code';W=Path('/dev/shm/source66-review102-hold18-20261114');V=O/'validated/66';sys.path.insert(0,str(E));import review18_contract as C
sys.path.insert(0,'/dev/shm/native-inline-engine-review66-v23-actual102-layout');import delivery as D

def spec(p):p=Path(p).resolve();return dict(path=str(p),bytes=p.stat().st_size,sha256=D.digest(p))
def write(p,x):D.write(p,x)
h=D.load(V/'review-handoff.json');r=D.load(V/'validated-article-record.json');raw=D.load(W/'book57-source66-raw-report.json');profile=D.load(E/'normal18-actual-final-frozen-producer-profile.json');prior=D.load('/dev/shm/review66-sourceQA/43629880764/archive-handoff.json');layout=next(x for x in D.load(prior['global_approved_evidence']['video_layout_approval']['path'])['articles']if x['source_id']=='66');book=next(x for x in D.load(prior['global_approved_evidence']['book_illustrations']['path'])['illustrations']if x['source_id']=='66');normalized={k:raw['output_preview_hold_validation'][v]for k,v in profile['decoder_keys'].items()}
def check(raw,article='66'):
 return C.actual_normal_tail(raw,article=article,new_id='57',expected_kind=profile['output_kind'],expected_program_sha=profile['helper']['sha256'],actual_hold=normalized,layout_row=layout,book_row=book,request_json_sha256='7678088cd5f548afa618f9606494462e0d9d597c53019ce99acac4a9e09ddda7')
g=check(raw);tests=[]
for name,changed,n in [('production_promotion',dict(raw,production_delivery_eligible=True),'66'),('wrong_authority',dict(raw,specific_review_authorization_sha256='0'*64),'66'),('wrong_article',raw,'65')]:
 try:check(changed,n)
 except ValueError as e:tests.append(dict(case=name,rejected=True,reason=str(e)))
 else:raise AssertionError(name)
t=O/'actual-review10266-positive-and-three-required-eligibility-negatives.json';write(t,dict(actual_real_contract_passed=True,negatives=tests,original_physical_thresholds_and_media_not_changed=True))
up=Path(D.load(W/'ready-book57-source66.json')['upstream_record']);ap=up.with_name('66-review18-upstream-with-actual-source-V3-reference.json');a=D.load(ap);a.pop('source_validation_completed_after_producer_inheritance_claim',None);a.update(original_producer_prior_full_delivery_V3_claim_false_preserved=True,actual_source_fullV3_handoff_bound_without_chronology_claim=True);write(ap,a)
p=Path('/dev/shm/prepare_review66_hold18_consumer.py');text=p.read_text().replace('source_validation_completed_after_producer_inheritance_claim=True','actual_source_fullV3_handoff_bound_without_chronology_claim=True');p.write_text(text)
assert h['preview_only']is True and h['preview_delivery_eligible']is True and h['production_delivery_eligible']is False and h['active_final_replacement_authorized']is False and h['articles'][0]['passed_per_article']is False and h['articles'][0]['preview_passed']is True
assert r['id']=='66' and r['new_id']=='57' and r['preview_only']is True and r['production_delivery_eligible']is False and r['actual_probe']['frames']==3984 and r['actual_audio_chain']['packet_count']==6101 and r['tail']['extra_body_hold_frames']==18
extras=[up,Path(D.load(up)['inherited_actual_native_QA_record']),W/'ready-book57-source66.json',t,p,Path(__file__),O/'actual-consumer-preparation.json'];item=h['articles'][0]['section'];known={x['path']for x in item['evidence']}
for p in extras:
 s=spec(p)
 if s['path']not in known:item['evidence'].append(s);known.add(s['path'])
h.update(review_only=True,review_delivery_eligible=True,user_individual_finalization_authorized=False,normal70_final_assembly_eligible=False,specific_review_authorization_id='102',original_producer_prior_deliveryV3_claim=False,current_source_fullV3_actually_bound=True,no_temporal_order_claim_between_sourceQA_and_producer_claim=True,original_native_inline_sourceQA_handoff_unchanged=spec('/dev/shm/review66-sourceQA/43629880764/archive-handoff.json'),handoff_frozen_after_final_serialization=True)
inp=D.load(V/'actual-sample-input.json');inp['articles']=[item];write(V/'actual-sample-input.json',inp);rep=D.load(V/'report.json');rep.update(review_only=True,user_individual_finalization_authorized=False,original_raw_producer_inheritance_record=spec(up),original_raw_claim_prior_full_deliveryV3=False,source_QA_actual_binding_without_chronology_claim=True);write(V/'report.json',rep)
refresh={str(ap),str(V/'actual-sample-input.json'),str(V/'report.json')}
for row in h['validation_files']:
 if row['path']in refresh:row.update(spec(row['path']))
known={x['path']for x in h['validation_files']}
for i,p in enumerate(extras):
 s=spec(p)
 if s['path']not in known:h['validation_files'].append(dict(s,relative_validation_path='actual-review10266-role-and-authority/'+str(i)+'-'+p.name));known.add(s['path'])
for row in h['validation_files']:assert spec(row['path'])=={k:row[k]for k in ('path','bytes','sha256')},row['path']
assert all(x['video_sha256']==r['sha256']for x in item['stills']);write(V/'review-handoff.json',h);print(json.dumps(dict(handoff=spec(V/'review-handoff.json'),record=spec(V/'validated-article-record.json'),actual_probe=r['actual_probe'],audio=r['actual_audio_chain'],tail=r['tail'],review_only=h['review_only'],production_delivery_eligible=h['production_delivery_eligible']),ensure_ascii=False))
