"""Pure V3 delivery contracts. No network or mutation at import."""
import hashlib, json, re, zipfile
from exact057_controlled_audio import actual_exact057_repair_scope
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

def post_quality_missing_art_recovery(run,article):
    recovery=run.get('post_quality_recovery')
    if recovery is None:return False
    require(run['run_id']==43538347790 and run['head_sha']=='e558509b9bfb09fa869511c09a54be9a156b1471' and article in {'10','11','12','51','42'},'Unapproved outer-failure recovery scope')
    require(recovery['kind']=='missing-approved-illustration-after-genuine-canonical-quality-pass' and recovery['original_outer_job_conclusion']=='failure','Do not relabel the failed outer job as successful')
    for key in ('artifact_outer_status_member','artifact_missing_illustration_report_member'):safe_path(recovery[key])
    for key in ('artifact_outer_status_sha256','artifact_missing_illustration_report_sha256'):require(HEX64.fullmatch(recovery[key])is not None,'Actual recovery original member SHA required')
    return True

def official_job_declaration(run,article,canonical_sha):
    require(run['repository']in(PRIMARY,BACKUP),'Unexpected official repository')
    # GitHub may report queued for a matrix that already contains completed
    # successful jobs. The actual article job is decisive; overall run state
    # and conclusion are retained as evidence, never another delivery gate.
    require(isinstance(run['run_attempt'],int)and run['run_attempt']>0,'Actual run attempt required')
    job=run['job'];require(isinstance(job['id'],int)and job['id']>0,'Actual job ID required')
    recovering=post_quality_missing_art_recovery(run,article)
    require(job['article']==article and job['status']=='completed'and job['conclusion']==('failure'if recovering else'success')and job['name']and job['upload_step_name'],'Actual successful article job or exact authorized missing-art recovery required')
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
        if post_quality_missing_art_recovery(run,article):
            recovery=run['post_quality_recovery'];outer_bytes=z.read(recovery['artifact_outer_status_member']);missing_bytes=z.read(recovery['artifact_missing_illustration_report_member'])
            require(hashlib.sha256(outer_bytes).hexdigest()==recovery['artifact_outer_status_sha256']and hashlib.sha256(missing_bytes).hexdigest()==recovery['artifact_missing_illustration_report_sha256'],'Original failed outer/report bytes differ')
            outer=json.loads(outer_bytes);missing=json.loads(missing_bytes)
            require(outer['article']==article and outer['passed']is False and outer['stage']=='approved-illustrated-tail.log'and outer['canonical_pipeline_passed']is True and outer['video_sha256']==canonical_sha and outer['error']=='approved-illustrated-tail.log: exit 1','Outer failure was not strictly after genuine passed canonical quality')
            require(missing['article']==article and missing['passed']is False and missing['production_delivery_eligible']is False and missing['postprocessor_sha256']=='dc204b91415e28297b844e9666087b0e23e67194944b359cb5fb5ddbca0f1208'and missing['kind']=='approved-book-illustration60-then-approved-summary60'and missing['body_reencoded_frames']==missing['audio_reencoded_or_added_packets']==0,'Original postprocessor failure did not preserve genuine passed body/audio')
            require(missing['error']=="[Errno 2] No such file or directory: '/home/runner/work/literate-enigma/literate-enigma/插图阅读小册/illustrations/"+article+".png'",'Original failure was not the explicitly diagnosed missing approved artwork')
        require(run['artifact_mp4_member']in z.namelist(),'Selected canonical member missing; cannot fabricate original working media')
        h=hashlib.sha256()
        with z.open(run['artifact_mp4_member'])as f:
            for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
        require(h.hexdigest()==canonical_sha,'Actual artifact MP4 member SHA mismatch')
    return status

