"""Actual dual verification and optional cleanup of own closed small-record bare."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import urllib.parse
import urllib.request

B=Path(__file__).resolve().parent
ALLOWED={'user-review-source-record-assets-14-13-20261114','user-review-source-record-assets-27-20261114','book24-26-publication-record-assets-20261114','reviewed-book21-23-publication-record-assets-20261114','final-directory-first58-record-assets-20261114','children-language-publication-record-assets-20261114','preview28-closure-record-assets-20261114','titanic-publication-record-assets-20261114'}
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work-dir',required=True);parser.add_argument('--expected-files',required=True,type=int);parser.add_argument('--cleanup-own-closed-bare',action='store_true');a=parser.parse_args()
    w=Path(a.work_dir).resolve();assert w.parent==B and w.name in ALLOWED
    m=load(w/'prepared-archive.json');assert not m.get('articles')
    token=subprocess.check_output(['gh','auth','token'],text=True).strip()
    def api(repo,path):
        url='https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%')
        with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Codex-public-records-dual-blob-check'}),timeout=30) as r:return json.loads(r.read())
    observations=[]
    for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
        asset=load(w/('assets-'+role+'.json'))
        assert api(repo,'git/ref/heads/'+asset['asset_branch'])['object']['sha']==asset['asset_commit']
        tree=api(repo,'git/trees/'+asset['video_tree_sha']+'?recursive=1');assert not tree.get('truncated')
        leaves={r['path']:r for r in tree['tree'] if r['type']=='blob'}
        assert len(leaves)==len(asset['files_index'])==a.expected_files
        for row in asset['files_index']:
            relative=row['repo_path'][len(m['prefix'])+1:];remote=leaves[relative]
            local=w/'payload'/row['repo_path'];assert local.suffix.lower() not in ['.mp4','.wav','.pkl','.npy','.npz']
            raw=local.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
            gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            assert remote['sha']==row['git_blob_sha']==gitsha and remote['size']==row['bytes'] and remote['mode']=='100644'
        observations.append({'repository':repo,'asset_commit':asset['asset_commit'],'asset_branch':asset['asset_branch'],'record_subtree':asset['video_tree_sha'],'file_count':a.expected_files,'all_local_SHA256_and_remote_Git_SHA_sizes_modes_exact':True})
    assert len({r['asset_commit'] for r in observations})==1
    receipt={'kind':'actual-dual-small-record-asset-closure','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archives':observations,'actual_dual_blob_rows':2*a.expected_files,'new_media_or_video_quality_acceptance_claimed':False,'canonical_refs_release_or_tags_modified':False}
    save(w/'actual-dual-small-record-verification.json',receipt)
    if a.cleanup_own_closed_bare:
        p=w/'assets.git';assert p.is_dir() and p.parent==w
        check=subprocess.run(['git','--git-dir='+str(p),'fsck','--full','--no-reflogs'],text=True,capture_output=True);assert check.returncode==0
        size=sum(q.stat().st_size for q in p.rglob('*') if q.is_file());shutil.rmtree(p)
        save(w/'closed-own-record-bare-cleanup-receipt.json',{'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'only_deleted':str(p),'logical_bytes_removed':size,'actual_dual_blob_rows_previously_verified':2*a.expected_files,'git_fsck_exit_code':check.returncode,'git_fsck_output':check.stdout+check.stderr,'all_original_payload_images_sources_metadata_and_zip_kept':True,'canonical_refs_release_or_tags_modified':False})
        receipt['own_closed_bare_only_bytes_removed']=size
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
