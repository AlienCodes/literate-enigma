"""Offline behavioral fixtures only. No production QC, upload, push or cleanup is executed."""
import copy, hashlib, io, json, os, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
import delivery as D
import release_actions as R
from release_contract import exact_assets,pdf_reference,tail_contract,official_job_declaration,artifact_contents,book_illustrations,canonical_audio_contract,reviewed_canonical_audio_copy
H=lambda b:hashlib.sha256(b).hexdigest()
POLICY='compact_illustrated_bilingual_vocab_summary'

def book_fixture():
    return {'edition_policy':POLICY,'count':70,'illustrations':[{'source_id':f'{i:02}','new_id':f'{i:02}','sha256':H(('native'+str(i)).encode()),'bytes':1,'native_pixel_dimensions':[1536,1024],'reused_same_approved_artwork_without_edit':True}for i in range(1,71)]}

def pdf_fixture():
    data=b'%PDF-1.7\nsynthetic compact transport fixture\n%%EOF\n';chunks=[data[:17],data[17:]]
    parts=[{'index':i+1,'repo_path':f'PDF/part{i+1:03}','bytes':len(b),'sha256':H(b)}for i,b in enumerate(chunks)]
    manifest={'release_name':'考研学人.pdf','edition_policy':POLICY,'bytes':len(data),'sha256':H(data),'parts':parts};mb=json.dumps(manifest).encode()
    approval={'status':'passed','publication_approved':True,'edition_policy':{'main_content':['70 approved illustrations','current English articles','current specified Chinese translations','focused words and whole phrases','current five-point closing summaries'],'excludes':['sentence/grammar explanations','video-note commentary sections','extra exercises and answer keys'],'source_material_preserved_for_future_analysis_volume':True},'latest_user_scope_applied':True,'pdf_bytes':len(data),'pdf_sha256':H(data)};ab=json.dumps(approval).encode()
    spec={'repository':R.REPO,'branch':'main','pinned_commit':'a'*40,'release_name':'考研学人.pdf','bytes':len(data),'sha256':H(data),'parts':parts,'edition_policy':POLICY,
          'parts_manifest':{'repo_path':'PDF/parts.json','bytes':len(mb),'sha256':H(mb)},'approval':{'repo_path':'PDF/approval.json','bytes':len(ab),'sha256':H(ab)}}
    ib=json.dumps(book_fixture()).encode();spec['illustrations_manifest']={'repo_path':'PDF/book-images.json','bytes':len(ib),'sha256':H(ib)}
    raw={'PDF/parts.json':mb,'PDF/approval.json':ab,'PDF/book-images.json':ib};streams={p['repo_path']:b for p,b in zip(parts,chunks)}
    return data,spec,raw,streams

def records_fixture(root):
    records=[]
    for i in range(1,71):
        n=f'{i:02}';data=('synthetic-video-'+n).encode();a=f'最终版4K视频/{n}.mp4';b=f'顺序重排版/视频/{n}-title.mp4'
        for name in[a,b]:p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        records.append({'id':n,'new_id':n,'canonical_path':a,'reordered_path':b,'bytes':len(data),'sha256':H(data)})
    return records

