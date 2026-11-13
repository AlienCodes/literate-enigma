"""Read public QC relay files through GitHub's Git blob API; no private inputs."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.parse

REPO='AlienCodes/literate-enigma'
def api(route):
    return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/'+route]))
def contents(path,ref):
    return api('contents/'+urllib.parse.quote(path,safe='/')+'?ref='+urllib.parse.quote(ref,safe=''))
def blob(path,ref):
    item=contents(path,ref)
    data=(base64.b64decode(item['content']) if item.get('encoding')=='base64'
          else base64.b64decode(api('git/blobs/'+item['sha'])['content']))
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item['sha']
    return data
def main():
    p=argparse.ArgumentParser();p.add_argument('run_id',type=int);p.add_argument('--directory',required=True,type=Path)
    a=p.parse_args();branch=f'codex/public-ci-qc-{a.run_id}'
    commit=api('git/ref/heads/'+branch)['object']['sha']
    prefix=f'public-ci-qc/{a.run_id}'
    raw=blob(prefix+'/manifest.json',commit);manifest=json.loads(raw)
    assert manifest['run_id']==a.run_id and manifest['private_cache_GT_model_exports'] is False
    assert manifest['kind']=='public-observation-only-not-quality-acceptance'
    a.directory.mkdir(parents=True,exist_ok=True)
    (a.directory/'manifest.json').write_bytes(raw)
    received=[]
    for art in manifest['artifacts']:
        for spec in art.get('files',[]):
            name=Path(spec['path']).name
            assert spec['path']==prefix+'/'+name and Path(name).suffix in ['.json','.mp4','.wav']
            data=blob(spec['path'],commit)
            assert len(data)==spec['bytes'] and hashlib.sha256(data).hexdigest()==spec['sha256']
            (a.directory/name).write_bytes(data)
            received.append({'file':name,'bytes':len(data),'sha256':spec['sha256']})
    receipt={'repository':REPO,'branch':branch,'commit':commit,'run_id':a.run_id,
             'files':received,'acceptance':False}
    (a.directory/'retrieval-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'files':len(received),'bytes':sum(r['bytes'] for r in received),'acceptance':False}))
if __name__=='__main__':main()
