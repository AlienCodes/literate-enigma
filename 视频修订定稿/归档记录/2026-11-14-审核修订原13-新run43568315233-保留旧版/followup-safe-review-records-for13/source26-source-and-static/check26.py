"""Original GEN/full text checks in the closed article14 mirror, exclusively reused."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).parent;B=H.parent;M=B/'article14-user-review-20261114/gen-text-validation/mirror';W=M/'_text-preflight-work26';C=H/'candidate-payload';OUT=H/'gen-text-validation-v2';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
core={p:sha(M/p)for p in P.CORE_FILES};context={}
for folder,glob in [('视频/脚本','[0-9][0-9].json'),('新版定稿','[0-9][0-9]-*.md')]:
 for src in (B/'payload'/folder).glob(glob):
  dst=M/folder/src.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);context[str(src.relative_to(B/'payload'))]=sha(src)
for rel in ['视频/脚本/26.json','视频/工具/初稿生成/gen26.py','新版定稿/26-the-language-the-children-invented.md','视频/制作记录/26_待改清单.md','视频/工具/用户同意记录.json']:
 dst=M/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(C/rel,dst)
W.mkdir(exist_ok=True);(W/'scripts').mkdir(exist_ok=True)
for src in (M/'视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(src,W/'scripts'/src.name)
if not(W/'fonts').exists():(W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True)
candidate=json.loads((C/'视频/脚本/26.json').read_text());before=sha(C/'视频/脚本/26.json');workjson=W/'scripts/26.json';workjson.unlink(missing_ok=True)
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,text=P.execute([sys.executable,M/'视频/工具/初稿生成/gen26.py'],W,env,OUT/'original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(candidate,got)
report={'article':'26','book_order':'27','kind':'actual-original-full-JSON-GEN-and-text-checks','exclusive_closed_mirror_reuse':True,'new_snapshot_copied':False,'current_source_sha256':before,'generator_sha256':sha(C/'视频/工具/初稿生成/gen26.py'),'manuscript_sha256':sha(C/'新版定稿/26-the-language-the-children-invented.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta and code==0,'JSON_differences':delta,'original_core_before_sha256':core,'native_video_or_audio_or_dispatch_produced':False,'cross_article_70_context_sha256':context}
assert code==0 and not delta
raw,rawtext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','26','出片'],W,env,OUT/'original-text-before-repair.log')
repair,repairtext=P.execute([sys.executable,M/'视频/工具/新管/修.py','26'],W,env,OUT/'original-mechanical-repair.log')
actual=json.loads(workjson.read_text());shutil.copyfile(workjson,OUT/'26-original-auto-repaired.json')
final,finaltext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','26','出片'],W,env,OUT/'original-text-after-repair.log')
report.update(original_text_before_repair_exit=raw,original_repair_exit=repair,original_text_after_repair_exit=final,original_text_hard_errors=[l for l in finaltext.splitlines()if l.strip().startswith('✘')],original_pending_confirmations=[l for l in finaltext.splitlines()if l.strip().startswith('？')],original_mechanical_repair_differences=P.differences(candidate,actual),original_core_after_sha256={p:sha(M/p)for p in P.CORE_FILES},candidate_source_unchanged=sha(C/'视频/脚本/26.json')==before)
report['passed']=report['whole_JSON_roundtrip_exact']and raw==repair==final==0 and report['original_core_before_sha256']==report['original_core_after_sha256']and report['candidate_source_unchanged']
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'GEN_exact':report['whole_JSON_roundtrip_exact'],'text_before':raw,'text_after':final,'report_sha256':sha(OUT/'report.json')},ensure_ascii=False));sys.exit(0 if report['passed']else 1)
