from pathlib import Path
import copy,difflib,hashlib,importlib.util,json,os,shutil,subprocess,sys
H=Path(__file__).parent;B=Path('/workspace/work/video-audit70-20261113');PAY=B/'payload';C=H/'candidate-payload';BE=H/'before';M19=Path('/dev/shm/article19-user-review-draft-20261114/thin-validation-v1/mirror');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('P',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
rels=['视频/脚本/52.json','视频/工具/初稿生成/gen52.py','新版定稿/52-the-killer-smog-of-1952.md'];actualmd=Path('/workspace/work/video-revision-delivery/next-passed-validated/43533004625/52/final-source')/rels[2]
for rel in rels:
 src=PAY/rel if(PAY/rel).is_file()else actualmd;dst=BE/rel;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists()or dst.read_bytes()==src.read_bytes()
 if not dst.exists():shutil.copyfile(src,dst)
 (C/rel).parent.mkdir(parents=True,exist_ok=True)
assert sha(BE/rels[0])=='832249bb44617d38ede75560a5e57af6ba79ec284c9609407cb30ce879f6f862'
old=json.loads((BE/rels[0]).read_text());d=copy.deepcopy(old);c=d['sentences'][8]['chunks'][1];assert c['en']=='but a 1954 Ministry of Health report blamed later deaths on **influenza**.'
for pair in c['align']:
 pair[0]=pair[0].replace('blamed','**blamed**').replace('on **influenza**.','**on** **influenza**.')
 pair[1]=pair[1].replace('把','**把**(blamed on)').replace('归因于','**归咎于**(blamed on)')
c['en']=' '.join(e for e,z in c['align']);c['zh']=''.join(z for e,z in c['align'])
assert 'later deaths' in c['en'] and '**blamed** later deaths **on**'in c['en'];assert c['zh']=='但卫生部1954年的一份报告**把**(blamed on)后来的死亡**归咎于**(blamed on)**流感**(influenza)。'
note='人们把煤烟当成寻常的生活麻烦，\n很少想到家中取暖的煤火也是污染元凶。\n这种掉以轻心，或许也是政府应对不够积极的原因之一。'
assert not d['sentences'][12]['chunks'][0].get('note');d['sentences'][12]['chunks'][0]['note']=note
assert d['sentences'][12]['chunks'][0]['en']=="Such **complacency** may help to explain the government's **grudging** **response**."
rootdecision=Path('/dev/shm/root-source52-measured-minimum-opening-gain-selection.json');assert sha(rootdecision)=='64871acd352cf8808a9c468e0fff2f04ec2e050f9bc95fe2fe87b86bf4dc1cf8'
assert '分段增益dB'not in d or all(k not in d.get('分段增益dB',{}).get(si,{})for si,k in[('S1','2'),('S5','1')])
for si,k in[('S1','2'),('S5','1')]:d.setdefault('分段增益dB',{}).setdefault(si,{})[k]=1.5
d['核对确认'].setdefault('同词异译',{})['blamed on：把/归咎于']='不是两种译法：blame A on B 是把A归咎于B，本文blamed later deaths on influenza；英文blamed和on是同一用法的两部分，中文把和归咎于是同一谓语的两部分，A后来的死亡普通，原influenza流感重点保留。'
for a,b in zip(old['sentences'],d['sentences']):
 assert len(a['chunks'])==len(b['chunks'])and a['para']==b['para']
 for x,y in zip(a['chunks'],b['chunks']):assert x['en'].replace('**','')==y['en'].replace('**','')and len(x['align'])==len(y['align'])
assert d['sentences'][-1]==old['sentences'][-1];assert sum('人们把煤烟当成' in c.get('note','')for s in d['sentences']for c in s['chunks'])==1
reverse=copy.deepcopy(d);reverse['sentences']=copy.deepcopy(old['sentences']);reverse['核对确认']=copy.deepcopy(old['核对确认']);reverse.pop('分段增益dB',None)if'分段增益dB'not in old else reverse.__setitem__('分段增益dB',copy.deepcopy(old['分段增益dB']));assert reverse==old
(C/rels[0]).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');gen,issues=P.pure_generator(d);assert gen and not issues;(C/rels[1]).write_text(gen)
# Original af22 turns the latest approved JSON's existing raw detailed five-point summary into baseline MD; no old-summary rollback.
canonical=H/'before/52-latest-PAY-original-sync-canonical.md';shutil.copyfile(actualmd,canonical);tmp=H/'tmp';tmp.mkdir(exist_ok=True)
cmd=[sys.executable,str(M19/'视频/工具/sync_article.py'),str(BE/rels[0]),str(canonical)];r=subprocess.run(cmd,text=True,capture_output=True,env={**os.environ,'TMPDIR':str(tmp),'PYTHONDONTWRITEBYTECODE':'1'});(H/'before/52-current-PAY-original-MD-sync.log').write_text(r.stdout+r.stderr);assert r.returncode==0
(H/'before/52-original-actual-MD-to-latest-PAY-sync.diff').write_text(''.join(difflib.unified_diff(actualmd.read_text().splitlines(True),canonical.read_text().splitlines(True),fromfile=str(actualmd),tofile=str(canonical))))
t=canonical.read_text();a=old['sentences'][8]['chunks'][1];b=d['sentences'][8]['chunks'][1]
for f in['en','zh']:assert t.count(a[f])==1;t=t.replace(a[f],b[f],1)
a=old['sentences'][12]['chunks'][0]['zh'];assert t.count(a)==1;t=t.replace(a,a+note.replace('\n',''),1)
row='| blamed on | 本文：把……归咎于；v. (blame A on B) 把A归咎于B；将A的责任归于B（blamed为blame的过去式） | 3 |\n';assert '| blamed on |'not in t and t.count('| influenza |')==1;t=t.replace('| influenza |',row+'| influenza |',1);(C/rels[2]).write_text(t)
auth=json.loads((PAY/'视频/工具/用户同意记录.json').read_text());records=[]
for n in range(117,125):
 p=Path(f'/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-{n}.json');assert p.exists(),p;raw=json.loads(p.read_text());q=raw['user_instruction_verbatim'];records.append({'feedback':n,'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
 auth['记录'].append({'篇':'52','日期':'2026-11-14','原话':q,'用于':f'用户{n:03}伦敦source52/frozenbook41：120重点blamed…on及把…归咎于；123124已接受小字仅Such complacency所在S13；122已4K定稿、118和122spoken逗号修改由原接口/实际新母审修，display英文逗号保留；117119短段头两gain由root实测决定选择，非伪称用户给具体dB。','来源文件':str(p),'来源文件SHA256':sha(p)})
(C/'视频/工具/用户同意记录.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
work=PAY/'视频/制作记录/52_待改清单.md';work=work if work.exists()else M19/'视频/制作记录/52_待改清单.md';wp=C/'视频/制作记录/52_待改清单.md';wp.parent.mkdir(parents=True,exist_ok=True);wp.write_text(work.read_text()+'\n\n## 用户117–124 source52/frozenbook41本轮定稿\n\n120指定S9C2 blamed later deaths on同key/中文把…归咎于，原influenza流感保留；123124指定S13 Such complacency页唯一新增小字全文，S18末页/summary不加。122正式定稿，S4 though两边与S18整句仅spoken逗号需新母接口落实，displayEnglish及原中文/notes/summary不改。root实测决定64871只增S1段2及S5段1各+1.5dB，保原auto/S5BOOST；本候选未实施spoken修改、不是最终新声/WAVhash。\n')
r={'source_id':'52','frozen_book_order':'41','user122_final_authorized':True,'kind':'presentation120123124-and-rootselected-two-opening-gains-before-spoken-interface','actual_new_spoken_S4_S18_still_pending':True,'gain_only_diagnostic_hashes_not_final_new_voice':True,'before_source_sha256':sha(BE/rels[0]),'source_sha256':sha(C/rels[0]),'GEN_sha256':sha(C/rels[1]),'MD_sha256':sha(C/rels[2]),'original_af22_sync_sha256':sha(M19/'视频/工具/sync_article.py'),'MD_base_actual_latest_handoff':'/workspace/work/video-revision-delivery/next-passed-validated/43533004625/52/archive-handoff.json','latest_PAY_approved_five_point_summary_raw_preserved':True,'all_bare_display_English_and_chunks_align_indices_paragraphs_exact':True,'all_original_notes_preserved_except_new_S13_only_note':True,'root_selected_only_gain_leaves':{'/分段增益dB/S1/2':1.5,'/分段增益dB/S5/1':1.5},'root_gain_selection':{'path':str(rootdecision),'sha256':sha(rootdecision)},'specific_caption_anchor':'S13C1 Such complacency may help to explain the government\'s grudging response.','caption_fulltext':note.replace('\n',''),'caption_not_on_S18_or_summary':True,'original_spoken_English_same_current_mother_no_interface_yet':True,'effective_original_controls_except_two_root_selected_gains_exact':True,'source_diff':P.differences(old,d),'actual_raw_feedback':records,'PAY_CI_alias_media_PDF_unchanged':True}
p=H/'source52-presentation120123124-and-opening-gain-implementation-v1.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in['source_diff','actual_raw_feedback']},ensure_ascii=False))
