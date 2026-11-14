"""Unchanged official GEN/full text checks in a small independent data mirror."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).parent;B=H.parent;BASE=B/'article14-user-review-20261114/gen-text-validation/mirror';M=H/'thin-validation/mirror';W=M/'_text-work36';C=H/'candidate-payload';OUT=H/'gen-text-validation-v6';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
T=M/'视频/工具';T.mkdir(parents=True,exist_ok=True)
for name in ['CLAUDE.md','AGENTS.md','README.md']:
 q=M/name
 if not q.exists():q.symlink_to(BASE/name)
for p in (BASE/'视频/制作记录').iterdir():
 q=M/'视频/制作记录'/p.name;q.parent.mkdir(parents=True,exist_ok=True)
 if not q.exists():q.symlink_to(p,target_is_directory=p.is_dir())
for name in ['对照文本','工作进度']:
 q=M/'视频'/name
 if not q.exists():q.symlink_to(BASE/'视频'/name,target_is_directory=True)
for p in (BASE/'视频/工具').iterdir():
 q=T/p.name
 if p.name in ('初稿生成','用户同意记录.json'):continue
 if not q.exists():q.symlink_to(p,target_is_directory=p.is_dir())
G=T/'初稿生成';G.mkdir(exist_ok=True)
for p in (BASE/'视频/工具/初稿生成').iterdir():
 if p.name=='gen36.py' or p.name=='__pycache__':continue
 q=G/p.name
 if not q.exists():q.symlink_to(p,target_is_directory=p.is_dir())
context={}
for folder,pattern in [('视频/脚本','[0-9][0-9].json'),('新版定稿','[0-9][0-9]-*.md')]:
 for root in [BASE,B/'payload']:
  for p in (root/folder).glob(pattern):
   q=M/folder/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 for p in (M/folder).glob(pattern):context[str(p.relative_to(M))]=sha(p)
for p in (BASE/'视频').glob('*.md'):
 q=M/'视频'/p.name;shutil.copyfile(p,q)
for p in (BASE/'视频/制作记录').glob('36*'):
 if not p.is_file()or p.suffix not in('.md','.json'):continue
 q=M/'视频/制作记录'/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
for rel in ['视频/脚本/已发版本/36.json','视频/制作记录/逐句确认/36.json']:
 p=BASE/rel
 if p.is_file():q=M/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
for rel in ['视频/脚本/36.json','视频/工具/初稿生成/gen36.py','新版定稿/36-the-company-that-invented-its-own-killer.md','视频/制作记录/36_待改清单.md','视频/工具/用户同意记录.json']:
 q=M/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(C/rel,q)
W.mkdir(exist_ok=True);(W/'scripts').mkdir(exist_ok=True)
for p in (M/'视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(p,W/'scripts'/p.name)
if not(W/'fonts').exists():(W/'fonts').symlink_to(T/'fonts',target_is_directory=True)
RF=M/'视频/资源/字体';RF.parent.mkdir(parents=True,exist_ok=True)
if not RF.exists():RF.symlink_to(T/'fonts',target_is_directory=True)
core={p:sha(M/p)for p in P.CORE_FILES};candidate=json.loads((C/'视频/脚本/36.json').read_text());before=sha(C/'视频/脚本/36.json');workjson=W/'scripts/36.json';workjson.unlink(missing_ok=True)
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(T),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,_=P.execute([sys.executable,G/'gen36.py'],W,env,OUT/'original-GEN.log');got=json.loads(workjson.read_text())if workjson.exists()else{};delta=P.differences(candidate,got)
report={'article':'36','book_order':'28','kind':'actual-original-full-JSON-GEN-and-text-checks','thin_mirror_context_current_file_hashes':context,'current_source_sha256':before,'generator_sha256':sha(C/'视频/工具/初稿生成/gen36.py'),'manuscript_sha256':sha(C/'新版定稿/36-the-company-that-invented-its-own-killer.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta and code==0,'JSON_differences':delta,'original_core_before_sha256':core,'native_video_or_audio_or_dispatch_produced':False}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert code==0 and not delta
why16='T1没加信息：仅按用户指定补fetched重点，原小字与全部正文保持原文。T3词性：fetched为动词过去式，portfolio名词、consortium和buyers名词、giants名词保持原注。T6不生硬：中文沿用以约5.25亿美元卖给，按用户要求只标以和卖给，金额普通。T7通顺：分隔标记只服务词色，连读语序完整。T8看得懂：主体为专利组合，以指定价钱卖给十二家买家组成的财团，原小字fetch卖得价钱解释逐字保持。T21贴合语境：fetched在此指卖得该价钱，保原译法和用户点名分隔两处高亮。'
why17='T1没加信息：只补bankruptcy破产重点，原left bankruptcy小字不变。T3词性：bankruptcy为名词破产；reorganisation名词、once-mighty形容词、downsized和streamlined及refocused as过去分词、printer和clients名词保持原注。T6不生硬：沿用柯达于2013年9月走出破产，left和走出保持普通。T7通顺：原中文全句语序逐字保持。T8看得懂：19个月改组后柯达走出破产，缩小并精简业务，转做面向企业客户的商业印刷。T21贴合语境：bankruptcy指公司的破产状态，标破产准确，原说明沿用。'
why19='T1没加信息：末句与已验43543967031源原文相同，原五点简述逐字沿用，当前只是同一内容机器折行前后需分别绑定。T3词性：medal为奖章名词，the end of为终结名词结构，原重点标记准确。T6不生硬：中文沿用那枚奖章颁发的同年，柯达也宣布胶卷终结。T7通顺：主句中文语序与已验源一致。T8看得懂：说明指出以时间作主语，读者能理解同年出现的两件事。T21贴合语境：medal和the end of都沿用原文词义。T33简述讲全：先机、牵制、衰退、重组、反差五点依次讲第一台数码相机、胶卷利润牵制、转型迟缓破产、贷款与专利出售重组、获奖与停产胶卷的反差；事实、段次、已验128px画面内容全部保留。'
confirmation=[]
for si,why in [(16,why16),(17,why17),(19,why19)]:
 rc,stdout=P.execute([sys.executable,T/'逐句确认.py','36',f'S{si}',why],W,env,OUT/f'original-sentence-confirmation-S{si}.log');assert rc==0
 confirmation.append({'sentence':si,'exit':rc,'conclusion':why})
rec=M/'视频/制作记录/逐句确认/36.json';report['original_sentence_confirmation']={'user_changed_sentences':[16,17],'unchanged_summary_machine_wrap_binding_sentence':19,'records':confirmation,'before_mechanical_wrap_record_sha256':sha(rec)}
raw,rawtext=P.execute([sys.executable,T/'踩坑核查.py','36','出片'],W,env,OUT/'original-text-before-repair.log')
repair,_=P.execute([sys.executable,T/'新管/修.py','36'],W,env,OUT/'original-mechanical-repair.log')
actual=json.loads(workjson.read_text());shutil.copyfile(workjson,OUT/'36-original-auto-repaired.json')
rc,_=P.execute([sys.executable,T/'逐句确认.py','36','S19',why19],W,env,OUT/'original-sentence-confirmation-S19-after-mechanical-wrap.log');assert rc==0
dest=C/'视频/制作记录/逐句确认/36.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(rec,dest);report['original_sentence_confirmation']['after_mechanical_wrap_record_sha256']=sha(rec)
final,finaltext=P.execute([sys.executable,T/'踩坑核查.py','36','出片'],W,env,OUT/'original-text-after-repair.log')
report.update(original_text_before_repair_exit=raw,original_repair_exit=repair,original_text_after_repair_exit=final,original_text_hard_errors=[l for l in finaltext.splitlines()if l.strip().startswith('✘')],original_pending_confirmations=[l for l in finaltext.splitlines()if l.strip().startswith('？')],original_mechanical_repair_differences=P.differences(candidate,actual),original_core_after_sha256={p:sha(M/p)for p in P.CORE_FILES},candidate_source_unchanged=sha(C/'视频/脚本/36.json')==before)
report['passed']=report['whole_JSON_roundtrip_exact']and raw==repair==final==0 and report['original_core_before_sha256']==report['original_core_after_sha256']and report['candidate_source_unchanged']
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'GEN_exact':report['whole_JSON_roundtrip_exact'],'text_before':raw,'text_after':final,'report_sha256':sha(OUT/'report.json')},ensure_ascii=False));sys.exit(0 if report['passed']else 1)
