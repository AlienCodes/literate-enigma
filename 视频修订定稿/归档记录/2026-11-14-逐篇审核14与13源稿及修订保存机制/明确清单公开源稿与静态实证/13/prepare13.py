"""Two user-requested article13 focus changes; no spoken/audio/control edits."""
import copy,datetime,hashlib,importlib.util,json,re,shutil
from pathlib import Path
B=Path('/workspace/work/video-audit70-20261113');PAY=B/'payload';H=Path(__file__).parent;C=H/'candidate-payload';BEFORE=H/'before'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('original_data_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
rels=['视频/脚本/13.json','视频/工具/初稿生成/gen13.py','新版定稿/13-eleven-days-without-sleep.md','视频/制作记录/13_待改清单.md','视频/工具/用户同意记录.json']
for rel in rels:
 p=PAY/rel
 if p.exists():
  q=BEFORE/rel;q.parent.mkdir(parents=True,exist_ok=True)
  if not q.exists():shutil.copyfile(p,q)
  q=C/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
p=BEFORE/'gen-sources-gen13.py'
if not p.exists():shutil.copyfile(B/'gen-sources/gen13.py',p)
old=json.loads((BEFORE/rels[0]).read_text());new=copy.deepcopy(old)
c=new['sentences'][1]['chunks'][2]
assert c['en']=='and logged his **mood**.' and c['zh']=='并记录了他的**情绪**(mood)。'
c['align']=[['and','并'],['**logged**','**记录了**(logged)'],['his **mood**.','他的**情绪**(mood)。']]
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
c=new['sentences'][14]['chunks'][0]
assert c['align']==[['In 1997','1997年，'],['Guinness World Records','吉尼斯世界纪录']]
c['align']=[['In 1997','1997年，'],['**Guinness World Records**','**吉尼斯世界纪录**(Guinness World Records)']]
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
new['allow_clash']=list(dict.fromkeys(new.get('allow_clash',[])+['logged','Guinness World Records']))
def plain_en(s):return s.replace('**','')
for a,b in zip(old['sentences'],new['sentences']):
 assert a['para']==b['para'] and len(a['chunks'])==len(b['chunks'])
 for u,v in zip(a['chunks'],b['chunks']):assert plain_en(u['en'])==plain_en(v['en'])
for key in old:
 if key not in ['sentences','allow_clash']:assert old[key]==new[key],key
assert old['sentences'][-1]['chunks'][-1]['note']==new['sentences'][-1]['chunks'][-1]['note']
source=C/rels[0];source.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
gen,issues=P.pure_generator(new);assert not issues,issues;(C/rels[1]).write_text(gen)
md=(BEFORE/rels[2]).read_text()
assert md.count('and logged his **mood**.')==1 and md.count('In 1997 Guinness World Records **discontinued**')==1
md=md.replace('and logged his **mood**.','and **logged** his **mood**.').replace('In 1997 Guinness World Records **discontinued**','In 1997 **Guinness World Records** **discontinued**')
assert md.count('并记录了他的**情绪**(mood)')==1
md=md.replace('并记录了他的**情绪**(mood)','并**记录了**(logged)他的**情绪**(mood)')
assert md.count('1997年，吉尼斯世界纪录')==1
md=md.replace('1997年，吉尼斯世界纪录','1997年，**吉尼斯世界纪录**(Guinness World Records)')
assert '| logged |'not in md and '| Guinness World Records |'not in md
md=md.replace('| mood |','| logged | 本文：记录；v. (log) 记录（log observations/data） | 1 |\n| mood |',1)
md=md.replace('| perils |','| Guinness World Records | 本文：吉尼斯世界纪录；专有名词. 吉尼斯世界纪录 | 5 |\n| perils |',1)
(C/rels[2]).write_text(md)
auth=json.loads((C/rels[4]).read_text())
entries=[{'篇':'13','日期':'2026-11-10','原话':'不用管，这个就是我清点的词，我清点的词不用管，撞不撞车，全都留，全都留，全都特批。我专门说的这个加为重点词汇的这个所有的词全都这个重点特批。','用于':'allow_clash.logged / Guinness World Records（2026-11-14用户本篇点名新增重点词；完整短语整体标注）','来源':'沿用真实通用特批；本轮具体截图和原话见USER-REVIEW-2026-11-14-009及010.json；其他篇原重点词不变'}, {'篇':'13','日期':'2026-11-14','原话':'Ok，然后这个11天不睡觉的这个实验就可以定稿了，可以定稿了。','用于':'本篇logged记录与Guinness World Records吉尼斯世界纪录整体重点修改后重新生成4K定稿；仅原13/书23','来源':'当前会话用户明确指令，root转交唯一13源编辑任务'}]
for e in entries:
 if e not in auth['记录']:auth['记录'].append(e)
(C/rels[4]).write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
pending=(C/rels[3]).read_text()if(C/rels[3]).exists()else''
pending+='\n\n## 2026-11-14 审核后定稿\n\n- S2 logged 标为重点词汇，本文义“记录”；句中“记录了”整体标。\n- S15 Guinness World Records / 吉尼斯世界纪录作为完整词组整体标为重点。\n- 用户明确：“Ok，然后这个11天不睡觉的这个实验就可以定稿了，可以定稿了。”保持既有正文朗读、全部音控、末页和详细简述，仅按本轮重点词修改后出4K。\n'
(C/rels[3]).write_text(pending)
report={'article':'13','book_order':'23','kind':'two-user-requested-focus-only-source-proposal','quality_acceptance':False,'before_source_sha256':sha(BEFORE/rels[0]),'after_source_sha256':sha(source),'generator_sha256':sha(C/rels[1]),'manuscript_sha256':sha(C/rels[2]),'all_spoken_English_chunk_boundaries_exact':True,'all_other_non_sentence_controls_exact':True,'full_last_summary_note_exact':True,'exact_JSON_diff':P.differences(old,new),'auth_entries':entries,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(H/'proposal-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k in ['after_source_sha256','generator_sha256','manuscript_sha256']},ensure_ascii=False))
