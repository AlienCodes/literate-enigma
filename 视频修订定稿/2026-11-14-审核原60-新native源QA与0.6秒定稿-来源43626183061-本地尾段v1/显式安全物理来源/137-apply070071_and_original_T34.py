"""Draft-only incremental070/071 plus required original T34 align split and actual review ledger."""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,shutil,sys
H=Path(__file__).parent;B=H.parent;C=H/'candidate-payload';V=H/'thin-validation';M=V/'mirror';W=M/'_text-work';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('P60delta',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
hist=H/'candidate-payload/history062-069-v1';hist.mkdir(exist_ok=True)
for rel,name in [('视频/脚本/60.json','draft-source75c-v1.json'),('视频/工具/初稿生成/gen60.py','draft-GEN-v1.py'),('新版定稿/60-the-scientific-giant-who-changed-the-world.md','draft-MD-v1.md')]:
 if not(hist/name).exists():shutil.copyfile(C/rel,hist/name)
old=json.loads((C/'视频/脚本/60.json').read_text());shutil.copyfile(C/'视频/脚本/60.json',W/'scripts/60.json');shutil.copyfile(C/'视频/脚本/60.json',M/'视频/脚本/60.json')
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'}
rc,out=P.execute([sys.executable,M/'视频/工具/拆分组.py','60','--写入'],W,env,V/'60-original-T34-split.log');assert rc==0
split=json.loads((W/'scripts/60.json').read_text());splitdelta=P.differences(old,split);assert splitdelta
assert all(r['path'].startswith('/sentences/0/chunks/1/align') or r['path'] in ['/换行变更已获同意','/核对确认/对齐/S1-2 stars in its apparent','/核对确认/对齐/S1-2 stars in its apparent vicinity'] for r in splitdelta)
for a,b in zip(old['sentences'],split['sentences']):
 assert a['para']==b['para']and len(a['chunks'])==len(b['chunks'])
 for x,y in zip(a['chunks'],b['chunks']):assert x['en']==y['en']and x['zh']==y['zh']and x.get('note')==y.get('note')
new=copy.deepcopy(split);c=new['sentences'][6]['chunks'][0];prior_note=c['note'];explain='此处 to dazzle = 被眩惑 / 被迷晕。\ndazzle 本意是强光刺眼，\n引申为因光环/声望而让人晕头转向、盲目崇拜';c['note']+='\n（'+explain+'）'
c=new['sentences'][9]['chunks'][1]
for a in c['align']:
 a[0]=a[0].replace('the law of','the **law** of');a[1]=a[1].replace('光电效应定律','光电效应**定律**(law)')
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align']);assert '**law**'in c['en']and '**定律**(law)'in c['zh'];new['allow_clash'].append('law')
source=C/'视频/脚本/60.json';source.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');text,issues=P.pure_generator(new);assert text and not issues;(C/'视频/工具/初稿生成/gen60.py').write_text(text)
md=C/'新版定稿/60-the-scientific-giant-who-changed-the-world.md';t=md.read_text();oldnote=prior_note.replace('\n','');assert t.count(oldnote)==1;t=t.replace(oldnote,oldnote+'（'+explain.replace('\n','')+'）',1)
a=old['sentences'][9]['chunks'][1];b=new['sentences'][9]['chunks'][1]
for key in ['en','zh']:
 assert t.count(a[key])==1;t=t.replace(a[key],b[key],1)
assert '| law |'not in t and t.count('| governs |')==1;t=t.replace('| governs |','| law | 本文：定律；n. 定律，规律（the law of gravity）；法律，法规 | 4 |\n| governs |',1);md.write_text(t)
root=Path('/workspace/work/first50-review-release');auth=C/'视频/工具/用户同意记录.json';d=json.loads(auth.read_text())
for n in [70,71]:
 p=root/f'USER-REVIEW-2026-11-14-{n:03}.json';r=json.loads(p.read_text());assert r['source_id']=='60';d['记录'].append({'篇':'60','日期':'2026-11-14','原话':r['user_instruction_verbatim'],'用于':f'用户{n:03}仅本篇隔离draft编辑：070语境to dazzle说明加上且保原grammar；071仅S10 law定律重点允许撞词，光电效应及S10RoyalSwedish普通；未获36final/native授权，不改声控/PAY/CI/远端别名/PDF。','来源文件':str(p),'来源文件SHA256':sha(p)})
auth.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
work=C/'视频/制作记录/60_待改清单.md';t=work.read_text();t+='\n\n## 2026-11-14 用户062–071真实原审核引文及实施定位（仅草稿）\n\n'
for n in range(62,72):
 p=root/f'USER-REVIEW-2026-11-14-{n:03}.json';r=json.loads(p.read_text());t+=f'### 用户{n:03}原话\n\n'+r['user_instruction_verbatim']+'\n\n'
t+='实施定位（以下为编辑者据原句和用户指定目标记录的差异，不冒用户逐字话）：\nS3会使经过它附近的星光偏折→会使星光偏折/偏离方向，依据064原话。\nS4新增说明全文：1919年11月6日，日食观测结果在两学会的联席会议上公布，人们认为它支持了爱因斯坦的预言：太阳引力会使星光偏折。依据066/067。\nS6成了举世皆知的名人→成了一位全球性的名人，依据069；celebrity名人重点保留。\nS7在原Stockholm和prove说明后加此处to dazzle被眩惑/被迷晕及用户强光/光环引申解释，依据070。\nS10仅law定律加重点，依据071；S11 That law音频由独立auditor只读诊断，072没有新增focus或音控实施授权。\n';work.write_text(t)
assert old['sentences'][-1]==new['sentences'][-1]
for a,b in zip(old['sentences'],new['sentences']):
 for x,y in zip(a['chunks'],b['chunks']):assert x['en'].replace('**','')==y['en'].replace('**','')
assert{k:v for k,v in split.items()if k not in ['sentences','allow_clash']}=={k:v for k,v in new.items()if k not in ['sentences','allow_clash']}
r=dict(article='60',book_order='36',draft_only=True,final_or_native_authorized=False,source_sha256=sha(source),GEN_sha256=sha(C/'视频/工具/初稿生成/gen60.py'),MD_sha256=sha(md),original_T34_split_exit=rc,original_T34_split_diff=splitdelta,new_070_note_actual_text=explain.replace('\n',''),new_071_law_focus_only_S10=True,all_bare_English_chunks_and_effective_DSP_exact=True,original_S15_summary_raw_exact=True,PAY_CI_remote_audio_PDF_unchanged=True,incremental_delta=P.differences(old,new))
(H/'draft070071-original-T34-implementation-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['original_T34_split_diff','incremental_delta']},ensure_ascii=False))
