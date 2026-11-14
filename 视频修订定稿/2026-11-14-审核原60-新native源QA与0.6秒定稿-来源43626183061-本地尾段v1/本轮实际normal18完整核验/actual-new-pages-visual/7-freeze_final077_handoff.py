import copy,hashlib,json,pathlib
O=pathlib.Path('/dev/shm/review36-hold06-intake/validated/60');W=pathlib.Path('/dev/shm/book36-source60-production-20261114');N=pathlib.Path('/dev/shm/review36-native/43626183061/60');P=O.parent.parent

def load(p): return json.loads(pathlib.Path(p).read_text())
def write(p,x): pathlib.Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def spec(p):
 p=pathlib.Path(p).resolve();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
h=load(O/'archive-handoff.json');r=load(O/'validated-article-record.json');idxp=N/'actual-focus-frames/actual-new-focus-frames-index.json';idx=load(idxp);movie=spec(h['articles'][0]['final_mp4']['path'])
assert movie==h['articles'][0]['final_mp4'] and r['sha256']==movie['sha256'] and r['bytes']==movie['bytes'] and r['actual_probe']['frames']==4543
assert r['audio_repaired'] is True and r['actual_audio_chain']['packet_count']==6976 and r['actual_audio_chain']['aac_adts_sha256']=='4dc642494a287329c27d72973254dc11d108797c853a9073790b9cf35cc5c489'
for x in idx['frames']:
 assert spec(x['path'])['sha256']==x['sha256']
assert len(idx['frames'])==14
visual={'kind':'independent-source60-actual-native-fourteen-target-pages-and-current-final-tail-visual-review','source_id':'60','quality_book_order':'36','native_run':43626183061,'actual_native_MP4':idx['actual_native_MP4'],'actual_final_MP4':movie,'passed':True,'all_fourteen_actual_native_target_pages_viewed_in_contact':True,'contact':spec(N/'actual-focus-frames/actual-review-target-pages-contact.jpg'),'individual_native_target_images_also_viewed':[spec(N/'actual-focus-frames'/('actual-native-'+str(i).zfill(3)+'.png')) for i in (1,3,5)],'actual_native_five_boundary_images_independently_viewed':True,'current_final_body_last_independently_viewed':spec('/dev/shm/book36-source60-hold06-20261114/book36-source60/decoded-boundary-previews/60-body-last.jpg'),'other_current_final_four_boundary_images_actual_review_by_producer':spec(W/'actual-five-boundary-visual-review.json'),'observations':['全部点名重点及中英对应完整；apparent/Brazil/deflect/Royal/Revolution/Askew/law/miss、governs/ejects、looked past/after all呈现符合已批准范围，Royal Swedish保持普通。','三处新说明及用户通俗解读全文完整；末页英文主体、对应中文和三行通俗解读均居中，无越界或截字。','最后正文字体清楚、行距和左右边距均衡；0.6秒保持的是实际新正文末画面。','新增重点改变原循环palette序号，未声称旧正文颜色/RGB完全相同。原五点简述内容保留。'],'no_new_listening_or_human_acoustic_claim':True,'automatic_frame_locator_not_used_as_visual_acceptance':True,'source_media_QA_and_old_history_not_modified':True}
vp=P/'source60-independent-actual-fourteen-pages-and-final-centered-tail-review.json';write(vp,visual)
auth=spec('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-077.json');auth79=spec('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-079.json')
extras=[vp,idxp,N/'actual-focus-frames/actual-review-target-pages-contact.jpg',N/'locate_actual_review_frames.py',W/'actual-five-boundary-visual-review.json',P/'finalize077.log',P/'finalize077-schema-adapter.log',pathlib.Path(__file__),*[pathlib.Path(x['path']) for x in idx['frames']]]
item=h['articles'][0]['section'];known={x['path'] for x in item['evidence']}
for p in extras:
 s=spec(p)
 if s['path'] not in known:item['evidence'].append(s);known.add(s['path'])
h.update(current_title_zh='爱因斯坦的诺奖之路',video_title_authorization=auth,delivery_scope_authorization=auth79,delivery_scope='permanent_dual_cloud_archive_without_individual_release',actual_reviewed_new_pages_and_centered_final_tail=spec(vp),success_full_transcript_export_claimed=False,original_formal_two_ASR_routes_passed=True,first_failed_native_transcript_bundle_is_history_only=True,handoff_frozen_after_final_serialization=True)
inp=load(O/'actual-sample-input.json');inp['articles']=[item];write(O/'actual-sample-input.json',inp)
report=load(O/'report.json');report.update(actual_new_pages_and_centered_tail_visual_review=spec(vp),current_title_zh=h['current_title_zh'],video_title_authorization=auth,delivery_scope_authorization=auth79,canonical_controlled_audio_repair_applied=True,tail_postprocessing_changes_audio=False,actual_success_full_transcript_export_claimed=False,original_formal_two_ASR_routes_passed=True,original_failed_attempt_and_schema_interface_failure_logs_preserved=True);write(O/'report.json',report)
for row in h['validation_files']:
 if pathlib.Path(row['path']) in {O/'actual-sample-input.json',O/'report.json'}:row.update(spec(row['path']))
paths={x['path'] for x in h['validation_files']}
for i,p in enumerate(extras):
 s=spec(p)
 if s['path'] not in paths:h['validation_files'].append(dict(s,relative_validation_path='actual-new-pages-visual/'+str(i)+'-'+pathlib.Path(p).name));paths.add(s['path'])
for row in h['validation_files']:
 assert spec(row['path'])=={k:row[k] for k in ('path','bytes','sha256')},row['path']
assert all(x['video_sha256']==movie['sha256'] for x in item['stills'])
write(O/'archive-handoff.json',h)
print(json.dumps(dict(handoff=spec(O/'archive-handoff.json'),record=spec(O/'validated-article-record.json'),visual_review=spec(vp),actual_probe=r['actual_probe'],audio=r['actual_audio_chain'],tail=r['tail'],validation_files=len(h['validation_files'])),ensure_ascii=False))
