"""Source33: only explicitly requested divers focus, retaining actual accepted text/audio."""
import copy,datetime,hashlib,importlib.util,json,re,shutil
from pathlib import Path
B=Path('/workspace/work/video-audit70-20261113');PAY=B/'payload';H=Path(__file__).parent;C=H/'candidate-payload';BEFORE=H/'before'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
rels=['视频/脚本/33.json','视频/工具/初稿生成/gen33.py','新版定稿/33-thirteen-in-the-cave.md','视频/制作记录/33_待改清单.md','视频/工具/用户同意记录.json']
states={}
for rel in rels:
 p=PAY/rel;states[rel]={'exists':p.exists(),'sha256':sha(p)if p.exists()else None}
 if p.exists():
  for root in [BEFORE,C]:
   q=root/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
assert not states[rels[2]]['exists']
actual=B/'next-passed-native/43543967031/33/artifact-files'
mdsource=actual/'33-actual-working-manuscript.md';assert sha(mdsource)=='4956ee47680b6d4cc958d09cf0e43d292500c5b1cc6be7b05602d2d8bd2666a1'
for root in [BEFORE,C]:
 q=root/rels[2];q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(mdsource,q)
states[rels[2]].update(restored_from_actual_accepted_run_manuscript=str(mdsource),restored_sha256=sha(mdsource))
genbase=B/'gen-sources/gen33.py';states['gen-sources/gen33.py']={'exists':genbase.exists(),'sha256':sha(genbase)if genbase.exists()else None}
if genbase.exists():shutil.copyfile(genbase,BEFORE/'gen-sources-gen33.py')
(BEFORE/'baseline-states.json').write_text(json.dumps(states,ensure_ascii=False,indent=2)+'\n')
old=json.loads((BEFORE/rels[0]).read_text());new=copy.deepcopy(old)
c=new['sentences'][13]['chunks'][1]
assert c['align'][1]==['a **contingent** of more than 100 divers,','一支100多名潜水员组成的**分队**(contingent)，']
c['align'][1]=['a **contingent** of more than 100 **divers**,','一支100多名**潜水员**(divers)组成的**分队**(contingent)，']
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
bare=lambda s:re.sub(r'\([^()]*\)','',s.replace('**',''))
for a,b in zip(old['sentences'],new['sentences']):
 assert a['para']==b['para']and len(a['chunks'])==len(b['chunks'])
 for u,v in zip(a['chunks'],b['chunks']):
  assert u['en'].replace('**','')==v['en'].replace('**','')
  assert bare(u['zh'])==bare(v['zh'])
  assert u.get('note')==v.get('note')
assert {k:v for k,v in old.items()if k!='sentences'}=={k:v for k,v in new.items()if k!='sentences'}
assert old['sentences'][-1]==new['sentences'][-1]
source=C/rels[0];source.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
gen,issues=P.pure_generator(new);assert not issues,issues;(C/rels[1]).write_text(gen)
md=(BEFORE/rels[2]).read_text()
for a,b in [('a **contingent** of more than 100 divers,','a **contingent** of more than 100 **divers**,'),('一支100多名潜水员组成的**分队**(contingent)，','一支100多名**潜水员**(divers)组成的**分队**(contingent)，')]:
 assert md.count(a)==1,(a,md.count(a));md=md.replace(a,b)
row='| divers | 本文：潜水员；n. (diver) 潜水员（deep-sea divers） | 2 |'
assert md.count(row)==1
assert md.split('## 速查表',1)[1]==(BEFORE/rels[2]).read_text().split('## 速查表',1)[1]
(C/rels[2]).write_text(md)
auth=json.loads((C/rels[4]).read_text())
review=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-034.json')
quote='这一篇可以定稿了，4k视频。我们新标注的这些单词也要出现在每一篇要记的单词里面。'
if review.exists():quote=json.loads(review.read_text()).get('user_instruction_verbatim',quote)
entries=[{'篇':'33','日期':'2026-11-14','原话':quote,'用于':'仅S14C2 divers重点对应潜水员后重新生成4K定稿；既有必记速查表divers（名词原形diver）条目保留；保43543967031已验原声及全部控制，原时序不新增0.3秒','来源':str(review),'用户要求的指定位置原记录':'USER-REVIEW-2026-11-14-033.json'}]
if review.exists():entries[0]['来源文件SHA256']=sha(review)
for e in entries:
 if e not in auth['记录']:auth['记录'].append(e)
(C/rels[4]).write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
pending=(C/rels[3]).read_text()if(C/rels[3]).exists()else''
pending+='\n\n## 2026-11-14 审核后定稿\n\n- S14C2 including a contingent of more than 100 divers：divers与潜水员标为对应重点，保原复数与原小字。\n- 必记词汇速查表已有一条divers（原形diver），释义潜水员；本次保留，不重复添加。\n- 保全部原正文、五点简述、录音和DSP，插图2秒+简述2秒；本篇没有0.3秒试看停留改动。\n'
(C/rels[3]).parent.mkdir(parents=True,exist_ok=True);(C/rels[3]).write_text(pending)
ad=json.loads((actual/'33-actual-working-source.json').read_text());normal=copy.deepcopy(ad);normal['sentences'][-1]['chunks'][-1]['note']=old['sentences'][-1]['chunks'][-1]['note'];assert normal==old
assert ad['sentences'][-1]['chunks'][-1]['note'].replace('\n','').replace('▹','')==old['sentences'][-1]['chunks'][-1]['note'].replace('\n','').replace('▹','')
report={'article':'33','book_order':'30','kind':'single-specified-divers-focus-source-proposal','quality_acceptance':False,'before_source_sha256':sha(BEFORE/rels[0]),'after_source_sha256':sha(source),'generator_sha256':sha(C/rels[1]),'manuscript_sha256':sha(C/rels[2]),'actual_accepted_source_sha256':sha(actual/'33-actual-working-source.json'),'actual_accepted_source_only_existing_summary_wrap_diff':True,'all_spoken_English_chunk_boundaries_exact':True,'all_existing_non_sentence_controls_and_CF_exact':True,'bare_Chinese_exact':True,'all_original_notes_exact':True,'full_last_summary_note_exact':True,'specified_S14C2_divers_plural_retained':True,'vocabulary_table_existing_exact_row':row,'vocabulary_table_has_divers_headword_diver_and_Potential_new_occurrence_not_duplicate_word':True,'vocabulary_table_and_facts_entire_section_exact':True,'exact_JSON_diff':P.differences(old,new),'auth_entries':entries,'baseline_states':states,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(H/'proposal-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k in ['after_source_sha256','generator_sha256','manuscript_sha256']},ensure_ascii=False))
