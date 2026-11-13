"""Prepare reviewed source-only cleanup and article12 corrections. Never produces MP4/PDF."""
import ast,copy,hashlib,json,os,re,shutil,subprocess
from pathlib import Path

ROOT=Path('/workspace/work/github-publication/target')
OUT=Path('/workspace/work/video-audit70-20261113')
PAY=OUT/'payload';PAY.mkdir(exist_ok=True)
REPORT='视频/制作记录/旧简述清理-2026-11-13'
PENDING='视频/制作记录/待修改/2026-11-13'
review=json.loads((OUT/'review01-24.json').read_text())
targets=review['confirmed_remove_ids'];by_id={r['id']:r for r in review['articles']}
paths=subprocess.check_output(['git','ls-tree','-r','--name-only','-z','HEAD','--','新版定稿'],cwd=ROOT).decode().split('\0')
def read(path):
    p=ROOT/path
    return p.read_bytes() if p.exists() else subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT)
def put(path,data):
    dest=PAY/path;dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(data.encode() if isinstance(data,str) else data)
def js(data):return json.dumps(data,ensure_ascii=False,indent=1)+'\n'
def visible(text):
    text=re.sub(r'\{\{.*?\}\}','',text,flags=re.S)
    text=re.sub(r'\*\*([^*]+)\*\*\([^)]*\)',r'\1',text)
    return text.replace('**','').replace('\n','')
def patch_json(data,ops):
    for op in ops:
        parts=op['path'].strip('/').split('/');node=data
        for key in parts[:-1]:node=node[int(key)] if isinstance(node,list) else node[key]
        key=int(parts[-1]) if isinstance(node,list) else parts[-1]
        if op['op']=='test':assert node[key]==op['value'],op['path']
        elif op['op']=='replace':node[key]=copy.deepcopy(op['value'])
        else:raise AssertionError(op)

CEO='（盲测中，百事赢了老版可口可乐。可口可乐于是改用更甜、更接近百事口味的新配方。百事借机嘲讽：你输了盲测，现在又学我们的口味，不就是承认我们更好喝吗？我们赢了，放假一天庆祝！）'
CEO_LINES='（盲测中，百事赢了老版可口可乐。\n可口可乐于是改用更甜、更接近百事口味的新配方。\n百事借机嘲讽：你输了盲测，现在又学我们的口味，\n不就是承认我们更好喝吗？\n我们赢了，放假一天庆祝！）'
assert CEO_LINES.replace('\n','')==CEO

END_EXPLANATION='（盲测只比味道，不告诉人喝的是什么牌子，所以测不出老顾客对可口可乐这个品牌的感情。新配方即使更受试饮者欢迎，也不代表老顾客愿意放弃熟悉的老可乐。）'
END_LINES='（盲测只比味道，不告诉人喝的是什么牌子，\n所以测不出老顾客对可口可乐这个品牌的感情。\n新配方即使更受试饮者欢迎，\n也不代表老顾客愿意放弃熟悉的老可乐。）'
assert END_LINES.replace('\n','')==END_EXPLANATION
changes=[];source_before={};script_after={};md_after={};gen_after={}
for no in targets:
    row=by_id[no];sp=f'视频/脚本/{no}.json';gp=f'视频/工具/初稿生成/gen{no}.py'
    mp=next(p for p in paths if p.startswith('新版定稿/'+no+'-'))
    before=json.loads(read(sp));after=copy.deepcopy(before)
    old_note=after['sentences'][-1]['chunks'][-1]['note']
    old_prefix,summary=old_note.split('（简述：',1)
    assert old_prefix.rstrip()==row['note_before_tagged_summary'],no
    keep=row['retain_prefix_exact'].rstrip('\n')
    new_note=(keep+'\n' if keep else '')+'（简述：'+summary
    after['sentences'][-1]['chunks'][-1]['note']=new_note
    assert new_note.split('（简述：',1)[1]==summary
    control=copy.deepcopy(after);control['sentences'][-1]['chunks'][-1]['note']=old_note
    assert control==before,no
    removed=''.join(s['exact_text'] for s in row['remove_spans']).lstrip('\n')
    gp_raw=read(gp).decode();gen=gp_raw
    old_gen_note=row['note_before_tagged_summary']
    parsed=ast.parse(gen)
    data_node=next(n.value for n in parsed.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='S' for t in n.targets))
    literal_nodes=[n for n in ast.walk(data_node) if isinstance(n,ast.Constant) and n.value==old_gen_note]
    assert len(literal_nodes)==1,(no,'generator note literal')
    token=ast.get_source_segment(gen,literal_nodes[0])
    assert gen.count(token)==1,(no,'generator note literal segment')
    gen=gen.replace(token,json.dumps(new_note,ensure_ascii=False),1)
    md=read(mp).decode();remove_md=removed.replace('\n','')
    assert md.count(remove_md)==1,(no,'article old recap')
    summary_text='（简述：'+summary
    has_new_summary=summary_text in md
    md=md.replace(remove_md,'' if has_new_summary else summary_text,1)
    assert remove_md not in md
    assert summary_text in md
    assert '（结局：' not in new_note.split('（简述：',1)[0]
    source_before[no]=before;script_after[no]=after;md_after[no]=(mp,md);gen_after[no]=(gp,gen)
    changes.append({'original_id':no,'title':before['title_zh'],'last_sentence_1_based':len(before['sentences']),
        'removed_legacy_exact':removed,'kept_local_explanation_exact':keep,
        'note_before':old_note,'note_after':new_note,
        'new_summary_sha256':hashlib.sha256(summary_text.encode()).hexdigest(),
        'new_summary_unchanged':True,'body_text_unchanged':True,'md_new_summary_inserted':not has_new_summary})

