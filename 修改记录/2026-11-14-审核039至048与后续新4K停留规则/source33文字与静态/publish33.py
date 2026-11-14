"""Freeze source33 data only after actual text/static/input/semantic checks."""
from pathlib import Path
import copy,datetime,hashlib,importlib.util,json,shutil
H=Path(__file__).parent;B=H.parent;C=H/'candidate-payload';PAY=B/'payload';CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json')
IR=Path('/workspace/work/video-revision-delivery/article33-review-intake-20261114/independent-single-feedback-candidate-review.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=load('article33_diff',B/'generator_text_preflight.py');T=load('article33_layout_digest',B/'illustrated-tail/illustrated_tail.py')
text=json.loads((H/'thin-validation/report.json').read_text());static=json.loads((H/'static-render-report.json').read_text());ind=json.loads(IR.read_text());visual=json.loads((H/'actual-visual-review.json').read_text());audio=json.loads((H/'original-audio-input-invariance.json').read_text());vocab=json.loads((H/'vocabulary-table-inclusion.json').read_text())
assert text['passed']and static['passed']and ind['semantic_scope_passed']and visual['approved']and audio['passed_input_invariance']and vocab['passed']
source=C/'视频/脚本/33.json';assert sha(source)==text['source_sha256']==static['after_source_sha256']==visual['source_sha256']==audio['sources']['candidate']['source_file_sha256']==vocab['source_sha256']
assert sha(source)=='da87d68fdee3401e499aa145c23d9b2c663ce3b27f79feec5eca1ddb0d794e72'
beforepath=H/'before/视频/脚本/33.json';before=json.loads(beforepath.read_text());new=json.loads(source.read_text())
assert {k:v for k,v in before.items()if k!='sentences'}=={k:v for k,v in new.items()if k!='sentences'}
assert before['sentences'][-1]==new['sentences'][-1]
assert all(s['summary_text_font_rows_and_pixels_exact']and s['body_tail_font_and_geometry_exact']for s in static['resolutions'])
manifest_before=CI.read_bytes();approved=json.loads(manifest_before);row=next(r for r in approved['articles']if r['source_id']=='33');assert row['source_json_sha256']==sha(beforepath)==static['before_source_sha256'];assert row['source_layout_structural_sha256']==T.source_layout_digest(before)
oldrow=copy.deepcopy(row);row['source_json_sha256']=sha(source);row['source_layout_structural_sha256']=T.source_layout_digest(new);afterraw=(json.dumps(approved,ensure_ascii=False,indent=2)+'\n').encode();diff=P.differences(json.loads(manifest_before),approved);assert len(diff)==2 and all('/articles/'in d['path']for d in diff)
states=json.loads((H/'before/baseline-states.json').read_text());files=[]
for rel in ['视频/脚本/33.json','视频/工具/初稿生成/gen33.py','新版定稿/33-thirteen-in-the-cave.md','视频/制作记录/33_待改清单.md']:
 state=states[rel];dest=PAY/rel;assert dest.exists()==state['exists'],rel
 if state['exists']:assert sha(dest)==state['sha256'],rel
 files.append((C/rel,dest))
genstate=states['gen-sources/gen33.py'];gentarget=B/'gen-sources/gen33.py';assert gentarget.exists()==genstate['exists']
if gentarget.exists():assert sha(gentarget)==genstate['sha256']
files.append((C/'视频/工具/初稿生成/gen33.py',gentarget));rec='视频/制作记录/逐句确认/33.json';rec_target=PAY/rec
if rec_target.exists():
 b=H/'before/current-PAY-sentence-confirmation33.json'
 if not b.exists():shutil.copyfile(rec_target,b)
files.append((C/rec,rec_target))
auth=PAY/'视频/工具/用户同意记录.json';authbefore=auth.read_bytes();current=json.loads(authbefore);added=json.loads((H/'proposal-report.json').read_text())['auth_entries'];assert len(added)==1 and added[0]['篇']=='33'and '定稿'in added[0]['用于']
for r in added:
 if r not in current['记录']:current['记录'].append(r)
(H/'用户同意记录.actual-before.json').write_bytes(authbefore);applied=[]
for src,dest in files:
 old=sha(dest)if dest.exists()else None;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);applied.append({'path':str(dest),'before_sha256':old,'after_sha256':sha(dest),'bytes':dest.stat().st_size})
