from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
H=Path(__file__).parent;B=Path('/workspace/work/video-audit70-20261113');PAY=B/'payload';C=H/'candidate-payload';BE=H/'before';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();spec=importlib.util.spec_from_file_location('P',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);rels=['视频/脚本/37.json','视频/工具/初稿生成/gen37.py','新版定稿/37-dynamite-for-the-heart.md']
for rel in rels:
 q=BE/rel;q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists()or q.read_bytes()==(PAY/rel).read_bytes()
 if not q.exists():shutil.copyfile(PAY/rel,q)
 (C/rel).parent.mkdir(parents=True,exist_ok=True)
assert sha(BE/rels[0])=='b1b8945ccf3581df48ade5714a2d0e93e4cc6812708f95bef6f5e44439106c99';old=json.loads((BE/rels[0]).read_text());d=copy.deepcopy(old);c=d['sentences'][15]['chunks'][1];assert c['en']=='which **widens** blood vessels.'and c['zh']=='它会**扩张**(widens)血管。'
for pair in c['align']:pair[0]=pair[0].replace('blood vessels','**blood vessels**');pair[1]=pair[1].replace('血管','**血管**(blood vessels)')
c['en']=' '.join(e for e,z in c['align']);c['zh']=''.join(z for e,z in c['align']);assert c['en']=='which **widens** **blood vessels**.'
for a,b in zip(old['sentences'],d['sentences']):
 assert len(a['chunks'])==len(b['chunks'])and a['para']==b['para']
 for x,y in zip(a['chunks'],b['chunks']):assert x['en'].replace('**','')==y['en'].replace('**','')and x.get('note')==y.get('note')and len(x['align'])==len(y['align'])
assert{k:v for k,v in d.items()if k!='sentences'}=={k:v for k,v in old.items()if k!='sentences'}
p=C/rels[0];p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');gen,issues=P.pure_generator(d);assert gen and not issues;(C/rels[1]).write_text(gen);t=(BE/rels[2]).read_text();a=old['sentences'][15]['chunks'][1]
for f in['en','zh']:assert t.count(a[f])==1;t=t.replace(a[f],c[f],1)
assert '| blood vessels |'not in t and t.count('| widens |')==1;lines=t.splitlines(True);k=next(i for i,l in enumerate(lines)if l.startswith('| widens |'));lines.insert(k+1,'| blood vessels | 本文：血管；n. pl. (blood vessel) 血管（动脉、静脉或毛细血管等输送血液的管道） | 6 |\n');t=''.join(lines);(C/rels[2]).write_text(t)
# Actual paragraph comes from the source; avoid inventing numbering in the table.
md=C/rels[2];md.write_text(md.read_text().replace('血液的管道） | 6 |','血液的管道） | '+str(d['sentences'][15]['para'])+' |'))
auth=json.loads((PAY/'视频/工具/用户同意记录.json').read_text());rp=Path('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-131.json');origin={'kind':'root-relayed-user131-exact-scope','raw_ledger_not_yet_local':True};quote='Blood vessels标注为重点词汇。 在这个地方整体标注重点词汇。'
if rp.exists():raw=json.loads(rp.read_text());quote=raw['user_instruction_verbatim'];origin={'path':str(rp),'sha256':sha(rp)}
auth['记录'].append({'篇':'37','日期':'2026-11-14','原话':quote,'用于':'用户131仅S16C2 blood vessels整词组及血管同key重点，和widens扩张不同色，词表blood vessel名词义同步；暂reviewdraft，129130音频由独立只读音审，不擅加gain或生成native。','来源':origin});(C/'视频/工具/用户同意记录.json').parent.mkdir(parents=True,exist_ok=True);(C/'视频/工具/用户同意记录.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n');w=PAY/'视频/制作记录/37_待改清单.md';out=C/'视频/制作记录/37_待改清单.md';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(w.read_text()+'\n\n## 用户131本轮reviewdraft\n\n'+quote+'\n\n实施定位：source37/book43 S16第二块which widens blood vessels，blood vessels完整同key标血管，widens扩张原重点且异色，原英文bare/chunk/音控/summary/notes全部保留。尚无本轮定稿或native授权。\n')
r={'source_id':'37','frozen_book_order':'43','draft_only':True,'user131_feedback_origin':origin,'source_sha256':sha(p),'GEN_sha256':sha(C/rels[1]),'MD_sha256':sha(C/rels[2]),'only_blood_vessels_whole_phrase_and_CN_xueguan':True,'all_bare_English_notes_summary_and_effective_voice_controls_exact':True,'new_audio_repair_not_applied':True,'no_native_or_final_authorized_yet':True,'diff':P.differences(old,d),'PAY_CI_current_alias_book_catalog_PDF_unchanged':True};q=H/'user131-text-implementation-v1.json';q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
