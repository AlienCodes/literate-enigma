#!/usr/bin/env python3
from pathlib import Path
import os,sys,json,hashlib,shutil,subprocess,re,datetime,copy
B=Path(__file__).resolve().parent
sys.path.insert(0,str(B));from generator_text_preflight import pure_generator,differences,digest,overlay_current_data
PYTHON='/workspace/work/video-venv/bin/python';PAY=B/'payload'
MIRRORS=[B/f'preflight-frozen66-v2-part{i}/mirror' for i in (1,2,3)]
T=MIRRORS[0]/'视频/工具';sys.path.insert(0,str(T));from 译文核查 import 指纹,去标,逐句格式
L=['T1没加信息','T3词性','T6不生硬','T7通顺','T8看得懂','T21贴合语境']
SPEC={
('21',2):[
'该句仍说假冒官员秘密告知售塔消息；只按用户点名补scrap重点标色。',
'deputy为形容词性“副的”，director-general为名词“总负责人”，momentous为形容词“重大的”，confidentially为副词“私下地”，scrap为名词“废铁”。',
'“作为废铁出售”清楚表达拆作回收金属，并非出售零散纸片。',
'消息主句后由that从句补充铁塔将出售的内容，整句关系完整。',
'小字说明官职后置定语、私下传消息及将要被出售的结构；简述交代冒充官员骗局。',
'scrap在金属商售塔语境取废铁义，confidentially是骗子要求秘密行动的叙述。'],
('22',4):[
'玻璃外墙是原因的主句保持原意；新增说明把正文所述内凹立面、反射聚光和街面高温连起来。',
'glazed为形容词“镶玻璃的”，facade为名词“正面墙”；be to blame为应负责任的固定表达。',
'“罪魁祸首”表达导致汽车受损的原因；说明用凹面镜解释外墙怎样集中阳光。',
'上方那面玻璃墙为主语，是罪魁祸首为谓语判断；小字接着说明原因。',
'外墙向内弯曲、反射集中到街面、局部高温、汽车烤坏四步已在小字说明。',
'facade指建筑外立面，glazed指玻璃覆盖，不能读成一块普通平玻璃直接产生热源。'],
('22',11):[
'报纸给大楼起嘲讽绰号的事实保持原句；按用户后续“没有撞车才标”的条件，撤掉本轮误加的dubbed重点。',
'dubbed是dub的过去式动词“把…戏称为”，本轮依撞词条件恢复普通文字；taunt是名词“嘲讽”，保留重点。',
'“把对讲机大楼戏称为烤焦机大楼”完整表达起绰号，解释Scorchie来自scorch。',
'报纸为主语、戏称为为动作、绰号为结果，末尾一句嘲讽作同位补充。',
'注释明确Walkie-Talkie是对讲机俗称、Scorchie改自烤焦，使双关可理解。',
'dubbed不是正式改名，taunt说明报纸绰号具有讥讽性质。'],
('44',1):[
'第二块按用户本轮指定的“这是一次对改变的压倒性地明确的拒绝”译文调整，83%及1955年保持正文原事实。',
'referendum是名词“全民公投”，overwhelmingly是副词“压倒性地”，rejection是名词“拒绝”。',
'第二块作为前块公投结果的同位概括，使用用户指定中文并把对改变移在前面。',
'先叙述83%选择继续靠左，再概括对改变的拒绝；主句及同位解释的关系明确。',
'小字说明keep doing为继续，同位语概括投票结果；83%说明所谓压倒性。',
'overwhelmingly修饰clear，表达投票结果的明确程度；rejection的对象为改变行车侧。'],
('44',4):[
'国家、车次与左右方向均沿用正文事实，本轮只新增挪威、芬兰及过境三项重点标色。',
'Norway、Finland为国家专名“挪威”“芬兰”，border crossings为复数名词短语“过境”；orientation和isolation为名词，inconvenient为形容词“不便的”。',
'“每年约有500万车次过境”表达跨境流动数量，因而靠左方向造成不便的逻辑可读。',
'先交代邻国靠右及跨境频繁，so再引出瑞典靠左的隔离和出行不便，因果连贯。',
'with附加结构补充车流背景，三项国家和过境词语已英汉对应标色。',
'border crossings在此计过境车次而非五百万个边境口岸，orientation指行车侧方向。'],
('50',13):[
'脑组织塑料研究及方法质疑保持原文；新增popularised as标色对应“被大众传作”，并保留一勺引号。',
'tissue是名词“组织”，popularised as是被动过去分词短语“被大众传作”，spoonful为名词“一勺”，queried为动词“质疑”，methodology为名词“研究方法”。',
'“其含量被大众传作一勺”说明大众传播中的比喻数量，避免误读为研究逐人量出完整一勺。',
'先述2025年脑组织研究，分号后转述其他研究者的方法质疑，三块顺序和转折完整。',
'小字说明popularised as修饰amount且意为被广泛传成，读者能区别原研究与传播说法。',
'popularised as突出通俗化转述，一勺带引号；queried是质疑研究方法而不是断言已证伪。'],
('51',6):[
'两个字母与故意错拼的oll korrect对应保持原意，本轮把stood for作为代表义重点词。',
'stood for是stand for的过去式动词短语“代表”，knowingly是副词“有意”，illiterate是形容词修饰拼法。',
'“这两个字母代表的是”直接解释缩写，文盲拼法由说明指出是故意错拼。',
'字母为主语，代表为谓语，后面说明有意错拼的词组，整句读通。',
'小字同时列stand for的原形与代表义、oll korrect对应all correct，错拼关系清楚。',
'stand for在缩写语境表示代表，不取容忍或支持义；illiterate描述故意模仿的拼法。'],
('51',11):[
'234对60张选举人票保留原文；新增小字明确him指范布伦，哈里森获胜、范布伦未能连任。',
'unseated是过去式动词“把…赶下台”，electoral votes是名词短语“选举人票”。',
'“把他赶下台”在大选语境表达击败在任总统，小字补明谁的票数较多。',
'哈里森为主语、范布伦为宾语，234比60的补充说明与获胜方向一致。',
'注释指出1840年哈里森234票、范布伦60票，并明确结果是未能连任。',
'unseated指选举击败而非暴力罢黜，electoral votes区别于全国普通选民票。'],
('65',14):[
'主句温暖天气后入口融水结冰保留正文；年份说明依据已完成事实复核区分2016年事件与2017年报道。',
'record-breaking为形容词“破纪录的”，tunnel为名词“隧道”，solidified为动词“凝固”。',
'“流进入口隧道、随后凝固成冰”按动作次序表达，没有把种子库入口等同储藏室。',
'after时间短语之后述融水进入约100米入口隧道并结冰，时间方向及并列动作一致。',
'小字明确入口进水为2016年10月、2017年5月广泛报道、种子储藏区没有进水。',
'tunnel指入口隧道，solidified指水结冰；年份补充避免把报道日期误作进水日期。'],
}
SPEC={k:''.join(a+'：'+v for a,v in zip(L,vs)) for k,vs in SPEC.items()}
def tails():
 a=json.loads((B/'confirmation-tail-review-21-48.json').read_text())['rows'];z=json.loads((B/'confirmation-tail-review-49-70.json').read_text())['articles'];out={}
 for row in a:out[row['id']]=(row['sentence'],row['suggested_conclusion'],row['source_sha256'])
 for row in z:out[row['id']]=(row['sentence'],row['conclusion'],row['source_sha256'])
 return out
