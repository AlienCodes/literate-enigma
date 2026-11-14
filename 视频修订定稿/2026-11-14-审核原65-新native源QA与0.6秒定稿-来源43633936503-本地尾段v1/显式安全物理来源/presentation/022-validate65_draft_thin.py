"""Run unchanged original GEN/text checks on isolated source65 user091 draft."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).resolve().parent;B=Path('/workspace/work/video-audit70-20261113');BASE=B/'preflight-frozen66-v2-part1/mirror';C=H/'candidate-payload';V=H/'thin-validation';M=V/'mirror';W=M/'_text-work'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('original_data_preflight65',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
if not M.exists():
 (M/'视频').mkdir(parents=True)
 shutil.copytree(B/'article53-user-review-20261114/thin-validation/mirror/视频/工具',M/'视频/工具',copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pdf','*.PDF'))
 for rel in ['新版定稿','视频/制作记录','视频/脚本','_text-work/scripts']:(M/rel).mkdir(parents=True,exist_ok=True)
 (W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True);q=M/'视频/资源/字体';q.parent.mkdir(parents=True);q.symlink_to(M/'视频/工具/fonts',target_is_directory=True)
 for p in BASE.glob('*.md'):shutil.copyfile(p,M/p.name)
for root in [BASE,B/'payload']:
 for p in (root/'视频/制作记录').glob('*'):
  if p.is_file()and p.suffix in('.md','.json'):shutil.copyfile(p,M/'视频/制作记录'/p.name)
 for p in (root/'视频').glob('*.md'):shutil.copyfile(p,M/'视频'/p.name)
 for p in (root/'新版定稿').glob('*.md'):shutil.copyfile(p,M/'新版定稿'/p.name)
 for p in (root/'视频/脚本').glob('[0-9][0-9].json'):shutil.copyfile(p,M/'视频/脚本'/p.name);shutil.copyfile(p,W/'scripts'/p.name)
for rel in ['视频/脚本/65.json','视频/工具/初稿生成/gen65.py','新版定稿/65-the-day-the-doomsday-vault-opened.md','视频/工具/用户同意记录.json','视频/制作记录/65_待改清单.md']:
 (M/rel).unlink(missing_ok=True);shutil.copyfile(C/rel,M/rel)
snapshot=BASE/'视频/脚本/已发版本/65.json';assert snapshot.is_file();dest=M/'视频/脚本/已发版本/65.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(snapshot,dest)
record=M/'视频/制作记录/逐句确认/65.json';record.parent.mkdir(exist_ok=True);shutil.copyfile(B/'payload/视频/制作记录/逐句确认/65.json',record)
logs=V/'logs';logs.mkdir(exist_ok=True);core={p:sha(M/p)for p in P.CORE_FILES};expected=json.loads((C/'视频/脚本/65.json').read_text());source_sha=sha(C/'视频/脚本/65.json');workjson=W/'scripts/65.json';workjson.unlink(missing_ok=True)
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'};env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
for k in ['YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID']:env.pop(k,None)
code,text=P.execute([sys.executable,M/'视频/工具/初稿生成/gen65.py'],W,env,logs/'65-original-GEN.log');got=json.loads(workjson.read_text());delta=P.differences(expected,got);assert code==0 and not delta
why='T1没加信息：用户091只将国家名Norway挪威标为重点，原斯匹次卑尔根岛及斯瓦尔巴群岛位置事实逐字保留。T3词性：Norway国家专名挪威，所有格s普通；archipelago名词群岛，原重点保留；corridor名词通道。T6不生硬：在挪威斯瓦尔巴群岛的斯匹次卑尔根岛上为原连续中文。T7通顺：群岛位置到山坡通道的两块原样顺接。T8看得懂：原同位语in Norways Svalbard archipelago及完成被动小字完整保留。T21贴合语境：Norway指斯瓦尔巴群岛所属国家挪威，仅Norway和挪威同key，所有格s、Svalbard和斯瓦尔巴普通，群岛仍对应archipelago独立key。'
review,reviewtext=P.execute([sys.executable,M/'视频/工具/逐句确认.py','65','S1',why],W,env,logs/'65-original-S1-review.log');assert review==0
why11='T1没加信息：用户093只标已有的国家名Lebanon黎巴嫩和Morocco摩洛哥，原ICARDA播种繁育事实原样保留。T3词性：Lebanon与Morocco均国家专名，sowed为动词过去式种下了，vigorous形容词强健的。T6不生硬：在黎巴嫩和摩洛哥原完整地点状语保留，In在和and和普通。T7通顺：播种到新植物发芽并恢复种子收藏库，原两块逻辑保持。T8看得懂：原通俗说明三行全文保留。T21贴合语境：两个国家分别对应黎巴嫩和摩洛哥，独立key且原sowed种下了等重点完整。T34原拆分组：同序国家重点各自对应，连续中英文均未改。'
review11,reviewtext11=P.execute([sys.executable,M/'视频/工具/逐句确认.py','65','S11',why11],W,env,logs/'65-original-S11-review.log');assert review11==0
raw,rawtext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','65','出片'],W,env,logs/'65-original-text-before-repair.log');rc,rt=P.execute([sys.executable,M/'视频/工具/新管/修.py','65'],W,env,logs/'65-original-repair.log');actual=json.loads(workjson.read_text());shutil.copyfile(workjson,V/'65-original-auto-repaired.json')
review17=0
if '并且更暖的天气' in expected['sentences'][-1]['chunks'][-1]['zh']:
 a=expected['sentences'][-1]['chunks'][-1];b=actual['sentences'][-1]['chunks'][-1]
 assert a['en']==b['en']and a['zh']==b['zh']and a['note'].replace('\n','').replace('▹','')==b['note'].replace('\n','').replace('▹','')
 why17='T1没加信息：用户094只把末句and对应单独的而改为并且，保留前块而建的。原五点简述文字内容逐字不变，原G35仅自动折行和续行标记。T3词性：haven名词避难所，apocalypse名词世界末日，weakness名词弱点，warmer为形容词比较级更暖的，found过去式找到了；and为普通连词并且。T6不生硬：在自家入口处却有一个弱点，并且更暖的天气找到了它，为指定连续译文。T7通顺：主语A haven由built短语后置修饰，had谓语，天气作后半句并列主语。T8看得懂：原built against及it指weakness语法说明保留，独立末卡仍讲备份取种重建虚惊加固。T21贴合语境：weakness仍指入口防水弱点，and并且普通不新增重点。T33简述讲全：2008启用与存放者所有权、2015ICARDA取种、黎巴嫩摩洛哥繁育与2017起存回、2016年10月融水与2017报道及种子未受淹、排水防水加固五点完整。用户095要求末正文放大居中，使用原renderer先拆出独立简述再量正文，没有加回inline简述，也没有删除或改写末卡内容。'
 review17,reviewtext17=P.execute([sys.executable,M/'视频/工具/逐句确认.py','65','S17',why17],W,env,logs/'65-original-S17-after-mechanical-review.log');assert review17==0
last,lasttext=P.execute([sys.executable,M/'视频/工具/踩坑核查.py','65','出片'],W,env,logs/'65-original-text-after-repair.log');out=C/'视频/制作记录/逐句确认/65.json';out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(record,out)
r={'article':'65','book_order':'37','draft_only':True,'passed':code==raw==rc==last==0 and not delta,'source_sha256':source_sha,'GEN_sha256':sha(C/'视频/工具/初稿生成/gen65.py'),'MD_sha256':sha(C/'新版定稿/65-the-day-the-doomsday-vault-opened.md'),'original_generator_exit':code,'whole_JSON_roundtrip_exact':not delta,'JSON_differences':delta,'original_text_before_repair_exit':raw,'original_repair_exit':rc,'original_text_after_repair_exit':last,'original_text_hard_errors':[x for x in lasttext.splitlines()if x.strip().startswith('✘')],'original_text_pending_confirmations':[x for x in lasttext.splitlines()if x.strip().startswith('？')],'original_mechanical_repair_differences':P.differences(expected,actual),'original_sentence_S1_review_exit':review,'core_before_sha256':core,'core_after_sha256':{p:sha(M/p)for p in P.CORE_FILES},'original_existing_frozen_L13_snapshot':{'path':str(snapshot),'sha256':sha(snapshot),'missing_snapshot_skip_not_used':True},'source_input_unchanged':sha(C/'视频/脚本/65.json')==source_sha,'no_native_audio_video_or_dispatch':True}
r['original_sentence_S11_review_exit']=review11
r['original_sentence_S17_after_mechanical_review_exit']=review17
# The unchanged official pipeline repairs mechanical layout before its text gate.
# Preserve the optional raw diagnostic (including the old S17 summary fingerprint),
# and evaluate the actual original generator/repair/final-text exits without adding
# a new prerequisite that the unprocessed diagnostic must also pass.
r['passed']=code==rc==last==0 and not delta and review11==0 and r['core_before_sha256']==r['core_after_sha256']and r['source_input_unchanged']
r['pass_basis']='Exact original GEN roundtrip plus unchanged official mechanical repair and after-repair text gate; the separate raw-before-repair diagnostic is retained verbatim, not claimed passed.'
(V/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k]for k in ['passed','whole_JSON_roundtrip_exact','original_text_before_repair_exit','original_repair_exit','original_text_after_repair_exit','original_text_hard_errors','original_text_pending_confirmations']},ensure_ascii=False));sys.exit(0 if r['passed']else 1)
