"""Pure V3 delivery contracts. No network or mutation at import."""
import hashlib, json, re, zipfile
from pathlib import Path, PurePosixPath
PRIMARY = 'alienalgorithm/postgraduate-vocabulary'
BACKUP = 'AlienCodes/literate-enigma'
BACKUP_BRANCH = 'codex/all-deliverables-20261113'
ASSET_POLICY = 'book_order_70_4k_plus_pinned_book_pdf'
HEX40 = re.compile(r'^[0-9a-f]{40}$'); HEX64 = re.compile(r'^[0-9a-f]{64}$')
MAX_ASSET = 2_000_000_000

def require(ok, message):
    if not ok: raise ValueError(message)

def safe_path(value):
    require(isinstance(value,str) and value and '\\' not in value,'Invalid repository/member path')
    p=PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '.' not in p.parts,'Unsafe repository/member path')
    return value

def pdf_reference(spec):
    require(spec['repository']==PRIMARY and spec['branch']=='main','PDF parts must be frozen from primary main')
    require(spec['edition_policy']=='compact_illustrated_bilingual_vocab_summary','Only current compact main-book policy is authorized')
    for field in ('approval','illustrations_manifest'):
        approval=spec[field];safe_path(approval['repo_path']);require(approval['bytes']>0 and HEX64.fullmatch(approval['sha256'])is not None,'Actual frozen PDF approval/book-illustration record required')
    require(HEX40.fullmatch(spec['pinned_commit']) is not None,'PDF commit must be immutable')
    name=spec['release_name'];require(Path(name).name==name and name=='考研学人.pdf','Use the user-specified single complete PDF name')
    require(isinstance(spec['bytes'],int) and 0<spec['bytes']<MAX_ASSET and HEX64.fullmatch(spec['sha256']) is not None,'Complete PDF byte count/SHA required')
    parts=spec['parts'];require(isinstance(parts,list) and parts and len({p['repo_path']for p in parts})==len(parts),'Ordered unique PDF byte parts required')
    for part in parts:
        safe_path(part['repo_path']);require(isinstance(part['bytes'],int)and 0<part['bytes']<=90*1024*1024 and HEX64.fullmatch(part['sha256'])is not None,'PDF part exceeds90MiB or lacks exact bytes/SHA')
    require(sum(p['bytes']for p in parts)==spec['bytes'],'PDF part sizes do not sum to exact full bytes')
    if any('index'in p for p in parts):require([p.get('index')for p in parts]==list(range(1,len(parts)+1)),'PDF part indices/order differ')
    require(spec['pinned_commit']!='0'*40 and spec['sha256']!='0'*64,'Unfilled PDF placeholders rejected')
    if 'parts_manifest'in spec:
        m=spec['parts_manifest'];safe_path(m['repo_path']);require(m['bytes']>0 and HEX64.fullmatch(m['sha256'])is not None,'Frozen parts-manifest size/SHA required')
    return spec

def approved_compact_pdf(spec,approval):
    require(approval['status']=='passed'and approval['publication_approved']is True and approval['pdf_sha256']==spec['sha256']and approval['pdf_bytes']==spec['bytes'],'PDF is not actual approved current compact edition')
    policy=approval['edition_policy']
    require(isinstance(policy,dict)and approval.get('latest_user_scope_applied')is True,'Actual root compact-content approval required')
    require(set(policy['main_content'])=={'70 approved illustrations','current English articles','current specified Chinese translations','focused words and whole phrases','current five-point closing summaries'},'Main book includes unapproved analysis/content')
    require(set(policy['excludes'])>={'sentence/grammar explanations','video-note commentary sections','extra exercises and answer keys'},'Compact main-book exclusions not explicit')
    require(policy.get('source_material_preserved_for_future_analysis_volume')is True,'Detailed source analysis records must be preserved separately')
    if 'pages'in spec:require(approval['pages']==spec['pages'],'Approved actual page count differs')
    return True

def book_illustrations(data, order_rows=None):
    """Actual book map, keyed by original article; approved artwork is not interchangeable."""
    ids={f'{i:02}'for i in range(1,71)};rows=data['illustrations']
    require(data['edition_policy']=='compact_illustrated_bilingual_vocab_summary' and data['count']==len(rows)==70,'Actual current70 book illustrations required')
    require({r['source_id']for r in rows}=={r['new_id']for r in rows}==ids and len({r['source_id']for r in rows})==70,'Book illustration source/order mapping must be a bijection')
    for row in rows:
        require(HEX64.fullmatch(row['sha256'])is not None and row['bytes']>0 and row['native_pixel_dimensions']==[1536,1024] and row['reused_same_approved_artwork_without_edit']is True,'Actual approved native book artwork identity/dimensions required')
    by_id={r['source_id']:r for r in rows}
    if order_rows is not None:
        require({r['source_id']:r['new_id']for r in order_rows}=={k:v['new_id']for k,v in by_id.items()},'Video order differs from frozen approved book illustration order')
    return by_id

