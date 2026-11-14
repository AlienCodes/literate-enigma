"""Save the live revision record in both authorized repos; no final-file claim."""
import base64,hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent;PAY=BASE/'payload'
LOCAL=Path('/workspace/work/github-publication/target')
REL='视频/制作记录/旧简述清理-2026-11-13/核查记录/最新修订总记录.json'
def api(repo,path,data=None,method='GET'):
    args=['gh','api','repos/'+repo+'/'+path]
    if method!='GET':args+=['-X',method]
    if data is not None:args+=['--input','-']
    return json.loads(subprocess.check_output(args,input=None if data is None else json.dumps(data).encode()))

def replace_blob(repo, tree_sha, parts, blob_sha):
    """Update small child trees bottom-up; recursive root updates time out on the backup."""
    rows=api(repo,'git/trees/'+tree_sha)['tree'] if tree_sha else []
    rows=[{k:r[k] for k in ('path','mode','type','sha')} for r in rows]
    name=parts[0]
    old=next((r for r in rows if r['path']==name),None)
    if len(parts)==1:
        leaf={'path':name,'mode':'100644','type':'blob','sha':blob_sha}
    else:
        child=replace_blob(repo,old['sha'] if old else None,parts[1:],blob_sha)
        leaf={'path':name,'mode':'040000','type':'tree','sha':child}
    return api(repo,'git/trees',{'tree':[r for r in rows if r['path']!=name]+[leaf]},'POST')['sha']

