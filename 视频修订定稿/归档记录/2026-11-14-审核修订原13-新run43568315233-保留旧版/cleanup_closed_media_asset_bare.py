"""Delete only an own bare after dual blob and full MP4 readback closure."""
from pathlib import Path
import argparse
import datetime
import json
import shutil
import subprocess

B=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work-dir',required=True);a=parser.parse_args()
    w=Path(a.work_dir).resolve();assert w.parent==B and w.name.startswith('run')
    meta=load(w/'prepared-archive.json');stream=load(w/'remote-video-byte-verification.json');proof=load(w/'actual-dual-asset-blob-verification.json')
    assert meta['articles'] and all(r['passed_per_article'] is True for r in meta['articles'])
    assert stream['passed'] is True and len(stream['streams'])==2*len(meta['articles'])
    refs=[]
    for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
        asset=load(w/('assets-'+role+'.json'))
        assert proof['actual_dual_blob_rows']==2*len(asset['files_index'])
        assert any(r['repository']==repo and r['asset_commit']==asset['asset_commit'] and r['record_subtree']==asset['video_tree_sha'] for r in proof['archives'])
        head=subprocess.check_output(['gh','api','repos/'+repo+'/git/ref/heads/'+asset['asset_branch'],'--jq','.object.sha'],text=True).strip()
        assert head==asset['asset_commit']
        for article in meta['articles']:
            matches=[r for r in stream['streams'] if r['repository']==repo and r['source_id']==article['source_id']];assert len(matches)==1
            row=matches[0];assert row['passed'] is True and row['http_status']==200 and row['sha256']==article['sha256'] and row['bytes']==article['bytes'] and row['pinned_asset_commit']==head
        refs.append({'repository':repo,'asset_commit':head,'video_subtree':asset['video_tree_sha']})
    assert len({r['asset_commit'] for r in refs})==1
    bare=w/'assets.git';assert bare.is_dir() and bare.parent==w
    test=subprocess.run(['git','--git-dir='+str(bare),'fsck','--full','--no-reflogs'],text=True,capture_output=True);assert test.returncode==0
    size=sum(p.stat().st_size for p in bare.rglob('*') if p.is_file());shutil.rmtree(bare)
    receipt={'kind':'full-dual-verified-media-asset-closed-own-bare-only-cleanup','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_dual_blob_rows':proof['actual_dual_blob_rows'],'actual_full_public_MP4_HTTP200_SHA256_streams':len(stream['streams']),'remote_asset_refs':refs,'only_deleted':str(bare),'logical_bytes_removed':size,'git_fsck_exit_code':test.returncode,'git_fsck_output':test.stdout+test.stderr,'all_payload_native_media_rawZIP_sources_QA_GENMD_retained':True,'canonical_or_review_release_modified':False}
    (w/'closed-dual-asset-own-bare-cleanup-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