def exact_assets(records,pdf):
    pdf_reference(pdf);require(len(records)==70,'Exactly70 new video records required')
    ids={f'{i:02}'for i in range(1,71)}
    require({r['id']for r in records}=={r['new_id']for r in records}==ids,'Source/book order must be a bijection')
    assets=[{'kind':'pdf','name':pdf['release_name'],'bytes':pdf['bytes'],'sha256':pdf['sha256']}]
    for r in sorted(records,key=lambda r:int(r['new_id'])):
        name=PurePosixPath(safe_path(r['reordered_path'])).name
        require(re.match(re.escape(r['new_id'])+r'(?:-| )',name)is not None and name.lower().endswith('.mp4'),'Video name must carry exact existing book-order prefix')
        require(isinstance(r['bytes'],int)and 0<r['bytes']<MAX_ASSET and HEX64.fullmatch(r['sha256'])is not None,'Actual video size/SHA required')
        assets.append({'kind':'video','id':r['id'],'new_id':r['new_id'],'name':name,'bytes':r['bytes'],'sha256':r['sha256']})
    require(len(assets)==len({a['name']for a in assets})==71,'Exactly71 distinct assets required')
    return assets

def official_job_declaration(run,article,canonical_sha):
    require(run['repository']in(PRIMARY,BACKUP),'Unexpected official repository')
    # GitHub may report queued for a matrix that already contains completed
    # successful jobs. The actual article job is decisive; overall run state
    # and conclusion are retained as evidence, never another delivery gate.
    require(isinstance(run['run_attempt'],int)and run['run_attempt']>0,'Actual run attempt required')
    job=run['job'];require(isinstance(job['id'],int)and job['id']>0,'Actual job ID required')
    require(job['article']==article and job['status']=='completed'and job['conclusion']=='success'and job['name']and job['upload_step_name'],'Only the actual successful article job is accepted')
    require(job['run_attempt']==run['run_attempt'],'Job/run attempt mismatch')
    require(run['artifact_zip']['sha256']==run['artifact_zip_sha256'],'Local artifact ZIP identity mismatch')
    safe_path(run['artifact_status_member']);safe_path(run['artifact_mp4_member'])
    require(run['canonical_selection']in('native_pre_card','rechecked_native_final','native_final_official_passed'),'Choose actual canonical provenance explicitly, never infer from a filename')
    require(run['artifact_mp4_sha256']==canonical_sha,'Selected actual canonical MP4 fingerprint mismatch')
    if run['canonical_selection']=='native_pre_card':safe_path(run['artifact_native_final_member']);require(HEX64.fullmatch(run['artifact_native_final_sha256'])is not None,'Native final member/SHA required alongside pre-card canonical')
    return job

def artifact_contents(run,article,canonical_sha,blob):
    """Verify actual immutable ZIP members; status is not inferred from matrix success."""
    require(hashlib.sha256(blob).hexdigest()==run['artifact_zip_sha256'],'Actual artifact ZIP SHA mismatch')
    import io
    with zipfile.ZipFile(io.BytesIO(blob))as z:
        require(len(z.namelist())==len(set(z.namelist())),'Duplicate ZIP members')
        for name in z.namelist():safe_path(name.rstrip('/'))
        status=json.loads(z.read(run['artifact_status_member']))
        require(status.get('passed')is True and status.get('stage')=='final4K-passed'and status.get('article')==article and status.get('canonical_pipeline_passed')is True and (status.get('width'),status.get('height'))==(3840,2160) and status.get('summary_frames')==60 and status.get('summary_seconds')==2,'Native producer artifact is not actual passed final4K for this article')
        if run['canonical_selection']=='native_pre_card':
            require(status.get('canonical_video_sha256')==canonical_sha and status.get('video_sha256')==run['artifact_native_final_sha256'],'Raw canonical/native final identities differ')
            require(run['artifact_native_final_member']in z.namelist(),'Actual native final member missing')
            h=hashlib.sha256()
            with z.open(run['artifact_native_final_member'])as f:
                for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
            require(h.hexdigest()==run['artifact_native_final_sha256'],'Actual native final member SHA mismatch')
        else:require(status.get('video_sha256')==canonical_sha,'Rechecked canonical must be actual passed native final MP4')
        require(run['artifact_mp4_member']in z.namelist(),'Selected canonical member missing; cannot fabricate original working media')
        h=hashlib.sha256()
        with z.open(run['artifact_mp4_member'])as f:
            for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
        require(h.hexdigest()==canonical_sha,'Actual artifact MP4 member SHA mismatch')
    return status

