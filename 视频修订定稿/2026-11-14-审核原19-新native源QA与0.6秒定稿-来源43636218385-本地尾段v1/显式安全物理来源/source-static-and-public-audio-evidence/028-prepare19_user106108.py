"""Only latest-PAY source19 user106–108 text changes; audio105 separately read-only."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
O=Path(__file__).parent;B=Path('/workspace/work/video-audit70-20261113');PAY=B/'payload';C=O/'candidate-payload';before=O/'before';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();s=importlib.util.spec_from_file_location('P19',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
rels=['视频/脚本/19.json','视频/工具/初稿生成/gen19.py','新版定稿/19-tulip-mania.md']
for rel in rels:
 q=before/rel;q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists()or q.read_bytes()==(PAY/rel).read_bytes();shutil.copyfile(PAY/rel,q)if not q.exists()else None;(C/rel).parent.mkdir(parents=True,exist_ok=True)
p=C/rels[0];old=json.loads((before/rels[0]).read_text());assert sha(before/rels[0])=='cc3c5eea0f7d9ec0712b2e58adba7e5ef8b61d6518a322f9b25a12fcc45282fb';d=copy.deepcopy(old)
c=d['sentences'][3]['chunks'][1]
for pair in c['align']:
 pair[0]=pair[0].replace('a skilled craftsman','a **skilled** **craftsman**');pair[1]=pair[1].replace('熟练工匠','**熟练**(skilled)**工匠**(craftsman)')
c=d['sentences'][7]['chunks'][0]
for pair in c['align']:pair[0]=pair[0].replace('a Scottish','a **Scottish**');pair[1]=pair[1].replace('一位苏格兰','一位**苏格兰的**(Scottish)')
c=d['sentences'][7]['chunks'][2]
for pair in c['align']:pair[0]=pair[0].replace('casting it as','**casting** it **as**');pair[1]=pair[1].replace('将其描绘为','**将**(casting as)其**描绘为**(casting as)')
changed=[(4,2),(8,1),(8,3)]
for si,ci in changed:
 c=d['sentences'][si-1]['chunks'][ci-1];c['en']=' '.join(e for e,z in c['align']);c['zh']=''.join(z for e,z in c['align'])
d.setdefault('allow_clash',[]).extend(['skilled','craftsman','Scottish','casting as','casting','as']);d['核对确认'].setdefault('同词异译',{})['casting as：将/描绘为']='不是两种译法：cast A as B 的完整意思为将A描绘为B，本文casting it as中it对应普通的其；将和描绘为是同一谓语的两部分，同key标casting as，依据用户108指定整个cast…as搭配重点。'
for a,b in zip(old['sentences'],d['sentences']):
 assert len(a['chunks'])==len(b['chunks'])and a['para']==b['para']
 for x,y in zip(a['chunks'],b['chunks']):assert x['en'].replace('**','')==y['en'].replace('**','')and x.get('note')==y.get('note')and len(x['align'])==len(y['align'])
assert{k:v for k,v in old.items()if k not in['sentences','allow_clash','核对确认']}=={k:v for k,v in d.items()if k not in['sentences','allow_clash','核对确认']};cf=copy.deepcopy(d['核对确认']);cf['同词异译'].pop('casting as：将/描绘为');cf.pop('同词异译')if'同词异译'not in old['核对确认']and not cf['同词异译']else None;assert cf==old['核对确认'];assert d['sentences'][-1]==old['sentences'][-1]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');gen,issues=P.pure_generator(d);assert gen and not issues;(C/rels[1]).write_text(gen);t=(before/rels[2]).read_text()
for si,ci in changed:
 a=old['sentences'][si-1]['chunks'][ci-1];b=d['sentences'][si-1]['chunks'][ci-1]
 for f in['en','zh']:
  if a[f]!=b[f]:assert t.count(a[f])==1,(si,ci,f);t=t.replace(a[f],b[f],1)
rows=[('wages',['| skilled | 本文：熟练；adj. 熟练的，有技能的（a skilled worker/craftsman） | 2 |','| craftsman | 本文：工匠；n. 工匠，手艺人（复数 craftsmen） | 2 |']),('journalist',['| Scottish | 本文：苏格兰的；adj. 苏格兰的，苏格兰人的 | 3 |']),('hysteria',['| casting as | 本文：将……描绘为；v. (cast A as B) 将A描绘为B；把A塑造成B（casting为cast的现在分词） | 3 |'])]
for anchor,rr in rows:
 for row in rr:assert '| '+row.split('|')[1].strip()+' |'not in t
 assert t.count('| '+anchor+' |')==1;t=t.replace('| '+anchor+' |','\n'.join(rr)+'\n| '+anchor+' |',1)
(C/rels[2]).write_text(t);auth=json.loads((PAY/'视频/工具/用户同意记录.json').read_text());records=[];work='## source19/book38 用户105–109\n\n仅106–108文字重点同步：skilled熟练、craftsman工匠，保wages工钱；Scottish苏格兰的且一位普通；casting it as中casting/as同key、it普通，中文将/描绘为同key、其普通，lemma cast A as B。其它中文/ENbare/chunk/原note/独立5点summary/全部语音控制保持最新PAY。105 petals词尾与全篇音频由独立音频子任务cache-only取证，真实问题方可root实读后选最小修复，不因旧通用原门已过就忽略用户听感。本轮109已定稿授权，但文字/音频真实门未闭合前不将旧fb88称为新修订成片；不TTS、不生成新视频、不动PDF/书目录/Release。\n'
for n in range(105,110):
 roots=[Path(f'/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-{n:03}.json'),Path(f'/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-{n:03}.json')];rp=next((q for q in roots if q.exists()),None)
 if rp:
  r=json.loads(rp.read_text());quote=r['user_instruction_verbatim'];origin={'path':str(rp),'sha256':sha(rp)}
 else:
  quote=None;origin={'kind':'root-authorized-specific-scope-task-message','raw_ledger_not_yet_local':True}
 ev={'source_id':'19','book_order':'38','feedback':n,'user_instruction_verbatim':quote,'origin':origin,'no_user_verbatim_invented':quote is None};ep=O/f'feedback-{n:03}-intake.json';ep.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n');records.append({'path':str(ep),'sha256':sha(ep)})
 if quote:
  auth['记录'].append({'篇':'19','日期':'2026-11-14','原话':quote,'用于':f'用户{n:03} source19/book38本轮指定106–108重点/译文/词表同步，casting/as为同一搭配完整标注，点名词允许撞词、原其它焦点保留；105音检另域待实证，109本篇4K定稿及本篇下载审核特许覆盖079仅此篇，原0.6秒/图2秒/简述2秒保留。','来源反馈号':f'{n:03}','来源文件':str(ep),'来源文件SHA256':sha(ep)});work+='\n### 用户'+f'{n:03}'+'原话\n\n'+quote+'\n'
(C/'视频/工具/用户同意记录.json').parent.mkdir(parents=True,exist_ok=True);(C/'视频/工具/用户同意记录.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n');wp=C/'视频/制作记录/19_待改清单.md';wp.parent.mkdir(parents=True,exist_ok=True);basework=PAY/'视频/制作记录/19_待改清单.md';wp.write_text((basework.read_text()if basework.exists()else'')+'\n\n'+work+'\n执行定位（非新增用户逐字引文）：S8一位苏格兰记者→一位苏格兰的记者；cast A as B整搭配的两个EN片段及两处CN同一谓语部分共同标同key；原其为it，保持普通。\n')
r=dict(source_id='19',book_order='38',user109_final_authorized=True,new_video_not_generated=True,audio105_pending=True,before_source_sha256=sha(before/rels[0]),source_sha256=sha(p),GEN_sha256=sha(C/rels[1]),MD_sha256=sha(C/rels[2]),all_bare_English_chunk_indices_and_all_voice_DSP_exact_to_latest_PAY=True,all_original_notes_and_raw5point_summary_preserved=True,only_106107108_designated_occurrences_focused=True,later_S13_craftsmen_ordinary_preserved=True,cast_A_as_B_complete_split_focus_same_key=True,diff=P.differences(old,d),feedback_evidence=records,PAY_CI_old_4K_remote_current_book_catalog_PDF_unchanged=True);o=O/'user106108-text-implementation-v1.json';o.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in['diff','feedback_evidence']},ensure_ascii=False))
