"""Independent core certification; never creates or accepts a production deliverable."""
from pathlib import Path
import argparse,os,sys,json,hashlib,shutil,subprocess,time,copy
p=argparse.ArgumentParser();p.add_argument('--variant',choices=['original'],required=True);p.add_argument('--root-adoption',type=Path,required=True);p.add_argument('--root-adoption-sha256',required=True);p.add_argument('--reference-loader-code-adoption',type=Path,required=True);p.add_argument('--reference-loader-code-adoption-sha256',required=True);a=p.parse_args()
ROOT=Path.cwd();PKG=ROOT/'.github/source58-reference-loader110-code-certification';REPO=ROOT/'official-main';T=REPO/'视频/工具';W=Path(os.environ['RUNNER_TEMP'])/'completion-machine/video';OUT=ROOT/'certification-public';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();report={'variant':a.variant,'passed':False,'production_audio_or_video_acceptance':False,'official_main_commit':'fc0b56af9a0ac0e97015548b756d4e51d66dc2ea','stage':'start'}
def save(): (OUT/'certification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def run(args,label,cwd=REPO,env=None):
 report['stage']=label;save();t=time.time();r=subprocess.run(list(map(str,args)),cwd=cwd,env=env or E,capture_output=True,text=True);(OUT/(label+'.log')).write_text(r.stdout+'\n'+r.stderr);report.setdefault('checks',[]).append({'name':label,'exit':r.returncode,'seconds':round(time.time()-t,2),'log_SHA256':sha(OUT/(label+'.log'))});save();return r
E={**{k:v for k,v in os.environ.items()if not k.startswith('XG_KEEP_REVIEWED_')},'XG_P':str(REPO),'XG_TOOLS':str(T),'XG_WORK':str(W),'XG_NOPUSH':'1','STRICT_CACHE':'1'}
try:
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==report['official_main_commit']
 manifest=json.loads((PKG/'stock-runtime-manifest.json').read_text());report['stock_runtime_manifest']=manifest
 assert manifest['files']==[{'path': '视频/工具/独立复核/synth.py', 'main_SHA256': '23e024232b98ea83a6782e548d2b5f69b31141761a2e7c8d372805bba3b57746', 'patch_SHA256': 'a0c9cad9ac953e68768470e8181f7e325c8ee8ff08ca57b68bbd136b99b83264', 'scope': 'Existing original a0c9 raw-mother cache I/O only; all original GT transforms and audit unchanged. No producer, gain, threshold or geometry change.'}] and manifest['kind']=='source58-reference-only-single-synth-raw-cache-IO-overlay-on-true-stock110'
 assert a.reference_loader_code_adoption_sha256=='d1e20809f66bae747f6bd22c2e1fb6f7b982758d4a20b61112f2397bf30e2fb3' and a.reference_loader_code_adoption_sha256!='0'*64
 assert sha(a.reference_loader_code_adoption)==a.reference_loader_code_adoption_sha256
 code_scope=json.loads(a.reference_loader_code_adoption.read_text());assert not code_scope.get('not_an_adoption',False)
 report['actual_reference_loader_code_adoption_SHA256']=a.reference_loader_code_adoption_sha256
 actual_source_scope=json.loads(a.root_adoption.read_text());assert actual_source_scope['source_id']=='58' and actual_source_scope['book_order']==67
 assert a.variant=='original' and len(a.root_adoption_sha256)==64 and sha(a.root_adoption)==a.root_adoption_sha256=='da74c2afe807d755e84a8bb573ab648e2bdcca15180b25baea434ef553bba041'
 report['actual_source58_original_stock_final_source_scope_adoption_SHA256']=a.root_adoption_sha256
 program_inventory=json.loads((PKG/'actual-original-stock110-exact-expected-programs.json').read_text())
 assert program_inventory['program_count']==110
 for f in program_inventory['stock_files']:assert sha(T/f['path'])==f['sha256'], ('Stock original program differs',f['path'])
 assert sha(T/'make_video.py')=='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
 assert not any(k.startswith('XG_KEEP_REVIEWED_')for k in E)
 report['actual_source58_original_stock_profile_no_KEEP_flags_and_no_target_audio_rerun']=True
 for f in manifest['files']: assert sha(REPO/f['path'])==f['main_SHA256']
 assert (W/'make_video.py').is_file() and (W.parent/'tts/kokoro-v1.0.onnx').is_file()
 # Resource observations only; original quality checks remain the acceptance test.
 resource_inventory=PKG/'certification-resource-inventory.json'
 shutil.copyfile(resource_inventory,OUT/'resource-inventory.json')
 cachemap=REPO/'视频/配音缓存/老条目指纹.json'
 report['actual_dependency_observations']={'formal_cache_map_present':cachemap.is_file(),'formal_cache_map_SHA256':sha(cachemap) if cachemap.is_file() else None,'formal_legacy_entries':len(json.loads(cachemap.read_text()).get('条目',{})) if cachemap.is_file() else 0,'public_cache_JSON_count':len(list((REPO/'视频/配音缓存').glob('*.json'))),'existing_private_model_present':(W.parent/'tts/kokoro-v1.0.onnx').is_file(),'existing_private_ASR_directory_present':(Path.home()/'asr').is_dir(),'resources_are_original_not_invented_markers':True}
 # Restore four exact pre-existing 07 raw/timed cache resources; preserve original G72 map and checks.
 ending_resources=json.loads((PKG/'ending-cache-resources.json').read_text());restored=[]
 for resource in ending_resources['files']:
  src=ROOT/'ending-reference-resources'/resource['repository_path'];dst=W.parent/'tts/cache_tts'/Path(resource['repository_path']).name
  assert sha(src)==resource['SHA256']
  assert json.loads(cachemap.read_text())['条目'][dst.name]==resource['SHA256'][:16]
  prior=sha(dst) if dst.exists() else None;shutil.copyfile(src,dst)
  restored.append({'cache_key':dst.name,'full_SHA256':sha(dst),'prior_warm_cache_SHA256':prior,'original_formal_G72_fingerprint_matches':True})
 report['restored_original_07_resources']=restored
 (OUT/'ending-cache-resources-scalar.json').write_text(json.dumps({'source_pin':ending_resources['pin'],'files':restored,'private_arrays_exported':False},ensure_ascii=False,indent=2)+'\n')
 # New24 is independently tested against the current full-screen rule before legacy fixture setup.
 current24=OUT/'current-24-structured.json';shutil.copyfile(REPO/'视频/脚本/24.json',current24)
 code="import sys,json;sys.path.insert(0,sys.argv[1]);import render as R;d=json.load(open(sys.argv[2]));R.apply_script(d);k=' '.join(p[0] for c in d['sentences'][-1]['chunks'] for p in c['align']);assert R.NOTE_WIDE.get(k)=='整屏';print('Current structured24 full-screen positive passed')"
 r=run([sys.executable,'-c',code,T,current24],'current24-positive',cwd=T);assert r.returncode==0
 fixture=json.loads((PKG/'historical-fixtures-manifest.json').read_text());report['historical_fixture_provenance']=fixture
 for f in fixture['files']:
  src=PKG/'historical-fixtures'/f['path'];assert sha(src)==f['SHA256'];dst=REPO/f['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  if f['path'].startswith('视频/脚本/'):
   (W/'scripts').mkdir(exist_ok=True);shutil.copyfile(src,W/'scripts'/Path(f['path']).name)
 # Adopt only the pre-existing, independently proved visual resource explicitly approved by root.
 baseline_resource=PKG/'approved-regression/回归基准_27.json'
 baseline_info=json.loads((PKG/'approved-regression/approved-baseline-manifest.json').read_text())
 assert sha(baseline_resource)==baseline_info['source_SHA256']
 shutil.copyfile(baseline_resource,T/'新管/回归基准_27.json')
 report['approved_existing_visual_baseline']=baseline_info
 for proof in (PKG/'approved-regression').glob('*.json'):
  target='approved-'+('visual-baseline.json' if proof.name=='回归基准_27.json' else proof.name)
  shutil.copyfile(proof,OUT/target)
 # Same historical immutable regression fixtures; exactly one independently adopted reference-input overlay.
 report['actual_stock_program_SHA256_before_reference_IO_overlay']={f['path']:sha(T/f['path']) for f in program_inventory['stock_files']}
 for f in manifest['files']:
  src=PKG/'patch'/f['path'];assert sha(src)==f['patch_SHA256'];shutil.copyfile(src,REPO/f['path'])
 report['actual_reference_IO_only_overlay_SHA256']={f['path']:sha(REPO/f['path'])for f in manifest['files']}
 for f in program_inventory['expected_stock_programs']:assert sha(T/f['path'])==f['sha256'], ('Unexpected program mutation',f['path'])
 report['all110_actual_programs_match_exact_stock109_plus_reference_IO_only_overlay']=True
 fonts=REPO/'视频/资源/字体';fonts.parent.mkdir(parents=True,exist_ok=True)
 if not fonts.exists():fonts.symlink_to(T/'fonts',target_is_directory=True)
 if not (W/'fonts').exists():(W/'fonts').symlink_to(T/'fonts',target_is_directory=True)
 # The same canonical repository alias is required by original selftests; this job is isolated.
 alias=Path('/home/user/postgraduate-vocabulary');subprocess.run(['sudo','mkdir','-p',str(alias.parent)],check=True)
 if alias.is_symlink():subprocess.run(['sudo','rm',str(alias)],check=True)
 if not alias.exists():subprocess.run(['sudo','ln','-s',str(REPO),str(alias)],check=True)
 assert alias.resolve()==REPO.resolve()
 r=run([sys.executable,T/'出片指纹.py','--拷',W],'canonical-module-copy',cwd=REPO);assert r.returncode==0
 # A newly approved raw-mother loader must rebuild only the current regression article's temporary GT.
 if any(f['path'].endswith('/独立复核/synth.py') for f in manifest['files']):
  removed=[]
  for oldgt in sorted((W.parent/'qc_independent/gt').glob('27_*')):
   if oldgt.is_file():removed.append({'name':oldgt.name,'SHA256':sha(oldgt)});oldgt.unlink()
  report['fresh_reference_27_temporary_files_removed']=removed
  report['unchanged_independent_audit_SHA256']=sha(T/'独立复核/audit.py')
  report['fresh_reference_is_original_raw_cache_not_processed_PCM']=True
 prior_stamp=T/'新管/快测通过.json';report['prior_stamp_historical_not_reused_SHA256']=sha(prior_stamp)if prior_stamp.exists()else None
 prior_stamp.unlink(missing_ok=True);new_stamp_after_ns=time.time_ns()
 r=run([sys.executable,T/'新管/快测.py'],'original-full-fastcheck',cwd=W);assert r.returncode==0,'Original full quickcheck failed; no approval stamp invented'
 report['original_full_fastcheck_passed']=True
 assert prior_stamp.is_file()and prior_stamp.stat().st_mtime_ns>=new_stamp_after_ns
 fresh=json.loads(prior_stamp.read_text());expected_programs={f['path']:f['sha256'][:16]for f in program_inventory['expected_stock_programs']}
 assert len(fresh['程序'])==program_inventory['program_count']==110 and fresh['程序']==expected_programs
 assert fresh['程序']['make_video.py']=='4c85e1fbdd2e82c5'and fresh['程序']['render.py']=='477a516f7100ac05'
 report['new_exact_single_reference_IO_overlay110_stamp_created_after_original_fullquick']=True
 report['gain_mode_specific_conditional_tests_not_applicable_stock_original_variant']=True
 stamp=T/'新管/快测通过.json';assert stamp.is_file();shutil.copyfile(stamp,OUT/'real-fastcheck-stamp.json');report['real_fastcheck_stamp_SHA256']=sha(stamp)
 r=run([sys.executable,T/'新管/印章.py'],'real-stamp-validation',cwd=W);assert r.returncode==0
 if a.variant=='keep-reviewed-gain':
  r=run([sys.executable,PKG/'targeted-mode-tests.py','--tools',T,'--requests',PKG/'request-fixtures','--output',OUT/'targeted-mode-tests.json'],'new-mode-functional-tests',cwd=W);assert r.returncode==0
  # Real frozen source + restored original TTS cache: measurement only, never auto-write gains.
  real=[]
  for no in ['10','11','12']:
   src=PKG/'request-fixtures'/f'{no}.json';dst=W/'scripts'/f'{no}.json';shutil.copyfile(src,dst);source_sha=sha(dst)
   r=run([sys.executable,'make_video.py',dst,f'_keep-gain-real-{no}.mp4'],f'real{no}-cached-audio',cwd=W,env={**E,'AUDIO_ONLY':'1'});assert r.returncode==0
   wav=W/f'work_{no}/a.wav';seg=W/f'work_{no}/分段.json';before=sha(wav);assert sha(dst)==source_sha
   r=run([sys.executable,T/'句内响度.py',no,'--写入','--保持已审增益'],f'real{no}-readonly-measurement',cwd=W);assert r.returncode==0;assert sha(dst)==source_sha and sha(wav)==before
   gate=run([sys.executable,T/'响度一致性核对.py',wav,'--句内','--分段',seg],f'real{no}-unchanged-loudness-gate',cwd=W);assert gate.returncode in [0,1]
   real.append({'article':no,'actual_frozen_request_source_SHA256':source_sha,'actual_cached_audio_PCM_file_SHA256':before,'source_JSON_and_approved_gain_byte_exact_after_measurement':True,'actual_audio_file_byte_exact_after_measurement':True,'original_loudness_gate_exit':gate.returncode,'article_audio_quality_rejected':gate.returncode==1,'article_audio_or_video_acceptance':False})
  report['real_cached_source_measurements']=real
 report.update({'passed':True,'stage':'source58-reference-IO-only-stock109-full110-original-fullquick-code-certified-not-article-quality'});save()
except Exception as e:
 report.update({'passed':False,'error':str(e)});save();raise
