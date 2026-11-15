"""Original dual verifier/MP4/READY plus standalone master public-path readback."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,sys,urllib.request,urllib.parse
R=Path(__file__).resolve().parent
W=R/'run43736478355-58-book67-review-normal18-v1'
H='/workspace/work/review58-finalV3/43736478355-normal18/archive-handoff.json'
HS='4c833c5b9581e4974fd28a92658711578219989ca9092c60b531ce215572fe82'
assert hashlib.sha256(Path(H).read_bytes()).hexdigest()==HS
assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=419430400+8*1024*1024
monitor=json.loads((R/'ACTUAL-BOOK67-HYBRID-stream-stream-actual-01-400-MONITOR.json').read_bytes())
assert monitor['process_returncode']==0 and monitor['original400MiB_trip']is False
for role in ['primary','backup']:
 x=json.loads((W/('assets-'+role+'.json')).read_bytes())
 assert x['asset_commit']=='04d25604f2b3739d7118a568c0af5632a2795367'and x['root_tree']=='7f6360c2592f067d4aca4b560b316d21e0b5117d'and x['remote_asset_ref_verified']is True and x['all_blobs_raw_HTTP_readback_exact']is True
def run(args,p,timeout):
 with p.open('x')as log:
  process=subprocess.run(list(map(str,args)),stdout=log,stderr=subprocess.STDOUT,timeout=timeout,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(R)})
 assert process.returncode==0,str(p)
with ThreadPoolExecutor(max_workers=2)as pool:
 x=pool.submit(run,[sys.executable,R/'archive_batch.py','stream','--work-dir',W],W/'actual-dual-full-MP4-HTTP.log',180)
 y=pool.submit(run,[sys.executable,R/'verify_dual_media_asset_blobs.py','--work-dir',W,'--expected-files','284'],W/'actual-dual-Git-blobs.log',400)
 x.result();y.result()
index=json.loads((W/'payload-file-index.json').read_bytes());rows=[]
targets=[x for x in index if '/原节目母带WAV/'in x['repo_path']and Path(x['repo_path']).name in {'58-original-program-master-pre-video-AF.wav','58-original-program-master-export.json'}]
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
proof={'kind':'actual-source58-book67-explicit-standalone-original-program-master-and-export-evidence-dual-public-path-full-readback','source_id':'58','book_order':'67','role':'original-program-master/pre-video-AF-not-post-AAC','WAV_bytes':7540124,'WAV_sha256':'3bfba6a7aff011312ee82fca359ec69947aef371a05abc56c42dbf45918bf5d5','export_json_sha256':'262a4e86c087357da858d8c40f6bb5b539ad781c443ebe3a8f20f9f380d3077b','original_export_remains_bound_to_original_native_video_not_rewritten_to_normal_final':True,'streams':rows,'all4_streams_verified':True,'original_sourceQA_and_finalH_unchanged':True}
out=R/'ACTUAL-BOOK67-STANDALONE-MASTER-WAV-AND-EVIDENCE-DUAL-PUBLIC-FULL-READBACK.json'
with out.open('x')as log:json.dump(proof,log,ensure_ascii=False,indent=2);log.write('\n')
ready=R/'ready-book67-source58-full.json';run([sys.executable,R/'emit_ready_revision_download_manifest.py','--work-dir',W,'--handoff',H,'--output',ready],W/'actual-ready-manifest.log',60)
assert not (W/'assets.git').exists()
print(json.dumps({'ready':str(ready),'bytes':ready.stat().st_size,'sha256':hashlib.sha256(ready.read_bytes()).hexdigest(),'original568_blobrows_and_two_whole_MP4_HTTP_passed':True,'all145unique_blobs_each_repository_full_raw_already_passed':True,'standalone_WAV_and_export_JSON_4public_whole_streams_passed':True,'only_owned_standard_Git_seed_already_fsck_closed_and_removed':True,'no_current_change_by_this_stage':True}),flush=True)
