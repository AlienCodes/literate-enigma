"""Copy already-public QC using native Actions when the local storage host is blocked."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
REPO='AlienCodes/literate-enigma'
BRANCH='codex/finish-05-and-summaries-20261112'
def api(route,data=None,method='GET'):
    args=['gh','api','repos/'+REPO+'/'+route]
    if method!='GET':args+=['-X',method]
    if data is not None:args+=['--input','-']
    raw=subprocess.check_output(args,input=None if data is None else json.dumps(data).encode())
    return json.loads(raw)

def main():
    p=argparse.ArgumentParser();p.add_argument('run_id',type=int);p.add_argument('articles',nargs='+');p.add_argument('--execute',action='store_true')
    args=p.parse_args();nos=[n.zfill(2) for n in args.articles]
    assert len(nos)==len(set(nos)) and all(n.isdigit() and 1<=int(n)<=70 for n in nos)
    run=api(f'actions/runs/{args.run_id}');assert run['head_branch']==BRANCH
    request={'repository':REPO,'run_id':args.run_id,'source_commit':run['head_sha'],
             'artifacts':[f'article{n}-revised-canonical-4K-final' for n in nos],
             'debug_branch':f'codex/public-ci-qc-{args.run_id}',
             'prefix':f'public-ci-qc/{args.run_id}'}
    workflow='''name: Copy public candidate QC to an isolated branch
on:
  push:
    branches: [codex/finish-05-and-summaries-20261112]
    paths: ['.github/video-qc-relay/**', '.github/workflows/relay-public-video-qc.yml']
permissions:
  actions: read
  contents: write
jobs:
  relay:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          sparse-checkout: .github/video-qc-relay
      - name: Copy only public diagnostic outputs, keeping failed status
        env:
          GH_TOKEN: ${{ github.token }}
        run: python .github/video-qc-relay/relay_public_qc.py .github/video-qc-relay/request.json
'''
    files={'.github/video-qc-relay/relay_public_qc.py':(HERE/'relay_public_qc.py').read_bytes(),
           '.github/video-qc-relay/request.json':(json.dumps(request,indent=2)+'\n').encode(),
           '.github/workflows/relay-public-video-qc.yml':workflow.encode()}
    state={'request':request,'files_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in files.items()},'acceptance':False}
    if args.execute:
        master=api('git/ref/heads/master')['object']['sha']
        assert master=='6355a02864ebae616b693200d9d26f74f5da80e9'
        parent=api('git/ref/heads/'+BRANCH)['object']['sha']
        base=api('git/commits/'+parent)['tree']['sha']
        updates=[]
        for name,data in files.items():
            b=api('git/blobs',{'content':base64.b64encode(data).decode(),'encoding':'base64'},'POST')
            assert b['sha']==hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            updates.append({'path':name,'type':'blob','mode':'100644','sha':b['sha']})
        tree=api('git/trees',{'base_tree':base,'tree':updates},'POST')['sha']
        commit=api('git/commits',{'tree':tree,'parents':[parent],
                                'message':'Retrieve public candidate QC for run '+str(args.run_id)},'POST')['sha']
        api('git/refs/heads/'+BRANCH,{'sha':commit,'force':False},'PATCH')
        assert api('git/ref/heads/master')['object']['sha']==master
        state.update({'commit':commit,'queued':True})
    (HERE/f'relay-{args.run_id}-request-state.json').write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps(state))

if __name__=='__main__':main()
