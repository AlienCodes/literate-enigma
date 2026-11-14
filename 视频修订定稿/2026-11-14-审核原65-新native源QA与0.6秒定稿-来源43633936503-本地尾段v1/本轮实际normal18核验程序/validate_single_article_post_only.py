"""Strict actual normal18 local tail validation over an unchanged full-V3 body.

Existing native/source/audio QA is inherited honestly, never claimed rerun.
New native47/34/62 must first obtain their own original full quality acceptance.
"""
import argparse,copy,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=Path('/dev/shm/native-inline-engine-reviewed65-v24-controlled-current-role')
sys.path.insert(0,str(BASE))
import delivery as D
from normal18_contract import actual_normal_tail,current_stills,fresh_derived_record
from hold18_geometry import require

def spec(p):
    p=Path(p).resolve();return {'path':str(p),'bytes':p.stat().st_size,'sha256':D.digest(p)}
def checked(r):
    p=Path(r['path']);require(p.stat().st_size==r['bytes']and D.digest(p)==r['sha256'],'Actual declared input differs: '+str(p));return p
def compact_audio(a):return {k:v for k,v in a.items()if k!='projection'}
def load_module(p):
    s=importlib.util.spec_from_file_location('actual_normal18_helper',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def validate(a):
    ufile=Path(a.upstream_record);u=D.load(ufile);n=u['article'];out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    profile_path=HERE/'normal18-actual-final-frozen-producer-profile.json';profile=D.load(profile_path);helper=checked(profile['helper'])
    require(n in profile['normal_final_source_ids']and u['postprocessing_only']is True and u['new_native_generated']is False,'Actual authorized local normal18 source required')
    prior_path=Path(u['inherited_passed_handoff']);require(D.digest(prior_path)==u['inherited_passed_handoff_sha256'],'Actual inherited fullV3 handoff differs')
    prior=D.load(prior_path);original=next(r for r in prior['articles']if r['source_id']==n)
    require(original['passed_per_article']is True and not prior.get('preview_only',False),'A preview cannot be promoted to a normal final')
    for row in prior['validation_files']:checked(row)
    old=D.load(original['validated_record']);oq=old['qc'];checked(original['final_mp4']);canonical=checked(original['canonical_source_mp4'])
    require(D.digest(canonical)==u['source_video_sha256']and u['source_native_run']==prior['source_run'],'Actual original quality-passed body/source differs')
    raw_path=Path(a.tail_report);raw=D.load(raw_path);movie=Path(a.mp4);up=Path(u['actual_output_file']);require(D.digest(movie)==raw['video_sha256']and D.digest(up)==u['actual_output_sha256']==raw['input_video_sha256'],'Actual local normal18 MP4 chain differs')
    folder=ufile.parent;timing_path=folder/(n+'-verification.json');timing=D.load(timing_path);adapted_path=folder/(n+'-summary-verification.json');status_path=folder/(n+'-upstream-summary-status.json');adapted=D.load(adapted_path);status=D.load(status_path)
    require(D.digest(adapted_path)==raw['upstream_verification_sha256']and D.digest(status_path)==raw['upstream_status_sha256'],'Actual postprocessor input proof/status differs')
    require(adapted['postprocessing_only']is True and adapted['inherited_true_native_full_QA_run']==prior['source_run']and status['true_original_native_full_QA_run']==prior['source_run'],'Do not fabricate a new native quality run')
    require(timing['kind']==profile['upstream_kind']and timing['preview_only']is False and timing['finalization_authorized']is True and timing['last_body_hold_frames']==18,'Actual upstream final18 declaration differs')
    for key in ('original_audio_identical','original_audio_packet_timings_identical','copied_prefix_coded_pictures_identical','copied_prefix_packet_timings_identical','body_script_identical'):
        require(timing[key]is True,'Actual unchanged original end-card check failed: '+key)
    require(timing['body_outside_summary_min_ssim']>.995 and timing['old_summary_pixel_verification']['held_body_frame_match_error']<2,'Actual original end-card visual bounds failed')
    layout=next(r for r in D.load(checked(prior['global_approved_evidence']['video_layout_approval']))['articles']if r['source_id']==n)
    book=next(r for r in D.load(checked(prior['global_approved_evidence']['book_illustrations']))['illustrations']if r['source_id']==n)
    decoded=raw['output_final_hold_validation'];normalized={k:decoded[v]for k,v in profile['decoder_keys'].items()}
    g=actual_normal_tail(raw,article=n,new_id=original['new_id'],expected_kind=profile['output_kind'],expected_program_sha=profile['helper']['sha256'],actual_hold=normalized,layout_row=layout,book_row=book,request_json_sha256=oq['source_sha256']['request']['json'])
    require(timing['unheld_voice_ceiling_frame']==g['speech_ceiling_frame']and timing['source_voice_endpoint_seconds']==raw['source_voice_endpoint_seconds'],'Actual measured speech endpoint changed')
    current=load_module(helper);require(current.verify_final_hold(movie,raw['body_frames'])==decoded,'Independent actual18 decoder differs')
    require(raw['illustration_composed_4k_rgb_sha256']==oq['illustration']['preparation']['prepared_rgb_sha256'],'Approved illustration RGB changed')
    prepared=raw['illustration_preparation'];require(current.sha(prepared['prepared_image_path'])==prepared['prepared_png_sha256']and current.rgb_sha(prepared['prepared_image_path'])==prepared['prepared_rgb_sha256'],'Actual prepared image identity differs')
    audio=[D.actual_aac(p)for p in(canonical,up,movie)];require(audio[0]==audio[1]==audio[2],'Actual original→held18→final AAC/codec/side-data/absolute clock differs')
    probe=D.probe(movie);require(probe['frames']==g['held_body_end_frame_exclusive']+120,'Actual output frame count differs')
    review_path=Path(a.boundary_review);review=D.load(review_path);require(review['actually_visually_reviewed']is True and review['video_sha256']==raw['video_sha256'],'Actual current boundary review required')
    stills=current_stills(raw['decoded_frame_previews'],video_sha256=raw['video_sha256'],held_body_end=raw['body_frames'],output_frames=raw['output_frames'])
    qc=copy.deepcopy(oq);qc.update(video_sha256=D.digest(movie),video_bytes=movie.stat().st_size,actual_probe=probe,preview_only=False,production_delivery_eligible=True,local_postprocessing_only=True,new_native_quality_run_claimed=False,inherited_full_V3_handoff=spec(prior_path))
    if 'native_inline_final_original_bytes_preserved'in qc['official_run']:qc['official_run']['inherited_native_inline_final_original_bytes_preserved']=qc['official_run'].pop('native_inline_final_original_bytes_preserved')
    qc['official_run']['current_final_is_local_tail_derivative']=True
    qc['speech_end'].update(end_frame=g['speech_ceiling_frame'],endpoint_seconds=raw['source_voice_endpoint_seconds'])
    qc['body_hold']={**g,'actual_decoded_hold_validation':decoded}
    qc['illustration'].update(start_frame=raw['illustration_start_frame'],preparation=prepared)
    qc['illustration']['frame_comparison'].update(start_frame=raw['illustration_start_frame'],video_sha256=D.digest(movie),report_sha256=D.digest(raw_path))
    qc['summary'].update(start_frame=raw['summary_start_frame'])
    qc['audio']['lossless_copy'].update(final_video_sha256=D.digest(movie),final_aac_adts_sha256=audio[2]['aac_adts_sha256'],final_packet_projection_sha256=audio[2]['packet_projection_sha256'],final_packet_count=audio[2]['packet_count'])
    qc['audio_repair_applied_in_this_tail_postprocess']=False
    record=fresh_derived_record(old,mp4_spec=spec(movie),actual_probe=probe,current_qc=qc,actual_audio_chain=compact_audio(audio[2]),actual_geometry=g)
    record.update(local_postprocessing_only=True,new_native_job_claimed=False)
    D.write(out/'validated-article-record.json',record);D.write(out/'actual-current-QC.json',qc)
    item=copy.deepcopy(original['section']);item.update(mp4=spec(movie),qc=spec(out/'actual-current-QC.json'),stills=stills)
    item['evidence'].extend(spec(p)for p in(raw_path,review_path,ufile,profile_path,Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-094.json')))
    report={'status':'passed_actual_normal18_post_only','source_id':n,'new_id':original['new_id'],'source_run':prior['source_run'],'local_postprocessing_only':True,'new_native_job_or_TTS_claimed':False,'actual_MP4':spec(movie),'actual_probe':probe,'actual_geometry':g,'actual_audio_chain':[compact_audio(x)for x in audio],'inherited_full_V3':spec(prior_path),'actual_new_tail_proof':spec(raw_path),'actual_visual_review':spec(review_path),'production_delivery_eligible':True,'preview_only':False,'original_source_GEN_MD_voice_QA_unchanged':True}
    D.write(out/'report.json',report);D.write(out/'actual-sample-input.json',{'kind':'normal18-post-only-inheriting-real-full-V3','articles':[item]})
    snapshot=out/'code-snapshot';snapshot.mkdir(exist_ok=True);hashes={}
    for p in(Path(__file__),HERE/'normal18_contract.py',HERE/'hold18_geometry.py',profile_path,helper,BASE/'delivery.py',BASE/'release_contract.py'):
        target=snapshot/p.name;shutil.copyfile(p,target);hashes[p.name]=D.digest(target)
    validation=[{**r,'relative_validation_path':'inherited-full-V3/'+r['relative_validation_path']}for r in prior['validation_files']]
    require(D.digest(profile['composition_bridge']['path'])==profile['composition_bridge']['sha256'],'Actual composition bridge differs')
    extras=[ufile,raw_path,review_path,timing_path,adapted_path,status_path,profile_path,Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-094.json'),Path(profile['composition_bridge']['path']),*folder.glob('*.png'),*[Path(r['path'])for r in raw['decoded_frame_previews']]]
    validation +=[{**spec(p),'relative_validation_path':'actual-normal18-evidence/'+str(i)+'-'+p.name}for i,p in enumerate(dict.fromkeys(extras))]
    validation +=[{**spec(p),'relative_validation_path':str(p.relative_to(out))}for p in out.rglob('*')if p.is_file()and p.name!='archive-handoff.json']
    hand={'status':'passed_actual_normal18_post_only_for_permanent_archive','kind':'authorized-normal18-local-tail-derivative','source_run':prior['source_run'],'local_postprocessing_only':True,'new_native_job_or_TTS_claimed':False,'complete70_release_validated':False,'publishing_or_remote_mutation_executed':False,'preview_only':False,'production_delivery_eligible':True,'articles':[{'source_id':n,'new_id':original['new_id'],'passed_per_article':True,'final_mp4':spec(movie),'canonical_source_mp4':original['canonical_source_mp4'],'immutable_native_zip':original['immutable_native_zip'],'validated_record':str(out/'validated-article-record.json'),'section':item}],'additional_public_media_inputs':[spec(up)],'report_path':str(out/'report.json'),'input_path':str(out/'actual-sample-input.json'),'validation_files':validation,'global_approved_evidence':prior['global_approved_evidence'],'tool_source_sha256':hashes,'code_snapshot_path':str(snapshot),'native_root':prior['native_root'],'inherited_full_V3':spec(prior_path)}
    D.write(out/'archive-handoff.json',hand)
    for row in validation:checked(row)
    require(record['actual_probe']==qc['actual_probe']and all(s['video_sha256']==record['sha256']for s in item['stills']),'Current record/QC/stills disagree')
    print(json.dumps({'handoff':spec(out/'archive-handoff.json'),'record':spec(out/'validated-article-record.json'),'actual_packet_count':audio[2]['packet_count']},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in('upstream-record','tail-report','mp4','boundary-review','output'):p.add_argument('--'+k,required=True)
    validate(p.parse_args())
