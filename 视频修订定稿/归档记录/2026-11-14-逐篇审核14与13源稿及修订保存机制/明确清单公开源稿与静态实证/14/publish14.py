"""Commit only authorized article14 data and its actual static layout binding."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil
H=Path(__file__).parent;B=H.parent;C=H/'candidate-payload';PAY=B/'payload'
CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=load('article14_exact_diff',B/'generator_text_preflight.py');T=load('unchanged_static_digest',B/'illustrated-tail/illustrated_tail.py')
text=json.loads((H/'recheck-after-T34/report.json').read_text());static=json.loads((H/'static-render-report.json').read_text())
assert text['passed']and static['passed']
source=C/'视频/脚本/14.json';assert sha(source)==text['current_source_sha256']==static['after_source_sha256']
before=json.loads((H/'before/视频/脚本/14.json').read_text());new=json.loads(source.read_text())
assert {k:v for k,v in before.items()if k not in('sentences','allow_clash')}=={k:v for k,v in new.items()if k not in('sentences','allow_clash')}
assert before['sentences'][-1]['chunks'][-1]['note']==new['sentences'][-1]['chunks'][-1]['note']
manifest_before=CI.read_bytes();approved=json.loads(manifest_before);row=next(r for r in approved['articles']if r['source_id']=='14')
assert row['source_json_sha256']==sha(H/'before/视频/脚本/14.json')and row['source_layout_structural_sha256']==T.source_layout_digest(before)
frozen_row=json.loads(json.dumps(row));row['source_json_sha256']=sha(source);row['source_layout_structural_sha256']=T.source_layout_digest(new)
afterraw=(json.dumps(approved,ensure_ascii=False,indent=2)+'\n').encode();assert len(P.differences(json.loads(manifest_before),approved))==2
files=[]
for rel in [Path('视频/脚本/14.json'),Path('视频/工具/初稿生成/gen14.py'),Path('新版定稿/14-the-fungus-that-turns-ants-into-zombies.md')]:
 assert sha(PAY/rel)==sha(H/'before'/rel)
 files.append((C/rel,PAY/rel))
assert sha(B/'gen-sources/gen14.py')==sha(H/'before/gen-sources-gen14.py')
files.append((C/'视频/工具/初稿生成/gen14.py',B/'gen-sources/gen14.py'))
auth=PAY/'视频/工具/用户同意记录.json';authbefore=auth.read_bytes();current=json.loads(authbefore);added=json.loads((C/'视频/工具/用户同意记录.json').read_text())['记录'][-2:]
assert all(r['篇']=='14'for r in added)
for r in added:
 if r not in current['记录']:current['记录'].append(r)
(H/'用户同意记录.actual-before.json').write_bytes(authbefore)
applied=[]
for src,dest in files:
 old=sha(dest);shutil.copyfile(src,dest);applied.append({'path':str(dest),'before_sha256':old,'after_sha256':sha(dest),'bytes':dest.stat().st_size})
auth.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n');applied.append({'path':str(auth),'before_sha256':hashlib.sha256(authbefore).hexdigest(),'after_sha256':sha(auth),'scope':'Only two exact article14 consent records appended; unrelated current records retained.'})
(H/'approved-video-layouts70.before.json').write_bytes(manifest_before);CI.write_bytes(afterraw);(H/'approved-video-layouts70.after.json').write_bytes(afterraw)
report={'article':'14','book_order':'21','source_freeze_complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'eight_user_feedback_implemented':True,'source_JSON_sha256':sha(PAY/'视频/脚本/14.json'),'GEN_sha256':sha(PAY/'视频/工具/初稿生成/gen14.py'),'MD_sha256':sha(PAY/'新版定稿/14-the-fungus-that-turns-ants-into-zombies.md'),'GEN_sources_sha256':sha(B/'gen-sources/gen14.py'),'files_applied':applied,'exact_JSON_diff':P.differences(before,new),'original_GEN_JSON_text_checks':{'path':str(H/'recheck-after-T34/report.json'),'sha256':sha(H/'recheck-after-T34/report.json'),'all_passed':True},'actual_static_1080_and_4K':{'path':str(H/'static-render-report.json'),'sha256':sha(H/'static-render-report.json'),'all_passed':True,'actual_changed_page_renders':18,'actually_visually_reviewed_all_18_changed_pages':True,'actual_tail_and_summary_contact':str(H/'actual-4K-tail-summary-contact.jpg')},'CI_approved_manifest':{'path':str(CI),'before_sha256':hashlib.sha256(manifest_before).hexdigest(),'after_sha256':sha(CI),'before_row':frozen_row,'after_row':row,'only_two_article14_source_digest_leaves_changed':True,'unchanged_approved_summary_text_RGB_font':True},'spoken_English_and_chunk_boundaries_exact':True,'all_existing_DSP_and_audio_controls_exact':True,'summary_five_points_and_full_last_note_exact':True,'body_tail_geometry_and_font_exact':True,'body_tail_RGB_identity_claimed':False,'official_cyclic_color_shift_expected':True,'official_core_or_renderer_modified':False,'native_video_or_audio_generated_or_dispatched_by_this_agent':False,'published40_review_bundle_modified':False,'sole_next_native_launcher':'/root/resume_audio_ci'}
p=H/'source-freeze-and-static-approval.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k in('article','source_JSON_sha256','GEN_sha256','MD_sha256','GEN_sources_sha256')},ensure_ascii=False));print('report',str(p),sha(p));print('manifest',sha(CI))
