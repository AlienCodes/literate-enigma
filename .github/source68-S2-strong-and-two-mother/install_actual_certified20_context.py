from pathlib import Path
import os,json,hashlib,shutil,subprocess,sys
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);REPO=ROOT/'official-main';T=REPO/'视频/工具';M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';W=M/'video';O=ROOT/'mother68-strong-and-public';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()=='fc0b56af9a0ac0e97015548b756d4e51d66dc2ea'
pins=json.loads((N/'transport-file-pins.json').read_text());assert all(sha(N/r['relative'])==r['sha256'] and (N/r['relative']).stat().st_size==r['bytes'] for r in pins)
manifest=json.loads((N/'actual-spoken20-runtime-contract.json').read_text());cert=json.loads((N/'actual20-certification43693920217.json').read_text());assert cert['passed'] is True and cert['overlay_manifest']==manifest and cert['new_actual_110_program_stamp_created_after_full_quickcheck'] is True
records=[]
for r in manifest['files']:
 src=N/'patch'/r['path'];dst=REPO/r['path'];assert sha(src)==r['patch_SHA256'] and sha(dst)==r['main_SHA256'];shutil.copyfile(src,dst);assert sha(dst)==r['patch_SHA256'];records.append({'path':r['path'],'sha256':sha(dst)})
stamp=N/'evidence/real-spoken20-fastcheck-stamp.json';assert sha(stamp)==cert['real_fastcheck_stamp_SHA256']=='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41';d=json.loads(stamp.read_text());assert len(d['程序'])==110 and d['程序']['make_video.py']=='0e6c4ff6dd4ab4e3';shutil.copyfile(stamp,T/'新管/快测通过.json')
fonts=REPO/'视频/资源/字体';fonts.parent.mkdir(parents=True,exist_ok=True)
if not fonts.exists():fonts.symlink_to(T/'fonts',target_is_directory=True)
W.mkdir(exist_ok=True)
if not (W/'fonts').exists():(W/'fonts').symlink_to(T/'fonts',target_is_directory=True)
alias=Path('/home/user/postgraduate-vocabulary');subprocess.run(['sudo','mkdir','-p',str(alias.parent)],check=True)
if not alias.exists():subprocess.run(['sudo','ln','-s',str(REPO),str(alias)],check=True)
assert alias.resolve()==REPO.resolve()
E={**os.environ,'XG_P':str(REPO),'XG_TOOLS':str(T),'XG_WORK':str(W),'XG_NOPUSH':'1','STRICT_CACHE':'1','XG_KEEP_REVIEWED_GAIN':'1','XG_KEEP_REVIEWED_ENDING':'1','XG_KEEP_REVIEWED_CUTS':'1'}
subprocess.run([sys.executable,T/'新管/印章.py'],cwd=W,env=E,check=True)
subprocess.run([sys.executable,T/'出片指纹.py','--拷',W],cwd=REPO,env=E,check=True)
Tenv=T/'环境';Wenv=W/'环境'
if not Wenv.exists():Wenv.symlink_to(Tenv,target_is_directory=True)
assert sha(Tenv/'模型校验码.json')==sha(Wenv/'模型校验码.json')=='dfde6c065a3558b74923ce82865a3b01dae1f839af4456b74de55dc3ff492312'
for name,expected in {'读音改正.json':'5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b','按语境读音.json':'4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'}.items():
 src=T/'发音词典'/name;dst=W/name;assert sha(src)==expected
 if dst.exists():assert sha(dst)==expected
 else:shutil.copyfile(src,dst)
assert sha(T/'make_video.py')==sha(W/'make_video.py')=='0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
(O/'actual-spoken20-install-and-original-context.json').write_text(json.dumps({'kind':'original-exact-certified20-installation-before-target-only-two-mothers','actual_codecert_run':43693920217,'actual_codecert_sha256':sha(N/'actual20-certification43693920217.json'),'actual_110_stamp_sha256':sha(stamp),'actual_root_execution_adoption_sha256':sha(N/'actual-root-two-mother-execution-adoption.json'),'canonical_alias_actual':str(alias.resolve()),'portable_registry_sha256':sha(Wenv/'模型校验码.json'),'dictionary_context_exact':True,'files':records,'no_model_called_by_installer':True,'quality_acceptance':False},ensure_ascii=False,indent=2)+'\n')