# Article12: apply the independently measured, generator-checked data-only fix.
before12=copy.deepcopy(script_after['12'])
patch_json(script_after['12'],json.loads((OUT/'alignment12/source12-exact-sip-and-focus-overlay.json').read_text()))
d12=script_after['12'];changed_sip=d12['sentences'][0]['chunks'][1]
assert changed_sip['en']==' '.join(x[0] for x in changed_sip['align'])
assert changed_sip['zh']==''.join(x[1] for x in changed_sip['align'])
for old_s,new_s in zip(before12['sentences'],d12['sentences']):
    for old_c,new_c in zip(old_s['chunks'],new_s['chunks']):
        for k in ('en','zh'):assert visible(old_c[k])==visible(new_c[k])
        assert old_c.get('note')==new_c.get('note')

last12=d12['sentences'][-1]['chunks'][-1]
retained12,new_summary12=last12['note'].split('（简述：',1)
last12['note']=retained12.rstrip()+'\n'+END_LINES+'\n（简述：'+new_summary12
item12=next(row for row in changes if row['original_id']=='12')
item12['note_after']=last12['note'];item12['new_user_approved_local_explanation']=END_EXPLANATION

# The requested CEO explanation must follow the actual antecedent of "the change".
ceo_chunk=d12['sentences'][13]['chunks'][-1]
old_ceo=ceo_chunk['note'];grammar,old_ceo_explanation=old_ceo.split('\n（这句话是在描写',1)
old_ceo_explanation='（这句话是在描写'+old_ceo_explanation
ceo_chunk['note']=grammar+'\n'+CEO_LINES

mp,md=md_after['12']
summary_text12='（简述：'+new_summary12
assert md.count(summary_text12)==1
md=md.replace(summary_text12,END_EXPLANATION+summary_text12,1)
assert md.count(old_ceo_explanation.replace('\n',''))==1
md=md.replace(old_ceo_explanation.replace('\n',''),CEO,1)
en_start=md.index('## 英文');zh_start=md.index('## 中文');tbl_start=md.index('## 速查表')
en=md[en_start:zh_start];zh=md[zh_start:tbl_start];tail=md[tbl_start:]
for word in ['stocked up on','protester','packaging']:
    assert en.count(word)==1,word
    en=en.replace(word,'**'+word+'**',1)
for text,key in [('囤积了','stocked up on'),('抗议者','protester'),('包装','packaging')]:
    assert text in zh
    zh=zh.replace(text,'**'+text+'**('+key+')',1)
assert zh.count('（小口喝；抿）')==1
zh=zh.replace('（小口喝；抿）','',1).replace('**啜饮**(sip)','**啜饮**(sip)（小口喝；抿）',1)
new_rows=[
    '| stocked up on | v. (stock up on) 大量储备，囤积（stock up on sth） | 3 |',
    '| protester | n. 抗议者，示威者 | 3 |',
    '| packaging | n. 包装，包装材料 | 3 |',
]
for row in new_rows:
    word=row.split('|')[1].strip();assert not re.search(r'^\| '+re.escape(word)+r' \|',tail,re.M)
marker='\n## 史实与来源';assert marker in tail
tail=tail.replace(marker,'\n'+'\n'.join(new_rows)+'\n'+marker,1)
md=md[:en_start]+en+zh+tail;md_after['12']=(mp,md)

