"""Two exact user-requested article26 focus changes; no voice/control edits."""
import copy,datetime,hashlib,importlib.util,json,shutil
from pathlib import Path
B=Path('/workspace/work/video-audit70-20261113');PAY=B/'payload';H=Path(__file__).parent;C=H/'candidate-payload';BEFORE=H/'before'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
rels=['视频/脚本/26.json','视频/工具/初稿生成/gen26.py','新版定稿/26-the-language-the-children-invented.md','视频/制作记录/26_待改清单.md','视频/工具/用户同意记录.json']
for rel in rels:
 p=PAY/rel
 if p.exists():
  q=BEFORE/rel;q.parent.mkdir(parents=True,exist_ok=True)
  if not q.exists():shutil.copyfile(p,q)
  q=C/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
p=BEFORE/'gen-sources-gen26.py'
gen_baseline=B/'gen-sources/gen26.py'
if gen_baseline.exists():
 if not p.exists():shutil.copyfile(gen_baseline,p)
(BEFORE/'gen-sources-baseline-state.json').write_text(json.dumps({'path':str(gen_baseline),'exists':gen_baseline.exists(),'sha256':sha(gen_baseline)if gen_baseline.exists()else None},indent=2)+'\n')
old=json.loads((BEFORE/rels[0]).read_text());new=copy.deepcopy(old)
c=new['sentences'][3]['chunks'][1]
assert c['align'][3]==['of gestures','手势，']
c['align'][3]=['of **gestures**','**手势**(gestures)，']
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
c=new['sentences'][15]['chunks'][0]
assert c['align'][0]==['Linguists','语言学家']
c['align'][0]=['**Linguists**','**语言学家**(Linguists)']
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
new['allow_clash']=list(dict.fromkeys(new.get('allow_clash',[])+['gestures','linguist']))
for a,b in zip(old['sentences'],new['sentences']):
 assert a['para']==b['para'] and len(a['chunks'])==len(b['chunks'])
 for u,v in zip(a['chunks'],b['chunks']):assert u['en'].replace('**','')==v['en'].replace('**','')
for key in old:
 if key not in ['sentences','allow_clash']:assert old[key]==new[key],key
assert old['sentences'][-1]['chunks'][-1]['note']==new['sentences'][-1]['chunks'][-1]['note']
source=C/rels[0];source.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');gen,issues=P.pure_generator(new);assert not issues,issues;(C/rels[1]).write_text(gen)
md=(BEFORE/rels[2]).read_text()
assert md.count('**repertoire** of gestures with parents')==1 and md.count('Linguists had a rare chance')==1
md=md.replace('**repertoire** of gestures with parents','**repertoire** of **gestures** with parents').replace('Linguists had a rare chance','**Linguists** had a rare chance')
assert md.count('**一整套/全部**(repertoire)手势，')==1 and md.count('\n语言学家难得有机会')==1
md=md.replace('**一整套/全部**(repertoire)手势，','**一整套/全部**(repertoire)**手势**(gestures)，').replace('\n语言学家难得有机会','\n**语言学家**(Linguists)难得有机会')
assert '| gestures |'not in md and '| linguist |'in md
md=md.replace('| siblings |','| gestures | 本文：手势；n. (gesture) 手势，姿势（make a gesture） | 2 |\n| siblings |',1)
(C/rels[2]).write_text(md)
auth=json.loads((C/rels[4]).read_text())
entries=[{'篇':'26','日期':'2026-11-10','原话':'不用管，这个就是我清点的词，我清点的词不用管，撞不撞车，全都留，全都留，全都特批。我专门说的这个加为重点词汇的这个所有的词全都这个重点特批。','用于':'allow_clash.gestures / linguist（2026-11-14用户本篇指定新增S4 gestures手势与S16 Linguists语言学家重点；保复数和大小写，linguist沿用原词表词头）','来源':'沿用真实通用特批；本轮具体截图和原话见USER-REVIEW-2026-11-14-012及013.json；其他篇原重点词不变'}]
review=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-014.json')
if review.exists():
 r=json.loads(review.read_text());quote=r.get('user_instruction_verbatim')
 if quote:entries.append({'篇':'26','日期':'2026-11-14','原话':quote,'用于':'本篇两项重点修改后重新生成4K定稿；仅原26/书27','来源':str(review),'来源文件SHA256':sha(review)})
for e in entries:
 if e not in auth['记录']:auth['记录'].append(e)
(C/rels[4]).write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
pending=(C/rels[3]).read_text()if(C/rels[3]).exists()else''
pending+='\n\n## 2026-11-14 审核后定稿\n\n- S4 gestures 标为重点词汇，本文义“手势”。\n- S16 Linguists 标为重点词汇，本文义“语言学家”；保持原复数和大小写，词表沿用 linguist 词头。\n- 用户已明确本篇可以定稿并出4K；具体授权原话另见本轮审核记录014。保持既有正文朗读、全部音控、末页和详细简述。\n'
(C/rels[3]).write_text(pending)
report={'article':'26','book_order':'27','kind':'two-user-requested-focus-only-source-proposal','quality_acceptance':False,'before_source_sha256':sha(BEFORE/rels[0]),'after_source_sha256':sha(source),'generator_sha256':sha(C/rels[1]),'manuscript_sha256':sha(C/rels[2]),'all_spoken_English_chunk_boundaries_exact':True,'all_other_non_sentence_controls_exact':True,'full_last_summary_note_exact':True,'exact_JSON_diff':P.differences(old,new),'auth_entries':entries,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(H/'proposal-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k in ['after_source_sha256','generator_sha256','manuscript_sha256']},ensure_ascii=False))
