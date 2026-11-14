"""Article27 authorized nutrients focus only; preserve all sound controls."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
B=Path('/workspace/work/video-audit70-20261113');H=Path(__file__).parent;PAY=B/'payload';C=H/'candidate-payload'
mdrel=Path('新版定稿/27-life-in-the-forbidden-zone.md');rels=[Path('视频/脚本/27.json'),Path('视频/工具/初稿生成/gen27.py'),mdrel]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=load('original_source_encoder',B/'generator_text_preflight.py');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for rel in rels:
 p=H/'before'/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():shutil.copyfile(PAY/rel,p)
for rel in rels:(C/rel).parent.mkdir(parents=True,exist_ok=True)
if (B/'gen-sources/gen27.py').exists()and not(H/'before/gen-sources-gen27.py').exists():shutil.copyfile(B/'gen-sources/gen27.py',H/'before/gen-sources-gen27.py')
old=json.loads((H/'before/视频/脚本/27.json').read_text());new=copy.deepcopy(old);c=new['sentences'][13]['chunks'][1]
assert c['en']=='**impeding** the return of nutrients to the soil.'
c['en']=c['en'].replace('nutrients','**nutrients**');c['zh']=c['zh'].replace('养分','**养分**(nutrients)');c['align']=[[x.replace('nutrients','**nutrients**'),y.replace('养分','**养分**(nutrients)')]for x,y in c['align']]
assert c['en']==' '.join(x for x,y in c['align'])and c['zh']==''.join(y for x,y in c['align'])
new['allow_clash']=list(dict.fromkeys(new.get('allow_clash',[])+['nutrients']))
assert{k:v for k,v in old.items()if k not in('sentences','allow_clash')}=={k:v for k,v in new.items()if k not in('sentences','allow_clash')}
assert [[c['en'].replace('**','')for c in s['chunks']]for s in old['sentences']]==[[c['en'].replace('**','')for c in s['chunks']]for s in new['sentences']]
assert old['sentences'][-1]['chunks'][-1]['note']==new['sentences'][-1]['chunks'][-1]['note']
text,issues=P.pure_generator(new);assert text and not issues
(C/'视频/脚本/27.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');(C/'视频/工具/初稿生成/gen27.py').write_text(text)
md=(H/'before'/mdrel).read_text();head,tail=md.split('## 速查表',1)
for a,b in [('return of nutrients to','return of **nutrients** to'),('**阻碍了**(impeding)养分','**阻碍了**(impeding)**养分**(nutrients)')]:assert head.count(a)==1;head=head.replace(a,b)
lines=tail.splitlines();i=next(i for i,l in enumerate(lines)if l.startswith('| guarantee |'));lines.insert(i,'| nutrients | 本文：养分；n. (nutrient) 养分，营养物质（nutrients in the soil） | 4 |');md=head+'## 速查表'+'\n'.join(lines)+'\n';(C/mdrel).write_text(md)
auth=PAY/'视频/工具/用户同意记录.json';a=json.loads(auth.read_text());before=H/'before/用户同意记录.json'
if not before.exists():shutil.copyfile(auth,before)
q=next(r['原话']for r in a['记录']if r.get('篇')=='69'and'我清点的词'in r.get('原话',''));a['记录'].append({'篇':'27','日期':'2026-11-10','原话':q,'用于':'allow_clash.nutrients（2026-11-14 用户点名养分作为整词重点；既有reserves与其他篇重点保留）','来源':'用户2026-11-10对所有用户点名重点词的通用特批；本篇具体反馈USER-REVIEW-2026-11-14-007.json'})
rv=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-008.json');r=json.loads(rv.read_text());a['记录'].append({'篇':'27','日期':'2026-11-14','原话':r['user_instruction_verbatim'],'用于':'本篇审核完成后，认真核查整篇音轨及Another/A third词头、落实nutrients重点并重新出4K；其它篇仍按各自授权','来源':str(rv),'来源文件SHA256':sha(rv)})
(C/'视频/工具/用户同意记录.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
for i in [7,8]:
 p=Path('/workspace/work/first50-review-release')/f'USER-REVIEW-2026-11-14-{i:03}.json';out=H/'feedback'/p.name;out.parent.mkdir(exist_ok=True);shutil.copyfile(p,out)
rep={'article':'27','book_order':'22','candidate_source_sha256':sha(C/'视频/脚本/27.json'),'candidate_GEN_sha256':sha(C/'视频/工具/初稿生成/gen27.py'),'candidate_MD_sha256':sha(C/mdrel),'before_source_sha256':sha(H/'before/视频/脚本/27.json'),'English_spoken_and_chunk_boundaries_exact':True,'all_existing_audio_controls_exact':True,'original_summary_last_full_note_exact':True,'only_new_focus_and_named_clash_exemption':'nutrients/养分','diff':P.differences(old,new),'published_to_PAY':False}
(H/'proposal-report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in rep.items()if k!='diff'},ensure_ascii=False))
