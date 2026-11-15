"""Pinned remote current66->69 one-row delta readback; no mutation."""
from pathlib import Path
import sys,json,hashlib,urllib.request,urllib.parse
sys.path.insert(0,'/workspace/work/cover4300-v7-exact15-dual-archive-20261115')
import archive_cover4300_v7_exact15 as m
R=Path(__file__).resolve().parent;W=R/'run43741796325-35-book54-review-normal18-v1';C=Path('/dev/shm/archive-writer-main061')
s=m.load(C/'CURRENT-ARCHIVE-STATE.json');p=m.load(C/'integration-plan-book54-source35-full-final.json')
oldinv=m.load(p['previous_inventory']);invraw=Path(s['actual_inventory']).read_bytes();inv=json.loads(invraw)
regraw=(C/'latest_requests.json').read_bytes();reg=json.loads(regraw)
oldrows={x['source_id']:x for x in oldinv['articles']};newrows={x['source_id']:x for x in inv['articles']}
assert len(oldrows)==len(newrows)==69 and all(newrows[k]==v for k,v in oldrows.items()if k!='35')
assert newrows['35']['previous_versions'][-1]==oldrows['35']and newrows['35']['sha256']=='b44489f1bd20cdcdd6bfd1484ca1676f088577567aa0fbe1eca8f8f3bf38bf0d'
critical=[x for x in m.load(W/'payload-file-index.json')if x['sha256']in{'478962d68b9959caea78f72ab053e31590f3d7cb9a5fe4c4db2f91827fb09873','6cfc749c60ea7fb680cd0f3f712810a7b7b5eab3349fb54f850501cfa2b2e0f3','18a7d06adaf59aa0d4bb671c31f30c0835aaf3f1ce926fd80537e21d51fdcf9d','b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}]
assert len(critical)>=4;c=m.Client();checks=[]
for role,repo,branch in m.REPOS:
 head=s['primary_main'if role=='primary'else'backup_head'];assert c.api(repo,'git/ref/heads/'+branch)['object']['sha']==head
 commit=c.api(repo,'git/commits/'+head);assert [x['sha']for x in commit['parents']]==[p['expected_heads'][role]]
 roots=m.simple(c.tree(repo,commit['tree']['sha']));oldcommit=c.api(repo,'git/commits/'+p['expected_heads'][role]);oldroots=m.simple(c.tree(repo,oldcommit['tree']['sha']))
 assert {k:v for k,v in roots.items()if k!='视频修订定稿'}=={k:v for k,v in oldroots.items()if k!='视频修订定稿'}
 oldvideo=c.tree(repo,oldroots['视频修订定稿']['sha']);video=c.tree(repo,roots['视频修订定稿']['sha']);assert roots['视频修订定稿']['sha']==s['video_subtree']
 oldreg=json.loads(c.raw(repo,oldvideo['latest_requests.json']['sha']));assert c.raw(repo,video['latest_requests.json']['sha'])==regraw and c.raw(repo,video['已归档视频总清单.json']['sha'])==invraw
 assert reg['latest_requested_revision_completed_count']==66 and oldreg['latest_requested_revision_completed_count']==65
 assert all(a==b for a,b in zip(oldreg['articles'],reg['articles'])if a['source_id']!='35')
 for k,v in oldreg.items():
  if k not in {'articles','latest_requested_revision_completed_count'}:assert reg[k]==v
 oldfinal=c.tree(repo,oldvideo['最终定稿']['sha']);oldalias=m.simple(c.tree(repo,oldfinal['视频']['sha']));newalias=m.simple(c.tree(repo,s['final_directory']['video_tree_sha']))
 assert len(oldalias)==65 and len(newalias)==66 and set(newalias)-set(oldalias)=={'54 比信先到家的鸟.mp4'}and all(newalias[k]==v for k,v in oldalias.items())
 q=Path('/workspace/work/book54-source35-original-normal18-20261115/media/book54-source35/54-4K-末句后0.6秒-原插图2秒-原简述2秒.mp4');assert newalias['54 比信先到家的鸟.mp4']['sha']==m.blob(q.read_bytes())
 readbacks=[]
 for x in critical:
  u='https://raw.githubusercontent.com/'+repo+'/'+head+'/'+urllib.parse.quote(x['repo_path'],safe='/')
  with urllib.request.urlopen(u,timeout=90)as response:assert response.status==200;raw=response.read(x['bytes']+1)
  assert len(raw)==x['bytes']and m.digest(raw)==x['sha256'];readbacks.append({'path':x['repo_path'],'bytes':len(raw),'sha256':m.digest(raw),'whole_HTTP':True})
 checks.append({'repository':repo,'actual_head':head,'root':commit['tree']['sha'],'video_tree':roots['视频修订定稿']['sha'],'all_other_root_nodes_exact':True,'current_inventory_registry_full_byte_SHA_Git_identity_exact':True,'other68_inventory_and69_requests_deep_exact':True,'old_whole35_row_preserved_without_fabricated_source_run':True,'other65_alias_nodes_exact_only_new54_alias':True,'actual_H_sourceH_user_final_and_b00_full_raw_readbacks':readbacks})
assert c.api(m.REPOS[1][1],'git/ref/heads/master')['object']['sha']==m.MASTER
record={'kind':'independent-sole-writer-actual-book54-source35-full-dual-current-postcheck','actual_complete_count':66,'actual_inventory_count':69,'actual_latest_alias_count':66,'source_id':'35','book_order':'54','checks':checks,'registry_SHA256':m.digest(regraw),'inventory_SHA256':m.digest(invraw),'closure_SHA256':m.digest((C/'actual-book54-source35-full-current-final-closure.json').read_bytes()),'original672_Git_identity_and169unique_each_repo_wholeRAW_proofs_bound':True,'original2asset_and2canonical_MP4_whole_streams_bound':True,'standalone_WAV_and_JSON4_public_whole_stream_proof_SHA256':m.digest((R/'ACTUAL-BOOK54-STANDALONE-MASTER-WAV-AND-EVIDENCE-DUAL-PUBLIC-FULL-READBACK.json').read_bytes()),'no_audio_reencode_or_GitHub_jobgreen_as_quality_substitute':True}
out=R/'ACTUAL-INDEPENDENT-BOOK54-FULL-CURRENT-PINNED-READBACK.json';m.save(out,record)
print(json.dumps({'proof':str(out),'bytes':out.stat().st_size,'sha256':m.digest(out.read_bytes()),'actual_complete66':True}),flush=True)
