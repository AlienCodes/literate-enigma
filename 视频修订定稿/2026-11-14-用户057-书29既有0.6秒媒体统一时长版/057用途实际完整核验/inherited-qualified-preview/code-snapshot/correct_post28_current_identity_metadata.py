"""Correct current derived record metadata only; preserve all original QA bytes."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

OUT=Path('/workspace/work/video-revision-delivery/post-only-hold18-validated/28')
def load(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def spec(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}

record_path=OUT/'validated-article-record.json';handoff_path=OUT/'preview-handoff.json'
history=OUT/'history-before-current-probe-metadata-correction';history.mkdir(exist_ok=True)
for p in (record_path,handoff_path):
    target=history/p.name
    if not target.exists():shutil.copyfile(p,target)
r=load(record_path);h=load(handoff_path);report=load(OUT/'report.json')
assert h['articles'][0]['preview_mp4']['sha256']==r['sha256']==report['actual_mp4']['sha256']=='1e1685c5b0eff4ebb2d3e8bab3f368336ea31a313b38c10a0ef0f7a1ae365163'
assert r['id']=='28'and r['new_id']=='29'and r['bytes']==17473089
assert r['reordered_path'].startswith('顺序重排版/视频/29 ')
assert report['actual_probe']==r['qc']['actual_probe'] and report['actual_probe']['frames']==4858
before=copy.deepcopy(r['actual_probe']);old_tail=copy.deepcopy(r['tail'])
r['inherited_original_0_3_preview_actual_probe']=before
r['inherited_original_0_3_preview_tail']=old_tail
r['actual_probe']=copy.deepcopy(report['actual_probe'])
r['tail'].update(speech_end_frame=4720,held_body_end_frame=4738,extra_body_hold_frames=18,
                 illustration_start_frame=4738,summary_start_frame=4798,output_frames=4858,
                 voice_endpoint_seconds=157.33,voice_to_illustration_gap_seconds=report['actual_geometry']['voice_to_picture_seconds'])
assert r['qc']['video_sha256']==r['sha256']and r['qc']['video_bytes']==r['bytes']
assert r['qc']['preview_hold']['frames']==18 and r['qc']['illustration']['start_frame']==4738 and r['qc']['summary']['start_frame']==4798
write(record_path,r)
patch={'kind':'current_derived_record_probe_and_tail_metadata_correction_only',
       'previous_handoff':spec(history/'preview-handoff.json'),
       'previous_record':spec(history/'validated-article-record.json'),
       'current_record':spec(record_path),'old_probe_preserved_as_inherited':before,
       'current_actual_probe':r['actual_probe'],'old_tail_preserved_as_inherited':old_tail,
       'current_tail':r['tail'],'id_new_id_paths_SHA_bytes_QC_match_actual_current_MP4':True,
       'prior_original_full_V3_record_unchanged':True,'media_or_quality_checks_repeated_or_changed':False,
       'explanation':'The new record inherited the0.3 preview top-level probe/tail while its nested actual postprocess report and QC were already correct. Only the derived current record labels are synchronized; old metadata and original quality records remain explicit history.'}
patch_path=OUT/'current-probe-and-tail-metadata-correction.json';write(patch_path,patch)
snapshot=OUT/'code-snapshot';tool=snapshot/Path(__file__).name;shutil.copyfile(__file__,tool)
h['tool_source_sha256'][tool.name]=digest(tool)
h['current_identity_metadata_correction']=spec(patch_path)
upstream=Path('/workspace/work/video-audit70-20261113/article28-user-review-20261114/hold18-preview/upstream/28-new-requested-preview-hold18-then-summary60.mp4')
h['additional_public_media_inputs']=[spec(upstream)]
for row in h['validation_files']:
    if Path(row['path'])==record_path:row.update(spec(record_path))
known={v['path']for v in h['validation_files']}
for p in [patch_path,tool,*history.iterdir()]:
    if str(p)not in known:h['validation_files'].append({**spec(p),'relative_validation_path':str(p.relative_to(OUT))})
write(handoff_path,h)
print(json.dumps({'current_handoff':spec(handoff_path),'current_record':spec(record_path),'metadata_only_correction':spec(patch_path)},ensure_ascii=False))