changes=[
 {'original':'01','changes':['保留批准的双重负担、统计回归及照片例子；说明括号规范；通俗五点简述']},
 {'original':'02','changes':['Stanford／斯坦福大学','Psychology／心理学','college-entrance exam／高考，保留原文连字符','350字五点简述；分清早期相关、两步复核与成人可信度；本篇4K定稿明确授权']},
 {'original':'03','changes':['organism／微生物','germ／病菌','cultured／培养','Ulcers／溃疡']},
 {'original':'04','changes':['cabbie／出租车司机','quickest route／最快的路线','qualify译文按用户改为并且只有大约一半，最终会合格','rear／靠后的','grey matter／灰质','alike／一样','加入街道记忆与复杂图形记忆取舍解释；通俗简述；4K定稿']},
 {'original':'05','changes':['screening／筛查','baker／面包师','co-worker／同事','convicted of整体，分离中文被判与罪保持同色']},
 {'original':'06','changes':['hoof／蹄子','guard against／防范','reasoned／推理，动词','加入人们无意发出提示并非故意欺骗的小字；4K定稿']},
 {'original':'10','changes':['整轨响度审查，末句If so受控增益；原生新4K实际专用音频核查18/18通过；仅补图后的成片验收单列']},
 {'original':'11','changes':['program／程序，名词','Commentators／解说员','完整通俗简述；4K定稿']},
 {'original':'12','changes':['sip释义精准放词下','stocked up on整体、protester、packaging','批准的百事庆祝及品牌感情解释','原稿标题Coke双爆破修复；原生新4K全部音频检查通过，保持音包补图后实际成片V3通过']},
 {'original':'20','changes':['ago留在who lived about5,300years ago这一行；between另起第三行','artery／动脉','joints／关节','旧内嵌结局移除，正文末屏放大居中，五点简述讲清死因与未知凶手']},
 {'original':'21','changes':['scrap／废铁，for保持普通字','核查并重排正文末屏']},
 {'original':'22','changes':['批准的玻璃立面聚光小字及新简述','撤回早前误加dubbed重点，遵用户后续没有撞词才标的具体条件','移除旧内嵌结局的窄宽/无标签特批，让独立简述正常排版']},
 {'original':'39','changes':['加入预防奏效只留下账单的小字，说明不能因没出灾难就说钱白花','通俗详细简述，澄清1000亿美元是美国本国政府企业估算；4K定稿']},
 {'original':'42','changes':['lavish中文exact巨大的/奢侈的','instruments／仪器，词表解释本语境精密观测仪器','377字五点简述，解释主镜误差、错检、COSTAR和新相机、原主镜仍有缺陷']},
 {'original':'44','changes':['这是一次对改变的压倒性地明确的拒绝，overwhelmingly是副词','Norway／挪威、Finland／芬兰分格对齐','border crossings／过境，保留复数','全轨审查，S4C1最小−1dB候选，实际新轨待验收','末屏放大居中']},
 {'original':'50','changes':['popularised as整体重点／被大众传作','324字简述，明确检出不等于致病、关联不等于因果、一勺为有争议估算','末页放大居中']},
 {'original':'51','changes':['stood for整体／代表','pedigree／来历','加入哈里森234票对范布伦60票小字','讲清乔克托语旧说与报纸错拼说','全轨响度审查，开头OK及oll wright批准增益，实际音频专门核查20/20通过；音包不变补图后完整V3通过','末屏放大居中']},
 {'original':'55','changes':['罗马混凝土末屏重排','通俗简述写清石灰自修补机制，尊重既定中文使周围混凝土断裂、占据']},
 {'original':'65','changes':['正文保留英文，补充实际2016年进水/2017年报道年份说明；摘要不夸大首次取种数量']},
]
record={
 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
 'task':'70篇精读视频及正式印刷书的全部修订、重建和GitHub交付',
 'state':'COMPACT_475_PAGE_BOOK_APPROVED_AND_DUAL_ARCHIVED; ALL70_TEXT_STATIC_LAYOUT_PASSED; TWO_ILLUSTRATED_4K_VIDEOS_PASSED; REMAINING_AUDIO_PRODUCTION_IN_PROGRESS',
 'status_is_not_a_final_delivery_claim':True,
 'scope':{'main_pdf_latest_correction':'799页含解析版本仅未发布本地历史草稿，主册改为v4-compact；小字/句析/语法/练习均从主册移除，解析材料源码留存供以后单独解析书，本轮不制作解析册', 'video':'全部70篇真正重渲3840×2160，按书中最新顺序编号排列，不用旧片补数',
          'source':'重点词、指定译文、小字、全70简述、末页字号和居中、全篇排版核对',
          'audio':'实际新成片全轨检查，重点10/12/44/51；质量未通过则修复并重验',
          'pdf':'按用户最新纠正，沿原400多页B5规格：只插图、中英文章、重点词短语及篇末简述，保留先前批准第2页序言和成套封底；不额外增加解析/练习',
          'pdf_editorial':'删阅读小册、点击目录可跳转、新顺序版及模板/软件/制作说明；采用正式书名考研学人、副题70篇趣味英语阅读',
          'preface':'准确统计重点词与短语、解释类型与70篇选文；无官方考研词表时不得宣称全部标词都是大纲词',
          'attribution':'全部新PDF保留默认隐藏、可开启的朋克英语来源图层',
          'release':'最新要求只放整本正式PDF和全部70部4K视频，编号篇名严格对齐书序；源码及详细QC保存在GitHub仓库',
          'old_release':'用户要求替换旧Release；等新整套实际验收及上传核对后处理明确旧对象，尚未删除任何Release或Git历史'},
 'specific_changes':changes,
 'global_changes':['实查全部70篇旧末屏与独立简述；1231句正文双分辨率排版审查',
                   '12篇移除旧内嵌结局，保留必要语法与局部解释',
                   '70篇简述完整阅读并独立交叉复核，当前56篇正文摘要改写；新02/42/50优先反馈已再澄清',
                   '旧字面摘要锚保留历史记录，现行全文由请求源稿及实际排版归一化校验，原检查器不被绕过'],
 'production':{
               'new_final_videos_passed':2,'required_videos':70,
               'passed_videos':[{'original_id':'53','book_order':'35','sha256':'b82966baa6439b194a6fa1e2c222f226517982318ef398ae631efcd5c562d588'},
                                {'original_id':'64','book_order':'63','sha256':'78ef9444e6a65a07ed934c8f9b7f7b51dbcb6d0d6e783db9f61b99a5659b40c9'}],
               'passed_video_ending':'实际正文结束后，书中对应插图60帧，再简述60帧；3840×2160、30fps；原正文编码与AAC包及绝对时间保持不变',
               'official_producer_run_for_passed_two':43523430839,
               'active_runs_at_recording':{'article26_official_rerender':43529134759,'keep_reviewed_gain_original_native_regression':43530603703},
               'readonly_diagnostics_run':43528832985,
               'observed_blockers':['草稿声音程序会额外改写已审句内增益；最小保留模式补丁正在原完整回归认证',
                                    '同一实际PCM在不同CPU上新推TTS参考不逐样本相同，已证实并着手修复原始create母素材读取；保留原自检、阈值及真实声学问题检查',
                                    '原生参考输入枚举、全70词汇上下文、简述续行装饰比较已修，其他真实声音和高亮疑点继续逐篇处理'],
               'new_final_pdfs_passed':1,
               'whole_book':{'pages':475,'bytes':375955024,'sha256':'65bc695c7b789fbc397c443ea6a387ee616f2569865a4350edc0137ddcff089e',
                            'format':'B5 176×250mm；只插图、中英文章、词汇短语和简述；保留批准封面/第2页序言/目录/封底',
                            'primary_pinned_commit':'8404ddff99dfa094aa005fec70643d9da55e21fc','archive_prefix':'考研学人印刷版/2026-11-13-v4/',
                            'frozen_asset_count':637,'dual_archive_verified':True,
                            'full_pdf_in_git':'原字节四分片、完整SHA、复组程序；Release交付单个完整PDF'},
               'release_published':False,'old_release_deleted':False},
 'preservation':{'primary':'alienalgorithm/postgraduate-vocabulary:main',
                 'backup':'AlienCodes/literate-enigma:codex/all-deliverables-20261113',
                 'backup_master_never_modified':'6355a02864ebae616b693200d9d26f74f5da80e9',
                 'latest_saved_source_state':json.loads((BASE/'PUBLISHED-SOURCE-STATE.json').read_text())},
 'observed_source_sha256_at_recording':{f'{n:02d}':hashlib.sha256((PAY/f'视频/脚本/{n:02d}.json').read_bytes()).hexdigest() for n in range(1,71)},
 'hash_note':'本记录为当前逐文件观察值，后续metadata/最终排版可变化；最终源冻结清单与正式验收另存。',
}
live_path=BASE/'LATEST-WORK-STATE.json'
if live_path.exists():
    live=json.loads(live_path.read_text())
    record['state']=live['state']
    record['production']=live['production']
    record['production_snapshot_basis']='LATEST-WORK-STATE.json，按实际成片验收与原生run观察更新；不把队列、诊断或失败候选计入定稿数'