def actual_A21_repair_scope(review, native, raw_audio, article):
    """Truthful adapter for the already approved, actually run A21 instrument.

    This validates the actual native report contract. It neither changes an
    acoustic threshold nor asks a repaired voice to equal the old damaged one.
    """
    requests = {
        '15': '181b21b9d960292284ce34ed7cdf56b0ce3592b255b7480941c5924aaf713b33',
        '17': '8e16bf3ed5e7ea22fa7442b592fc8b68848c0097732d8d3633535817aa4c4244',
        '18': '5192b78e582c36fd7d5a34973d8314c5b23e13b8313c8960ac29653bd7fa5d8c',
        '30': '34eb48747f1ea7d14b41ccc0cf45aa1592907aacf6618999b3506944e2ff4a0c'}
    require(article in requests, 'A21 repair scope is limited to the four actually approved requests')
    program = '4bd358eb6d78e755a9d88ba55bc07dca99c814f84b9b1153061d8bed8fd43e55'
    reference = '1af4157360a0266eb23c5f072ced0184b412bed344b94e10170b3698a8d67635'
    scope = native.get('approved_audio_repair_scope', {})
    require(scope.get('kind') == 'one-root-approved-original-release-instead-of-grafted-release' and
            scope.get('original_A21_five_phase_checks_required') is True and
            scope.get('untouched_voice_waveform_level_pitch_and_controls_required') is True,
            'Actual approved original-release repair scope absent')
    require(scope.get('request_source_sha256') == requests[article] == review.get('request_source_sha256') ==
            native['request_source_sha256'].get('视频/脚本/' + article + '.json'), 'A21 request differs from the exact approved reference')
    require(scope.get('reference_file_sha256') == reference == raw_audio.get('reference_file_sha256') ==
            review.get('reference_file_sha256'), 'A21 actual reference differs from the approved file')
    require(program == native.get('approved_audio_qc_program_sha256') == raw_audio.get('program_sha256') ==
            review.get('program_sha256'), 'Actual A21 QC program identity differs')
    require(native.get('canonical_pipeline_passed') is True and native.get('passed') is True and
            native.get('approved_audio_qc') == raw_audio and raw_audio.get('article') == article and
            raw_audio.get('passed') is True, 'Actual complete original pipeline/A21 report not passed')
    require(raw_audio.get('original_official_sound_gates_modified') is False and
            raw_audio.get('private_GT_cache_or_raw_producer_PCM_read') is False and
            raw_audio.get('original_A21_program_sha256') ==
            'b479569558f2867f59014e26384d190690df509383b6c3dbf6bab30d15a2f19e',
            'A21 report is not the approved actual public-MP4/original-function measurement')
    checks = raw_audio.get('checks', [])
    require(checks and all(c.get('passed') is True for c in checks), 'Actual A21 repair has failed checks')
    by_name = {c['name']: c for c in checks}
    require(len(by_name) == len(checks) and {
        'accepted-original-duplicate-reproduced', 'exact-root-approved-request-source-sha256',
        'all-approved-request-audio-controls-exact', 'actual-working-all-approved-audio-controls-exact',
        'actual-working-old-donor-removed', 'actual-working-approved-original-boost-exact',
        'whole-track-level-preserved', 'every-untouched-whole-sentence-preserved',
        'untouched-whole-sentence-pitch-preserved', 'voiced-prefix-before-controlled-release-pitch-preserved',
        'actual-single-original-release-passes-every-original-A21-phase',
        'actual-no-double-release-in-any-original-A21-phase'} <= set(by_name),
        'A21 actual control/five-phase/untouched-voice evidence is incomplete')
    request_check = by_name['exact-root-approved-request-source-sha256']
    require(request_check['actual_sha256'] == request_check['expected_sha256'] == requests[article],
            'A21 measured request SHA differs')
    actual = raw_audio.get('actual_original_A21', {})
    phases = actual.get('phase_results', [])
    require(actual.get('single_release_passed_all_phases') is True and
            actual.get('double_release_detected_any_phase') is False and len(phases) == 5 and
            sorted(p['endpoint_offset_s'] for p in phases) == [-.005, -.0025, 0., .0025, .005] and
            all(p.get('single_release_original_A21_passed') is True and p.get('double_release') is None for p in phases),
            'Actual repaired release did not pass every unchanged original A21 phase')
    return True



