"""Archive one explicitly authorized existing Tu29 movie using existing Git blobs."""
from pathlib import Path
import argparse,base64,datetime,hashlib,json,subprocess,urllib.error,urllib.parse,urllib.request,uuid
from archive_batch import load,write,digest
B=Path(__file__).resolve().parent
W=B/'user057-reuse-tu29-existing06-assets'
H=Path('/workspace/work/first34-hold06-20261114/reuse-tu29/archive-handoff.json')
P=Path('视频修订定稿/2026-11-14-用户057-书29既有0.6秒媒体统一时长版')
OLD=B/'run43576642418-28-hold18-preview051-v2';SIDE=B/'preview28-hold18-current-metadata-sidecar-20261114'
H_SHA='8aa9ff04e6ae659326d4269334aa870f14ff1e380f1dc0408ebb45d960850fbe'
DENIED={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
def gitsha(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def prepare():
    assert digest(H)==H_SHA;h=load(H);assert h['kind']=='first34-uniform-timing057-existing-qualified-preview-reuse' and h['production_delivery_eligible'] is True and h['preview_only'] is False
    assert h['new_native_job_or_TTS_claimed'] is False and h['new_tail_or_audio_processing_claimed'] is False and h['new_subjective_listening_or_effect_acceptance_claimed'] is False and h['final_user_acceptance'] is False
    item=h['articles'][0];assert item['source_id']=='28' and item['new_id']=='29' and item['passed_per_article'] is True
    assert item['final_mp4']['sha256']=='1e1685c5b0eff4ebb2d3e8bab3f368336ea31a313b38c10a0ef0f7a1ae365163' and item['final_mp4']['bytes']==17473089
    assert not W.exists();W.mkdir();ram=Path('/dev/shm')/('codex-public-approved-small-record-payload-'+uuid.uuid4().hex);ram.mkdir();(W/'payload').symlink_to(ram,target_is_directory=True)
    known={};files={};inherited=[]
    for work,label in [(OLD,'原0.6秒样片完整证据'),(SIDE,'原样片最新引用元数据旁证')]:
        a=load(work/'assets-primary.json');k=load(work/'assets-backup.json');m=load(work/'prepared-archive.json');assert a['asset_commit']==k['asset_commit'] and a['video_tree_sha']==k['video_tree_sha']
        inherited.append({'label':label,'asset_commit':a['asset_commit'],'video_tree_sha':a['video_tree_sha'],'source_prefix':m['prefix']})
        for f in a['files_index']:
            known.setdefault((f['bytes'],f['sha256']),f)
            rel=P/label/Path(f['repo_path']).relative_to(m['prefix']);files[str(rel)]={**f,'repo_path':str(rel),'storage_origin':'existing_permanent_Git_object'}
    def add(spec,relative):
        assert spec['sha256'] not in DENIED;key=(spec['bytes'],spec['sha256']);rel=P/relative
        if key in known:row={**known[key],'repo_path':str(rel),'storage_origin':'existing_permanent_Git_object'}
        else:
            src=Path(spec['path']);assert src.suffix in {'.json','.py','.log','.md','.yml','.txt'} and src.stat().st_size==spec['bytes'] and digest(src)==spec['sha256']
            raw=src.read_bytes();assert len(raw)<1024*1024;target=W/'payload'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            row={'repo_path':str(rel),'bytes':len(raw),'sha256':spec['sha256'],'git_blob_sha':gitsha(raw),'storage_origin':'new_small_metadata'}
        files[str(rel)]=row
    def local(p,relative):p=Path(p);add({'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)},relative)
    for f in h['validation_files']:
        rel=f.get('relative_validation_path',f.get('validation_relative_path'));assert rel and not Path(rel).is_absolute() and '..' not in Path(rel).parts;add(f,Path('057用途实际完整核验')/rel)
    local(H,Path('057用途实际完整核验/archive-handoff.json'))
    for f in h['global_approved_evidence'].values():add(f,Path('既有批准依据')/Path(f['path']).name)
    video=P/'视频/29 青蒿一握，济世千万.mp4';add(item['final_mp4'],video.relative_to(P));add(item['canonical_source_mp4'],Path('原准确canonical底片')/Path(item['canonical_source_mp4']['path']).name);add(item['immutable_native_zip'],Path('真实原生来源ZIP')/Path(item['immutable_native_zip']['path']).name)
    local(Path(__file__),Path('归档程序')/Path(__file__).name);local(B/'first34_scope057_archive_policy.py',Path('归档程序/first34_scope057_archive_policy.py'))
    rec=load(item['validated_record']);assert rec['tail']['extra_body_hold_frames']==18 and rec['tail']['voice_to_illustration_gap_seconds']>=0.6
    row={'source_id':'28','new_id':'29','title_zh':'青蒿一握，济世千万','title_en':'A Handful of Wormwood That Saved Millions','video_repo_path':str(video),'bytes':17473089,'sha256':item['final_mp4']['sha256'],'passed_per_article':True,'source_run':43576642418,'production_delivery_eligible':True,'preview_only':False,'final_user_acceptance':False,'subjective_listening_or_effect_acceptance_claimed':False,'current_uniform_timing_authorized_by_user057':True,'media_origin':'existing_qualified_preview06_reused_as_explicit_user057_uniform_timing_edition','reused_existing_preview_asset_commit':'dd7a3d7badbdcae587f11522f69c0ebaef21853f','new_native_Actions_run_claimed':False,'actual_runtime_GEN_or_voice_rerun_claimed':False,'new_tail_or_audio_processing_claimed':False,'local_postprocessing_only':True,'post_reading_pause_seconds':0.6,'nominal_extra_hold_frames_at_30fps':18,'actual_end_reading_pause_seconds':rec['tail']['voice_to_illustration_gap_seconds'],'postprocessing_full_V3_handoff_sha256':H_SHA,'GEN_origin':item['section']['final_source']['gen'].get('origin'),'MD_origin':item['section']['final_source']['md'].get('origin'),'final_GEN_claimed_as_runtime':False,'canonical_audio_basis':'exact_existing_qualified_preview_media_reused_with_original_full_V3_and_user057_purpose_authority'}
    meta={'kind':'user057-existing-qualified-Tu29-Git-object-reuse-archive','prefix':str(P),'asset_branch':'codex/user057-book29-existing06-timing-assets','articles':[row],'source_run':43576642418,'original_handoff_status':h['status'],'original_handoff_kind':h['kind'],'actual_handoff_sha256':H_SHA,'inherited_frozen_subtrees':inherited,'created_utc':datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),'not_a_new_native_or_new_TTS_or_media_processing_job':True,'all_PDF_work_paused':True}
    manifest=W/'payload'/P/'archive-manifest.json';write(manifest,meta);local(manifest,Path('archive-manifest.json'));write(W/'prepared-archive.json',meta);write(W/'payload-file-index.json',list(files.values()));print(json.dumps({'files':len(files),'new_metadata_files':sum(f['storage_origin']=='new_small_metadata' for f in files.values()),'copied_or_uploaded_media':False,'work_dir':str(W)},ensure_ascii=False))
def push(repo):
    m=load(W/'prepared-archive.json');files=load(W/'payload-file-index.json');token=subprocess.check_output(['gh','auth','token'],text=True).strip()
    def api(path,method='GET',data=None):
        req=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),method=method,data=None if data is None else json.dumps(data).encode(),headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=45) as r:return json.loads(r.read())
    for base in m['inherited_frozen_subtrees']:
        actual=api('git/commits/'+base['asset_commit']);assert actual['sha']==base['asset_commit'];assert api('git/trees/'+base['video_tree_sha'])['sha']==base['video_tree_sha']
    for f in files:
        if f['storage_origin']!='new_small_metadata':continue
        p=W/'payload'/f['repo_path'];assert p.stat().st_size==f['bytes'] and digest(p)==f['sha256'];raw=p.read_bytes();assert gitsha(raw)==f['git_blob_sha'];assert api('git/blobs','POST',{'content':base64.b64encode(raw).decode(),'encoding':'base64'})['sha']==f['git_blob_sha']
    node={}
    for base in m['inherited_frozen_subtrees']:node[base['label']]={'opaque_tree':base['video_tree_sha']}
    for f in files:
        relative=Path(f['repo_path']).relative_to(m['prefix']);parts=relative.parts
        if parts[0] in {b['label'] for b in m['inherited_frozen_subtrees']}:continue
        cur=node
        for part in parts[:-1]:cur=cur.setdefault(part,{})
        cur[parts[-1]]={'blob':f['git_blob_sha']}
    def tree(n):
        entries=[]
        for name,child in sorted(n.items()):
            if 'blob' in child:entries.append({'path':name,'mode':'100644','type':'blob','sha':child['blob']})
            else:entries.append({'path':name,'mode':'040000','type':'tree','sha':child.get('opaque_tree') or tree(child)})
        return api('git/trees','POST',{'tree':entries})['sha']
    subtree=tree(node);root=subtree
    for part in reversed(P.parts):root=api('git/trees','POST',{'tree':[{'path':part,'mode':'040000','type':'tree','sha':root}]})['sha']
    author={'name':'Codex','email':'codex@users.noreply.github.com','date':m['created_utc']};commit=api('git/commits','POST',{'tree':root,'parents':['dd7a3d7badbdcae587f11522f69c0ebaef21853f'],'message':'按用户057复用书29已验0.6秒原片与原证据，保留预览历史 [skip ci]','author':author,'committer':author})['sha']
    previous=W/'asset-local.json'
    if previous.exists():assert load(previous)['asset_commit']==commit
    ref='heads/'+m['asset_branch']
    try:assert api('git/ref/'+ref)['object']['sha']==commit
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
        assert api('git/refs','POST',{'ref':'refs/'+ref,'sha':commit})['object']['sha']==commit
    assert api('git/ref/'+ref)['object']['sha']==commit
    base={'asset_commit':commit,'commits':[commit],'asset_branch':m['asset_branch'],'root_tree':root};write(previous,base);out={**base,'repository':repo,'video_tree_sha':subtree,'files':len(files),'files_index':files,'remote_asset_ref_verified':True,'main_or_master_changed':False,'existing_media_Git_objects_reused_without_upload':True};write(W/('assets-primary.json' if repo.startswith('alienalgorithm/') else 'assets-backup.json'),out);print(json.dumps({k:v for k,v in out.items() if k!='files_index'},ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','push']);p.add_argument('--repo');a=p.parse_args();prepare() if a.action=='prepare' else push(a.repo)