def canonical_audio_contract(review,native,article,selected_sha,actual_aac_sha,evidence_hashes,status_sha,strict_review):
    require(review['actual_new_output']is True and review['status']=='passed'and review['canonical_video_sha256']==selected_sha and review['report_sha256']in evidence_hashes,'Canonical audio review identity/evidence differs')
    if strict_review:
        require(review['tool']=='audio-qc.py','Acoustic repairs and10/12/44/51 require actual dedicated MP4 acoustic QC')
        return 'actual_dedicated_audio_qc'
    require(review['tool']=='native_official_audio_gates','Unchanged audio must use the actual official gates contract, not a fabricated audio-qc.py report')
    # Approved repairs to reference reproducibility or factual diagnostic
    # defects have their actual source SHAs in the pinned producer records.
    # Do not turn the old blanket checks_unchanged flag into a delivery gate or
    # falsely overwrite it; acceptance remains actual passed sound/media.
    require(review['report_sha256']==status_sha and native.get('canonical_pipeline_passed')is True and native.get('passed')is True,'Actual complete approved audio pipeline did not pass')
    require(native.get('article')==article and native.get('accepted_prior_aac_identical')is True,'Native prior voice comparison did not actually pass')
    require(native.get('canonical_aac_adts_sha256')==native.get('accepted_source',{}).get('aac_adts_sha256')==actual_aac_sha,'Actual current canonical AAC differs from the native accepted voice proof')
    return 'actual_official_audio_gates_plus_exact_accepted_AAC'

def tail_contract(qc,illustration,stills,evidence_hashes,book_row):
    speech=qc['speech_end'];art=qc['illustration'];summary=qc['summary'];total=qc['actual_probe']['frames']
    require(speech['actual_new_output']is True and speech['measured_from_actual_audio']is True and speech['report_sha256']in evidence_hashes,'Actual narration-end evidence required')
    start=speech['end_frame'];require(isinstance(start,int)and start>0,'Actual speech-end frame required')
    require(qc['article']==illustration['source_id']==book_row['source_id'] and illustration['new_id']==book_row['new_id'],'Illustration belongs to a different article/book-order entry')
    require(illustration['approved']is True and illustration['book_source_sha256']==book_row['sha256'],'Illustration does not match this exact article in the frozen approved book map')
    require(art['decoded_from_actual_mp4']is True and art['frames']==60 and art['start_frame']==start,'Illustration must immediately follow real narration for60 frames')
    require((art['width'],art['height'])==(3840,2160)and art['approved_illustration_sha256']==book_row['sha256']and art['book_source_sha256']==illustration['book_source_sha256'],'Actual4K illustration/native source SHA mismatch')
    compare=art['frame_comparison'];require(compare['status']=='passed'and compare['actual_new_output']is True and compare['decoded_from_actual_mp4']is True and compare['frames_checked']==60 and compare['start_frame']==start and compare['video_sha256']==qc['video_sha256']and compare['reference_sha256']==illustration['sha256']and compare['report_sha256']in evidence_hashes,'Actual60-frame illustration comparison report required')
    require(summary['decoded_from_actual_mp4']is True and summary['frames']==60 and summary['start_frame']==start+60 and summary['start_frame']+60==total,'Tail must be speech→60 illustration→60 summary→end')
    require({s['kind']for s in stills}>={'body_end','illustration','summary'},'Actual body/illustration/card stills required')
    for s in stills:
        if s['kind']=='body_end':require(0<=s['frame']<start,'Body still after speech end')
        if s['kind']=='illustration':require(start<=s['frame']<start+60,'Illustration still outside actual illustration interval')
        if s['kind']=='summary':require(start+60<=s['frame']<total,'Summary still outside final card')
    return {'speech_end_frame':start,'illustration_frames':60,'summary_frames':60,'approved_illustration_sha256':illustration['sha256']}
