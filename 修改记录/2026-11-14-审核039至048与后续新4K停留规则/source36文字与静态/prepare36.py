"""Only the two explicitly approved Kodak focus changes; original voice untouched."""
import copy,datetime,hashlib,importlib.util,json,re,shutil
from pathlib import Path
B=Path('/workspace/work/video-audit70-20261113');PAY=B/'payload';H=Path(__file__).parent;C=H/'candidate-payload';BEFORE=H/'before'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
rels=['视频/脚本/36.json','视频/工具/初稿生成/gen36.py','新版定稿/36-the-company-that-invented-its-own-killer.md','视频/制作记录/36_待改清单.md','视频/工具/用户同意记录.json']
states={}
for rel in rels:
 p=PAY/rel;states[rel]={'exists':p.exists(),'sha256':sha(p)if p.exists()else None}
 if p.exists():
  q=BEFORE/rel;q.parent.mkdir(parents=True,exist_ok=True)
  if not q.exists():shutil.copyfile(p,q)
  q=C/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
# A prior safe mirror cleanup left no PAY36 manuscript. Restore from the actual
# accepted run's used manuscript, preserving that video's detailed five points.
assert not states[rels[2]]['exists']
mdsource=B/'next-passed-native/43543967031/36/artifact-files/36-actual-working-manuscript.md'
assert sha(mdsource)=='9a3b61748583feb80594d042c0df5379452924efd9556b532435cf453540cc55'
for base in [BEFORE,C]:
 p=base/rels[2];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(mdsource,p)
states[rels[2]].update(restored_from_actual_accepted_run_manuscript=str(mdsource),restored_sha256=sha(mdsource))
genbase=B/'gen-sources/gen36.py';states['gen-sources/gen36.py']={'exists':genbase.exists(),'sha256':sha(genbase)if genbase.exists()else None}
if genbase.exists():shutil.copyfile(genbase,BEFORE/'gen-sources-gen36.py')
(BEFORE/'baseline-states.json').write_text(json.dumps(states,ensure_ascii=False,indent=2)+'\n')
old=json.loads((BEFORE/rels[0]).read_text());new=copy.deepcopy(old)
c=new['sentences'][15]['chunks'][1]
assert c['align'][0]==['fetched about $525 million','以约5.25亿美元卖给']
c['align'][0]=['**fetched** about $525 million','**以**(fetched)约5.25亿美元**卖给**(fetched)']
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
c=new['sentences'][16]['chunks'][0]
assert c['align'][-1]==['left bankruptcy in September 2013,','于2013年9月走出破产，']
c['align'][-1]=['left **bankruptcy** in September 2013,','于2013年9月走出**破产**(bankruptcy)，']
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
new['allow_clash']=list(dict.fromkeys(new.get('allow_clash',[])+['fetched','bankruptcy']))
new.setdefault('核对确认',{}).setdefault('同词异译',{})['fetched：以/卖给']='用户2026-11-14明确要求 fetched 对应中文只标“以”“卖给”，金额普通，原小字不改；这是同一谓语“以……卖给”的两处对应，不是两个不同释义。'
bare=lambda s:re.sub(r'\([^()]*\)','',s.replace('**',''))
for a,b in zip(old['sentences'],new['sentences']):
 assert a['para']==b['para']and len(a['chunks'])==len(b['chunks'])
 for u,v in zip(a['chunks'],b['chunks']):
  assert u['en'].replace('**','')==v['en'].replace('**','')
  assert bare(u['zh'])==bare(v['zh'])
  assert u.get('note')==v.get('note')
for key in old:
 if key not in ['sentences','allow_clash','核对确认']:assert old[key]==new[key],key
for key,value in old['核对确认'].items():
 if key=='同词异译':
  for sub,value2 in value.items():assert new['核对确认'][key][sub]==value2
 else:assert new['核对确认'][key]==value
