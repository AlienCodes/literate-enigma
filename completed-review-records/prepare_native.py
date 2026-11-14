from pathlib import Path
import json,sys
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root));import publish_review as P
m=json.loads((root/'MANIFEST.json').read_text());z=json.loads((root/'ZIP-IDENTITY.json').read_text());st=json.loads((root/'STATE.json').read_text());idx=json.loads(Path('/workspace/work/video-archive-batches-20261114/operations-native43554669373-46/final-remote-cumulative-inventory.json').read_text());lookup={x['source_id']:x for x in idx['articles']};sources=[]
for v in m['videos']:
 if v['source_id'] in lookup:
  row=lookup[v['source_id']];commit='3c320110a663b59c7e5aeb9b1bd5f6f8f4d57f20'
 else:
  n=v['source_id'];run=43556145154 if n=='02' else 43556226408;b=Path(f'/workspace/work/video-archive-batches-20261114/run{run}-{n}');row=json.loads((b/'prepared-archive.json').read_text())['articles'][0];commit=json.loads((b/'assets-primary.json').read_text())['asset_commit']
 assert row['bytes']==v['bytes']and row['sha256']==v['sha256'];sources.append({'source_id':v['source_id'],'commit':commit,'repo_path':row['video_repo_path'],'bytes':v['bytes'],'sha256':v['sha256']})
n={'release_id':st['release_id'],'preview_target_commit':st['preview_target_commit'],'manifest_sha256':P.sha(root/'MANIFEST.json'),'ZIP':z,'published_pdf':json.loads(Path('/workspace/work/video-revision-delivery/published-pdf-v4-frozen-primary.json').read_text()),'video_sources':sources};(root/'NATIVE-INPUT.json').write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n')
files={'.github/first50-review/native_review.py':(root/'native_review.py').read_bytes(),'.github/first50-review/NATIVE-INPUT.json':(root/'NATIVE-INPUT.json').read_bytes(),'.github/first50-review/MANIFEST.json':(root/'MANIFEST.json').read_bytes(),'.github/workflows/publish-first50-review.yml':(root/'publish-first50-review.yml').read_bytes(),'local-upload-failure.log':(root/'publication.log').read_bytes(),'streaming-ZIP-transport-check.json':(root/'streaming-ZIP-transport-check.json').read_bytes()}
print(json.dumps(P.archive_records('native-preparation',files),ensure_ascii=False),flush=True)