auth.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n');applied.append({'path':str(auth),'before_sha256':hashlib.sha256(authbefore).hexdigest(),'after_sha256':sha(auth),'scope':'Only exact source33 user034 final consent appended to fresh current data; all unrelated entries preserved.'})
(H/'approved-video-layouts70.before.json').write_bytes(manifest_before);CI.write_bytes(afterraw);(H/'approved-video-layouts70.after.json').write_bytes(afterraw)
r={'article':'33','book_order':'30','source_freeze_complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_JSON_sha256':sha(PAY/'视频/脚本/33.json'),'GEN_sha256':sha(PAY/'视频/工具/初稿生成/gen33.py'),'MD_sha256':sha(PAY/'新版定稿/33-thirteen-in-the-cave.md'),'GEN_sources_sha256':sha(gentarget),'GEN_sources_baseline_existed':genstate['exists'],'files_applied':applied,'exact_JSON_diff':P.differences(before,new),'original_GEN_JSON_text_checks':{'path':str(H/'thin-validation/report.json'),'sha256':sha(H/'thin-validation/report.json'),'all_passed':True,'GEN_whole_JSON_exact':True,'before_repair_exit':0,'mechanical_repair_exit':0,'after_repair_exit':0,'all_original_program_files_unchanged':True},'independent_semantic_review':{'path':str(IR),'sha256':sha(IR),'passed':True},'actual_static_1080_and_4K':{'path':str(H/'static-render-report.json'),'sha256':sha(H/'static-render-report.json'),'all_passed':True,'all_16_sentences_before_and_candidate_measured':True,'actual_changed_page_renders':2,'actual_visual_review_sha256':sha(H/'actual-visual-review.json')},'original_own_audio_input_invariance':{'path':str(H/'original-audio-input-invariance.json'),'sha256':sha(H/'original-audio-input-invariance.json'),'effective_model_input_plan_count':36,'all_input_and_DSP_equal_before_actual_candidate':True,'actual_old_native_title_and_S1_S15_31_plan_keys_exact':True,'original_prep_does_not_enumerate_four_S16_ending_speed_mothers_or_donor':True,'ending_speed_text_and_controls_preserved':True,'new_audio_quality_pass_not_claimed':True},'actual_per_article_vocabulary_table_inclusion':{'path':str(H/'vocabulary-table-inclusion.json'),'sha256':sha(H/'vocabulary-table-inclusion.json'),'divers_row_with_diver_and_chinese_exists_exactly_once':True,'original_table_preserved':True},'CI_approved_manifest':{'path':str(CI),'before_sha256':hashlib.sha256(manifest_before).hexdigest(),'after_sha256':sha(CI),'before_row':oldrow,'after_row':row,'only_two_source33_digest_leaves_changed':True,'all_other_approved_rows_preserved':True},'all_spoken_English_and_chunk_boundaries_exact':True,'all_current_DSP_CF_and_audio_controls_exact':True,'all_original_notes_and_current_five_point_summary_exact':True,'source_manuscript_missing_baseline_restored_from_actual_used_4956ee47':True,'summary_RGB_font_rows_exact':True,'no_additional_end_page_hold_for_source33':True,'official_core_or_renderer_modified':False,'new_audio_video_or_native_dispatch_by_this_agent':False,'sole_next_native_launcher':'/root/resume_audio_ci'}
p=H/'source-freeze-and-static-approval.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k in('article','source_JSON_sha256','GEN_sha256','MD_sha256')},ensure_ascii=False));print('report',sha(p));print('manifest',sha(CI))
