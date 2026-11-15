"""Original cached-machine isolated W, only new CMU2 S11 readonly scalar; no whole/native."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys,traceback
sys.dont_write_bytecode=True
HELPER_SHA='4e412d8852805ba732246841ba0b21819fa864f5b400efe34ffd81ba85e98aea'
PROFILE_SHA='6a26cf82c83342bc43e1abee1b5ae09159a94210e24377f39c5dd31c88afdc41'
SOURCE_SHA='98f19d88462902693e5cdb579c2d539150d22cff9be5b42a7f57ebc1d42ecb7b'
MOTHER_KEY='Linux-native56-exact-S11-CMU2-Wallace-pronCTX-43759374449'
MOTHER_VERSION='b7a003ff3df1f4b269f8c12708946abaaa05cb7df7047df9ea58b673f802f325'
MATH_KEY='Linux-native56-only-S11-CMU2-whole-original-math-43765008177'
MATH_VERSION='9379d7272d5811602cc5c1c7e1393a7c44306e0d70d6fbe78050864cb190b053'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,msg):
 if not v:raise AssertionError(msg)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def verify_transport(N):
 rows=json.loads((Path(N)/'transport-file-pins.json').read_text())
 for r in rows:
  rel=Path(r['relative']);require(not rel.is_absolute()and'..'not in rel.parts,'Transport path escaped');p=Path(N)/rel;require(p.is_file()and not p.is_symlink()and p.stat().st_size==r['bytes']and sha(p)==r['sha256'],'Frozen input/program differs '+str(rel))
 require(sha(Path(N)/'probe/observe56_CMU2_only_S11_wordprotected_bounded_scalars.py')==HELPER_SHA and sha(Path(N)/'probe/profile.json')==PROFILE_SHA,'Wrong new helper/profile');return rows
def validate_parent(path,literal,N,require_copy=True):
 N=Path(N);h=load('_CMU2_readonly_adoption_validation',N/'probe/observe56_CMU2_only_S11_wordprotected_bounded_scalars.py');profile=json.loads((N/'probe/profile.json').read_text());inp=h.bind_inputs(N/'probe',profile);v=h.validate_execution_adoption(path,literal,profile,inp)
 if require_copy:require(Path(path).read_bytes()==(N/'actual-parent-CMU2-bounded-review.json').read_bytes() and (N/'actual-parent-CMU2-bounded-review.sha256').read_text().strip()==literal,'Actual parent record/literal transport copy differs')
 return v
def cache_api_row(path,key,version):
 d=json.loads(Path(path).read_text());require(d['total_count']==len(d['actions_caches'])==1,'Unique actual API row');r=d['actions_caches'][0];require(r['key']==key and r['version']==version and r['ref']=='refs/heads/codex/finish-05-and-summaries-20261112','Actual key/version/ref differs');return r
def helper_argv(N,M,T,O,parent,literal):
 return [sys.executable,str(Path(N)/'probe/observe56_CMU2_only_S11_wordprotected_bounded_scalars.py'),'--tools',str(T),'--video-root',str(M),'--inputs',str(Path(N)/'probe'),'--profile',str(Path(N)/'probe/profile.json'),'--output',str(Path(O)/'56-CMU2-S11-original-wordprotected-bounded-scalars.json'),'--execution-adoption',str(parent),'--execution-adoption-sha256',literal]
def main():
 p=argparse.ArgumentParser();p.add_argument('--actual-parent-review-adoption',type=Path,required=True);p.add_argument('--actual-parent-review-adoption-sha256',required=True);a=p.parse_args();N=Path(__file__).resolve().parent;verify_transport(N);validate_parent(a.actual_parent_review_adoption,a.actual_parent_review_adoption_sha256,N)
 ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';W=M/'video';T=ROOT/'official-main/视频/工具';C=M/'tts/cache_tts';O=ROOT/'source56-CMU2-bounded-readonly-public';require(not O.exists(),'Fresh scalar directory required')
 require(all(os.environ.get(k)=='1'for k in ['AUDIO_ONLY','STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS'])and not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC','CACHE_LOG']),'Only exact original strict modes')
 require(os.environ.get('CMU2_S11_MOTHER_CACHE_HIT')==os.environ.get('CMU2_S11_G36_CACHE_HIT')=='true','Exact existing new mother/math must hit')
 api={'mothers':cache_api_row(N/'probe/inputs/mother_cache_API.json',MOTHER_KEY,MOTHER_VERSION),'math':cache_api_row(N/'probe/inputs/math_cache_API.json',MATH_KEY,MATH_VERSION)}
 identity=json.loads((N/'probe/inputs/identity.json').read_text());require(all((C/n).is_file()and not(C/n).is_symlink()and sha(C/n)==v for n,v in identity['actual_four_private_files'].items()),'Exact a387/42d actual four cached leaves required')
 runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual run identity needed for setup isolation');scratch=M/('_CMU2_S11_bounded_setup_'+runid);require(not scratch.exists(),'Old setup cannot be reused');scratch.mkdir();O.mkdir();report={'kind':'actual-parent-reviewed-new-CMU2-onlyS11-bounded-original-cache-readonly-setup','actual_parent_record_SHA256':a.actual_parent_review_adoption_sha256,'helper_SHA256':HELPER_SHA,'profile_SHA256':PROFILE_SHA,'cache_API':api,'no_new_math_TTS_whole_cut_CF_checker_or_quality_authorized':True,'restoration':{},'errors':[]};status=1
 try:
  observer=load('_CMU2_existing_work_namespace',N/'probe/inputs/observer.py')
  with observer.work_namespace(W,scratch,report['restoration']):
   W.mkdir();subprocess.run([sys.executable,str(N/'install_actual_certified22_context.py')],check=True);(W/'scripts').mkdir();source=W/'scripts/56.json';source.write_bytes((N/'probe/inputs/source.json').read_bytes());require(sha(source)==SOURCE_SHA,'Exact same-byte current98f initialization required')
   context=load('_CMU2_actual_shared_context',N/'apply_exact_measured_S11_CMU2_context_data.py');report['actual_shared_context']=context.apply(T,W,N/'CMU2-context/按语境读音.json',N/'CMU2-context/actual-shared-CMU2-context-data-binding.json',O/'56-actual-shared-CMU2-readonly-context.json')
   restore=load('_CMU2_actual_existing_f853',N/'restore_exact_existing_S11_CMU2_G36_JSON.py');report['actual_f853_readback']=restore.restore_existing_original_math(M/'tts/source56-only-S11-CMU2-whole-original-math-cache'/restore.NAME,C/restore.NAME,os.environ['CMU2_S11_G36_CACHE_HIT'])
   status=subprocess.run(helper_argv(N,M,T,O,a.actual_parent_review_adoption,a.actual_parent_review_adoption_sha256)).returncode;scalar=json.loads((O/'56-CMU2-S11-original-wordprotected-bounded-scalars.json').read_text());report['helper_diagnostic_completed']=scalar['diagnostic_completed'];report['helper_exit']=status;require(status==0 and scalar['diagnostic_completed']is True and scalar['errors']==[],'Original readonly measurement did not complete; never relax')
 except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc();status=1
 finally:
  report['original_cached_W_inode_and_PCM_restored']=report['restoration'].get('normal_work_inode_and_PCM_restored')is True;report['caller_completed']=status==0 and not report['errors']and report['original_cached_W_inode_and_PCM_restored']
  if not report['caller_completed']:status=1
  (O/'56-CMU2-S11-actual-readonly-parent-binding-and-all-restores.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return status
if __name__=='__main__':sys.exit(main())
