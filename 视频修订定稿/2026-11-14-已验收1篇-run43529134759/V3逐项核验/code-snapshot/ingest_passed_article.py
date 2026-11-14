#!/usr/bin/env python3
"""Passed native ZIP → unchanged illustrated-tail helper → honest V3 section.

Artifact download is via the connected GitHub tool. This local command never
changes a repository or publishes a release. Human frame review is explicit.
"""
import argparse, datetime, json, shutil, subprocess, sys, zipfile
from pathlib import Path
import delivery as D
from derive_final_generator import derive
from import_actual_article import import_one, spec

B=Path(__file__).resolve().parent
AUDIT=Path('/workspace/work/video-audit70-20261113');PAY=AUDIT/'payload';TAIL=AUDIT/'illustrated-tail'
HELPER=TAIL/'illustrated_tail.py';HELPER_SHA='dc204b91415e28297b844e9666087b0e23e67194944b359cb5fb5ddbca0f1208'

def prepare(args):
    n=args.article.zfill(2);root=Path(args.native_root).resolve();output=Path(args.output_root).resolve()
    D.require(n not in {'10','12','44','51'},'This importer is for unchanged-audio articles; use their actual dedicated acoustic report contract for repaired articles')
    D.require(D.digest(HELPER)==HELPER_SHA,'Use the actually approved frozen postprocessor')
    api=D.GitHub();repo=D.BACKUP[0];job=api.api(repo,f'actions/jobs/{args.job_id}');run=api.api(repo,f'actions/runs/{args.run_id}/attempts/{job["run_attempt"]}');art=api.api(repo,f'actions/artifacts/{args.artifact_id}')
    D.require(job['run_id']==args.run_id and job['status']=='completed'and job['conclusion']=='success'and f'({n})'in job['name'],'Actual successful article job required')
    D.require(not art['expired']and art['workflow_run']['id']==args.run_id and art['digest']=='sha256:'+D.digest(args.zip),'Actual immutable run artifact ZIP SHA differs')
    root.mkdir(parents=True,exist_ok=True);files=root/'files';files.mkdir(exist_ok=True);zip_path=root/f'article{n}-passed-output.zip'
    if Path(args.zip).resolve()!=zip_path:shutil.copyfile(args.zip,zip_path)
    with zipfile.ZipFile(zip_path)as z:
        names=[p for p in z.namelist()if not p.endswith('/')];D.require(len(names)==len(set(names)),'Duplicate ZIP members')
        native=json.loads(z.read(next(p for p in names if Path(p).name==n+'-status.json')))
        D.require(native.get('article')==n and native.get('passed')is True and native.get('stage')=='final4K-passed'and native.get('canonical_pipeline_passed')is True,'Failed candidates cannot enter this pipeline')
        dest_names=set()
        for name in names:
            D.relpath(name);base=Path(name).name
            D.require(base not in dest_names,'Ambiguous flattened artifact filenames');dest_names.add(base)
            D.require(Path(base).suffix.lower()in {'.json','.mp4','.png','.jpg','.log','.md','.py','.wav'},'Unexpected nonpublic working/cache member in producer artifact')
            (files/base).write_bytes(z.read(name))
    canonical=files/f'{n}-4K-读完即转简述2秒.mp4';D.require(D.digest(canonical)==native['video_sha256'],'Actual passed native media fingerprint differs')
    metadata=output/n;metadata.mkdir(parents=True,exist_ok=True);D.write(output/'actual-native-run.json',run);D.write(metadata/'actual-native-job.json',job);D.write(metadata/'actual-native-artifact.json',art)
    # Logs corroborate provenance if already acquired. They are not another gate.
    log=metadata/'actual-native-job.log'
    if not log.exists():log.write_text('')
    receipt={'no':n,'artifact_id':args.artifact_id,'zip_sha256':D.digest(zip_path),'run_id':args.run_id,'run_commit':run['head_sha'],'job_id':args.job_id,'native_status_passed':True,'note':'Actually successful original two-second-summary output; final illustration processing recorded separately.'};D.write(root/'retrieval-receipt.json',receipt)
    requested=files/f'{n}-original-request.json'
    expected=native['request_source_sha256'][f'视频/脚本/{n}.json']
    candidates=[p for p in files.glob('*.json')if D.digest(p)==expected]+[PAY/f'视频/脚本/{n}.json']
    chosen=next((p for p in candidates if p.is_file()and D.digest(p)==expected),None);D.require(chosen is not None,'Attach the exact immutable original request JSON, not a later source')
    if chosen.resolve()!=requested.resolve():shutil.copyfile(chosen,requested)
    derived=metadata/'derived-source'
    if not derived.exists():
        derive(files/f'{n}-source.json',requested,PAY/f'视频/工具/初稿生成/gen{n}.py',next((PAY/'新版定稿').glob(n+'-*.md')),files/f'{n}-status.json',AUDIT/'preflight-frozen66-v2-part1/mirror/视频/工具',AUDIT/'generator_text_preflight.py',derived)
    manifest=Path('/workspace/work/punk-print-20261113-v3/book-illustrations70.json');image=next(r for r in D.load(manifest)['illustrations']if r['source_id']==n)
    final=root/f'{n}-4K-正文后插图2秒-简述2秒.mp4';report=root/f'{n}-illustrated-tail-verification.json'
    command=[sys.executable,str(HELPER),'--source-id',n,'--input',str(canonical),'--verification',str(files/f'{n}-summary-verification.json'),'--illustration-manifest',str(manifest),'--order-manifest',str(AUDIT/'publication-order-manifest-readonly.json'),'--crop-review',str(TAIL/'illustration-crop-review70.json'),'--illustration',image['approved_book_illustration_path'],'--summary-image',str(files/f'{n}-简述.png'),'--layout-approval',str(TAIL/'approved-video-layouts70.json'),'--status',str(files/f'{n}-status.json'),'--source-script',str(requested),'--output',str(final),'--report',str(report),'--preview-dir',str(root/'decoded-tail-previews'),'--prepared-illustration-output',str(root/f'{n}-插图4K.png')]
    if report.exists():
        already=D.load(report);D.require(already.get('passed')is True and already.get('video_sha256')==D.digest(final),'Existing output is not a matching passed report; retain it for diagnosis')
    else:
        D.write(root/'illustrated-tail-command.json',{'argv':command,'helper_sha256':HELPER_SHA})
        with (root/'illustrated-tail.log').open('w')as log:subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
    checked=D.load(report);D.require(checked['passed']is True and checked['production_delivery_eligible']is True,'Actual illustrated-tail processing failed')
    result={'status':'actual_passed_tail_waiting_boundary_frame_review','article':n,'final':spec(final),'raw_report':spec(report),'decoded_frames_to_actually_view':checked['decoded_frame_previews'],'native_job':args.job_id,'native_artifact':args.artifact_id,'no_publication_or_repository_write':True};D.write(root/'prepared-section.json',result);print(json.dumps(result,ensure_ascii=False))

