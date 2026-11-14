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
   if p.is_file()and p.suffix in('.md','.json')and(p.name.startswith('47')or p.name=='重点词被去掉.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
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
for rel in ['视频/脚本/47.json','视频/工具/初稿生成/gen47.py','新版定稿/47-shadows-of-wolves-over-yellowstone.md','视频/工具/用户同意记录.json']:
 (M/rel).unlink(missing_ok=True);shutil.copyfile(C/rel,M/rel)
shutil.copyfile(C/'视频/制作记录/47_待改清单.md',M/'视频/制作记录/47_待改清单.md')
record_src=B/'payload/视频/制作记录/逐句确认/47.json'
if not record_src.exists():record_src=BASE/'视频/制作记录/逐句确认/47.json'
record_dest=M/'视频/制作记录/逐句确认/47.json';record_dest.parent.mkdir(exist_ok=True);shutil.copyfile(record_src,record_dest)
snapshot=H/'next-native-root-actual-last-sent47.json';assert sha(snapshot)=='3b2ffeb112b8c80e34a180bd47b6ae56fb5948b044fc370c1e462e5daf724dcf';snapdest=M/'视频/脚本/已发版本/47.json';snapdest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(snapshot,snapdest)
logs=V/'logs-v3';logs.mkdir(exist_ok=True);core={p:sha(M/p)for p in P.CORE_FILES};expected=json.loads((C/'视频/脚本/47.json').read_text());source_sha=sha(C/'视频/脚本/47.json');workjson=W/'scripts/47.json';workjson.unlink(missing_ok=True)
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,text=P.execute([sys.executable,M/'视频/工具/初稿生成/gen47.py'],W,env,logs/'47-original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(expected,got);assert code==0 and not delta
reasons={
'S4':'T1没加信息：因果说明仍指2014年流行视频讲的故事，原狼回归威慑麋鹿、柳树恢复、河岸泥土固定四层完整。T3词性：viral video名词短语，narrated by过去分词短语，spun过去式，compelling形容词，narrative名词，wary of形容词短语，retreated from过去式，willows复数名词，flourish和stabilise为let后不带to不定式。T6不生硬：正文原中文沿用片中说表明叙事归属，因果句完整。T7通顺：原中英文语序、所有主文标点及重点全一致，说明原64字一横行顺因果读通。T8看得懂：四个括注威慑力、行为改变、植被恢复、地貌重塑完整，同一行居中并由实际47px主字和29px说明核图。T21贴合语境：这条是片中故事的因果链，后文研究质疑其简单化；新布局没有把它升级为科学定论。',
'S13':'T1没加信息：用户038接受的新说明只解释原狼影比喻与本文多因素、争论和研究未有定论，相关依据在S6鹿群、S7觅食、S8抽样、S11缺水和S12争议。T3词性：unresolved形容词悬而未决，fainter和messier形容词比较级，fable名词谣传。T6不生硬：狼的影子明确比喻生态影响，作用可能夸大并非断言毫无作用。T7通顺：原正文比谣传更加无力、研究复杂的语序完整，说明由比喻释义、作者态度、其他影响因素和暂无定论串起。T8看得懂：本页只呈新通俗说明，语法比较状语和省略looks两旧说明均移除；按四处标点折行可连续读。T21贴合语境：通俗解释保可能和现有研究尚无定论等限定语，避免把影响较弱误解成狼不重要。'}
reviews=[]
for sid,why in reasons.items():
 review_code,review_text=P.execute([sys.executable,M/'视频/工具/逐句确认.py','47',sid,why],W,env,logs/f'47-original-{sid}-text-review.log');assert review_code==0;reviews.append({'sentence':sid,'exit':review_code})
record_out=C/'视频/制作记录/逐句确认/47.json';record_out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(record_dest,record_out)
raw,rawtext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','47','出片'],W,env,logs/'47-original-text-before-repair.log');rc,rt=P.execute([sys.executable,M/'视频/工具/新管/修.py','47'],W,env,logs/'47-original-repair.log');actual=json.loads(workjson.read_text());shutil.copyfile(workjson,V/'47-original-auto-repaired.json');last,lasttext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','47','出片'],W,env,logs/'47-original-text-after-repair.log')
r={'article':'47','kind':'actual-original-GEN-full-JSON-and-text-thin-mirror','thin_snapshot_scope':'Exact original production tools, all70 canonical MD/JSON and root-level production records required by unchanged selftests; only47 nested sentence review record. No archived proof trees copied.','source_sha256':source_sha,'GEN_sha256':sha(C/'视频/工具/初稿生成/gen47.py'),'MD_sha256':sha(C/'新版定稿/47-shadows-of-wolves-over-yellowstone.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta,'JSON_differences':delta,'original_text_before_repair_exit':raw,'original_repair_exit':rc,'original_text_after_repair_exit':last,'original_text_hard_errors':[x for x in lasttext.splitlines()if x.strip().startswith('✘')],'original_text_pending_confirmations':[x for x in lasttext.splitlines()if x.strip().startswith('？')],'original_mechanical_repair_differences':P.differences(expected,actual),'original_sentence_text_reviews':reviews,'sentence_review_before_sha256':sha(record_src),'sentence_review_after_sha256':sha(record_out),'only_requested_sentence_review_records_updated':all(json.loads(record_src.read_text()).get(k)==v for k,v in json.loads(record_out.read_text()).items()if k not in('S4','S13')),'core_before_sha256':core,'core_after_sha256':{p:sha(M/p)for p in P.CORE_FILES},'actual_original_last_sent_snapshot':{'path':str(snapshot),'sha256':sha(snapshot),'copied_to_exact_original_L13_lookup':str(snapdest),'missing_snapshot_skip_not_used':True},'source_input_unchanged':sha(C/'视频/脚本/47.json')==source_sha,'no_audio_video_or_dispatch':True}
r['passed']=code==raw==rc==last==0 and not delta and r['core_before_sha256']==r['core_after_sha256']and r['source_input_unchanged'];(V/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'GEN_exact':not delta,'text_before':raw,'text_after':last,'report_sha256':sha(V/'report.json')},ensure_ascii=False));sys.exit(0 if r['passed']else 1)
