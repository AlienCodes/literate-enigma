"""Archive a genuinely validated normal18 derivative without inventing a native run."""
from pathlib import Path
import argparse
import errno
import json
import os
import shutil
from archive_batch import digest, load, now, write

B=Path(__file__).resolve().parent
SAFE={'.json','.py','.sh','.md','.txt','.log','.csv','.diff','.patch','.yml','.yaml','.png','.jpg','.mp4','.zip'}
BINARY={'.png','.jpg','.mp4','.zip'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--handoff',required=True);ap.add_argument('--expected-handoff-sha256',required=True);ap.add_argument('--base-work-dir',required=True);ap.add_argument('--work-dir',required=True);ap.add_argument('--explicit-public-manifest',required=True);ap.add_argument('--explicit-public-manifest-sha256',required=True);a=ap.parse_args()
    hp=Path(a.handoff).resolve();assert digest(hp)==a.expected_handoff_sha256;h=load(hp)
    assert h['status']=='passed_actual_normal18_post_only_for_permanent_archive'
    if h['kind']!='authorized-normal18-local-tail-derivative':
        import existing_final_tail_handoff_compat as exact_kind
        exact_kind.check(h,a.expected_handoff_sha256)
    assert h['local_postprocessing_only'] is True and h['new_native_job_or_TTS_claimed'] is False and h['production_delivery_eligible'] is True and h['preview_only'] is False
    assert len(h['articles'])==1;item=h['articles'][0];assert item['passed_per_article'] is True;sid=item['source_id'];nid=item['new_id']
    w=Path(a.work_dir).resolve();base=Path(a.base_work_dir).resolve();assert w.parent==B and base.parent==B and w!=base
    old=load(base/'prepared-archive.json');old_asset=load(base/'assets-primary.json');assert load(base/'assets-backup.json')['asset_commit']==old_asset['asset_commit'];old_article=next(r for r in old['articles'] if r['source_id']==sid);assert old_article['source_run']==h['source_run']
    authority=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-051.json');assert digest(authority)=='4bcae46b68b9584f107966f683af580b474fa9835f101834fe55ed6968dfc36b';assert load(authority)['required_behavior']['nominal_extra_hold_frames']==18
    prefix=Path('视频修订定稿')/f"2026-11-14-审核原{sid}-0.6秒定稿-原生来源{h['source_run']}-本地尾段v1";pay=w/'payload';bindings=[];stored={}
    def add(source,relative,size=None,sha=None):
        source=Path(source);assert source.suffix.lower() in SAFE and '__pycache__' not in source.parts and not source.name.startswith('CURRENT-ROOT-DELIVERY-STATE')
        actual=digest(source);n=source.stat().st_size;assert size is None or n==size;assert sha is None or actual==sha
        target=pay/relative;target.parent.mkdir(parents=True,exist_ok=True);key=(n,actual)
        if target.exists():assert digest(target)==actual
        elif source.suffix.lower() in BINARY:
            try:os.link(stored.get(key,source),target)
            except OSError as error:
                if error.errno!=errno.EXDEV:raise
                shutil.copyfile(source,target)
        else:shutil.copyfile(source,target)
        if source.suffix.lower() in BINARY:stored[key]=target
        bindings.append({'original_path':str(source),'repo_path':str(relative),'bytes':n,'sha256':actual})
    def spec(row,relative):add(row['path'],relative,row['bytes'],row['sha256'])
    old_prefix=Path(old['prefix'])
    for row in load(base/'payload-file-index.json'):
        relative=Path(row['repo_path']).relative_to(old_prefix);add(base/'payload'/row['repo_path'],prefix/'原生来源与修改后正文原完整V3档案'/relative,row['bytes'],row['sha256'])
    for row in h['validation_files']:
        relative=row.get('relative_validation_path',row.get('validation_relative_path'));assert relative;spec(row,prefix/'本轮实际normal18完整核验'/relative)
    add(hp,prefix/'本轮实际normal18完整核验/archive-handoff.json');add(h['report_path'],prefix/'本轮实际normal18完整核验/whole-report.json');add(h['input_path'],prefix/'本轮实际normal18完整核验/actual-input.json')
    codes=Path(h['code_snapshot_path'])
    for name,sha in h['tool_source_sha256'].items():add(codes/name,prefix/'本轮实际normal18核验程序'/name,sha=sha)
    write(pay/prefix/'本轮实际normal18核验程序/archivist-exact-handoff-code-bindings.json',{'programs_from_original_passed_handoff':h['tool_source_sha256'],'handoff_sha256':a.expected_handoff_sha256,'not_a_fabricated_producer_snapshot_manifest':True})
    for row in h['global_approved_evidence'].values():spec(row,prefix/'本轮实际批准依据'/Path(row['path']).name)
    for number,row in enumerate(h.get('additional_public_media_inputs',[]),1):spec(row,prefix/'实际公开格式中间输入'/f'{number:02d}-{Path(row["path"]).name}')
    manifest=Path(a.explicit_public_manifest).resolve();assert digest(manifest)==a.explicit_public_manifest_sha256;add(manifest,prefix/'显式安全物理来源/safe-public-evidence-manifest.json')
    for number,row in enumerate(load(manifest)['files'],1):
        source=Path(row.get('path',row.get('source_path','')));assert str(source) not in {'','.'};relative=row.get('archive_relative_path',row.get('safe_archive_relative_path',row.get('relative_path',f'{number:03d}-{source.name}')));assert not Path(relative).is_absolute() and '..' not in Path(relative).parts;add(source,prefix/'显式安全物理来源'/relative,row['bytes'],row['sha256'])
    section=item['section']
    for row in section.get('stills',[]):
        assert row['video_sha256']==item['final_mp4']['sha256'];spec(row,prefix/'实际当前成片解码帧'/Path(row['path']).name)
    video_path=prefix/'视频'/f"{nid} {old_article['title_zh']}.mp4";spec(item['final_mp4'],video_path);spec(item['canonical_source_mp4'],prefix/'原准确canonical底片'/Path(item['canonical_source_mp4']['path']).name);spec(item['immutable_native_zip'],prefix/'原生来源原ZIP非新Actions'/Path(item['immutable_native_zip']['path']).name)
    add(authority,prefix/'用户051统一0.6秒实际授权.json');add(Path(__file__),prefix/'归档程序'/Path(__file__).name)
    if h['kind']!='authorized-normal18-local-tail-derivative':add(Path(exact_kind.__file__),prefix/'归档程序'/Path(exact_kind.__file__).name)
    row={'source_id':sid,'new_id':nid,'title_zh':old_article['title_zh'],'title_en':old_article['title_en'],'video_repo_path':str(video_path),'bytes':item['final_mp4']['bytes'],'sha256':item['final_mp4']['sha256'],'passed_per_article':True,'source_run':h['source_run'],'production_delivery_eligible':True,'preview_only':False,'media_origin':'actual_validated_normal18_local_tail_derivative_of_original_native_source','new_native_Actions_run_claimed':False,'actual_runtime_GEN_or_voice_rerun_claimed':False,'GEN_origin':section['final_source']['gen'].get('origin'),'MD_origin':section['final_source']['md'].get('origin'),'final_GEN_claimed_as_runtime':False,'canonical_audio_basis':'inherited_full_V3_canonical_and_actual_postprocessing_AAC_projection_identity','approved_audio_repair_applied':False,'local_postprocessing_only':True,'post_reading_pause_seconds':0.6,'nominal_extra_hold_frames_at_30fps':18,'inherited_full_native_archive_commit':old_asset['asset_commit'],'postprocessing_full_V3_handoff_sha256':a.expected_handoff_sha256}
    meta={'kind':'actual-validated-normal18-postonly-assets','created_utc':now(),'source_run':h['source_run'],'prefix':str(prefix),'asset_branch':f"codex/passed4k-assets-{h['source_run']}-{sid}-hold18-postonly-v1",'articles':[row],'actual_handoff_sha256':a.expected_handoff_sha256,'original_handoff_status':h['status'],'original_handoff_kind':h['kind'],'local_postprocessing_only':True,'new_native_job_or_TTS_claimed':False,'material_source_bindings':bindings,'canonical_active_index_or_alias_updated_by_preparation':False,'release_created':False,'all_PDF_work_paused':True}
    write(pay/prefix/'archive-manifest.json',meta);write(w/'prepared-archive.json',meta);index=[{'repo_path':str(p.relative_to(pay)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(pay.rglob('*')) if p.is_file()];write(w/'payload-file-index.json',index);print(json.dumps({'work_dir':str(w),'files':len(index),'logical_bytes':sum(r['bytes'] for r in index),'article':row,'only_declared_public_media_and_metadata_copied':True},ensure_ascii=False))

if __name__=='__main__':main()
