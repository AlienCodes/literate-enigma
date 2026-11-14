from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
B=Path('/workspace/work/video-audit70-20261113');H=Path('/dev/shm/article40-user139140-draft-20261114');C=H/'candidate-payload';BASE=B/'preflight-frozen66-v2-part1/mirror';V=H/'independent-thin-validation';M=V/'mirror';W=M/'_text-work40';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();s=importlib.util.spec_from_file_location('P',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
if not M.exists():
 (M/'视频').mkdir(parents=True);shutil.copytree(Path('/dev/shm/article52-user120124-final-20261114/thin-validation-v1/mirror/视频/工具'),M/'视频/工具',copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'));shutil.copytree(BASE/'新版定稿',M/'新版定稿');(M/'视频/制作记录').mkdir();(M/'视频/脚本').mkdir();W.mkdir();(W/'scripts').mkdir();(W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True);q=M/'视频/资源/字体';q.parent.mkdir(parents=True);q.symlink_to(M/'视频/工具/fonts',target_is_directory=True)
 for p in BASE.glob('*.md'):shutil.copyfile(p,M/p.name)
for root in [BASE,B/'payload']:
 for p in (root/'视频/制作记录').glob('*'):
  if p.is_file() and p.suffix in('.md','.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
 for p in (root/'视频').glob('*.md'):shutil.copyfile(p,M/'视频'/p.name)
 for p in (root/'新版定稿').glob('*.md'):shutil.copyfile(p,M/'新版定稿'/p.name)
 for p in (root/'视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(p,M/'视频/脚本'/p.name);shutil.copyfile(p,W/'scripts'/p.name)
for rel in ['视频/脚本/40.json','视频/工具/初稿生成/gen40.py','新版定稿/40-the-glue-that-failed.md']:
 (M/rel).unlink(missing_ok=True);shutil.copyfile(C/rel,M/rel)
authpath=M/'视频/工具/用户同意记录.json';authpath.unlink(missing_ok=True);shutil.copyfile(B/'payload/视频/工具/用户同意记录.json',authpath);auth=json.loads(authpath.read_text());authority=[]
for no in (139,140,142,144):
 p=Path('/dev/shm/archive-writer-user-review-20261114')/f'USER-REVIEW-2026-11-14-{no:03d}.json'
 if not p.exists():continue
 d=json.loads(p.read_text());quote=d.get('user_instruction_verbatim');assert quote and d['source_id']=='40';auth['记录'].append({'篇':'40','日期':'2026-11-14','原话':quote,'用于':'用户'+str(no)+'本篇审核落地与定稿授权' if no==144 else '用户'+str(no)+'指定页面的文字/小字修改','来源':str(p)});authority.append({'record':no,'path':str(p),'sha256':sha(p),'quote':quote})
authpath.write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
pending=M/'视频/制作记录/40_待改清单.md';basepending=B/'payload/视频/制作记录/40_待改清单.md'
if not basepending.exists():basepending=BASE/'视频/制作记录/40_待改清单.md'
if basepending.exists():shutil.copyfile(basepending,pending)
with pending.open('a') as f:
 f.write('\n\n## 2026-11-14 用户139/140/142最新审核，原历史保留\n')
 f.write('用户139只替换S6 without a problem语法解释，保solution定义；落地小字：`他发明的这种胶当时还找不到合适的用途。“有方案却没问题”，是说发明已经有了，实际用途却还没找到。`\n')
 f.write('用户140 S11译文：`这种**懊恼**(frustration)给了弗莱一个主意。` 原英文与give sb an idea说明完整。\n')
 f.write('用户142 S19原next door注后新增：`便利贴最初用黄色纸，是因为当时隔壁实验室恰好只有剩下的黄纸。后来，黄色成了便利贴的标志性颜色。` 原独立五点简述保持。\n')
 for x in authority:f.write('用户'+str(x['record'])+'原话：'+x['quote']+'\n')
snapshot=H/'before/视频/脚本/40.json';assert sha(snapshot)=='df869484faa5bfaeebf4ebc2648be395682d653edc896238c08ee8e4730891f1';dest=M/'视频/脚本/已发版本/40.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(snapshot,dest)
recordsrc=B/'payload/视频/制作记录/逐句确认/40.json';recordsrc=recordsrc if recordsrc.exists() else BASE/'视频/制作记录/逐句确认/40.json';record=M/'视频/制作记录/逐句确认/40.json';record.parent.mkdir(exist_ok=True);shutil.copyfile(recordsrc,record)
logs=V/'logs';logs.mkdir(exist_ok=True);tmp=H/'tmp-original-tools-independent';tmp.mkdir(exist_ok=True);core={p:sha(M/p) for p in P.CORE_FILES};expected=json.loads((C/'视频/脚本/40.json').read_text());source_sha=sha(C/'视频/脚本/40.json');GEN_sha=sha(C/'视频/工具/初稿生成/gen40.py');MD_sha=sha(C/'新版定稿/40-the-glue-that-failed.md');assert source_sha=='44d850a163dd06814282c9728b62aa79d069c912b3f91bdfab69945fc9392ba7';workjson=W/'scripts/40.json';workjson.unlink(missing_ok=True);env={**os.environ,'TMPDIR':str(tmp),'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,_=P.execute([sys.executable,M/'视频/工具/初稿生成/gen40.py'],W,env,logs/'40-original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(expected,got);assert code==0 and not delta
reasons={'S6':'T1没加信息：用户139接受解释方案，只替截图without a problem的语法说明，原solution解决方案定义和英文原句保持。T3词性：summary名词总结，solution名词方案；原重点解决和方案保持同一词key。T6不生硬：原用他自己的话总结、解决不存在的问题的方案与通俗解释相互说明。T7通顺：说明他发明的胶已有但当时缺合适用途，不矛盾也不增研发事实。T8看得懂：有方案却没问题表示暂缺用途，完整保留用户接受说明。T21贴合语境：problem指待解决的实际问题，并非说明方案完美。', 'S11':'T1没加信息：用户140精确译文这种懊恼给了弗莱一个主意，原英文The frustration gave Fry an idea保留，未加新的行动或因果。T3词性：frustration名词懊恼，gave为give过去式给，idea名词主意。T6不生硬：这种懊恼给了弗莱一个主意依用户指定自然通顺。T7通顺：这种回指书签滑落带来的懊恼，后文用胶水固定书签顺接。T8看得懂：原give sb an idea说明完整保留，英文重点frustration与懊恼对应准确。T21贴合语境：只将原译换为用户句子，弗莱并未收到实体礼物。', 'S19':'T1没加信息：用户142接受便利贴黄色缘由说明，唯一放The laboratory next door所在最后正文页，原next door语法注和独立详细五点简述保持全文。T3词性：leftover形容词剩余的，yellow形容词黄色的，paper名词纸。T6不生硬：原因为当时隔壁的实验室里只有一些剩余的黄纸与新增解释衔接自然。T7通顺：新增第二句说明黄色后来成了标志性颜色，原上市简述保持。T8看得懂：原next door说明完整，新增小字解释现成黄纸而非设计师刻意选择。T21贴合语境：全部新增字句来自用户142已接受说明，没有推导新的实验或营销细节。T33简述讲全：原意外、用途、冷遇、转机、上市五点字句完整保留。'}
for sid,why in reasons.items():
 rc,_=P.execute([sys.executable,M/'视频/工具/逐句确认.py','40',sid,why],W,env,logs/f'40-original-{sid}-review.log');assert rc==0
raw,txt=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','40','出片'],W,env,logs/'40-original-text-before-repair.log');rc,_=P.execute([sys.executable,M/'视频/工具/新管/修.py','40'],W,env,logs/'40-original-repair.log');actual=json.loads(workjson.read_text());shutil.copyfile(workjson,V/'40-actual-original-mechanical-result.json')
for sid,why in reasons.items():
 pr,_=P.execute([sys.executable,M/'视频/工具/逐句确认.py','40',sid,why],W,env,logs/f'40-original-{sid}-post-repair-review.log');assert pr==0
last,lasttxt=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','40','出片'],W,env,logs/'40-original-text-after-repair.log')
r=dict(source_id='40',book_order='46',source_sha256=source_sha,GEN_sha256=GEN_sha,MD_sha256=MD_sha,original_generator_exit=code,whole_JSON_roundtrip_exact=not delta,original_text_before_repair_exit=raw,original_repair_exit=rc,original_text_after_repair_exit=last,actual_original_mechanical_differences=P.differences(expected,actual),hard_errors=[x for x in lasttxt.splitlines() if x.strip().startswith('✘')],pending_confirmations=[x for x in lasttxt.splitlines() if x.strip().startswith('？')],core_before_sha256=core,core_after_sha256={p:sha(M/p) for p in P.CORE_FILES},actual_latest_accepted_snapshot_for_L13=dict(path=str(snapshot),sha256=sha(snapshot),historical_ROOT_snapshot_not_claimed=True,missing_fixture_not_skipped=True),scoped_user_authority_records=authority,candidate_three_source_files_unchanged=source_sha==sha(C/'视频/脚本/40.json') and GEN_sha==sha(C/'视频/工具/初稿生成/gen40.py') and MD_sha==sha(C/'新版定稿/40-the-glue-that-failed.md'),actual_updated_sentence_reasons_only_local_mirror=True,new_audio_native_or_media_acceptance_not_claimed=True,PAY_CI_remote_PDF_unchanged=True)
r['passed']=code==raw==rc==last==0 and not delta and r['candidate_three_source_files_unchanged'] and r['core_before_sha256']==r['core_after_sha256'];out=V/'independent-original-GEN-fulltext-report.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(passed=r['passed'],GEN_exact=not delta,text_before=raw,text_after=last,mechanical_differences=r['actual_original_mechanical_differences'],report=str(out),sha256=sha(out)),ensure_ascii=False));sys.exit(0 if r['passed'] else 1)
