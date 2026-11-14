"""Bind four actually rendered, source-owner-applied and GEN-paired sources.

Only the eight source-digest leaves in the working CI approval are changed.
"""
import copy,datetime,hashlib,json,pathlib
from PIL import Image
B=pathlib.Path(__file__).parent;AUD=B.parent
CI=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json')
sha=lambda x:hashlib.sha256(x).hexdigest()
def rgb(p):
    with Image.open(p)as im:
        assert im.size==(3840,2160)
        return sha(im.convert('RGB').tobytes())
def diff(a,b,p=''):
    if isinstance(a,dict)and isinstance(b,dict):return[z for k in sorted(a.keys()|b.keys())for z in([p+'/'+k]if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
    if isinstance(a,list)and isinstance(b,list):return[p]if len(a)!=len(b)else[z for i,(x,y)in enumerate(zip(a,b))for z in diff(x,y,p+'/'+str(i))]
    return[]if a==b else[p]
pr=(B/'preview-report.json').read_bytes();preview=json.loads(pr);assert preview['passed']and not preview['manifest_mutation_executed']
application_path=AUD/'root-approved-audio-source-application-20261114/application.json';application=json.loads(application_path.read_bytes());applied={a['id']:a for a in application['articles']}
pair_path=AUD/'root-approved-audio-source-GEN-text-20261114/report.json';paired=json.loads(pair_path.read_bytes());assert paired['status']=='passed'
old=json.loads((B/'approved-video-layouts70.before.json').read_bytes());oldrows={x['source_id']:x for x in old['articles']}
raw=CI.read_bytes();current=json.loads(raw);before=copy.deepcopy(current);assert current['passed']and current['count']==70
rows={x['source_id']:x for x in current['articles']};actual={}
for a in preview['articles']:
    no=a['source_id'];assert no in ['05','15','17','30']
    p=AUD/'payload/视频/脚本'/f'{no}.json';data=p.read_bytes();assert sha(data)==a['after_source_json_sha256']==applied[no]['after_sha256']
    assert data==(B/f'{no}-current-approved-sound-source.json').read_bytes();actual[no]=(p,data)
    row=rows[no];assert row==oldrows[no],'Approval row changed since actual rendering: '+no
    assert a['all_body_text_translation_alignment_notes_and_summary_exact']and a['all_sentence_fonts_and_geometry_exact']
    for r in a['actual_renders']:
        assert rgb(r['summary_png'])==r['summary_rgb_sha256']==row['summary_rgb_sha256']
        assert sha(pathlib.Path(r['summary_png']).read_bytes())==r['summary_png_sha256']
        assert rgb(r['body_tail_png'])==r['body_tail_rgb_sha256']
    assert a['actual_renders'][0]['body_tail_rgb_sha256']==a['actual_renders'][1]['body_tail_rgb_sha256']==rgb(AUD/'final-layout/body-tail'/f'{no}.png')
    row['source_json_sha256']=a['after_source_json_sha256'];row['source_layout_structural_sha256']=a['after_source_layout_structural_sha256']
changed=diff(before,current);assert len(changed)==8 and all(x.endswith('/source_json_sha256')or x.endswith('/source_layout_structural_sha256')for x in changed)
assert CI.read_bytes()==raw and all(p.read_bytes()==data for p,data in actual.values()),'Concurrent source or CI change'
after=(json.dumps(current,ensure_ascii=False,indent=2)+'\n').encode();(B/'approved-video-layouts70.before-commit.json').write_bytes(raw);(B/'approved-video-layouts70.after.json').write_bytes(after)
tmp=CI.with_suffix('.json.nextfour.tmp');tmp.write_bytes(after);tmp.replace(CI)
report=copy.deepcopy(preview);report.update(created_binding_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_kind='actual_official_static_4K_rerender_then_exact_applied_and_GEN_paired_source_binding_only_not_new_video',
    actual_preview_report_path=str(B/'preview-report.json'),actual_preview_report_sha256=sha(pr),manifest_mutation_executed=True,source_applied_by_unique_writer='resume_audio_ci',
    source_owner_application_report_path=str(application_path),source_owner_application_report_sha256=sha(application_path.read_bytes()),
    source_GEN_pair_report_path=str(pair_path),source_GEN_pair_report_sha256=sha(pair_path.read_bytes()),
    layout_worker_modified_source_audio_or_video=False,audio_QC_or_new_native_pass_not_claimed=True,
    before_commit_manifest_sha256=sha(raw),after_manifest_sha256=sha(after),only_manifest_field_changes=changed,
    frozen_or_local_baseline_manifests_modified=False,PNG_RGB_font_and_approval_fields_unchanged=True,modified_manifest_only_working_CI=True,CI_manifest_path=str(CI))
(B/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=True,source_ids=list(actual),manifest_sha256=sha(after),report=str(B/'report.json'),report_sha256=sha((B/'report.json').read_bytes())),ensure_ascii=False))
