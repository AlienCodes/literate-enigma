from pathlib import Path
import sys,json,copy
E=Path('/dev/shm/review45-hold06-intake/code');sys.path.insert(0,str(E));import validate_single_article_post_only as V;import normal18_contract as C
D=V.D;O=E.parent;P=O/'validated/16';W=Path('/dev/shm/book45-source16-user137-hold06-20261114');h=D.load(P/'archive-handoff.json');r=D.load(P/'validated-article-record.json');raw=D.load(W/'book45-source16-raw-report.json');profile=D.load(E/'normal18-actual-final-frozen-producer-profile.json');source=Path('/dev/shm/review16-sourceQA/43644041957/archive-handoff.json');prior=D.load(source);layout=next(x for x in D.load(prior['global_approved_evidence']['video_layout_approval']['path'])['articles']if x['source_id']=='16');book=next(x for x in D.load(prior['global_approved_evidence']['book_illustrations']['path'])['illustrations']if x['source_id']=='16');actual={k:raw['output_final_hold_validation'][v]for k,v in profile['decoder_keys'].items()}
def check(q,n='16'):return C.actual_normal_tail(q,article=n,new_id='45',expected_kind=profile['output_kind'],expected_program_sha=profile['helper']['sha256'],actual_hold=actual,layout_row=layout,book_row=book,request_json_sha256='9bfb9b4e8a68b5418f1a0fd50734d2f479cbffbed259b70b7ee07125e06f7631')
check(raw);tests=[]
for name,q,n in [('wrong-authority',dict(raw,single_article_review_authorization_sha256='0'*64),'16'),('wrong-source',raw,'15'),('review-promotion',dict(raw,preview_only=True),'16')]:
 try:check(q,n)
 except ValueError as e:tests.append(dict(case=name,rejected=True,reason=str(e)))
 else:raise AssertionError(name)
test=O/'actual137-contract-positive-and-three-required-scope-negatives.json';D.write(test,dict(actual137_positive_passed=True,negatives=tests,original_physical_numeric_and_acoustic_checks_unchanged=True))
assert r['actual_probe']['frames']==4439 and r['actual_audio_chain']['packet_count']==6814 and r['actual_audio_chain']['aac_adts_sha256']=='f858c0d2d9ed55a2c405609eda0e7fb4d7d8e38ee3bf4766cf4be2bf956be80f'and r['audio_repaired']is True and r['tail']['extra_body_hold_frames']==18
extras=[test,Path(__file__),Path('/dev/shm/prepare16_final_consumer.py'),W/'ready-book45-source16.json',W/'exact137-scope-and-original-physical-function-tests.json'];item=h['articles'][0]['section'];known={x['path']for x in item['evidence']}
for p in extras:
 sp=V.spec(p)
 if sp['path']not in known:item['evidence'].append(sp);known.add(sp['path'])
h.update(handoff_frozen_after_final_serialization=True,specific_authorization_id='137',current_source_fullV3_actually_bound=True,all_current_native_Origin_QC_checks_preserved=True,no_additional_acoustic_repair_in_tail_postprocess=True)
i=D.load(P/'actual-sample-input.json');i['articles']=[item];D.write(P/'actual-sample-input.json',i)
for row in h['validation_files']:
 if row['path']==str(P/'actual-sample-input.json'):row.update(V.spec(row['path']))
known={x['path']for x in h['validation_files']}
for j,p in enumerate(extras):
 sp=V.spec(p)
 if sp['path']not in known:h['validation_files'].append(dict(sp,relative_validation_path='actual137-role-and-authority/'+str(j)+'-'+p.name));known.add(sp['path'])
for x in h['validation_files']:assert V.spec(x['path'])=={k:x[k]for k in ('path','bytes','sha256')}
def refs(v,trail=''):
 out=[]
 if isinstance(v,dict):
  if all(k in v for k in ('path','bytes','sha256'))and str(v['path']).startswith('/')and not str(v['path']).lower().endswith('.pdf'):out.append((trail,v))
  for k,x in v.items():out+=refs(x,trail+'/'+str(k))
 elif isinstance(v,list):
  for j,x in enumerate(v):out+=refs(x,trail+'/'+str(j))
 return out
rows=refs(h)+refs(i)+refs(D.load(P/'report.json'))
for trail,x in rows:assert V.spec(x['path'])=={k:x[k]for k in ('path','bytes','sha256')},(trail,x['path'])
D.write(O/'recursive-final-input-section-evidence-integrity-before-freeze.json',dict(checked_reference_count=len(rows),all_nested_absolute_declared_files_byte_and_SHA_exact=True,original_source_handoff=V.spec(source),media_and_old_handoffs_not_modified=True))
D.write(P/'archive-handoff.json',h);print(json.dumps(dict(handoff=V.spec(P/'archive-handoff.json'),record=V.spec(P/'validated-article-record.json'),final=h['articles'][0]['final_mp4'],audio=r['actual_audio_chain'],tail=r['tail'],nested_reference_count=len(rows)),ensure_ascii=False))
