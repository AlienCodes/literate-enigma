"""Original GEN/text checks in a production-tools + canonical-data thin mirror."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).parent;B=H.parent;BASE=B/'preflight-frozen66-v2-part1/mirror';C=H/'candidate-payload';V=H/'thin-validation';M=V/'mirror';W=M/'_text-work'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
if not M.exists():
 (M/'视频').mkdir(parents=True);shutil.copytree(BASE/'视频/工具',M/'视频/工具',ignore=shutil.ignore_patterns('__pycache__','*.pyc'));shutil.copytree(BASE/'新版定稿',M/'新版定稿')
 (M/'视频/制作记录').mkdir()
 for root in [BASE,B/'payload']:
  for p in (root/'视频/制作记录').glob('*'):
   if p.is_file()and p.suffix in('.md','.json')and(p.name.startswith('27')or p.name=='重点词被去掉.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
  for p in (root/'视频').glob('*.md'):shutil.copyfile(p,M/'视频'/p.name)
  for p in (root/'新版定稿').glob('*.md'):shutil.copyfile(p,M/'新版定稿'/p.name)
 W.mkdir();(W/'scripts').mkdir()
 for p in (B/'payload/视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(p,W/'scripts'/p.name)
 (W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True)
 resource=M/'视频/资源/字体';resource.parent.mkdir(parents=True);resource.symlink_to(M/'视频/工具/fonts',target_is_directory=True)
(M/'视频/脚本').mkdir(exist_ok=True)
for p in (B/'payload/视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(p,M/'视频/脚本'/p.name)
for root in [BASE,B/'payload']:
 for p in (root/'视频/制作记录').glob('*'):
  if p.is_file()and p.suffix in('.md','.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
for rel in ['视频/脚本/27.json','视频/工具/初稿生成/gen27.py','新版定稿/27-life-in-the-forbidden-zone.md','视频/工具/用户同意记录.json']:shutil.copyfile(C/rel,M/rel)
record_src=B/'payload/视频/制作记录/逐句确认/27.json'
if not record_src.exists():record_src=BASE/'视频/制作记录/逐句确认/27.json'
record_dest=M/'视频/制作记录/逐句确认/27.json';record_dest.parent.mkdir(exist_ok=True);shutil.copyfile(record_src,record_dest)
logs=V/'logs';logs.mkdir(exist_ok=True);core={p:sha(M/p)for p in P.CORE_FILES};expected=json.loads((C/'视频/脚本/27.json').read_text());source_sha=sha(C/'视频/脚本/27.json');workjson=W/'scripts/27.json';workjson.unlink(missing_ok=True)
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,text=P.execute([sys.executable,M/'视频/工具/初稿生成/gen27.py'],W,env,logs/'27-original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(expected,got);assert code==0 and not delta
why='T1没加信息：本次只落实用户点名的nutrients养分重点，原句数字、事实和语序都保留。T3词性：decomposing现在分词作宾语补足语，polluted为形容词化分词，impeding现在分词表结果，nutrients复数名词译养分。T6不生硬：沿用用户审定的养分回归土壤，语序自然。T7通顺：最重污染处落叶分解少了约40%，阻碍养分回归土壤，整句读通。T8看得懂：保留the return of A to B释义，英文与中文养分同色、大小清楚。T21贴合语境：nutrients指落叶分解后回归土壤的养分，符合本文营养循环语境。'
review_code,review_text=P.execute([sys.executable,M/'视频/工具/逐句确认.py','27','S14',why],W,env,logs/'27-original-sentence14-review.log');assert review_code==0
record_out=C/'视频/制作记录/逐句确认/27.json';record_out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(record_dest,record_out)
raw,rawtext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','27','出片'],W,env,logs/'27-original-text-before-repair.log');rc,rt=P.execute([sys.executable,M/'视频/工具/新管/修.py','27'],W,env,logs/'27-original-repair.log');actual=json.loads(workjson.read_text());shutil.copyfile(workjson,V/'27-original-auto-repaired.json');last,lasttext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','27','出片'],W,env,logs/'27-original-text-after-repair.log')
r={'article':'27','kind':'actual-original-GEN-full-JSON-and-text-thin-mirror','thin_snapshot_scope':'Exact original production tools, all70 canonical MD/JSON and root-level production records required by unchanged selftests; only27 nested sentence review record. No archived proof trees copied.','source_sha256':source_sha,'GEN_sha256':sha(C/'视频/工具/初稿生成/gen27.py'),'MD_sha256':sha(C/'新版定稿/27-life-in-the-forbidden-zone.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta,'JSON_differences':delta,'original_text_before_repair_exit':raw,'original_repair_exit':rc,'original_text_after_repair_exit':last,'original_text_hard_errors':[x for x in lasttext.splitlines()if x.strip().startswith('✘')],'original_text_pending_confirmations':[x for x in lasttext.splitlines()if x.strip().startswith('？')],'original_mechanical_repair_differences':P.differences(expected,actual),'original_sentence14_review_tool_exit':review_code,'sentence_review_before_sha256':sha(record_src),'sentence_review_after_sha256':sha(record_out),'only_sentence14_review_record_updated':all(json.loads(record_src.read_text()).get(k)==v for k,v in json.loads(record_out.read_text()).items()if k!='S14'),'core_before_sha256':core,'core_after_sha256':{p:sha(M/p)for p in P.CORE_FILES},'source_input_unchanged':sha(C/'视频/脚本/27.json')==source_sha,'no_audio_video_or_dispatch':True}
r['passed']=code==raw==rc==last==0 and not delta and r['core_before_sha256']==r['core_after_sha256']and r['source_input_unchanged'];(V/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'GEN_exact':not delta,'text_before':raw,'text_after':last,'report_sha256':sha(V/'report.json')},ensure_ascii=False));sys.exit(0 if r['passed']else 1)
