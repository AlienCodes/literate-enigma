"""Rerun original GEN/text in the already frozen mirror after exact T34 split."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).parent;B=H.parent;V=H/'gen-text-validation';M=V/'mirror';W=M/'_text-preflight-work';C=H/'candidate-payload'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
OUT=H/'recheck-after-T34';OUT.mkdir(exist_ok=True)
initial=json.loads((V/'report.json').read_text());assert initial['core_unchanged']and initial['articles'][0]['generator_roundtrip_exact']
core={p:sha(M/p)for p in P.CORE_FILES}
for rel in ['视频/脚本/14.json','视频/工具/初稿生成/gen14.py','新版定稿/14-the-fungus-that-turns-ants-into-zombies.md','视频/工具/用户同意记录.json']:
 shutil.copyfile(C/rel,M/rel)
candidate=json.loads((C/'视频/脚本/14.json').read_text());before=sha(C/'视频/脚本/14.json');workjson=W/'scripts/14.json';workjson.unlink()
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,text=P.execute([sys.executable,M/'视频/工具/初稿生成/gen14.py'],W,env,OUT/'original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(candidate,got)
report={'article':'14','kind':'actual-original-full-JSON-GEN-and-text-recheck-after-authorized-T34-data-split','first_failed_run_retained':str(V/'report.json'),'first_failed_T34_log':str(V/'logs/14-text-gate-after-repair.log'),'current_source_sha256':before,'generator_sha256':sha(C/'视频/工具/初稿生成/gen14.py'),'manuscript_sha256':sha(C/'新版定稿/14-the-fungus-that-turns-ants-into-zombies.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta and code==0,'JSON_differences':delta,'new_snapshot_copied':False,'original_core_before_sha256':core,'native_video_or_audio_or_dispatch_produced':False}
assert code==0 and not delta
raw,rawtext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','14','出片'],W,env,OUT/'original-text-before-repair.log')
repair,repairtext=P.execute([sys.executable,M/'视频/工具/新管/修.py','14'],W,env,OUT/'original-mechanical-repair.log')
actual=json.loads(workjson.read_text());shutil.copyfile(workjson,OUT/'14-original-auto-repaired.json')
final,finaltext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','14','出片'],W,env,OUT/'original-text-after-repair.log')
report.update(original_text_before_repair_exit=raw,original_repair_exit=repair,original_text_after_repair_exit=final,original_text_hard_errors=[l for l in finaltext.splitlines()if l.strip().startswith('✘')],original_pending_confirmations=[l for l in finaltext.splitlines()if l.strip().startswith('？')],original_mechanical_repair_differences=P.differences(candidate,actual),original_core_after_sha256={p:sha(M/p)for p in P.CORE_FILES},candidate_source_unchanged=sha(C/'视频/脚本/14.json')==before)
report['passed']=report['whole_JSON_roundtrip_exact']and raw==repair==final==0 and report['original_core_before_sha256']==report['original_core_after_sha256']and report['candidate_source_unchanged']
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'GEN_exact':report['whole_JSON_roundtrip_exact'],'text_before':raw,'text_after':final,'report_sha256':sha(OUT/'report.json')},ensure_ascii=False));sys.exit(0 if report['passed']else 1)
