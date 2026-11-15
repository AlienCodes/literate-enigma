"""Selected-only original cached AudioOnly -> original A21 private metadata preview.

No baseline replay, new primary TTS, new G36 mathematics, GT, ASR or image render.
Every official canonical quality check is still required after this precondition.
"""
from pathlib import Path
import argparse,contextlib,hashlib,importlib.util,io,json,os,sys,traceback
sys.dont_write_bytecode=True
MAKERS={'68':'0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36','23':'1b87c1d4d1685bdd59325587184cca35f853354a015e6fe89c11f150cd2a6239','56':'1b87c1d4d1685bdd59325587184cca35f853354a015e6fe89c11f150cd2a6239'}
BOOKS={'68':53,'23':62,'56':65}
def require(ok,msg):
    if not ok:raise AssertionError(msg)
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def load(name,p):s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def directory_snapshot(path):
    p=Path(path)
    if not p.exists():return{'exists':False}
    require(p.is_dir()and not p.is_symlink(),'Private work must be a real directory')
    files={}
    for f in sorted(p.rglob('*')):
        require(not f.is_symlink(),'Do not follow private work symlinks')
        if f.is_file():files[str(f.relative_to(p))]={'bytes':f.stat().st_size,'sha256':digest(f)}
    return{'exists':True,'inode':p.stat().st_ino,'files':files}
def verify_selected_phase_at_work(work,phase):
    work=Path(work)
    require(digest(work/'a.wav')==phase['actual_complete_WAV']['file_sha256'],'A21 work is not the just-proved selected WAV')
    for filename,key in [('分段.json','actual_original_piece_time_table'),('句子声音指纹.json','actual_voice_fingerprint_table')]:
        require(json.loads((work/filename).read_text())==phase[key],'A21 selected work metadata mismatch: '+filename)

@contextlib.contextmanager
def selected_phase_work_namespace(observer,normal,selected,scratch,phase,restoration):
    """Bind the actual new phase inode at the original checker's work_NO path."""
    normal,selected,scratch=map(Path,(normal,selected,scratch))
    # Fresh flags cannot inherit successful phase-assembly restoration values.
    require(not restoration,'A fresh independent selected binding restoration is required')
    restoration.update(normal_work_inode_and_PCM_restored=False,selected_phase_inode_and_all_files_restored=False,actual_selected_phase_bound_at_original_work_path=False)
    require(selected!=normal and selected.is_dir()and not selected.is_symlink(),'Wrong private selected work role')
    before=directory_snapshot(selected);verify_selected_phase_at_work(selected,phase)
    require(not scratch.exists(),'Fresh selected binding scratch required');scratch.mkdir()
    try:
        with observer.work_namespace(normal,scratch,restoration):
            require(not os.path.lexists(normal),'Original work namespace was not isolated')
            os.replace(selected,normal)
            try:
                require(directory_snapshot(normal)==before,'Selected inode/files changed at original work path')
                verify_selected_phase_at_work(normal,phase)
                restoration['actual_selected_phase_bound_at_original_work_path']=True
                yield
            finally:
                # Always restore the selected inode to its genuine private phase
                # path, even when the original checker raises or its output is bad.
                require(not os.path.lexists(selected),'Selected private path unexpectedly occupied')
                require(normal.is_dir()and not normal.is_symlink()and normal.stat().st_ino==before['inode'],'Selected work inode replaced during preview')
                os.replace(normal,selected)
                restoration['selected_phase_inode_and_all_files_restored']=directory_snapshot(selected)==before
    finally:
        require(restoration['normal_work_inode_and_PCM_restored']is True,'Original normal work inode/PCM was not restored')
        require(restoration['selected_phase_inode_and_all_files_restored']is True,'Actual selected phase files changed during metadata-only preview')

def validate_adoption(d,helper_sha,profile_sha,kernel_sha,no):
    expected={'source_id':no,'book_order':BOOKS[no],'helper_SHA256':helper_sha,'profile_SHA256':profile_sha,'kernel_SHA256':kernel_sha,'selected_only_original_cached_whole_then_A21_private_metadata_authorized':True,'new_TTS_or_new_math_or_GT_or_ASR_or_render_authorized':False,'owner_source_write_authorized':False}
    require(not str(d.get('kind','')).startswith('TEMPLATE')and all(type(d.get(k))is type(v)and d[k]==v for k,v in expected.items()),'Exact parent/ROOT execution adoption required for this new assembly')