def actual_two_opening_report_checks(raw_audio, production_required=True):
    """Read the exact original article27 instrument without clearing its R finding.

    A diagnostic fixture is useful for interface checks only. Actual native
    acceptance always requires the non-diagnostic production report.
    """
    require(raw_audio.get('article')=='27' and raw_audio.get('kind')==
            'exact-two-approved-opening-pieces-controlled-audio-repair',
            'Only the actual two-opening article27 instrument is supported')
    require(raw_audio.get('passed')is True and raw_audio.get('repair_applied')is True and
            raw_audio.get('official_full_gates_are_separate_required_precondition')is True and
            raw_audio.get('official_gates_replaced_or_thresholds_modified')is False,
            'Actual article27 original instrument did not pass')
    if production_required:
        require(raw_audio.get('diagnostic_only')is False and
                raw_audio.get('production_delivery_eligible')is True,
                'A diagnostic candidate is not a passed native production report')
    require(raw_audio.get('program_sha256')==
            '2316283d99881b679a3f3c51bae59450fc65387ec2d6bd264d334cd485f2fea6' and
            raw_audio.get('reference_file_sha256')==
            '37581282f897aa22f776ee186ebe597e2d4ea67fa3f7abb23b392870fefe2037',
            'Article27 exact approved program/reference differs')
    fp=raw_audio['fingerprints']
    expected={'request_source_sha256':'e1214d8e9314a1cb54da82e2532889198bec555d6be9189fbfb43b5fdedcd728',
              'request_generator_sha256':'8509dd84018445aadb204b6bd9b2e7a609dbf65aed59e4a725f515053a820dbb',
              'actual_raw_WAV_sha256':'def5cf361fc57229ff8e14bf8db379fa60ca876b4ecde7eae6689444d4416ea7',
              'accepted_video_sha256':'4ab9da92fd3f57c226bd064c4c076d3f3b5428545542410d83ddc7cd90d9075e',
              'accepted_AAC_ADTS_sha256':'14bc91c62e66921fb55a215a42ce2db6a5544316600687b535a468770ae28252',
              'canonical_AAC_ADTS_sha256':'d619f0175ab2c57c6a5b77b9c6f0d62cd5b9fc2c548ec3900a45b3c44919b6f9'}
    require(all(fp.get(k)==v for k,v in expected.items()),'Article27 measured original source/audio binding differs')
    checks=raw_audio.get('checks',[]);by_name={r['name']:r for r in checks}
    require(checks and len(by_name)==len(checks),'Actual article27 check records missing or duplicated')
    required={'exact-entire-request-nonreview-document','exact-entire-actual-nonreview-document',
              'all-approved-audio-controls-exact','actual-no-clipping-or-nonfinite',
              'whole-track-level-preserved','outside-approved-ranges-same-voice-timing-gain',
              'every-untouched-active-one-second-block-preserved','original-audio-health-all-items',
              'original-whole-track-loudness','original-within-sentence-adjacent-level-rule',
              'actual-all-producer-group-times-and-gains-exact',
              'only-exact-root-approved-existing-S12-baseline-preserved'}
    required|={f'approved-gain-articulation-and-waveform:{unit}:{shave}'
              for unit in ('S13#1','S14#1')for shave in ('0.0','0.02','0.04')}
    required|={'actual-pitch-preserved:'+s for s in ['title']+[f'S{i}'for i in range(1,17)]}
    require(required<=set(by_name),'Actual article27 two openings/unchanged voice evidence incomplete')
    retained='original-suppressed-segment-rule-every-body-sentence'
    expected_finding=[['S12',2,[99.2,101.4],1.572465497844636,5.199999999999999]]
    require(retained in by_name and by_name[retained].get('passed')is False and
            by_name[retained].get('failures')==expected_finding,
            'Keep the exact original S12 R finding; do not clear or generalize it')
    require(all(row.get('passed')is True for name,row in by_name.items()if name!=retained),
            'Actual article27 contains another failed acoustic check')
    baseline=raw_audio.get('existing_accepted_supplemental_baseline',{})
    require(baseline.get('classification')=='baseline_existing_unchanged' and
            all(baseline.get(k)is True for k in ('preservation_conditions_passed',
                'original_R_findings_not_cleared','exact_original_tuple_equal',
                'native_prefix_matches_immutable_old_hash','original_S12_group_metadata_exact',
                'zero_gain_and_no_changed_public_samples')) and
            baseline.get('old_original_R_passed')is False and baseline.get('new_original_R_passed')is False and
            baseline.get('old_original_R_findings')==baseline.get('new_original_R_findings')==expected_finding and
            baseline.get('native_prefix_float32_sha256')==
            '95daa46f23e7049cbb52be992a133205566128ed61c0667658c19e7174e1c7d6',
            'The exact authorized unchanged S12 passage is not preserved')
    windows={r['label']:r for r in baseline.get('public_float32_sample_identity',[])}
    for label,span,expected_sha in (
        ('window',[99.2,101.4],'f2544118b088d03cc83bb5ca82f3571a36845fa83ed3943410fb584be7d618cd'),
        ('context',[92.8,101.6],'48123765ef3b0cd9efe263c5354d79941caccbd257c413c6ad2ce1f23bd1d1de')):
        row=windows.get(label,{})
        require(row.get('span_s')==span and row.get('float32_bitexact')is True and
                row.get('old_sha256')==row.get('new_sha256')==expected_sha,
                'Actual S12 public samples/window differ')
    return True