TAIL=tails()
def semantic_sentence(s,tail=False):
 cs=[]
 for c in s['chunks']:
  note=c.get('note','');note=note.split('（简述：')[0]
  cs.append((去标(c['en']),去标(c['zh']),去标(note)))
 return cs

def setup(part):
 m=MIRRORS[part-1];overlay_current_data(PAY,m)
 src=PAY/'视频/制作记录/逐句确认'
 if src.exists():shutil.copytree(src,m/'视频/制作记录/逐句确认',dirs_exist_ok=True)
 w=m/'_resumed-preflight-work';w.mkdir(exist_ok=True);(w/'scripts').mkdir(exist_ok=True)
 if not (w/'fonts').exists():(w/'fonts').symlink_to(m/'视频/工具/fonts',target_is_directory=True)
 env={**os.environ,'XG_P':str(m),'XG_TOOLS':str(m/'视频/工具'),'XG_WORK':str(w),'VIDEO_S':'1','PYTHONDONTWRITEBYTECODE':'1'}
 env['PATH']=str(Path(PYTHON).parent)+os.pathsep+env.get('PATH','')
 for k in ('YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID'):env.pop(k,None)
 return m,w,env

def execute(cmd,w,e,p):
 with p.open('w') as st:r=subprocess.run([str(v) for v in cmd],cwd=w,env=e,stdout=st,stderr=subprocess.STDOUT)
 return r.returncode,p.read_text(errors='replace')

