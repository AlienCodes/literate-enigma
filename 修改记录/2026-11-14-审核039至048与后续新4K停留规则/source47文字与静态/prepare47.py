"""Only user035/038/039 two page notes/layout; preserve actual accepted47 voice/content."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,shutil
B=Path('/workspace/work/video-audit70-20261113');H=Path(__file__).parent;PAY=B/'payload';C=H/'candidate-payload';D=Path('/workspace/work/video-revision-delivery/next-passed-validated/43533004625/47');mdrel=Path('新版定稿/47-shadows-of-wolves-over-yellowstone.md');rels=[Path('视频/脚本/47.json'),Path('视频/工具/初稿生成/gen47.py'),mdrel];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('source47_original_encoder',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
for rel in rels:
 p=H/'before'/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():shutil.copyfile(PAY/rel,p)
 (C/rel).parent.mkdir(parents=True,exist_ok=True)
assert sha(PAY/'视频/脚本/47.json')=='0417489c8a672e7e63d46c2239d847acabda2d93160cabed3b0fb14f701ac39a'
assert(PAY/mdrel).read_bytes()==(D/'final-source'/mdrel).read_bytes()
reference=H/'actual-accepted-reference';reference.mkdir(exist_ok=True)
for source,dest in [(D/'final-source/视频/脚本/47.json',reference/'47-actual-last-accepted-used-source.json'),(D/'final-source'/mdrel,reference/'47-actual-last-accepted-used.md'),(D/'archive-handoff.json',reference/'47-original-accepted-archive-handoff.json')]:shutil.copyfile(source,dest)
rdir=Path('/workspace/work/first50-review-release');records={}
for i in[35,36,38,39]:
 p=rdir/f'USER-REVIEW-2026-11-14-{i:03}.json';records[i]=json.loads(p.read_text());out=H/'feedback'/p.name;out.parent.mkdir(exist_ok=True);shutil.copyfile(p,out)
old=json.loads((H/'before/视频/脚本/47.json').read_text());new=copy.deepcopy(old);orig_note=new['sentences'][3]['chunks'][3]['note'];one=orig_note.replace(' ->\n','→');assert'\n'not in one and len(one)==64
new['sentences'][3]['chunks'][3]['note']=one
first=new['sentences'][3]['chunks'][0];first['align'][0][0]+='{{一行}}';first['en']=' '.join(a for a,b in first['align'])
accepted=records[38]['accepted_small_text'];lines=['（“狼的影子”比喻狼对生态系统的影响。','作者认为，流行故事可能夸大了狼的作用；','柳树恢复、河岸变稳等变化还受其他因素影响，','现有研究尚无定论，真实情况比故事复杂。）'];assert ''.join(lines)=='（'+accepted+'）'
assert new['sentences'][12]['chunks'][1]['note']=='（than the fable suggested：比较状语从句）';assert new['sentences'][12]['chunks'][2]['note']=='（the science messier：省略了 looks）';new['sentences'][12]['chunks'][1].pop('note');new['sentences'][12]['chunks'][2]['note']='\n'.join(lines)
q39=records[39]['user_instruction_verbatim'];q38=records[38]['user_instruction_verbatim'];new.setdefault('说明放宽特批',{})['S4']={'倍数':1.5,'依据':'用户2026-11-14反馈035明确指定四排因果说明合成一横行、保原全部内容；039用户定稿原话：“'+q39+'”。root对实际正文43→47px、说明27→29px、1856/1860px实测已批准，仅S4首chunk使用既有{{一行}}显示标记、说明≤1.5倍正文宽的窄布局特批（root实看本方案后已批准）；原L19及renderer其他页默认保持。'}
new.setdefault('换行变更已获同意',{})['S4']='用户2026-11-14反馈035指定原因果说明四行合一横行；039定稿原话：“'+q39+'”；仅说明换行和该页合理放大，原完整内容均保持。'
new['换行变更已获同意']['S13']='用户2026-11-14原话：“'+q38+'” 依038已接受全文替换本页两条语法小字，按标点折行以舒适阅读；039已定稿。'
def clean_display(c):
 o=copy.deepcopy(c);o.pop('note',None);o['en']=re.sub(r'\{\{.*?\}\}','',o['en']);o['align']=[[re.sub(r'\{\{.*?\}\}','',a),b]for a,b in o['align']];return o
assert[[clean_display(c)for c in s['chunks']]for s in old['sentences']]==[[clean_display(c)for c in s['chunks']]for s in new['sentences']]
assert all(s==new['sentences'][i]for i,s in enumerate(old['sentences'])if i not in(3,12));assert{k:v for k,v in old.items()if k not in('sentences','说明放宽特批','换行变更已获同意')}=={k:v for k,v in new.items()if k not in('sentences','说明放宽特批','换行变更已获同意')}
text,issues=P.pure_generator(new);assert text and not issues;(C/'视频/脚本/47.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');(C/'视频/工具/初稿生成/gen47.py').write_text(text)
md=(H/'before'/mdrel).read_text();a=orig_note.replace('\n','');assert md.count(a)==1;md=md.replace(a,one);a='（than the fable suggested：比较状语从句）（the science messier：省略了 looks）';assert md.count(a)==1;md=md.replace(a,'（'+accepted+'）');(C/mdrel).write_text(md)
auth=PAY/'视频/工具/用户同意记录.json';a=json.loads(auth.read_text());shutil.copyfile(auth,H/'before/用户同意记录.json')
for idx,scope in[(38,'换行变更已获同意.S13；仅指定页删除than.../省略looks两语法说明，放已接受通俗解释；不动S14结语、原正文/重点/5点summary/DSP'),(39,'说明放宽特批.S4（1.5倍正文宽）、S4C1既有{{一行}}显示标记、换行变更已获同意.S4；035原64字因果说明单行且47px正文、29px说明、1856px在屏界内；本篇已定稿4K，所有其他内容/原声保全；PDF全暂停')]:
 p=rdir/f'USER-REVIEW-2026-11-14-{idx:03}.json';a['记录'].append({'篇':'47','日期':'2026-11-14','原话':records[idx]['user_instruction_verbatim'],'用于':scope,'来源':str(p),'来源文件SHA256':sha(p)})
(C/'视频/工具/用户同意记录.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
rep={'article':'47','book_order':'32','candidate_source_sha256':sha(C/'视频/脚本/47.json'),'candidate_GEN_sha256':sha(C/'视频/工具/初稿生成/gen47.py'),'candidate_MD_sha256':sha(C/mdrel),'before_source_sha256':sha(H/'before/视频/脚本/47.json'),'latest_accepted_used_source_exact':True,'latest_accepted_used_MD_exact_before':True,'accepted_final_MP4_sha256':'41a80d97ec08a8308df802694e82cd00cbd2f41c3d2f5496adf2001ef8b10c98','actual_last_accepted_used_source':str(reference/'47-actual-last-accepted-used-source.json'),'actual_Git_last_sent_source_for_L13_snapshot':str(H/'next-native-root-actual-last-sent47.json'),'all_visible_English_main_Chinese_focus_original_chunk_boundaries_and_audio_controls_exact_after_removing_only_existing_display_marker':True,'one_existing_display_only_marker_added_to_S4C1_en_and_align':True,'raw_English_and_alignment_source_identity_not_claimed':True,'all_other_pages_including_real_S14_conclusion_and_full_summary_exact':True,'S4_original64_characters_oneline_content_preserved':True,'S13_only_new_accepted_explanation_both_grammar_notes_removed':True,'diff':P.differences(old,new),'published_to_PAY':False,'PDF_produced_or_changed':False};(H/'proposal-report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in rep.items()if k!='diff'},ensure_ascii=False))