# Use the reviewer's minimal GEN12 changes (four affected chunks), then clear its old recap.
gp,gen=gen_after['12'];proposal=(OUT/'alignment12/gen12-proposal-only.py').read_text()
old_token=json.dumps(by_id['12']['note_before_tagged_summary'],ensure_ascii=False)
assert proposal.count(old_token)==1
proposal=proposal.replace(old_token,json.dumps(d12['sentences'][-1]['chunks'][-1]['note'],ensure_ascii=False),1)
old_ceo_full=grammar+'\n'+old_ceo_explanation
assert proposal.count(json.dumps(old_ceo_full,ensure_ascii=False))==1
proposal=proposal.replace(json.dumps(old_ceo_full,ensure_ascii=False),json.dumps(ceo_chunk['note'],ensure_ascii=False),1)
# This pre-existing generator used coarser groups in the CEO chunk. Keep the
# currently accepted actual script groups when saving the newly edited note.
parsed=ast.parse(proposal)
snode=next(n.value for n in parsed.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='S' for t in n.targets))
ceo_node=snode.elts[13].elts[1].elts[1]
old_segment=ast.get_source_segment(proposal,ceo_node)
ceo_data=[[tuple(pair) for pair in ceo_chunk['align']],ceo_chunk['note']]
assert proposal.count(old_segment)==1
proposal=proposal.replace(old_segment,repr(ceo_data),1)
gen_after['12']=(gp,proposal)

for no in targets:
    after=script_after[no];gp,gen=gen_after[no];mp,md=md_after[no]
    compile(gen,gp,'exec')
    tree=ast.parse(gen);S=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='S' for t in n.targets)))
    assert S[-1][1][-1][1]==after['sentences'][-1]['chunks'][-1]['note'],no
    # Execute only the original data serializer's equivalent for touched chunks.
    if no=='12':
        for si,ci in [(0,1),(10,2),(11,0),(11,1),(13,1)]:
            c=S[si][1][ci];al=[list(p) for p in c[0]]
            result={'en':' '.join(a for a,b in al if a!='\n'),'zh':''.join(b for a,b in al),'align':al}
            if len(c)>1:result['note']=c[1]
            assert result==after['sentences'][si]['chunks'][ci],(si,ci,'generator roundtrip')
    put(f'视频/脚本/{no}.json',js(after));put(gp,gen);put(mp,md)

mapping=json.loads(Path('/workspace/work/order70-recommended.json').read_text())['order']
for row in changes:row['playback_id']=f'{mapping.index(row["original_id"])+1:02d}'
validation={'checked_articles':70,'accepted_video_sha256_verified':70,'legacy_articles':len(targets),
    'original_ids':targets,'all_current_summaries_retained_exactly':True,
    'ordinary_grammar_and_context_notes_retained':True,'new_01_22_user_notes_retained':True,
    'renderer_modified':False,'MP4_generated':False,'PDF_generated':False,
    'video_delivery_status':'User subsequently authorizes4K regeneration and finalization of all affected articles. Existing MP4s remain unchanged until new verified renders are delivered.',
    'article12_alignment':'sip/啜饮/gloss share the same horizontal center; existing word meanings and visible English are unchanged',
    'article12_new_focus':['stocked up on','protester','packaging'],
    'article12_ceo_note':{'text':CEO,'timeline':'the change refers to replacing the original formula; do not confuse with the later restoration'},
    'changes':changes}
