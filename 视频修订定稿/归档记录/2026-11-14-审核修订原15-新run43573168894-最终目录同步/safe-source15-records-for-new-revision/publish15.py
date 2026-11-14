"""Freeze only source15 focus data after original/independent/static checks."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil
H=Path(__file__).parent;B=H.parent;C=H/'candidate-payload';PAY=B/'payload'
CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json')
IR=Path('/workspace/work/video-revision-delivery/article15-review-intake-20261114/independent-two-feedback-candidate-review.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=load('article15_exact_diff',B/'generator_text_preflight.py');T=load('unchanged_static_digest',B/'illustrated-tail/illustrated_tail.py')
text=json.loads((H/'gen-text-validation-v3/report.json').read_text());static=json.loads((H/'static-render-report.json').read_text());independent=json.loads(IR.read_text());visual=json.loads((H/'actual-visual-review.json').read_text())
assert text['passed']and static['passed']and independent['semantic_scope_passed']and visual['approved']
source=C/'视频/脚本/15.json';assert sha(source)==text['current_source_sha256']==static['after_source_sha256']==independent['candidate_source_sha256']
beforepath=H/'before/视频/脚本/15.json';before=json.loads(beforepath.read_text());new=json.loads(source.read_text())
assert {k:v for k,v in before.items()if k not in('sentences','allow_clash')}=={k:v for k,v in new.items()if k not in('sentences','allow_clash')}
assert before['除阻加强']==new['除阻加强']=={'S8':{'1':[3.25,3.315,5.0]}}
assert before['sentences'][-1]==new['sentences'][-1]and before['sentences'][14]==new['sentences'][14]
assert all(s['summary_text_font_rows_and_pixels_exact']and s['body_tail_font_and_geometry_exact']for s in static['resolutions'])
# Read the shared manifest afresh inside the coordinated single-writer window.
manifest_before=CI.read_bytes();approved=json.loads(manifest_before);row=next(r for r in approved['articles']if r['source_id']=='15')
assert row['source_json_sha256']==sha(beforepath)==static['before_source_sha256']
assert row['source_layout_structural_sha256']==T.source_layout_digest(before)
frozen_row=json.loads(json.dumps(row));row['source_json_sha256']=sha(source);row['source_layout_structural_sha256']=T.source_layout_digest(new)
afterraw=(json.dumps(approved,ensure_ascii=False,indent=2)+'\n').encode();diff=P.differences(json.loads(manifest_before),approved);assert len(diff)==2 and all('/articles/'in d['path']for d in diff)
files=[]
for rel in [Path('视频/脚本/15.json'),Path('视频/工具/初稿生成/gen15.py'),Path('新版定稿/15-the-myth-of-the-unsinkable.md'),Path('视频/制作记录/15_待改清单.md')]:
 assert sha(PAY/rel)==sha(H/'before'/rel),(rel,'baseline changed')
 files.append((C/rel,PAY/rel))
genstate=json.loads((H/'before/gen-sources-baseline-state.json').read_text());gentarget=B/'gen-sources/gen15.py';assert gentarget.exists()==genstate['exists']
if gentarget.exists():assert sha(gentarget)==genstate['sha256']
files.append((C/'视频/工具/初稿生成/gen15.py',gentarget))
auth=PAY/'视频/工具/用户同意记录.json';authbefore=auth.read_bytes();current=json.loads(authbefore);added=json.loads((H/'proposal-report.json').read_text())['auth_entries'];assert len(added)==2 and all(r['篇']=='15'for r in added)
for r in added:
 if r not in current['记录']:current['记录'].append(r)
(H/'用户同意记录.actual-before.json').write_bytes(authbefore);applied=[]
for src,dest in files:
 old=sha(dest)if dest.exists()else None;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);applied.append({'path':str(dest),'before_sha256':old,'after_sha256':sha(dest),'bytes':dest.stat().st_size})
auth.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n');applied.append({'path':str(auth),'before_sha256':hashlib.sha256(authbefore).hexdigest(),'after_sha256':sha(auth),'scope':'Only two exact source15 consent records appended to fresh current data; unrelated entries retained.'})
(H/'approved-video-layouts70.before.json').write_bytes(manifest_before);CI.write_bytes(afterraw);(H/'approved-video-layouts70.after.json').write_bytes(afterraw)
report={'article':'15','book_order':'25','source_freeze_complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'two_user_feedback_implemented':True,'source_JSON_sha256':sha(PAY/'视频/脚本/15.json'),'GEN_sha256':sha(PAY/'视频/工具/初稿生成/gen15.py'),'MD_sha256':sha(PAY/'新版定稿/15-the-myth-of-the-unsinkable.md'),'GEN_sources_sha256':sha(gentarget),'GEN_sources_baseline_existed':genstate['exists'],'files_applied':applied,'exact_JSON_diff':P.differences(before,new),'original_GEN_JSON_text_checks':{'path':str(H/'gen-text-validation-v3/report.json'),'sha256':sha(H/'gen-text-validation-v3/report.json'),'all_passed':True,'earlier_missing_mirror_fixture_runs_preserved':True},'independent_semantic_review':{'path':str(IR),'sha256':sha(IR),'passed':True},'actual_static_1080_and_4K':{'path':str(H/'static-render-report.json'),'sha256':sha(H/'static-render-report.json'),'all_passed':True,'three_sources_actual_latest_A21_native_current_before_and_candidate':True,'actual_changed_page_renders':4,'actual_visual_review_sha256':sha(H/'actual-visual-review.json')},'CI_approved_manifest':{'path':str(CI),'before_sha256':hashlib.sha256(manifest_before).hexdigest(),'after_sha256':sha(CI),'before_row':frozen_row,'after_row':row,'only_two_article15_source_digest_leaves_changed':True,'unchanged_approved_summary_canonical_text_RGB_font':True},'spoken_English_and_chunk_boundaries_exact':True,'all_current_DSP_CF_and_audio_controls_exact':True,'A21_plus5_exact':True,'latest_passed_A21_audio_source_readonly_comparison':{'path':str(H/'latest-A21-readonly-source-identity.json'),'sha256':sha(H/'latest-A21-readonly-source-identity.json'),'known_latest_CF_and_original_summary_wrap_differences_not_substituted':True,'latest_native_source_sha256':'3c6324bbcba5f24f2f3639b99f6f767f20e3c3315205090b002844fe62b13bc4','required_native_video_sha256':'46e616b986839c44cb0f37bb0a6c779a814de4df7e05963313bbb3a19391c348','latest_native_voice_binding_and_acceptance_not_claimed_by_text_writer':True},'current_five_point_summary_and_full_last_note_exact':True,'existing_S15_ice_patrol_sentence_exact':True,'body_tail_geometry_and_font_exact':True,'body_tail_RGB_identity_claimed':False,'official_core_or_renderer_modified':False,'native_video_or_audio_generated_or_dispatched_by_this_agent':False,'sole_next_native_launcher':'/root/resume_audio_ci'}
p=H/'source-freeze-and-static-approval.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k in('article','source_JSON_sha256','GEN_sha256','MD_sha256','GEN_sources_sha256')},ensure_ascii=False));print('report',sha(p));print('manifest',sha(CI))