class V3Contracts(unittest.TestCase):
    def test_71_only_and_book_order(self):
        _,pdf,_,_=pdf_fixture()
        with tempfile.TemporaryDirectory()as td:
            rows=records_fixture(Path(td));assets=exact_assets(list(reversed(rows)),pdf)
            self.assertEqual(len(assets),71);self.assertEqual(assets[0]['name'],'考研学人.pdf')
            self.assertEqual([a['new_id']for a in assets[1:]],[f'{i:02}'for i in range(1,71)])
            self.assertEqual({Path(a['name']).suffix for a in assets},{'.pdf','.mp4'})
            with self.assertRaises(ValueError):exact_assets(rows[:-1],pdf)
            rows[0]['reordered_path']='顺序重排版/视频/70-wrong.mp4'
            with self.assertRaises(ValueError):exact_assets(rows,pdf)
    def test_compact_approval_and_placeholders(self):
        _,pdf,_,_=pdf_fixture();pdf_reference(pdf)
        bad=copy.deepcopy(pdf);bad['edition_policy']='799_page_analysis_draft'
        with self.assertRaises(ValueError):pdf_reference(bad)
        bad=copy.deepcopy(pdf);bad['pinned_commit']='0'*40
        with self.assertRaises(ValueError):pdf_reference(bad)
    def test_ordered_original_pdf_bytes_and_bad_part(self):
        data,pdf,raw,streams=pdf_fixture()
        def open_url(url,**kw):return io.BytesIO(streams[R.urllib.parse.unquote(url).split('/'+pdf['pinned_commit']+'/',1)[1]])
        with tempfile.TemporaryDirectory()as td,patch.object(R,'api',return_value={'status':'ahead'}),patch.object(R,'raw_primary',side_effect=lambda path,commit:raw[path]),patch.object(R.urllib.request,'urlopen',side_effect=open_url):
            dest=Path(td)/pdf['release_name'];R.download_pdf(pdf,dest);self.assertEqual(dest.read_bytes(),data)
            broken=copy.deepcopy(pdf);broken['parts'][0]['sha256']='1'*64
            with self.assertRaises(ValueError):R.download_pdf(broken,Path(td)/'bad.pdf')
            self.assertFalse((Path(td)/'.assembling-bad.pdf').exists())
    def test_lfs_pointer_rejected_even_when_declared_hash_matches(self):
        pointer=b'version https://git-lfs.github.com/spec/v1\noid sha256:abc\n';_,pdf,_,_=pdf_fixture()
        pdf.update(bytes=len(pointer),sha256=H(pointer),parts=[{'index':1,'repo_path':'PDF/pointer','bytes':len(pointer),'sha256':H(pointer)}]);pdf.pop('parts_manifest')
        approval={'status':'passed','publication_approved':True,'edition_policy':{'main_content':['70 approved illustrations','current English articles','current specified Chinese translations','focused words and whole phrases','current five-point closing summaries'],'excludes':['sentence/grammar explanations','video-note commentary sections','extra exercises and answer keys'],'source_material_preserved_for_future_analysis_volume':True},'latest_user_scope_applied':True,'pdf_bytes':len(pointer),'pdf_sha256':H(pointer)};ab=json.dumps(approval).encode();pdf['approval'].update(bytes=len(ab),sha256=H(ab))
        with tempfile.TemporaryDirectory()as td,patch.object(R,'api',return_value={'status':'identical'}),patch.object(R,'raw_primary',return_value=ab),patch.object(R.urllib.request,'urlopen',return_value=io.BytesIO(pointer)):
            with self.assertRaises(ValueError):R.download_pdf(pdf,Path(td)/'pointer.pdf')
    def test_speech_illustration_summary_timeline(self):
        video='b'*64;image='c'*64;book='d'*64;ev={'e'*64,'f'*64}
        qc={'article':'01','video_sha256':video,'actual_probe':{'frames':220},'speech_end':{'actual_new_output':True,'measured_from_actual_audio':True,'end_frame':100,'report_sha256':'e'*64},
            'illustration':{'decoded_from_actual_mp4':True,'frames':60,'start_frame':100,'width':3840,'height':2160,'approved_illustration_sha256':book,'book_source_sha256':book,
            'frame_comparison':{'status':'passed','actual_new_output':True,'decoded_from_actual_mp4':True,'frames_checked':60,'start_frame':100,'video_sha256':video,'reference_sha256':image,'report_sha256':'f'*64}},
            'summary':{'decoded_from_actual_mp4':True,'frames':60,'start_frame':160}}
        illustration={'source_id':'01','new_id':'01','approved':True,'sha256':image,'book_source_sha256':book};stills=[{'kind':'body_end','frame':99},{'kind':'illustration','frame':100},{'kind':'summary','frame':160}];row={'source_id':'01','new_id':'01','sha256':book}
        tail_contract(qc,illustration,stills,ev,row)
        for mutate in[lambda q:q['summary'].update(start_frame=100),lambda q:q['illustration'].update(frames=59),lambda q:q['illustration'].update(approved_illustration_sha256='a'*64),lambda q:q['illustration']['frame_comparison'].update(frames_checked=1)]:
            bad=copy.deepcopy(qc);mutate(bad)
            with self.assertRaises(ValueError):tail_contract(bad,illustration,stills,ev,row)
        for key,value in [('source_id','02'),('new_id','02'),('book_source_sha256','a'*64)]:
            bad=copy.deepcopy(illustration);bad[key]=value
            with self.assertRaises(ValueError):tail_contract(qc,bad,stills,ev,row)
    def test_wrapping_allowed_visible_gloss_or_audio_gain_change_rejected(self):
        source={'no':'01','gain':1,'sentences':[{'para':1,'chunks':[{'en':'A **word**.','zh':'一个**词**(word)。','align':[['A **word**.','一个**词**(word)。']],'note':'（简述：▸起点：甲。▸后续：乙。）'}]}]}
        wrapped=copy.deepcopy(source);wrapped['sentences'][0]['chunks'][0]['note']='（简述：▸起点：甲。\n▹▸后续：乙。）';D.source_invariants(source,wrapped,'01')
        bad=copy.deepcopy(source);bad['gain']=2
        with self.assertRaises(ValueError):D.source_invariants(source,bad,'01')
        bad=copy.deepcopy(source);bad['sentences'][0]['chunks'][0]['zh']+='{{新增可见解释|word}}'
        with self.assertRaises(ValueError):D.source_invariants(source,bad,'01')
    def test_original_wrap_consent_move_preserves_exact_quote_and_history(self):
        source={'no':'01','sentences':[],'换行变更已获同意':{'S1':'actual user quote'},'换行变更记录':[{'日期':'2026-11-01','S2':'older quote'}]}
        final=copy.deepcopy(source);consent=final.pop('换行变更已获同意');final['换行变更记录'].append({'日期':'2026-11-14',**consent});D.source_invariants(source,final,'01')
        final['换行变更记录'][-1]['S1']='rewritten quote'
        with self.assertRaises(ValueError):D.source_invariants(source,final,'01')
    def test_unchanged_native_audio_accepts_real_contract_but_not_repairs(self):
        status_sha='a'*64;video='b'*64;aac='c'*64
        review={'tool':'native_official_audio_gates','actual_new_output':True,'status':'passed','canonical_video_sha256':video,'report_sha256':status_sha}
        native={'article':'53','passed':True,'checks_unchanged':True,'canonical_pipeline_passed':True,'accepted_prior_aac_identical':True,'canonical_aac_adts_sha256':aac,'accepted_source':{'aac_adts_sha256':aac}}
        self.assertEqual(canonical_audio_contract(review,native,'53',video,aac,{status_sha},status_sha,False),'actual_official_audio_gates_plus_exact_accepted_AAC')
        native['checks_unchanged']=False
        self.assertEqual(canonical_audio_contract(review,native,'53',video,aac,{status_sha},status_sha,False),'actual_official_audio_gates_plus_exact_accepted_AAC')
        with self.assertRaises(ValueError):canonical_audio_contract(review,native,'53',video,aac,{status_sha},status_sha,True)
        with self.assertRaises(ValueError):canonical_audio_contract(review,native,'53',video,'d'*64,{status_sha},status_sha,False)
    def test_original_acoustic_report_keeps_raw_canonical_SHA_across_exact_audio_copy(self):
        raw_sha='a'*64;selected='b'*64;aac='c'*64;report_sha='d'*64;copy_sha='e'*64
        raw={'article':'10','passed':True,'canonical_sha256':raw_sha,'checks':[{'passed':True}]}
        native={'article':'10','passed':True,'canonical_pipeline_passed':True,'canonical_video_sha256':raw_sha,'canonical_aac_adts_sha256':aac,'approved_audio_qc':raw}
        review={'tool':'audio-qc.py','actual_new_output':True,'status':'passed','canonical_video_sha256':selected,'reviewed_canonical_video_sha256':raw_sha,'binding':'reviewed_native_pre_card_then_exact_audio_copy','report_sha256':report_sha,'copy_verification_sha256':copy_sha}
        proof={'article':'10','source_kind':'new-canonical-4K','canonical_pipeline_passed':True,'canonical_source_video_sha256':raw_sha,'video_sha256':selected,'original_audio_identical':True,'original_audio_packet_timings_identical':True,'final_canonical_aac_identical':True,'canonical_aac_adts_sha256':aac}
        self.assertEqual(canonical_audio_contract(review,native,'10',selected,aac,{report_sha,copy_sha},'f'*64,True),'actual_dedicated_audio_qc_then_verified_exact_AAC_copy')
        reviewed_canonical_audio_copy(review,native,raw,proof,'10',selected,aac)
        for key,value in [('canonical_source_video_sha256',selected),('original_audio_packet_timings_identical',False),('canonical_aac_adts_sha256','f'*64)]:
            bad=copy.deepcopy(proof);bad[key]=value
            with self.assertRaises(ValueError):reviewed_canonical_audio_copy(review,native,raw,bad,'10',selected,aac)
        bad=copy.deepcopy(raw);bad['canonical_sha256']=selected
        with self.assertRaises(ValueError):reviewed_canonical_audio_copy(review,native,bad,proof,'10',selected,aac)

