"""Execute actual original helper and text gate for approved05; only publish GEN."""
import pathlib,importlib.util,json,hashlib,shutil,subprocess,os,sys,datetime
B=pathlib.Path(__file__).parent;M=B/'mirror';PAY=pathlib.Path('/workspace/work/video-audit70-20261113/payload');BASE=pathlib.Path('/workspace/work/github-publication/target');F=pathlib.Path('/workspace/work/video-audit70-20261113/generator_text_preflight.py');spec=importlib.util.spec_from_file_location('unchanged_factory',F);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
source=PAY/'视频/脚本/05.json';raw=source.read_bytes();want='47fa4c8746deecb0583e08633d1b52751ed3e6046ee5c1e46d032c443d220fba';assert hashlib.sha256(raw).hexdigest()==want
md=next((PAY/'新版定稿').glob('05-*.md'));mdraw=md.read_bytes();GEN=PAY/'视频/工具/初稿生成/gen05.py';oldgen=GEN.read_bytes();(B/'gen05-before.py').write_bytes(oldgen)
prep=json.loads((B/'mirror-preparation.json').read_text());corebefore={p:f.digest(M/p) for p in f.CORE_FILES};assert corebefore==prep['core_before']
f.overlay_current_data(BASE,M);f.overlay_current_data(PAY,M);assert corebefore=={p:f.digest(M/p) for p in f.CORE_FILES}
text,issues=f.pure_generator(json.loads(raw));(B/'pure-factory-issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n');assert text is not None and not issues
candidate=B/'gen05-candidate.py';candidate.write_text(text);target=M/'视频/工具/初稿生成/gen05.py';target.write_text(text)
W=M/'_05-original-text-gate-work';W.mkdir(exist_ok=True);(W/'scripts').mkdir(exist_ok=True)
for p in (M/'视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(p,W/'scripts'/p.name)
(W/'scripts/05.json').unlink()
if not (W/'fonts').exists():(W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True)
fonts=M/'视频/资源/字体';fonts.parent.mkdir(parents=True,exist_ok=True)
if not fonts.exists():fonts.symlink_to(M/'视频/工具/fonts',target_is_directory=True)
PY='/workspace/work/video-venv/bin/python';env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(pathlib.Path(PY).parent)+os.pathsep+env.get('PATH','')
for k in ('YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID'):env.pop(k,None)
def execute(cmd,log):
 with log.open('w') as stream:r=subprocess.run(list(map(str,cmd)),cwd=W,env=env,stdout=stream,stderr=subprocess.STDOUT)
 return r.returncode,log.read_text(errors='replace')
code,stdout=execute([PY,target],B/'05-original-helper-full-stdout.log');got=json.loads((W/'scripts/05.json').read_text()) if (W/'scripts/05.json').exists() else None;diff=f.differences(json.loads(raw),got);(B/'05-original-helper-whole-JSON-differences.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2)+'\n')
report={'article':'05','created_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_fullSHA256':want,'source_JSON_or_MD_modified':False,'original_factory_SHA256':f.digest(F),'factory_issues':issues,'original_helper_exit':code,'original_helper_full_stdout_file':str(B/'05-original-helper-full-stdout.log'),'original_helper_stdout_SHA256':hashlib.sha256(stdout.encode()).hexdigest(),'whole_JSON_deep_equal':code==0 and not diff,'whole_JSON_differences':diff,'candidate_GEN_SHA256':f.digest(candidate),'generator_published':False,'original_cores_before':corebefore,'baseline_snapshot_commit':prep['baseline_head'],'audio_video_or_PDF_production':False,'push_or_launch':False}
assert code==0 and not diff,'Original fullJSON roundtrip failed; GEN not published.'
(W/'scripts/05.json').write_bytes(raw)
textcode,textstdout=execute([PY,M/'视频/工具/踩坑核查.py','05','文本'],B/'05-original-text-gate-full-stdout.log');report.update({'original_text_gate_exit':textcode,'original_text_gate_full_stdout_file':str(B/'05-original-text-gate-full-stdout.log'),'original_text_gate_stdout_SHA256':hashlib.sha256(textstdout.encode()).hexdigest(),'original_text_hard_error_lines':[x for x in textstdout.splitlines() if x.strip().startswith('✘')],'original_text_pending_lines':[x for x in textstdout.splitlines() if x.strip().startswith('？')],'original_checker_selftest_failure':('核查程序失灵' in textstdout or '【失灵】' in textstdout),'original_cores_after':{p:f.digest(M/p) for p in f.CORE_FILES},'JSON_input_after_SHA256':f.digest(source),'MD_input_before_SHA256':hashlib.sha256(mdraw).hexdigest(),'MD_input_after_SHA256':f.digest(md)})
report['original_cores_unchanged']=report['original_cores_after']==corebefore
safe=report['original_cores_unchanged'] and source.read_bytes()==raw and md.read_bytes()==mdraw
if textcode==0 and safe:
 GEN.write_bytes(candidate.read_bytes());report['generator_published']=True;report['published_GEN_SHA256']=f.digest(GEN)
report['status']='passed' if report['generator_published'] else 'needs_review'
(B/'05-original-generator-and-text-gate-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':report['status'],'helper_exit':code,'wholeJSONequal':not diff,'text_exit':textcode,'generator_published':report['generator_published'],'GEN_SHA256':report.get('published_GEN_SHA256'),'report':str(B/'05-original-generator-and-text-gate-validation.json')},ensure_ascii=False))
assert report['status']=='passed'