assert old['sentences'][-1]==new['sentences'][-1]
source=C/rels[0];source.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
gen,issues=P.pure_generator(new);assert not issues,issues;(C/rels[1]).write_text(gen)
md=(BEFORE/rels[2]).read_text()
for a,b in [('patents fetched about $525 million','patents **fetched** about $525 million'),('Kodak left bankruptcy in September 2013,','Kodak left **bankruptcy** in September 2013,'),('以约5.25亿美元卖给一个由十二家','**以**(fetched)约5.25亿美元**卖给**(fetched)一个由十二家'),('于2013年9月走出破产，','于2013年9月走出**破产**(bankruptcy)，')]:
 assert md.count(a)==1,(a,md.count(a));md=md.replace(a,b)
assert '| fetch |'not in md and '| bankruptcy |'not in md
md=md.replace('| giants |','| fetch | 本文：以……卖给；v. 卖得（价钱）（fetch a good price） | 4 |\n| giants |',1)
md=md.replace('| downsized |','| bankruptcy | 本文：破产；n. 破产（file for bankruptcy） | 5 |\n| downsized |',1)
assert md.count('| fetch |')==md.count('| bankruptcy |')==1
(C/rels[2]).write_text(md)
auth=json.loads((C/rels[4]).read_text())
entries=[{'篇':'36','日期':'2026-11-10','原话':'不用管，这个就是我清点的词，我清点的词不用管，撞不撞车，全都留，全都留，全都特批。我专门说的这个加为重点词汇的这个所有的词全都这个重点特批。','用于':'allow_clash.fetched / bankruptcy（2026-11-14用户本篇指定S16C2 fetched与S17C1 bankruptcy重点；fetched中文仅以、卖给同色、金额普通、原小字不改）','来源':'沿用真实通用特批；本轮具体截图及原话见USER-REVIEW-2026-11-14-027和028.json；其他篇原重点词不变'}]
review=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-029.json');r=json.loads(review.read_text());quote=r['user_instruction_verbatim']
entries.append({'篇':'36','日期':'2026-11-14','原话':quote,'用于':'仅本篇两处重点修改后重新生成4K定稿；保43543967031已通过实际音频及全部声音控制','来源':str(review),'来源文件SHA256':sha(review)})
for e in entries:
 if e not in auth['记录']:auth['记录'].append(e)
(C/rels[4]).write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
pending=(C/rels[3]).read_text()if(C/rels[3]).exists()else''
pending+='\n\n## 2026-11-14 审核后定稿\n\n- S16C2 fetched 标为重点，对应中文仅“以”“卖给”同色；中间金额不标，fetch小字原样保留。\n- S17C1 bankruptcy 标为重点，中文“破产”，left与“走出”不标。\n- 用户明确本篇4K重新定稿，见审核029；保原43543967031已通过实际音轨、全部DSP、正文、简述及插图2秒+简述2秒结构。\n'
(C/rels[3]).write_text(pending)
actual=B/'next-passed-native/43543967031/36/artifact-files/36-actual-working-source.json';ad=json.loads(actual.read_text());normal=copy.deepcopy(ad);normal['sentences'][-1]['chunks'][-1]['note']=old['sentences'][-1]['chunks'][-1]['note'];assert normal==old
assert ad['sentences'][-1]['chunks'][-1]['note'].replace('\n','').replace('▹','')==old['sentences'][-1]['chunks'][-1]['note'].replace('\n','').replace('▹','')
report={'article':'36','book_order':'28','kind':'two-user-requested-focus-only-source-proposal','quality_acceptance':False,'before_source_sha256':sha(BEFORE/rels[0]),'after_source_sha256':sha(source),'generator_sha256':sha(C/rels[1]),'manuscript_sha256':sha(C/rels[2]),'actual_accepted_source_sha256':sha(actual),'actual_accepted_source_only_existing_summary_wrap_diff':True,'all_spoken_English_chunk_boundaries_exact':True,'all_existing_non_sentence_controls_and_CF_exact':True,'bare_Chinese_exact':True,'all_original_notes_exact':True,'full_last_summary_note_exact':True,'fetched_Chinese_only_separate_yi_and_maigei_colored':True,'price_uncolored':True,'exact_JSON_diff':P.differences(old,new),'auth_entries':entries,'baseline_states':states,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(H/'proposal-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k in ['after_source_sha256','generator_sha256','manuscript_sha256']},ensure_ascii=False))
