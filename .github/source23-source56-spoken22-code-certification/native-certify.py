"""Independent core certification; never creates or accepts a production deliverable."""
from pathlib import Path
import argparse,os,sys,json,hashlib,shutil,subprocess,time,copy
p=argparse.ArgumentParser();p.add_argument('--variant',choices=['original','case-consistent-producer'],required=True);p.add_argument('--source68-code-adoption',type=Path,required=True);p.add_argument('--source68-code-adoption-sha256',required=True);p.add_argument('--source35-code-adoption',type=Path,required=True);p.add_argument('--source35-code-adoption-sha256',required=True);p.add_argument('--source23-code-adoption',type=Path,required=True);p.add_argument('--source23-code-adoption-sha256',required=True);p.add_argument('--source56-code-adoption',type=Path,required=True);p.add_argument('--source56-code-adoption-sha256',required=True);a=p.parse_args()
ROOT=Path.cwd();PKG=ROOT/'.github/source23-source56-spoken22-code-certification';REPO=ROOT/'official-main';T=REPO/'视频/工具';W=Path(os.environ['RUNNER_TEMP'])/'completion-machine/video';OUT=ROOT/'certification-public';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();report={'variant':a.variant,'passed':False,'production_audio_or_video_acceptance':False,'official_main_commit':'fc0b56af9a0ac0e97015548b756d4e51d66dc2ea','stage':'start'}
def save(): (OUT/'certification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def run(args,label,cwd=REPO,env=None):
 report['stage']=label;save();t=time.time();r=subprocess.run(list(map(str,args)),cwd=cwd,env=env or E,capture_output=True,text=True);(OUT/(label+'.log')).write_text(r.stdout+'\n'+r.stderr);report.setdefault('checks',[]).append({'name':label,'exit':r.returncode,'seconds':round(time.time()-t,2),'log_SHA256':sha(OUT/(label+'.log'))});save();return r
E={**os.environ,'XG_P':str(REPO),'XG_TOOLS':str(T),'XG_WORK':str(W),'XG_NOPUSH':'1','STRICT_CACHE':'1','XG_KEEP_REVIEWED_GAIN':'1' if a.variant=='case-consistent-producer' else '0','XG_KEEP_REVIEWED_ENDING':'1' if a.variant=='case-consistent-producer' else '0','XG_KEEP_REVIEWED_CUTS':'1' if a.variant=='case-consistent-producer' else '0'}
try:
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==report['official_main_commit']
 manifest=json.loads((PKG/'overlay-manifest.json').read_text());report['overlay_manifest']=manifest
 assert a.variant=='case-consistent-producer', 'This caller certifies exact source23/S13 and source56/S11 extensions after all prior20 checks'
 assert len(a.source68_code_adoption_sha256)==64 and sha(a.source68_code_adoption)==a.source68_code_adoption_sha256, 'Separately adopted exact source68 code extension is required'
 report['source68_code_adoption_SHA256']=a.source68_code_adoption_sha256
 assert len(a.source35_code_adoption_sha256)==64 and sha(a.source35_code_adoption)==a.source35_code_adoption_sha256, 'Separately adopted exact source35 code extension is required'
 report['source35_code_adoption_SHA256']=a.source35_code_adoption_sha256
 assert len(a.source23_code_adoption_sha256)==64 and sha(a.source23_code_adoption)==a.source23_code_adoption_sha256, 'Separately reviewed actual ROOT exact source23 code adoption is required'
 report['source23_code_adoption_SHA256']=a.source23_code_adoption_sha256
 assert len(a.source56_code_adoption_sha256)==64 and sha(a.source56_code_adoption)==a.source56_code_adoption_sha256, 'Separately reviewed actual ROOT exact source56 code adoption is required'
 report['source56_code_adoption_SHA256']=a.source56_code_adoption_sha256
 assert sha(PKG/'request56-actual-accepted-display.json')=='c1af03c1aaf2d6630fa0e8bf6876f55c6d9ff47ba83b13dccd30a4d73b492d7c'
 assert sha(PKG/'ACTUAL-USER-BOOK65-SOURCE56-S11-SPOKEN-FIRST-COMMA-RAW-AUTHORITY.json')=='6d06196750fc7506988d75e5dda7a48e99101421636eff7668671678c6ec9c80'
 assert sha(PKG/'62-S13-CURRENT-CONVERSATION-RAW-USER-READING-AUTHORITY-20261115.json')=='f8f3f7d7b8ecf33b15cade1bcf9923d2e5ae80d2a38f117ae0cf9252a210ed5f'
 assert sha(PKG/'65-CURRENT-CONVERSATION-TWO-FEEDBACK-AND-FINAL-AUTHORITY-20261115.json')=='d1492d3967cb1852859b9eb2016a3aaa66963a99c0b88fcb128b0b8572b58778'
 current65=json.loads((PKG/'65-CURRENT-CONVERSATION-TWO-FEEDBACK-AND-FINAL-AUTHORITY-20261115.json').read_text())
 assert current65['book_order']==65 and current65['actual_user_messages_separate'][-1]=='65篇 定稿 4K'
 report['source56_and_current_authority_scope']={'actual_source56_S11_accepted_display_SHA256':'c1af03c1aaf2d6630fa0e8bf6876f55c6d9ff47ba83b13dccd30a4d73b492d7c','current62_authority_SHA256':'f8f3f7d7b8ecf33b15cade1bcf9923d2e5ae80d2a38f117ae0cf9252a210ed5f','current65_three_separate_actual_messages_SHA256':'d1492d3967cb1852859b9eb2016a3aaa66963a99c0b88fcb128b0b8572b58778','only_first_compromise_comma_deleted_without_and_Wallace_comma_retained':True,'direct_conversation_transcription_NOT_native_message_ID_or_independent_transport_bytes':True,'new_target_mother_or_article_quality_acceptance':False}
 assert sha(PKG/'SOURCE23-BOOK62-EXACT23-S13-CONTRACT-V8-SOURCE-AND-PRIVATE-SHADOW-ROOT-REVIEW-HANDOFF.json')=='de8fbeb728a7963a4dc541c95ef681a5340d22b8613f050eda8d1eb031ee51ab'
 assert sha(PKG/'request23-original-display-v8.json')=='fdb946be34bb940a99c0931895e295c171a7312ea06a2c06266b6f7f3a7b222b'
 assert sha(PKG/'FOUR-ACTUAL-FEEDBACK-READABLE-RECORDS.json')=='d1bd9cb4044be19f90d6828b9f344337490be4d5476cca7c990507f3faae6d65'
 actual_forwarded=json.loads((PKG/'FOUR-ACTUAL-FEEDBACK-READABLE-RECORDS.json').read_text())
 assert actual_forwarded[2]['actual_user_requirement_as_forwarded_by_root']=='and 后屏幕仍显示逗号，配音连读 and to avert imprisonment；只移除 and 后那一个合成用逗号，保 imprisonment 后逗号。'
 assert sha(PKG/'ACTUAL-USER-BOOK62-4K-NORMAL18-FINAL-AUTHORITY.json')=='b5741a1f9e9c7b32e414826e52dec07907df5893cb08f730189d1ded6a0af604'
 assert sha(PKG/'EXACT-FIVE-OLD-S13-MOTHER-LEAVES-PRIVATE-RETIREMENT-HISTORY.json')=='f531e0b257ebfe49cd0095edeb048432d483fc71316c3da3007ac48067633bf1'
 assert sha(PKG/'request23-private-shadow-v8.json')=='4866d7df34f4ffe72c69451874a8b39347181b481e3576ebbe602106e657935f'
 prior20=json.loads((PKG/'historical20-certification.json').read_text())
 assert sha(PKG/'historical20-certification.json')=='50a3abb8d8388ba4587eed0baab4eed5b57afad9fc73cbdb1aa4b48bbaa56c01' and prior20['passed'] is True
 assert sha(PKG/'historical20-real-fastcheck-stamp.json')=='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41'
 report['source23_code_only_source_and_authority_provenance']={'source_V8_SHA256':'fdb946be34bb940a99c0931895e295c171a7312ea06a2c06266b6f7f3a7b222b','V8_H_SHA256':'de8fbeb728a7963a4dc541c95ef681a5340d22b8613f050eda8d1eb031ee51ab','actual_ROOT_forwarded_requirement_file_SHA256':'d1bd9cb4044be19f90d6828b9f344337490be4d5476cca7c990507f3faae6d65','actual_forwarded_requirement_object_index':2,'actual_final_authority_SHA256':'b5741a1f9e9c7b32e414826e52dec07907df5893cb08f730189d1ded6a0af604','not_claimed_native_message_transport_bytes_or_new_target_execution_authorization':True,'no_target_mothers_created':True,'S19_whole0p8_not_modified':True}
 assert sha(PKG/'USER-BOOK53-FINALIZATION-AFTER-EXACTLY-LAYOUT-ILLUSTRATION-20261115.json')=='c61ac0483b54f6c6c2092d27e3e697ebea63ee23b95e85e33f2ff1a509f027d0'
 assert sha(PKG/'USER-BOOK54-FINALIZATION-AFTER-BEARINGS-20261115.json')=='18a7d06adaf59aa0d4bb671c31f30c0835aaf3f1ce926fd80537e21d51fdcf9d'
 assert sha(PKG/'USER-BOOK54-SOURCE35-EXACT-S15-TARGET-AUDIO-ONLY-AUTHORITY.json')=='47d628d193dee56ff8e8a10fde9c66590467fac6cf85086a15feb72a82572f3f'
 assert sha(PKG/'root-source24-book49-exact-S18-spoken17-code-only-adoption-20261115.json')=='2c0c51c9624f5b3d44d2d9e66b3feb113e471060de2c9a70ae0a8b869da5e5f6'
 assert sha(PKG/'USER-BOOK49-FINALIZATION-AFTER-AND-SPOKEN-COMMA-20261115.json')=='a5615c07b6cef6b46dd1a98b69734015d62e9cf674c9a2fb31748c759fe275b9'
 assert sha(PKG/'request24-original-display.json')=='533d34bb3261935549042a5863a1fa4e65c816bbb218964e017bc9867bc72c16'
 assert sha(PKG/'make_video.py')=='1b87c1d4d1685bdd59325587184cca35f853354a015e6fe89c11f150cd2a6239'
 report['source24_code_only_and_no_new_target_mother_or_quality_acceptance']=True
 report['source23_code_only_and_no_new_target_mother_or_quality_acceptance']=True
 assert len(manifest['files'])==17 and manifest['files'][0]['patch_SHA256']=='1b87c1d4d1685bdd59325587184cca35f853354a015e6fe89c11f150cd2a6239'
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
 r=run([sys.executable,PKG/'pure_source23_spoken21_projection_tests.py','--candidate',T/'make_video.py','--prior20',PKG/'prior20-make_video.py','--fixture23',PKG/'request23-original-display-v8.json','--shadow23',PKG/'request23-private-shadow-v8.json','--fixture43',PKG/'feature-sources/43.json','--fixture52',PKG/'feature-sources/52.json','--fixture24',PKG/'request24-original-display.json'],'source23-exact-seven-pure-projection-regressions',cwd=W);assert r.returncode==0
 r=run([sys.executable,PKG/'pure_source56_spoken22_projection_tests.py','--candidate',T/'make_video.py','--prior21',PKG/'prior21-unadopted-make_video.py','--baseline56',PKG/'request56-actual-accepted-display.json','--fixture23',PKG/'request23-original-display-v8.json','--fixture43',PKG/'feature-sources/43.json','--fixture52',PKG/'feature-sources/52.json','--fixture24',PKG/'request24-original-display.json'],'source56-exact-seven-pure-projection-regressions',cwd=W);assert r.returncode==0
 prior_stamp=T/'新管/快测通过.json';report['historical_stamp_sha256_before_new_quickcheck']=sha(prior_stamp)if prior_stamp.exists()else None
 prior_stamp.unlink(missing_ok=True);new_stamp_after_ns=time.time_ns()
 r=run([sys.executable,T/'新管/快测.py'],'original-full-fastcheck',cwd=W);assert r.returncode==0,'Original full quickcheck failed; no approval stamp invented'
 assert prior_stamp.is_file()and prior_stamp.stat().st_mtime_ns>=new_stamp_after_ns
 fresh_stamp=json.loads(prior_stamp.read_text());assert len(fresh_stamp['程序'])==110 and fresh_stamp['程序']['make_video.py']=='1b87c1d4d1685bdd'
 assert sha(prior_stamp)!='3c251c77fb58b775ae1389a52ce31467686201ba98b842af545f2923357a6c32'
 assert sha(prior_stamp)!='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41', 'Prior20 actual110 stamp cannot certify the new23 case'
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
   gate=run([sys.executable,T/'响度一致性核对.py',wav,'--句内','--分段',seg],f'real{no}-unchanged-loudness-gate',cwd=W);assert gate.returncode in [0,1]
   real.append({'article':no,'actual_frozen_request_source_SHA256':source_sha,'actual_cached_audio_PCM_file_SHA256':before,'source_JSON_and_approved_gain_byte_exact_after_measurement':True,'actual_audio_file_byte_exact_after_measurement':True,'original_loudness_gate_exit':gate.returncode,'article_audio_quality_rejected':gate.returncode==1,'article_audio_or_video_acceptance':False})
  report['real_cached_source_measurements']=real
 # Source24 new mothers and timing are a separate target-only reviewed phase.
 report['target24_new_mother_and_timing_test_run']=False
 report['target68_new_mother_and_timing_test_run']=False
 report['target35_new_mother_and_timing_test_run']=False
 report['target23_new_mother_and_timing_test_run']=False
 report['target56_new_mother_and_timing_test_run']=False
 report['original_three_case_mother_test_not_rerun_prior_actual_result_is_history']=True
 report['native16_cache_preparation_not_repeated_existing_separate_certificate_preserved']=True
 report.update({'passed':True,'stage':'source23-source56-spoken22-extension-code-only-certified-target-mothers-not-created'});save()
except Exception as e:
 report.update({'passed':False,'error':str(e)});save();raise
