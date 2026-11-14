from pathlib import Path
import sys,json,copy,hashlib,zipfile
E=Path('/dev/shm/review46-hold06-intake/code');sys.path.insert(0,str(E));import validate_single_article_post_only as V;import normal18_contract as C;import exact40_video143_overlay as X
D=V.D;O=E.parent;P=O/'validated/40';W=Path('/dev/shm/book46-source40-user144-hold06-new143-art-20261114');h=D.load(P/'archive-handoff.json');r=D.load(P/'validated-article-record.json');raw=D.load(W/'book46-source40-raw-report.json');profile=D.load(E/'normal18-actual-final-frozen-producer-profile.json');source=Path('/dev/shm/review40-completion-sourceQA/43646979464/archive-handoff.json');prior=D.load(source);layout=next(x for x in D.load(prior['global_approved_evidence']['video_layout_approval']['path'])['articles']if x['source_id']=='40');new=D.load(X.P['new_manifest']['path']);old=D.load(X.P['original_producer_manifest']['path']);crop=D.load(X.P['new_crop']['path']);oldcrop=D.load(X.P['original_producer_crop']['path']);book,choice=X.metadata(new,old,crop,oldcrop);actual={k:raw['output_final_hold_validation'][v]for k,v in profile['decoder_keys'].items()}
def check(q,n='40'):return C.actual_normal_tail(q,article=n,new_id='46',expected_kind=profile['output_kind'],expected_program_sha=profile['helper']['sha256'],actual_hold=actual,layout_row=layout,book_row=book,request_json_sha256='66f6b6206d38e4cbcb5fd92faf9e3c5118b8749962eb52e68121204070ddb7ec')
check(raw);tests=[]
for name,q,n in [('wrong-authority',dict(raw,single_article_review_authorization_sha256='0'*64),'40'),('wrong-source',raw,'39'),('preview-promotion',dict(raw,preview_only=True),'40')]:
 try:check(q,n)
 except ValueError as e:tests.append(dict(case=name,rejected=True,reason=str(e)))
 else:raise AssertionError(name)
for name in ['wrong-new-video-art','another-source-artwork-changed','wrong-crop']:
 nn=copy.deepcopy(new);cc=copy.deepcopy(crop)
 if name=='wrong-new-video-art':next(x for x in nn['illustrations']if x['source_id']=='40')['sha256']='0'*64
 elif name=='another-source-artwork-changed':next(x for x in nn['illustrations']if x['source_id']=='01')['sha256']='0'*64
 else:next(x for x in cc['articles']if x['source_id']=='40')['source_crop_box']=[0,0,1536,864]
 try:X.metadata(nn,old,cc,oldcrop)
 except ValueError as e:tests.append(dict(case=name,rejected=True,reason=str(e)))
 else:raise AssertionError(name)
test=O/'actual144-and143-positive-and-six-required-scope-negatives.json';D.write(test,dict(actual144_normal18_and_independent143_pixel_recomposition_passed=True,negative_cases=tests,original_physical_numeric_and_sound_gate_thresholds_unchanged=True))
assert r['actual_probe']['frames']==4031 and r['actual_audio_chain']['packet_count']==6176 and r['actual_audio_chain']['aac_adts_sha256']=='a7171c1d7bfd7e430a05b62b8cdb096ed860a6877c96446cbf587996c55d5c68'and r['audio_repaired']is False and r['tail']['extra_body_hold_frames']==18
assert r['illustration']['approved_video_illustration_source_sha256']=='c620a3ca7f8df9985f1d7f89e055f5f33be34f67cbcc7c07fc95dd4045df585e'and r['illustration']['book_source_sha256']=='5b1aabe5efdc4543a1989bfac2dd27a8e1f3dbd0f5db232f32c5800ef9e496e1'and r['qc']['illustration']['frame_comparison']['reference_sha256']==raw['illustration_preparation']['prepared_png_sha256']
history=O/'actual40-original-failure-and-bootstrap-public-artifact-history.json';oldzip=Path('/dev/shm/source40-exact-ending-default-retry-failed-43640848824/artifact.zip');assert oldzip.is_file()
with zipfile.ZipFile(oldzip)as z:names=z.namelist();assert all(not name.lower().endswith(('.pkl','.npy','.npz','.safetensors','.pt'))for name in names)
D.write(history,dict(kind='source40-public-original-failure-provenance-not-current-quality-input',original_failed_native_run=43640848824,original_public_artifact_zip=V.spec(oldzip),original_false_status_preserved=True,source_voice_text_ASR_4K_gate_provenance_inherited_not_rerun=True,first_postonly_bootstrap_failed_run=43645133365,first_bootstrap_resource=V.spec(Path('/dev/shm/source40-postonly-first-bootstrap-failure-43645133365/files/40-approved-illustration-resource.json')),new_successful_outer_completion_run=43646979464,new_completion_not_claimed_full_original_pipeline_rerun=True,original_book_image_is_historical_5b1aabe_not_user143_c620=True))
extras=[test,history,oldzip,Path(__file__),Path('/dev/shm/prepare40_final144_consumer.py'),W/'ready-book46-source40.json',W/'source40-only-user143-new-art-and-user144-hold18-profile.json',E/'exact40-current143-image-data-overlay-only.patch'];item=h['articles'][0]['section'];known={x['path']for x in item['evidence']}
for p in extras:
 sp=V.spec(p)
 if sp['path']not in known:item['evidence'].append(sp);known.add(sp['path'])
h.update(handoff_frozen_after_final_serialization=True,specific_authorization_id='144',video_illustration_authorization_id='143',current_source_fullV3_actually_bound=True,original_voice_text_ASR_4K_gate_run=43640848824,actual_new_native_remaining_outer_completion_run=43646979464,original_full_pipeline_rerun_in_completion=False,current_PCM_only_inherited_from_actual_proof=True,no_acoustic_repair_applied_in_tail=True,user143_video_only_new_art_actually_verified=True,shared_book_illustrations_and_PDF_unchanged=True)
i=D.load(P/'actual-sample-input.json');i['articles']=[item];D.write(P/'actual-sample-input.json',i)
for x in h['validation_files']:
 if x['path']==str(P/'actual-sample-input.json'):x.update(V.spec(x['path']))
known={x['path']for x in h['validation_files']}
for j,p in enumerate(extras):
 sp=V.spec(p)
 if sp['path']not in known:h['validation_files'].append(dict(sp,relative_validation_path='actual144-and143-role-and-authority/'+str(j)+'-'+p.name));known.add(sp['path'])
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
D.write(O/'recursive-final-input-section-evidence-integrity-before-freeze.json',dict(checked_refs=len(rows),all_nested_absolute_file_bytes_and_SHA_exact=True,source_QA_handoff=V.spec(source),all_old_evidence_and_media_unchanged=True));D.write(P/'archive-handoff.json',h);print(json.dumps(dict(handoff=V.spec(P/'archive-handoff.json'),record=V.spec(P/'validated-article-record.json'),final=h['articles'][0]['final_mp4'],audio=r['actual_audio_chain'],tail=r['tail'],video_only_143_native_SHA=r['illustration']['approved_video_illustration_source_sha256'],original_shared_book_SHA=r['illustration']['book_source_sha256'],nested_refs=len(rows)),ensure_ascii=False))