(OUT/'cleanup-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
put(REPORT+'/清理核验.json',json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
for name in ['review01-24.json','review25-48.json','review49-70.json','visual01-24.json','visual49-70.json','delivered-video-inspection.json']:
    put(REPORT+'/核查记录/'+name,(OUT/name).read_bytes())
put(REPORT+'/核查记录/visual25-48.json',json.dumps({'checked_ids':[f'{n:02d}' for n in range(25,49)],'body_and_standalone_summary_cards_visually_reviewed':True,'duplicate_legacy_recaps_found':0,'local_grammar_lexical_context_notes_retained':True,'reviewer':'root'},ensure_ascii=False,indent=2)+'\n')
for p in (OUT/'contacts').glob('*.jpg'):put(REPORT+'/成片截图/'+p.name,p.read_bytes())
for name in ['source12-exact-sip-and-focus-overlay.json','focus12-metadata.json','exact-metrics-and-overlay.json','generator-roundtrip-check.json','gen12-sip-and-focus-proposal.diff','proposal12.json']:
    put(REPORT+'/新可乐对齐核对/'+name,(OUT/'alignment12'/name).read_bytes())
for name in ['prepare_cleanup.py','inspect_delivered_videos.py']:
    put(REPORT+'/核查程序/'+name,(OUT/name).read_bytes())

state=json.loads((ROOT/PENDING/'修改状态.json').read_text())
assert state['render_allowed'] is False and state['pdf_build_allowed'] is False
state['legacy_summary_cleanup']={'status':'SOURCE_FIXED_4K_REGENERATION_REQUESTED','checked_articles':70,'confirmed':len(targets),'original_ids':targets,'report':REPORT+'/清理核验.json'}
state['status']='AFFECTED_ARTICLES_4K_FINALIZATION_REQUESTED'
state['render_allowed']=True;state['render_scope']=sorted(set(['01','03','05']+targets))
state['unmodified_article_regeneration_requested']=False
state['article12']={'original_number':'12','playback_number':'05','title':'新可乐的79天','sip_gloss':'aligned directly under sip/啜饮','new_focus':['stocked up on','protester','packaging'],'ceo_explanation':CEO,'final_sentence_explanation':END_EXPLANATION,'production':'4K regeneration and finalization explicitly requested'}
put(PENDING+'/修改状态.json',json.dumps(state,ensure_ascii=False,indent=2)+'\n')
notes=(ROOT/PENDING/'修改记录.md').read_text()
notes+='\n## 全70篇旧简述清理与新可乐后续修改\n\n已对照70个已归档MP4的实际正文尾帧和新版独立简述页，确认原篇号'+ '、'.join(targets)+'共12篇残留旧简述。仅移除这些旧段落，保留正常解释及新版独立简述。源稿、生成数据同步修订。\n\n新可乐（原12/重排05）：sip说明移到sip／啜饮正下方；stocked up on、protester、packaging及对应中文新增重点标记；百事CEO说明按原文换配方的时间线澄清。所有视频和PDF继续暂停重生成。\n'
notes+='\n## 用户最新指示：修改后的篇目全部需要4K定稿\n\n用户已确认百事CEO说明及最后一句品牌感情解释，并明确要求原12重出4K。随后又强调：“所有的这些东西改完之后，我们要重新生成视频定稿的呀。”因此本轮全部受影响篇目均需正式重生成4K、核验、定稿并保存GitHub与Release。未改动篇目不额外重做；PDF仍不生成。\n\n最后一句新加局部解释：'+END_EXPLANATION+'\n'
put(PENDING+'/修改记录.md',notes)
table='\n'.join('| '+r['playback_id']+' | '+r['original_id']+' | '+r['title']+' |' for r in changes)
readme='''# 全70篇旧简述残留核查与源稿清理

状态：源稿已修订。用户随后明确要求本轮全部受影响篇目重新生成4K并定稿；PDF仍暂停。现有MP4及旧Release保留，待新成片核验后另行归档交付。

逐一读取70个已归档4K视频，核对SHA-256，并检查正文最后一屏与末尾独立简述页。完整源稿审阅与画面复核确认12篇同时存在旧简述和新版独立简述。

| 当前播放序号 | 原篇号 | 篇名 |
|---|---|---|
'''+table+'''

清理只删除已确认的旧故事概述，保留紧邻的语法、词义、局部背景解释和新版简述。原10“空墙”的背景解释、原25 ingenuity词义、原70邮票国家识别说明，以及用户刚确认的原01小字均保留。

原因：早期段落使用“结局”或根本没有标签；添加新版独立简述时，这些旧段落仍被当成普通注释保留。此次同时清理视频脚本、genNN数据和文章源稿，避免重生成再次带回。

新可乐另修：sip小字说明移到sip和啜饮共同中心下方；新增stocked up on、protester、packaging重点标记并补词汇表；CEO小字按正文更换配方的时间线说明。全部为数据修改，未更改画面程序或音频。

核查截图是从现有成片提取的“修改前”证据；不能当作修好后的新成片。静态预览另有明确标记。收到用户重新开始的指示后，才按正式做.sh与定稿.sh输出4K，并检查音频与末页独立简述。
'''
put(REPORT+'/README.md',readme)
print(json.dumps({'staged_source_articles':len(targets),'payload_files':sum(1 for p in PAY.rglob('*') if p.is_file()),'legacy_ids':targets,'video_generation':False},ensure_ascii=False),flush=True)
