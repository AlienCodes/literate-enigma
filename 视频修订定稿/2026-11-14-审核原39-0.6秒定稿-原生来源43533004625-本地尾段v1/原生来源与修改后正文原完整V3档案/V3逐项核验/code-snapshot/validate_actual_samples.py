#!/usr/bin/env python3
"""Validate the two actual passed native artifacts and real illustrated tails.

This is a per-article import/QC check. It cannot build, archive or publish a
partial release and does not pretend that the remaining68 articles passed.
"""
import datetime, hashlib, json, shutil, zipfile
from pathlib import Path
import delivery as D
from release_contract import book_illustrations

B=Path(__file__).resolve().parent
ACTUAL=Path('/workspace/work/video-audit70-20261113/actual-passed-43523430839')
AUDIT=Path('/workspace/work/video-audit70-20261113')
TAIL=AUDIT/'illustrated-tail';PAY=AUDIT/'payload'
OUT=B/'actual53-64-validation'
BOOK=Path('/workspace/work/punk-print-20261113-v4-compact/archive-payload/考研学人印刷版/2026-11-13-v4/核验/book-illustrations70.json')

def spec(path):
    p=Path(path);return {'path':str(p),'bytes':p.stat().st_size,'sha256':D.digest(p)}

def summary_text(source):
    found=[]
    for sentence in source['sentences']:
        for chunk in sentence['chunks']:
            text=chunk.get('note','');start=text.find('（简述：')
            if start<0:continue
            depth=0
            for end in range(start,len(text)):
                depth+=(text[end]=='（')-(text[end]=='）')
                if depth==0:found.append(text[start:end+1]);break
    D.require(len(found)==1,'Expected unique actual five-point summary')
    return found[0]

