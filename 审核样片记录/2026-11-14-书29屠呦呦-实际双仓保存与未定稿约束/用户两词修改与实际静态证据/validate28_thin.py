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
   if p.is_file()and p.suffix in('.md','.json')and(p.name.startswith('28')or p.name=='重点词被去掉.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
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
for rel in ['视频/脚本/28.json','视频/工具/初稿生成/gen28.py','新版定稿/28-a-handful-of-wormwood-that-saved-millions.md','视频/工具/用户同意记录.json']:
 (M/rel).unlink(missing_ok=True);shutil.copyfile(C/rel,M/rel)
record_src=B/'payload/视频/制作记录/逐句确认/28.json'
if not record_src.exists():record_src=BASE/'视频/制作记录/逐句确认/28.json'
record_dest=M/'视频/制作记录/逐句确认/28.json';record_dest.parent.mkdir(exist_ok=True);shutil.copyfile(record_src,record_dest)
logs=V/'logs-v3';logs.mkdir(exist_ok=True);core={p:sha(M/p)for p in P.CORE_FILES};expected=json.loads((C/'视频/脚本/28.json').read_text());source_sha=sha(C/'视频/脚本/28.json');workjson=W/'scripts/28.json';workjson.unlink(missing_ok=True)
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,text=P.execute([sys.executable,M/'视频/工具/初稿生成/gen28.py'],W,env,logs/'28-original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(expected,got);assert code==0 and not delta
reasons={
'S1':'T1没加信息：523项目取自原1967年5月23日启动日期，事实数字原样。T3词性：was named after是一般过去时被动动词短语，译得名于。T4方向：after在name after固定用法中不是时间之后。T6不生硬：原得名于它的启动日期保持。T7通顺：整句523项目是一项秘密军事任务涉及多机构得名于日期，原句读通。T8看得懂：be named after原小字以命名保留。T21贴合语境：用户030要求was named after整体仅得名于三字同色。',
'S14':'T1没加信息：原2011年拉斯克评审团对药物救命效果的评价未增具体人数。T3词性：credited是credit过去式，与with构成credit A with B用法。T4方向：把B功劳归给A，本句A这种药物B挽救数百万人的功劳，不反向。T6不生硬：原将挽救了数百万人的功劳归功于这种药物保留。T7通顺：整体中文语序exact不为英文拆乱。T8看得懂：用户031指定将和归功于两处同色，原credit A with B小字保留。T21贴合语境：重点表示评审团把挽救生命的功劳归于这种药物，同一释义两段不是两种异译。',
'S17':'T1没加信息：葛洪古方与低温提取的原结语及五点简述均逐字核原批准源。T3词性：essence名词精髓，skipped过去式略去，lay为lie过去式。T4方向：lay in在于，古方只有浸泡青蒿而略去煮沸。T6不生硬：葛洪那句话的精髓正在于它略去的煮沸，中文指代明确。T7通顺：古方浸泡提示低温提取与全文寻找青蒿素的线索相接。T8看得懂：lie in和it skipped原语法说明完整，结语单页独立居中和大字号另实际核图。T21贴合语境：essence指古方关键线索，skipped表示省略加热步骤。T33简述讲全：寻药说明氯喹抗药性和523任务；线索交代青蒿时灵时不灵与古方浸泡；突破明确低温乙醚提取及小鼠有效尚非人体安全证据；验证交代自愿试服和21病人及分离纯晶体；影响交代联合疗法获世卫推荐、挽救生命与2015诺奖。'}
reviews=[]
for sid,why in reasons.items():
 review_code,review_text=P.execute([sys.executable,M/'视频/工具/逐句确认.py','28',sid,why],W,env,logs/f'28-original-{sid}-text-review.log');assert review_code==0;reviews.append({'sentence':sid,'exit':review_code})
record_out=C/'视频/制作记录/逐句确认/28.json';record_out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(record_dest,record_out)
raw,rawtext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','28','出片'],W,env,logs/'28-original-text-before-repair.log');rc,rt=P.execute([sys.executable,M/'视频/工具/新管/修.py','28'],W,env,logs/'28-original-repair.log');actual=json.loads(workjson.read_text());shutil.copyfile(workjson,V/'28-original-auto-repaired.json');post_review_code,post_review_text=P.execute([sys.executable,M/'视频/工具/逐句确认.py','28','S17',reasons['S17']],W,env,logs/'28-original-S17-after-mechanical-wrap-review.log');assert post_review_code==0;shutil.copyfile(record_dest,record_out);last,lasttext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','28','出片'],W,env,logs/'28-original-text-after-repair.log')
r={'article':'28','kind':'actual-original-GEN-full-JSON-and-text-thin-mirror','thin_snapshot_scope':'Exact original production tools, all70 canonical MD/JSON and root-level production records required by unchanged selftests; only28 nested sentence review record. No archived proof trees copied.','source_sha256':source_sha,'GEN_sha256':sha(C/'视频/工具/初稿生成/gen28.py'),'MD_sha256':sha(C/'新版定稿/28-a-handful-of-wormwood-that-saved-millions.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta,'JSON_differences':delta,'original_text_before_repair_exit':raw,'original_repair_exit':rc,'original_text_after_repair_exit':last,'original_text_hard_errors':[x for x in lasttext.splitlines()if x.strip().startswith('✘')],'original_text_pending_confirmations':[x for x in lasttext.splitlines()if x.strip().startswith('？')],'original_mechanical_repair_differences':P.differences(expected,actual),'original_sentence_text_reviews':reviews,'sentence_review_before_sha256':sha(record_src),'sentence_review_after_sha256':sha(record_out),'only_requested_sentence_review_records_updated':all(json.loads(record_src.read_text()).get(k)==v for k,v in json.loads(record_out.read_text()).items()if k not in('S1','S14','S17')),'core_before_sha256':core,'core_after_sha256':{p:sha(M/p)for p in P.CORE_FILES},'source_input_unchanged':sha(C/'视频/脚本/28.json')==source_sha,'no_audio_video_or_dispatch':True}
r['passed']=code==raw==rc==last==0 and not delta and r['core_before_sha256']==r['core_after_sha256']and r['source_input_unchanged'];(V/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'GEN_exact':not delta,'text_before':raw,'text_after':last,'report_sha256':sha(V/'report.json')},ensure_ascii=False));sys.exit(0 if r['passed']else 1)
