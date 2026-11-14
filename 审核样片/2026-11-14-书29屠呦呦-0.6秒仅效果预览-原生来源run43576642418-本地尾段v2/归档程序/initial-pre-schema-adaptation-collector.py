"""Preserve actual user051 preview V3 and honest local-postprocess lineage.

This is an archive collector, not a new media/quality producer. It never writes
the cumulative final inventory, final aliases, publication tags or PDF files.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
from archive_batch import digest, load, now, write

B=Path(__file__).resolve().parent
FLAGS={'preview_only':True,'production_delivery_eligible':False,'final_user_acceptance':False,'normal70_final_assembly_eligible':False}
MP4_SHA='1e1685c5b0eff4ebb2d3e8bab3f368336ea31a313b38c10a0ef0f7a1ae365163'
SAFE={'.json','.py','.sh','.md','.txt','.log','.csv','.diff','.patch','.yml','.yaml','.png','.jpg','.mp4','.zip'}
OLD=B/'run43576642418-28-hold9-preview032'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--handoff',required=True);ap.add_argument('--expected-handoff-sha256',required=True);ap.add_argument('--expected-kind',required=True);ap.add_argument('--expected-status',required=True);ap.add_argument('--work-dir',required=True);a=ap.parse_args()
    hp=Path(a.handoff).resolve();assert hp.name=='preview-handoff.json' and digest(hp)==a.expected_handoff_sha256
    h=load(hp);assert h['kind']==a.expected_kind and h['status']==a.expected_status and h['status'].startswith('passed_')
    assert h['kind']!='source28-book29-hold9-user-review-preview' and all(h.get(k) is v for k,v in FLAGS.items())
    assert h['source_run']==43576642418 and len(h['articles'])==1
    item=h['articles'][0];assert item['source_id']=='28' and item['new_id']=='29' and item['preview_passed'] is True and item['passed_per_article'] is False
    media=item['preview_mp4'];assert media['bytes']==17473089 and media['sha256']==MP4_SHA
    authority=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-051.json');assert digest(authority)=='4bcae46b68b9584f107966f683af580b474fa9835f101834fe55ed6968dfc36b'
    user=load(authority);assert user['required_behavior']['nominal_extra_hold_frames']==18 and user['required_behavior']['pause_seconds']==0.6 and user['execution_state']['Tu_Youyou_effect_final_acceptance_still_pending'] is True
    w=Path(a.work_dir).resolve();assert w.parent==B and w.name=='run43576642418-28-hold18-preview051-v2'
    pay=w/'payload';prefix=Path('审核样片/2026-11-14-书29屠呦呦-0.6秒仅效果预览-原生来源run43576642418-本地尾段v2');bindings=[]
    def add(source,relative,size=None,sha=None):
        source=Path(source);assert source.suffix.lower() in SAFE and '__pycache__' not in source.parts
        actual=digest(source);assert size is None or source.stat().st_size==size;assert sha is None or actual==sha
        target=pay/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert digest(target)==actual
        elif source.suffix.lower() in {'.mp4','.zip','.png','.jpg'}:os.link(source,target)
        else:shutil.copyfile(source,target)
        bindings.append({'original_path':str(source),'repo_path':str(relative),'bytes':source.stat().st_size,'sha256':actual})
    def spec(row,relative):add(row['path'],relative,row['bytes'],row['sha256'])
    old=load(OLD/'prepared-archive.json');old_prefix=Path(old['prefix']);old_primary=load(OLD/'assets-primary.json');assert old_primary['asset_commit']=='37f26cbd597572fefe0b7c4f15cfd935e05cced7'
    assert load(OLD/'remote-video-byte-verification.json')['passed'] is True
    for row in load(OLD/'payload-file-index.json'):
        relative=Path(row['repo_path']).relative_to(old_prefix)
        add(OLD/'payload'/row['repo_path'],prefix/'历史0.3样片与原生源完整已验档案'/relative,row['bytes'],row['sha256'])
    for row in h['validation_files']:
        rel=row.get('relative_validation_path',row.get('validation_relative_path'));assert rel;spec(row,prefix/'本轮真实完整V3验收'/rel)
    add(hp,prefix/'本轮真实完整V3验收/preview-handoff.json');add(h['report_path'],prefix/'本轮真实完整V3验收/whole-report.json');add(h['input_path'],prefix/'本轮真实完整V3验收/actual-inputs.json')
    codes=Path(h['code_snapshot_path'])
    for name,sha in h['tool_source_sha256'].items():add(codes/name,prefix/'本轮实际V3程序'/name,sha=sha)
    add(codes/'snapshot-manifest.json',prefix/'本轮实际V3程序/snapshot-manifest.json')
    for row in h['global_approved_evidence'].values():spec(row,prefix/'本轮实际批准依据'/Path(row['path']).name)
    inputs=load(h['input_path']);input_article=next(r for r in inputs['articles'] if r['id']=='28')
    for number,row in enumerate(input_article.get('evidence',[]),1):spec(row,prefix/'本轮逐项原输入证据'/f'{number:03d}-{Path(row["path"]).name}')
    physical=Path('/workspace/work/video-audit70-20261113/article28-user-review-20261114/hold18-integrator/safe-public-evidence-manifest.json');assert digest(physical)=='893a5df6a218c63b9585a17fda33594547e7dc5bbc629bdd6134686be39e3363'
    add(physical,prefix/'本轮实际物理处理证据/safe-public-evidence-manifest.json')
    for number,row in enumerate(load(physical)['files'],1):spec(row,prefix/'本轮实际物理处理证据'/f'{number:02d}-{Path(row["path"]).name}')
    video_path=prefix/'视频/29 青蒿一握，济世千万（0.6秒仅效果预览-未替换最终）.mp4';spec(media,video_path)
    spec(item['canonical_source_mp4'],prefix/'本轮准确canonical原件'/Path(item['canonical_source_mp4']['path']).name)
    spec(item['immutable_native_zip'],prefix/'原生来源原ZIP非本次新Actions'/Path(item['immutable_native_zip']['path']).name)
    for row in item['section'].get('stills',[]):spec(row,prefix/'本轮实际解码帧'/Path(row['path']).name)
    add(authority,prefix/'用户051实际授权.json');add(B/'ACTIVE-GLOBAL-POSTREADING-HOLD18-20261114.json',prefix/'最新0.6秒规则及实际授权绑定.json');add(Path(__file__),prefix/'归档程序'/Path(__file__).name)
    article={'source_id':'28','new_id':'29','title_zh':'青蒿一握，济世千万','title_en':'A Handful of Wormwood That Saved Millions','video_repo_path':str(video_path),'bytes':media['bytes'],'sha256':media['sha256'],'source_run':h['source_run'],**FLAGS,'preview_delivery_quality_verified_by_original_handoff':True,'normal_final_delivery_claimed':False,'active_final_replacement_authorized':False,'media_origin':'actual_validated_local_tail_only_postprocess_of_original_native_source','new_native_Actions_run_claimed':False,'actual_runtime_GEN_or_voice_rerun_claimed':False,'original_native_source_and_whole_earlier_QA_preserved':True}
    meta={'kind':'user051-source28-hold18-local-postonly-preview-assets-not-final','created_utc':now(),'prefix':str(prefix),'asset_branch':'codex/review-preview4k-assets-43576642418-28-hold18-v2','source_run':h['source_run'],'articles':[article],**FLAGS,'actual_preview_handoff_sha256':a.expected_handoff_sha256,'original_handoff_kind':h['kind'],'original_handoff_status':h['status'],'original_report_path':h['report_path'],'original_report_sha256':digest(h['report_path']),'material_source_bindings':bindings,'prior_0_3_preview_asset_commit':old_primary['asset_commit'],'old_release_tags_active_final_index_aliases_or_PDF_modified':False,'native_run_created_or_claimed_by_archive':False}
    write(pay/prefix/'preview-archive-manifest.json',meta);write(w/'prepared-archive.json',meta)
    index=[{'repo_path':str(p.relative_to(pay)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(pay.rglob('*')) if p.is_file()];write(w/'payload-file-index.json',index)
    print(json.dumps({'work_dir':str(w),'files':len(index),'logical_bytes':sum(r['bytes'] for r in index),'original_native_source_run_preserved':h['source_run'],'preview_only':True,'new_native_run_claimed':False,'video':article},ensure_ascii=False))

if __name__=='__main__':main()
