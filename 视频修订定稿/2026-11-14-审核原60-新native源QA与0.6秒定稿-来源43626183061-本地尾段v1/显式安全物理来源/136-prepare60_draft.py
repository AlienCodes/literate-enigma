"""Only authorized062–069 isolated manuscript draft; never install PAY/CI or produce video."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
B=Path('/workspace/work/video-audit70-20261113');H=Path(__file__).parent;PAY=B/'payload';RAM=Path('/dev/shm/article60-text-review-draft-20261114');RAM.mkdir(exist_ok=True)
for name in ['before','candidate-payload','thin-validation','static-1080','static-4K']:
 (RAM/name).mkdir(exist_ok=True)
 if not(H/name).exists():(H/name).symlink_to(RAM/name,target_is_directory=True)
C=H/'candidate-payload';mdrel=Path('新版定稿/60-the-scientific-giant-who-changed-the-world.md');actualMD=Path('/workspace/work/video-revision-delivery/next-passed-validated/43543967031/60/final-source')/mdrel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for rel in ['视频/脚本/60.json','视频/工具/初稿生成/gen60.py','视频/制作记录/60_待改清单.md']:
 src=PAY/rel
 if src.is_file():
  dest=H/'before'/rel;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();shutil.copyfile(src,dest)
p=H/'before'/mdrel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();shutil.copyfile(actualMD,p);assert sha(p)=='e44790a371772e2980ebf33e543eb05189df463f6000a25d7f4af59eeff5277b'
old=json.loads((H/'before/视频/脚本/60.json').read_text());assert sha(H/'before/视频/脚本/60.json')=='eed1655c0919db32a3a016b24791b93d25683f287c7ccb2523e168a69bddc562';new=copy.deepcopy(old)
c=new['sentences'][0]['chunks'][1];c['align'][-1][0]=c['align'][-1][0].replace('apparent','**apparent**');c['align'][-1][1]=c['align'][-1][1].replace('看似','**看似**(apparent)')
c=new['sentences'][1]['chunks'][1];c['align'][-1][0]=c['align'][-1][0].replace('Brazil','**Brazil**');c['align'][-1][1]=c['align'][-1][1].replace('巴西','**巴西**(Brazil)')
c=new['sentences'][2]['chunks'][1];assert c['align'][-1][1]=='会使经过它附近的星光**偏折**(deflect)。';c['align'][-1][1]='会**使**(deflect)星光**偏折/偏离方向**(deflect)。'
c=new['sentences'][3]['chunks'][0];assert c['en'].count('Royal')==2;c['align'][-1][0]=c['align'][-1][0].replace('Royal','**Royal**');assert c['align'][-1][1].count('皇家')==2;c['align'][-1][1]=c['align'][-1][1].replace('皇家','**皇家**(Royal)')
c=new['sentences'][3]['chunks'][1];assert c['align'][0][1]=='观测**结果**(findings)';c['align'][0][1]='其观测**结果**(findings)'
accepted='1919年11月6日，日食观测结果在两学会的联席会议上公布，人们认为它支持了爱因斯坦的预言：太阳引力会使星光偏折。'
wrapped='1919年11月6日，日食观测结果在两学会的联席会议上公布，\n人们认为它支持了爱因斯坦的预言：\n太阳引力会使星光偏折。';assert wrapped.replace('\n','')==accepted;c['note']+='\n（'+wrapped+'）'
c=new['sentences'][4]['chunks'][0];c['align'][-1][0]=c['align'][-1][0].replace('Revolution','**Revolution**');c['align'][-1][1]=c['align'][-1][1].replace('革命','**革命**(Revolution)')
c=new['sentences'][4]['chunks'][1];c['align'][-1][0]=c['align'][-1][0].replace('Askew','**Askew**');c['align'][-1][1]=c['align'][-1][1].replace('歪了','**歪了**(Askew)')
c=new['sentences'][5]['chunks'][1];assert c['align'][1][1]=='举世皆知的';c['align'][1][1]='一位全球性的'
modified=[(1,2),(2,2),(3,2),(4,1),(4,2),(5,1),(5,2),(6,2)]
for si,ci in modified:
 c=new['sentences'][si-1]['chunks'][ci-1];c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
assert new['sentences'][9]==old['sentences'][9],'Royal Swedish Academy ordinary occurrence is outside065 screenshot scope'
new['allow_clash']=['apparent','Brazil','Royal','Revolution','Askew'];new['核对确认']['同词异译']['deflect：使/偏折/偏离方向']='不是两种译法：deflect 的完整本文义为使……偏折/偏离方向，中文使和偏折/偏离方向被星光隔开，是同一使动谓语的两部分（T23）；用户064明确指定此完整译文和两处同key标注。'
for a,b in zip(old['sentences'],new['sentences']):
 assert a['para']==b['para']and len(a['chunks'])==len(b['chunks'])
 for x,y in zip(a['chunks'],b['chunks']):assert x['en'].replace('**','')==y['en'].replace('**','')and len(x['align'])==len(y['align'])
assert{k:v for k,v in old.items()if k not in ['sentences','核对确认']}=={k:v for k,v in new.items()if k not in ['sentences','核对确认','allow_clash']}
for rel in ['视频/脚本/60.json','视频/工具/初稿生成/gen60.py',str(mdrel),'视频/工具/用户同意记录.json']:(C/rel).parent.mkdir(parents=True,exist_ok=True)
s=importlib.util.spec_from_file_location('original60_encoder',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P);code,issues=P.pure_generator(new);assert code and not issues;(C/'视频/脚本/60.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');(C/'视频/工具/初稿生成/gen60.py').write_text(code)
md=(H/'before'/mdrel).read_text()
for si,ci in modified:
 a=old['sentences'][si-1]['chunks'][ci-1];b=new['sentences'][si-1]['chunks'][ci-1]
 for field in ['en','zh']:
  if a[field]!=b[field]:assert md.count(a[field])==1,(si,ci,field);md=md.replace(a[field],b[field],1)
oldnote=old['sentences'][3]['chunks'][1]['note'].replace('\n','');assert md.count(oldnote)==1;md=md.replace(oldnote,oldnote+'（'+accepted+'）',1)
assert md.count('| deflect | 本文：偏折；')==1;md=md.replace('| deflect | 本文：偏折；','| deflect | 本文：使……偏折/偏离方向；',1)
additions=[('vicinity','| apparent | 本文：看似；adj. 表面上的，看起来的；明显的（apparent to sb） | 1 |'),('general relativity','| Brazil | 本文：巴西；n. 巴西（国家名） | 1 |'),('findings','| royal | 本文：皇家；adj. 皇家的，王室的（the Royal Society 皇家学会） | 2 |'),('headline','| Revolution | 本文：革命；n. 革命，重大变革；（天体）公转 | 2 |'),('overnight','| Askew | 本文：歪了；adj. 歪斜的，不正的（标题中作表语）；adv. 歪斜地，偏离正确方向地 | 2 |')]
for anchor,row in additions:
 assert row.split('|')[1].strip().lower()not in [line.split('|')[1].strip().lower()for line in md.splitlines()if line.startswith('|')and len(line.split('|'))>2];assert md.count('| '+anchor+' |')==1;md=md.replace('| '+anchor+' |',row+'\n| '+anchor+' |',1)
(C/mdrel).write_text(md)
auth=json.loads((PAY/'视频/工具/用户同意记录.json').read_text());feedback=[]
for n in range(62,70):
 p=Path('/workspace/work/first50-review-release')/f'USER-REVIEW-2026-11-14-{n:03}.json';r=json.loads(p.read_text());assert r['source_id']=='60'and r['book_order']=='36';feedback.append(dict(path=str(p),sha256=sha(p)));auth['记录'].append({'篇':'60','日期':'2026-11-14','原话':r['user_instruction_verbatim'],'用于':f'用户{n:03}本篇指定修改仅落实隔离草稿和静态效果核查；点名词apparent/Brazil/两处Royal/Revolution/Askew允许撞词，原vicinity/findings/proclaimed/headline/celebrity重点保留；066说明按067加在S4页且保原grammar。尚未获得36定稿/视频生成授权，不调用做或定稿，不改远端别名/生产PAY/CI/音频/PDF。','来源文件':str(p),'来源文件SHA256':sha(p)})
(C/'视频/工具/用户同意记录.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
work=H/'before/视频/制作记录/60_待改清单.md';out=C/'视频/制作记录/60_待改清单.md';out.parent.mkdir(parents=True,exist_ok=True);text=work.read_text()if work.exists()else'';text+='\n\n## 2026-11-14 用户062–069：仅隔离草稿编辑\n\n按记录逐项落实apparent看似、Brazil巴西、deflect使……偏折/偏离方向、S4两处Royal皇家、其观测结果、066原文说明、Revolution革命、Askew歪了、成了一位全球性的名人。原裸EN/chunk/align索引/全部声控保持，S10 Royal Swedish普通不扩展。原grammar/详细五点简述保留。仅JSON/GEN/MD隔离草稿与双分辨率静态，未定稿，不生成或替换视频、PAY/CI、远端别名或PDF。\n';out.write_text(text)
r=dict(article='60',book_order='36',draft_only=True,final_or_native_authorized=False,PAY_CI_remote_alias_audio_PDF_unchanged=True,before_source_sha256=sha(H/'before/视频/脚本/60.json'),candidate_source_sha256=sha(C/'视频/脚本/60.json'),candidate_GEN_sha256=sha(C/'视频/工具/初稿生成/gen60.py'),candidate_MD_sha256=sha(C/mdrel),actual_used_MD_basis=dict(path=str(actualMD),sha256=sha(actualMD),PAY_MD_missing=True),accepted_note_exact=accepted,note_linebreaks_only_for_comfort=True,old_S4_grammar_preserved=True,S10_unrequested_Royal_ordinary_exact=True,all_bare_English_chunks_and_control_indices_exact=True,all_effective_audio_controls_exact=True,original_last_summary_note_exact=old['sentences'][-1]==new['sentences'][-1],feedback=feedback,diff=P.differences(old,new))
(H/'draft-proposal-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['feedback','diff']},ensure_ascii=False))