def main():
 part=int(sys.argv[1]);ids=os.environ.get('PREFLIGHT_IDS','').split(',') if os.environ.get('PREFLIGHT_IDS') else [f'{i:02}' for i in range(1,71) if (i-1)%3==part-1]
 m,w,e=setup(part);out=B/('resumed-preflight-'+os.environ['PREFLIGHT_SUFFIX'] if os.environ.get('PREFLIGHT_SUFFIX') else f'resumed-preflight-part{part}');out.mkdir(exist_ok=True)
 for f in ['logs','auto-repaired-sources','generators']:(out/f).mkdir(exist_ok=True)
 core={str(p.relative_to(m)):digest(p) for p in [m/'视频/工具/踩坑核查.py',m/'视频/工具/译文核查.py',m/'视频/工具/新管/修.py',m/'视频/工具/初稿生成/核对.py']}
 report={'part':part,'ids':ids,'scope':'actual original generator/full JSON exact, original repair, then original text gate; sentence records refreshed only with documented review or semantic-invariant body','core_hashes':core,'articles':[]}
 def save():(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 for no in ids:
  src=PAY/f'视频/脚本/{no}.json';d=json.loads(src.read_text());row={'article':no,'source_sha256':digest(src)};report['articles'].append(row);save()
  shutil.copyfile(src,m/f'视频/脚本/{no}.json');shutil.copyfile(src,w/f'scripts/{no}.json')
  # Exact GEN proof before publication; preserves every current title/cap/gain/summary JSON field.
  text,issues=pure_generator(d);row['generator_issues']=issues
  if text is not None:
   g=out/f'generators/gen{no}.py';g.write_text(text);gen=m/f'视频/工具/初稿生成/gen{no}.py';shutil.copyfile(g,gen)
   (w/f'scripts/{no}.json').unlink();gc,gs=execute([PYTHON,gen],w,e,out/f'logs/{no}-generator.log');row['generator_exit']=gc
   got=json.loads((w/f'scripts/{no}.json').read_text()) if (w/f'scripts/{no}.json').exists() else None
   row['generator_differences']=differences(d,got);row['generator_exact']=(gc==0 and not row['generator_differences'])
   if row['generator_exact'] and digest(src)==row['source_sha256'] and no not in os.environ.get('PREFLIGHT_NO_PUBLISH_IDS','').split(','):
    dst=PAY/f'视频/工具/初稿生成/gen{no}.py';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(g,dst);row['generator_published']=True
  shutil.copyfile(src,w/f'scripts/{no}.json')
  rc,rs=execute([PYTHON,m/'视频/工具/新管/修.py',no],w,e,out/f'logs/{no}-repair.log');row['repair_exit']=rc
  repaired=json.loads((w/f'scripts/{no}.json').read_text());target=out/f'auto-repaired-sources/{no}.json';shutil.copyfile(w/f'scripts/{no}.json',target)
  row['repair_differences']=differences(d,repaired);row['normalized_sha256']=digest(target)
  # No repaired JSON is written to PAY by this script.
  if int(no)>=21:
   prior=json.loads((m/f'视频/制作记录/逐句确认/{no}.json').read_text());issued=json.loads((m/f'视频/脚本/已发版本/{no}.json').read_text());rec=copy.deepcopy(prior);changes=[]
   for si,s in enumerate(repaired['sentences'],1):
    key=f'S{si}';old=prior.get(key,{});fp=指纹(s)
    if key not in prior:raise RuntimeError(f'{no} {key} has no prior reviewed conclusion')
    conclusion=old['结论'];reason='existing fingerprint already matches'
    if (no,si) in SPEC:conclusion=SPEC[(no,si)];reason='actual focused review of new approved keyword/note/translation'
    if si==len(repaired['sentences']):
     ti,conclusion,reviewhash=TAIL[no];assert ti==si
     # Explicit summary review allows subsequent typography-only/approved lexical cleanup only; record input hashes for audit.
     reason='current final body and approved summary read and reviewed with concrete T33'
     row['tail_review_source_sha256']=reviewhash
    elif (no,si) not in SPEC and fp!=old.get('指纹'):
     if semantic_sentence(s)!=semantic_sentence(issued['sentences'][si-1]):raise RuntimeError(f'{no} {key}: substantive body difference lacks reviewed conclusion')
     if old.get('指纹')!=指纹(issued['sentences'][si-1]):raise RuntimeError(f'{no} {key}: original conclusion does not match issued body')
     reason='same English/Chinese/local note semantics as issued confirmed body; only markup, alignment boundaries or mechanical note wrap changed'
    if fp!=old.get('指纹') or conclusion!=old['结论']:
     rec[key]={'指纹':fp,'结论':conclusion,'时间':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M')};changes.append({'sentence':si,'before_fingerprint':old.get('指纹'),'after_fingerprint':fp,'reason':reason,'conclusion_changed':conclusion!=old['结论']})
   fmt=逐句格式(repaired,rec,no);row['confirmation_format_errors']=fmt
   if fmt:raise RuntimeError(f'{no}: invalid detailed confirmation {fmt}')
   if digest(src)!=row['source_sha256']:raise RuntimeError(f'{no}: source changed during review, refusing record publication')
   for root in [PAY,m]:
    dst=root/f'视频/制作记录/逐句确认/{no}.json';dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(json.dumps(rec,ensure_ascii=False,indent=1)+'\n')
   row['confirmation_updates']=changes
  if no=='02':
   si,conclusion,reviewhash=TAIL[no];assert si==len(repaired['sentences'])
   recpath=PAY/f'视频/制作记录/逐句确认/{no}.json';rec=json.loads(recpath.read_text()) if recpath.exists() else {};rec[f'S{si}']={'指纹':指纹(repaired['sentences'][-1]),'结论':conclusion,'时间':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M')}
   if digest(src)!=row['source_sha256']:raise RuntimeError('02 changed during final tail review')
   for root in [PAY,m]:
    targetrec=root/f'视频/制作记录/逐句确认/{no}.json';targetrec.parent.mkdir(parents=True,exist_ok=True);targetrec.write_text(json.dumps(rec,ensure_ascii=False,indent=1)+'\n')
   row['extra_parent_requested_tail_confirmation']=True
  # Original text gate reads the actual auto-repaired JSON and refreshed records.
  tc,ts=execute([PYTHON,m/'视频/工具/踩坑核查.py',no,'出片'],w,e,out/f'logs/{no}-text-gate.log')
  row['text_exit']=tc;row['hard_errors']=[x.strip()[1:].strip() for x in ts.splitlines() if x.strip().startswith('✘')];row['pending']=[x.strip()[1:].strip() for x in ts.splitlines() if x.strip().startswith('？')];row['exception_tail']=ts.splitlines()[-16:] if tc and not row['hard_errors'] else [];row['source_unchanged']=digest(src)==row['source_sha256'];save();print(no,'GEN',row.get('generator_exact'),'repair',rc,'gate',tc,'hard',len(row['hard_errors']),'pending',len(row['pending']),flush=True)
 report['core_unchanged']=all(digest(m/rel)==sha for rel,sha in core.items());report['status']='passed' if report['core_unchanged'] and all(r.get('generator_exact') and r['text_exit']==0 and r['source_unchanged'] for r in report['articles']) else 'needs_data_review';save()
if __name__=='__main__':main()
