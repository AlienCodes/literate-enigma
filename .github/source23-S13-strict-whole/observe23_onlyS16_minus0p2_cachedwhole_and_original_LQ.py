"""Source23 original f081 run_phase; one source S16 gain only; original LQ check. No quality waiver."""
from pathlib import Path
import importlib.util,hashlib
_ORIGINAL=Path(__file__).with_name('observe23_strict_cached_baseline_and_selected_whole.py')
if hashlib.sha256(_ORIGINAL.read_bytes()).hexdigest()!='f0812887447c50e6418445877ecf9bcc1d6fd8c421737fde9fa4437cfbb7f8d6':raise ValueError('Immutable original f081 observer bytes differ before import')
_spec=importlib.util.spec_from_file_location('_unchanged_source23_original_f081_whole',_ORIGINAL)
base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(base)
for _key,_value in vars(base).items():
    if not _key.startswith('__'):globals()[_key]=_value

PROFILE_SHA256 = '9ca186322f08128addd7a87f8e0423ceac224705e6df2ea5d291394cb59eaa73'

def verify_only_S16_gain_candidate(inputs,profile,verified_original_graft):
    current_raw=inputs['LQ_current_baseline'].read_bytes();selected_raw=inputs['LQ_selected_candidate'].read_bytes()
    current=json.loads(current_raw);selected=json.loads(selected_raw)
    require(digest(inputs['LQ_ROOT_actual_scope'])==profile['only_S16_gain_scope']['ROOT_scope_SHA256'],'Actual ROOT S16 gain scope is not pinned')
    require(current.get('句子增益dB') is None and typed(selected.get('句子增益dB'))==typed({'S16':-0.2}),'Only original S16 -0.2 gain is authorized')
    inv=copy.deepcopy(selected);inv.pop('句子增益dB');require(typed(inv)==typed(current),'Unknown source change beyond only S16 gain')
    raw_inverse=selected_raw.replace(',\n "句子增益dB": {\n  "S16": -0.2\n }'.encode(),b'',1)
    require(raw_inverse==current_raw,'Entire source raw inverse must equal measured current')
    graft_back=copy.deepcopy(current)
    expected=profile['only_S16_gain_scope']['actual_graft_candidate_to_current_only11_CF_delta']
    require([x['path']for x in exact_data_diff(verified_original_graft,current)]==expected,'Current graft evidence metadata roles differ')
    for path in expected:
        q=graft_back
        parts=path.split('/')[1:]
        for k in parts[:-1]:q=q[k]
        require(q[parts[-1]]=='89e9ea72220c','Current graft whole-MD5 witness differs');q[parts[-1]]='3a7b75e8f3bc'
    require(typed(graft_back)==typed(verified_original_graft),'Unknown graft/current physical source delta')
    measured=json.loads(inputs['LQ_prior_actual_graft_report'].read_text())
    require(measured['diagnostic_completed']is True and measured['exact_scope_proved']is True,'Prior actual graft whole must be successful')
    prior=measured['phases']['selected']
    require(prior['source_sha256']==profile['inputs']['candidate']['sha256'] and prior['actual_complete_WAV']['file_sha256']==profile['baseline_audio']['WAV_sha256'] and prior['actual_complete_WAV']['file_md5']==profile['only_S16_gain_scope']['actual_complete_baseline_WAV_MD5'],'Actual current graft WAV/source witness differs')
    for k in ('aac_adts_sha256','packet_projection_sha256','packet_count'):require(prior['actual_codec_packet_payload_side_and_absolute_clock'][k]==profile['baseline_audio'][k],'Actual graft AAC/clock witness differs')
    for d in [current,selected]:require(d.get('词尾除阻',{}).get('S13')=={'1':[3.7,'t']} and d.get('区间声音指纹',{}).get('S13')=='d2e182d92ebf','S13 graft/mother scope must be preserved')
    require(current['sentences'][15]['chunks'][0]['en']=='**Recognition** **lagged**.','Wrong actual S16 English')
    return current,selected

