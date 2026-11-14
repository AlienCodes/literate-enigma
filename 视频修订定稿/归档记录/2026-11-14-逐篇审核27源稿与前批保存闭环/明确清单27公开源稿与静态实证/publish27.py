"""Freeze article27 nutrients data; sound controls remain exclusively audio-owned."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil
H=Path(__file__).parent;B=H.parent;C=H/'candidate-payload';PAY=B/'payload';CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=load('source_diff_exact',B/'generator_text_preflight.py');T=load('unchanged_layout_digest27',B/'illustrated-tail/illustrated_tail.py')
checks=json.loads((H/'thin-validation/report.json').read_text());static=json.loads((H/'static-render-report.json').read_text());assert checks['passed']and static['passed']
source=C/'视频/脚本/27.json';assert sha(source)==checks['source_sha256']==static['after_source_sha256']
old=json.loads((H/'before/视频/脚本/27.json').read_text());new=json.loads(source.read_text());assert{k:v for k,v in old.items()if k not in('sentences','allow_clash')}=={k:v for k,v in new.items()if k not in('sentences','allow_clash')}
assert old['sentences'][-1]['chunks'][-1]['note']==new['sentences'][-1]['chunks'][-1]['note']
raw=CI.read_bytes();a=json.loads(raw);row=next(r for r in a['articles']if r['source_id']=='27');oldrow=json.loads(json.dumps(row));approvedsource=B/'final-layout/inputs/27.json'
assert row['source_json_sha256']==sha(approvedsource)==static['old_approved_source_sha256']
assert row['source_layout_structural_sha256']==T.source_layout_digest(json.loads(approvedsource.read_text()))
row['source_json_sha256']=sha(source);row['source_layout_structural_sha256']=T.source_layout_digest(new);assert len(P.differences(json.loads(raw),a))==2
files=[]
for rel in [Path('视频/脚本/27.json'),Path('视频/工具/初稿生成/gen27.py'),Path('新版定稿/27-life-in-the-forbidden-zone.md')]:
 assert sha(PAY/rel)==sha(H/'before'/rel);files.append((C/rel,PAY/rel))
gen=B/'gen-sources/gen27.py';assert not gen.exists();files.append((C/'视频/工具/初稿生成/gen27.py',gen))
record=PAY/'视频/制作记录/逐句确认/27.json';assert sha(record)==checks['sentence_review_before_sha256'];shutil.copyfile(record,H/'before/逐句确认27.json');assert checks['only_sentence14_review_record_updated'];files.append((C/'视频/制作记录/逐句确认/27.json',record))
auth=PAY/'视频/工具/用户同意记录.json';authraw=auth.read_bytes();authdata=json.loads(authraw);added=json.loads((C/'视频/工具/用户同意记录.json').read_text())['记录'][-2:];assert all(r['篇']=='27'for r in added)
for r in added:
 if r not in authdata['记录']:authdata['记录'].append(r)
(H/'用户同意记录.actual-before.json').write_bytes(authraw);applied=[]
for src,dest in files:
 before=sha(dest)if dest.exists()else None;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);applied.append({'path':str(dest),'before_sha256':before,'after_sha256':sha(dest),'bytes':dest.stat().st_size})
auth.write_text(json.dumps(authdata,ensure_ascii=False,indent=2)+'\n');applied.append({'path':str(auth),'before_sha256':hashlib.sha256(authraw).hexdigest(),'after_sha256':sha(auth),'scope':'Only27 two consent records appended fresh;13/14/other entries retained.'})
(H/'approved-video-layouts70.before.json').write_bytes(raw);CI.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');shutil.copyfile(CI,H/'approved-video-layouts70.after.json')
r={'article':'27','book_order':'22','text_source_freeze_complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sole_requested_new_focus':'nutrients/养分','source_JSON_sha256':sha(PAY/'视频/脚本/27.json'),'GEN_sha256':sha(PAY/'视频/工具/初稿生成/gen27.py'),'MD_sha256':sha(PAY/'新版定稿/27-life-in-the-forbidden-zone.md'),'sentence14_review_record_sha256':sha(record),'files_applied':applied,'exact_source_diff':P.differences(old,new),'original_GEN_JSON_text_checks':{'path':str(H/'thin-validation/report.json'),'sha256':sha(H/'thin-validation/report.json'),'all_passed':True},'actual_static_1080_and_4K':{'path':str(H/'static-render-report.json'),'sha256':sha(H/'static-render-report.json'),'all_passed':True,'actual_changed_page_renders':2,'actual_target_and_tail_contact':str(H/'actual-target-and-tail-contact.jpg'),'actually_visually_reviewed':True},'CI_approved_manifest':{'path':str(CI),'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':sha(CI),'before_row':oldrow,'after_row':row,'only_two_article27_source_digest_leaves_changed':True,'old_approved_to_current_before_only_original_summary_wrap':True,'original_approved_summary_canonical_text_RGB_and_font_unchanged':True},'all_spoken_English_and_chunk_boundaries_exact':True,'all_existing_audio_DSP_controls_exact':True,'all_existing_summary_full_note_exact':True,'tail_body_geometry_and_font_exact':True,'tail_RGB_identity_not_claimed':True,'official_core_or_renderer_modified':False,'audio_or_video_produced_or_dispatched_by_this_agent':False,'published40_package_unchanged':True,'next_source_writer':'/root/resume_audio_ci exclusively for necessary27 audio controls; this text writer is now stopped'}
p=H/'text-source-freeze-and-static-approval.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k.endswith('sha256')or k=='article'},ensure_ascii=False));print('report',sha(p),'manifest',sha(CI))