def finalize(args):
    n=args.article.zfill(2);root=Path(args.native_root).resolve();review=D.load(args.boundary_review);raw=D.load(root/f'{n}-illustrated-tail-verification.json')
    D.require(review['article']==n and review['actually_visually_reviewed']is True and review['video_sha256']==raw['video_sha256'],'Actual boundary-frame review required for this exact final media')
    expected={r['sha256']for r in raw['decoded_frame_previews']};D.require(len(expected)==5 and {r['sha256']for r in review['frames']}==expected,'Review must cover the five actual body/art/card boundary frames')
    for row in raw['decoded_frame_previews']:D.checked_file(row)
    output=Path(args.output_root).resolve();result=import_one(root,n,output)
    D.write(output/n/'actual-boundary-frame-review.json',review)
    cfg=D.load(output/'actual-sample-input.json');item=cfg['articles'][0];record=D.load(output/n/'validated-article-record.json')
    handoff={'status':'passed_actual_article_section_for_permanent_archive','source_id':n,'new_id':record['new_id'],'complete70_release_validated':False,'published_or_archived_remote':False,'section':item,'record_path':str(output/n/'validated-article-record.json'),'validation_report':str(output/'report.json'),'native_root':str(root),'validated_source_root':str(output/'final-source'),'request_source_root':str(output/'request-source'),'canonical_archive_path':record['canonical_path'],'book_order_archive_path':record['reordered_path'],'actual_frame_review':spec(output/n/'actual-boundary-frame-review.json'),'files':[{**spec(p),'validation_relative_path':str(p.relative_to(output))}for p in sorted(output.rglob('*'))if p.is_file()]}
    D.write(output/'archive-handoff.json',handoff);print(json.dumps({'status':handoff['status'],'article':n,'handoff':str(output/'archive-handoff.json')},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['prepare','finalize']);parser.add_argument('--article',required=True);parser.add_argument('--native-root',required=True);parser.add_argument('--output-root',required=True);parser.add_argument('--zip');parser.add_argument('--run-id',type=int);parser.add_argument('--job-id',type=int);parser.add_argument('--artifact-id',type=int);parser.add_argument('--boundary-review');args=parser.parse_args()
    if args.phase=='prepare':
        D.require(all(getattr(args,k)for k in('zip','run_id','job_id','artifact_id')),'prepare requires actual ZIP/run/job/artifact identity');prepare(args)
    else:D.require(args.boundary_review,'finalize requires actual reviewed-frame record');finalize(args)
