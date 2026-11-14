#!/usr/bin/env python3
"""Import a genuinely passed producer that ALREADY contains both60-frame pages.

Preserves the native final MP4 and every original report byte. Local aliases
only let the existing per-article validator inspect the original audio chain.
No tail generation, re-encoding, repository write or publication occurs here.
"""
import argparse, datetime, hashlib, json, os, shutil, zipfile
from pathlib import Path
import delivery as D
from derive_final_generator import derive
from import_actual_article import import_one, spec, preview_path

B=Path(__file__).resolve().parent;AUDIT=Path('/workspace/work/video-audit70-20261113')

def link_exact(source,destination):
    source=Path(source);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():D.require(D.digest(source)==D.digest(destination),'Existing native alias differs');return
    try:os.link(source,destination)
    except OSError:shutil.copyfile(source,destination)

def prepare(a):
    n=a.article.zfill(2);root=Path(a.native_root).resolve();out=Path(a.output_root).resolve();root.mkdir(parents=True,exist_ok=True)
    api=D.GitHub();repo=D.BACKUP[0];job=api.api(repo,f'actions/jobs/{a.job_id}');run=api.api(repo,f'actions/runs/{a.run_id}/attempts/{job["run_attempt"]}');artifact=api.api(repo,f'actions/artifacts/{a.artifact_id}')
    D.require(job['status']=='completed'and job['conclusion']=='success'and job['run_id']==a.run_id and f'({n})'in job['name'],'Actual successful inline article job required')
    D.require(not artifact['expired']and artifact['workflow_run']['id']==a.run_id and artifact['digest']=='sha256:'+D.digest(a.zip),'Actual immutable native ZIP/run digest differs')
    archive=root/f'article{n}-passed-output.zip';link_exact(a.zip,archive);extracted=root/'artifact-files';files=root/'files';files.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive)as z:
        names=[v for v in z.namelist()if not v.endswith('/')];D.require(len(names)==len(set(names)),'Duplicate native ZIP members')
        for member in names:
            D.relpath(member);dest=extracted/member;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():D.require(hashlib.sha256(z.read(member)).hexdigest()==D.digest(dest),'Existing extracted native original differs')
            else:dest.write_bytes(z.read(member))
    def named(basename):
        hits=[p for p in names if Path(p).name==basename];D.require(len(hits)==1,'Actual native producer member missing/ambiguous: '+basename);return hits[0]
    def by_sha(fingerprint,suffix):
        hits=[p for p in names if p.lower().endswith(suffix)and D.digest(extracted/p)==fingerprint];D.require(hits,'Actual native member SHA not found: '+fingerprint);return hits[0]
    main_member=named(n+'-status.json');main_path=extracted/main_member;main=D.load(main_path)
    D.require(main['passed']is True and main['stage']=='final4K-passed'and main['article']==n and main['first_tail_page']=='illustration'and main['illustration_frames']==main['summary_frames']==60,'This is not an actual passed native inline final')
    proof_member=named(main['illustrated_tail_verification']['file']);proof_path=extracted/proof_member;D.require(D.digest(proof_path)==main['illustrated_tail_verification']['sha256'],'Actual native inline report fingerprint differs');proof=D.load(proof_path)
    D.require(proof['passed']is True and proof['production_delivery_eligible']is True and proof['source_kind']=='new-canonical-4K'and proof['kind']=='approved-book-illustration60-then-approved-summary60'and proof['video_sha256']==main['video_sha256']and proof['output_frames']==main['output_frames'],'Actual native inline proof/media differs')
    final_member=named(main['final_video_file']);final_native=extracted/final_member;D.require(D.digest(final_native)==main['video_sha256'],'Actual native final MP4 bytes differ')
    upstream_member=by_sha(proof['upstream_status_sha256'],'.json');upstream_path=extracted/upstream_member;upstream=D.load(upstream_path)
    D.require(upstream['passed']is True and upstream['stage']=='final4K-passed'and upstream['article']==n and upstream['video_sha256']==proof['input_video_sha256'],'Actual passed upstream two-second-card provenance differs')
    old_media_member=by_sha(proof['input_video_sha256'],'.mp4');old_media=extracted/old_media_member
    copy_member=by_sha(proof['upstream_verification_sha256'],'.json');copy_path=extracted/copy_member;copy=D.load(copy_path)
    D.require(copy['video_sha256']==proof['input_video_sha256']and copy['original_audio_identical']is True and copy['original_audio_packet_timings_identical']is True,'Actual original canonical-to-native audio chain differs')
    collection_member=named(n+'-actual-source-collection.json');collection_path=extracted/collection_member;collection=D.load(collection_path)
    D.require(collection==main['actual_source_collection']and collection['article']==n,'Actual observed source collection differs from native status')
    records={}
    for role,record in collection['files'].items():
        member=named(record['file']);path=extracted/member;D.require(D.digest(path)==record['sha256'],'Actual observed source bytes differ: '+role);records[role]=(member,path)
    expected=main['request_source_sha256'];md_keys=[key for key in expected if key.startswith('新版定稿/')and key.endswith('.md')];D.require(len(md_keys)==1,'One actual requested manuscript required')
    request_names={'request_json':f'视频/脚本/{n}.json','request_generator':f'视频/工具/初稿生成/gen{n}.py','request_manuscript':md_keys[0]}
    for role,rel in request_names.items():
        member,path=records[role];D.require(D.digest(path)==expected[rel],'Collected request differs from immutable request fingerprint');link_exact(path,files/'immutable-request'/rel)
    aliases=[(upstream_path,files/f'{n}-status.json'),(records['request_json'][1],files/f'{n}-original-request.json'),(records['actual_working_source'][1],files/f'{n}-source.json'),(old_media,files/f'{n}-4K-读完即转简述2秒.mp4'),(copy_path,files/f'{n}-summary-verification.json'),(proof_path,root/f'{n}-illustrated-tail-verification.json'),(final_native,root/f'{n}-4K-正文后插图2秒-简述2秒.mp4')]
    prepared_member=by_sha(proof['illustration_preparation']['prepared_png_sha256'],'.png');aliases.append((extracted/prepared_member,root/f'{n}-插图4K.png'))
    previews=[]
    for row in proof['decoded_frame_previews']:
        member=by_sha(row['sha256'],'.jpg');path=root/'decoded-tail-previews'/Path(row['path']).name;aliases.append((extracted/member,path));previews.append({**row,'path':str(path),'original_native_member':member})
    for src,dest in aliases:link_exact(src,dest)
    extra=[main_path,collection_path,*[path for member,path in records.values()]]
    raw_qc=None
    if 'approved_audio_qc'in upstream:
        raw_member=named(n+'-approved-audio-qc.json');raw_qc=extracted/raw_member;D.require(D.load(raw_qc)==upstream['approved_audio_qc'],'Actual original acoustic report differs from native status');extra.append(raw_qc)
    differences=collection.get('source_differences')
    if differences:
        diff_path=extracted/named(differences['file']);D.require(D.digest(diff_path)==differences['sha256'],'Actual observed source-difference report differs');extra.append(diff_path)
    authorization=[extracted/member for member in names if Path(member).name==n+'-user-authorization.json'];extra.extend(authorization)
    context={'kind':'actual_native_inline_adapter_aliases_only','no_tail_added_or_video_reencoded':True,'main_status_member':main_member,'main_status_sha256':D.digest(main_path),'upstream_status_member':upstream_member,'upstream_mp4_member':old_media_member,'actual_working_source_member':records['actual_working_source'][0],'actual_working_manuscript_member':records['actual_working_manuscript'][0],'actual_working_manuscript_local':str(records['actual_working_manuscript'][1]),'dedicated_audio_qc_local':str(raw_qc)if raw_qc else None,'extra_evidence_local_files':[str(p)for p in extra],'original_native_final_member':final_member,'original_native_final_sha256':D.digest(final_native),'collector_generator_execution_observed':collection['generator_execution_observed']}
    D.write(root/'inline-adapter-context.json',context)
    dest=out/n;dest.mkdir(parents=True,exist_ok=True);D.write(out/'actual-native-run.json',run);D.write(dest/'actual-native-job.json',job);D.write(dest/'actual-native-artifact.json',artifact)
    log=dest/'actual-native-job.log'
    if not log.exists():log.write_text('')
    D.write(root/'retrieval-receipt.json',{'no':n,'artifact_id':a.artifact_id,'job_id':a.job_id,'run_id':a.run_id,'run_commit':run['head_sha'],'zip_sha256':D.digest(archive),'native_status_passed':True,'native_inline_final_original_bytes_preserved':True})
    derived=dest/'derived-source'
    if not derived.exists():derive(records['actual_working_source'][1],records['request_json'][1],records['request_generator'][1],files/'immutable-request'/md_keys[0],main_path,AUDIT/'preflight-frozen66-v2-part1/mirror/视频/工具',AUDIT/'generator_text_preflight.py',derived)
    result={'status':'actual_native_inline_final_waiting_visual_review','article':n,'final':spec(final_native),'local_final_alias':str(root/f'{n}-4K-正文后插图2秒-简述2秒.mp4'),'original_report':spec(proof_path),'decoded_frames_to_actually_view':previews,'video_reencoded_or_tail_added':False};D.write(root/'prepared-inline-section.json',result);print(json.dumps(result,ensure_ascii=False))

