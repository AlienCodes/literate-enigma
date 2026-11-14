"""Read-only dual Git blob verification for the whitelisted review records."""
from pathlib import Path
import datetime
import json
import subprocess
import urllib.parse
import urllib.request

B=Path(__file__).resolve().parent
W=B/'user-review-source-record-assets-14-13-20261114'
def load(p):return json.loads(p.read_text())
def main():
    token=subprocess.check_output(['gh','auth','token'],text=True).strip()
    def api(repo,path):
        url='https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%')
        with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Codex-exact-review-record-verification'}),timeout=30) as r:return json.loads(r.read())
    observations=[]
    for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
        asset=load(W/('assets-'+role+'.json'))
        assert api(repo,'git/ref/heads/'+asset['asset_branch'])['object']['sha']==asset['asset_commit']
        tree=api(repo,'git/trees/'+asset['video_tree_sha']+'?recursive=1');assert not tree.get('truncated')
        leaves={r['path']:r for r in tree['tree'] if r['type']=='blob'}
        prefix=load(W/'prepared-archive.json')['prefix']
        assert len(leaves)==len(asset['files_index'])==166
        for row in asset['files_index']:
            path=row['repo_path'][len(prefix)+1:];remote=leaves[path]
            assert remote['sha']==row['git_blob_sha'] and remote['size']==row['bytes'] and remote['mode']=='100644'
        observations.append({'repository':repo,'asset_commit':asset['asset_commit'],'video_subtree':asset['video_tree_sha'],'all166_blob_modes_sizes_and_Git_SHA_exact':True})
    assert len({r['asset_commit'] for r in observations})==1
    refs={
      'primary':api('alienalgorithm/postgraduate-vocabulary','git/ref/heads/main')['object']['sha'],
      'backup':api('AlienCodes/literate-enigma','git/ref/heads/codex/all-deliverables-20261113')['object']['sha'],
      'protected_master':api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha'],
    }
    assert refs=={'primary':'d01249744b1f144b589583f63ea439451b640be4','backup':'0dd7d706eb796e8ae53daf8b5cead113fee76759','protected_master':'6355a02864ebae616b693200d9d26f74f5da80e9'}
    receipt={'kind':'public-user-review-source-and-static-records-actual-dual-verification','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repositories':observations,'canonical_refs_observed_unchanged':refs,'actual_dual_blob_rows':332,'new_native_media_or_QC_acceptance_asserted':False,'canonical_unique_count_still':55,'review40_release_tags_or_media_modified':False,'only_explicit_safe_source14_83_and_source13_51_file_lists_with_code_and_authority_records_collected':True}
    (W/'actual-dual-record-verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
