"""Source65 isolated country-focus draft plus unchanged original mandatory align splitting."""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).resolve().parent;B=Path('/workspace/work/video-audit70-20261113');C=H/'candidate-payload';M=H/'thin-validation/mirror';W=M/'_text-work'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('orig65encoder093',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
user=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-093.json');r=json.loads(user.read_text());assert r['source_id']=='65'and r['book_order']=='37'
history=H/'history091-v1';history.mkdir(exist_ok=True)
for rel,name in [('视频/脚本/65.json','source.json'),('视频/工具/初稿生成/gen65.py','GEN.py'),('新版定稿/65-the-day-the-doomsday-vault-opened.md','manuscript.md')]:
 if not(history/name).exists():shutil.copyfile(C/rel,history/name)
old=json.loads((history/'source.json').read_text());new=copy.deepcopy(old);c=new['sentences'][10]['chunks'][0]
assert c['align'][0]==['In Lebanon and Morocco,','在黎巴嫩和摩洛哥，']
c['align'][0]=['In **Lebanon** and **Morocco**,','在**黎巴嫩**(Lebanon)和**摩洛哥**(Morocco)，']
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align']);new['allow_clash']+=['Lebanon','Morocco']
(W/'scripts/65.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');shutil.copyfile(W/'scripts/65.json',M/'视频/脚本/65.json')
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'}
rc,text=P.execute([sys.executable,M/'视频/工具/拆分组.py','65','--写入'],W,env,H/'thin-validation/65-original-T34-091093-split.log');assert rc==0
split=json.loads((W/'scripts/65.json').read_text());delta=P.differences(new,split)
assert delta and all(r['path'].startswith('/sentences/0/chunks/0/align')or r['path'].startswith('/sentences/10/chunks/0/align')or r['path'].startswith('/核对确认/对齐/')or r['path']=='/换行变更已获同意' for r in delta)
for a,b in zip(old['sentences'],split['sentences']):
 assert a['para']==b['para']and len(a['chunks'])==len(b['chunks'])
 for x,y in zip(a['chunks'],b['chunks']):assert x['en'].replace('**','')==y['en'].replace('**','')and x.get('note')==y.get('note')
assert old['sentences'][-1]==split['sentences'][-1]
(C/'视频/脚本/65.json').write_text(json.dumps(split,ensure_ascii=False,indent=2)+'\n');code,issues=P.pure_generator(split);assert code and not issues;(C/'视频/工具/初稿生成/gen65.py').write_text(code)
md=C/'新版定稿/65-the-day-the-doomsday-vault-opened.md';t=(history/'manuscript.md').read_text()
for key in ['en','zh']:
 a=old['sentences'][10]['chunks'][0][key];b=split['sentences'][10]['chunks'][0][key];assert t.count(a)==1;t=t.replace(a,b,1)
assert t.count('| sowed |')==1 and '| Lebanon |'not in t and '| Morocco |'not in t
t=t.replace('| sowed |','| Lebanon | 本文：黎巴嫩；n. 黎巴嫩（国家名） | 4 |\n| Morocco | 本文：摩洛哥；n. 摩洛哥（国家名） | 4 |\n| sowed |',1);md.write_text(t)
auth=C/'视频/工具/用户同意记录.json';d=json.loads(auth.read_text());d['记录'].append({'篇':'65','日期':'2026-11-14','原话':r['user_instruction_verbatim'],'用于':'用户093只给S11 Lebanon黎巴嫩与Morocco摩洛哥各独立重点，词表同步；In/在及and/和普通，原sowed种下等重点、小字与五点简述完整。用户091/093新增重点后按原拆分组T34机械拆align组，英文和中文连续正文都不改，原对齐确认按原工具迁移。仅隔离草稿，未授权37定稿/native，不改音频控制、生产PAY/CI/远端视频/PDF。','来源文件':str(user),'来源文件SHA256':sha(user)});auth.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=C/'视频/制作记录/65_待改清单.md';t=p.read_text();t+='\n\n## 2026-11-14 用户093与原T34机械对齐\n\nS11 Lebanon/黎巴嫩和Morocco/摩洛哥各独立同key重点，In/在、and/和普通，原sowed/种下了等重点不变。新增词同步速查表。原拆分组程序仅拆S1/S11中同序重点，裸英文/连续中文/notes和音控不改；旧091 T34真实失败记录保留，不将失败冒充通过。本篇仍仅草稿与092音频诊断，未定稿/PDF不动。\n';p.write_text(t)
report={'article':'65','book_order':'37','draft_only':True,'user_records':['091','093'],'original_T34_split_exit':rc,'original_T34_split_delta':delta,'source_sha256':sha(C/'视频/脚本/65.json'),'GEN_sha256':sha(C/'视频/工具/初稿生成/gen65.py'),'MD_sha256':sha(md),'all_bare_English_continuous_Chinese_and_notes_preserved_by_alignment_split':True,'all_effective_audio_controls_preserved':True,'original_last_sentence_summary_exact':True,'PAY_CI_audio_video_PDF_unchanged':True,'original_091_T34_failure_preserved':True,'incremental_source_delta':P.differences(old,split)}
(H/'draft091093-original-T34-implementation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['original_T34_split_delta','incremental_source_delta']},ensure_ascii=False))
