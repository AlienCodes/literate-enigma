"""User091 source65 isolated keyword draft; no production/media/voice changes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

H=Path(__file__).resolve().parent
B=Path('/workspace/work/video-audit70-20261113')
PAY=B/'payload'
C=H/'candidate-payload'
MD=Path('新版定稿/65-the-day-the-doomsday-vault-opened.md')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for rel in [Path('视频/脚本/65.json'),Path('视频/工具/初稿生成/gen65.py'),MD,Path('视频/制作记录/65_待改清单.md'),Path('视频/制作记录/逐句确认/65.json')]:
 p=PAY/rel
 if p.is_file():
  q=H/'before'/rel;q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copyfile(p,q)
old=json.loads((H/'before/视频/脚本/65.json').read_text())
assert sha(H/'before/视频/脚本/65.json')=='78e60dd231df4ac71df83e21a26f82bbf706dc0bef80bee156a36bc287661ede'
new=copy.deepcopy(old)
c=new['sentences'][0]['chunks'][0]
assert c['en']=="On Spitsbergen, in Norway's Svalbard **archipelago**,"
assert c['zh']=='在挪威斯瓦尔巴**群岛**(archipelago)的斯匹次卑尔根岛上，'
assert len(c['align'])==1
c['align'][0][0]=c['align'][0][0].replace('Norway','**Norway**',1)
c['align'][0][1]=c['align'][0][1].replace('挪威','**挪威**(Norway)',1)
c['en']=c['align'][0][0];c['zh']=c['align'][0][1]
assert 'Norway' not in new['allow_clash'];new['allow_clash'].append('Norway')
assert old['sentences'][0]['chunks'][0]['note']==c['note']
assert all(x==y for x,y in zip(old['sentences'][1:],new['sentences'][1:]))
for si,(x,y) in enumerate(zip(old['sentences'],new['sentences']),1):
 for ci,(a,b) in enumerate(zip(x['chunks'],y['chunks']),1):
  assert a['en'].replace('**','')==b['en'].replace('**','')
  assert len(a['align'])==len(b['align'])
assert {k:v for k,v in old.items()if k not in ['sentences','allow_clash']}=={k:v for k,v in new.items()if k not in ['sentences','allow_clash']}
s=importlib.util.spec_from_file_location('original_encoder65',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
code,issues=P.pure_generator(new);assert code and not issues
for rel in ['视频/脚本/65.json','视频/工具/初稿生成/gen65.py',str(MD),'视频/工具/用户同意记录.json','视频/制作记录/65_待改清单.md']:(C/rel).parent.mkdir(parents=True,exist_ok=True)
(C/'视频/脚本/65.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
(C/'视频/工具/初稿生成/gen65.py').write_text(code)
md=(H/'before'/MD).read_text()
for field in ['en','zh']:
 a=old['sentences'][0]['chunks'][0][field];b=c[field];assert md.count(a)==1;md=md.replace(a,b,1)
assert md.count('| archipelago |')==1 and '| Norway |'not in md
md=md.replace('| archipelago |','| Norway | 本文：挪威；n. 挪威（国家名） | 1 |\n| archipelago |',1)
(C/MD).write_text(md)
auth=json.loads((PAY/'视频/工具/用户同意记录.json').read_text())
user=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-091.json')
r=json.loads(user.read_text());assert r['source_id']=='65'and r['book_order']=='37'
auth['记录'].append({'篇':'65','日期':'2026-11-14','原话':r['user_instruction_verbatim'],'用于':'用户091指定S1 Norway与中文挪威独立同key重点并同步词表，保留possessive s与Svalbard普通及原archipelago群岛重点；只隔离JSON/GEN/MD草稿与原文字门和静态核查，未授权37定稿或native，不改既有声音控制、视频、生产PAY/CI、远端当前别名或PDF。','来源文件':str(user),'来源文件SHA256':sha(user)})
(C/'视频/工具/用户同意记录.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
pending=H/'before/视频/制作记录/65_待改清单.md';text=pending.read_text()if pending.exists()else''
text+='\n\n## 2026-11-14 用户091：仅隔离草稿\n\nS1仅Norway与挪威标为重点，词表加入Norway挪威；possessive s、Svalbard及其中文保持普通，原archipelago群岛重点保留。裸英文、chunk/align索引、原小字、末尾五点简述和全部音控逐项保持。未授权本篇定稿或新native，原视频质量待核验状态不改。用户092指出S2 At its end偏轻，另行只读诊断，不凭该文本稿修改音控。PDF不动。\n'
(C/'视频/制作记录/65_待改清单.md').write_text(text)
report={'article':'65','book_order':'37','draft_only':True,'user_record':'091','before_source_sha256':sha(H/'before/视频/脚本/65.json'),'candidate_source_sha256':sha(C/'视频/脚本/65.json'),'candidate_GEN_sha256':sha(C/'视频/工具/初稿生成/gen65.py'),'candidate_MD_sha256':sha(C/MD),'all_bare_English_chunk_align_indices_notes_summary_and_audio_controls_preserved':True,'possessive_and_Svalbard_ordinary':True,'old_archipelago_focus_preserved':True,'no_native_or_final_authorization':True,'no_production_PAY_CI_current_alias_video_audio_PDF_changed':True,'exact_source_delta':P.differences(old,new),'actual_user091_sha256':sha(user)}
(H/'draft-proposal-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='exact_source_delta'},ensure_ascii=False))
