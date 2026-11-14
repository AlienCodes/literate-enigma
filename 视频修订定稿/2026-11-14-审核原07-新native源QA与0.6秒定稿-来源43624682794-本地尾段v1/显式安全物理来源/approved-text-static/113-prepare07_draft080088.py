"""Implement ONLY authorized source07/book03 manuscript draft080–088. No PAY/CI/media."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,shutil
O=Path(__file__).parent;B=Path('/workspace/work/video-audit70-20261113');H=O;C=O/'candidate-payload';before=O/'before';F=Path('/workspace/work/video-revision-delivery/next-passed-validated/43548189084/07/final-source');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();s=importlib.util.spec_from_file_location('P07',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
rels=['视频/脚本/07.json','视频/工具/初稿生成/gen07.py','新版定稿/07-the-octopus-that-escaped.md']
for rel in rels:
 dest=before/rel;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();shutil.copyfile(F/rel,dest);(C/rel).parent.mkdir(parents=True,exist_ok=True)
old=json.loads((before/rels[0]).read_text());assert sha(before/rels[0])=='70202897bd8568697e1dbbca36076e6089aaf20b1aebecb29b4a39a62d7a5d69';d=copy.deepcopy(old)
def modify(si,ci,enmap=(),zhmap=()):
 c=d['sentences'][si-1]['chunks'][ci-1]
 for field,maps in[(0,enmap),(1,zhmap)]:
  for a,b in maps:
   count=sum(p[field].count(a)for p in c['align']);assert count==1,(si,ci,a,count)
   for pair in c['align']:pair[field]=pair[field].replace(a,b)
 c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
modify(1,2,[("New Zealand's","**New Zealand**'s"),('Aquarium','**Aquarium**')],[('新西兰','**新西兰**(New Zealand)'),('水族馆','**水族馆**(Aquarium)')]);modify(1,3,[('octopus','**octopus**')],[('章鱼','**章鱼**(octopus)')])
modify(2,3,[('a drain','a **drain**')],[('排水口','**排水管道**(drain)')]);modify(2,4,[('the Pacific','**the Pacific**')],[('排水口的管道','其管道'),('太平洋','**太平洋**(the Pacific)')])
caption='这次逃脱发生后约三个月才被媒体报道；‘未被报道’不等于‘尚未被发现’。';c=d['sentences'][4]['chunks'][0];c['note']+='\n（这次逃脱发生后约三个月才被媒体报道；\n‘未被报道’不等于‘尚未被发现’。）';assert c['note'].replace('\n','').endswith('（'+caption+'）')
modify(7,2,[('shell','**shell**')],[('外壳','**外壳**(shell)')]);modify(9,3,[('react','**react**')],[('作出反应','**做出反应**(react)')]);modify(11,1,[('Seattle','**Seattle**')],[('西雅图','**西雅图**(Seattle)')]);modify(12,2,[('bristly','**bristly**'),('stick','**stick**')],[('带刺毛的','**带刺毛的**(bristly)'),('棍子','**棍子**(stick)')]);modify(13,1,[('Consciousness','**Consciousness**')],[('意识','**意识**(Consciousness)')])
newfocus=['New Zealand','Aquarium','octopus','drain','the Pacific','shell','react','Seattle','bristly','stick','Consciousness'];d.setdefault('allow_clash',[]).extend(newfocus)
for a,b in zip(old['sentences'],d['sentences']):
 assert len(a['chunks'])==len(b['chunks'])and a['para']==b['para']
 for x,y in zip(a['chunks'],b['chunks']):assert x['en'].replace('**','')==y['en'].replace('**','')and len(x['align'])==len(y['align'])
assert{k:v for k,v in old.items()if k not in['sentences','allow_clash']}=={k:v for k,v in d.items()if k not in['sentences','allow_clash']}
assert old['sentences'][-1]==d['sentences'][-1]
source=C/rels[0];source.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');gen,issues=P.pure_generator(d);assert gen and not issues;(C/rels[1]).write_text(gen)
t=(before/rels[2]).read_text();as_md=lambda x:re.sub(r'\{\{(.*?)\|[^}]+\}\}',r'\1',x)
changed=[(1,2),(1,3),(2,3),(2,4),(7,2),(9,3),(11,1),(12,2),(13,1)]
for si,ci in changed:
 a=old['sentences'][si-1]['chunks'][ci-1];b=d['sentences'][si-1]['chunks'][ci-1]
 for field in['en','zh']:
  x=as_md(a[field]);y=as_md(b[field]);assert t.count(x)==1,(si,ci,field,x);t=t.replace(x,y,1)
oldnote=old['sentences'][4]['chunks'][0]['note'].replace('\n','');newnote=d['sentences'][4]['chunks'][0]['note'].replace('\n','');assert t.count(oldnote)==1;t=t.replace(oldnote,newnote,1)
# Match original actual table's Chinese/English first occurrence order; do not duplicate existing entries.
newrows=[('atop',['| New Zealand | 本文：新西兰；n. 新西兰（国家名） | 1 |','| Aquarium | 本文：水族馆；n. 水族馆；水族箱 | 1 |','| octopus | 本文：章鱼；n. 章鱼 | 1 |']),('stretched',['| drain | 本文：排水管道；n. 排水管，排水道；v. 排干，流走 | 1 |']),('deposited',['| the Pacific | 本文：太平洋；n. 太平洋（the Pacific Ocean 的简称） | 1 |']),('beak',['| shell | 本文：外壳；n. 外壳；贝壳；（蛋等的）壳 | 3 |']),('autonomy',['| react | 本文：做出反应；v. 做出反应；发生反应 | 3 |']),('jars',['| Seattle | 本文：西雅图；n. 西雅图（美国城市名） | 4 |']),('adopting',['| bristly | 本文：带刺毛的；adj. 有刚毛的，长满硬毛的；易怒的 | 4 |','| stick | 本文：棍子；n. 棍子，枝条；v. 粘贴，刺入；坚持 | 4 |']),('possessing',['| Consciousness | 本文：意识；n. 意识，知觉；清醒状态 | 5 |'])]
for anchor,rows in newrows:
 for row in rows:assert '| '+row.split('|')[1].strip()+' |'not in t
 assert t.count('| '+anchor+' |')==1;t=t.replace('| '+anchor+' |','\n'.join(rows)+'\n| '+anchor+' |',1)
(C/rels[2]).write_text(t)
# Draft authorizations contain genuine raw records where present; no invented full user quote.
auth=json.loads((B/'payload/视频/工具/用户同意记录.json').read_text());records=[];work='## 用户080–088：book03/source07仅隔离草稿\n\n指定New Zealand新西兰/Aquarium水族馆/octopus章鱼三独立key，New Zealand所有格s普通，National国家/Napier内皮尔普通；drain排水管道及其管道、the Pacific太平洋整体；083新说明澄清未报道不等于未发现，保go+adj原grammar；shell外壳/react做出反应/Seattle西雅图/bristly带刺毛的/stick棍子/Consciousness意识均仅指定出现，旧focus保留，正文其余EN/中文/全部声控和最后summary保持。无新final/native授权，PAY/CI/current03alias/原first34ZIP/PDF不动。\n'
for n in range(80,89):
 paths=[Path(f'/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-{n:03}.json'),Path(f'/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-{n:03}.json')];rp=next((p for p in paths if p.exists()),None)
 if rp:
  r=json.loads(rp.read_text());quote=r['user_instruction_verbatim'];origin={'path':str(rp),'sha256':sha(rp)};assert str(r.get('source_id','07')).zfill(2)=='07'
 else:
  quote={87:'在这个地方，这个stick标注重点词汇。 bristly 也标 为重点词汇。',88:'Consciousness 标注为重点词汇，标注为重点词汇。'}[n];origin={'kind':'root-delegated-actual-user-verbatim-task-message','raw_ledger_not_yet_local':True}
 ep=O/f'feedback-{n:03}-actual-draft-intake.json';ev={'source_id':'07','book_order':'03','feedback':n,'user_instruction_verbatim':quote,'origin':origin,'draft_only':True,'new_native_final_not_authorized':True};ep.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n');records.append({'path':str(ep),'sha256':sha(ep)});auth['记录'].append({'篇':'07','日期':'2026-11-14','原话':quote,'用于':f'用户{n:03}本篇指定重点/中文义/083已接受注释仅隔离draft落实；点名词撞车允许，全部原焦点保留，不扩其它未点出现；尚无本篇重新定稿或新视频授权。','来源反馈号':f'{n:03}','来源文件':str(ep),'来源文件SHA256':sha(ep)});work+='\n### 用户'+f'{n:03}'+'原话\n\n'+quote+'\n'
(C/'视频/工具/用户同意记录.json').parent.mkdir(parents=True,exist_ok=True);(C/'视频/工具/用户同意记录.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n');wp=C/'视频/制作记录/07_待改清单.md';wp.parent.mkdir(parents=True,exist_ok=True);wp.write_text(work+'\n实施定位（非用户额外原话）：S2旧排水口→排水管道，后排水口的管道→其管道；S9作出反应→做出反应；用户083接受根给定的确切说明全文为'+caption+'；其余裸中文仅focus标记变化。\n')
h=Path('/dev/shm/first34-hold06-intake/validated/book03-source07/archive-handoff.json');r=dict(source_id='07',book_order='03',draft_only=True,new_native_final_authorized=False,baseline_actual_first34_handoff={'path':str(h),'sha256':sha(h),'source_run':43548189084,'actual_source_sha256':sha(before/rels[0]),'actual_used_MD_sha256':sha(before/rels[2]),'current_delivered_MP4_sha256':'3ba931446468d28e2d1eea2fa57ddf1c79b24bad52be4fbd697a828c7865dede'},candidate_source_sha256=sha(source),candidate_GEN_sha256=sha(C/rels[1]),candidate_MD_sha256=sha(C/rels[2]),new_focus_terms=newfocus,only_specific_occurrences_focused=True,all_original_spoken_English_chunk_indices_and_DSP_unchanged=True,last_sentence_and_original_summary_raw_exact=True,old_go_unreported_grammar_preserved=True,accepted_note_exact=caption,all_requested_new_terms_present_once_in_word_table=True,feedback_evidence=records,delta=P.differences(old,d),PAY_CI_remote_alias_first34ZIP_media_audio_PDF_untouched=True)
p=O/'draft080088-implementation-report.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in['delta','feedback_evidence']},ensure_ascii=False))
