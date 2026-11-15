"""Only four standalone original-master public-path streams after mature fullGit closure."""
from pathlib import Path
import hashlib,json,urllib.request,urllib.parse
R=Path(__file__).resolve().parent;W=R/'run43728728741-70-book50-review-normal18-v1'
H=Path('/workspace/work/review70-finalV3/43728728741-normal18/archive-handoff.json')
assert hashlib.sha256(H.read_bytes()).hexdigest()=='9b7de7262eaa8dcb8f91abfb323cab92829d10a603df42eaf6c2b5fc7cf36758'
ready=json.loads((R/'ready-book50-source70-full.json').read_bytes())
ap=json.loads((W/'assets-primary.json').read_bytes());ab=json.loads((W/'assets-backup.json').read_bytes());assert ready['asset_commit']==ap['asset_commit']==ab['asset_commit']
assert json.loads((W/'actual-dual-asset-blob-verification.json').read_bytes())['actual_dual_blob_rows']==560
assert json.loads((W/'remote-video-byte-verification.json').read_bytes())['passed']is True
index=json.loads((W/'payload-file-index.json').read_bytes());rows=[]
targets=[x for x in index if '/原节目母带WAV/'in x['repo_path']and Path(x['repo_path']).name in {'70-original-program-master-pre-video-AF.wav','70-original-program-master-export.json'}]
assert len(targets)==2
for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
 asset=json.loads((W/('assets-'+role+'.json')).read_bytes())
 for item in targets:
  url='https://raw.githubusercontent.com/'+repo+'/'+asset['asset_commit']+'/'+urllib.parse.quote(item['repo_path'],safe='/');hasher=hashlib.sha256();g=hashlib.sha1(f'blob {item["bytes"]}\0'.encode());n=0
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'actual-standalone-original-program-master-role-readback','Accept-Encoding':'identity'}),timeout=120)as response:
   assert response.status==200
   for block in iter(lambda:response.read(196608),b''):
    n+=len(block);assert n<=item['bytes'];hasher.update(block);g.update(block)
  assert n==item['bytes']and hasher.hexdigest()==item['sha256']
  rows.append({'repository':repo,'commit':asset['asset_commit'],'repo_path':item['repo_path'],'bytes':n,'sha256':hasher.hexdigest(),'git_blob_sha':g.hexdigest(),'http_status':200,'entire_stream':True})
proof={'kind':'actual-source70-book50-explicit-standalone-original-program-master-and-export-evidence-dual-public-path-full-readback','source_id':'70','book_order':'50','role':'original-program-master/pre-video-AF-not-post-AAC','WAV_bytes':6739004,'WAV_sha256':'950829b17bedc5ac103b93bb9b488a712163800bbf5c392bf1163b381cd61f34','export_json_sha256':'2d81a706c495244c8233e8f91864d7a0911b851b94122f7546c3a22f70d8bb8e','original_export_remains_bound_to_original_native_video_not_rewritten_to_normal_final':True,'streams':rows,'all4_streams_verified':True,'original_sourceQA_and_finalH_unchanged':True}
out=R/'ACTUAL-BOOK50-STANDALONE-MASTER-WAV-AND-EVIDENCE-DUAL-PUBLIC-FULL-READBACK.json'
with out.open('x')as log:json.dump(proof,log,ensure_ascii=False,indent=2);log.write('\n')
print(json.dumps({'proof':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'all4_actual_whole_streams':True}),flush=True)