def require_existing_math(key,cache,expected):
    if key is None:return
    name='调平_'+key+'.json';require(name in expected,'Unknown actual G36 key; do not calculate: '+name)
    p=Path(cache)/name;require(p.is_file()and not p.is_symlink()and digest(p)==expected[name],'Exact original G36 JSON missing or changed; no recomputation: '+name)
def guard_original_math_factory(observer,original_factory,expected,cache,events):
    def factory(module,original,phase,state,profile,result,new_math):
        observe=original_factory(module,original,phase,state,profile,result,new_math)
        def existing_only(clips,tmap,gaps,no='',rounds=2):
            current=module._auto_level;module._auto_level=original
            try:key=observer.auto_key(module,clips,tmap,gaps,no)
            finally:module._auto_level=current
            require_existing_math(key,cache,expected)
            require(os.environ.get('STRICT_CACHE')=='1','Original G36 reads must remain strict')
            value=observe(clips,tmap,gaps,no,rounds)
            require(os.environ.get('STRICT_CACHE')=='1'and not new_math,'Original observer attempted a new G36 calculation')
            require_existing_math(key,cache,expected);events.append({'existing_key':key,'strict_before_after':True,'new_math':False})
            return value
        return existing_only
    return factory

def main():
    p=argparse.ArgumentParser()
    for k in ['tools','video-root','source','working-source','reference-report','observer','support','original-profile','overlay','certificate','identity','kernel','profile','execution-adoption','output']:p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--execution-adoption-sha256',required=True);a=p.parse_args();T=a.tools.resolve();M=a.video_root.resolve();W=M/'video';cache=M/'tts/cache_tts';out=a.output.resolve()
    report={'kind':'same_job_selected_original_cached_whole_and_A21_physical_metadata_precondition','diagnostic_completed':False,'physical_metadata_precheck_ready':False,'quality_acceptance':False,'production_delivery_eligible':False,'forbidden_model_events':[],'errors':[],'restoration':{},'phases':{},'no_baseline_GT_ASR_or_render':True}
    observer=None;old_math_factory=None;cache_before=None;public_before=None;normal_before=None;phase_work=None;phase_before=None;frozen_before=None;saved_modules={};log=io.StringIO()
    try:
        profile=json.loads(a.profile.read_text());no=profile['source_id'];require(no in MAKERS and profile['book_order']==BOOKS[no],'Wrong finite source');report.update(source_id=no,book_order=BOOKS[no])
        require(digest(a.execution_adoption)==a.execution_adoption_sha256,'Wrong assembly execution adoption SHA')
        validate_adoption(json.loads(a.execution_adoption.read_text()),digest(__file__),digest(a.profile),digest(a.kernel),no)
        require(not out.is_relative_to(M),'Public diagnostic output must remain outside private machine')
        inputs={'source':a.source,'reference_report':a.reference_report,'observer':a.observer,'support':a.support,'original_profile':a.original_profile,'overlay':a.overlay,'certificate':a.certificate,'identity':a.identity,'kernel':a.kernel}
        require(all(digest(path)==profile['input_SHA256'][name]for name,path in inputs.items()),'Wrong frozen assembly input')
        require(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKERS[no]and digest(T/'新管/快测通过.json')==profile['stamp_SHA256'],'Wrong actual certified maker/stamp')
        require(all(os.environ.get(k)=='1'for k in ['STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']),'Original reviewed strict modes required')
        require(not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC']),'Unreviewed overrides')
        kernel=load('_original_A21_kernel_'+no,a.kernel);source=json.loads(a.source.read_text());working=json.loads(a.working_source.read_text());require(str(source['no'])==str(working['no'])==no,'Wrong source JSON role')
        require(not kernel.physical_delta(source,working),'Working source already has an unreviewed physical difference from frozen request')
        require(kernel.typed(source.get('区间声音指纹'))==kernel.typed(working.get('区间声音指纹')),'Actual raw-fingerprint metadata differs from frozen request')
        for category in ['词尾辅音','双爆破','除阻加强放宽']:require(kernel.typed(source.get('核对确认',{}).get(category))==kernel.typed(working.get('核对确认',{}).get(category)),'A21 approval category changed in working data: '+category)
        identity=json.loads(a.identity.read_text());require({k:digest(M/'tts'/k)for k in identity['models_SHA256']}==identity['models_SHA256']and digest(M/'tts/voice_mb.npy')==identity['voice_SHA256'],'Actual original model/voice fullSHA mismatch')
        original_profile=json.loads(a.original_profile.read_text());reference=json.loads(a.reference_report.read_text());require(reference['exact_scope_proved']is True and reference['source_id']==no,'Actual successful selected whole reference required');known=reference['phases']['selected']
        require(known['actual_complete_WAV']['file_sha256']==profile['expected_whole']['RAW_SHA256'],'Wrong known physical WAV role')
        require(known['actual_codec_packet_payload_side_and_absolute_clock']==profile['expected_whole']['standard_AAC'],'Wrong standard packet/priming/absolute clock reference')
        observer=load('_actual_original_single_selected_'+no,a.observer);support=load('_actual_original_source_support_'+no,a.support);require(observer.SOURCE_NO==support.SOURCE_NO==no and observer.MAKER_SHA256==MAKERS[no],'Wrong original whole/cache/source namespace ABI')
        support.validate_certificate(T,json.loads(a.overlay.read_text()),json.loads(a.certificate.read_text()))
        require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent,'Original canonical ROOT alias differs')
        require(digest(T/'环境/模型校验码.json')==digest(W/'环境/模型校验码.json')==observer.REGISTRY_SHA256,'Original portable model registry differs')
        require(digest(T/'发音词典/读音改正.json')==observer.DICT_SHA256 and digest(T/'发音词典/按语境读音.json')==profile['context_SHA256'],'Wrong original actual dictionary context')
        for name,h in identity['actual_four_private_files'].items():require(digest(cache/name)==h,'Exact existing selected mother/marker differs: '+name)
        expected_math={row['file']:row['sha256']for row in known['original_G36_calls']if row.get('file')}
        require(expected_math==profile['existing_original_G36_JSON_SHA256'],'Finite actual original G36 dependency map differs')
        for name,h in expected_math.items():require((cache/name).is_file()and not(cache/name).is_symlink()and digest(cache/name)==h,'Original G36 must hit before source execution: '+name)
        require(digest(M/'tts/AF.txt')==known['AF_sha256'],'Original complete-track AF changed')
        cache_before=observer.inventory(cache);public_before=observer.inventory(T.parent/'配音缓存');normal_before=directory_snapshot(W/('work_'+no));frozen_before={str(x):digest(x)for x in list(inputs.values())+[a.profile,a.working_source,T/'make_video.py',W/'make_video.py',T/'新管/快测通过.json',T/'词尾辅音核对.py',T/'发音词典/读音改正.json',T/'发音词典/按语境读音.json',T/'环境/模型校验码.json',W/'环境/模型校验码.json',M/'tts/voice_mb.npy',M/'tts/AF.txt']+[M/'tts'/k for k in identity['models_SHA256']]}
        for name in ('render','title2','clean','出片指纹'):saved_modules[name]=sys.modules.get(name)
        runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual native run ID required for fresh private same-job namespace')
        scratch=M/('_A21_metadata_selected_'+no+'_'+runid);require(not scratch.exists(),'Fresh private same-job selected-only namespace required');scratch.mkdir();paths={'T':T,'M':M,'W':W,'scratch':scratch};observer.CACHE=cache
        old_math_factory=observer.math_guard;math_events=[];observer.math_guard=guard_original_math_factory(observer,old_math_factory,expected_math,cache,math_events);used={};new_math={}
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            with support.environment_and_cwd(W,report['restoration']):
                with observer.work_namespace(W/('work_'+no),scratch,report['restoration']):
                    with support.source_namespace(W,a.source.read_bytes(),report['restoration']):
                        observer.run_phase('selected',a.source.read_bytes(),digest(a.source),paths,support,original_profile,report,used,new_math)
            observer.math_guard=old_math_factory;report['restoration']['original_observer_math_factory_restored']=observer.math_guard is old_math_factory
            phase=report['phases']['selected'];require(phase['actual_complete_WAV']['file_sha256']==profile['expected_whole']['RAW_SHA256'],'Actual same-job selected WAV differs from measured identity')
            require(phase['actual_codec_packet_payload_side_and_absolute_clock']==profile['expected_whole']['standard_AAC'],'Actual same-job selected AAC/packet/absolute clock differs')
            require(not new_math and not report['forbidden_model_events'],'A new model or G36 operation occurred')
            phase_work=Path(phase['private_work_preserved_path']);require(phase_work.resolve().is_relative_to(M),'Private phase path escaped machine');phase_before=directory_snapshot(phase_work)
            report['same_job_exact_selected_whole_reproduced_before_metadata_preview']=True
            report['selected_work_binding_restoration']={}
            with selected_phase_work_namespace(observer,W/('work_'+no),phase_work,scratch/'A21-selected-binding',phase,report['selected_work_binding_restoration']):
                report['A21_metadata_preview']=kernel.preview(T,M,a.source,phase,observer,support,profile,report['forbidden_model_events'])
        report['cached_original_G36_reads']=math_events;report['new_original_G36_JSONs']=new_math;report['whole_original_cached_model_entries']=list(used.values());report['original_private_execution_log']=log.getvalue();report['diagnostic_completed']=True
    except BaseException as e:report['errors'].append({'type':type(e).__name__,'message':str(e)});traceback.print_exc()
    finally:
        if observer is not None and old_math_factory is not None:observer.math_guard=old_math_factory;report['restoration']['original_observer_math_factory_restored']=observer.math_guard is old_math_factory
        for name,value in saved_modules.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value
        report['entire_existing_private_cache_unchanged']=cache_before is not None and observer.inventory(cache)==cache_before
        report['original_public_cache_unchanged']=public_before is not None and observer.inventory(T.parent/'配音缓存')==public_before
        report['normal_work_inode_and_all_files_restored']=normal_before is not None and directory_snapshot(W/('work_'+report['source_id']))==normal_before
        report['new_private_phase_work_not_modified_by_metadata_preview']=phase_before is not None and directory_snapshot(phase_work)==phase_before
        report['all_frozen_inputs_and_original_program_bytes_unchanged']=frozen_before is not None and all(digest(x)==h for x,h in frozen_before.items())
        checks=['entire_existing_private_cache_unchanged','original_public_cache_unchanged','normal_work_inode_and_all_files_restored','new_private_phase_work_not_modified_by_metadata_preview','all_frozen_inputs_and_original_program_bytes_unchanged'];rest=['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored','original_observer_math_factory_restored']
        report['diagnostic_completed']=bool(report['diagnostic_completed']and all(report.get(k)is True for k in checks)and all(report['restoration'].get(k)is True for k in rest)and all(report.get('selected_work_binding_restoration',{}).get(k)is True for k in ['normal_work_inode_and_PCM_restored','selected_phase_inode_and_all_files_restored','actual_selected_phase_bound_at_original_work_path']))
        report['physical_metadata_precheck_ready']=bool(report['diagnostic_completed']and report['A21_metadata_preview']['original_A21_no_bad_and_physical_fields_unchanged'])
        report['scope_limit']='One original selected-only cached AudioOnly proves actual private phase identity, then only original A21 check/write_grafts metadata is previewed. No baseline/GT/ASR/render or full canonical QA is run. Original full shell and every original quality gate remain mandatory. Unknown metadata changes are reported and never adopted.'
        out.parent.mkdir(parents=True,exist_ok=True);require(not out.exists(),'Never overwrite a previous diagnostic');out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return 0 if report['physical_metadata_precheck_ready']else(2 if report['diagnostic_completed']else 1)
if __name__=='__main__':sys.exit(main())
