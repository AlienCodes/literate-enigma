"""Read-only two entire public ZIP streams, only after actual66 current closed."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.parse,subprocess
R=Path(__file__).resolve().parent;W=R/'run43741796325-35-book54-review-normal18-v1';C=Path('/dev/shm/archive-writer-main061')
load=lambda p:json.loads(Path(p).read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
state=load(C/'CURRENT-ARCHIVE-STATE.json');reg=load(C/'latest_requests.json');assert reg['latest_requested_revision_completed_count']==66
entry=next(x for x in reg['articles']if x['source_id']=='35');assert entry['latest_requested_revision_complete']is True and entry['latest_revision_final']['sha256']=='b44489f1bd20cdcdd6bfd1484ca1676f088577567aa0fbe1eca8f8f3bf38bf0d'
ready=R/'ready-book54-source35-full.json';assert load(ready)['source_id']=='35'
items=[x for x in load(W/'payload-file-index.json')if '/原生来源原ZIP非新Actions/'in x['repo_path']];assert len(items)==1;x=items[0]
assert x['bytes']==47964978 and x['sha256']=='12d1791d3095652e378b17cccf7cdce75ac12d6313ec36d93f84b1930ab29d29'
rows=[]
for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
 a=load(W/('assets-'+role+'.json'));actual=subprocess.check_output(['gh','api','repos/'+repo+'/git/ref/heads/'+a['asset_branch'],'--jq','.object.sha'],text=True).strip();assert actual==a['asset_commit']
 u='https://raw.githubusercontent.com/'+repo+'/'+a['asset_commit']+'/'+urllib.parse.quote(x['repo_path'],safe='/');h=hashlib.sha256();g=hashlib.sha1(f'blob {x["bytes"]}\0'.encode());n=0
 with urllib.request.urlopen(urllib.request.Request(u,headers={'Accept-Encoding':'identity','User-Agent':'closed35-entire-public-nativeZIP-readback'}),timeout=120)as response:
  assert response.status==200
  for b in iter(lambda:response.read(196608),b''):n+=len(b);assert n<=x['bytes'];h.update(b);g.update(b)
 assert n==x['bytes']and h.hexdigest()==x['sha256']and g.hexdigest()=='4801e4e0029b018d58a51516b0ea1e920e543ea5'
 rows.append({'repository':repo,'asset_branch':a['asset_branch'],'asset_commit':a['asset_commit'],'repo_path':x['repo_path'],'bytes':n,'sha256':h.hexdigest(),'git_blob_sha':g.hexdigest(),'http_status':200,'entire_HTTP':True})
p=R/'ACTUAL-CLOSED54-NATIVE-ZIP-DUAL-ENTIRE-HTTP-BYTES-PROOF.json';p.write_text(json.dumps({'kind':'actual-closed-book54-source35-native-public-ZIP-dual-entire-HTTP-byte-proof','source_id':'35','book_order':'54','actual_complete_current_count':66,'actual_ready_sha256':sha(ready),'streams':rows,'only_read_no_local_ZIP_or_other_cache_evicted':True,'MP4_master_WAV_source_H_and_all_history_preserved':True},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'proof':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}))