def main():
    config={'request_source_root':str(OUT/'request-source'),'final_source_root':str(OUT/'final-source'),
            'catalog_path':str(OUT/'frozen-primary/来源视频清单.json'),'order_map_path':str(OUT/'frozen-primary/篇号对照.json'),
            'book_illustrations':spec(BOOK),'illustration_composition_review':spec(TAIL/'composition-qc70.json'),
            'illustration_crop_review':spec(TAIL/'illustration-crop-review70.json'),'video_layout_approval':spec(TAIL/'approved-video-layouts70.json'),
            'source_derivation':{'factory':spec(AUDIT/'generator_text_preflight.py'),'original_tools_root':str(AUDIT/'preflight-frozen66-v2-part1/mirror/视频/工具')},'articles':[]}
    # Mapping was actually fetched from this immutable primary commit via the
    # GitHub connector; no fabricated paths/order are inferred from filenames.
    config['mapping_commit']='8404ddff99dfa094aa005fec70643d9da55e21fc'
    _,order,old,reorder=D.mapping(config);images=book_illustrations(D.load(BOOK),order['rows'])
    compositions=D.load(TAIL/'composition-qc70.json');crops=D.load(TAIL/'illustration-crop-review70.json');layouts=D.load(TAIL/'approved-video-layouts70.json')
    compose={r['source_id']:r for r in compositions['articles']};crop={r['source_id']:r for r in crops['articles']};layout={r['source_id']:r for r in layouts['articles']}
    observed_run=D.load(OUT/'actual-native-run.json');validated=[]
    for n in ('53','64'):
        root=ACTUAL/n;files=root/'files';dest=OUT/n
        native=D.load(files/f'{n}-status.json');report_path=root/f'{n}-illustrated-tail-verification.json';report=D.load(report_path)
        retrieval=D.load(root/'retrieval-receipt.json');job=D.load(dest/'actual-native-job.json');artifact=D.load(dest/'actual-native-artifact.json')
        zip_path=root/f'article{n}-passed-output.zip';canonical=files/f'{n}-4K-读完即转简述2秒.mp4';final=root/f'{n}-4K-正文后插图2秒-简述2秒.mp4'
        with zipfile.ZipFile(zip_path)as z:
            status_member=next(p for p in z.namelist()if Path(p).name==n+'-status.json')
            source_member=next(p for p in z.namelist()if Path(p).name==n+'-source.json')
            media_member=next(p for p in z.namelist()if Path(p).name==canonical.name)
        upload_step=next(step for step in job['steps']if '仅保留本篇' in step['name'])
        run={'repository':D.BACKUP[0],'run_id':retrieval['run_id'],'run_attempt':job['run_attempt'],'status':observed_run['status'],'conclusion':observed_run['conclusion'],'head_sha':observed_run['head_sha'],'workflow_path':observed_run['path'],'entrypoint':'视频/工具/新管/定稿.sh','stage':'4K',
             'canonical_selection':'native_final_official_passed','artifact_id':retrieval['artifact_id'],'artifact_zip':spec(zip_path),'artifact_zip_sha256':retrieval['zip_sha256'],'artifact_status_member':status_member,'artifact_mp4_member':media_member,'artifact_mp4_sha256':D.digest(canonical),
             'job':{'id':job['id'],'name':job['name'],'article':n,'run_attempt':job['run_attempt'],'status':job['status'],'conclusion':job['conclusion'],'upload_step_name':upload_step['name']}}
        class ActualAcquiredEvidence:
            def api(self,repository,route):
                D.require(repository==D.BACKUP[0],'Unexpected repository')
                if route.startswith('actions/runs/'):return observed_run
                if route.startswith('actions/jobs/'):return job
                if route.startswith('actions/artifacts/'):return artifact
                raise ValueError(route)
            def raw_job_logs(self,*args):return (dest/'actual-native-job.log').read_text()
            def raw_artifact(self,*args):return zip_path.read_bytes()
        observed=D.verify_remote_official_job(ActualAcquiredEvidence(),run,n,D.digest(canonical))
        D.write(dest/'actual-job-artifact-binding.json',{k:v for k,v in observed.items()if not k.startswith('_')})
        request_files={'json':files/f'{n}-original-request.json','gen':PAY/f'视频/工具/初稿生成/gen{n}.py','md':next((PAY/'新版定稿').glob(n+'-*.md'))}
        names={'json':f'视频/脚本/{n}.json','gen':f'视频/工具/初稿生成/gen{n}.py','md':'新版定稿/'+request_files['md'].name}
        final_files={'json':files/f'{n}-source.json','gen':dest/f'derived-source/gen{n}.py','md':request_files['md']}
        proof=spec(dest/'derived-source/derived-source-proof.json');asked={};sources={}
        for kind,path in request_files.items():
            target=OUT/'request-source'/names[kind];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);asked[kind]={**spec(target),'path':names[kind]}
        for kind,path in final_files.items():
            target=OUT/'final-source'/names[kind];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);entry={**spec(target),'path':names[kind]}
            if kind=='json':entry.update(origin='official_artifact_working_copy',artifact_id=run['artifact_id'],artifact_member=source_member)
            else:entry.update(origin='derived_after_final_QC'if kind=='gen'else'request_manuscript_with_verified_final_source_equivalence',derived_from_json_sha256=D.digest(final_files['json']),derivation_proof=proof)
            sources[kind]=entry
        native_audio=D.actual_aac(canonical);final_audio=D.actual_aac(final)
        D.write(dest/'actual-lossless-packet-proof.json',{'canonical':native_audio,'final':final_audio})
        raw_source=D.load(final_files['json']);provenance=D.load(proof['path']);end=report['body_frames']
        evidence=[spec(report_path),spec(files/f'{n}-status.json'),spec(files/f'{n}-summary-verification.json'),proof,spec(dest/'actual-lossless-packet-proof.json'),spec(dest/'actual-job-artifact-binding.json'),spec(dest/'actual-native-job.log')]
        image={'source_id':n,'new_id':images[n]['new_id'],'approved':True,'book_source_sha256':images[n]['sha256'],**spec(root/f'{n}-插图4K.png'),'native_source':spec(images[n]['approved_book_illustration_path'])}
        stills=[{**spec(row['path']),'kind':'body_end'if row['label']=='body-last'else('illustration'if row['label'].startswith('illustration')else'summary'),'frame':row['frame'],'video_sha256':D.digest(final),'decoded_from_actual_mp4':True}for row in report['decoded_frame_previews']]
        chain={'canonical_video_sha256':D.digest(canonical),'final_video_sha256':D.digest(final),'audio_packet_times_identical':report['aac_packet_payload_and_absolute_timings_identical']}
        for role,audio in [('canonical',native_audio),('final',final_audio)]:
            for key in ('aac_adts_sha256','packet_projection_sha256','packet_count'):chain[role+'_'+key]=audio[key]
        qc={'article':n,'status':'passed'if report['passed']and report['production_delivery_eligible']else'failed','actual_new_mp4':report['source_kind']=='new-canonical-4K','video_sha256':D.digest(final),'video_bytes':final.stat().st_size,'official_run':run,'actual_probe':D.probe(final),
            'speech_end':{'actual_new_output':True,'measured_from_actual_audio':True,'end_frame':end,'report_sha256':D.digest(files/f'{n}-summary-verification.json')},
            'illustration':{'decoded_from_actual_mp4':True,'frames':report['illustration_frames'],'start_frame':report['illustration_start_frame'],'width':3840,'height':2160,'approved_illustration_sha256':report['approved_illustration_sha256'],'book_source_sha256':images[n]['sha256'],'preparation':report['illustration_preparation'],
                            'frame_comparison':{'status':'passed'if report['passed']else'failed','actual_new_output':True,'decoded_from_actual_mp4':True,'frames_checked':report['illustration_frames_checked'],'start_frame':end,'video_sha256':report['video_sha256'],'reference_sha256':image['sha256'],'report_sha256':D.digest(report_path)}},
            'summary':{'decoded_from_actual_mp4':True,'frames':report['summary_frames'],'start_frame':report['summary_start_frame'],'overflow':False,'normal_font_size':True,'font_px':layout[n]['summary_font_4k_px'],'text_sha256':hashlib.sha256(summary_text(raw_source).encode()).hexdigest(),'approved_request_text_sha256':layout[n]['approved_summary_text_sha256']},
            'audio':{'canonical_qc':{'tool':'native_official_audio_gates','actual_new_output':True,'status':'passed','canonical_video_sha256':D.digest(canonical),'report_sha256':D.digest(files/f'{n}-status.json')},'repair_applied':False,'lossless_copy':chain},
            'source_sha256':{'request':{k:v['sha256']for k,v in asked.items()},'final':{k:v['sha256']for k,v in sources.items()}},
            'source_transform':{'status':provenance['status'],'actual_working_copy':True,'operations':['L19']+(['production_qc_metadata']if n=='53'else[]),'report_sha256':proof['sha256'],'changed_paths':provenance['changed_paths']},
            'adapter_scope':'Explicit actual native status + raw real postprocessor report field mapping; not fabricated audio-qc.py or unobserved runtime GEN/MD.'}
        D.write(dest/'actual-qc-v3.json',qc)
        item={'id':n,'mp4':spec(final),'canonical_mp4':spec(canonical),'qc':spec(dest/'actual-qc-v3.json'),'request_source':asked,'final_source':sources,'illustration':image,'stills':stills,'evidence':evidence}
        config['articles'].append(item)
        record=D.validate_article(config,item,old,reorder,images,compose,crop,{'10','12','51'})
        D.write(dest/'validated-article-record.json',record)
        validated.append({'id':n,'new_id':record['new_id'],'passed_per_article':True,'bytes':record['bytes'],'sha256':record['sha256'],'actual_aac_packet_count':record['actual_audio_chain']['packet_count'],'canonical_audio_basis':record['canonical_audio_acceptance_basis'],'whole_actual_final_JSON_GEN_roundtrip':True})
        print(json.dumps(validated[-1],ensure_ascii=False),flush=True)
    D.write(OUT/'actual-sample-input.json',config)
    result={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_actual_two_article_interface_only','actual_articles':validated,'complete70_release_validated':False,'remaining_articles_not_claimed_passed':68,'published_or_archived_remote':False,'native_job_metadata_actually_acquired_from_GitHub':True,'raw_job_logs_actually_acquired_from_GitHub':True,'original_actual_ZIP_digests_rechecked':True}
    D.write(OUT/'report.json',result);return result

if __name__=='__main__':main()