def validate_LQ_adoption(value,helper_sha,profile_sha):
    require(value.get('kind')=='derived-concrete-S16-gain-cachedwhole-binding-to-actual-ROOT-not-new-root-origin','Not an exact derived ROOT binding')
    require(value.get('source_id')=='23' and value.get('book_order')==62 and value.get('mother_scope_target')=='S13' and value.get('gain_sentence')=='S16' and type(value.get('gain_dB')) is float and value.get('gain_dB')==-0.2,'Wrong explicit source/gain scope')
    require(value.get('helper_sha256')==helper_sha and value.get('profile_sha256')==profile_sha and value.get('ROOT_scope_SHA256')=='fed111ee3a80e6bd3885a55ffb23ec104dacf92c79833c62acd2af6da4a14aff' and value.get('original_run_phase_helper_SHA256')=='f0812887447c50e6418445877ecf9bcc1d6fd8c421737fde9fa4437cfbb7f8d6','Exact helper/profile/real ROOT scope required')
    require(value.get('no_new_TTS_or_G36_or_GT_ASR')is True,'No new model/math scope')

def compare_only_S16_gain_phases(profile,report):
    import numpy as np
    require(set(report['phases'])=={'baseline','selected'},'Only exact baseline and selected phase labels permitted')
    old,new=report['phases']['baseline'],report['phases']['selected'];checks=[]
    for sid in ['title']+['S'+str(i)for i in range(1,20)if i!=16]:
        a,b=phase_arrays['baseline'][sid],phase_arrays['selected'][sid]
        ac,bc=old['actual_sample_clock'][sid],new['actual_sample_clock'][sid]
        require(ac['start_sample']==bc['start_sample']and ac['end_sample_exclusive']==bc['end_sample_exclusive'],'Absolute segment clock changed')
        x,y=[phase_post_arrays[k][c['start_sample']:c['end_sample_exclusive']] for k,c in [('baseline',ac),('selected',bc)]]
        u,v=[phase_int16_arrays[k][c['start_sample']:c['end_sample_exclusive']] for k,c in [('baseline',ac),('selected',bc)]]
        row={'segment':sid,'pre_float_exact':a.dtype==b.dtype and a.shape==b.shape and bool(np.array_equal(a,b)),'post_float_exact':x.dtype==y.dtype and x.shape==y.shape and bool(np.array_equal(x,y)),'PCM16_exact':u.dtype==v.dtype and u.shape==v.shape and bool(np.array_equal(u,v)),'effective_DSP_exact':sid=='title'or typed(old['observed_sentences'][sid]['effective_source_DSP'])==typed(new['observed_sentences'][sid]['effective_source_DSP']),'absolute_clock_exact':True}
        checks.append(row);require(all(row[k]for k in ['pre_float_exact','post_float_exact','PCM16_exact','effective_DSP_exact']),'A non-S16 segment changed: '+sid)
    report['unchanged_title_S13_and_other17_sentence_actual_arrays_and_DSP']=checks
    require(len(checks)==19 and any(x['segment']=='S13'for x in checks),'S13 must be included in unchanged actual PCM scope')
    report['actual_global_master_scale_ratio_selected_over_baseline']=new['actual_original_mastering']['logical_normalization_scale']/old['actual_original_mastering']['logical_normalization_scale']
    require(report['actual_global_master_scale_ratio_selected_over_baseline']==1.,'Master coefficient changed')
    require(old['actual_original_pre_master_peak_ownership_metadata']['all_callback_segments_tied_at_whole_absolute_peak']==new['actual_original_pre_master_peak_ownership_metadata']['all_callback_segments_tied_at_whole_absolute_peak']==['S6'],'Actual global peak owner must remain unchanged S6')
    a,b=phase_arrays['baseline']['S16'],phase_arrays['selected']['S16'];require(a.dtype==b.dtype and a.shape==b.shape and np.array_equal(a*10**(-0.2/20),b)and not np.array_equal(a,b),'Actual S16 must be only original exact scalar gain branch')
    oldc,newc=old['actual_sample_clock']['S16'],new['actual_sample_clock']['S16'];require(oldc['start_sample']==newc['start_sample']and oldc['end_sample_exclusive']==newc['end_sample_exclusive'],'S16 sample count/clock changed')
    before,after=copy.deepcopy(old['observed_sentences']['S16']),copy.deepcopy(new['observed_sentences']['S16'])
    for k in ['pre_master_PCM_sha256','effective_source_DSP']:before.pop(k);after.pop(k)
    require(typed(before)==typed(after),'S16 raw mother/cuts/pieces/auto gain changed')
    post0=phase_post_arrays['baseline'][oldc['start_sample']:oldc['end_sample_exclusive']];post1=phase_post_arrays['selected'][newc['start_sample']:newc['end_sample_exclusive']]
    pcm0=phase_int16_arrays['baseline'][oldc['start_sample']:oldc['end_sample_exclusive']];pcm1=phase_int16_arrays['selected'][newc['start_sample']:newc['end_sample_exclusive']]
    report['actual_S16_only_original_gain_factor_exact']=True
    report['actual_S16_post_float_changed']=not np.array_equal(post0,post1)
    report['actual_S16_final_WAV_PCM16_changed']=not np.array_equal(pcm0,pcm1)
    require(report['actual_S16_post_float_changed'] and report['actual_S16_final_WAV_PCM16_changed'],'S16 actual mastered/quantized gain effect not observed')
    report['legacy_run_phase_peak_target_label_S13_not_claimed_S16']=True

