"""Verify already accepted media archive Git objects; never run quality gates."""
from pathlib import Path
import argparse
import datetime
import json
import subprocess
import urllib.parse
import urllib.request

B=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work-dir',required=True);parser.add_argument('--expected-files',required=True,type=int);a=parser.parse_args()
    w=Path(a.work_dir).resolve();assert w.parent==B
    meta=json.loads((w/'prepared-archive.json').read_text());assert meta['articles'] and all(r['passed_per_article'] is True for r in meta['articles'])
    token=subprocess.check_output(['gh','auth','token'],text=True).strip()
    def api(repo,path):
        url='https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%')
        with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Codex-exact-passed-media-Git-verification'}),timeout=30) as r:return json.loads(r.read())
    rows=[]
    for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
        asset=json.loads((w/('assets-'+role+'.json')).read_text())
        assert api(repo,'git/ref/heads/'+asset['asset_branch'])['object']['sha']==asset['asset_commit']
        tree=api(repo,'git/trees/'+asset['video_tree_sha']+'?recursive=1');assert not tree.get('truncated')
        leaves={r['path']:r for r in tree['tree'] if r['type']=='blob'}
        assert len(leaves)==len(asset['files_index'])==a.expected_files
        for item in asset['files_index']:
            remote=leaves[item['repo_path'][len(meta['prefix'])+1:]]
            assert remote['sha']==item['git_blob_sha'] and remote['size']==item['bytes'] and remote['mode']=='100644'
        rows.append({'repository':repo,'asset_commit':asset['asset_commit'],'record_subtree':asset['video_tree_sha'],'files':a.expected_files,'all_remote_Git_blob_modes_sizes_SHA_exact':True})
    assert len({r['asset_commit'] for r in rows})==len({r['record_subtree'] for r in rows})==1
    receipt={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'actual-dual-Git-asset-verification-of-already-passed-revision','source_ids':[r['source_id'] for r in meta['articles']],'archives':rows,'actual_dual_blob_rows':2*a.expected_files,'new_unique_article_count_claimed':False,'original_media_or_quality_program_changed':False,'old_assets_or_published_review_release_modified':False}
    (w/'actual-dual-asset-blob-verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
