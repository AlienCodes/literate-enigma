"""Resume only the unfinished backup half of an already archived exact source snapshot."""
import os,json,hashlib,time
from pathlib import Path
B=Path('/workspace/work/video-audit70-20261113')
os.environ['VIDEO_SOURCE_PAYLOAD']='/workspace/work/video-source-publish-snapshot-20261114-v9'
source=(B/'publish_sources.py').read_text(); assert source.count("result={'asset_branch'")==1
ns={};exec(compile(source.split("result={'asset_branch'",1)[0],str(B/'publish_sources.py'),'exec'),ns)
original_api=ns['api']
def retry_api(repo,path,method='GET',data=None):
 for attempt in range(3):
  try:return original_api(repo,path,method,data)
  except RuntimeError as error:
   if method!='POST' or path!='git/trees' or 'timed out' not in str(error) or attempt==2:raise
   (B/'phase9-backup-tree-retry.json').write_text(json.dumps({'repository':repo,'attempt':attempt+1,'tree_payload':data,'remote_ref_not_changed':True},ensure_ascii=False,indent=2)+'\n')
   time.sleep(2)
ns['api']=retry_api
result=json.loads((B/'PUBLISHED-SOURCE-STATE.json').read_text());assert len(result['archives'])==1 and result['archives'][0]['source_commit']=='3c320110a663b59c7e5aeb9b1bd5f6f8f4d57f20';assert result['asset_commit']==ns['asset_commit']
result['archives'].append(ns['attach']('AlienCodes/literate-enigma','codex/all-deliverables-20261113'))
(B/'PUBLISHED-SOURCE-STATE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for path in ns['files']:
 target=ns['LOCAL']/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ns['PAY']/path).read_bytes())
print(json.dumps(result,ensure_ascii=False),flush=True)
