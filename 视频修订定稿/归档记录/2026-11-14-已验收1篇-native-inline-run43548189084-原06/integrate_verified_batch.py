"""Narrow fresh-HEAD Git-tree graft of already dual-verified passed4K assets.

Uses the established archive_batch/prepare_operation outputs. No rendering,
source editing, quality policy changes, release operations or master writes.
Requires an explicit writer window and exact observed parent heads.
"""
import argparse,base64,datetime,hashlib,json,pathlib,subprocess,urllib.parse,urllib.request
B=pathlib.Path(__file__).resolve().parent
MASTER='6355a02864ebae616b693200d9d26f74f5da80e9'
REPOS=[('primary','alienalgorithm/postgraduate-vocabulary','main'),('backup','AlienCodes/literate-enigma','codex/all-deliverables-20261113')]
def load(p):return json.loads(pathlib.Path(p).read_text())
def save(p,o):pathlib.Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def gitblob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--plan',required=True);a.add_argument('--execute',action='store_true');args=a.parse_args();assert args.execute,'Explicit root-granted writer window required'
 plan=load(args.plan);assert plan['writer_window_granted_by_root'] is True
 token=subprocess.check_output(['gh','auth','token'],text=True).strip()
 def api(repo,path,method='GET',data=None):
  q=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
  with urllib.request.urlopen(q,timeout=90)as r:return json.loads(r.read())
 def tree(repo,sha,recursive=False):
  x=api(repo,'git/trees/'+sha+('?recursive=1' if recursive else ''));assert not x.get('truncated');return {z['path']:z for z in x['tree']}
 def shallow(rows):return {k:{n:v[n] for n in ['path','mode','type','sha']} for k,v in rows.items()}
 prior=pathlib.Path(plan['previous_inventory']).read_bytes();old=load(plan['previous_inventory']);op=pathlib.Path(plan['operation_work_dir']);om=load(op/'prepared-archive.json')
 latest=next((op/'payload').rglob('累计清单快照.json')).read_bytes();inventory=json.loads(latest)
 assert inventory['archived_passed_count']==plan['result_count'];newids=[];assets=[];streams=0
 for raw in plan['article_work_dirs']:
  w=pathlib.Path(raw);m=load(w/'prepared-archive.json');p=load(w/'assets-primary.json');k=load(w/'assets-backup.json');assert p['asset_commit']==k['asset_commit'] and p['video_tree_sha']==k['video_tree_sha'];s=load(w/'remote-video-byte-verification.json');assert s['passed'] and len(s['streams'])==len(m['articles'])*2
  for article in m['articles']:
   assert article['passed_per_article'] is True;newids.append(article['source_id'])
   for role,repo,branch in REPOS:
    ss=[v for v in s['streams'] if v['repository']==repo and v['source_id']==article['source_id']];assert len(ss)==1;v=ss[0];assert v['passed'] and v['http_status']==200 and v['sha256']==article['sha256'] and v['bytes']==article['bytes'] and v['pinned_asset_commit']==p['asset_commit'];streams+=1
  assets.append((m,p,w))
 p=load(op/'assets-primary.json');k=load(op/'assets-backup.json');assert p['asset_commit']==k['asset_commit'] and p['video_tree_sha']==k['video_tree_sha'];assets.append((om,p,op))
 assert len(set(newids))==len(newids);oldrows={v['source_id']:v for v in old['articles']};newrows={v['source_id']:v for v in inventory['articles']};assert all(newrows[n]==v for n,v in oldrows.items());assert set(newrows)-set(oldrows)==set(newids)
 assert api(REPOS[1][1],'git/ref/heads/master')['object']['sha']==MASTER
 receipt={'status':'fresh_head_graft_prepared','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archived_passed_count':len(newrows),'new_source_ids':newids,'remaining_not_claimed_passed':70-len(newrows),'source_run':plan['source_run'],'actual_public_HTTP200_full_MP4_SHA256_streams':streams,'native_inline_final_bytes_preserved_without_append_or_rerender':True,'derived_final_GEN_separately_labeled':True,'release_created':False,'whole70_passed_claimed':False,'archives':[]};path=op/'final-archive-receipt.json'
 prepared=[]
 for role,repo,branch in REPOS:
  expected=plan['expected_heads'][role];assert api(repo,'git/ref/heads/'+branch)['object']['sha']==expected
  root=tree(repo,api(repo,'git/commits/'+expected)['tree']['sha']);video=tree(repo,root['视频修订定稿']['sha']);oldfull=tree(repo,root['视频修订定稿']['sha'],True)
  oldblob=api(repo,'git/blobs/'+video['已归档视频总清单.json']['sha']);assert base64.b64decode(oldblob['content'])==prior
  updated=shallow(video)
  for m,asset,w in assets:
   remote=tree(repo,asset['video_tree_sha'],True);prefix=m['prefix'];relprefix=prefix.split('/',1)[1]
   for f in asset['files_index']:
    rel=f['repo_path'][len(prefix)+1:];r=remote[rel];assert r['type']=='blob' and r['sha']==f['git_blob_sha'] and r['size']==f['bytes']
   if relprefix.startswith('归档记录/'):
    child=shallow(tree(repo,video['归档记录']['sha'])) if '归档记录' in video else {};name=relprefix.split('/',1)[1];assert name not in child;child[name]={'path':name,'mode':'040000','type':'tree','sha':asset['video_tree_sha']};newchild=api(repo,'git/trees','POST',{'tree':list(child.values())})['sha'];updated['归档记录']={'path':'归档记录','mode':'040000','type':'tree','sha':newchild}
   else:
    assert '/' not in relprefix and relprefix not in updated;updated[relprefix]={'path':relprefix,'mode':'040000','type':'tree','sha':asset['video_tree_sha']}
  blob=api(repo,'git/blobs','POST',{'content':base64.b64encode(latest).decode(),'encoding':'base64'})['sha'];assert blob==gitblob(latest)
  updated['已归档视频总清单.json']={'path':'已归档视频总清单.json','mode':'100644','type':'blob','sha':blob}
  vtree=api(repo,'git/trees','POST',{'tree':list(updated.values())})['sha'];current=tree(repo,vtree,True)
  assert all(n=='已归档视频总清单.json' or (n in current and current[n]['sha']==v['sha'] and current[n]['mode']==v['mode']) for n,v in oldfull.items() if v['type']=='blob')
  roots=shallow(root);roots['视频修订定稿']={'path':'视频修订定稿','mode':'040000','type':'tree','sha':vtree};rtree=api(repo,'git/trees','POST',{'tree':list(roots.values())})['sha']
  commit=api(repo,'git/commits','POST',{'message':plan['message'],'tree':rtree,'parents':[expected]})['sha'];prepared.append((role,repo,branch,expected,commit,vtree,rtree,root))
 assert len({x[5] for x in prepared})==1
 save(op/'prepared-graft-commits.json',[{'role':r,'repository':repo,'branch':branch,'parent':parent,'commit':c,'video_subtree':v,'root_tree':rt} for r,repo,branch,parent,c,v,rt,_ in prepared])
 for role,repo,branch,expected,*_ in prepared:assert api(repo,'git/ref/heads/'+branch)['object']['sha']==expected,'Another writer moved HEAD; do not force'
 for role,repo,branch,expected,commit,vtree,rtree,oldroot in prepared:
  api(repo,'git/refs/heads/'+branch,'PATCH',{'sha':commit,'force':False});assert api(repo,'git/ref/heads/'+branch)['object']['sha']==commit
  roots=tree(repo,rtree);assert {n:r['sha'] for n,r in oldroot.items() if n!='视频修订定稿'}=={n:r['sha'] for n,r in roots.items() if n!='视频修订定稿'}
  actual=api(repo,'contents/视频修订定稿/已归档视频总清单.json?ref='+commit);assert base64.b64decode(actual['content'])==latest
  assert api(REPOS[1][1],'git/ref/heads/master')['object']['sha']==MASTER
  receipt['archives'].append({'role':role,'repository':repo,'branch':branch,'parent':expected,'commit':commit,'video_subtree':vtree,'root_tree':rtree,'all_new_blob_sizes_and_identities_verified':True,'all_prior_archive_blob_modes_and_identities_unchanged_except_cumulative_index':True,'all_other_root_subtrees_unchanged':True,'protected_master_unchanged':MASTER});save(path,receipt)
 receipt['status']='permanent_double_repository_archive_verified';save(path,receipt);(op/'final-remote-cumulative-inventory.json').write_bytes(latest)
 state=load(B/'CURRENT-ARCHIVE-STATE.json');state.update(permanently_archived_count=len(newrows),primary_main=prepared[0][4],backup_head=prepared[1][4],video_subtree=prepared[0][5],actual_inventory=str(op/'final-remote-cumulative-inventory.json'),last_completed_receipt=str(path),next_true_passed_not_main_archived=[],next_expected_count=None,main_backup_write_window='archive writer window; next root window must be coordinated');save(B/'CURRENT-ARCHIVE-STATE.json',state)
 print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