raw=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()
dest=PAY/REL;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
if '--local-only' in sys.argv:
    print(json.dumps({'local_record':str(dest),'sha256':hashlib.sha256(raw).hexdigest(),'remote_write_executed':False},ensure_ascii=False))
    raise SystemExit(0)
receipts=[]
for repo,branch in [('alienalgorithm/postgraduate-vocabulary','main'),('AlienCodes/literate-enigma','codex/all-deliverables-20261113')]:
    master=api(repo,'git/ref/heads/master')['object']['sha'] if branch!='main' else None
    parent=api(repo,'git/ref/heads/'+branch)['object']['sha'];base=api(repo,'git/commits/'+parent)['tree']['sha']
    b=api(repo,'git/blobs',{'content':base64.b64encode(raw).decode(),'encoding':'base64'},'POST')
    assert b['sha']==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    tree=replace_blob(repo,base,REL.split('/'),b['sha'])
    commit=api(repo,'git/commits',{'message':'记录全部修订及最新印刷书、序言封底、书序4K和Release交付要求 [skip ci]','tree':tree,'parents':[parent]},'POST')['sha']
    api(repo,'git/refs/heads/'+branch,{'sha':commit,'force':False},'PATCH')
    assert api(repo,'git/ref/heads/'+branch)['object']['sha']==commit
    actual=api(repo,'git/blobs/'+b['sha']);assert base64.b64decode(actual['content'])==raw
    if master:assert api(repo,'git/ref/heads/master')['object']['sha']==master
    receipts.append({'repository':repo,'branch':branch,'commit':commit,'path':REL,'sha256':hashlib.sha256(raw).hexdigest(),'remote_bytes_verified':True})
    (BASE/'latest-journal-remote-receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipts[-1],ensure_ascii=False),flush=True)
target=LOCAL/REL;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
