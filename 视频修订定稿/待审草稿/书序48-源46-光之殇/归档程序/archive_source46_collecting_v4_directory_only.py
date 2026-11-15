"""Public collecting drafts only. Serving registry, accepted rows and final trees stay exact."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import base64,copy,hashlib,json,os,shutil,subprocess,sys,tempfile,urllib.request,urllib.parse
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061');sys.path.insert(0,str(B))
from integrate_verified_batch import post_incremental_tree
def load(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def spec(p):p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}
def pinned(x):
 p=Path(x['path']);assert p.suffix in {'.json','.md','.diff'};raw=p.read_bytes();assert len(raw)==x['bytes']and hashlib.sha256(raw).hexdigest()==x['sha256'];return raw
def fixed(p,size,sha):return {'path':p,'bytes':size,'sha256':sha}
def main():
 state=load(C/'CURRENT-ARCHIVE-STATE.json');assert state['primary_main']=='f8ea72ad21602dace1107cae49af0304a9a4d88b'and state['backup_head']=='4541e395ecd68b667ab44c0fb372f4b01be7f3b5'
 registry=(C/'latest_requests.json').read_bytes();rr=json.loads(registry);entry=next(x for x in rr['articles']if x['source_id']=='46');assert entry['latest_feedback_authority']=='152'and entry['latest_finalization_authority']is None and entry['final_4K_generation_authorized']is False and entry['latest_requested_revision_complete']is False
 assert rr['latest_requested_revision_completed_count']==47 and state['permanently_archived_count']==64 and state['final_directory']['video_count']==63
 hp=fixed('/workspace/work/source46-consolidated-v4-COLLECTING-NOT-FINAL-20261115/SOURCE46-BOOK48-CONSOLIDATED-V4-COLLECTING-DRAFT-HANDOFF.json',4374,'7db9c79b0c83a1bbf1d210228014b2ffc25a9f1a076544f34c8dce1d84f48772');h4=json.loads(pinned(hp));h3=json.loads(pinned(h4['prior_v3_H_preserved']));h2=json.loads(pinned(h3['prior_v2_H_preserved']));h1=json.loads(pinned(h2['prior_first_translation_H_preserved']))
 for h in [h1,h2,h3,h4]:assert h['source_id']=='46'and h['book_order']==48 and h['production_delivery_eligible']is False and h['preview_only']is True and h['new_matching_draft_GEN_NOT_generated']is True
 R=Path(tempfile.mkdtemp(prefix='book48-source46-v4-collecting-metadata-',dir=str(B)));W=R/'draft-only-small-records';P=W/'payload';P.mkdir(parents=True);prefix=Path('视频修订定稿/待审草稿');article=prefix/'书序48-源46-光之殇';bindings=[];deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
 def add(x,relative,role):
  raw=pinned(x);assert x['sha256']not in deny;target=P/relative;assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);v={**x,'repo_path':str(relative),'role':role};bindings.append(v);return {k:v[k]for k in ['repo_path','bytes','sha256','role']}
 histories=[];latest=None
 versions=[('历史/149-151原草稿',None,h1['prior_149151_source_MD_and_state_unchanged']['source'],h1['prior_149151_source_MD_and_state_unchanged']['MD'],None),('历史/第一译文',h2['prior_first_translation_H_preserved'],h1['new_draft_source'],h1['new_draft_MD'],h1),('历史/v2',h3['prior_v2_H_preserved'],h2['new_draft_source'],h2['new_draft_MD'],h2),('历史/v3',h4['prior_v3_H_preserved'],h3['new_draft_source'],h3['new_draft_MD'],h3),('补充译文-v4',hp,h4['new_draft_source'],h4['new_draft_MD'],h4)]
 notes=[['narrow_validation','full_eight_leaf_JSON_changes','one_MD_sentence_diff'],['narrow_draft_validation','JSON_nine_leaf_changes','MD_only_requested_changes'],['narrow_draft_validation','JSON_exactly_eight_Chinese_leaf_changes','MD_only_S8_translation_and_banter_gloss_changes'],['narrow_draft_validation','JSON_exactly_eleven_S9_and_local_review_leaf_changes','MD_only_requested_S9_and_current_glossary_changes']]
 for i,(version,hs,js,md,h)in enumerate(versions):
  folder=article/version;record={'version':version,'source_JSON':add(js,folder/'46.json','collecting-draft-source-NOT-final'),'MD':add(md,folder/'46-lost-in-the-glare.md','collecting-draft-MD-NOT-final')}
  if hs:record['handoff']=add(hs,folder/'来源与范围'/Path(hs['path']).name,'original-frozen-draft-H-NOT-production-QA')
  if h:
   for key in notes[i-1]:x=h[key];add(x,folder/'来源与范围'/Path(x['path']).name,'narrow-draft-text-note-NOT-official-full-QA')
  if i==0:add(h1['prior_149151_source_MD_and_state_unchanged']['state'],folder/'SOURCE46-COLLECTING-PAUSED152-STATE.json','source46-only-original-collecting-state')
  if i==4:latest=record
  else:histories.append(record)
 raw_specs=[h1['new_latest_raw_advice'],h2['actual_two_user_requests'],h3['latest_actual_raw_user_request'],h4['latest_actual_raw_user_request']];requests=[]
 for x in raw_specs:
  archived=add(x,article/'用户补充原话'/Path(x['path']).name,'actual-user-raw-no-numeric-feedback-ID-invented');data=json.loads(pinned(x))
  for request in data.get('requests',[data]):
   assert request['local_descriptive_id']and request['raw_user_text_verbatim'];requests.append({'descriptive_id':request['local_descriptive_id'],'raw_user_text_verbatim':request['raw_user_text_verbatim'],'source_location':request['source_location'],'English_anchor':{k:v for k,v in request.items()if k.startswith('English_anchor')},'raw_record':archived})
 assert len(raw_specs)==4 and len(requests)==5
 for x in [fixed('/workspace/work/root-source46-book48-consolidated-v3-narrow-draft-review-20261115.json',3148,'18a05ce8bf917c012fb9c4745f5ec0b608f726270a4c7a24d620793f13eb36b5'),fixed('/workspace/work/root-source46-book48-consolidated-v4-narrow-draft-review-20261115.json',2545,'46130561ff66d9f2508780589292d1a704e0a2b3834e68c5b93771bae984f6e3')]:add(x,article/'核验说明'/Path(x['path']).name,'root-narrow-draft-review-NOT-production-QA')
 index={'kind':'dedicated-pending-draft-index-not-serving-or-final','source_id':'46','frozen_book_order':'48','current_video_order':'48','title_zh':'光之殇','status':'COLLECTING_USER_FEEDBACK','latest_version':'v4','latest':latest,'history':histories,'actual_supplement_requests':requests,'actual_raw_JSON_files':4,'actual_request_count':5,'production_delivery_eligible':False,'preview_only':True,'finalization_authority':None,'hold_authority':'152','original149to152_registry_entry_preserved':True,'new_GEN_TTS_audio_render_or_media_generated':False,'legacy_GEN_bytes_not_archived_only_original_descriptor_in_H_retained':True,'official_complete_text_or_audio_QA_not_claimed':True,'latest_requests_registry_SHA256_unchanged':hashlib.sha256(registry).hexdigest(),'latest_final_tree_unchanged':state['final_directory']['final_tree_sha'],'video_alias_tree_unchanged':state['final_directory']['video_tree_sha'],'49to70_pause153_and_PDF_pause_preserved':True}
 save(P/article/'待审草稿索引.json',index);save(P/prefix/'待审索引.json',{'kind':'public-non-serving-pending-draft-catalog','drafts':[{'source_id':'46','book_order':'48','latest_version':'v4','status':'COLLECTING_USER_FEEDBACK','draft_index_repo_path':str(article/'待审草稿索引.json'),'production_delivery_eligible':False,'finalization_authority':None,'hold_authority':'152'}],'serving_registry_and_accepted_final_directories_unchanged':True})
 save(P/article/'用途与实际来源映射.json',{'kind':'public-draft-only-source-to-remote-map','bindings':bindings,'legacy_GEN_only_descriptor_not_file':h4['legacy_historical_GEN_exists_only_in_original_before_folder'],'legacy_GEN_not_read_or_uploaded':True,'not_a_final_or_preview_video':True})
 (P/article/'待审说明.md').write_text('# 第48篇《光之殇》待审草稿\n\n当前为收集意见中的 v4，原用户152的等待要求继续有效。这不是定稿视频，也未获得生成许可。\n\n保留原149—151草稿及第一译文、v2、v3历史；四份原话JSON包含五条实际补充请求，未另造数字反馈号。最新JSON、MD及逐项来源见待审草稿索引.json。\n\n没有新GEN、音频、渲染或官方全篇影音验收；旧GEN只在原H中留来源描述，本包不含该GEN文件。现行视频清单、最新定稿目录、49—70篇及PDF均保持原样。\n')
 target=P/article/'归档程序'/Path(__file__).name;target.parent.mkdir();shutil.copyfile(__file__,target)
 files=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':digest(p)}for p in sorted(P.rglob('*'))if p.is_file()];assert all(x['sha256']not in deny for x in files)
 save(W/'prepared-archive.json',{'prefix':str(prefix),'asset_branch':'codex/book48-source46-v4-collecting-draft-only-20261115','kind':'public-draft-only-small-metadata-asset-no-accepted-article'});save(W/'payload-file-index.json',files);shutil.copyfile(B/'archive_batch.py',R/'archive_batch.py');save(C/'active-source46-v4-draft-only-location.json',{'root':str(R),'work_dir':str(W),'files':len(files),'logical_bytes':sum(x['bytes']for x in files)})
 for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
  with (W/(role+'-push.log')).open('w')as f:subprocess.run([sys.executable,str(R/'archive_batch.py'),'push','--work-dir',str(W),'--repo',repo],check=True,timeout=85,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'TMPDIR':str(R),'PYTHONDONTWRITEBYTECODE':'1'})
 token=subprocess.check_output(['gh','auth','token'],text=True).strip()
 def api(repo,path,method='GET',data=None):
  q=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json'})
  with urllib.request.urlopen(q,timeout=90)as r:return json.loads(r.read())
 def tree(repo,sha,recursive=False):
  d=api(repo,'git/trees/'+sha+('?recursive=1'if recursive else''));assert not d.get('truncated');return {x['path']:x for x in d['tree']}
 def simple(t):return {k:{f:v[f]for f in ['path','mode','type','sha']}for k,v in t.items()}
 def verify(repo,asset):
  leaves=tree(repo,asset['video_tree_sha'],True);assert sum(v['type']=='blob'for v in leaves.values())==len(files)
  def check(x):
   raw=(P/x['repo_path']).read_bytes();rel=x['repo_path'][len(str(prefix))+1:];leaf=leaves[rel];expected=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert leaf['mode']=='100644'and leaf['sha']==expected and leaf['size']==len(raw);got=base64.b64decode(api(repo,'git/blobs/'+expected)['content']);assert got==raw;return True
  with ThreadPoolExecutor(max_workers=4)as pool:assert all(pool.map(check,files))
 assets=[load(W/'assets-primary.json'),load(W/'assets-backup.json')];assert assets[0]['asset_commit']==assets[1]['asset_commit']and assets[0]['video_tree_sha']==assets[1]['video_tree_sha']
 for repo,asset in zip(['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma'],assets):verify(repo,asset)
 assert api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha']=='6355a02864ebae616b693200d9d26f74f5da80e9'
 prepared=[]
 for role,repo,branch,parent in [('primary','alienalgorithm/postgraduate-vocabulary','main',state['primary_main']),('backup','AlienCodes/literate-enigma','codex/all-deliverables-20261113',state['backup_head'])]:
  assert api(repo,'git/ref/heads/'+branch)['object']['sha']==parent;roots=tree(repo,api(repo,'git/commits/'+parent)['tree']['sha']);video=tree(repo,roots['视频修订定稿']['sha']);assert roots['视频修订定稿']['sha']==state['video_subtree']and '待审草稿'not in video
  assert base64.b64decode(api(repo,'git/blobs/'+video['latest_requests.json']['sha'])['content'])==registry
  assert video['最终定稿']['sha']==state['final_directory']['final_tree_sha'];new=simple(video);new['待审草稿']={'path':'待审草稿','mode':'040000','type':'tree','sha':assets[0]['video_tree_sha']};vsha=post_incremental_tree(api,repo,new,roots['视频修订定稿']['sha'],video)
  nr=simple(roots);nr['视频修订定稿']={'path':'视频修订定稿','mode':'040000','type':'tree','sha':vsha};rootsha=api(repo,'git/trees','POST',{'tree':list(nr.values())})['sha'];commit=api(repo,'git/commits','POST',{'message':'保存第48篇源46累计待审草稿v4及实际用户原话，不改定稿或生成影音 [skip ci]','tree':rootsha,'parents':[parent]})['sha'];prepared.append((role,repo,branch,parent,commit,vsha,rootsha,roots,video))
 assert len({x[5]for x in prepared})==1;save(R/'prepared-draft-only-canonical-commits.json',[{'role':x[0],'parent':x[3],'commit':x[4],'video_subtree':x[5]}for x in prepared])
 for _,repo,branch,parent,*_ in prepared:assert api(repo,'git/ref/heads/'+branch)['object']['sha']==parent
 archives=[]
 for role,repo,branch,parent,commit,vsha,rootsha,roots,video in prepared:
  api(repo,'git/refs/heads/'+branch,'PATCH',{'sha':commit,'force':False});assert api(repo,'git/ref/heads/'+branch)['object']['sha']==commit;actualroot=tree(repo,rootsha);actual=tree(repo,vsha)
  assert {k:v['sha']for k,v in roots.items()if k!='视频修订定稿'}=={k:v['sha']for k,v in actualroot.items()if k!='视频修订定稿'}
  assert simple(video)=={k:v for k,v in simple(actual).items()if k!='待审草稿'}and actual['待审草稿']['sha']==assets[0]['video_tree_sha']
  assert base64.b64decode(api(repo,'git/blobs/'+actual['latest_requests.json']['sha'])['content'])==registry;verify(repo,assets[0]);assert api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha']=='6355a02864ebae616b693200d9d26f74f5da80e9'
  archives.append({'role':role,'repository':repo,'branch':branch,'parent':parent,'commit':commit,'video_subtree':vsha,'draft_subtree':assets[0]['video_tree_sha'],'all_draft_files_complete_readback':len(files),'registry_git_blob_unchanged':actual['latest_requests.json']['sha'],'final_entire_tree_unchanged':actual['最终定稿']['sha'],'accepted_inventory_git_blob_unchanged':actual['已归档视频总清单.json']['sha'],'AGENTS_other_roots_PDF_master_unchanged':True})
 receipt={'kind':'actual-source46-book48-collecting-v4-draft-directory-only-dual-closure','archives':archives,'metadata_asset_commit':assets[0]['asset_commit'],'draft_files_per_repo':len(files),'actual_small_blob_complete_readbacks':4*len(files),'only_new_video_root_entry':'待审草稿','source46_latest_registry_whole_bytes_unchanged':True,'registry_SHA256_unchanged':hashlib.sha256(registry).hexdigest(),'all70_source_request_rows_and_global_policies_unchanged':True,'accepted_count_unchanged':64,'latest_final_video_count_unchanged':63,'completed_request_count_unchanged':47,'video_alias_tree_unchanged':state['final_directory']['video_tree_sha'],'no_GEN_audio_TTS_render_media_QA_or_Release':True,'latest_draft_version':'v4','source46_book48_hold152_no_final_authority_preserved':True,'public_draft_index_repo_path':str(prefix/'待审索引.json'),'source46_draft_index_repo_path':str(article/'待审草稿索引.json'),'v4_source_repo_path':str(article/'补充译文-v4/46.json'),'v4_MD_repo_path':str(article/'补充译文-v4/46-lost-in-the-glare.md'),'v4_H_SHA256':hp['sha256']};out=R/'actual-source46-v4-draft-only-dual-closure.json';save(out,receipt)
 state.update(primary_main=archives[0]['commit'],backup_head=archives[1]['commit'],video_subtree=archives[0]['video_subtree'],last_metadata_only_draft_receipt=str(out));save(C/'CURRENT-ARCHIVE-STATE.json',state)
 fsck=subprocess.run(['git','--git-dir='+str(W/'assets.git'),'fsck','--full'],capture_output=True,text=True);assert fsck.returncode==0;shutil.rmtree(W/'assets.git');idx=W/'assets.index'
 if idx.exists():idx.unlink()
 print(json.dumps({'receipt':str(out),'receipt_sha256':digest(out),'primary_main':state['primary_main'],'backup_delivery':state['backup_head'],'only_draft_directory_added':True,'registry_and_all_final_trees_unchanged':True,'files_per_repo':len(files)}),flush=True)
if __name__=='__main__':main()
