"""Materialize only validated current Git-blob aliases; never upload media."""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from build_final_alias_plan import build
from final_alias_git import create_final_tree

B=Path(__file__).resolve().parent
REPOS=[('primary','alienalgorithm/postgraduate-vocabulary','main'),('backup','AlienCodes/literate-enigma','codex/all-deliverables-20261113')]
MASTER='6355a02864ebae616b693200d9d26f74f5da80e9'
def load(p):return json.loads(Path(p).read_text())
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def shallow(rows):return {name:{k:r[k] for k in ['path','mode','type','sha']} for name,r in rows.items()}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');a=parser.parse_args();assert a.execute
    state=load(B/'CURRENT-ARCHIVE-STATE.json');inventory_path=Path(state['actual_inventory']);raw_inventory=inventory_path.read_bytes();inventory=json.loads(raw_inventory)
    assert inventory['archived_passed_count']==state['permanently_archived_count']==58
    authority=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-017.json');assert load(authority)['requirements']['latest_passed_versions_in_stable_final_directory'] is True
    rows={r['source_id']:r for r in inventory['articles']}
    for sid,sha in {'14':'7fda94db377ec5ba4699c04b93aa38d65b52ed06a720396f458a5e5551db31aa','13':'5d4380c4b405b5deec5a756bc17489d34d9e2aced648e256f6be0a505fbc01cd','26':'86867cce1791f3ac6c3913e870d95dedd10a18f1dcd560dcde47e6d56bd5a6f9','61':'ae3a57c5eb3ba32bed99830b52914165600330a5293ab734d2c2cef2c31e1232'}.items():assert rows[sid]['sha256']==sha
    work=B/'final-directory-first58-20261114';work.mkdir(exist_ok=True)
    expected={'primary':state['primary_main'],'backup':state['backup_head']};save(work/'parent-heads-and-inventory.json',{'expected_heads':expected,'inventory_path':str(inventory_path),'inventory_sha256':hashlib.sha256(raw_inventory).hexdigest(),'root017_authority_sha256':hashlib.sha256(authority.read_bytes()).hexdigest(),'only_existing_accepted_Git_blobs':True})
    h=load('/workspace/work/video-revision-delivery/next-passed-validated/43569401028/26/archive-handoff.json');catalog_spec=h['global_approved_evidence']['book_illustrations'];catalog_raw=Path(catalog_spec['path']).read_bytes();assert len(catalog_raw)==catalog_spec['bytes'] and hashlib.sha256(catalog_raw).hexdigest()==catalog_spec['sha256']
    catalog_path=work/'book-illustrations70.frozen.json';catalog_path.write_bytes(catalog_raw);catalog=json.loads(catalog_raw)
    token=subprocess.check_output(['gh','auth','token'],text=True).strip()
    def api(repo,path,method='GET',data=None):
        request=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),method=method,data=None if data is None else json.dumps(data).encode(),headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'Codex-final-validated-Git-alias-materialization'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request,timeout=90) as r:return json.loads(r.read())
            except urllib.error.HTTPError as error:
                body=error.read().decode(errors='replace')
                with (work/'actual-HTTP-observations.jsonl').open('a') as log:log.write(json.dumps({'repository':repo,'method':method,'path':path,'status':error.code,'attempt':attempt+1,'body':body[:2048]})+'\n')
                if error.code in [500,502,503,504] and attempt<3:time.sleep(2**attempt);continue
                raise
    def tree(repo,sha,recursive=False):
        result=api(repo,'git/trees/'+sha+('?recursive=1' if recursive else ''));assert not result.get('truncated');return {r['path']:r for r in result['tree']}
    assert api(REPOS[1][1],'git/ref/heads/master')['object']['sha']==MASTER
    contexts=[]
    for role,repo,branch in REPOS:
        assert api(repo,'git/ref/heads/'+branch)['object']['sha']==expected[role]
        root=tree(repo,api(repo,'git/commits/'+expected[role])['tree']['sha']);video=tree(repo,root['视频修订定稿']['sha']);assert '最终定稿' not in video,'Initial creation must not overwrite an existing directory'
        blob=api(repo,'git/blobs/'+video['已归档视频总清单.json']['sha']);assert base64.b64decode(blob['content'])==raw_inventory
        full=tree(repo,root['视频修订定稿']['sha'],True);contexts.append((role,repo,branch,root,video,full))
    assert contexts[0][3]['视频修订定稿']['sha']==contexts[1][3]['视频修订定稿']['sha']
    plan=build(inventory,contexts[0][5],catalog);save(work/'exact-alias-plan.json',plan)
    prepared=[]
    for role,repo,branch,root,video,full in contexts:
        actual_plan=build(inventory,full,catalog);assert actual_plan==plan
        result=create_final_tree(api,repo,plan);updated=shallow(video);updated['最终定稿']={'path':'最终定稿','mode':'040000','type':'tree','sha':result['final_tree_sha']}
        new_video=api(repo,'git/trees',method='POST',data={'tree':list(updated.values())})['sha'];observed=tree(repo,new_video)
        assert set(observed)==set(video)|{'最终定稿'} and all(observed[name]['sha']==entry['sha'] and observed[name]['mode']==entry['mode'] and observed[name]['type']==entry['type'] for name,entry in video.items())
        roots=shallow(root);roots['视频修订定稿']={'path':'视频修订定稿','mode':'040000','type':'tree','sha':new_video};new_root=api(repo,'git/trees',method='POST',data={'tree':list(roots.values())})['sha']
        commit=api(repo,'git/commits',method='POST',data={'message':'按书序建立58篇已验4K最终定稿目录及逐篇修改记录，原Git视频对象复用；保留全部旧版 [skip ci]','tree':new_root,'parents':[expected[role]]})['sha']
        prepared.append({'role':role,'repository':repo,'branch':branch,'parent':expected[role],'commit':commit,'video_subtree':new_video,'root_tree':new_root,'original_root':root,'final_directory':result})
    assert len({r['video_subtree'] for r in prepared})==len({r['final_directory']['final_tree_sha'] for r in prepared})==1
    save(work/'prepared-graft-commits.json',prepared)
    for row in prepared:assert api(row['repository'],'git/ref/heads/'+row['branch'])['object']['sha']==row['parent']
    receipt={'status':'prepared_final_directory_aliases','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_unique_videos':58,'requested_total':70,'unpassed12_not_included':True,'video_bytes_uploaded':0,'new_media_generation_or_quality_gate_runs':False,'inventory_blob_unchanged':True,'all_old_video_children_and_other_root_children_unchanged':True,'all58_aliases_existing_verified_blobs_only':True,'archives':[]}
    for row in prepared:
        repo=row['repository'];api(repo,'git/refs/heads/'+row['branch'],method='PATCH',data={'sha':row['commit'],'force':False});assert api(repo,'git/ref/heads/'+row['branch'])['object']['sha']==row['commit']
        actual_root=tree(repo,row['root_tree']);assert {n:(r['mode'],r['type'],r['sha']) for n,r in actual_root.items() if n!='视频修订定稿'}=={n:(r['mode'],r['type'],r['sha']) for n,r in row['original_root'].items() if n!='视频修订定稿'}
        actual_video=tree(repo,row['video_subtree']);assert actual_video['最终定稿']['sha']==row['final_directory']['final_tree_sha']
        assert api(REPOS[1][1],'git/ref/heads/master')['object']['sha']==MASTER
        receipt['archives'].append({k:v for k,v in row.items() if k!='original_root'});save(work/'actual-final-directory-receipt.json',receipt)
    receipt['status']='permanent_dual_final_directory_verified';save(work/'actual-final-directory-receipt.json',receipt)
    state=load(B/'CURRENT-ARCHIVE-STATE.json');state.update(primary_main=prepared[0]['commit'],backup_head=prepared[1]['commit'],video_subtree=prepared[0]['video_subtree'],last_final_directory_receipt=str(work/'actual-final-directory-receipt.json'),final_alias_catalog={'path':str(catalog_path),'bytes':len(catalog_raw),'sha256':catalog_spec['sha256']},final_alias_inventory_snapshot=str(inventory_path),final_directory=receipt['archives'][0]['final_directory']);save(B/'CURRENT-ARCHIVE-STATE.json',state)
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
