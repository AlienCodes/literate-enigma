"""Original GEN/text checks in a production-tools + canonical-data thin mirror."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).parent;B=H.parent;BASE=B/'preflight-frozen66-v2-part1/mirror';C=H/'candidate-payload';V=H/'thin-validation';M=V/'mirror';W=M/'_text-work'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
if not M.exists():
 (M/'视频').mkdir(parents=True);shutil.copytree(BASE/'视频/工具',M/'视频/工具',copy_function=__import__('os').link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'));shutil.copytree(BASE/'新版定稿',M/'新版定稿')
 (M/'视频/制作记录').mkdir()
 for root in [BASE,B/'payload']:
  for p in (root/'视频/制作记录').glob('*'):
   if p.is_file()and p.suffix in('.md','.json')and(p.name.startswith('33')or p.name=='重点词被去掉.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
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
for rel in ['视频/脚本/33.json','视频/工具/初稿生成/gen33.py','新版定稿/33-thirteen-in-the-cave.md','视频/工具/用户同意记录.json']:
 (M/rel).unlink(missing_ok=True);shutil.copyfile(C/rel,M/rel)
record_src=B/'payload/视频/制作记录/逐句确认/33.json'
if not record_src.exists():record_src=BASE/'视频/制作记录/逐句确认/33.json'
record_dest=M/'视频/制作记录/逐句确认/33.json';record_dest.parent.mkdir(exist_ok=True);shutil.copyfile(record_src,record_dest)
logs=V/'logs-v1';logs.mkdir(exist_ok=True);core={p:sha(M/p)for p in P.CORE_FILES};expected=json.loads((C/'视频/脚本/33.json').read_text());source_sha=sha(C/'视频/脚本/33.json');workjson=W/'scripts/33.json';workjson.unlink(missing_ok=True)
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,text=P.execute([sys.executable,M/'视频/工具/初稿生成/gen33.py'],W,env,logs/'33-original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(expected,got);assert code==0 and not delta
reasons={
'S14':'T1没加信息：原约万人参与救援及百余潜水员人数均未改，只按用户指定补divers重点。T3词性：divers是diver复数名词潜水员，contingent分队名词、converged on汇集到动词短语及policemen警察名词、deployed调派原注保留。T4方向：a contingent of A中文一支A组成的分队语序沿用原文。T6不生硬：一支100多名潜水员组成的分队原句保留。T7通顺：不为英文拆乱中文，divers潜水员只加成对标记。T8看得懂：前文S5已有divers潜水员，此处仍同义，原including与a contingent of小字逐字保持。T21贴合语境：divers就是救援队里的潜水员，不指潜水本身或队伍。必记表：原速查表divers行已有潜水员及名词原形diver，本次保留一条不重复添加。',
'S16':'T1没加信息：原结语每个男孩生还而两名救援者被悼念与原五点简述不增减。T3词性：alive形容词活着、mourned被动哀悼沿原注。T6不生硬：每个男孩都活着回到了家，而两名救援者却只能永远被悼念，原句表达保留。T7通顺：原中文语序原样。T8看得懂：原小字交代两名救援者为2018年萨曼与2019年去世海豹队员，前文有依据。T21贴合语境：mourned对应悼念准确。T33简述讲全：五点被困、发现、难题、救出、代价，依次讲泰国12男孩和助理教练被困洞穴，九天后找到13人全活，窄水道救援与气瓶布置，镇静担架接力带出，13全获救但两救援者遇难；整段逐字沿实际43543967031已验稿，只原机器换行单独绑定。'}
reviews=[]
for sid,why in reasons.items():
 review_code,review_text=P.execute([sys.executable,M/'视频/工具/逐句确认.py','33',sid,why],W,env,logs/f'33-original-{sid}-text-review.log');assert review_code==0;reviews.append({'sentence':sid,'exit':review_code})
record_out=C/'视频/制作记录/逐句确认/33.json';record_out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(record_dest,record_out)
raw,rawtext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','33','出片'],W,env,logs/'33-original-text-before-repair.log');rc,rt=P.execute([sys.executable,M/'视频/工具/新管/修.py','33'],W,env,logs/'33-original-repair.log');actual=json.loads(workjson.read_text());shutil.copyfile(workjson,V/'33-original-auto-repaired.json');post_review_code,post_review_text=P.execute([sys.executable,M/'视频/工具/逐句确认.py','33','S16',reasons['S16']],W,env,logs/'33-original-S16-after-mechanical-wrap-review.log');assert post_review_code==0;shutil.copyfile(record_dest,record_out);last,lasttext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','33','出片'],W,env,logs/'33-original-text-after-repair.log')
r={'article':'33','kind':'actual-original-GEN-full-JSON-and-text-thin-mirror','thin_snapshot_scope':'Exact original production tools, all70 canonical MD/JSON and root-level production records required by unchanged selftests; only33 nested sentence review record. No archived proof trees copied.','source_sha256':source_sha,'GEN_sha256':sha(C/'视频/工具/初稿生成/gen33.py'),'MD_sha256':sha(C/'新版定稿/33-thirteen-in-the-cave.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta,'JSON_differences':delta,'original_text_before_repair_exit':raw,'original_repair_exit':rc,'original_text_after_repair_exit':last,'original_text_hard_errors':[x for x in lasttext.splitlines()if x.strip().startswith('✘')],'original_text_pending_confirmations':[x for x in lasttext.splitlines()if x.strip().startswith('？')],'original_mechanical_repair_differences':P.differences(expected,actual),'original_sentence_text_reviews':reviews,'sentence_review_before_sha256':sha(record_src),'sentence_review_after_sha256':sha(record_out),'only_requested_sentence_review_records_updated':all(json.loads(record_src.read_text()).get(k)==v for k,v in json.loads(record_out.read_text()).items()if k not in('S14','S16')),'core_before_sha256':core,'core_after_sha256':{p:sha(M/p)for p in P.CORE_FILES},'source_input_unchanged':sha(C/'视频/脚本/33.json')==source_sha,'no_audio_video_or_dispatch':True}
r['passed']=code==raw==rc==last==0 and not delta and r['core_before_sha256']==r['core_after_sha256']and r['source_input_unchanged'];(V/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'GEN_exact':not delta,'text_before':raw,'text_after':last,'report_sha256':sha(V/'report.json')},ensure_ascii=False));sys.exit(0 if r['passed']else 1)
