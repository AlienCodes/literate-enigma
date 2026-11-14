"""Real unchanged original GEN/text gates in an isolated RAM mirror, no sound/video."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys,subprocess,base64,urllib.parse
B=Path('/workspace/work/video-audit70-20261113');H=Path(__file__).parent;C=H/'candidate-payload';BASE=B/'preflight-frozen66-v2-part1/mirror';V=H/'thin-validation-v2-root-selected';M=V/'mirror';W=M/'_text-work16';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('P16',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
if not M.exists():
 (M/'视频').mkdir(parents=True);shutil.copytree(Path('/dev/shm/article19-user-review-draft-20261114/thin-validation-v1/mirror/视频/工具'),M/'视频/工具',copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 shutil.copytree(BASE/'新版定稿',M/'新版定稿');(M/'视频/制作记录').mkdir();(M/'视频/脚本').mkdir();W.mkdir();(W/'scripts').mkdir();(W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True);q=M/'视频/资源/字体';q.parent.mkdir(parents=True);q.symlink_to(M/'视频/工具/fonts',target_is_directory=True)
 for p in BASE.glob('*.md'):shutil.copyfile(p,M/p.name)
for root in [BASE,B/'payload']:
 for p in(root/'视频/制作记录').glob('*'):
  if p.is_file()and p.suffix in('.md','.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
 for p in(root/'视频').glob('*.md'):shutil.copyfile(p,M/'视频'/p.name)
 for p in(root/'新版定稿').glob('*.md'):shutil.copyfile(p,M/'新版定稿'/p.name)
 for p in(root/'视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(p,M/'视频/脚本'/p.name);shutil.copyfile(p,W/'scripts'/p.name)
for rel in ['视频/脚本/16.json','视频/工具/初稿生成/gen16.py','新版定稿/16-the-bread-made-from-air.md','视频/工具/用户同意记录.json','视频/制作记录/16_待改清单.md']:
 (M/rel).unlink(missing_ok=True);shutil.copyfile(C/rel,M/rel)
# The old latest-published book42 was the actual646210 legacy MP4, not a passed
# current48 native. Bind L13 to that pin's original snapshot without skip flags.
snapshot=H/'actual-published-646210-source/16.json';snapshot.parent.mkdir(exist_ok=True)
if not snapshot.exists():
 rel='视频/脚本/已发版本/16.json';endpoint='repos/alienalgorithm/postgraduate-vocabulary/contents/'+urllib.parse.quote(rel,safe='/')+'?ref=64621068034f8b6e09836a6d97210a0e9b2f1ed6';raw=json.loads(subprocess.check_output(['gh','api',endpoint]));snapshot.write_bytes(base64.b64decode(raw['content']))
assert json.loads(snapshot.read_text())['no']=='16'
# Exact646210 GitHub source bytes are retained as actual previous published source.
dest=M/'视频/脚本/已发版本/16.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(snapshot,dest)
recsrc=B/'payload/视频/制作记录/逐句确认/16.json';recsrc=recsrc if recsrc.exists()else BASE/'视频/制作记录/逐句确认/16.json';record=M/'视频/制作记录/逐句确认/16.json';record.parent.mkdir(exist_ok=True);shutil.copyfile(recsrc,record)
fixture=BASE/'视频/对照文本/16-文本.docx';fc=M/'视频/对照文本/16-文本.docx';fc.parent.mkdir(exist_ok=True)
if fixture.exists():shutil.copyfile(fixture,fc);assert sha(fixture)==sha(fc)
# Original declared 文本 phase is the official video-only preflight and excludes
# only not-yet-generated comparison documents; no DOCX/PDF fixture is fabricated.
text_stage='文本'
logs=V/'logs';logs.mkdir(exist_ok=True);tmp=H/'temp-original-tools';tmp.mkdir(exist_ok=True);core={p:sha(M/p)for p in P.CORE_FILES};expected=json.loads((C/'视频/脚本/16.json').read_text());source_sha=sha(C/'视频/脚本/16.json');workjson=W/'scripts/16.json';workjson.unlink(missing_ok=True)
env={**os.environ,'TMPDIR':str(tmp),'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1','GIT_NO_LAZY_FETCH':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,_=P.execute([sys.executable,M/'视频/工具/初稿生成/gen16.py'],W,env,logs/'16-original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(expected,got);assert code==0 and not delta,(code,delta)
reasons={
'S15':'T1没加信息：用户135只要求Jewish犹太加重点，原身为犹太裔、哈伯离德到流亡逝世情节不增删。T3词性：Jewish形容词犹太人的/犹太的，画面按用户标犹太，原裔仍普通字与origin对应；outcast、regime、seized沿原。T6不生硬：身为犹太裔哈伯的原译不改。T7通顺：原Of Jewish origin背景到离开德国及dying结果完整。T8看得懂：原an outcast身份说明、after时间从句、dying结果状语小字保留。T21贴合语境：这里指犹太血统，不改成宗教信仰；拼写和英文原声无变，正确origin发音与普通next的六core新母原案不得回退。',
'S17':'T1没加信息：用户136仅把relatives亲属标重点，原死亡营及哈伯亲属去世叙述完整。T3词性：relatives为relative名词复数亲属，非此处相对的形容词；variant变体沿原。T6不生硬：他的一些亲属就死在那里原译不改。T7通顺：原where非限制性定语从句指死亡营。T8看得懂：原where和relatives of his小字完整保留。T21贴合语境：只写亲属而不编造具体人数/姓名，未改原史实。',
'S18':'T1没加信息：用户137指旧inline结局移除，最新请求已没有结局块，本轮不重复删除原EN/CN两块正文、两处grammar-note和独立原5点简述。T3词性：nitrogen氮、proteins蛋白质、passed through经过了沿原。T6不生硬：原人体蛋白质DNA氮与每人携带哈伯化学的译文完整。T7通顺：原因果so句完整。T8看得懂：原in our proteins and DNA后置定语、a little of Habers chemistry解释仍完整。T21贴合语境：化学贡献与战争遗产并存，最终版不能旧legacy充新。T33简述讲全：突破、养育、战争、命运、余波五点原文原序全部保留；仅独立summary2秒，原书16图2秒与最后读完0.6秒须新成片真核。'}
reviews=[]
for sid,why in reasons.items():
 rc,_=P.execute([sys.executable,M/'视频/工具/逐句确认.py','16',sid,why],W,env,logs/f'16-original-{sid}-review.log');assert rc==0;reviews.append(sid)
raw,txt=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','16',text_stage],W,env,logs/'16-original-text-before-repair.log');rc,_=P.execute([sys.executable,M/'视频/工具/新管/修.py','16'],W,env,logs/'16-original-repair.log');actual=json.loads(workjson.read_text());shutil.copyfile(workjson,V/'16-original-mechanical-repair-result.json')
for sid in ['S18']:
 pr,_=P.execute([sys.executable,M/'视频/工具/逐句确认.py','16',sid,reasons[sid]],W,env,logs/f'16-original-{sid}-post-mechanical-review.log');assert pr==0
last,lasttxt=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','16',text_stage],W,env,logs/'16-original-text-after-repair.log');out=C/'视频/制作记录/逐句确认/16.json';out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(record,out)
r={'source_id':'16','book_order':'45','kind':'original-tools-isolated-root-selected-actual-native16-metadata-and-display-timing-text-gates','original_stage':text_stage,'comparison_document_not_fabricated_or_generated':True,'source_sha256':source_sha,'GEN_sha256':sha(C/'视频/工具/初稿生成/gen16.py'),'MD_sha256':sha(C/'新版定稿/16-the-bread-made-from-air.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta,'original_text_before_repair_exit':raw,'original_repair_exit':rc,'original_text_after_repair_exit':last,'original_mechanical_repair_differences':P.differences(expected,actual),'hard_errors':[x for x in lasttxt.splitlines()if x.strip().startswith('✘')],'pending_confirmations':[x for x in lasttxt.splitlines()if x.strip().startswith('？')],'source_input_unchanged':sha(C/'视频/脚本/16.json')==source_sha,'core_before_sha256':core,'core_after_sha256':{p:sha(M/p)for p in P.CORE_FILES},'reviewed_sentences':reviews,'actual_published_source_baseline_for_L13':{'path':str(snapshot),'sha256':sha(snapshot),'pin':'64621068034f8b6e09836a6d97210a0e9b2f1ed6','legacy_role_recorded':True,'missing_snapshot_skip_not_used':True},'no_audio_video_PAY_CI_PDF_modified':True};r['passed']=code==raw==rc==last==0 and not delta and r['source_input_unchanged']and r['core_before_sha256']==r['core_after_sha256'];p=V/'report.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'GEN_exact':not delta,'text_before':raw,'repair':rc,'text_after':last,'hard_errors':r['hard_errors'],'pending':r['pending_confirmations'],'report':str(p),'sha256':sha(p)},ensure_ascii=False));sys.exit(0 if r['passed'] else 1)