def finalize(a):
    n=a.article.zfill(2);root=Path(a.native_root).resolve();out=Path(a.output_root).resolve();prepared=D.load(root/'prepared-inline-section.json');review=D.load(a.boundary_review)
    D.require(review['article']==n and review['actually_visually_reviewed']is True and review['video_sha256']==prepared['final']['sha256'],'Review the actual native final boundaries')
    expected={row['sha256']for row in prepared['decoded_frames_to_actually_view']};D.require(len(expected)==5 and {row['sha256']for row in review['frames']}==expected,'Actual five native boundary frame identities differ')
    for row in prepared['decoded_frames_to_actually_view']:D.checked_file(row)
    import_one(root,n,out);D.write(out/n/'actual-boundary-frame-review.json',review)
    config=D.load(out/'actual-sample-input.json');item=config['articles'][0];record=D.load(out/n/'validated-article-record.json');context=D.load(root/'inline-adapter-context.json')
    recovering=bool(context.get('post_quality_recovery'))
    D.require(record['sha256']==(prepared['final']['sha256']if recovering else context['original_native_final_sha256']),'Actual final original/recovered bytes differ')
    snapshot=out/'code-snapshot';snapshot.mkdir(exist_ok=True);names=['delivery.py','release_contract.py','derive_final_generator.py','validate_actual_samples.py','ingest_passed_article.py','import_actual_article.py','validate_section.py','request_source_inputs.py','ingest_inline_article.py','ingest_recover_missing_illustration.py','exact057_controlled_audio.py','exact057-instrument-bindings.json','exact077_source60_audio.py','exact077-source60-instrument-binding.json','actual-approved-audio60-controlled-qc.py','actual-approved-audio60-controlled-qc-reference.json'];hashes={}
    for name in names:shutil.copyfile(B/name,snapshot/name);hashes[name]=D.digest(snapshot/name)
    D.write(snapshot/'snapshot-manifest.json',{'scope':'Exact current native-inline import/finalize code; no claim of a second rendering or new acoustic audit','sha256':hashes})
    article={'source_id':n,'new_id':record['new_id'],'passed_per_article':True,'final_mp4':item['mp4'],'canonical_source_mp4':item['canonical_mp4'],'immutable_native_zip':record['qc']['official_run']['artifact_zip'],'canonical_archive_path':record['canonical_path'],'book_order_archive_path':record['reordered_path'],'validated_record':str(out/n/'validated-article-record.json'),'section':item,'source_notes':'Native inline final preserved byte-for-byte. Original collector usedGEN/workingMD/source/request/diff and execution_observed are retained. Derived final GEN is separate and actual fullJSON-roundtripped, never relabeled as the executed generator.'}
    handoff={'status':'passed_actual_native_inline_article_for_permanent_archive','source_run':record['qc']['official_run']['run_id'],'complete70_release_validated':False,'publishing_or_remote_mutation_executed':False,'articles':[article],'report_path':str(out/'report.json'),'input_path':str(out/'actual-sample-input.json'),'validation_files':[{**spec(path),'relative_validation_path':str(path.relative_to(out))}for path in sorted(out.rglob('*'))if path.is_file()and path.name!='archive-handoff.json'],'global_approved_evidence':{k:config[k]for k in ('book_illustrations','illustration_composition_review','illustration_crop_review','video_layout_approval')},'frozen_primary_mapping_commit':config['mapping_commit'],'tool_source_sha256':hashes,'code_snapshot_path':str(snapshot),'native_root':str(root),'native_inline_final_original_bytes_preserved':True}
    if recovering:
        handoff.update(status='passed_genuine_canonical_quality_and_actual_missing_art_recovery_for_permanent_archive',native_inline_final_original_bytes_preserved=False,original_outer_job_preserved_as_failed=True,body_and_audio_reencoded=False)
        article['source_notes']='Original outer job remains failed solely for missing approved illustration. Genuine original passed canonical 4K/body/audio and all original collector sources remain immutable; local same approved helper completed illustration60 and summary60 with exact AAC/absolute timing, actual frame review and full V3 validation. Derived final GEN remains separately labeled.'
    D.write(out/'archive-handoff.json',handoff);print(json.dumps({'article':n,'status':handoff['status'],'handoff':str(out/'archive-handoff.json')},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','finalize']);p.add_argument('--article',required=True);p.add_argument('--native-root',required=True);p.add_argument('--output-root',required=True);p.add_argument('--zip');p.add_argument('--run-id',type=int);p.add_argument('--job-id',type=int);p.add_argument('--artifact-id',type=int);p.add_argument('--boundary-review');a=p.parse_args()
    if a.phase=='prepare':D.require(all(getattr(a,k)for k in('zip','run_id','job_id','artifact_id')),'Actual native ZIP/run/job/artifact identity required');prepare(a)
    else:D.require(a.boundary_review,'Actual five-frame review required');finalize(a)
