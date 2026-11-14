"""Bind an already actually rendered exact approved source after owner applies it.

No image regeneration, source edit, audio edit, helper-ignore expansion, or old
approval mutation. Only current CI article67's two source digests are updated.
"""
import copy,datetime,hashlib,json,pathlib
from PIL import Image
B=pathlib.Path(__file__).parent
CI=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json')
PAY=pathlib.Path('/workspace/work/video-audit70-20261113/payload/视频/脚本/67.json')
sha=lambda x:hashlib.sha256(x).hexdigest()
def rgb(p):
    with Image.open(p)as im:
        assert im.size==(3840,2160)
        return sha(im.convert('RGB').tobytes())
def diff(a,b,p=''):
    if isinstance(a,dict)and isinstance(b,dict):return[z for k in sorted(a.keys()|b.keys())for z in ([p+'/'+k]if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
    if isinstance(a,list)and isinstance(b,list):return[p]if len(a)!=len(b)else[z for i,(x,y)in enumerate(zip(a,b))for z in diff(x,y,p+'/'+str(i))]
    return[]if a==b else[p]
preview_raw=(B/'preview-report.json').read_bytes();preview=json.loads(preview_raw);assert preview['passed']and not preview['manifest_mutation_executed']
actual=PAY.read_bytes();assert sha(actual)==preview['actual_approved_source_candidate_sha256']=='6839a46ebdb51cdcff6a65ca238efc228f1e114efd1734cee6c994ca659a29cb'
assert actual==(B/'67-current-approved-sound-source.json').read_bytes()
old_manifest=json.loads((B/'approved-video-layouts70.before.json').read_bytes());old_row=next(x for x in old_manifest['articles']if x['source_id']=='67')
raw=CI.read_bytes();current=json.loads(raw);assert current['passed']and current['count']==70
row=next(x for x in current['articles']if x['source_id']=='67');assert row==old_row,'Article67 approval changed since actual preview'
article=preview['articles'][0];assert article['source_id']=='67'
for r in article['actual_renders']:
    assert rgb(r['summary_png'])==r['summary_rgb_sha256']==row['summary_rgb_sha256']
    assert sha(pathlib.Path(r['summary_png']).read_bytes())==r['summary_png_sha256']
    assert rgb(r['body_tail_png'])==r['body_tail_rgb_sha256']
assert article['actual_renders'][0]['body_tail_rgb_sha256']==article['actual_renders'][1]['body_tail_rgb_sha256']==rgb('/workspace/work/video-audit70-20261113/final-layout/body-tail/67.png')
before=copy.deepcopy(current);row['source_json_sha256']=article['after_source_json_sha256'];row['source_layout_structural_sha256']=article['after_source_layout_structural_sha256']
changed=diff(before,current);assert len(changed)==2 and all(x.endswith('/source_json_sha256')or x.endswith('/source_layout_structural_sha256')for x in changed)
assert PAY.read_bytes()==actual and CI.read_bytes()==raw,'Concurrent source or CI change'
after=(json.dumps(current,ensure_ascii=False,indent=2)+'\n').encode();(B/'approved-video-layouts70.before-commit.json').write_bytes(raw);(B/'approved-video-layouts70.after.json').write_bytes(after);(B/'67-actual-applied-source.json').write_bytes(actual)
tmp=CI.with_suffix('.json.rebind67.tmp');tmp.write_bytes(after);tmp.replace(CI)
report=copy.deepcopy(preview);report.update(created_binding_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    evidence_kind='actual_official_static_4K_rerender_then_exact_source_application_binding_only_not_new_video',
    actual_preview_report_path=str(B/'preview-report.json'),actual_preview_report_sha256=sha(preview_raw),
    manifest_mutation_executed=True,source_application_not_claimed=False,source_applied_by_unique_writer='resume_audio_ci',
    actual_applied_source_path=str(PAY),actual_applied_source_sha256=sha(actual),
    layout_worker_modified_source_audio_or_video=False,GEN_pair_and_audio_quality_pass_not_claimed_by_layout_report=True,
    before_commit_manifest_sha256=sha(raw),after_manifest_sha256=sha(after),only_manifest_field_changes=changed,
    frozen_or_local_baseline_manifests_modified=False,PNG_RGB_font_and_approval_fields_unchanged=True,
    modified_manifest_only_working_CI=True,CI_manifest_path=str(CI))
report['articles'][0]['latest_source_path']=str(PAY)
(B/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=True,manifest=str(CI),manifest_sha256=sha(after),report=str(B/'report.json'),report_sha256=sha((B/'report.json').read_bytes())),ensure_ascii=False))
