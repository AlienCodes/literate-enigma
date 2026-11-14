"""Draft-only073,074,075: requested Chinese meanings and two focus phrases."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
H=Path(__file__).parent;B=H.parent;C=H/'candidate-payload';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();s=importlib.util.spec_from_file_location('P60late',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
hist=C/'history070071-v2';hist.mkdir(exist_ok=True)
for rel,name in [('视频/脚本/60.json','draft-source-d5dd-v2.json'),('视频/工具/初稿生成/gen60.py','draft-GEN-v2.py'),('新版定稿/60-the-scientific-giant-who-changed-the-world.md','draft-MD-v2.md')]:
 if not(hist/name).exists():shutil.copyfile(C/rel,hist/name)
old=json.loads((C/'视频/脚本/60.json').read_text());new=copy.deepcopy(old)
c=new['sentences'][10]['chunks'][0]
for pair in c['align']:pair[1]=pair[1].replace('**决定了**(governs)','**规定了**(governs)').replace('**打出**(ejects)','**打出/击出**(ejects)')
c=new['sentences'][12]['chunks'][1]
for pair in c['align']:pair[0]=pair[0].replace('miss','**miss**');pair[1]=pair[1].replace('错过','**错过**(miss)')
c=new['sentences'][14]['chunks'][0]
for pair in c['align']:pair[0]=pair[0].replace('after all','**after all**');pair[1]=pair[1].replace('终究','**终究还是**(after all)')
changed=[(11,1),(13,2),(15,1)]
for si,ci in changed:
 c=new['sentences'][si-1]['chunks'][ci-1];c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align'])
new['allow_clash']+=['miss','after all'];source=C/'视频/脚本/60.json';source.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');code,issues=P.pure_generator(new);assert code and not issues;(C/'视频/工具/初稿生成/gen60.py').write_text(code)
md=C/'新版定稿/60-the-scientific-giant-who-changed-the-world.md';t=md.read_text()
for si,ci in changed:
 a=old['sentences'][si-1]['chunks'][ci-1];b=new['sentences'][si-1]['chunks'][ci-1]
 for field in ['en','zh']:
  if a[field]!=b[field]:assert t.count(a[field])==1,(si,ci,field);t=t.replace(a[field],b[field],1)
for a,b in [('| governs | 本文：决定了；','| governs | 本文：规定了；'),('| ejects | 本文：打出；','| ejects | 本文：打出/击出；')]:assert t.count(a)==1;t=t.replace(a,b,1)
assert '| miss |'not in t and t.count('| ceremony |')==1;t=t.replace('| ceremony |','| miss | 本文：错过；v. 错过，未赶上；未击中；想念 | 4 |\n| ceremony |',1)
assert '| after all |'not in t and t.count('| honoured |')==1;t=t.replace('| honoured |','| after all | 本文：终究还是；短语. 终究，毕竟；（解释原因）别忘了 | 5 |\n| honoured |',1);md.write_text(t)
root=Path('/workspace/work/first50-review-release');auth=C/'视频/工具/用户同意记录.json';a=json.loads(auth.read_text());work=C/'视频/制作记录/60_待改清单.md';w=work.read_text()
for n in [73,74,75]:
 p=root/f'USER-REVIEW-2026-11-14-{n:03}.json';r=json.loads(p.read_text());assert r['source_id']=='60';a['记录'].append({'篇':'60','日期':'2026-11-14','原话':r['user_instruction_verbatim'],'用于':f'用户{n:03}仅隔离draft指定词义/重点，governs规定了/ejects打出/击出、miss错过、after all整组终究还是及本篇词表同步；新增miss和after all点名词允许撞词，原focus保留；072音频诊断另域未实施，未获36final/native授权。','来源文件':str(p),'来源文件SHA256':sha(p)});w+=f'\n### 用户{n:03}原话（仅草稿）\n\n'+r['user_instruction_verbatim']+'\n'
auth.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');w+='\n编辑执行定位（非用户逐字引文）：S11原决定了→规定了，原打出→打出/击出，分别同governs和ejects重点；S13仅miss错过重点，将普通；S15终究→终究还是四字同after all key，登上了诺贝尔的普通、podium讲台重点保留。S7新增说明实际全文为：此处 to dazzle = 被眩惑 / 被迷晕。dazzle 本意是强光刺眼，引申为因光环/声望而让人晕头转向、盲目崇拜。该前导语为root允许的语境澄清，不当作一般被动语法。\n';work.write_text(w)
for a,b in zip(old['sentences'],new['sentences']):
 assert len(a['chunks'])==len(b['chunks'])
 for x,y in zip(a['chunks'],b['chunks']):assert x['en'].replace('**','')==y['en'].replace('**','')and x.get('note')==y.get('note')and len(x['align'])==len(y['align'])
assert{k:v for k,v in old.items()if k not in ['sentences','allow_clash']}=={k:v for k,v in new.items()if k not in ['sentences','allow_clash']}
r=dict(article='60',book_order='36',draft_only=True,final_or_native_authorized=False,source_sha256=sha(source),GEN_sha256=sha(C/'视频/工具/初稿生成/gen60.py'),MD_sha256=sha(md),delta=P.differences(old,new),all_bare_English_chunk_indices_and_DSP_exact=True,all_notes_and_summary_raw_preserved=True,new_body_tail_focus_and_translation_changed_by075=True,new_body_tail_RGB_or_geometry_identity_not_claimed=True,focus_correspondence_preserved_not_fixed_RGB=True,audio072_still_open_not_repaired=True,PAY_CI_remote_alias_audio_PDF_unchanged=True)
(H/'draft073075-implementation-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='delta'},ensure_ascii=False))
