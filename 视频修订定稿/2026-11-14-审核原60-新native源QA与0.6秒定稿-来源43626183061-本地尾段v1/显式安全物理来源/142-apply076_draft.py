from pathlib import Path
import json,hashlib,copy,shutil,importlib.util
B=Path('/workspace/work/video-audit70-20261113');H=B/'article60-user-review-draft-20261114';C=H/'candidate-payload';O=Path('/dev/shm/article60-text-review-draft-20261114');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();s=importlib.util.spec_from_file_location('P',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
p=C/'视频/脚本/60.json';assert sha(p)=='8be8d9d4e0efcc6552b737b312af5697e188cdef4d70aeb8bb02976ba6cdc6fd';old=json.loads(p.read_text());new=copy.deepcopy(old);hist=C/'history062075-v3';hist.mkdir(exist_ok=True)
for rel,name in[('视频/脚本/60.json','draft-source-8be8-v3.json'),('视频/工具/初稿生成/gen60.py','draft-GEN-v3.py'),('新版定稿/60-the-scientific-giant-who-changed-the-world.md','draft-MD-v3.md')]:
 assert not(hist/name).exists();shutil.copyfile(C/rel,hist/name)
assert new['title_zh']=='改变世界的科学巨匠';new['title_zh']='爱因斯坦的诺奖之路';c=new['sentences'][14]['chunks'][0]
assert len(new['sentences'][14]['chunks'])==2
for pair in c['align']:pair[0]=pair[0].replace('looked past','**looked past**');pair[1]=pair[1].replace('绕开不看','**绕开不看**(looked past)')
c['en']=' '.join(a for a,b in c['align']);c['zh']=''.join(b for a,b in c['align']);assert c['note']==old['sentences'][14]['chunks'][0]['note']
oldgrammar='（carried there by…：过去分词短语作状语；\nthe prize had honoured：定语从句，修饰 man）'
text='当时诺贝尔奖委员会的老学究们觉得相对论太颠覆了，不敢颁奖，就一直装作没看见。但兜兜转转，爱因斯坦最后还是拿了诺贝尔奖（靠光电效应），狠狠打了委员会的脸。'
caption='（通俗解读：当时诺贝尔奖委员会的老学究们觉得相对论太颠覆了，\n不敢颁奖，就一直装作没看见。但兜兜转转，\n爱因斯坦最后还是拿了诺贝尔奖（靠光电效应），狠狠打了委员会的脸。）'
c=new['sentences'][14]['chunks'][1];assert c['note'].startswith(oldgrammar+'\n（简述：');summary=c['note'][len(oldgrammar)+1:];c['note']=caption+'\n'+summary;assert c['note'].split('（简述：',1)[1]==old['sentences'][14]['chunks'][1]['note'].split('（简述：',1)[1];assert caption.replace('\n','')[len('（通俗解读：'):-1]==text
new['allow_clash'].append('looked past');p.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');gen,issues=P.pure_generator(new);assert gen and not issues;(C/'视频/工具/初稿生成/gen60.py').write_text(gen)
md=C/'新版定稿/60-the-scientific-giant-who-changed-the-world.md';t=md.read_text();assert t.count('# ZH: '+old['title_zh'])==1;t=t.replace('# ZH: '+old['title_zh'],'# ZH: '+new['title_zh'],1)
for field in['en','zh']:
 a=old['sentences'][14]['chunks'][0][field];b=new['sentences'][14]['chunks'][0][field];assert t.count(a)==1;t=t.replace(a,b,1)
flat=lambda x:x.replace('\n','');assert t.count(flat(oldgrammar))==1;t=t.replace(flat(oldgrammar),flat(caption),1)
assert '| looked past |'not in t and t.count('| podium |')==1;t=t.replace('| podium |','| looked past | 本文：忽视；绕开不看；v. (look past) 忽视，不予理会；看向……的远处 | 5 |\n| podium |',1);md.write_text(t)
root=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-076.json');quote='Look past 在这个地方标注为重点词汇。整体标注重点词汇。\n\n在最下面加上小字:\n> '+text+'\n\n截图里面原来这个小字就是这个截图最下面最最原先最下面那个小字去掉。换上，我刚刚给这个小字 然后我觉得这个中文名字好像有点儿跟这篇文章，跟这篇文章不太匹配。能不能能不能换一个？能不能能不能换一个跟这篇文章内容更加匹配的，更加匹配的这个名字呢？'
if root.exists():z=json.loads(root.read_text());assert z['source_id']=='60';quote=z['user_instruction_verbatim'];origin={'path':str(root),'sha256':sha(root)}
else:origin={'kind':'root-delegated-user-verbatim-task-message','actual_ledger_not_yet_present':True}
ev={'source_id':'60','book_order':'36','feedback':'076','user_instruction_verbatim':quote,'origin':origin,'root_implementation_choice_not_user_verbatim':{'new_title_zh':new['title_zh'],'caption_prefix':'通俗解读：','purpose':'label user commentary as commentary, preserve all user wording; only bottom old grammar note replaced'},'draft_only':True,'native_final_not_authorized':True};ep=O/'actual-feedback-076-draft-intake.json';ep.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n');auth=C/'视频/工具/用户同意记录.json';a=json.loads(auth.read_text());a['记录'].append({'篇':'60','日期':'2026-11-14','原话':quote,'用于':'用户076隔离draft：looked past对应绕开不看重点，lemma look past；只删除S15最下carried there及the prize had honoured原说明，替为用户评论完整原文并由root指定前缀通俗解读；保中间looked past说明和原5点简述；用户授权换中文标题，root选爱因斯坦的诺奖之路，英文title和音轨不动；点名词允许撞词，尚无定稿或生成授权。','来源反馈号':'076','来源文件':str(ep),'来源文件SHA256':sha(ep)});auth.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');w=C/'视频/制作记录/60_待改清单.md';w.write_text(w.read_text()+'\n### 用户076原话（仅草稿）\n\n'+quote+'\n\n实施定位（非用户逐字引文）：用户授权中文标题换为贴合文章内容的名称，root选定《爱因斯坦的诺奖之路》，原改变世界的科学巨匠因此替换；英文标题和slug保持。S15原绕开不看标looked past；仅最下旧carried there by…及the prize had honoured两grammar删除，原中间the committee looked past说明保留；新通俗解读为用户原评论全文，不冒历史事实条目，root明确前导通俗解读，原5点简述全文不动。\n')
for x,y in zip(old['sentences'],new['sentences']):
 assert len(x['chunks'])==len(y['chunks'])
 for a,b in zip(x['chunks'],y['chunks']):assert a['en'].replace('**','')==b['en'].replace('**','')and len(a['align'])==len(b['align'])
assert{k:v for k,v in old.items()if k not in['sentences','allow_clash','title_zh']}=={k:v for k,v in new.items()if k not in['sentences','allow_clash','title_zh']}
r=dict(article='60',book_order='36',draft_only=True,native_final_not_authorized=True,source_sha256=sha(p),GEN_sha256=sha(C/'视频/工具/初稿生成/gen60.py'),MD_sha256=sha(md),actual_S15_chunk_count=2,screenshot_bottom_note_maps_to_actual_chunk2=True,original_chunk1_middle_grammar_preserved=True,only_original_bottom_grammar_replaced=True,user_comment_verbatim_after_prefix_and_linebreak_removal=text,new_title_zh=new['title_zh'],title_en_and_slug_unchanged=True,summary_raw_exact=True,all_bare_spoken_English_chunk_boundaries_and_DSP_unchanged=True,PAY_CI_audio_PDF_untouched=True,delta=P.differences(old,new),previous062075_reports_and_images_preserved=True,feedback_evidence={'path':str(ep),'sha256':sha(ep)})
out=O/'draft076-implementation-report.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='delta'},ensure_ascii=False))
