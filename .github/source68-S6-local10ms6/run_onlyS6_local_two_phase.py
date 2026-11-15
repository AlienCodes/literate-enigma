"""Concrete onlyS6 local two-phase conditional original math caller; no actual execution yet.
Original cached-machine W inode isolation, actual20 setup and strict saved math.
No inference, whole, GT, ASR, CF change or waveform export; one actual new original S6 math may be saved.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, subprocess, sys, traceback
sys.dont_write_bytecode=True
ROOT_SHA='185b3e1502aeb77d1af7bac4c7f05af298924c49e2f0b9448db6313b127a6da2'
HELPER_SHA='f804301caa20b9fc3fd8a14f2675877d4ce22cdac18aec3f8cfa3ec16aba3afc'
PROFILE_SHA='d66a6074caa2792dc0b2a65489f8b165a41fa63abe21fcac587549a89bce0950'
SOURCE_SHA='e122c817946c4ed6e7cd1394749879276ef2afe9d01ad691b4142c6bbd9ec9b4'
MOTHER_KEY='Linux-native68-exact-S2-first-spoken-comma-43702410293'
MOTHER_VERSION='1876e5e5b689945a432f2564472935c78443d40f5d021a2378395bf71140c1d5'
MATH_KEY='Linux-native68-only-target-whole-original-math-43722945326'
MATH_VERSION='00b4c677297a43021c5f8c943aa224d49fb32065f82bcda32a2d8ddeb68c0931'
def require(value, message):
    if not value: raise AssertionError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def cache_api_row(path, key, version):
    value = json.loads(Path(path).read_text())
    require(value['total_count'] == len(value['actions_caches']) == 1, 'Unique actual API cache identity required')
    row = value['actions_caches'][0]
    require(row['key'] == key and row['version'] == version and
            row['ref'] == 'refs/heads/codex/finish-05-and-summaries-20261112', 'Wrong exact actual API cache key/version/ref')
    return row

def validate_root(path,literal_sha,package):
    p,N=Path(path),Path(package)
    require(literal_sha==ROOT_SHA and p.is_file() and not p.is_symlink() and sha(p)==ROOT_SHA,'Mandatory actual ROOT185b fullSHA CLI required')
    require(p.read_bytes()==(N/'root-onlyS6-local-execution-scope.json').read_bytes(),'ROOT transport copy differs')
    value=json.loads(p.read_text())
    require(value['candidate_only']=={'source':'68','sentence':'S6','old_boost':[9.025,9.085,3.5],'new_boost':[9.025,9.035,6.0]},'Wrong ROOT exact one boost scope')
    require(value['actual_H']['sha256']==sha(N/'probe/inputs/data_H.json') and value['actual_new_candidate_sound_or_quality_accepted'] is False,'Actual ROOT data provenance differs')
    return value

def verify_transport(package):
    N=Path(package);rows=json.loads((N/'transport-file-pins.json').read_text())
    require(rows and len({r['relative'] for r in rows})==len(rows),'Finite unique transport pins required')
    for r in rows:
        p=Path(r['relative']);require(not p.is_absolute() and '..' not in p.parts,'Transport escapes package');q=N/p
        require(q.is_file() and not q.is_symlink() and q.stat().st_size==r['bytes'] and sha(q)==r['sha256'],'Runtime transport differs '+str(p))
    require(sha(N/'probe/observe68_only_S6_local_two_phase.py')==HELPER_SHA and sha(N/'probe/profile.json')==PROFILE_SHA,'New local helper/profile binding differs')
    require(sha(N/'probe/baseline-observe.py')=='d53aebdd61c992473b6f3f455c23a852b979cd3fe8dce11f3fad35c576851ea4' and sha(N/'probe/baseline-profile.json')=='6ac2d576251651ef5d3ffdfd70f399c351b4af268df03d7259425027db128c7a','Original55 baseline helper/profile changed')
    return rows

def validate_parent_review(path,literal_sha,package):
    p,N=Path(path),Path(package)
    require(re.fullmatch('[0-9a-f]{64}',literal_sha or '') and p.is_file() and not p.is_symlink() and sha(p)==literal_sha,'Actual independent parent adoption fullSHA mandatory before setup/firstHTTP')
    require(p.read_bytes()==(N/'actual-parent-independent-onlyS6-review.json').read_bytes() and (N/'actual-parent-independent-onlyS6-review.sha256').read_text().strip()==literal_sha,'Actual independent parent review transport copy/literal differs')
    v=json.loads(p.read_text())
    require(v['kind']=='ROOT-DELEGATED-independent-source68-onlyS6-local10ms6-conditional-one-original-math-execution-adoption','Wrong independent actual review role')
    require(v['root_scope']['sha256']==ROOT_SHA and v['program_SHA256']==HELPER_SHA and v['profile_SHA256']==PROFILE_SHA,'Actual parent review must bind current ROOT/helper/profile')
    require(v['source_id']=='68' and v['changed_sentence']=='S6' and v['original_mother_scope_target']=='S2' and v['independent_review_passed'] is True and v['allow_only_S6_one_original_math_if_missing'] is True and v['new_TTS_GT_ASR_whole_or_CF_write_authorized'] is False,'Parent independent scope incomplete')
    return v

def helper_argv(package,repo,machine,tools,public):
    N=Path(package);helper=N/'probe/observe68_only_S6_local_two_phase.py';require(sha(helper)==HELPER_SHA,'Wrong onlyS6 local helper')
    root=N/'root-onlyS6-local-execution-scope.json'
    return [sys.executable,str(helper),'--tools',str(tools),'--video-root',str(machine),'--inputs',str(N/'probe'),'--profile',str(N/'probe/profile.json'),'--execution-adoption',str(root),'--execution-adoption-sha256',ROOT_SHA,'--output',str(Path(public)/'68-onlyS6-local-two-phase-measurement.json'),'--cache-path-output',str(Path(public)/'68-onlyS6-private-math-step-output.txt')]

def verify_actual_original_G27(package,tools,work):
    N,T,W=map(Path,(package,tools,work))
    require(sha(N/'original_G27_module_map.py')==sha(T/'出片指纹.py')=='ef589d2ad0bc9e1806a37161c81e727b7f900d4de490d05d4c74755b392b91a9','Actual original G27 module changed')
    require(sha(T/'新管/快测通过.json')=='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41','Actual original20 stamp must match before fresh helper')
    g=load('_source68_original_G27_actual_module_paths',N/'original_G27_module_map.py');expected=json.loads((N/'actual-original20-G27-eight-module-identities.json').read_text());repo=g.清单([str(T)])
    require(len(expected)==len(repo)==8 and set(repo)==set(expected),'Original recursive module map scope differs')
    require(g.核对工作目录(str(W),str(T))==[],'Original recursive G27 work check failed')
    rows={}
    for name,p in repo.items():
        q=g._找(name,g.工作目录搜(str(W)));require(q is not None,'Actual import path missing '+name);p,q=Path(p),Path(q)
        require(q.resolve() in [(W/(name+'.py')).resolve(),(W.parent/'tts'/(name+'.py')).resolve()] and sha(q)==sha(p)==expected[name],'Actual original helper import resolution/fullSHA differs '+name)
        rows[name]={'actual_original_tools_path':str(p.resolve()),'actual_work_import_path':str(q.resolve()),'sha256':sha(q)}
    return {'actual_original_G27_recursive_module_count':8,'actual_original20_stamp_sha256':sha(T/'新管/快测通过.json'),'module_paths_and_full_SHA256':rows,'fresh_helper_subprocess_no_previous_sys_modules':True}

def publish_verified_math_outputs(scalar,private_output,machine,real_output,outer_restored):
    # This runs only after caller's outer original-W context has fully exited.
    require(outer_restored is True and scalar.get('measurement_completed') is True and scalar.get('errors')==[] and scalar.get('forbidden_model_events')==[],'No cache SAVE output before actual measurement/all outer restores')
    guards=['all_original_modules_trace_env_cwd_path_restored','all_frozen_inputs_unchanged','all_preexisting_private_cache_files_unchanged_only_one_actual_S6_math_added','public_cache_bytes_unchanged','normal_work_inode_and_files_unchanged','original_private_initial_source_restored','actual_model_voice_AF_dictionary_context_stamp_PV_dossier_inputs_exact_after']
    require(all(scalar.get(k) is True for k in guards) and all(scalar.get('restoration',{}).get(k) is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored']),'A helper restoration/input scope failed; never expose cache SAVE')
    entries=scalar.get('actual_new_S6_original_math',{});private_output=Path(private_output)
    if not entries:
        require(not private_output.exists() or private_output.read_text()=='','Unexpected private output without actual new math')
        return False
    require(len(entries)==1 and scalar.get('math_save_integrity_independent_of_PV_verdict') is True,'Only one proven actual S6 math may be published')
    name,item=next(iter(entries.items()));match=re.fullmatch(r'调平_([0-9a-f]{40})\.json',name)
    require(match is not None and item.get('source_id')=='68' and item.get('target_sentence')=='S6' and item.get('strict_readback_exact') is True and re.fullmatch('[0-9a-f]{64}',item.get('sha256','')),'Invalid actual single-S6 math identity')
    calls=scalar.get('actual_candidate_G36',[])
    require(len(calls)==1 and calls[0]['sentence']=='S6' and calls[0]['file']==name and calls[0]['original_key']==match.group(1) and calls[0]['actual_math_created'] is True and calls[0]['strict_readback_exact'] is True and calls[0]['sha256']==item['sha256'],'Actual candidate G36 role/key/readback differs')
    M=Path(machine).resolve();folder=M/'tts/source68-only-S6-local-original-math-cache';copy_path=folder/name;original=M/'tts/cache_tts'/name
    require(not folder.is_symlink() and copy_path.is_file() and not copy_path.is_symlink() and original.is_file() and not original.is_symlink(),'Actual math SAVE copy/cache must be regular exact paths')
    require(sha(copy_path)==sha(original)==item['sha256'] and json.loads(copy_path.read_text())==json.loads(original.read_text())==item['value'],'Actual math SAVE SHA/value differs from measured scalar')
    runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual Actions run ID required')
    key='Linux-native68-only-S6-local-original-math-'+runid;save=scalar.get('private_original_math_save',{})
    require(save.get('cache_key')==key and save.get('exact_paths')==[str(copy_path)] and save.get('files')==entries and save.get('save_success_not_claimed') is True,'Private math declaration must contain this one actual measured path')
    expected='cache_key='+key+'\ncache_paths<<ONLY_S6_ORIGINAL_MATH_PATHS\n'+str(copy_path)+'\nONLY_S6_ORIGINAL_MATH_PATHS\n'
    require(private_output.is_file() and not private_output.is_symlink() and private_output.read_text()==expected,'Private step file has unknown fields/path/key or malformed boundary')
    real_output=Path(real_output)
    require(real_output.resolve()!=private_output.resolve() and not real_output.resolve().is_relative_to(M),'Real step output must be separate from private file/cached machine')
    # Publish freshly constructed known fields, never relay arbitrary private text.
    with real_output.open('a') as f:f.write(expected)
    return True

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--actual-root-execution-adoption',type=Path,required=True)
    parser.add_argument('--actual-root-execution-adoption-sha256',required=True)
    parser.add_argument('--actual-parent-review-adoption',type=Path,required=True)
    parser.add_argument('--actual-parent-review-adoption-sha256',required=True)
    a=parser.parse_args();N=Path(__file__).resolve().parent
    validate_root(a.actual_root_execution_adoption,a.actual_root_execution_adoption_sha256,N);validate_parent_review(a.actual_parent_review_adoption,a.actual_parent_review_adoption_sha256,N);pins=verify_transport(N)
    ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';W=M/'video';T=ROOT/'official-main/视频/工具';O=ROOT/'source68-only-S6-local10ms6-public'
    require(not O.exists(),'Fresh scalar output namespace required')
    require(all(os.environ.get(k)=='1' for k in ['AUDIO_ONLY','STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']) and not any(os.environ.get(k) for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC','CACHE_LOG']),'Exact original STRICT modes and no acoustic override required')
    require(os.environ.get('S2_MOTHER_CACHE_HIT')==os.environ.get('S2_G36_CACHE_HIT')=='true','Exact existing S2 mother/math caches must hit')
    mother_api=cache_api_row(N/'actual-mother-cache-API.json',MOTHER_KEY,MOTHER_VERSION);math_api=cache_api_row(N/'actual-G36-cache-API.json',MATH_KEY,MATH_VERSION)
    profile=json.loads((N/'probe/baseline-profile.json').read_text());C=M/'tts/cache_tts'
    require(sha(N/'probe/inputs/source.json')==SOURCE_SHA==profile['inputs']['source']['sha256'],'Exact final same-byte request source required')
    for entries in profile['cache_entries'].values():
        for row in entries.values():
            for name,digest in [(row['name'],row['sha256']),(row['name']+'.单线程',row['single_thread_marker_sha256'])]:require((C/name).is_file() and not (C/name).is_symlink() and sha(C/name)==digest,'Required original finite cache missing/wrong; no fallback '+name)
    s6=profile['expected']['S6']['original_G36'];require((C/s6['file']).is_file() and not (C/s6['file']).is_symlink() and sha(C/s6['file'])==s6['sha256'],'S6 existing bb23 regular JSON required; never manufacture empty JSON')
    runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual run ID required for isolation')
    scratch=M/('_source68_onlyS6_local_setup_'+runid);require(not scratch.exists(),'Old diagnostic namespace cannot be reused');scratch.mkdir();O.mkdir()
    report={'kind':'actual-ROOT185b-independent-parent-bound-original-onlyS6-local-conditional-math-caller','ROOT_execution_delegation_sha256':ROOT_SHA,'actual_parent_independent_review_sha256':a.actual_parent_review_adoption_sha256,'helper_sha256':HELPER_SHA,'profile_sha256':PROFILE_SHA,'source_sha256':SOURCE_SHA,'transport_pin_count':len(pins),'quality_acceptance':False,'no_whole_TTS_GT_ASR_render_or_audio_export':True,'only_one_new_S6_original_math_if_missing':True,'restoration':{},'errors':[]};status=1
    try:
        observer=load('_source68_S6_S2_existing_namespace_guard',N/'probe/inputs/observer.py')
        with observer.work_namespace(W,scratch,report['restoration']):
            W.mkdir();subprocess.run([sys.executable,str(N/'install_actual_certified20_context.py')],check=True)
            sd=W/'scripts';sd.mkdir();source=sd/'68.json';require(not source.exists(),'Never replace existing source');source.write_bytes((N/'probe/inputs/source.json').read_bytes());require(sha(source)==SOURCE_SHA,'Initial isolated source copy differs')
            context=load('_source68_S6_S2_exact_original_context',N/'apply_exact_existing_S13_context_data.py')
            report['actual_shared_original_context']=context.apply(T,W,N/'source68-S13-context.json',N/'root-source68-S13-context-adoption.json',O/'68-actual-shared-S13-context-data.json')
            restore=load('_source68_S6_S2_original_G36_restore',N/'restore_exact_existing_S2_G36_JSON.py')
            saved=M/'tts/source68-only-target-whole-original-math-cache'/restore.NAME;destination=C/restore.NAME
            report['actual_S2_original_G36_readback']=restore.restore_existing_original_math(saved,destination,os.environ['S2_G36_CACHE_HIT'])
            require(sha(saved)==sha(destination)==profile['expected']['S2']['original_G36']['sha256'],'Original exact S2 single-G36 readback required')
            report['actual_target_cache_API']={'S2_mother':mother_api,'S2_G36':math_api};report['S6_preexisting_original_G36_sha256']=sha(C/s6['file'])
            report['actual_original_G27_before_fresh_helper']=verify_actual_original_G27(N,T,W)
            registry=T.parent/'配音缓存/老条目指纹.json';cand=W/'读音改正.json';ctx=W/'按语境读音.json'
            require(registry.is_file() and sha(registry)==profile['old_registry_SHA256'],'Actual immutable fc0 original old-cache registry differs')
            require(sha(cand)==sha(T/'发音词典/读音改正.json')==profile['dictionary_SHA256'] and sha(ctx)==sha(T/'发音词典/按语境读音.json')==profile['context_SHA256'],'Original first-candidate W/ROOT dictionary/context route differs')
            require(sha(W/'scripts/68.json')==SOURCE_SHA,'Fresh source-first W changed before helper')
            report['actual_source_first_context_setup_readback']={'original_registry_path':str(registry.resolve()),'original_registry_sha256':sha(registry),'original_first_cand_path':str(cand.resolve()),'dictionary_sha256':sha(cand),'original_first_CTX_path':str(ctx.resolve()),'context_sha256':sha(ctx),'fresh_source_path':str((W/'scripts/68.json').resolve()),'source_sha256':SOURCE_SHA,'SENT_NO_and_spoken_and_actual_pron_route_still_checked_by_unchanged_fresh_helper':True}
            status=subprocess.run(helper_argv(N,ROOT,M,T,O)).returncode;report['local_helper_exit']=status;report['actual_original_G27_after_helper']=verify_actual_original_G27(N,T,W)
            p=O/'68-onlyS6-local-two-phase-measurement.json';require(p.is_file(),'Actual local scalar missing');scalar=json.loads(p.read_text());report['actual_measurement_completed']=scalar['measurement_completed'];report['actual_local_diagnostic_passed']=scalar['diagnostic_passed']
            require(scalar['measurement_completed'] is True and scalar['errors']==[],'Original local measurement did not complete; never relax')
    except BaseException as error:report['errors'].append({'type':type(error).__name__,'detail':str(error)});traceback.print_exc();status=1
    finally:
        report['original_cached_video_inode_and_top_PCM_restored']=report['restoration'].get('normal_work_inode_and_PCM_restored') is True
        report['caller_measurement_completed']=report.get('actual_measurement_completed') is True and not report['errors'] and report['original_cached_video_inode_and_top_PCM_restored']
        report['caller_completed']=report['caller_measurement_completed'] and report.get('actual_local_diagnostic_passed') is True
        report['math_outputs_published_after_all_restores']=False
        try:
            if report['caller_measurement_completed']:
                scalar=json.loads((O/'68-onlyS6-local-two-phase-measurement.json').read_text())
                report['math_outputs_published_after_all_restores']=publish_verified_math_outputs(scalar,O/'68-onlyS6-private-math-step-output.txt',M,Path(os.environ['GITHUB_OUTPUT']),report['original_cached_video_inode_and_top_PCM_restored'])
        except BaseException as error:
            report['errors'].append({'type':type(error).__name__,'detail':str(error),'during':'verified-math-output-publication-after-outer-restore'});status=1;report['caller_completed']=False;report['caller_measurement_completed']=False
        if not report['caller_completed']:status=1
        (O/'68-onlyS6-local-actual-ROOT185b-binding-and-setup.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return status

if __name__=='__main__':sys.exit(main())

