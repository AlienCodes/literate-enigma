#!/usr/bin/env python3
"""Recover only a genuine passed canonical whose outer wrapper lacked book art.
The original outer job/report remain failed. Original 4K body/audio stay intact;
the same approved packet-preserving helper completes the two actual tail pages.
"""
import argparse, json, shutil, subprocess, sys, zipfile
from pathlib import Path
import delivery as D
from derive_final_generator import derive
from import_actual_article import spec
from ingest_inline_article import link_exact, finalize

B=Path(__file__).resolve().parent;AUDIT=Path('/workspace/work/video-audit70-20261113');TAIL=AUDIT/'illustrated-tail'
HELPER=TAIL/'illustrated_tail.py';HELPER_SHA='dc204b91415e28297b844e9666087b0e23e67194944b359cb5fb5ddbca0f1208'

def prepare(a):
    n=a.article.zfill(2);root=Path(a.native_root).resolve();out=Path(a.output_root).resolve();root.mkdir(parents=True,exist_ok=True)
    api=D.GitHub();repo=D.BACKUP[0];job=api.api(repo,f'actions/jobs/{a.job_id}');run=api.api(repo,f'actions/runs/{a.run_id}/attempts/{job["run_attempt"]}');artifact=api.api(repo,f'actions/artifacts/{a.artifact_id}')
    D.require(job['status']=='completed'and job['conclusion']=='failure'and job['run_id']==a.run_id and f'({n})'in job['name'],'Keep the actual failed outer job identity')
    D.require(not artifact['expired']and artifact['workflow_run']['id']==a.run_id and artifact['digest']=='sha256:'+D.digest(a.zip),'Actual immutable failed-outer ZIP/run digest differs')
    archive=root/f'article{n}-passed-output.zip';link_exact(a.zip,archive);extracted=root/'artifact-files';files=root/'files';files.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive)as z:
        names=[v for v in z.namelist()if not v.endswith('/')];D.require(len(names)==len(set(names)),'Duplicate immutable ZIP members')
        for member in names:
            D.relpath(member);dest=extracted/member;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():D.require(D.digest(dest)==__import__('hashlib').sha256(z.read(member)).hexdigest(),'Existing original extracted file differs')
            else:dest.write_bytes(z.read(member))
    def named(basename):
        hits=[p for p in names if Path(p).name==basename];D.require(len(hits)==1,'Original recovery member missing/ambiguous: '+basename);return hits[0]
    def by_sha(fingerprint,suffix):
        hits=[p for p in names if p.lower().endswith(suffix)and D.digest(extracted/p)==fingerprint];D.require(hits,'Original actual member fingerprint missing');return hits[0]
    outer_member=named(n+'-status.json');outer_path=extracted/outer_member;outer=D.load(outer_path)
    missing_member=named(n+'-illustrated-tail-verification.json');missing_path=extracted/missing_member
    upstream_member=named(n+'-canonical-summary-passed-status.json');upstream_path=extracted/upstream_member;upstream=D.load(upstream_path)
    media_member=by_sha(upstream['video_sha256'],'.mp4');media=extracted/media_member
    recovery={'kind':'missing-approved-illustration-after-genuine-canonical-quality-pass','original_outer_job_conclusion':'failure','artifact_outer_status_member':outer_member,'artifact_outer_status_sha256':D.digest(outer_path),'artifact_missing_illustration_report_member':missing_member,'artifact_missing_illustration_report_sha256':D.digest(missing_path)}
    identity={'run_id':a.run_id,'head_sha':run['head_sha'],'post_quality_recovery':recovery,'artifact_zip_sha256':D.digest(archive),'artifact_status_member':upstream_member,'canonical_selection':'native_final_official_passed','artifact_mp4_member':media_member}
    D.artifact_contents(identity,n,upstream['video_sha256'],archive.read_bytes())
    collection_path=extracted/named(n+'-actual-source-collection.json');collection=D.load(collection_path);D.require(collection==upstream['actual_source_collection']==outer['actual_source_collection']and collection['article']==n,'Actual production collector must match both original statuses')
    records={}
    for role,record in collection['files'].items():
        member=named(record['file']);path=extracted/member;D.require(D.digest(path)==record['sha256'],'Actual observed source differs: '+role);records[role]=(member,path)
    expected=upstream['request_source_sha256'];md_keys=[key for key in expected if key.startswith('新版定稿/')and key.endswith('.md')];D.require(len(md_keys)==1,'One immutable requested manuscript required')
    for role,rel in {'request_json':f'视频/脚本/{n}.json','request_generator':f'视频/工具/初稿生成/gen{n}.py','request_manuscript':md_keys[0]}.items():
        member,path=records[role];D.require(D.digest(path)==expected[rel],'Collected request differs from immutable request');link_exact(path,files/'immutable-request'/rel)
    copy_path=extracted/named(n+'-summary-verification.json')
    for source,target in [(upstream_path,files/f'{n}-status.json'),(records['request_json'][1],files/f'{n}-original-request.json'),(records['actual_working_source'][1],files/f'{n}-source.json'),(media,files/f'{n}-4K-读完即转简述2秒.mp4'),(copy_path,files/f'{n}-summary-verification.json')]:link_exact(source,target)
    extra=[outer_path,missing_path,upstream_path,collection_path,*[path for member,path in records.values()]]
    raw_qc=None
    if 'approved_audio_qc'in upstream:
        raw_qc=extracted/named(n+'-approved-audio-qc.json');D.require(D.load(raw_qc)==upstream['approved_audio_qc'],'Original dedicated acoustic QC differs');extra.append(raw_qc)
    diff=collection['source_differences'];diff_path=extracted/named(diff['file']);D.require(D.digest(diff_path)==diff['sha256'],'Observed source diff differs');extra.append(diff_path)
    extra.extend(extracted/member for member in names if Path(member).name==n+'-user-authorization.json')
    context={'kind':'genuine-canonical-pass-completed-after-missing-approved-artwork','post_quality_recovery':recovery,'upstream_status_member':upstream_member,'upstream_mp4_member':media_member,'actual_working_source_member':records['actual_working_source'][0],'actual_working_manuscript_member':records['actual_working_manuscript'][0],'actual_working_manuscript_local':str(records['actual_working_manuscript'][1]),'dedicated_audio_qc_local':str(raw_qc)if raw_qc else None,'extra_evidence_local_files':[str(p)for p in extra],'original_outer_status_preserved_as_failed':True,'original_upstream_4K_body_and_audio_reencoded':False}
    D.write(root/'inline-adapter-context.json',context)
    dest=out/n;dest.mkdir(parents=True,exist_ok=True);D.write(out/'actual-native-run.json',run);D.write(dest/'actual-native-job.json',job);D.write(dest/'actual-native-artifact.json',artifact)
    log=dest/'actual-native-job.log'
    if not log.exists():log.write_text('')
    D.write(root/'retrieval-receipt.json',{'no':n,'artifact_id':a.artifact_id,'job_id':a.job_id,'run_id':a.run_id,'run_commit':run['head_sha'],'zip_sha256':D.digest(archive),'original_outer_status_passed':False,'native_status_passed':True,'selected_status_scope':'genuine original canonical-summary-passed status, not failed outer wrapper','recovery':recovery})
    derived=dest/'derived-source'
    if not derived.exists():derive(records['actual_working_source'][1],records['request_json'][1],records['request_generator'][1],files/'immutable-request'/md_keys[0],upstream_path,AUDIT/'preflight-frozen66-v2-part1/mirror/视频/工具',AUDIT/'generator_text_preflight.py',derived)
    manifest=Path('/workspace/work/punk-print-20261113-v3/book-illustrations70.json');image=next(row for row in D.load(manifest)['illustrations']if row['source_id']==n)
    final=root/f'{n}-4K-正文后插图2秒-简述2秒.mp4';report=root/f'{n}-illustrated-tail-verification.json'
    command=[sys.executable,str(HELPER),'--source-id',n,'--input',str(media),'--verification',str(copy_path),'--illustration-manifest',str(manifest),'--order-manifest',str(AUDIT/'publication-order-manifest-readonly.json'),'--crop-review',str(TAIL/'illustration-crop-review70.json'),'--illustration',image['approved_book_illustration_path'],'--summary-image',str(extracted/named(n+'-简述.png')),'--layout-approval',str(TAIL/'approved-video-layouts70.json'),'--status',str(upstream_path),'--source-script',str(records['request_json'][1]),'--output',str(final),'--report',str(report),'--preview-dir',str(root/'decoded-tail-previews'),'--prepared-illustration-output',str(root/f'{n}-插图4K.png')]
    D.require(D.digest(HELPER)==HELPER_SHA,'Use the actual frozen approved postprocessor')
    if report.exists():D.require(D.load(report).get('passed')is True and D.load(report).get('video_sha256')==D.digest(final),'Retain inconsistent existing recovery output for diagnosis')
    else:
        D.write(root/'illustrated-tail-command.json',{'argv':command,'helper_sha256':HELPER_SHA,'original_outer_job_preserved_as_failed':True})
        with(root/'illustrated-tail.log').open('w')as stream:subprocess.run(command,check=True,stdout=stream,stderr=subprocess.STDOUT)
    proof=D.load(report);D.require(proof['passed']is True and proof['production_delivery_eligible']is True,'Actual recovery postprocessing failed')
    result={'status':'genuine_upstream_quality_pass_with_completed_local_tail_waiting_actual_visual_review','article':n,'final':spec(final),'local_final_alias':str(final),'original_report':spec(report),'decoded_frames_to_actually_view':proof['decoded_frame_previews'],'body_or_audio_reencoded':False,'original_outer_job_preserved_as_failed':True};D.write(root/'prepared-inline-section.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','finalize']);p.add_argument('--article',required=True);p.add_argument('--native-root',required=True);p.add_argument('--output-root',required=True);p.add_argument('--zip');p.add_argument('--run-id',type=int);p.add_argument('--job-id',type=int);p.add_argument('--artifact-id',type=int);p.add_argument('--boundary-review');a=p.parse_args()
    if a.phase=='prepare':D.require(all(getattr(a,k)for k in('zip','run_id','job_id','artifact_id')),'Actual original artifact identity required');prepare(a)
    else:D.require(a.boundary_review,'Actual reviewed boundary frames required');finalize(a)
