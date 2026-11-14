"""Only the two explicitly approved Titanic focus changes; retain current A21 data."""
import copy,datetime,hashlib,importlib.util,json,re,shutil
from pathlib import Path
B=Path('/workspace/work/video-audit70-20261113');PAY=B/'payload';H=Path(__file__).parent;C=H/'candidate-payload';BEFORE=H/'before'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
rels=['视频/脚本/15.json','视频/工具/初稿生成/gen15.py','新版定稿/15-the-myth-of-the-unsinkable.md','视频/制作记录/15_待改清单.md','视频/工具/用户同意记录.json']
for rel in rels:
 p=PAY/rel
 if p.exists():
  q=BEFORE/rel;q.parent.mkdir(parents=True,exist_ok=True)
  if not q.exists():shutil.copyfile(p,q)
  q=C/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
gen_baseline=B/'gen-sources/gen15.py';p=BEFORE/'gen-sources-gen15.py'
if gen_baseline.exists()and not p.exists():shutil.copyfile(gen_baseline,p)
(BEFORE/'gen-sources-baseline-state.json').write_text(json.dumps({'path':str(gen_baseline),'exists':gen_baseline.exists(),'sha256':sha(gen_baseline)if gen_baseline.exists()else None},indent=2)+'\n')
old=json.loads((BEFORE/rels[0]).read_text());new=copy.deepcopy(old)
assert old['除阻加强']=={'S8':{'1':[3.25,3.315,5.0]}}
c=new['sentences'][12]['chunks'][0]
assert c['align'][1]==['inquiries in Washington and London','华盛顿和伦敦的调查']
c['align'][1]=['**inquiries** in Washington and London','华盛顿和伦敦的**调查**(inquiries)']
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
c=new['sentences'][15]['chunks'][1]
assert c['align'][0]==['the patrol','然而冰情巡逻']
c['align'][0]=['the **patrol**','然而冰情**巡逻**(patrol)']
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
new['allow_clash']=list(dict.fromkeys(new.get('allow_clash',[])+['inquiries','patrol']))
bare=lambda s:re.sub(r'\([^()]*\)','',s.replace('**',''))
for a,b in zip(old['sentences'],new['sentences']):
 assert a['para']==b['para']and len(a['chunks'])==len(b['chunks'])
 for u,v in zip(a['chunks'],b['chunks']):
  assert u['en'].replace('**','')==v['en'].replace('**','')
  assert bare(u['zh'])==bare(v['zh'])
for key in old:
 if key not in ['sentences','allow_clash']:assert old[key]==new[key],key
assert old['sentences'][14]==new['sentences'][14]
assert old['sentences'][-1]==new['sentences'][-1]
source=C/rels[0];source.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');gen,issues=P.pure_generator(new);assert not issues,issues;(C/rels[1]).write_text(gen)
md=(BEFORE/rels[2]).read_text()
for a,b in [('Between April and July 1912, inquiries in Washington and London','Between April and July 1912, **inquiries** in Washington and London'),('the patrol went ahead **regardless**.','the **patrol** went ahead **regardless**.'),('华盛顿和伦敦的调查听取了','华盛顿和伦敦的**调查**(inquiries)听取了'),('然而冰情巡逻**不管怎样**(regardless)','然而冰情**巡逻**(patrol)**不管怎样**(regardless)')]:
 assert md.count(a)==1,(a,md.count(a));md=md.replace(a,b)
assert '| inquiries |'not in md and md.count('| patrol |')==1
md=md.replace('| survivors |','| inquiries | 本文：调查；n. (inquiry) 调查；询问（a public inquiry） | 4 |\n| survivors |',1)
(C/rels[2]).write_text(md)
auth=json.loads((C/rels[4]).read_text());entries=[{'篇':'15','日期':'2026-11-10','原话':'不用管，这个就是我清点的词，我清点的词不用管，撞不撞车，全都留，全都留，全都特批。我专门说的这个加为重点词汇的这个所有的词全都这个重点特批。','用于':'allow_clash.inquiries / patrol（2026-11-14用户本篇指定新增S13C1 inquiries调查、仅S16C2 patrol巡逻重点；保复数小写及原S15 ice patrol重点）','来源':'沿用真实通用特批；本轮具体截图及原话见USER-REVIEW-2026-11-14-018和019.json；其他篇原重点词不变'}]
review=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-020.json');r=json.loads(review.read_text());quote=r['user_instruction_verbatim'];assert quote=='泰坦尼克号这一篇可以定稿了，4k重新定稿。'
entries.append({'篇':'15','日期':'2026-11-14','原话':quote,'用于':'仅本篇两处重点修改后重新生成4K定稿；保43562525001最新已通过A21音频','来源':str(review),'来源文件SHA256':sha(review)})
for e in entries:
 if e not in auth['记录']:auth['记录'].append(e)
(C/rels[4]).write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
pending=(C/rels[3]).read_text()if(C/rels[3]).exists()else''
pending+='\n\n## 2026-11-14 审核后定稿\n\n- S13C1 inquiries 标为重点，本文义“调查”，保复数和小写。\n- 仅S16C2 the patrol went ahead regardless 中 patrol 补重点，本文义“巡逻”；原S15 ice **patrol**与International Ice Patrol原样保留。\n- 用户明确本篇4K重新定稿，原话见审核020；保最新43562525001已验A21 +5音频、全部现有控制、正文与详细五点简述。CF/音包由唯一声音生产负责人核对，不复用旧指纹冒充最新音轨。\n'
(C/rels[3]).write_text(pending)
report={'article':'15','book_order':'25','kind':'two-user-requested-focus-only-source-proposal','quality_acceptance':False,'before_source_sha256':sha(BEFORE/rels[0]),'after_source_sha256':sha(source),'generator_sha256':sha(C/rels[1]),'manuscript_sha256':sha(C/rels[2]),'all_spoken_English_chunk_boundaries_exact':True,'all_existing_non_sentence_controls_and_CF_exact':True,'current_A21_plus5_exact':True,'bare_Chinese_exact':True,'existing_S15_ice_patrol_sentence_exact':True,'full_last_summary_note_exact':True,'exact_JSON_diff':P.differences(old,new),'auth_entries':entries,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(H/'proposal-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k in ['after_source_sha256','generator_sha256','manuscript_sha256']},ensure_ascii=False))
