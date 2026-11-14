"""Original GEN/full-text checks for three authorized source53 presentation edits."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).parent;B=H.parent;BASE=B/'preflight-frozen66-v2-part1/mirror';C=H/'candidate-payload';V=H/'thin-validation';M=V/'mirror';W=M/'_text-work';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('original_data_preflight53',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
if not M.exists():
 (M/'视频').mkdir(parents=True);shutil.copytree(BASE/'视频/工具',M/'视频/工具',ignore=shutil.ignore_patterns('__pycache__','*.pyc'));shutil.copytree(BASE/'新版定稿',M/'新版定稿');(M/'视频/制作记录').mkdir();(M/'视频/脚本').mkdir();W.mkdir();(W/'scripts').mkdir();(W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True);q=M/'视频/资源/字体';q.parent.mkdir(parents=True);q.symlink_to(M/'视频/工具/fonts',target_is_directory=True)
 for p in BASE.glob('*.md'):shutil.copyfile(p,M/p.name)
for root in [BASE,B/'payload']:
 for p in (root/'视频/制作记录').glob('*'):
  if p.is_file()and p.suffix in('.md','.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
 for p in (root/'视频').glob('*.md'):shutil.copyfile(p,M/'视频'/p.name)
 for p in (root/'新版定稿').glob('*.md'):shutil.copyfile(p,M/'新版定稿'/p.name)
 for p in (root/'视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(p,M/'视频/脚本'/p.name);shutil.copyfile(p,W/'scripts'/p.name)
for rel in ['视频/脚本/53.json','视频/工具/初稿生成/gen53.py','新版定稿/53-the-wind-that-kept-no-time.md','视频/工具/用户同意记录.json','视频/制作记录/53_待改清单.md']:
 (M/rel).unlink(missing_ok=True);shutil.copyfile(C/rel,M/rel)
snapshot=Path('/workspace/work/article35-source53-readonly-native-baseline-20261114/actual-root-last-sent53-at-native43523430839.json');assert sha(snapshot)=='40c62496709925567ae538f8202e4fa54dc9112b95b551ce52f536caaca0ee8a';dest=M/'视频/脚本/已发版本/53.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(snapshot,dest)
record_src=B/'payload/视频/制作记录/逐句确认/53.json'
if not record_src.exists():record_src=BASE/'视频/制作记录/逐句确认/53.json'
record=M/'视频/制作记录/逐句确认/53.json';record.parent.mkdir(exist_ok=True);shutil.copyfile(record_src,record)
logs=V/'logs';logs.mkdir(exist_ok=True);core={p:sha(M/p)for p in P.CORE_FILES};expected=json.loads((C/'视频/脚本/53.json').read_text());source_sha=sha(C/'视频/脚本/53.json');workjson=W/'scripts/53.json';workjson.unlink(missing_ok=True)
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,text=P.execute([sys.executable,M/'视频/工具/初稿生成/gen53.py'],W,env,logs/'53-original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(expected,got);assert code==0 and not delta
reasons={
'S14':'T1没加信息：只按用户058把原句analysis分析和mechanism机理标为重点，原flutter事实和1991年断言均保留。T3词性：analysis和mechanism都是名词，本文为分析与颤振机理；asserted过去式断言、erred过去式出错了。T6不生硬：后来的分析把这一机理称为颤振沿用原译。T7通顺：两块原语序与原小字完整连续。T8看得懂：call A B把A称为B与that宾语从句原说明完整。T21贴合语境：analysis为对大桥事故的分析，mechanism为气动自激过程的机理，与既有S11机理词义一致。',
'S15':'T1没加信息：只按用户059把委员会力主改为敦促，保进行与全部原风洞模型试验事实。T3词性：urged是urge过去式，作为谓语敦促，未加为新重点；wind-tunnel为风洞。T6不生硬：该委员会敦促进行风洞试验自然。T7通顺：原三块由提出试验到缩尺复制品试验渐成惯例连续通读。T8看得懂：原trials on和become customary说明完整。T21贴合语境：urged为委员会提出强烈建议，用户指定敦促而非力主，进行原样保留。',
'S17':'T1没加信息：只按用户060标实际过去式kept time with整体，与和合拍同一用法而大桥普通，原故事事实与原详细五点简述完整保留。T3词性：kept是keep过去式，keep time with为动词短语与某事物合拍，never否定在粗体外；instruct动词，accurately副词，destructive形容词。T6不生硬：风从未与大桥合拍沿用原译，两段中文只同色标注。T7通顺：原两块从正确解读到大桥自身运动使风具有破坏力连续。T8看得懂：原if read accurately和keep time with与turn A加形容词说明完整。T21贴合语境：kept time with意为按大桥运动的节拍吹，不是保存时间，原文否定never保持。T22短语整体：三个英文词同一重点，中文与和合拍用同key而中间大桥普通。T23分隔标注：与和合拍是同一谓语两部分，同一kept time with key并非新添多义。T33简述讲全：原五点逐字保留事故、结构隐患、共振纠误、颤振反馈机制、后续风洞试验和1950新桥。'}
reviews=[]
for sid,why in reasons.items():
 rc,txt=P.execute([sys.executable,M/'视频/工具/逐句确认.py','53',sid,why],W,env,logs/f'53-original-{sid}-review.log');assert rc==0;reviews.append(dict(sentence=sid,exit=rc))
raw,rawtext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','53','出片'],W,env,logs/'53-original-text-before-repair.log');rc,rt=P.execute([sys.executable,M/'视频/工具/新管/修.py','53'],W,env,logs/'53-original-repair.log');actual=json.loads(workjson.read_text());shutil.copyfile(workjson,V/'53-original-auto-repaired.json');last,lasttext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','53','出片'],W,env,logs/'53-original-text-after-repair.log');out=C/'视频/制作记录/逐句确认/53.json';out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(record,out)
r=dict(article='53',book_order='35',source_sha256=source_sha,GEN_sha256=sha(C/'视频/工具/初稿生成/gen53.py'),MD_sha256=sha(C/'新版定稿/53-the-wind-that-kept-no-time.md'),original_generator_exit=code,whole_JSON_roundtrip_exact=not delta,JSON_differences=delta,original_text_before_repair_exit=raw,original_repair_exit=rc,original_text_after_repair_exit=last,original_text_hard_errors=[x for x in lasttext.splitlines()if x.strip().startswith('✘')],original_text_pending_confirmations=[x for x in lasttext.splitlines()if x.strip().startswith('？')],original_mechanical_repair_differences=P.differences(expected,actual),original_sentence_text_reviews=reviews,core_before_sha256=core,core_after_sha256={p:sha(M/p)for p in P.CORE_FILES},actual_original_last_sent_snapshot=dict(path=str(snapshot),sha256=sha(snapshot),immutable_native_run=43523430839,exact_original_L13_lookup=str(dest),missing_snapshot_skip_not_used=True),source_input_unchanged=sha(C/'视频/脚本/53.json')==source_sha,no_audio_video_or_dispatch=True)
r['passed']=code==raw==rc==last==0 and not delta and r['core_before_sha256']==r['core_after_sha256']and r['source_input_unchanged'];(V/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(passed=r['passed'],GEN_exact=not delta,text_before=raw,text_after=last,report=str(V/'report.json'),report_sha256=sha(V/'report.json')),ensure_ascii=False));sys.exit(0 if r['passed']else 1)