def actual_two_opening_repair_scope(review,native,raw_audio,article):
    require(article=='27','Article27 specific repair does not authorize other articles')
    actual_two_opening_report_checks(raw_audio)
    scope=native.get('approved_audio_repair_scope',{});fp=raw_audio['fingerprints']
    require(scope.get('kind')=='controlled_audio_repair'and scope.get('repair_applied')is True and
            scope.get('actual_original_full_pipeline_passed_first')is True and
            scope.get('whole_track_actual_audio_and_approved_unchanged_regions_required')is True,
            'Actual approved two-opening native repair scope absent')
    require(scope.get('request_source_sha256')==review.get('request_source_sha256')==
            fp['request_source_sha256']==native['request_source_sha256'].get('视频/脚本/27.json') and
            scope.get('reference_file_sha256')==review.get('reference_file_sha256')==raw_audio['reference_file_sha256'] and
            native.get('approved_audio_qc_program_sha256')==review.get('program_sha256')==raw_audio['program_sha256'],
            'Actual article27 scope/reference/request/program identity differs')
    require(native.get('canonical_pipeline_passed')is True and native.get('passed')is True and
            native.get('approved_audio_qc')==raw_audio and
            native.get('canonical_aac_adts_sha256')==fp['canonical_AAC_ADTS_sha256'] and
            native.get('accepted_source',{}).get('sha256')==fp['accepted_video_sha256'] and
            native.get('accepted_source',{}).get('aac_adts_sha256')==fp['accepted_AAC_ADTS_sha256'],
            'Actual full native pipeline or exact repaired/accepted voice chain differs')
    return True


SOURCE62_PROGRAM='1ffbaeb9a4cb0e7e161c255e038bb927aa6b6835cc702fe531cede594fbe8e1f'

SOURCE62_REFERENCE='96471961d87daa85a77d325c69a32c84accae0d986582306141fe3f9a0dbb5cb'

SOURCE62_EXPECTED={
    'request_source_sha256':'0779c44ccd17679ec853adc3fcc733623fc774e3cb6f68e59c7bb2c4ae62d541',
    'request_generator_sha256':'b2556d8b944ce21df821f9a113d639f296a0dde2858628cd45fdb8daf93eed8b',
    'actual_raw_WAV_sha256':'c5330026dbc9f81d0c7546a1716b9dade9960f44311862a5feb3e4aa0749d7c3',
    'accepted_video_sha256':'76ed237782d65e7bd19fd1c14891b55fd6b7014a43f7562f4d2faaf471a8b8af',
    'accepted_AAC_ADTS_sha256':'cbaa0988f1020bcaa2c245f8349001d8ad2224194164bfaa819231493f06b081',
    'canonical_AAC_ADTS_sha256':'b85f7e4c45784077f227b29a24b7cd72cef6c6160aa3783747ba708f8fda6348'}

