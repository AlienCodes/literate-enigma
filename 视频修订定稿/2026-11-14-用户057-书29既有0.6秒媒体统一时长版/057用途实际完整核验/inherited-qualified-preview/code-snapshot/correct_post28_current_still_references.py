"""Synchronize derived section with the already verified actual18-frame output."""
import copy,hashlib,json,shutil
from pathlib import Path
O=Path('/workspace/work/video-revision-delivery/post-only-hold18-validated/28')
T=Path('/workspace/work/video-audit70-20261113/article28-user-review-20261114/hold18-integrator')
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def spec(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
hpath=O/'preview-handoff.json';rpath=O/'validated-article-record.json';qpath=O/'28-current-local-postprocess-QC.json';ipath=O/'actual-sample-input.json'
history=O/'history-before-current-still-reference-correction';history.mkdir(exist_ok=True)
for p in (hpath,rpath,qpath,ipath):
    dest=history/p.name
    if not dest.exists():shutil.copyfile(p,dest)
h=load(hpath);r=load(rpath);q=load(qpath);i=load(ipath);rawpath=T/'28-actual-new-hold18-art60-summary60-report.json';raw=load(rawpath)
old_stills=copy.deepcopy(h['articles'][0]['section']['stills'])
require_sha='1e1685c5b0eff4ebb2d3e8bab3f368336ea31a313b38c10a0ef0f7a1ae365163'
assert raw['video_sha256']==r['sha256']==q['video_sha256']==require_sha
q['official_run']['inherited_native_inline_final_original_bytes_preserved']=q['official_run'].pop('native_inline_final_original_bytes_preserved')
q['official_run']['current_final_is_local_tail_derivative']=True
q['inherited_original_stills']=old_stills
write(qpath,q);r['qc']=q;write(rpath,r)
newstills=[]
for row in raw['decoded_frame_previews']:
    p=Path(row['path']);assert sha(p)==row['sha256']
    kind='body_end'if row['label']=='body-last'else'illustration'if row['label'].startswith('illustration')else'summary'
    newstills.append({**spec(p),'kind':kind,'frame':row['frame'],'video_sha256':require_sha,'decoded_from_actual_mp4':True})
assert [s['frame']for s in newstills]==[4737,4738,4797,4798,4857]
for item in (h['articles'][0]['section'],i['articles'][0]):
    item['stills']=newstills;item['qc']=spec(qpath)
    existing={v['sha256']for v in item['evidence']}
    for p in (rawpath,O/'report.json',T/'actual-seven-frame-boundary-review.json'):
        if sha(p)not in existing:item['evidence'].append(spec(p))
write(ipath,i)
patch={'kind':'current_held18_section_still_and_native_role_reference_correction_only',
       'previous_handoff':spec(history/'preview-handoff.json'),'old_stills_preserved_as_inherited':old_stills,
       'new_actual_stills':newstills,'actual_video_sha256':require_sha,
       'source_run':43576642418,'local_postprocessing_only':True,
       'current_record':spec(rpath),'current_qc':spec(qpath),
       'actual_media_quality_checks_not_rerun_or_changed':True,
       'explanation':'The original native evidence and0.3 stills remain history. Current derived section now points to already decoded and actually viewed0.6 frames. Original native preserved-byte fact is explicitly inherited, never a claim that this local derivative was inside the original artifact.'}
patchpath=O/'current-still-and-native-role-reference-correction.json';write(patchpath,patch)
tool=O/'code-snapshot'/Path(__file__).name;shutil.copyfile(__file__,tool)
h['tool_source_sha256'][tool.name]=sha(tool);h['current_still_reference_correction']=spec(patchpath)
for v in h['validation_files']:
    p=Path(v['path'])
    if p in (rpath,qpath,ipath):v.update(spec(p))
known={v['path']for v in h['validation_files']}
for p in (tool,patchpath,*history.iterdir()):
    if str(p)not in known:h['validation_files'].append({**spec(p),'relative_validation_path':str(p.relative_to(O))})
write(hpath,h)
for v in h['validation_files']:
    p=Path(v['path']);assert p.stat().st_size==v['bytes']and sha(p)==v['sha256'],p
assert load(rpath)['actual_probe']==q['actual_probe']==load(O/'report.json')['actual_probe']
assert all(s['video_sha256']==require_sha for s in h['articles'][0]['section']['stills'])
print(json.dumps({'handoff':spec(hpath),'record':spec(rpath),'validation_file_count':len(h['validation_files'])},ensure_ascii=False))
