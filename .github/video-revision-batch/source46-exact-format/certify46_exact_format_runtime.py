#!/usr/bin/env python3
"""Root-reviewed source46 format installation + ORIGINAL full fastcheck.

This is code certification, not article audio/native acceptance. Default mode
only validates the immutable capsule; --write-runtime is CI-only and must be
called after the old certified five-core was genuinely installed/verified.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROFILE_SHA256 = 'dff235ffef04da423b7a576e4bdfaf8adeec8a1673afa5b1a012fe5bbc6a9dbe'
CI_ROOT = Path('/home/runner/work/literate-enigma/literate-enigma')
FIXTURE_CONTEXT_SHA256 = 'f8bfcf8b8a455070b13e51adabb08dee55de10166ae46e6dcbc4f5113262c104'
HISTORICAL_FIXTURE_MANIFEST_SHA256 = 'e81d2f49eea100c89a75cbe286b1f8422e4e80e993f59e05c0db3d3e361805bd'
OLD_STAMP_SHA256 = '95a51b15bb4b71b8842851da8d16bb4109231f1ba69e24826792f2a718ef4a4a'
OLD_FIVE_CORE = {
 '草稿声音.sh':'c45c66e3cf68a380f5c829600cf6b0ed69f49f24c65e91c0330ed17d1a85475e',
 '句内响度.py':'9c5691cf59dc7776e822461044e50031ff118de29d7ae0769781a1cc66664bea',
 '独立复核/synth.py':'a0c9cad9ac953e68768470e8181f7e325c8ee8ff08ca57b68bbd136b99b83264',
 '结尾句接点.py':'1a5d43c4f5483014b69bbea7ad43dddb0333a9a80e29bb2b4c8029d8915ff798',
 '读音核对.py':'50f4363bb2fc2930be59904cdccfa44fd46f14393a0385c7846028ee25b4e84c',
}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def pin(p,value):
    p=Path(p);require(p.resolve(strict=True)==p and p.is_file(),'noncanonical file '+str(p))
    require(sha(p)==value['sha256'] and p.stat().st_size==value['bytes'],'file identity '+str(p))

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--capsule',required=True,type=Path)
    a.add_argument('--repository',required=True,type=Path)
    a.add_argument('--video-root',required=True,type=Path)
    a.add_argument('--root-decision',required=True,type=Path)
    a.add_argument('--root-decision-sha256',required=True)
    a.add_argument('--output',required=True,type=Path)
    a.add_argument('--setup-fix-decision',type=Path)
    a.add_argument('--setup-fix-decision-sha256')
    a.add_argument('--historical-fixtures',type=Path)
    a.add_argument('--write-runtime',action='store_true')
    args=a.parse_args()
    report={'kind':'source46-exact-user-format-original-full-fastcheck-code-certificate',
        'article':'46','book_order':48,'code_certification_passed':False,
        'native_article_passed':False,'article_audio_accepted':False,
        'audio_or_confirmation_metadata_approved_by_format_helper':False,
        'runtime_installed':False,'stage':'capsule-validation','checks':[]}
    def save():
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    try:
        capsule=args.capsule.resolve(strict=True)
        root=args.repository.resolve(strict=True);T=root/'视频/工具';M=args.video_root.resolve(strict=True);W=M/'video'
        require(args.repository==root and args.video_root==M,'canonical original root arguments')
        profile=capsule/'code-profile.json'
        require(sha(profile)==PROFILE_SHA256,'code profile mismatch')
        p=json.loads(profile.read_text())
        require(p['source_id']=='46' and p['book_order']==48,'wrong article scope')
        request=root/'.github/video-revision-batch/request/46/视频/脚本/46.json'
        pin(request,p['request'])
        require(len(args.root_decision_sha256)==64 and args.root_decision_sha256!='0'*64,'actual root adoption SHA required')
        require(sha(args.root_decision)==args.root_decision_sha256,'actual root adoption bytes mismatch')
        adoption=json.loads(args.root_decision.read_text())
        require(adoption.get('source_id')=='46' and adoption.get('book_order')==48,
                'root adoption must identify source46/book48')
        require(adoption.get('candidate_code_profile_sha256')==PROFILE_SHA256
                and adoption.get('code_only_runtime_certification_authorized') is True,
                'actual root decision must adopt this exact code profile and original full certification')
        report['actual_root_code_adoption']={'file':str(args.root_decision),'sha256':sha(args.root_decision)}
        candidates=capsule/'candidate/视频/工具'
        for n,item in p['candidate_programs'].items():pin(candidates/n,item)
        binding=capsule/'review-profiles/exact-CI-and-local-rehearsal-binding.json';pin(binding,p['binding'])
        proofs=root/'.github/video-revision-batch/source46-user-format-proofs'
        for item in p['proofs'].values():
            q=proofs/item['file'];require(q.resolve(strict=True)==q and sha(q)==item['sha256'],'actual raw user proof mismatch')
        report['immutable_request_sha256']=sha(request)
        report['candidate_programs']=p['candidate_programs']
        report['checks'].append('All four code files, exact binding, immutable118f and all three raw user proofs match reviewed capsule.')
        if not args.write_runtime:
            report['stage']='code-only-preflight-complete-not-installed';save();return 0
        require(root==CI_ROOT,'runtime installation is only the actual original CI checkout role')
        require(args.setup_fix_decision is not None and args.setup_fix_decision_sha256 is not None, 'separate actual root setup-fix adoption required')
        require(len(args.setup_fix_decision_sha256)==64 and sha(args.setup_fix_decision)==args.setup_fix_decision_sha256, 'setup-fix adoption raw bytes mismatch')
        setup_adoption=json.loads(args.setup_fix_decision.read_text())
        require(setup_adoption.get('source_id')=='46' and setup_adoption.get('book_order')==48 and setup_adoption.get('setup_fix_code_only_certification_authorized') is True, 'root setup-fix adoption scope mismatch')
        require(setup_adoption.get('candidate_code_profile_sha256')==PROFILE_SHA256 and setup_adoption.get('historical_fixture_manifest_sha256')==HISTORICAL_FIXTURE_MANIFEST_SHA256 and setup_adoption.get('corrected_certifier_sha256')==sha(__file__) and setup_adoption.get('fixture_context_sha256')==FIXTURE_CONTEXT_SHA256, 'root setup-fix adoption must bind exact existing format profile/new caller/context/historical resource')
        fixture_module=capsule/'historical95_fixture_context.py'
        require(sha(fixture_module)==FIXTURE_CONTEXT_SHA256, 'fixture restoration module mismatch')
        fixture_spec=importlib.util.spec_from_file_location('_source46_actual95_fixture_context',fixture_module)
        F=importlib.util.module_from_spec(fixture_spec);fixture_spec.loader.exec_module(F)
        report['actual_original_font_context'] = F.validate_runtime_context(root,T,W)
        fixture_package=args.historical_fixtures.resolve(strict=True) if args.historical_fixtures else capsule/'original95-certification-fixtures'
        F.prepare_fixture_plan(root,W,fixture_package)
        report['actual_setup_fix_root_code_adoption']={'file':str(args.setup_fix_decision),'sha256':sha(args.setup_fix_decision)}
        report['original_alias_and_ROOT_W_fonts_preexist_before_fullquick']=True
        require(Path(os.environ['RUNNER_TEMP']).resolve(strict=True)/'completion-machine'==M,'original RUNNER_TEMP machine relationship')
        require(Path(os.environ['XG_P']).resolve(strict=True)==root and Path(os.environ['XG_TOOLS']).resolve(strict=True)==T,'original root/tools environment')
        require(Path(os.environ['XG_WORK']).resolve(strict=True)==W and Path(os.environ['VIDEO_ROOT']).resolve(strict=True)==M,'original W/environment')
        require(os.environ.get('STRICT_CACHE')=='1' and os.environ.get('XG_NOPUSH')=='1','strict cache/nopush required')
        require(os.environ.get('XG_KEEP_REVIEWED_GAIN')=='1' and os.environ.get('XG_KEEP_REVIEWED_ENDING')=='1','original five-core preservation modes')
        require(os.environ.get('XG_KEEP_REVIEWED_CUTS') in (None,''),'do not import later CUTS-mode into original46 profile')
        for n,h in OLD_FIVE_CORE.items():require(sha(T/n)==h,'original five-core file changed '+n)
        for n,h in p['baseline_programs'].items():require(sha(T/n)==h,'baseline gate/maker changed '+n)
        for n,h in p['original_fastcheck'].items():
            q=T/n if n=='出片指纹.py' else T/'新管'/n
            require(sha(q)==h,'original full fastcheck/verifier/copy program changed')
        stamp=T/'新管/快测通过.json'
        require(sha(stamp)==OLD_STAMP_SHA256,'genuine old95a stamp required before installation')
        report['original_fivecore_stamp_sha256']=sha(stamp)
        env=dict(os.environ)
        def run(label,argv,timeout):
            report['stage']=label;save()
            log=args.output.parent/(label+'.log')
            with log.open('w') as s:
                r=subprocess.run([str(x) for x in argv],cwd=W,env=env,stdout=s,stderr=subprocess.STDOUT,timeout=timeout)
            row={'name':label,'argv':[str(x) for x in argv],'exit':r.returncode,'log':str(log),'log_sha256':sha(log)}
            report.setdefault('actual_steps',[]).append(row);save()
            require(r.returncode==0,label+' failed; original log retained')
        run('original-fivecore-stamp-before-format-install',['python3',T/'新管/印章.py'],120)
        # Copy only the four reviewed files; no rules, numerical gates, core,
        # source/GEN/MD, model/cache, or original reference data is edited.
        for n in p['candidate_programs']:
            target=T/n
            require(not target.is_symlink(),'refuse symlink target '+n)
            shutil.copyfile(candidates/n,target)
        shutil.copyfile(binding,T/'_source46_exact_user_format_binding.json')
        report['runtime_installed']=True
        run('original-module-copy-with-exact-format-helper',['python3',T/'出片指纹.py','--拷',W],120)
        # ORIGINAL full quickcheck is mandatory. There is no --盖 call here,
        # text-only option, edited benchmark, or synthesized stamp.
        fixture_evidence={}
        report['actual_original95_historical_fixture_context']=fixture_evidence
        with F.temporary_historical_fixtures(root,W,fixture_package,fixture_evidence):
            run('original-full-fastcheck-after-format-install',['python3',T/'新管/快测.py'],1800)
            run('original-new-stamp-verification',['python3',T/'新管/印章.py'],120)
            actual=json.loads(stamp.read_text())
            for n,item in p['candidate_programs'].items():
                require(actual['程序'].get(n)==item['sha256'][:16],'actual new stamp missing '+n)
                require(sha(T/n)==item['sha256'],'installed program changed during quickcheck '+n)
        require(fixture_evidence.get('original_files_or_absence_restored') is True, 'historical regression data must be restored before production continues')
        require(sha(stamp)!=OLD_STAMP_SHA256,'old stamp cannot certify new programs')
        new_copy=args.output.parent/'source46-actual-new-format-full-fastcheck-stamp.json'
        shutil.copyfile(stamp,new_copy)
        report['actual_original_generated_new_stamp']={'file':str(new_copy),'bytes':new_copy.stat().st_size,'sha256':sha(new_copy)}
        report['code_certification_passed']=True
        report['stage']='actual-original-full-fastcheck-code-certification-passed-not-native'
        save();return 0
    except BaseException as exc:
        report['error']={'type':type(exc).__name__,'message':str(exc)[:1500]}
        save()
        print(json.dumps(report,ensure_ascii=False),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
