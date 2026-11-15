"""Independent core certification; never creates or accepts a production deliverable."""
from pathlib import Path
import argparse,os,sys,json,hashlib,shutil,subprocess,time,copy
p=argparse.ArgumentParser();p.add_argument('--variant',choices=['original','case-consistent-producer'],required=True);p.add_argument('--source68-code-adoption',type=Path,required=True);p.add_argument('--source68-code-adoption-sha256',required=True);p.add_argument('--source35-code-adoption',type=Path,required=True);p.add_argument('--source35-code-adoption-sha256',required=True);p.add_argument('--reviewed-none-code-adoption',type=Path,required=True);p.add_argument('--reviewed-none-code-adoption-sha256',required=True);p.add_argument('--A45-writer-code-adoption',type=Path,required=True);p.add_argument('--A45-writer-code-adoption-sha256',required=True);p.add_argument('--GT-precision-code-adoption',type=Path,required=True);p.add_argument('--GT-precision-code-adoption-sha256',required=True);a=p.parse_args()
ROOT=Path.cwd();PKG=ROOT/'.github/source24-exact-GT-fullprecision-full110-codecert';REPO=ROOT/'official-main';T=REPO/'视频/工具';W=Path(os.environ['RUNNER_TEMP'])/'completion-machine/video';OUT=ROOT/'certification-public';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();report={'variant':a.variant,'passed':False,'production_audio_or_video_acceptance':False,'official_main_commit':'fc0b56af9a0ac0e97015548b756d4e51d66dc2ea','stage':'start'}
def save(): (OUT/'certification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def run(args,label,cwd=REPO,env=None):
 report['stage']=label;save();t=time.time();r=subprocess.run(list(map(str,args)),cwd=cwd,env=env or E,capture_output=True,text=True);(OUT/(label+'.log')).write_text(r.stdout+'\n'+r.stderr);report.setdefault('checks',[]).append({'name':label,'exit':r.returncode,'seconds':round(time.time()-t,2),'log_SHA256':sha(OUT/(label+'.log'))});save();return r
E={**os.environ,'XG_P':str(REPO),'XG_TOOLS':str(T),'XG_WORK':str(W),'XG_NOPUSH':'1','STRICT_CACHE':'1','XG_KEEP_REVIEWED_GAIN':'1' if a.variant=='case-consistent-producer' else '0','XG_KEEP_REVIEWED_ENDING':'1' if a.variant=='case-consistent-producer' else '0','XG_KEEP_REVIEWED_CUTS':'1' if a.variant=='case-consistent-producer' else '0'}
try:
 # Separate external dependency: the original tools-tree stamp still has110 entries.
 assert len(a.reviewed_none_code_adoption_sha256)==64 and sha(a.reviewed_none_code_adoption)==a.reviewed_none_code_adoption_sha256,'Actual ROOT reviewed-NONE code adoption is required; review templates cannot execute'
 binding=json.loads((PKG/'reviewed-none-codecert-execution-binding.json').read_text())
 assert a.A45_writer_code_adoption_sha256=='a941554951cbde2fd0f366746ff2659ce073e87551f2c2709addaa6dd4c942d3' and sha(a.A45_writer_code_adoption)==a.A45_writer_code_adoption_sha256,'Actual new ROOT A45 writer logic scope required'
 assert a.GT_precision_code_adoption_sha256=='d9e92e8a7f14f541f04d88a4651c3cf44b7386fd8cccd1dfc445dbe230d8a47c' and sha(a.GT_precision_code_adoption)==a.GT_precision_code_adoption_sha256,'Actual ROOT exact GT precision newlogic scope required'
 gt_binding=binding['GT_precision_extension'];assert gt_binding['execution_authorized_by_actual_ROOT_review']is True and gt_binding['actual_ROOT_adoption_SHA256']==a.GT_precision_code_adoption_sha256
 gtroot=json.loads(a.GT_precision_code_adoption.read_text());assert gtroot['source_id']=='24' and gtroot['book_order']==49 and gtroot['candidate_synth']['sha256']==gt_binding['candidate_synth_SHA256']=='d3ef082e903c0412e65c5ce53e54c3b27f9cea71b253cb39bd24e22ca3f54e4f'
 assert sha(PKG/'patch/视频/工具/独立复核/synth.py')==gt_binding['candidate_synth_SHA256'] and gt_binding['prior_synth_SHA256']=='499f74e365e7a7d38411c63fd89ce3cbadcc9c1c0f2670fc869ab873ec79d92f' and gt_binding['runtime_overlay_file_count']==18 and gt_binding['new_runtime_module_added']is False
 report['actual_ROOT_GT_fullprecision_logic_adoption_SHA256']=a.GT_precision_code_adoption_sha256
 writer_binding=binding['A45_writer_extension'];assert writer_binding['execution_authorized_by_actual_ROOT_review']is True and writer_binding['actual_ROOT_adoption_SHA256']==a.A45_writer_code_adoption_sha256
 assert writer_binding['candidate_utility_SHA256']=='ece967ee62c56839ff848f59d401f47640abfd99c060a068aa7e541abcf0f88c' and writer_binding['original_utility_SHA256']=='d7bc6ec887ce191d651ae8f19786b20bc5d428533062ac4b02985253e396c390' and sha(PKG/'patch/视频/工具/区间作废.py')==writer_binding['candidate_utility_SHA256']
 assert writer_binding['actual_prior110_stamp_SHA256']=='fe94cc7c38d43471f8fb192ffa374fa8e07620bb8492c0b789e8fa1960accd4d' and writer_binding['runtime_overlay_file_count']==18 and writer_binding['other109_actual_program_identities_unchanged']is True
 report['actual_ROOT_A45_writer_logic_adoption_SHA256']=a.A45_writer_code_adoption_sha256
 alias_repair_binding=binding['A23_selftest_alias_repair'];assert alias_repair_binding['execution_authorized_by_actual_ROOT_review']is True,'Actual ROOT A23 selftest-alias code adoption required'
 assert sha(PKG/'actual-A23-alias-code-adoption.json')==alias_repair_binding['actual_ROOT_adoption_SHA256'] and len(alias_repair_binding['actual_ROOT_adoption_SHA256'])==64
 assert sha(PKG/'patch/视频/工具/读音核对.py')==alias_repair_binding['candidate_checker_SHA256']=='b0b4f1a2d3151489aa8174e8bd734bb3f963e89fffb22e3dc170535327a2feb4' and alias_repair_binding['only_reader_selftest_changes_beyond_actual628d']is True
 assert binding['execution_authorized_by_actual_ROOT_review']is True and binding['root_adoption_SHA256']==a.reviewed_none_code_adoption_sha256
 assert binding['helper_SHA256']=='a60611151cef21d4e729e342587be2531c39bbecd832e2384085f8b3ac2880d0' and binding['patched_shell_SHA256']=='b66729435d893dc562beaea53c347503ad8c1a906193de6fe988c0e953516c59'
 assert binding['actual_prior20_stamp_SHA256']=='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41'
 assert binding['actual_measured_whole_intake_SHA256']=='b4c730b97083ca577b5d4299ebdfd098fd74726f30d032798908b5bfec493a93'
 assert binding['original_110_only_shell_entry_changes']is True and binding['external_helper_NOT_an_extra_program_in_original_110']is True
 assert binding['no_target_models_or_production_native_authorized']is True
 helper=PKG/'reviewed_none_ending24.py';assert sha(helper)==binding['helper_SHA256']
 helper_dst=REPO/'.github/video-revision-batch/reviewed_none_ending24.py';helper_dst.parent.mkdir(parents=True,exist_ok=True)
 if helper_dst.exists():assert sha(helper_dst)==sha(helper),'Do not replace any other external dependency'
 else:shutil.copyfile(helper,helper_dst)
 assert sha(helper_dst)==sha(helper)
 # No marker is installed into original regression source24: all110 original cases retain their original constructor route.
 assert not(REPO/'.github/video-revision-batch/request/24/reviewed-none-ending24-case.json').exists()
 report['reviewed_NONE_constructor_external_dependency']={'helper_SHA256':sha(helper_dst),'root_code_adoption_SHA256':a.reviewed_none_code_adoption_sha256,'helper_outside_tools_tree110':True,'original110_claim_does_not_include_external_helper':True,'separate_pure_data_original_AST_and_fake_command_route_tests_required':True,'no_marker_installed_for_original_fullquick':True}
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==report['official_main_commit']
 manifest=json.loads((PKG/'overlay-manifest.json').read_text());report['overlay_manifest']=manifest
 priorfe94=PKG/'fixtures/actual-prior-fe94-A23-reader110-certificate.json';assert sha(priorfe94)==writer_binding['actual_prior17_certificate_SHA256']=='0cc1c5d7962555e450125e3df5b76b04e54a66ab6dc8baf14325e4bf2d098186'
 priorfe94cert=json.loads(priorfe94.read_text());assert priorfe94cert['passed']is True and len(manifest['files'])==manifest['final_integrated_program_count']==18
 prior18_path=PKG/'fixtures/actual-prior-b086-A45-writer18-certificate.json';assert sha(prior18_path)==gt_binding['actual_prior18_certificate_SHA256']=='b0865478f50da33293c2ccaae6d2dcef7886e54fae2ae2a31a33b391a6a8f82e'
 prior18cert=json.loads(prior18_path.read_text());assert prior18cert['passed']is True and prior18cert['original_full_fastcheck_passed']is True
 restored_manifest=copy.deepcopy(manifest);assert restored_manifest.pop('GT_precision_extension')=={k:v for k,v in gt_binding.items()if k!='execution_authorized_by_actual_ROOT_review'}
 rows=[r for r in restored_manifest['files']if r['path']=='视频/工具/独立复核/synth.py'];assert len(rows)==1 and rows[0]['patch_SHA256']==gt_binding['candidate_synth_SHA256'];rows[0]['patch_SHA256']=gt_binding['prior_synth_SHA256']
 assert restored_manifest==prior18cert['overlay_manifest'],'Only the exact existing synth record may change beyond actual successful b08618'
 assert restored_manifest['files'][:-1]==priorfe94cert['overlay_manifest']['files'] and restored_manifest['files'][-1]=={'path': '视频/工具/区间作废.py', 'main_SHA256': 'd7bc6ec887ce191d651ae8f19786b20bc5d428533062ac4b02985253e396c390', 'patch_SHA256': 'ece967ee62c56839ff848f59d401f47640abfd99c060a068aa7e541abcf0f88c', 'scope': 'Retain only actual raw fingerprint of active valid original spoken-comma controls already bound to that exact raw; original clear/parser/A45 all unchanged'},'Exactly original fe94 seventeen records plus one approved utility after exactsynth inverse required'
 assert a.variant=='case-consistent-producer', 'This caller certifies only the exact source24 candidate extension'
 assert len(a.source68_code_adoption_sha256)==64 and sha(a.source68_code_adoption)==a.source68_code_adoption_sha256, 'Separately adopted exact source68 code extension is required'
 report['source68_code_adoption_SHA256']=a.source68_code_adoption_sha256
 assert len(a.source35_code_adoption_sha256)==64 and sha(a.source35_code_adoption)==a.source35_code_adoption_sha256, 'Separately adopted exact source35 code extension is required'
 report['source35_code_adoption_SHA256']=a.source35_code_adoption_sha256
 assert sha(PKG/'USER-BOOK53-FINALIZATION-AFTER-EXACTLY-LAYOUT-ILLUSTRATION-20261115.json')=='c61ac0483b54f6c6c2092d27e3e697ebea63ee23b95e85e33f2ff1a509f027d0'
 assert sha(PKG/'USER-BOOK54-FINALIZATION-AFTER-BEARINGS-20261115.json')=='18a7d06adaf59aa0d4bb671c31f30c0835aaf3f1ce926fd80537e21d51fdcf9d'
 assert sha(PKG/'USER-BOOK54-SOURCE35-EXACT-S15-TARGET-AUDIO-ONLY-AUTHORITY.json')=='47d628d193dee56ff8e8a10fde9c66590467fac6cf85086a15feb72a82572f3f'
 assert sha(PKG/'root-source24-book49-exact-S18-spoken17-code-only-adoption-20261115.json')=='2c0c51c9624f5b3d44d2d9e66b3feb113e471060de2c9a70ae0a8b869da5e5f6'
 assert sha(PKG/'USER-BOOK49-FINALIZATION-AFTER-AND-SPOKEN-COMMA-20261115.json')=='a5615c07b6cef6b46dd1a98b69734015d62e9cf674c9a2fb31748c759fe275b9'
 assert sha(PKG/'request24-original-display.json')=='533d34bb3261935549042a5863a1fa4e65c816bbb218964e017bc9867bc72c16'
 assert sha(PKG/'make_video.py')=='0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
 report['source24_code_only_and_no_new_target_mother_or_quality_acceptance']=True
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
 # Both modes use the same historical, immutable regression fixtures, never production requests.
 if a.variant=='case-consistent-producer':
  for f in manifest['files']:
   src=PKG/'patch'/f['path'];assert sha(src)==f['patch_SHA256'];shutil.copyfile(src,REPO/f['path'])
 report['actual_core_SHA256']={f['path']:sha(REPO/f['path']) for f in manifest['files']}
 assert sha(T/'草稿声音.sh')==binding['patched_shell_SHA256'] and sha(PKG/'草稿声音.sh')==sha(T/'草稿声音.sh')
 assert sha(T/'make_video.py')=='0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
 r=run([sys.executable,PKG/'pure_reviewed_none_ending24_tests.py','--output',OUT/'reviewed-NONE-separate-pure-data-and-routes.json'],'reviewed-NONE-separate-pure-data-and-shell-routes',cwd=W);assert r.returncode==0
 report['reviewed_NONE_separate_guard_and_original_shell_route_tests_passed']=True
 r=run([sys.executable,PKG/'pure-A45-writer-real-data-tests.py','--tools',T,'--output-dir',OUT],'A45-writer-real-current-raw-and-legacy-pure-tests',cwd=W);assert r.returncode==0
 report['A45_writer_separate_actual_current13_legacy_and_original_guard_pure_tests_passed']=True
 r=run([sys.executable,PKG/'pure-GT-fullprecision-real-source-tests.py'],'GT-fullprecision-exact-current-source-117-pure-tests',cwd=W,env={**E,'GT_PRECISION_TEST_OUTPUT_DIR':str(OUT)});assert r.returncode==0
 gtproof=OUT/'ACTUAL-EXACT24-GT-PRECISION-ORIGINAL-AST-LEGACY70-AND-PHYSICAL-BAD-FIXTURE-PROOF.json';assert json.loads(gtproof.read_text())['passed']is True and json.loads(gtproof.read_text())['test_count']==117
 report['GT_fullprecision_exact_source_only_separate117puretests_passed']=True
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
 r=run([sys.executable,PKG/'native-dispatch-tests.py','--tools',T,'--original-maker',PKG/'original-source/视频/工具/make_video.py','--expected',PKG/'16-dispatch-proposal-input-trace-v1.json','--output',OUT/'real-dispatch-mode-tests.json'],'new-dispatch-real-native-tests',cwd=W);assert r.returncode==0
 r=run([sys.executable,PKG/'native-cuts-tests.py','--tools',T,'--requests',PKG/'request-fixtures','--original-shell',PKG/'original-source/视频/工具/草稿声音.sh','--output',OUT/'real-cuts-mode-tests.json'],'new-cuts-mode-real-tests',cwd=W);assert r.returncode==0
 r=run([sys.executable,PKG/'native-pronunciation-tests.py','--tools',T,'--requests',PKG/'request-fixtures','--original-tool',PKG/'original-source/视频/工具/读音核对.py','--output',OUT/'real-pronunciation-selftest-tests.json'],'new-pronunciation-selftest-real-tests',cwd=W);assert r.returncode==0
 r=run([sys.executable,PKG/'native-ending-tests.py','--tools',T,'--requests',PKG/'request-fixtures','--original-tool',PKG/'original-source/视频/工具/结尾句接点.py','--output',OUT/'real-ending-mode-tests.json'],'new-ending-mode-real-tests',cwd=W);assert r.returncode==0
 r=run([sys.executable,PKG/'pure-source24-projection-tests.py'],'source24-exact-seven-pure-projection-regressions',cwd=W);assert r.returncode==0
 r=run([sys.executable,PKG/'pure_source24_source68_projection_tests.py','--candidate',T/'make_video.py','--prior18',PKG/'prior18-make_video.py','--prior17',PKG/'prior17-make_video.py','--fixture43',PKG/'feature-sources/43.json','--fixture52',PKG/'feature-sources/52.json','--fixture24',PKG/'request24-original-display.json'],'source24-source68-twelve-pure-projection-regressions',cwd=W);assert r.returncode==0
 r=run([sys.executable,PKG/'pure_source35_spoken20_projection_tests.py','--candidate',T/'make_video.py','--prior19',PKG/'prior19-make_video.py','--fixture43',PKG/'feature-sources/43.json','--fixture52',PKG/'feature-sources/52.json','--fixture24',PKG/'request24-original-display.json'],'source35-exact-seven-pure-projection-regressions',cwd=W);assert r.returncode==0
 prior_stamp=T/'新管/快测通过.json';report['historical_stamp_sha256_before_new_quickcheck']=sha(prior_stamp)if prior_stamp.exists()else None
 prior_stamp.unlink(missing_ok=True);new_stamp_after_ns=time.time_ns()
 r=run([sys.executable,T/'新管/快测.py'],'original-full-fastcheck',cwd=W);assert r.returncode==0,'Original full quickcheck failed; no approval stamp invented'
 assert prior_stamp.is_file()and prior_stamp.stat().st_mtime_ns>=new_stamp_after_ns
 fresh_stamp=json.loads(prior_stamp.read_text());assert len(fresh_stamp['程序'])==110 and fresh_stamp['程序']['make_video.py']=='0e6c4ff6dd4ab4e3'
 assert sha(prior_stamp)!='3c251c77fb58b775ae1389a52ce31467686201ba98b842af545f2923357a6c32'
 assert sha(prior_stamp)!='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41','Old successful spoken20 stamp cannot certify the new constructor shell'
 priorfe94stamp_path=PKG/'fixtures/actual-prior-fe94-A23-reader110-stamp.json';assert sha(priorfe94stamp_path)==writer_binding['actual_prior110_stamp_SHA256']
 priorfe94stamp=json.loads(priorfe94stamp_path.read_text())
 prior18stamp_path=PKG/'fixtures/actual-prior-b086-A45-writer18-stamp.json';assert sha(prior18stamp_path)==gt_binding['actual_prior110_stamp_SHA256']=='0e99d948667ca959e79e363bf0185ab83d77313f997319d7d767361bd3f145d8'
 prior18stamp=json.loads(prior18stamp_path.read_text());assert len(prior18stamp['程序'])==110
 expected_programs=dict(prior18stamp['程序']);assert expected_programs['独立复核/synth.py']==gt_binding['prior_synth_SHA256'][:16];expected_programs['独立复核/synth.py']=gt_binding['candidate_synth_SHA256'][:16]
 assert fresh_stamp['程序']==expected_programs and fresh_stamp['规则表版本']==prior18stamp['规则表版本'],'All other109 actualb086 original program identities must remain exact; only scopedGTsynth changes'
 assert sha(prior_stamp)!=gt_binding['actual_prior110_stamp_SHA256'],'Actual old0e99 stamp cannot certify newGTprecision'
 report['all_109_other_original_program_hashes_equal_actual_successful_b086_stamp']=True
 report['new_shell_stamp_entry_full_dependency_is_separately_declared']=True
 report['new_actual_110_program_stamp_created_after_full_quickcheck']=True
 report['original_full_fastcheck_passed']=True
 stamp=T/'新管/快测通过.json';assert stamp.is_file();shutil.copyfile(stamp,OUT/'real-fastcheck-stamp.json');report['real_fastcheck_stamp_SHA256']=sha(stamp)
 r=run([sys.executable,T/'新管/印章.py'],'real-stamp-validation',cwd=W);assert r.returncode==0
 if a.variant=='case-consistent-producer':
  r=run([sys.executable,PKG/'targeted-mode-tests.py','--tools',T,'--requests',PKG/'request-fixtures','--output',OUT/'targeted-mode-tests.json'],'new-mode-functional-tests',cwd=W);assert r.returncode==0
  # Real frozen source + restored original TTS cache: measurement only, never auto-write gains.
  real=[]
  for no in ['10','11','12']:
   src=PKG/'request-fixtures'/f'{no}.json';dst=W/'scripts'/f'{no}.json';shutil.copyfile(src,dst);source_sha=sha(dst)
   r=run([sys.executable,'make_video.py',dst,f'_keep-gain-real-{no}.mp4'],f'real{no}-cached-audio',cwd=W,env={**E,'AUDIO_ONLY':'1'});assert r.returncode==0
   wav=W/f'work_{no}/a.wav';seg=W/f'work_{no}/分段.json';before=sha(wav);assert sha(dst)==source_sha
   r=run([sys.executable,T/'句内响度.py',no,'--写入','--保持已审增益'],f'real{no}-readonly-measurement',cwd=W);assert r.returncode==0;assert sha(dst)==source_sha and sha(wav)==before
   gate=run([sys.executable,T/'响度一致性核对.py',wav,'--句内','--分段',seg],f'real{no}-unchanged-loudness-gate',cwd=W);assert gate.returncode==1,'Original10/11/12 bad loudness controls must all remain rejected'
   real.append({'article':no,'actual_frozen_request_source_SHA256':source_sha,'actual_cached_audio_PCM_file_SHA256':before,'source_JSON_and_approved_gain_byte_exact_after_measurement':True,'actual_audio_file_byte_exact_after_measurement':True,'original_loudness_gate_exit':gate.returncode,'article_audio_quality_rejected':gate.returncode==1,'article_audio_or_video_acceptance':False})
  report['real_cached_source_measurements']=real
 # Source24 new mothers and timing are a separate target-only reviewed phase.
 report['target24_new_mother_and_timing_test_run']=False
 report['target68_new_mother_and_timing_test_run']=False
 report['target35_new_mother_and_timing_test_run']=False
 report['original_three_case_mother_test_not_rerun_prior_actual_result_is_history']=True
 report['native16_cache_preparation_not_repeated_existing_separate_certificate_preserved']=True
 report.update({'passed':True,'stage':'source24-exact-GT-fullprecision-same18-original110-alllegacy23-and-separate117tests-certified-no-target-models'});save()
except Exception as e:
 report.update({'passed':False,'error':str(e)});save();raise