def actual_62_report_checks(raw_audio):
    require(raw_audio.get('article')=='62'and raw_audio.get('kind')=='controlled_audio_repair',
            'Only source62 exact 96-sample boundary repair instrument is supported')
    require(raw_audio.get('passed')is True and raw_audio.get('repair_applied')is True and
            raw_audio.get('diagnostic_only')is False and raw_audio.get('production_delivery_eligible')is True,
            'A diagnostic/candidate source62 report is not real native production acceptance')
    require(raw_audio.get('official_full_gates_are_separate_required_precondition')is True and
            raw_audio.get('official_gates_replaced_or_thresholds_modified')is False and
            raw_audio.get('private_caches_GT_or_PCM_exported')is False,
            'Source62 supplement cannot replace native gates or export private inputs')
    require(raw_audio.get('program_sha256')==SOURCE62_PROGRAM and raw_audio.get('reference_file_sha256')==SOURCE62_REFERENCE,
            'Source62 exact approved original program/reference differs')
    require(raw_audio.get('source_authorization_ids')==['049','051','052'],
            'Source62 exact authorization ledger scope differs')
    fp=raw_audio.get('fingerprints',{})
    require(all(fp.get(k)==v for k,v in SOURCE62_EXPECTED.items()),'Source62 exact request/GEN/raw/accepted/new AAC binding differs')
    require(re.fullmatch('[0-9a-f]{64}',fp.get('canonical_video_sha256',''))is not None and
            re.fullmatch('[0-9a-f]{64}',fp.get('actual_full_source_sha256',''))is not None and
            raw_audio.get('canonical_sha256')==fp['canonical_video_sha256'] and
            raw_audio.get('accepted_sha256')==fp['accepted_video_sha256'] and
            raw_audio.get('source_current_sha256')==fp['actual_full_source_sha256'],
            'Source62 original report self-binding differs')
    checks=raw_audio.get('checks',[]);by_name={r['name']:r for r in checks}
    require(checks and len(by_name)==len(checks)and all(r.get('passed')is True for r in checks),
            'Source62 real complete original supplement has missing/duplicate/failed checks')
    required={'exact-approved-fingerprint:'+k for k in SOURCE62_EXPECTED}
    required|={side+'-'+name for side in ('requested','actual')for name in
              ('entire-nonreview-source','exact-one-96sample-insertion-control','all-original-spoken-English-preserved')}
    required|={'native-raw-sample-exact:'+name for name in
              ['prefix','suffix','title','four-vowel']+[f'S{i}'for i in range(1,20)if i!=15]}
    required|={'original-pitch-preserved:'+name for name in ['title']+[f'S{i}'for i in range(1,20)]}
    required|={'unchanged-official-native-pipeline-already-passed','actual-canonical-4K-present',
               'exact-original-PCM16-shape-and-duration','original-audio-codec-clock',
               'exact-37-AAC-packet-locality-and-all-other-packets-preserved',
               'decoded-sample-clock-and-duration-preserved','actual-no-clipping-or-nonfinite',
               'decoded-all-samples-before-and-after-codec-context-exact',
               'actual-decoded-change-support-bound-to-approved-measurement',
               'actual-true-peak-below-zero','whole-track-original-level-preserved',
               'all-eight-unchanged-original-health-rules','unchanged-original-whole-sentence-R-rule',
               'independent-title-and-all19-body-sentences-mapped','unchanged-original-within-sentence-R-rule',
               'S15-real-producer-gains-times-and-standard-pauses','S15-moved-insertion-boundary-0_4s-no-deletion',
               'four-phrase-F0-clock-and-voicing-preserved','real-candidate-positive-and-local-mutation-negatives'}
    require(required<=set(by_name),'Source62 full raw/source/pitch/clock/health evidence incomplete')
    return True

