"""Bind actual user094/095 instructions forwarded by root; prefer writer's immutable ledger when ready."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;C=H/'candidate-payload';root=Path('/workspace/work/first50-review-release');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
quotes={
94:'在这里 而 改为 并且 而且你发现这个地方这个最后这一页这个排版是有问题的。这个最后这一页这个排版是有问题的，发现了吗？发现发发现了吗？这应该是之前的下面是有这么那个叫是有那种类似于简述的东西。然后弄没了，这这个地方这个他他没有调整，不是说让你认真调整了吗？怎么没有？怎么没有去做这件事呢？这个地方，这个地方认认真真弄一下。然后4k定稿，然后4k定稿记住0.6秒。',
95:'最后这一页这个字太小，这个排版注意一下，排版稍微中间靠一些。上下稍微往中间靠一些。拍完你让人看的舒适，你最后对不对？最后最后就这么两行字，你笑的时候把这个字要放大一些。这个排版你不不知道怎么排吗？'}
p=C/'视频/工具/用户同意记录.json';d=json.loads(p.read_text());rows=[]
for number in [94,95]:
 rp=root/f'USER-REVIEW-2026-11-14-{number:03}.json';entry={'篇':'65','日期':'2026-11-14','原话':quotes[number],'用于':f'用户{number:03}授权本篇4K定稿并按末句后0.6秒展示原图；仅末句普通and对应而改并且，原而建保留；按095使用原生S17字号上限88（4K176）给正文整体适当上下余白并居中，两个原grammar和原独立五点末卡保留，不加回inline简述。092音频单独诊断并等待最小候选及原全门，文字与静态不冒充成片QA。PDF不动。','用户记录号':f'{number:03}'}
 if rp.is_file():
  r=json.loads(rp.read_text());assert r['source_id']=='65'and r['book_order']=='37';entry.update({'原话':r['user_instruction_verbatim'],'来源文件':str(rp),'来源文件SHA256':sha(rp),'来源用户原话已实际读取':True});rows.append({'record':f'{number:03}','path':str(rp),'sha256':sha(rp),'writer_raw_read':True})
 else:
  entry.update({'来源说明':'主会话root在本任务中逐字转交的当前用户原话；archive_writer的单独文件尚未落地，不宣称已经读取或双仓保存该单独文件。','来源用户原话已由root转交':True,'单独安全ledger实际读取':False});rows.append({'record':f'{number:03}','root_forwarded_actual_user_words':True,'writer_raw_read':False})
 previous=[i for i,x in enumerate(d['记录'])if x.get('篇')=='65'and x.get('用户记录号')==entry['用户记录号']]
 assert len(previous)<=1
 if previous:
  assert rp.is_file() and d['记录'][previous[0]].get('单独安全ledger实际读取')is False
  d['记录'][previous[0]]=entry
 else:d['记录'].append(entry)
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');report={'article':'65','book_order':'37','final_authorization_user094095':True,'current_user_words_bound_without_invented_file_or_SHA':True,'records':rows,'local_consent_file_sha256':sha(p),'new_native_media_quality_acceptance_claimed':False};(H/'user094095-actual-consent-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
