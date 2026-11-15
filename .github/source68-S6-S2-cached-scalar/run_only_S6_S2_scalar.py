"""Concrete source68 S6/S2 bounded scalar caller; no actual execution yet.
Original cached-machine W inode isolation, actual20 setup and strict saved math.
No inference, whole, GT, ASR, render, source/CF change or waveform export.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, subprocess, sys, traceback
sys.dont_write_bytecode=True
ROOT_SHA='0b48f648ea974720a8b728587bb6190f4650720a9d2dda178ca5219538c2e831'
PARENT_SHA='dc9c25024b8bc7694e53098c839ca18c63e8106402540d47e4c3aee0aadf0b87'
HELPER_SHA='d53aebdd61c992473b6f3f455c23a852b979cd3fe8dce11f3fad35c576851ea4'
PROFILE_SHA='6ac2d576251651ef5d3ffdfd70f399c351b4af268df03d7259425027db128c7a'
H_SHA='2bcd57ac14b39674d0c5b83c93de1a98a2054063fedb243c2ce1f3f07b79d5fe'
SOURCE_SHA='e122c817946c4ed6e7cd1394749879276ef2afe9d01ad691b4142c6bbd9ec9b4'
MOTHER_KEY='Linux-native68-exact-S2-first-spoken-comma-43702410293'
MOTHER_VERSION='1876e5e5b689945a432f2564472935c78443d40f5d021a2378395bf71140c1d5'
MATH_KEY='Linux-native68-only-target-whole-original-math-43722945326'
MATH_VERSION='00b4c677297a43021c5f8c943aa224d49fb32065f82bcda32a2d8ddeb68c0931'
ARGV_SHA='53b57a75922e8552e9fcb9f3eabfdcb8cf0d09a9e61683dc70fb2a991f8c6e9b'
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
    p=Path(path);N=Path(package)
    require(literal_sha==ROOT_SHA and p.is_file() and not p.is_symlink() and sha(p)==ROOT_SHA,'Mandatory actual ROOT0b48 CLI record/fullSHA required before setup')
    require(p.read_bytes()==(N/'root-S6-S2-scalar-execution-delegation.json').read_bytes(),'ROOT transport copy differs')
    value=json.loads(p.read_text())
    require(value['handoff']['sha256']==H_SHA and value['helper']['sha256']==HELPER_SHA and value['profile']['sha256']==PROFILE_SHA,'Actual ROOT record must bind exact reviewed helper/profile/H')
    require(value['ROOT_did_not_personally_repeat_whole26271_helper_and43392_diff_review'] is True and value['actual_probe_not_yet_claimed'] is True and value['new_noise_or_word_cut_acceptance_not_granted'] is True,'ROOT delegation is not prior actual execution or voice acceptance')
    require(value['independent_full_logic_review_owner']=='/root/resume_audio_ci parent, distinct from child author /root/resume_audio_ci/analyze_51_edits','Only actual independent parent review may authorize sole transport')
    return value

def verify_transport(package):
    N=Path(package);rows=json.loads((N/'transport-file-pins.json').read_text())
    require(rows and len({r['relative'] for r in rows})==len(rows),'Finite unique transport pins required')
    for row in rows:
        rel=Path(row['relative']);require(not rel.is_absolute() and '..' not in rel.parts,'Transport escaped package')
        p=N/rel;require(p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'Frozen runtime transport differs '+str(rel))
    require(sha(N/'probe/observe68_only_S6_S2_actual_cached_scalars.py')==HELPER_SHA and sha(N/'probe/profile.json')==PROFILE_SHA and sha(N/'native-arguments.json')==ARGV_SHA and sha(N/'probe/SOURCE68-ONLY-S6-S2-ORIGINAL-CACHED-SCALAR-COMPLETE-CODE-DIFFS-54-COLD-TESTS-REVIEW-HANDOFF.json')==H_SHA,'Exact unchanged reviewed observer/profile/argv/H required')
    return rows

def validate_parent_review(path,literal_sha,package):
    p=Path(path)
    require(literal_sha==PARENT_SHA and p.is_file() and not p.is_symlink() and sha(p)==PARENT_SHA,'Actual independent parent review record/fullSHA is mandatory before setup or first HTTP')
    require(p.read_bytes()==(Path(package)/'actual-parent-independent-review-execution-adoption.json').read_bytes(),'Parent actual transport copy differs')
    value=json.loads(p.read_text())
    require(value['kind']=='ROOT-DELEGATED-independent-parent-full-code-review-and-bounded-source68-S6-S2-scalar-execution-adoption' and value['independent_review_owner']=='/root/resume_audio_ci, different from child author analyze_51_edits','Wrong actual independent review role')
    require(value['root_scope']['sha256']==ROOT_SHA and value['code_handoff_SHA256']==H_SHA and value['program_SHA256']==HELPER_SHA and value['profile_SHA256']==PROFILE_SHA,'Parent adoption must bind exact ROOT/code/profile')
    require(value['source_id']=='68' and value['book_order']==53 and value['targets']==['S6','S2'] and value['independent_review_passed'] is True and value['bounded_cache_only_scalar_execution_authorized'] is True and value['original54_cold_tests_independently_run_without_rewriting_frozenproof']['passed'] is True and value['all17_frozen_H_filepins_independently_verified'] is True and value['no_voice_or_CF_or_cut_acceptance'] is True,'Actual complete parent review/test/scope requirements not met')
    return value

def helper_argv(package,repo,machine,tools,public):
    N=Path(package);require(sha(N/'native-arguments.json')==ARGV_SHA,'Wrong closed arguments')
    d=json.loads((N/'native-arguments.json').read_text());require(d['root_execution_delegation_SHA256']==ROOT_SHA,'Argument ROOT role differs')
    require(list(d['arguments'])==['--tools','--video-root','--inputs','--profile','--output'],'Only exact unchanged helper CLI supported')
    mapping={'{{PACKAGE}}':str(N),'{{TOOLS}}':str(tools),'{{VIDEO_ROOT}}':str(machine),'{{PUBLIC}}':str(public)};args=[]
    for key,value in d['arguments'].items():
        for before,after in mapping.items():value=value.replace(before,after)
        require('{{' not in value,'Unresolved CLI role');args.extend([key,value])
    helper=Path(repo)/d['helper'];require(helper.resolve()==(N/'probe/observe68_only_S6_S2_actual_cached_scalars.py').resolve() and sha(helper)==HELPER_SHA,'Wrong two-sentence observer entrypoint')
    return [sys.executable,str(helper),*args]

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

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--actual-root-execution-adoption',type=Path,required=True)
    parser.add_argument('--actual-root-execution-adoption-sha256',required=True)
    parser.add_argument('--actual-parent-review-adoption',type=Path,required=True)
    parser.add_argument('--actual-parent-review-adoption-sha256',required=True)
    a=parser.parse_args();N=Path(__file__).resolve().parent
    validate_root(a.actual_root_execution_adoption,a.actual_root_execution_adoption_sha256,N);validate_parent_review(a.actual_parent_review_adoption,a.actual_parent_review_adoption_sha256,N);pins=verify_transport(N)
    ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';W=M/'video';T=ROOT/'official-main/视频/工具';O=ROOT/'source68-only-S6-S2-scalar-public'
    require(not O.exists(),'Fresh scalar output namespace required')
    require(all(os.environ.get(k)=='1' for k in ['AUDIO_ONLY','STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']) and not any(os.environ.get(k) for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC','CACHE_LOG']),'Exact original STRICT modes and no acoustic override required')
    require(os.environ.get('S2_MOTHER_CACHE_HIT')==os.environ.get('S2_G36_CACHE_HIT')=='true','Exact existing S2 mother/math caches must hit')
    mother_api=cache_api_row(N/'actual-mother-cache-API.json',MOTHER_KEY,MOTHER_VERSION);math_api=cache_api_row(N/'actual-G36-cache-API.json',MATH_KEY,MATH_VERSION)
    profile=json.loads((N/'probe/profile.json').read_text());C=M/'tts/cache_tts'
    require(sha(N/'probe/inputs/source.json')==SOURCE_SHA==profile['inputs']['source']['sha256'],'Exact final same-byte request source required')
    for entries in profile['cache_entries'].values():
        for row in entries.values():
            for name,digest in [(row['name'],row['sha256']),(row['name']+'.单线程',row['single_thread_marker_sha256'])]:require((C/name).is_file() and not (C/name).is_symlink() and sha(C/name)==digest,'Required original finite cache missing/wrong; no fallback '+name)
    s6=profile['expected']['S6']['original_G36'];require((C/s6['file']).is_file() and not (C/s6['file']).is_symlink() and sha(C/s6['file'])==s6['sha256'],'S6 existing bb23 regular JSON required; never manufacture empty JSON')
    runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual run ID required for isolation')
    scratch=M/('_source68_S6_S2_scalar_setup_'+runid);require(not scratch.exists(),'Old diagnostic namespace cannot be reused');scratch.mkdir();O.mkdir()
    report={'kind':'actual-ROOT0b48-and-parent-dc9c-bound-original-setup-only-source68-S6-S2-scalar-caller','ROOT_execution_delegation_sha256':ROOT_SHA,'actual_parent_independent_review_sha256':PARENT_SHA,'helper_sha256':HELPER_SHA,'profile_sha256':PROFILE_SHA,'argv_sha256':ARGV_SHA,'source_sha256':SOURCE_SHA,'transport_pin_count':len(pins),'quality_acceptance':False,'no_whole_TTS_new_math_GT_ASR_render_or_audio_export':True,'restoration':{},'errors':[]};status=1
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
            status=subprocess.run(helper_argv(N,ROOT,M,T,O)).returncode;report['unchanged_helper_exit']=status
            p=O/'68-S6-S2-bounded-original-cached-scalars.json';require(p.is_file(),'Actual scalar output missing');scalar=json.loads(p.read_text());report['unchanged_helper_diagnostic_completed']=scalar['diagnostic_completed']
            require(status==0 and scalar['diagnostic_completed'] is True and scalar['errors']==[],'Bounded original observation did not complete; never relax')
    except BaseException as error:report['errors'].append({'type':type(error).__name__,'detail':str(error)});traceback.print_exc();status=1
    finally:
        report['original_cached_video_inode_and_top_PCM_restored']=report['restoration'].get('normal_work_inode_and_PCM_restored') is True
        report['caller_completed']=status==0 and not report['errors'] and report['original_cached_video_inode_and_top_PCM_restored']
        if not report['caller_completed']:status=1
        (O/'68-S6-S2-actual-ROOT0b48-binding-and-setup.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return status

if __name__=='__main__':sys.exit(main())