def actual_62_repair_scope(review,native,raw_audio,article):
    require(article=='62','Source62 specific boundary repair does not authorize another source')
    actual_62_report_checks(raw_audio)
    scope=native.get('approved_audio_repair_scope',{});fp=raw_audio['fingerprints']
    require(scope.get('kind')=='controlled_audio_repair'and scope.get('repair_applied')is True and
            scope.get('actual_original_full_pipeline_passed_first')is True and
            scope.get('whole_track_actual_audio_and_approved_unchanged_regions_required')is True,
            'Actual source62 native supplement scope absent')
    require(scope.get('request_source_sha256')==review.get('request_source_sha256')==SOURCE62_EXPECTED['request_source_sha256']==
                native['request_source_sha256'].get('视频/脚本/62.json') and
            native['request_source_sha256'].get('视频/工具/初稿生成/gen62.py')==SOURCE62_EXPECTED['request_generator_sha256'] and
            scope.get('reference_file_sha256')==review.get('reference_file_sha256')==SOURCE62_REFERENCE and
            native.get('approved_audio_qc_program_sha256')==review.get('program_sha256')==SOURCE62_PROGRAM,
            'Actual source62 native request/GEN/program/reference scope differs')
    require(native.get('article')=='62'and native.get('canonical_pipeline_passed')is True and native.get('passed')is True and
            native.get('approved_audio_qc')==raw_audio and native.get('canonical_video_sha256')==fp['canonical_video_sha256'] and
            native.get('canonical_aac_adts_sha256')==fp['canonical_AAC_ADTS_sha256'] and
            native.get('final_wav_sha256')==fp['actual_raw_WAV_sha256'] and
            native.get('accepted_source',{}).get('sha256')==fp['accepted_video_sha256'] and
            native.get('accepted_source',{}).get('aac_adts_sha256')==fp['accepted_AAC_ADTS_sha256'],
            'Actual source62 native full QA/new-canonical/accepted lineage differs')
    # The original upstream status predates the final source collector. Existing
    # delivery.py already binds actual JSON/GEN/MD to the main immutable ZIP;
    # do not demand a collector field that this upstream ABI does not export.
    return True


