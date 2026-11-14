"""Apply explicit user057 scope to the unchanged already-verified Tu29 bytes.

No rendering, native generation, audio processing, subjective listening, or
alteration of any historical preview handoff/report occurs here.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

P = Path('/workspace/work/video-revision-delivery/hold18-intake-preparation-20261114')
sys.path.insert(0, str(P))
from hold18_geometry import geometry

OUT = Path(__file__).resolve().parent
OLD = Path('/workspace/work/video-revision-delivery/post-only-hold18-validated/28')
AUTH = Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-057.json')
AUTH_SHA = '3c91671ad6dcc1e30f6336efa394eac1ff776c8405157b924f2e86f64266284a'
VIDEO_SHA = '1e1685c5b0eff4ebb2d3e8bab3f368336ea31a313b38c10a0ef0f7a1ae365163'


def load(p): return json.loads(Path(p).read_text())
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()
def spec(p):
    p = Path(p).resolve()
    return {'path':str(p), 'bytes':p.stat().st_size, 'sha256':sha(p)}
def checked(r):
    p = Path(r['path'])
    assert p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], p
    return p
def write(p, v): Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n')


def main():
    assert not (OUT/'archive-handoff.json').exists(), 'A frozen adoption handoff must not be rewritten'
    assert sha(AUTH) == AUTH_SHA
    authority = load(AUTH)
    scope = authority['required_scope']
    assert scope['book_order_inclusive'] == [1,34]
    assert scope['source28_book29_existing_06_effect_preview_reuse_as_current_uniform_timing_edition_authorized'] is True
    assert scope['source28_prior_subjective_listening_or_effect_acceptance_not_invented'] is True
    anchors = [
        (OLD/'history-before-current-still-reference-correction/preview-handoff.json', '22adbe40a6bca892c460eaf6d76a1d5a6a299a7004f27f5977fb9cc931874ae1'),
        (OLD/'history-before-current-still-reference-correction/validated-article-record.json', 'c837b6bc68488900e99169e7354fb6d4af7dbacd9bdbb0b4e8b0f94b9f2fbbde'),
        (OLD/'preview-handoff.json', '9a8718c1ce2d62f4017d7a7adb55e5a87bb5a61209ad3d806864514e0a663860'),
        (OLD/'validated-article-record.json', '2b9bffc59173b799fa05bffd03a2e0934a3146a87993e98198a02f148eb89e7c')]
    for p, wanted in anchors: assert sha(p) == wanted, p
    old = load(OLD/'preview-handoff.json')
    prior = old['articles'][0]
    assert prior['source_id'] == '28' and prior['new_id'] == '29'
    assert old['preview_only'] is True and old['production_delivery_eligible'] is False
    assert prior['preview_passed'] is True and prior['passed_per_article'] is False
    movie = checked(prior['preview_mp4'])
    assert sha(movie) == VIDEO_SHA and movie.stat().st_size == 17473089
    record = load(OLD/'validated-article-record.json')
    assert record['actual_probe'] == record['qc']['actual_probe']
    assert record['actual_probe']['frames'] == 4858 and record['actual_probe']['fps'] == '30/1'
    assert (record['actual_probe']['width'],record['actual_probe']['height']) == (3840,2160)
    t = record['tail']
    g = geometry(t['voice_endpoint_seconds'],t['held_body_end_frame'],t['illustration_start_frame'],
                 t['summary_start_frame'],t['output_frames'],t['voice_to_illustration_gap_seconds'])
    assert g['speech_ceiling_frame'] == 4720 and t['extra_body_hold_frames'] == 18
    assert (t['illustration_start_frame'],t['summary_start_frame'],t['output_frames']) == (4738,4798,4858)
    assert record['qc']['audio']['lossless_copy']['final_packet_count'] == 7469
    assert record['qc']['audio']['lossless_copy']['final_aac_adts_sha256'] == '82898283b5f5c55b84912f8838ebdfed1a337300db09de759fc55a3eb389ddd2'
    section = copy.deepcopy(prior['section'])
    assert [r['frame'] for r in section['stills']] == [4737,4738,4797,4798,4857]
    assert all(r['video_sha256'] == VIDEO_SHA for r in section['stills'])
    for row in old['validation_files']: checked(row)
    for row in section['stills']: checked(row)
    receipt = {
        'kind':'explicit-user057-adoption-of-existing-qualified-Tu29-hold18-edition',
        'source_id':'28','new_id':'29','authority':spec(AUTH),
        'current_scope':'Uniform0.6s timing edition for book01-through34 only',
        'media':spec(movie),'actual_geometry_inherited_unchanged':g,
        'old_preview_and_metadata_anchors':[spec(p)for p,_ in anchors],
        'all_old_preview_flags_and_original_QA_bytes_preserved':True,
        'current_uniform_timing_installation_authorized':True,
        'new_native_TTS_render_tail_or_audio_processing_performed':False,
        'new_subjective_listening_or_effect_acceptance_claimed':False,
        'old_physical_quality_and_actual_visual_checks_reused_not_repeated':True,
        'old_preview_was_not_retroactively_production_authorized':True,
        'books35plus_or_PDF_modified':False}
    write(OUT/'explicit-user057-reuse-authority.json', receipt)
    qc = copy.deepcopy(record['qc'])
    qc.update(preview_only=False,production_delivery_eligible=True,
              active_final_replacement_authorized=True,final_user_acceptance=False,
              actual_new_mp4=False,reused_existing_qualified_media=True,
              current_scope_authority=spec(OUT/'explicit-user057-reuse-authority.json'),
              original_preview_QA=spec(checked(section['qc'])),
              subjective_listening_or_effect_acceptance_claimed=False,
              new_native_quality_run_claimed=False)
    write(OUT/'current-scope057-QC.json',qc)
    record.update(qc=qc,preview_only=False,production_delivery_eligible=True,
                  passed_per_article=True,active_final_replacement_authorized=True,
                  final_user_acceptance=False,reused_existing_qualified_media=True,
                  current_delivery_scope='first34-uniform-timing057',
                  current_scope_authority=spec(OUT/'explicit-user057-reuse-authority.json'),
                  original_preview_record=spec(OLD/'validated-article-record.json'))
    record['tail']['preview_only'] = False
    for key in ('preview_delivery_eligible','preview_passed','normal70_final_assembly_eligible'):
        record.pop(key,None)
    write(OUT/'validated-article-record.json',record)
    section['qc'] = spec(OUT/'current-scope057-QC.json')
    section['evidence'].append(spec(OUT/'explicit-user057-reuse-authority.json'))
    cfg = load(old['input_path'])
    cfg.update(kind='first34-user057-existing-qualified18-media-reuse',articles=[section])
    write(OUT/'actual-sample-input.json',cfg)
    report = {
        'status':'passed_actual_existing18_media_reuse_under_explicit_user057',
        'source_id':'28','new_id':'29','source_run':old['source_run'],
        'actual_media':spec(movie),'actual_probe':record['actual_probe'],
        'actual_tail':record['tail'],'actual_existing_V3_basis':spec(OLD/'preview-handoff.json'),
        'authority':spec(OUT/'explicit-user057-reuse-authority.json'),
        'production_delivery_eligible_for_current_scope':True,
        'no_new_native_TTS_tail_processing_subjective_listening_or_effect_acceptance_claimed':True,
        'quality_programs_or_thresholds_modified':False}
    write(OUT/'report.json',report)
    snap=OUT/'code-snapshot';snap.mkdir(exist_ok=True)
    shutil.copyfile(__file__,snap/Path(__file__).name)
    article={
        'source_id':'28','new_id':'29','passed_per_article':True,
        'final_mp4':spec(movie),'canonical_source_mp4':prior['canonical_source_mp4'],
        'immutable_native_zip':prior['immutable_native_zip'],
        'validated_record':str(OUT/'validated-article-record.json'),'section':section,
        'source_notes':'Exact existing0.6s preview bytes and real source/GEN/MD/AAC/physical QA retained; explicit user057 now authorizes their current uniform-timing installation. No new native generation, tail change or subjective acceptance is claimed.'}
    files=[{**r,'relative_validation_path':'inherited-qualified-preview/'+r['relative_validation_path']}
           for r in old['validation_files']]
    for i,(p,_)in enumerate(anchors):
        files.append({**spec(p),'relative_validation_path':'original-preview-anchors/'+str(i)+'-'+p.name})
    files.append({**spec(AUTH),'relative_validation_path':'authority/USER-REVIEW-2026-11-14-057.json'})
    files.extend({**spec(p),'relative_validation_path':str(p.relative_to(OUT))}
                 for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='archive-handoff.json')
    h={
        'status':'passed_actual_existing18_media_adopted_under_explicit_first34_scope057',
        'kind':'first34-uniform-timing057-existing-qualified-preview-reuse',
        'source_run':old['source_run'],'complete70_release_validated':False,
        'preview_only':False,'production_delivery_eligible':True,
        'active_final_replacement_authorized':True,'final_user_acceptance':False,
        'first34_uniform_timing_installation_eligible':True,
        'new_native_job_or_TTS_claimed':False,'new_tail_or_audio_processing_claimed':False,
        'new_subjective_listening_or_effect_acceptance_claimed':False,
        'publishing_or_remote_mutation_executed':False,
        'current_scope_authority':spec(AUTH),'reuse_authority':spec(OUT/'explicit-user057-reuse-authority.json'),
        'articles':[article],'report_path':str(OUT/'report.json'),
        'input_path':str(OUT/'actual-sample-input.json'),'validation_files':files,
        'global_approved_evidence':old['global_approved_evidence'],
        'tool_source_sha256':{Path(__file__).name:sha(snap/Path(__file__).name)},
        'code_snapshot_path':str(snap),'native_root':old['native_root'],
        'additional_public_media_inputs':old.get('additional_public_media_inputs',[]),
        'inherited_exact_preview_handoff':spec(OLD/'preview-handoff.json'),
        'original_archived22ad_handoff':spec(anchors[0][0]),
        'original_archivedc837_record':spec(anchors[1][0])}
    for row in files: checked(row)
    assert sha(movie)==VIDEO_SHA and record['actual_probe']==qc['actual_probe']
    for p,wanted in anchors: assert sha(p)==wanted
    write(OUT/'archive-handoff.json',h)
    print(json.dumps({'handoff':spec(OUT/'archive-handoff.json'),
                      'record':spec(OUT/'validated-article-record.json'),
                      'media_unchanged':spec(movie)},ensure_ascii=False))


if __name__=='__main__': main()
