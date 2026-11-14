"""Source28/book29: exact two authorized vocabulary reviews; no timing/sound change."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,shutil
B=Path('/workspace/work/video-audit70-20261113');H=Path(__file__).parent;PAY=B/'payload';C=H/'candidate-payload'
mdrel=Path('新版定稿/28-a-handful-of-wormwood-that-saved-millions.md');rels=[Path('视频/脚本/28.json'),Path('视频/工具/初稿生成/gen28.py'),mdrel]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=load('source_data_encoder',B/'generator_text_preflight.py');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for rel in rels:
 p=H/'before'/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():shutil.copyfile(PAY/rel,p)
 (C/rel).parent.mkdir(parents=True,exist_ok=True)
old=json.loads((H/'before/视频/脚本/28.json').read_text());new=copy.deepcopy(old)
c=new['sentences'][0]['chunks'][1];assert c['en']=='was named after its launch date, 23 May 1967.'
c['en']='**was named after** its launch date, 23 May 1967.';c['zh']='**得名于**(was named after)它的启动日期，1967年5月23日。';assert c['align'][:2]==[['was named','得名'],['after','于']];c['align']=[['**was named after**','**得名于**(was named after)']]+c['align'][2:]
c=new['sentences'][13]['chunks'][1];assert c['en']=='its **jury** credited the drug with saving millions.'
c['en']='its **jury** **credited** the drug **with** saving millions.';c['zh']='该奖的**评审团**(jury)**将**(credited with)挽救了数百万人的功劳**归功于**(credited with)这种药物。';c['align'][1]=['**credited** the drug **with** saving millions.','**将**(credited with)挽救了数百万人的功劳**归功于**(credited with)这种药物。']
new['核对确认'].setdefault('方向',{})['S1-2 after→得名于']='after属于完整be named after（以……命名），本句523项目得名于1967年5月23日启动日期，不是时间先后方向；用户030只得名于三字重点。'
new['核对确认'].setdefault('同词异译',{})['credited with：将/归功于']='不是两种译法：credit A with B的同一中文意思将B归功于A，被挽救了数百万人的功劳隔开；用户031明确只将与归功于两处同色，中间具体内容普通。'
new['allow_clash']=list(dict.fromkeys(new.get('allow_clash',[])+['was named after','credited','with']))
for s in new['sentences']:
 for c in s['chunks']:assert c['en']==' '.join(x for x,y in c['align'])and c['zh']==''.join(y for x,y in c['align'])
assert{k:v for k,v in old.items()if k not in('sentences','allow_clash','核对确认')}=={k:v for k,v in new.items()if k not in('sentences','allow_clash','核对确认')}
assert all(new['核对确认'].get(k)==v or k in('方向','同词异译')for k,v in old['核对确认'].items())
assert[[c['en'].replace('**','')for c in s['chunks']]for s in old['sentences']]==[[c['en'].replace('**','')for c in s['chunks']]for s in new['sentences']]
bare=lambda s:re.sub(r'\*\*([^*]+)\*\*\([^)]+\)',r'\1',s)
assert[[bare(c['zh'])for c in s['chunks']]for s in old['sentences']]==[[bare(c['zh'])for c in s['chunks']]for s in new['sentences']]
assert[[c.get('note')for c in s['chunks']]for s in old['sentences']]==[[c.get('note')for c in s['chunks']]for s in new['sentences']]
text,issues=P.pure_generator(new);assert text and not issues
(C/'视频/脚本/28.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');(C/'视频/工具/初稿生成/gen28.py').write_text(text)
md=(H/'before'/mdrel).read_text();head,tail=md.split('## 速查表',1)
for a,b in [('was named after its launch','**was named after** its launch'),('涉及多家机构，得名于它的','涉及多家机构，**得名于**(was named after)它的'),('its **jury** credited the drug with saving millions.','its **jury** **credited** the drug **with** saving millions.'),('该奖的**评审团**(jury)将挽救了数百万人的功劳归功于这种药物。','该奖的**评审团**(jury)**将**(credited with)挽救了数百万人的功劳**归功于**(credited with)这种药物。')]:assert head.count(a)==1;(head:=head.replace(a,b))
lines=tail.splitlines();i=next(i for i,l in enumerate(lines)if l.startswith('| urgent |'));lines.insert(i,'| was named after | 本文：得名于；v. phr. (be named after) 以……命名，得名于（be named after a person/date） | 1 |');i=next(i for i,l in enumerate(lines)if l.startswith('| Physiology |'));lines.insert(i,'| credited with | 本文：将……归功于；v. phr. (credit A with B) 把 B 的功劳归于 A，认为 B 是 A 的成就（credited the drug with saving millions） | 5 |');(C/mdrel).write_text(head+'## 速查表'+'\n'.join(lines)+'\n')
auth=PAY/'视频/工具/用户同意记录.json';a=json.loads(auth.read_text());shutil.copyfile(auth,H/'before/用户同意记录.json');q=next(r['原话']for r in a['记录']if r.get('篇')=='69'and'我清点的词'in r.get('原话',''))
a['记录'].append({'篇':'28','日期':'2026-11-10','原话':q,'用于':'allow_clash.was named after/credited/with（本轮用户明确点名两用法：was named after 整体仅得名于；credited/with同一不连续词组仅将/归功于；保其他篇既有重点）','来源':'2026-11-10用户对所有点名重点词通用特批；本篇USER-REVIEW-2026-11-14-030/031'})
rv=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-032.json');r=json.loads(rv.read_text());a['记录'].append({'篇':'28','日期':'2026-11-14','原话':r['user_instruction_verbatim'],'用于':'仅本篇4K效果试看，末句读完原最后正文保留九帧后图2秒、原简述2秒；包含030/031两词汇反馈；不覆盖旧active final、不扩大他篇。此数据candidate不改音频或时轴，停留由原pipeline另实施','来源':str(rv),'来源文件SHA256':sha(rv)});(C/'视频/工具/用户同意记录.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
for i in [30,31,32]:
 p=rv.parent/f'USER-REVIEW-2026-11-14-{i:03}.json';out=H/'feedback'/p.name;out.parent.mkdir(exist_ok=True);shutil.copyfile(p,out)
rep={'article':'28','book_order':'29','preview_only_original_active_final_preserved':True,'candidate_source_sha256':sha(C/'视频/脚本/28.json'),'candidate_GEN_sha256':sha(C/'视频/工具/初稿生成/gen28.py'),'candidate_MD_sha256':sha(C/mdrel),'before_source_sha256':sha(H/'before/视频/脚本/28.json'),'English_spoken_and_chunk_boundaries_exact':True,'bare_Chinese_text_and_order_exact':True,'all_notes_including_original_full_summary_exact':True,'all_existing_audio_controls_exact':True,'diff':P.differences(old,new),'published_to_PAY':False};(H/'proposal-report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in rep.items()if k!='diff'},ensure_ascii=False))