class SuccessfulJobRecovery(unittest.TestCase):
    def fixture(self):
        media=b'synthetic actual canonical member';canonical=H(media);z=io.BytesIO()
        with zipfile.ZipFile(z,'w')as a:a.writestr('status.json',json.dumps({'passed':True,'stage':'final4K-passed','article':'07','video_sha256':canonical,'canonical_video_sha256':'e'*64,'canonical_pipeline_passed':True,'width':3840,'height':2160,'summary_frames':60,'summary_seconds':2}));a.writestr('07.mp4',media)
        blob=z.getvalue();digest=H(blob);run={'repository':D.PRIMARY[0],'run_id':1,'run_attempt':1,'status':'completed','conclusion':'failure','head_sha':'a'*40,'workflow_path':'.github/workflows/official.yml',
            'canonical_selection':'rechecked_native_final','artifact_id':77,'artifact_zip_sha256':digest,'artifact_zip':{'sha256':digest},'artifact_status_member':'status.json','artifact_mp4_member':'07.mp4','artifact_mp4_sha256':canonical,
            'job':{'id':2,'name':'finalize (07)','article':'07','run_attempt':1,'status':'completed','conclusion':'success','upload_step_name':'Upload final'}}
        job={'run_id':1,'run_attempt':1,'name':'finalize (07)','status':'completed','conclusion':'success','steps':[{'name':'Upload final','number':5,'status':'completed','conclusion':'success','started_at':'2026-11-13T12:00:05Z','completed_at':'2026-11-13T12:00:07Z'}]}
        class API:
            def api(self,repo,route,*args):
                if route.startswith('actions/runs/'):return {'head_sha':run['head_sha'],'path':run['workflow_path'],'conclusion':'failure'}
                if route.startswith('actions/jobs/'):return job
                return {'expired':False,'workflow_run':{'id':1},'digest':'sha256:'+digest}
            def raw_job_logs(self,*args):return '2026-11-13T12:00:05.1Z ##[group]Run actions/upload-artifact@v4\n2026-11-13T12:00:06.1Z SHA256 digest of uploaded artifact zip is '+digest+'\n2026-11-13T12:00:07.1Z Artifact final has been successfully uploaded! Artifact ID is 77'
            def raw_artifact(self,*args):return blob
        return run,canonical,job,API()
    def test_failed_matrix_successful_job_actual_artifact_accepted(self):
        run,sha,job,api=self.fixture();self.assertFalse(D.verify_remote_official_job(api,run,'07',sha)['overall_matrix_success_required'])
    def test_queued_matrix_with_actual_successful_job_is_accepted(self):
        run,sha,job,api=self.fixture();run['status']='queued';run['conclusion']=None
        self.assertEqual(official_job_declaration(run,'07',sha)['id'],job['id']if 'id'in job else 2)
    def test_pre_card_and_native_final_may_have_different_container_hashes(self):
        run,canonical,job,api=self.fixture();raw=b'original canonical before exact card';final=b'actual native final after exact card';raw_sha=H(raw);final_sha=H(final);z=io.BytesIO()
        with zipfile.ZipFile(z,'w')as f:
            f.writestr('status.json',json.dumps({'article':'07','passed':True,'stage':'final4K-passed','video_sha256':final_sha,'canonical_video_sha256':raw_sha,'canonical_pipeline_passed':True,'width':3840,'height':2160,'summary_frames':60,'summary_seconds':2}));f.writestr('canonical.mp4',raw);f.writestr('native-final.mp4',final)
        blob=z.getvalue();run.update(canonical_selection='native_pre_card',artifact_zip_sha256=H(blob),artifact_mp4_sha256=raw_sha,artifact_mp4_member='canonical.mp4',artifact_native_final_member='native-final.mp4',artifact_native_final_sha256=final_sha);run['artifact_zip']['sha256']=H(blob)
        artifact_contents(run,'07',raw_sha,blob)
        with self.assertRaises(ValueError):artifact_contents(run,'07',final_sha,blob)

    def test_wrong_or_failed_job_rejected_even_when_run_succeeds(self):
        for key,value in[('conclusion','failure'),('run_id',9),('name','finalize (08)')]:
            run,sha,job,api=self.fixture();run['conclusion']='success';job[key]=value
            with self.assertRaises(ValueError):D.verify_remote_official_job(api,run,'07',sha)
    def test_wrong_job_upload_or_artifact_payload_rejected(self):
        run,sha,job,api=self.fixture();api.raw_job_logs=lambda *a:'Artifact ID:88'
        self.assertFalse(D.verify_remote_official_job(api,run,'07',sha)['actual_job_uploaded_selected_artifact'])
        run,sha,job,api=self.fixture()
        with self.assertRaises(ValueError):artifact_contents(run,'08',sha,api.raw_artifact())
        with self.assertRaises(ValueError):artifact_contents(run,'07','f'*64,api.raw_artifact())
    def test_download_log_cannot_impersonate_selected_upload(self):
        run,sha,job,api=self.fixture();good=api.raw_job_logs();download='2026-11-13T12:00:01.1Z ##[group]Run actions/download-artifact@v4\n2026-11-13T12:00:02.1Z Artifact ID: 77\n2026-11-13T12:00:02.2Z SHA256 digest of uploaded artifact zip is '+run['artifact_zip_sha256']
        wrong=good.replace('Artifact ID is 77','Artifact ID is 88').replace(run['artifact_zip_sha256'],'b'*64)
        api.raw_job_logs=lambda *args:download+'\n'+wrong
        self.assertFalse(D.verify_remote_official_job(api,run,'07',sha)['actual_job_uploaded_selected_artifact'])
        step=job['steps'][0]
        with self.assertRaises(ValueError):D.artifact_upload_step_proof(api.raw_job_logs(),job['steps'],step,run['artifact_id'],run['artifact_zip_sha256'])
    def test_actual_github_upload_action_log_format(self):
        logs=(Path(__file__).parent/'fixtures/actual-job26-upload-log.txt').read_text();step={'name':'仅保留本篇公开成片和核验材料','number':10,'status':'completed','conclusion':'success','started_at':'2026-11-13T23:10:00Z','completed_at':'2026-11-13T23:10:01Z'}
        proof=D.artifact_upload_step_proof(logs,[step],step,14083893826,'7c4a1bd64083145f7a94a4ca2a36bc774374ef266ce44c85a0688670d179d8f1')
        self.assertTrue(proof['unambiguous_selected_step_upload'])

