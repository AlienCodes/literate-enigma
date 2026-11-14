from pathlib import Path
import copy, hashlib, importlib.util, json, os, shutil, subprocess, sys
B=Path('/workspace/work/video-audit70-20261113')
H=Path('/dev/shm/article40-user139140-draft-20261114')
BASE=Path('/workspace/work/video-revision-delivery/next-passed-validated/43533004625/40/final-source')
C=H/'candidate-payload'; BE=H/'before'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rels=['视频/脚本/40.json','视频/工具/初稿生成/gen40.py','新版定稿/40-the-glue-that-failed.md']
for rel in rels:
 src=BASE/rel
 assert src.is_file(),src
 dst=BE/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert dst.read_bytes()==src.read_bytes()
 else:shutil.copyfile(src,dst)
 (C/rel).parent.mkdir(parents=True,exist_ok=True)
assert sha(BE/rels[0])=='df869484faa5bfaeebf4ebc2648be395682d653edc896238c08ee8e4730891f1'
old=json.loads((BE/rels[0]).read_text());d=copy.deepcopy(old)
c=d['sentences'][5]['chunks'][0]
assert c['en']=='In his own **summary**, it was a **solution** without a problem.'
assert c['note']=='（solution：解决方案；\nwithout a problem：介词短语作后置定语，\n修饰 solution，\n指这种胶找不到能用它来解决的问题）'
caption='他发明的这种胶当时还找不到合适的用途。“有方案却没问题”，是说发明已经有了，实际用途却还没找到。'
c['note']='（solution：解决方案；\n他发明的这种胶当时还找不到合适的用途。\n“有方案却没问题”，是说发明已经有了，\n实际用途却还没找到。）'
assert c['note'].replace('\n','')=='（solution：解决方案；'+caption+'）'
c=d['sentences'][10]['chunks'][0]
assert c['en']=='The **frustration** gave Fry an idea.'
assert c['zh']=='这份**懊恼**(frustration)让弗莱想到一个主意。'
c['align']=[['The **frustration**','这种**懊恼**(frustration)'],['gave Fry','给了弗莱'],['an idea.','一个主意。']]
c['zh']=''.join(z for e,z in c['align'])
assert c['zh']=='这种**懊恼**(frustration)给了弗莱一个主意。'
assert ' '.join(e for e,z in c['align'])==c['en']
tail=d['sentences'][-1]['chunks'][0]
assert tail['en']=='The laboratory next door had only **leftover** yellow paper.'
marker='\n（简述：';assert tail['note'].count(marker)==1
grammar,summary=tail['note'].split(marker,1)
assert grammar=='（next door：作后置定语，隔壁的）'
tail_caption='便利贴最初用黄色纸，是因为当时隔壁实验室恰好只有剩下的黄纸。后来，黄色成了便利贴的标志性颜色。'
tail['note']=grammar+'\n（便利贴最初用黄色纸，是因为当时隔壁实验室\n恰好只有剩下的黄纸。后来，\n黄色成了便利贴的标志性颜色。）'+marker+summary
for a,b in zip(old['sentences'],d['sentences']):
 assert a['para']==b['para'] and len(a['chunks'])==len(b['chunks'])
 for x,y in zip(a['chunks'],b['chunks']):assert x['en']==y['en'] and len(x['align'])==len(y['align'])
reverse=copy.deepcopy(d)
reverse['sentences'][5]['chunks'][0]['note']=old['sentences'][5]['chunks'][0]['note']
reverse['sentences'][10]=copy.deepcopy(old['sentences'][10])
reverse['sentences'][-1]=copy.deepcopy(old['sentences'][-1])
assert reverse==old
(C/rels[0]).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
s=importlib.util.spec_from_file_location('P',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
gen,issues=P.pure_generator(d);assert gen and not issues;(C/rels[1]).write_text(gen)
sync=Path('/dev/shm/article19-user-review-draft-20261114/thin-validation-v1/mirror/视频/工具/sync_article.py')
assert sha(sync)=='af22d9b97912bf74fb4f4bfae4c595a1475fdfe86c7a473f4e2789d1cccb85d6'
tmp=H/'tmp';tmp.mkdir(exist_ok=True)
canonical=H/'before/40-original-af22-latest-source-canonical.md'
shutil.copyfile(BE/rels[2],canonical)
rb=subprocess.run([sys.executable,str(sync),str(BE/rels[0]),str(canonical)],text=True,capture_output=True,env={**os.environ,'TMPDIR':str(tmp),'PYTHONDONTWRITEBYTECODE':'1'})
(H/'before/40-original-af22-latest-source-canonical.log').write_text(rb.stdout+rb.stderr)
assert rb.returncode==0
md=canonical.read_text()
for si,field in [(5,'note'),(10,'zh'),(18,'note')]:
 previous=old['sentences'][si]['chunks'][0][field];new=d['sentences'][si]['chunks'][0][field]
 previous=previous.replace('\n','')if field=='note'else previous
 new=new.replace('\n','')if field=='note'else new
 assert md.count(previous)==1,(si,field,md.count(previous))
 md=md.replace(previous,new,1)
(C/rels[2]).write_text(md)
check=H/'original-af22-MD-sync-check.md';shutil.copyfile(C/rels[2],check)
r=subprocess.run([sys.executable,str(sync),str(C/rels[0]),str(check)],text=True,capture_output=True,env={**os.environ,'TMPDIR':str(tmp),'PYTHONDONTWRITEBYTECODE':'1'})
(H/'original-af22-MD-sync-check.log').write_text(r.stdout+r.stderr)
assert r.returncode==0 and check.read_bytes()==(C/rels[2]).read_bytes()
report={'kind':'source40-book46-user139140142-two-captions-and-exact-translation-draft','source_id':'40','book_order':'46','draft_only':True,'user_final_authorization':False,'actual_latest_reference_run':43533004625,'before_source_sha256':sha(BE/rels[0]),'source_sha256':sha(C/rels[0]),'GEN_sha256':sha(C/rels[1]),'MD_sha256':sha(C/rels[2]),'source_differences':P.differences(old,d),'all_spoken_English_titles_para_chunks_original_controls_exact':True,'independent_original_summary_and_original_tail_grammar_note_exact':True,'caption_S6_only':caption,'caption_replaces_only_user_screenshot_without_a_problem_grammar_passage':True,'solution_definition_retained':True,'S11_plain_translation':'这种懊恼给了弗莱一个主意。','frustration_focus_unchanged':True,'S19_only_added_accepted_caption':tail_caption,'original_af22_MD_full_bytes_exact':True,'original_delivered_MD_historical_bytes_preserved':sha(BE/rels[2]),'MD_mechanical_current_approved_JSON_summary_sync_baseline':{'path':str(canonical),'sha256':sha(canonical),'reason':'Original af22 synchronizes historical prose summary to the already-approved current final JSON five-point summary without changing the actual current JSON or summary image.'},'PAY_CI_media_alias_PDF_unchanged':True}
p=H/'implementation139140.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(p),'sha256':sha(p),'source_sha256':report['source_sha256'],'GEN_sha256':report['GEN_sha256'],'MD_sha256':report['MD_sha256']},ensure_ascii=False))