def check_original_LQ_both_actual_outputs(profile,report,paths):
    path=paths['T']/'响度一致性核对.py';require(digest(path)==profile['only_S16_gain_scope']['original_LQ_SHA256'],'Original LQ program changed')
    spec=importlib.util.spec_from_file_location('_actual_unchanged_original_LQ',path);LQ=importlib.util.module_from_spec(spec);spec.loader.exec_module(LQ)
    rows=[]
    for role,file in [('master_WAV',paths['scratch']/'selected-private-original-work23/a.wav'),('original_encoded_AAC',paths['scratch']/'selected-actual-original-canonical.m4a')]:
        I,segs,levels,bad,summary=LQ.check(str(file));rows.append({'role':role,'private_path':str(file),'file_SHA256':digest(file),'original_program_SHA256':digest(path),'integrated_LUFS':I,'actual_segments':segs,'actual_levels_LUFS':levels,'original_bad_rows':bad,'original_summary':summary,'passed':not bad})
    report['actual_original_LQ_master_WAV_and_encoded_AAC']=rows
    require(all(x['passed']for x in rows),'Original LQ rejected actual selected WAV/AAC; retain report and stop')

def main():
    global CACHE
    p=argparse.ArgumentParser()
    for key in ('tools','video-root','inputs','profile','execution-adoption','ROOT-scope','output','cache-path-output'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--execution-adoption-sha256',required=True)
    a=p.parse_args();T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';CACHE=M/'tts/cache_tts';base.CACHE=CACHE
    report={'kind':'source'+SOURCE_NO+'_actual_original_strict_cached_two_phase_whole_scalar_observation',
        'source_id':SOURCE_NO,'book_order':BOOK_ORDER,'target_sentence':TARGET,'only_changed_gain_sentence':'S16','original_mother_scope_target_retained':'S13','quality_acceptance':False,
        'formal_acceptance':False,'production_delivery_eligible':False,'diagnostic_completed':False,
        'exact_scope_proved':False,'no_new_TTS_authorized':True,'forbidden_model_events':[],
        'phases':{},'errors':[],'restoration':{},'immutable_owner_source_GEN_MD_or_CF_written':False,
        'per_phase_W_script_is_private_temporary_source_and_restored':True}
    before=None;public_before=None;inputs=None;profile=None;scratch=None;new_math={};used={};support=None
    try:
        require(digest(a.profile)==PROFILE_SHA256,'Wrong source-specific frozen whole profile')
        profile=json.loads(a.profile.read_text());require(profile['source_id']==SOURCE_NO and profile['target_sentence']==TARGET,'Wrong profile source scope')
        inputs=bind_inputs(a.inputs,profile)
        require(digest(a.execution_adoption)==a.execution_adoption_sha256 and len(a.execution_adoption_sha256)==64,'Separate actual root adoption SHA must be literal-pinned')
        require(digest(a.ROOT_scope)=='fed111ee3a80e6bd3885a55ffb23ec104dacf92c79833c62acd2af6da4a14aff' and a.ROOT_scope.read_bytes()==inputs['LQ_ROOT_actual_scope'].read_bytes(),'Actual mandatory ROOT CLI scope differs'); validate_LQ_adoption(json.loads(a.execution_adoption.read_text()),digest(__file__),PROFILE_SHA256)
        require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent,'Original canonical ROOT alias differs')
        require(not a.output.resolve().is_relative_to(M),'Only safe scalar output outside private machine')
        require(all(os.environ.get(k)=='1'for k in ['STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']),'Original strict reviewed modes required')
        require(not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID']),'Unapproved voice/filter/old-scope override')
        require(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER_SHA256,'Exact spoken22 maker required')
        require(digest(T/'发音词典/读音改正.json')==DICT_SHA256 and digest(T/'发音词典/按语境读音.json')==CTX_SHA256,'Original dictionary context differs')
        require(digest(T/'环境/模型校验码.json')==digest(W/'环境/模型校验码.json')==REGISTRY_SHA256,'Original portable registry differs')
        ms=importlib.util.spec_from_file_location('_whole_'+SOURCE_NO+'_existing_mother_scope',inputs['mother_helper'])
        support=importlib.util.module_from_spec(ms);ms.loader.exec_module(support)
        require(support.SOURCE_NO==SOURCE_NO and support.TARGET==TARGET,'Wrong original target helper')
        support.validate_certificate(T,json.loads(inputs['overlay'].read_text()),json.loads(inputs['certificate'].read_text()))
        identity=json.loads(inputs['identity'].read_text());root=json.loads(inputs['mother_intake'].read_text())
        require(root['source_id']==SOURCE_NO and root['target_sentence']==TARGET and root['actual_private_cache_key']==profile['actual_mother_private_cache_key'] and root['actual_private_cache_version']==profile['actual_mother_private_cache_version'],'Wrong actual mother intake/cache provenance')
        require(identity['request_SHA256']==profile['inputs']['source']['sha256'] and identity['shadow_SHA256']==profile['inputs']['shadow']['sha256'] and identity['maker_SHA256']==MAKER_SHA256 and identity['actual_new_code_certificate_SHA256']==CERTIFICATE_SHA256 and identity['actual_new_110_stamp_SHA256']==STAMP_SHA256,'Actual mother fixture source/code roles differ')
        require(identity['actual_four_private_files']==profile['actual_four_private_files'],'Wrong exact selected private mother fixture')
        require(all(digest(CACHE/name)==h for name,h in profile['actual_four_private_files'].items()),'New mother/marker fullSHA mismatch')
        require({k:digest(M/'tts'/k)for k in identity['models_SHA256']}==identity['models_SHA256'] and digest(M/'tts/voice_mb.npy')==identity['voice_SHA256'],'Original actual model/voice fullSHA mismatch')
        owner,selected=json.loads(inputs['source'].read_text()),json.loads(inputs['shadow'].read_text())
        baseline=json.loads(inputs['baseline'].read_text());history=json.loads(inputs['history'].read_text())
        support.verify_request(owner,selected,history)
        historical_selected=selected
        verified_graft=verify_current_one_graft_candidate(inputs,profile,historical_selected)
        baseline,selected=verify_only_S16_gain_candidate(inputs,profile,verified_graft)
        donor=profile['strict_existing_donor'];require(digest(CACHE/donor['name'])==donor['sha256'],'Exact existing original t donor must hit; no synthesis or replacement')
        report['historical_fixture_shadow_is_not_new_candidate']=True
        report['actual_selected_candidate_source_SHA256']=profile['inputs']['LQ_selected_candidate']['sha256']
        require(all(str(x['no'])==SOURCE_NO and len(x['sentences'])==COUNT for x in [owner,selected,baseline]),'Wrong actual baseline/request sentence scope')
        require(baseline['title_en']==selected['title_en'],'Non-target title changed')
        bare=lambda d:[' '.join(re.sub(r'\*\*|\{\{.*?\}\}','',c['en']).strip()for c in s['chunks'])for s in d['sentences']]
        require(bare(baseline)==bare(selected),'Display English changed outside exact spoken schema')
        require(all(typed(dsp(baseline,'S'+str(i)))==typed(dsp(selected,'S'+str(i)))for i in range(1,COUNT+1)if 'S'+str(i)!='S16'),'Non-target typed source DSP changed')
        before=inventory(CACHE);public_before=inventory(T.parent/'配音缓存')
        scratch=M/('_source'+SOURCE_NO+'_onlyS16minus0p2_strict_cached_two_phase_whole');require(not scratch.exists(),'Fresh private diagnostic namespace required');scratch.mkdir()
        paths={'T':T,'M':M,'W':W,'scratch':scratch}
        report.update({'helper_sha256':digest(__file__),'profile_sha256':PROFILE_SHA256,'actual_root_execution_adoption_sha256':a.execution_adoption_sha256,'actual_inputs':{k:digest(v)for k,v in inputs.items()},'actual_used_cache_entries':[],'original_source_first_fresh_import_per_phase':True})
        with support.environment_and_cwd(W,report['restoration']):
            with work_namespace(W/('work_'+SOURCE_NO),scratch,report['restoration']):
                for label,role in [('baseline','LQ_current_baseline'),('selected','LQ_selected_candidate')]:
                    report['restoration']['normal_scripts_namespace_restored']=False
                    with support.source_namespace(W,inputs[role].read_bytes(),report['restoration']):
                        run_phase(label,inputs[role].read_bytes(),profile['inputs'][role]['sha256'],paths,support,profile,report,used,new_math)
        report['both_actual_original_whole_observations_completed']=True
        compare_only_S16_gain_phases(profile,report)
        require(all(not x['original_G36_calls'] for x in report['phases'].values()),'No original G36 call is authorized for source23')
        check_original_LQ_both_actual_outputs(profile,report,paths)
        require(report['actual_global_master_scale_ratio_selected_over_baseline']==1.0,'Master coefficient must remain exactly one relative to true baseline')
        require(not new_math,'No original G36 calculation or private SAVE is authorized')
        require(not report['forbidden_model_events'],'Forbidden model endpoint was reached')
        report['diagnostic_completed']=True
    except BaseException as error:
        report['errors'].append({'type':type(error).__name__,'detail':str(error)});traceback.print_exc()
    finally:
        try:
            if before is not None:
                after=inventory(CACHE);allowed=set(new_math)
                report['all_existing_private_cache_files_exact_before_after']=all(after.get(n)==h for n,h in before.items())
                report['only_actual_new_target_original_G36_JSON_added']=set(after)-set(before)==allowed and not(set(before)-set(after))
                report['actual_new_target_original_G36']=new_math
                report['public_cache_bytes_exact_before_after']=inventory(T.parent/'配音缓存')==public_before
                report['actual_used_cache_entries']=list(used.values())
                report['original_tools_and_work_maker_bytes_exact_after']=digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER_SHA256
                report['all_frozen_inputs_exact_after']=all(digest(v)==profile['inputs'][k]['sha256']for k,v in inputs.items())
                report['runtime_contract_files_exact_after']=all(digest(T/Path(r['path']).relative_to('视频/工具'))==r['patch_SHA256']for r in json.loads(inputs['overlay'].read_text())['files'])
                report['normal_original110_stamp_exact_after']=digest(T/'新管/快测通过.json')==STAMP_SHA256
                guards=['all_existing_private_cache_files_exact_before_after','only_actual_new_target_original_G36_JSON_added','public_cache_bytes_exact_before_after','original_tools_and_work_maker_bytes_exact_after','all_frozen_inputs_exact_after','runtime_contract_files_exact_after','normal_original110_stamp_exact_after']
                report['exact_scope_proved']=bool(report['diagnostic_completed'] and all(report.get(k)is True for k in guards) and all(report['restoration'].get(k)is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored']))
            math_save_integrity=bool(new_math and all(v.get('strict_readback_exact') is True for v in new_math.values())
                and all(report.get(k)is True for k in guards)
                and all(report['restoration'].get(k)is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored'])
                and not report['forbidden_model_events'])
            report['actual_original_math_private_save_integrity_proved_not_whole_acceptance']=math_save_integrity
            if math_save_integrity:
                directory=M/'tts'/('source'+SOURCE_NO+'-only-target-whole-original-math-cache')
                require(not directory.exists(),'Fresh actual private math-save namespace required');directory.mkdir()
                saved=[]
                for name,item in new_math.items():
                    destination=directory/name;shutil.copyfile(CACHE/name,destination)
                    require(digest(destination)==item['sha256'],'New private math-save copy mismatch');saved.append(str(destination))
                runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual Actions run ID required to emit cache save identity')
                key='Linux-native'+SOURCE_NO+'-only-target-whole-original-math-'+runid
                a.cache_path_output.parent.mkdir(parents=True,exist_ok=True)
                with a.cache_path_output.open('a')as out:out.write('cache_key='+key+'\ncache_paths<<WHOLE_TARGET_MATH_PATHS\n'+'\n'.join(saved)+'\nWHOLE_TARGET_MATH_PATHS\n')
                report['private_original_math_save']={'cache_key':key,'exact_paths':saved,'files':new_math,'save_success_not_claimed':True}
        except BaseException as error:
            report['exact_scope_proved']=False
            report['diagnostic_completed']=False
            report['errors'].append({'type':type(error).__name__,'detail':str(error),'during':'restore-identity-or-private-save-finalization'})
            traceback.print_exc()
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
        print(json.dumps({'output_sha256':digest(a.output),'diagnostic_completed':report['diagnostic_completed'],'exact_scope_proved':report['exact_scope_proved'],'errors':report['errors'],'new_model_inference_authorized':False,'production_or_formal_acceptance':False},ensure_ascii=False))
    return 0 if report['exact_scope_proved'] else 1
if __name__=='__main__':sys.exit(main())