def canonical_audio_contract(review,native,article,selected_sha,actual_aac_sha,evidence_hashes,status_sha,strict_review):
    require(review['actual_new_output']is True and review['status']=='passed'and review['canonical_video_sha256']==selected_sha and review['report_sha256']in evidence_hashes,'Canonical audio review identity/evidence differs')
    if strict_review:
        if article in {'05','67'} and review['tool'] in ('audio05-tail-qc.py','audio67-controlled-qc.py'):
            actual_exact057_repair_scope(review,native,native.get('approved_audio_qc',{}),article)
            require(review.get('binding')=='reviewed_native_pre_card_then_exact_audio_copy' and
                    review['reviewed_canonical_video_sha256']==native['canonical_video_sha256'] and
                    native['canonical_aac_adts_sha256']==actual_aac_sha and
                    review['copy_verification_sha256'] in evidence_hashes,
                    'Exact057 actual reviewed new-canonical-to-card audio chain differs')
            return 'actual_dedicated_audio_qc_then_verified_exact_AAC_copy'
        if review['tool']=='audio62-controlled-qc.py':
            actual_62_repair_scope(review,native,native.get('approved_audio_qc',{}),article)
            require(review.get('binding')=='reviewed_native_pre_card_then_exact_audio_copy'and
                    review['reviewed_canonical_video_sha256']==native['canonical_video_sha256']and
                    native['canonical_aac_adts_sha256']==actual_aac_sha and
                    review['copy_verification_sha256']in evidence_hashes,
                    'Source62 actual new canonical-to-card audio chain differs')
            return 'actual_dedicated_audio_qc_then_verified_exact_AAC_copy'
        if review['tool']=='audio27-controlled-qc.py':
            actual_two_opening_repair_scope(review,native,native.get('approved_audio_qc',{}),article)
            require(review.get('binding')=='reviewed_native_pre_card_then_exact_audio_copy'and
                    review['reviewed_canonical_video_sha256']==native['canonical_video_sha256']and
                    native['canonical_aac_adts_sha256']==actual_aac_sha and
                    review['copy_verification_sha256']in evidence_hashes,
                    'Article27 original reviewed canonical-to-card copy chain differs')
            return 'actual_dedicated_audio_qc_then_verified_exact_AAC_copy'
        if review['tool'] == 'audio-a21-qc.py':
            actual_A21_repair_scope(review, native, native.get('approved_audio_qc', {}), article)
            require(review.get('binding') == 'reviewed_native_pre_card_then_exact_audio_copy' and
                    review['reviewed_canonical_video_sha256'] == native['canonical_video_sha256'] and
                    native['canonical_aac_adts_sha256'] == actual_aac_sha and
                    review['copy_verification_sha256'] in evidence_hashes,
                    'A21 original reviewed canonical-to-card copy chain differs')
            return 'actual_dedicated_audio_qc_then_verified_exact_AAC_copy'
        require(review['tool']=='audio-qc.py','Acoustic repairs and10/12/44/51 require actual dedicated MP4 acoustic QC')
        if review.get('binding')=='reviewed_native_pre_card_then_exact_audio_copy':
            require(review['reviewed_canonical_video_sha256']==native['canonical_video_sha256']and native['canonical_aac_adts_sha256']==actual_aac_sha,'Original reviewed canonical identity/audio differs from actual selected copy')
            require(review['copy_verification_sha256']in evidence_hashes,'Original native audio-copy verification required')
            return 'actual_dedicated_audio_qc_then_verified_exact_AAC_copy'
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

def reviewed_canonical_audio_copy(review,native,raw_audio,copy_proof,article,selected_sha,actual_aac_sha):
    """A different MP4 container may contain the exact already-reviewed audio.

    Keep the acoustic report's ORIGINAL canonical SHA. The native immutable
    end-card proof establishes its AAC and absolute-time identity with the
    selected two-second-card MP4, which is inspected locally again.
    """
    if article in {'05','67'} and review['tool'] in ('audio05-tail-qc.py','audio67-controlled-qc.py'):
        actual_exact057_repair_scope(review,native,raw_audio,article)
    if review['tool']=='audio62-controlled-qc.py':
        actual_62_repair_scope(review,native,raw_audio,article)
    if review['tool'] == 'audio-a21-qc.py':
        actual_A21_repair_scope(review, native, raw_audio, article)
    if review['tool']=='audio27-controlled-qc.py':
        actual_two_opening_repair_scope(review,native,raw_audio,article)
    else:
        require(raw_audio['article']==article and raw_audio['passed']is True and raw_audio['checks']and all(c['passed']is True for c in raw_audio['checks']),'Original actual dedicated acoustic review failed')
    require(raw_audio['canonical_sha256']==review['reviewed_canonical_video_sha256']==native['canonical_video_sha256']and native['approved_audio_qc']==raw_audio,'Do not relabel the original acoustic report canonical fingerprint')
    require(copy_proof['article']==article and copy_proof['source_kind']=='new-canonical-4K'and copy_proof['canonical_pipeline_passed']is True,'Actual original canonical-copy verification required')
    require(copy_proof['canonical_source_video_sha256']==raw_audio['canonical_sha256']and copy_proof['video_sha256']==selected_sha,'Acoustic review→selected native MP4 lineage differs')
    require(copy_proof['original_audio_identical']is True and copy_proof['original_audio_packet_timings_identical']is True and copy_proof['final_canonical_aac_identical']is True,'Native processing changed reviewed audio payload or absolute timing')
    require(copy_proof['canonical_aac_adts_sha256']==native['canonical_aac_adts_sha256']==actual_aac_sha,'Actual selected native AAC differs from the reviewed canonical AAC')
    return True

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
