from pathlib import Path
import json,hashlib,importlib.util,copy
H=Path('/workspace/work/video-audit70-20261113/article60-user-review-draft-20261114');B=H.parent;C=H/'candidate-payload';R=Path('/dev/shm/article60-text-review-draft-20261114');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('P',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
old=json.loads((C/'history070071-v2/draft-source-d5dd-v2.json').read_text());p=C/'视频/脚本/60.json';d=json.loads(p.read_text());assert sha(p)=='8be8d9d4e0efcc6552b737b312af5697e188cdef4d70aeb8bb02976ba6cdc6fd'
assert '**规定了**(governs)'in d['sentences'][10]['chunks'][0]['zh']and '**打出/击出**(ejects)'in d['sentences'][10]['chunks'][0]['zh'];assert '**miss**'in d['sentences'][12]['chunks'][1]['en'];assert '**终究还是**(after all)'in d['sentences'][14]['chunks'][0]['zh']
for x,y in zip(old['sentences'],d['sentences']):
 assert len(x['chunks'])==len(y['chunks'])
 for a,b in zip(x['chunks'],y['chunks']):assert a['en'].replace('**','')==b['en'].replace('**','')and a.get('note')==b.get('note')and len(a['align'])==len(b['align'])
assert{k:v for k,v in old.items()if k not in['sentences','allow_clash']}=={k:v for k,v in d.items()if k not in['sentences','allow_clash']}
code,issues=P.pure_generator(d);assert code and not issues;assert(C/'视频/工具/初稿生成/gen60.py').read_text()==code
root=Path('/workspace/work/first50-review-release');q={73:'在这个地方，这个决定了govern 他下面就这种意思，由决定了改为规定了。改为 规定了\n\n打出 改为 打出/击出',74:'在这个地方就miss 这个miss，这个miss标注为重点词 错过',75:'在这个地方，这个after all标注为重点词 改为 终究还是 重点词汇标注重点词汇终究还是'}
auth=C/'视频/工具/用户同意记录.json';a=json.loads(auth.read_text());work=C/'视频/制作记录/60_待改清单.md';w=work.read_text();evidence=[]
for n,quote in q.items():
 ledger=root/f'USER-REVIEW-2026-11-14-{n:03}.json'
 if ledger.exists():
  record=json.loads(ledger.read_text());assert record['source_id']=='60';quote=record['user_instruction_verbatim'];origin={'path':str(ledger),'sha256':sha(ledger),'kind':'actual-root-ledger'}
 else:origin={'kind':'root-delegated-user-verbatim-task-message','actual_ledger_not_yet_present':True,'no_user_words_invented':True}
 ev={'article':'60','book_order':'36','feedback':n,'user_instruction_verbatim':quote,'origin':origin,'draft_only':True,'native_authorized':False};ep=R/f'actual-feedback-{n:03}-draft-intake.json';ep.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n');evidence.append({'path':str(ep),'sha256':sha(ep)})
 if not any(x.get('篇')=='60'and x.get('来源反馈号')==f'{n:03}'for x in a['记录']):a['记录'].append({'篇':'60','日期':'2026-11-14','原话':quote,'用于':f'用户{n:03}仅隔离draft指定词义或重点及本篇词表同步；miss和after all为本轮用户点名词允许撞词，原focus保留；072音频诊断另域尚未实施，无36final/native授权。','来源反馈号':f'{n:03}','来源文件':str(ep),'来源文件SHA256':sha(ep)})
 marker=f'### 用户{n:03}原话（仅草稿）'
 if marker not in w:w+='\n'+marker+'\n\n'+quote+'\n'
auth.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
loc='编辑执行定位（非用户逐字引文）：S11原决定了→规定了，原打出→打出/击出，分别同governs和ejects重点；S13仅miss错过重点，将普通；S15终究→终究还是四字同after all key，登上了诺贝尔的普通、podium讲台重点保留。S7新增说明实际全文为：此处 to dazzle = 被眩惑 / 被迷晕。dazzle 本意是强光刺眼，引申为因光环/声望而让人晕头转向、盲目崇拜。该前导语为root允许的语境澄清，不当作一般被动语法。'
if loc not in w:w+='\n'+loc+'\n'
work.write_text(w)
r=dict(article='60',book_order='36',draft_only=True,final_or_native_authorized=False,source_sha256=sha(p),GEN_sha256=sha(C/'视频/工具/初稿生成/gen60.py'),MD_sha256=sha(C/'新版定稿/60-the-scientific-giant-who-changed-the-world.md'),delta=P.differences(old,d),all_bare_English_chunk_indices_and_DSP_exact=True,all_notes_and_summary_raw_preserved=True,new_body_tail_focus_and_translation_changed_by075=True,new_body_tail_RGB_or_geometry_identity_not_claimed=True,focus_correspondence_preserved_not_fixed_RGB=True,audio072_still_open_not_repaired=True,PAY_CI_remote_alias_audio_PDF_unchanged=True,feedback_evidence=evidence,partial_first_apply_source_GEN_MD_were_already_written=True,original_partial_apply_stopped_on_unavailable074_ledger=True)
out=R/'draft073075-implementation-report.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='delta'},ensure_ascii=False))