class Native71BuildPublish(unittest.TestCase):
    def fixture(self,root):
        data,pdf,raw,streams=pdf_fixture();records=records_fixture(root);assets=exact_assets(records,pdf);audit='视频/制作记录/fixture';inv=audit+'/release-assets.json';sums=audit+'/SHA256SUMS.txt';mp=audit+'/manifest.json'
        R.write(root/inv,{'schema_version':3,'revision':'fixture','assets':assets});(root/sums).write_text(''.join(a['sha256']+'  '+a['name']+'\n'for a in assets));R.write(root/mp,{'exact_release_assets':assets,'published_pdf':pdf})
        images=audit+'/book-illustrations70.json';(root/images).write_bytes(raw['PDF/book-images.json'])
        files={str(p.relative_to(root)):{'bytes':p.stat().st_size,'sha256':R.sha(p)}for p in root.rglob('*')if p.is_file()}
        plan={'schema_version':3,'revision':'fixture','release':{'title':'fixture','asset_policy':'book_order_70_4k_plus_pinned_book_pdf','expected_asset_count':71},'files':files,'records':records,'published_pdf':pdf,'exact_assets':assets,'book_illustrations_repo_path':images,'manifest_path':mp,'audit_path':audit,'repository_asset_inventory_path':inv,'repository_asset_inventory_sha256':R.sha(root/inv),'repository_sha256sums_path':sums,'repository_sha256sums_sha256':R.sha(root/sums),'remote_receipt_repo_path':audit+'/REMOTE.json'};R.write(root/R.PROGRAM/'release-plan.json',plan)
        return data,pdf,raw,streams,plan
    def build(self,root,out):
        data,pdf,raw,streams,plan=self.fixture(root)
        def open_url(url,**kw):return io.BytesIO(streams[R.urllib.parse.unquote(url).split('/'+pdf['pinned_commit']+'/',1)[1]])
        with patch.object(R,'api',return_value={'status':'ahead'}),patch.object(R,'raw_primary',side_effect=lambda p,c:raw[p]),patch.object(R.urllib.request,'urlopen',side_effect=open_url):R.build(root,out)
        return plan
    def test_build_exact71_no_zip_json_readme_receipt_attachment(self):
        with tempfile.TemporaryDirectory()as td:
            root=Path(td)/'root';out=Path(td)/'out';root.mkdir();plan=self.build(root,out);actual=json.loads((out/'upload-plan.json').read_text())['assets']
            self.assertEqual(actual,plan['exact_assets']);self.assertEqual(len(actual),71);self.assertFalse(any(Path(a['name']).suffix not in('.mp4','.pdf')for a in actual))
    def publish_fixture(self,extra=False):
        with tempfile.TemporaryDirectory()as td:
            root=Path(td)/'root';out=Path(td)/'out';root.mkdir();source=self.build(root,out);plan=json.loads((out/'upload-plan.json').read_text());commit='b'*40;binding='Delivery manifest SHA-256: '+plan['finalization_manifest_sha256'];release={'id':9,'draft':True,'target_commitish':commit,'body':binding,'tag_name':'fixture','html_url':'https://github.com/'+R.REPO+'/releases/tag/fixture'}
            rows=[{'name':a['name'],'id':i+1,'state':'uploaded','size':a['bytes'],'digest':'sha256:'+a['sha256'],'browser_download_url':'https://example.invalid/'+a['name']}for i,a in enumerate(plan['assets'])]
            if extra:rows.append({'name':'README.json','id':99})
            patches=[]
            def api(route,method='GET',data=None,missing_ok=False):
                if route.startswith('releases/tags/'):return release
                if '/assets?'in route:return rows
                if route=='releases/9'and method=='PATCH':patches.append(data);release['draft']=False;return release
                if route=='releases/9':return release
                if route.startswith('git/ref/tags/'):return {'object':{'type':'commit','sha':commit}}
                raise AssertionError(route)
            env={'GITHUB_REPOSITORY':R.REPO,'ASSET_COMMIT':'c'*40,'GITHUB_RUN_ID':'123','GITHUB_SHA':'d'*40,'GH_TOKEN':'fixture-not-a-real-token'}
            with patch.dict(os.environ,env),patch.object(R,'api',side_effect=api),patch.object(R,'raw_primary',return_value=(root/source['manifest_path']).read_bytes()),patch.object(R,'upload')as upload:
                if extra:
                    with self.assertRaises(ValueError):R.publish(root,out,commit)
                    self.assertEqual(patches,[]);upload.assert_not_called()
                else:
                    result=R.publish(root,out,commit);self.assertFalse(result['delivery_complete']);self.assertTrue(result['release_public']);self.assertEqual(result['verified_assets'],71)
                    receipt=json.loads((out/'REMOTE-DELIVERY-VERIFICATION.json').read_text());self.assertEqual(len(receipt['assets']),71);self.assertNotIn('REMOTE-DELIVERY-VERIFICATION.json',[a['name']for a in plan['assets']]);upload.assert_not_called()
    def test_native_publication_keeps_receipt_repository_only(self):self.publish_fixture()
    def test_extra_draft_asset_rejected_before_publication(self):self.publish_fixture(True)
    def test_cleanup_cannot_skip_backup_archive(self):
        with tempfile.TemporaryDirectory()as td:
            ack=Path(td)/'ack.json';targets=Path(td)/'targets.json';D.write(ack,{'passed':True,'delivery_complete':True,'verification_archives':[{'repository':D.PRIMARY[0],'branch':D.PRIMARY[1]}]*2});D.write(targets,[])
            with patch.object(D,'GitHub')as api:
                with self.assertRaises(ValueError):D.cleanup_old_releases(ack,targets,True)
                api.return_value.api.assert_not_called()

