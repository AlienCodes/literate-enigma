"""Save the live revision record in both authorized repos; no final-file claim."""
import base64,hashlib,json,subprocess
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

changes=[
 {'original':'01','changes':['保留批准的双重负担、统计回归及照片例子；说明括号规范；通俗五点简述']},
 {'original':'02','changes':['Stanford／斯坦福大学','Psychology／心理学','college-entrance exam／高考，保留原文连字符','350字五点简述；分清早期相关、两步复核与成人可信度；本篇4K定稿明确授权']},
 {'original':'03','changes':['organism／微生物','germ／病菌','cultured／培养','Ulcers／溃疡']},
 {'original':'04','changes':['cabbie／出租车司机','quickest route／最快的路线','qualify译文按用户改为并且只有大约一半，最终会合格','rear／靠后的','grey matter／灰质','alike／一样','加入街道记忆与复杂图形记忆取舍解释；通俗简述；4K定稿']},
 {'original':'05','changes':['screening／筛查','baker／面包师','co-worker／同事','convicted of整体，分离中文被判与罪保持同色']},
 {'original':'06','changes':['hoof／蹄子','guard against／防范','reasoned／推理，动词','加入人们无意发出提示并非故意欺骗的小字；4K定稿']},
 {'original':'10','changes':['整轨响度审查，末句If so弱；受控增益候选；新实际音轨尚未验收通过']},
 {'original':'11','changes':['program／程序，名词','Commentators／解说员','完整通俗简述；4K定稿']},
 {'original':'12','changes':['sip释义精准放词下','stocked up on整体、protester、packaging','批准的百事庆祝及品牌感情解释','原稿标题Coke双爆破真实问题修复候选；实际新音频验收未通过']},
 {'original':'20','changes':['ago留在who lived about5,300years ago这一行；between另起第三行','artery／动脉','joints／关节','旧内嵌结局移除，正文末屏放大居中，五点简述讲清死因与未知凶手']},
 {'original':'21','changes':['scrap／废铁，for保持普通字','核查并重排正文末屏']},
 {'original':'22','changes':['批准的玻璃立面聚光小字及新简述','撤回早前误加dubbed重点，遵用户后续没有撞词才标的具体条件','移除旧内嵌结局的窄宽/无标签特批，让独立简述正常排版']},
 {'original':'39','changes':['加入预防奏效只留下账单的小字，说明不能因没出灾难就说钱白花','通俗详细简述，澄清1000亿美元是美国本国政府企业估算；4K定稿']},
 {'original':'42','changes':['lavish中文exact巨大的/奢侈的','instruments／仪器，词表解释本语境精密观测仪器','382字五点简述，解释主镜误差、错检、COSTAR和新相机、原主镜仍有缺陷']},
 {'original':'44','changes':['这是一次对改变的压倒性地明确的拒绝，overwhelmingly是副词','Norway／挪威、Finland／芬兰分格对齐','border crossings／过境，保留复数','全轨审查，S4C1最小−1dB候选，实际新轨待验收','末屏放大居中']},
 {'original':'50','changes':['popularised as整体重点／被大众传作','324字简述，明确检出不等于致病、关联不等于因果、一勺为有争议估算','末页放大居中']},
 {'original':'51','changes':['stood for整体／代表','pedigree／来历','加入哈里森234票对范布伦60票小字','讲清乔克托语旧说与报纸错拼说','全轨响度审查，开头OK及oll wright受控增益候选；实际新轨未验收','末屏放大居中']},
 {'original':'55','changes':['罗马混凝土末屏重排','通俗简述写清石灰自修补机制，尊重既定中文使周围混凝土断裂、占据']},
 {'original':'65','changes':['正文保留英文，补充实际2016年进水/2017年报道年份说明；摘要不夸大首次取种数量']},
]
record={
 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
 'task':'70篇精读视频及正式印刷书的全部修订、重建和GitHub交付',
 'state':'SOURCE_TEXT_CHECKS_AND_STATIC_LAYOUT_NEAR_FREEZE; NEW_VIDEO_AUDIO_QC_NOT_PASSED; NEW_PDF_PREPARATION_STARTED',
 'status_is_not_a_final_delivery_claim':True,
 'scope':{'video':'全部70篇真正重渲3840×2160，按书中最新顺序编号排列，不用旧片补数',
          'source':'重点词、指定译文、小字、全70简述、末页字号和居中、全篇排版核对',
          'audio':'实际新成片全轨检查，重点10/12/44/51；质量未通过则修复并重验',
          'pdf':'用户现已解除先前暂停：正式B5印刷书，全书最新修订正文/词汇/注释/简述，保留批准插图；第2页序言和成套封底',
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
 'production':{'current_github_run':43520785753,'commit':'6d97d91b8abde321a8dcf51977ac65555d87df37',
               'selected':['10','11','12','44','51'],'new_final_videos_passed':0,
               'observed_blockers':['10/11检查参考片段缓存尚未完整，原生单线程参考准备已证实不改已有声音',
                                    '12/44/51独立声音复核与部分高亮仍需实际草稿诊断',
                                    '诊断用草稿导出需修正原生16位指纹格式比较，不能据未取回声音作通过判断'],
               'new_final_pdfs_passed':0},
 'preservation':{'primary':'alienalgorithm/postgraduate-vocabulary:main',
                 'backup':'AlienCodes/literate-enigma:codex/all-deliverables-20261113',
                 'backup_master_never_modified':'6355a02864ebae616b693200d9d26f74f5da80e9',
                 'first_saved_source_state':json.loads((BASE/'PUBLISHED-SOURCE-STATE.json').read_text())},
 'observed_source_sha256_at_recording':{f'{n:02d}':hashlib.sha256((PAY/f'视频/脚本/{n:02d}.json').read_bytes()).hexdigest() for n in range(1,71)},
 'hash_note':'本记录为当前逐文件观察值，后续metadata/最终排版可变化；最终源冻结清单与正式验收另存。',
}
raw=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()
dest=PAY/REL;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
receipts=[]
for repo,branch in [('alienalgorithm/postgraduate-vocabulary','main'),('AlienCodes/literate-enigma','codex/all-deliverables-20261113')]:
    master=api(repo,'git/ref/heads/master')['object']['sha'] if branch!='main' else None
    parent=api(repo,'git/ref/heads/'+branch)['object']['sha'];base=api(repo,'git/commits/'+parent)['tree']['sha']
    b=api(repo,'git/blobs',{'content':base64.b64encode(raw).decode(),'encoding':'base64'},'POST')
    assert b['sha']==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    tree=api(repo,'git/trees',{'base_tree':base,'tree':[{'path':REL,'mode':'100644','type':'blob','sha':b['sha']}]},'POST')['sha']
    commit=api(repo,'git/commits',{'message':'记录全部修订及最新印刷书、序言封底、书序4K和Release交付要求 [skip ci]','tree':tree,'parents':[parent]},'POST')['sha']
    api(repo,'git/refs/heads/'+branch,{'sha':commit,'force':False},'PATCH')
    assert api(repo,'git/ref/heads/'+branch)['object']['sha']==commit
    actual=api(repo,'git/blobs/'+b['sha']);assert base64.b64decode(actual['content'])==raw
    if master:assert api(repo,'git/ref/heads/master')['object']['sha']==master
    receipts.append({'repository':repo,'branch':branch,'commit':commit,'path':REL,'sha256':hashlib.sha256(raw).hexdigest(),'remote_bytes_verified':True})
    (BASE/'latest-journal-remote-receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipts[-1],ensure_ascii=False),flush=True)
target=LOCAL/REL;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
