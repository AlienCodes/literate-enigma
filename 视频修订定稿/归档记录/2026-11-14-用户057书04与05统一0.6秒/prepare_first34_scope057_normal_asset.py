"""Prepare one actual first34 normal18 archive; no media production or QC changes."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,sys,uuid
import archive_revision_policy as revision
from archive_batch import load,write,digest
B=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--handoff',required=True);p.add_argument('--handoff-sha',required=True);p.add_argument('--base-work-dir',required=True);p.add_argument('--work-dir',required=True);a=p.parse_args()
    hp=Path(a.handoff);assert digest(hp)==a.handoff_sha;h=load(hp);item=h['articles'][0];sid=item['source_id'];nid=item['new_id'];assert revision.scope057.EXPECTED.get(nid)==sid
    baseline=load(B/'first34-uniform06-057-scope-20261114/primary-current-inventory-frozen.local.json');old=next(r for r in baseline['articles'] if r['source_id']==sid)
    base=Path(a.base_work_dir);bm=load(base/'prepared-archive.json');assert len(bm['articles'])==1 and bm['articles'][0]['source_id']==sid, 'Do not read/copy other articles from a shared archived batch'
    assert load(base/'assets-primary.json')['asset_commit']==load(base/'assets-backup.json')['asset_commit']==old['asset_commit']
    assert h['source_run']==old['source_run'] and h['status']=='passed_actual_normal18_post_only_for_permanent_archive' and h['kind']=='authorized-normal18-local-tail-derivative'
    assert any(r.get('sha256')==revision.scope057.USER_SHA for r in item['section']['evidence'])
    w=Path(a.work_dir);assert w.parent==B and not w.exists();w.mkdir();ram=Path('/dev/shm')/('codex-public-approved-asset-payload-user057-'+sid+'-'+uuid.uuid4().hex);ram.mkdir();(w/'payload').symlink_to(ram,target_is_directory=True)
    physical=[]
    for r in [item['section']['illustration'],item['section']['illustration']['native_source']]:
        physical.append({k:r[k] for k in ['path','bytes','sha256']})
    manifest=w/'archivist-explicit-declared-source-index.json';write(manifest,{'kind':'archivist-source-index-from-exact-frozen-handoff-not-a-fabricated-producer-manifest','actual_handoff_sha256':a.handoff_sha,'files':physical,'no_new_media_or_quality_claim':True})
    subprocess.run([sys.executable,str(B/'prepare_normal_hold18_postonly_assets.py'),'--handoff',str(hp),'--expected-handoff-sha256',a.handoff_sha,'--base-work-dir',str(base),'--work-dir',str(w),'--explicit-public-manifest',str(manifest),'--explicit-public-manifest-sha256',digest(manifest)],check=True,capture_output=True,text=True)
    m=load(w/'prepared-archive.json');r=m['articles'][0];record=load(item['validated_record']);r.update(current_uniform_timing_authorized_by_user057=True,actual_end_reading_pause_seconds=record['tail']['voice_to_illustration_gap_seconds'])
    authority=load(B/'user057-reuse-tu29-archive-authorization.json');user=authority['user057_record'];authority['authorized_revisions']=[{'source_id':sid,'new_id':nid,'previous_row':old,'previous_row_sha256':revision.identity(old),'review_record':user,'actual_scope057_handoff':{'path':str(hp),'bytes':hp.stat().st_size,'sha256':a.handoff_sha}}]
    auth=w/'user057-specific-archive-authorization.json';write(auth,authority);permit=revision.authorization(auth);revision.scope057.check_revision(old,r,authority['authorized_revisions'][0],permit)
    target=w/'payload'/m['prefix'];write(target/'archive-manifest.json',m);write(w/'prepared-archive.json',m)
    for src in [Path(__file__),B/'first34_scope057_archive_policy.py',Path(user['path']),auth]:
        dest=target/'用户057范围与归档程序'/src.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(src.read_bytes())
    index=[{'repo_path':str(p.relative_to(w/'payload')),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted((w/'payload').rglob('*')) if p.is_file()];write(w/'payload-file-index.json',index)
    write(w/'owned-payload-RAM-location.json',{'owned_payload':str(ram),'only_source_id':sid,'no_book35plus_media_or_body_opened':True,'all_PDF_work_paused':True})
    print(json.dumps({'source_id':sid,'new_id':nid,'files':len(index),'logical_bytes':sum(r['bytes'] for r in index),'work_dir':str(w),'no_quality_program_or_media_changed':True},ensure_ascii=False))
if __name__=='__main__':main()
