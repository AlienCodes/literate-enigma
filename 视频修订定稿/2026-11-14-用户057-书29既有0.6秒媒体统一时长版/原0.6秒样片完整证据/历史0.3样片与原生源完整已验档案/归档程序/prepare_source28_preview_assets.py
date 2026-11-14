"""Archive the actually validated user032 preview, never a normal final handoff.

This collector preserves every supplied flag and source file unchanged. It does
not call revision-policy, cumulative indexing, final aliases or production QC.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
from archive_batch import digest, now, load, write

B=Path(__file__).resolve().parent
FLAGS={'preview_only':True,'production_delivery_eligible':False,'final_user_acceptance':False,'normal70_final_assembly_eligible':False}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--handoff',required=True);parser.add_argument('--expected-handoff-sha256',required=True);parser.add_argument('--work-dir',required=True);a=parser.parse_args()
    hp=Path(a.handoff).resolve();assert hp.name=='preview-handoff.json' and digest(hp)==a.expected_handoff_sha256
    h=load(hp);assert h['kind']=='source28-book29-hold9-user-review-preview' and h['status']=='passed_actual_native_preview28_for_user_review_only'
    assert all(h.get(k) is v for k,v in FLAGS.items())
    assert len(h['articles'])==1;item=h['articles'][0];assert item['source_id']=='28' and item['new_id']=='29' and item['preview_passed'] is True and item['passed_per_article'] is False
    authority=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-032.json');assert digest(authority)=='74f3c5f1c9e9dc8c3f44d68533b0731e819709170fe6fb25d24eb3ceee8b5029'
    review=load(authority);assert review['execution_state']['single_article_4k_preview_generation_authorized_now'] is True and review['execution_state']['replace_existing_active_book29_final_now'] is False
    assert review['required_scope']['at_30fps_hold_frames']==9 and review['required_scope']['last_body_page_after_final_spoken_sentence_seconds']==0.3
    w=Path(a.work_dir).resolve();assert w.parent==B and w.name.startswith('run');pay=w/'payload';prefix=Path('审核样片')/f"2026-11-14-书29屠呦呦-末页增加0.3秒仅效果预览-run{h['source_run']}"
    report=load(h['report_path']);book=load(h['global_approved_evidence']['book_illustrations']['path']);catalog={r['source_id']:r for r in book['illustrations']};b=catalog['28'];assert b['new_id']=='29'
    source_input=load(h['input_path']);input_item=next(r for r in source_input['articles'] if r['id']=='28');bindings=[]
    def add(src,rel,size=None,sha=None):
        src=Path(src);raw_sha=digest(src);assert size is None or src.stat().st_size==size;assert sha is None or raw_sha==sha
        target=pay/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert digest(target)==raw_sha
        elif src.suffix.lower() in ['.mp4','.png','.jpg','.zip']:os.link(src,target)
        else:shutil.copyfile(src,target)
        bindings.append({'repo_path':str(rel),'bytes':src.stat().st_size,'sha256':raw_sha})
    def spec(row,rel):add(row['path'],rel,row['bytes'],row['sha256'])
    for row in h['validation_files']:
        rel=row.get('relative_validation_path',row.get('validation_relative_path'));assert rel;spec(row,prefix/'真实预览验收原件'/rel)
    add(hp,prefix/'真实预览验收原件/preview-handoff.json');add(authority,prefix/'用户仅预览授权/032.json')
    codes=Path(h['code_snapshot_path'])
    for name,sha in h['tool_source_sha256'].items():add(codes/name,prefix/'实际预览核验程序'/name,sha=sha)
    add(codes/'snapshot-manifest.json',prefix/'实际预览核验程序/snapshot-manifest.json')
    for row in h['global_approved_evidence'].values():spec(row,prefix/'实际批准依据'/Path(row['path']).name)
    evidence=[]
    for number,row in enumerate(input_item.get('evidence',[]),1):
        source=Path(row['path']);assert source.suffix.lower() in ['.json','.py','.sh','.md','.txt','.log','.csv','.diff','.patch','.yml','.yaml','.png','.jpg','.mp4','.zip'],'No private PCM/GT/model/cache objects permitted'
        rel=prefix/'逐项实际输入证据'/f'{number:02d}-{source.name}';spec(row,rel);evidence.append({**row,'repo_path':str(rel)})
    if evidence:write(pay/prefix/'逐项实际输入证据/original-evidence-bindings.json',{'individual_explicit_files_only_no_recursive_cache':True,'files':evidence})
    stem=f"29 {b['title_zh']}（仅效果预览-未替换最终）";spec(item['preview_mp4'],prefix/'视频'/(stem+'.mp4'));spec(item['canonical_source_mp4'],prefix/'实际官方底片'/('28-未插图原底片.mp4'));spec(item['immutable_native_zip'],prefix/'原生Actions产物'/f"source28-run{h['source_run']}-original-preview-output.zip")
    section=item['section']
    for row in section['stills']:spec(row,prefix/'实际解码帧'/Path(row['path']).name)
    spec(section['illustration'],prefix/'实际插图'/'29-4K.png');spec(section['illustration']['native_source'],prefix/'实际插图'/'29-书内批准原图.png')
    native=Path(item['preview_mp4']['path']).parent
    for folder,label in [('files','官方原产物解包'),('artifact-files','官方原始collector解包')]:
        source=native/folder
        if source.is_dir():
            for path in sorted(source.rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix.lower() in ['.json','.py','.md','.txt','.png']:add(path,prefix/label/path.relative_to(source))
    for name in ['28-illustrated-tail-verification.json','illustrated-tail.log','retrieval-receipt.json','actual-boundary-frame-review.json','illustrated-tail-command.json']:
        path=native/name
        if path.exists():add(path,prefix/'原生尾页及取回实证'/name)
    add(Path(__file__),prefix/'归档程序/prepare_source28_preview_assets.py')
    for name in ['user-authorized-source28-preview-only-032.json','PDF-PAUSE-USER-INSTRUCTION-20261114.json']:
        add(B/name,prefix/'范围与不变约束'/name)
    article={'source_id':'28','new_id':'29','title_zh':b['title_zh'],'title_en':b['title_en'],'video_repo_path':str(prefix/'视频'/(stem+'.mp4')),'bytes':item['preview_mp4']['bytes'],'sha256':item['preview_mp4']['sha256'],'source_run':h['source_run'],**FLAGS,'preview_delivery_quality_verified_by_original_handoff':True,'normal_final_delivery_claimed':False,'active_final_replacement_authorized':False,'GEN_origin':section['final_source']['gen'].get('origin'),'MD_origin':section['final_source']['md'].get('origin'),'final_GEN_claimed_as_runtime':False}
    meta={'schema_version':1,'kind':'user032-source28-preview-only-assets-not-final','created_utc':now(),'source_run':h['source_run'],'prefix':str(prefix),'asset_branch':f"codex/review-preview4k-assets-{h['source_run']}-28-hold9",**FLAGS,'articles':[article],'actual_preview_handoff_sha256':a.expected_handoff_sha256,'original_handoff_status_preserved':h['status'],'original_report_path':h['report_path'],'original_report_sha256':digest(h['report_path']),'authoritative_quality_scope':'Only actual dedicated source28 hold9 preview V3; no normal final eligibility inferred','material_source_bindings':bindings,'active_index_aliases_release_tags_or_PDF_modified':False,'release_created':False}
    write(pay/prefix/'preview-archive-manifest.json',meta)
    index=[]
    for path in sorted(pay.rglob('*')):
        if path.is_file():index.append({'repo_path':str(path.relative_to(pay)),'bytes':path.stat().st_size,'sha256':digest(path)})
    write(w/'payload-file-index.json',index);write(w/'prepared-archive.json',meta)
    print(json.dumps({'preview_only':True,'production_delivery_eligible':False,'work_dir':str(w),'prefix':str(prefix),'files':len(index),'logical_bytes':sum(r['bytes'] for r in index),'video':article,'active_index_or_final_directory_changed':False},ensure_ascii=False))

if __name__=='__main__':main()