class ReceiptPermanence(unittest.TestCase):
    def test_unrelated_or_failed_publisher_workflow_rejected_before_git_write(self):
        with tempfile.TemporaryDirectory()as td:
            archive=Path(td)/'archive.json';proof=Path(td)/'proof.json'
            D.write(archive,{'schema_version':3,'revision':'fixture','asset_commit':'a'*40,'archives':[{'role':'primary','repository':D.PRIMARY[0],'branch':D.PRIMARY[1]},{'role':'backup','repository':D.BACKUP[0],'branch':D.BACKUP[1]}]})
            D.write(proof,{'repository':D.PRIMARY[0],'run_id':123,'artifact_id':456,'artifact_zip_sha256':'a'*64,'receipt_member':'REMOTE.json'})
            for run in[{'path':'.github/workflows/unrelated.yml','conclusion':'success'},{'path':D.WORKFLOW,'conclusion':'failure'}]:
                with patch.object(D,'GitHub')as api,patch.object(D,'commit_records')as commit:
                    api.return_value.api.return_value=run
                    with self.assertRaises(ValueError):D.persist_release_receipt(archive,proof,True)
                    commit.assert_not_called()
    def test_primary_and_backup_get_identical_actual_native_receipt(self):
        with tempfile.TemporaryDirectory()as td:
            td=Path(td);archive=td/'archive.json';proof=td/'proof.json';_,pdf,_,_=pdf_fixture();records=records_fixture(td/'records');planned=exact_assets(records,pdf)
            inv=json.dumps({'schema_version':3,'revision':'fixture','assets':planned},ensure_ascii=False,indent=2).encode()+b'\n';sums=''.join(a['sha256']+'  '+a['name']+'\n'for a in planned).encode()
            receipt={'schema_version':3,'passed':True,'release_public':True,'delivery_complete':False,'revision':'fixture','repository':D.PRIMARY[0],'release_id':9,'tag_name':'fixture','release_url':'https://github.com/'+D.PRIMARY[0]+'/releases/tag/fixture','primary_archive_commit':'b'*40,'asset_commit':'c'*40,'publisher_workflow_run_id':123,'publisher_workflow_head_sha':'d'*40,'publisher_workflow_path':D.WORKFLOW,'repository_asset_inventory_path':'audit/release-assets.json','repository_asset_inventory_sha256':H(inv),'repository_sha256sums_path':'audit/SHA256SUMS.txt','repository_sha256sums_sha256':H(sums),'remote_receipt_repo_path':'audit/REMOTE.json','audit_path':'audit'}
            rb=json.dumps(receipt).encode();z=io.BytesIO()
            with zipfile.ZipFile(z,'w')as f:f.writestr('REMOTE.json',rb)
            blob=z.getvalue();D.write(archive,{'schema_version':3,'revision':'fixture','asset_commit':'c'*40,'backup_master_expected':'e'*40,'archives':[{'role':'primary','repository':D.PRIMARY[0],'branch':D.PRIMARY[1],'commit':'b'*40},{'role':'backup','repository':D.BACKUP[0],'branch':D.BACKUP[1],'commit':'f'*40}]});D.write(proof,{'repository':D.PRIMARY[0],'run_id':123,'artifact_id':456,'artifact_zip_sha256':H(blob),'receipt_member':'REMOTE.json'})
            api=unittest.mock.Mock()
            def request(repo,route,*args):
                if route.startswith('actions/runs/'):return {'path':D.WORKFLOW,'conclusion':'success','head_sha':'d'*40}
                if route.startswith('actions/artifacts/'):return {'expired':False,'workflow_run':{'id':123},'digest':'sha256:'+H(blob)}
                return {'object':{'sha':'e'*40}}
            api.api.side_effect=request;api.raw_artifact.return_value=blob;seen=[]
            def commit(api_,repo,branch,files,message):
                seen.append((repo,branch,files));return {'repository':repo,'branch':branch,'commit':'1'*40,'blobs':{k:H(v)for k,v in files.items()},'remote_bytes_verified':True}
            with patch.object(D,'GitHub',return_value=api),patch.object(D,'verify_public_release_receipt',return_value=planned),patch.object(D,'commit_records',side_effect=commit):result=D.persist_release_receipt(archive,proof,True)
            self.assertTrue(result['delivery_complete']);self.assertEqual(len(seen),4)
            self.assertEqual({(r[0],r[1])for r in seen[:2]},{D.PRIMARY,D.BACKUP});self.assertEqual(seen[0][2]['audit/REMOTE.json'],rb);self.assertEqual(seen[1][2]['audit/REMOTE.json'],rb)
            self.assertEqual(seen[2][2],seen[3][2])
    def test_new_release_cannot_be_an_old_cleanup_target(self):
        with tempfile.TemporaryDirectory()as td:
            td=Path(td);ack=td/'ack.json';targets=td/'targets.json';rows=[{'repository':r,'branch':b,'commit':'a'*40,'blobs':{}}for r,b in(D.PRIMARY,D.BACKUP)]
            data={'revision':'new','release_id':9,'tag_name':'new','asset_commit':'b'*40,'primary_archive_commit':'c'*40,'remote_receipt_repo_path':'audit/REMOTE.json','audit_path':'audit'}
            D.write(ack,{'passed':True,'delivery_complete':True,'revision':'new','verification_archives':rows,'verification_record_path':'audit/ACK.json','verification_record_sha256':'d'*64,'receipt_archives':rows,'remote_receipt_path':'audit/REMOTE.json','remote_receipt_sha256':'e'*64,'asset_commit':'b'*40,'primary_archive_commit':'c'*40})
            D.write(targets,[{'repository':D.PRIMARY[0],'release_id':9,'tag_name':'new','html_url':'https://github.com/'+D.PRIMARY[0]+'/releases/tag/new'}])
            with patch.object(D,'GitHub')as api,patch.object(D,'verify_record_reference',return_value=json.dumps(data).encode()),patch.object(D,'verify_public_release_receipt'),patch.object(D,'commit_records')as commit:
                with self.assertRaises(ValueError):D.cleanup_old_releases(ack,targets,True)
                self.assertFalse(any(len(c.args)>2 and c.args[2]=='DELETE'for c in api.return_value.api.call_args_list));commit.assert_not_called()


if __name__=='__main__':unittest.main()
