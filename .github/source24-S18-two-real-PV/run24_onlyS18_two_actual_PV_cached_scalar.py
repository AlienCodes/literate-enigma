"""Actual ROOT97c-only cached S18 scalar caller. No model/GT/whole or dispatch by author."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT_SHA='c89c5f0149cbc8f1f904bbe25a2ef83c53ec0a5b7231194e3213b71fad0a7dd5'
HELPER_SHA='7505bd1282020c260ba2fec4d14599b82e9acaa997b6911a2368d39b6b736d89'
PROFILE_SHA='19e4242fddc847c9f92e5f32e97061b363aad2987957fde1801b562e876830d4'
SOURCE_SHA='34afbcb1e517c10db4ebb963bbf59615b1c5cf439fee5156e85b14717f7edb13'
NAMESPACE_SHA='7013809ab08a9706ecc6e9a5e573637b51fb5aef23dc412d49ea296f9ed66752'
KEY='Linux-native24-exact-S18-first-spoken-comma-43702270266'
VERSION='4b2cb80918783a01e1492bc465a077d0af810af0637e4fdbff5650db20d481f1'
PARENT_KIND='ROOT-DELEGATED-independent-source24-onlyS18-two-real-PV-cached-scalar-execution-adoption'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,msg):
 if not x:raise AssertionError(msg)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def cache_api_row(path):
 d=json.loads(Path(path).read_text());require(d['total_count']==len(d['actions_caches'])==1,'One actual original mother-cache API row required');r=d['actions_caches'][0]
 require(r['key']==KEY and r['version']==VERSION and r['ref']=='refs/heads/codex/finish-05-and-summaries-20261112','Wrong original mother-cache key/version/ref; no substitution');return r
def validate_root(path,literal,N):
 path=Path(path);N=Path(N);require(literal==ROOT_SHA and path.is_file() and not path.is_symlink() and sha(path)==ROOT_SHA and path.read_bytes()==(N/'actual-ROOT-onlyS18-PV-execution-adoption.json').read_bytes(),'Mandatory actual ROOT97c bytes/SHA before setup or first HTTP')
 value=json.loads(path.read_text());probe=load('_PV24_only_validate_frozen_scope',N/'probe24_only_S18_two_actual_PV_original_cached_true_timed.py');probe.validate_adoption(value,HELPER_SHA,PROFILE_SHA);return value
def validate_parent(path,literal,N):
 p=Path(path);N=Path(N);require(re.fullmatch('[0-9a-f]{64}',literal or '') and p.is_file() and not p.is_symlink() and sha(p)==literal,'Actual independent parent record fullSHA required')
 require(p.read_bytes()==(N/'actual-parent-onlyS18-PV-review.json').read_bytes() and (N/'actual-parent-onlyS18-PV-review.sha256').read_text().strip()==literal,'Parent record copy/literal differs')
 v=json.loads(p.read_text());require(v['kind']==PARENT_KIND and v['root_scope']['sha256']==ROOT_SHA and v['program_SHA256']==HELPER_SHA and v['profile_SHA256']==PROFILE_SHA,'Parent must bind actual ROOT/helper/profile')
 require(v['source_id']=='24' and v['target_sentence']=='S18' and v['book_order']==49 and v['independent_review_passed'] is True and v['only_cached_original_S18_two_PV_and_true_timed_scalars_authorized'] is True and v['new_TTS_math_GT_ASR_whole_audio_or_CF_write_authorized'] is False,'Actual independent finite scope incomplete');return v
def verify_transport(N):
 N=Path(N);rows=json.loads((N/'transport-file-pins.json').read_text());require(rows and len({r['relative']for r in rows})==len(rows),'Unique finite transport pins required')
 for r in rows:
  rel=Path(r['relative']);require(not rel.is_absolute() and '..'not in rel.parts,'Transport path escaped');p=N/rel;require(p.is_file() and not p.is_symlink() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'Frozen input/program differs '+str(rel))
 require(sha(N/'probe24_only_S18_two_actual_PV_original_cached_true_timed.py')==HELPER_SHA and sha(N/'profile.json')==PROFILE_SHA and sha(N/'original701380_namespace_support.py')==NAMESPACE_SHA,'Frozen observer/profile/namespace source mismatch');return rows
def helper_argv(N,M,T,O):
 N,M,T,O=map(Path,(N,M,T,O));return [sys.executable,str(N/'probe24_only_S18_two_actual_PV_original_cached_true_timed.py'),'--tools',str(T),'--video-root',str(M),'--profile',str(N/'profile.json'),'--source',str(N/'inputs/source.json'),'--input-dir',str(N/'inputs'),'--execution-adoption',str(N/'actual-ROOT-onlyS18-PV-execution-adoption.json'),'--execution-adoption-sha256',ROOT_SHA,'--output',str(O/'24-S18-two-actual-PV-true-timed-scalar.json')]
def verify_G27(N,T,W,profile):
 N,T,W=map(Path,(N,T,W));require(sha(T/'出片指纹.py')=='ef589d2ad0bc9e1806a37161c81e727b7f900d4de490d05d4c74755b392b91a9','Original actual G27 changed');g=load('_PV24_caller_original_G27',T/'出片指纹.py');paths=g.清单([str(T)]);require(len(paths)==8 and set(paths)==set(profile['original_G27_expected']) and g.核对工作目录(str(W),str(T))==[],'Original eight work imports differ');rows={}
 for name,p in paths.items():
  q=g._找(name,g.工作目录搜(str(W)));require(q is not None and sha(q)==sha(p)==profile['original_G27_expected'][name],'Original module fullSHA/path differs '+name);rows[name]={'tools_path':str(Path(p).resolve()),'work_path':str(Path(q).resolve()),'sha256':sha(q)}
 return rows
def snapshot(W):
 W=Path(W);return {'exists':os.path.lexists(W),'inode':W.lstat().st_ino if os.path.lexists(W)else None,'current_work24_WAV_SHA256':sha(W/'work_24/a.wav')if(W/'work_24/a.wav').is_file()else None,'scripts':{p.name:sha(p)for p in(W/'scripts').glob('*.json')}}
def main():
 p=argparse.ArgumentParser()
 for k in ['actual-root-execution-adoption','actual-parent-review-adoption']:p.add_argument('--'+k,type=Path,required=True);p.add_argument('--'+k+'-sha256',required=True)
 a=p.parse_args();N=Path(__file__).resolve().parent;validate_root(a.actual_root_execution_adoption,a.actual_root_execution_adoption_sha256,N);validate_parent(a.actual_parent_review_adoption,a.actual_parent_review_adoption_sha256,N);pins=verify_transport(N)
 ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';W=M/'video';T=ROOT/'official-main/视频/工具';O=ROOT/'source24-two-PV-public';require(not O.exists(),'Fresh PV-only public namespace required');O.mkdir()
 report={'kind':'actual-ROOT97c-and-parent-bound-onlyS18-two-PV-cached-scalar-setup','source_id':'24','book_order':49,'target_sentence':'S18','root_SHA256':ROOT_SHA,'actual_parent_review_SHA256':a.actual_parent_review_adoption_sha256,'helper_SHA256':HELPER_SHA,'profile_SHA256':PROFILE_SHA,'quality_acceptance':False,'formal_acceptance':False,'caller_diagnostic_completed':False,'restoration':{},'errors':[],'runtime_transport_pin_count':len(pins)};status=1;before=None
 try:
  require(all(os.environ.get(k)=='1'for k in ['AUDIO_ONLY','STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS'])and not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID']),'Original strict modes; no voice/filter/fingerprint override')
  require(os.environ.get('ACTUAL_S18_MOTHER_CACHE_HIT')=='true','Actual saved raw/timed four-leaf mother cache must hit')
  report['cache_API']=cache_api_row(N/'inputs/actual-mother-cache-API.json');identity=json.loads((N/'inputs/actual-mother-identity.json').read_text());C=M/'tts/cache_tts'
  for name,want in identity['actual_four_private_files'].items():q=C/name;require(q.is_file()and not q.is_symlink()and sha(q)==want,'Missing/wrong actual PKL or marker; no fallback '+name)
  profile=json.loads((N/'profile.json').read_text());runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual Actions run ID required');scratch=M/('_PV24_onlyS18_setup_'+runid);require(not scratch.exists(),'Fresh isolated PV setup required');scratch.mkdir();before=snapshot(W)
  lib=load('_PV24_original701380_namespace_only',N/'original701380_namespace_support.py')
  with lib.work_namespace(W,scratch,report['restoration']):
   W.mkdir();subprocess.run([sys.executable,str(N/'install_actual_certified18_context.py')],check=True);sd=W/'scripts';sd.mkdir();source=sd/'24.json';source.write_bytes((N/'inputs/source.json').read_bytes());require(sha(source)==SOURCE_SHA,'Only same-byte current34af source initialization allowed')
   gp=json.loads((N/'actual-G27-eight-full-identities.json').read_text());report['G27_before_helper']=verify_G27(N,T,W,gp)
   args=helper_argv(N,M,T,O);report['actual_helper_argv']=args;status=subprocess.run(args).returncode;report['helper_exit']=status
   report['G27_after_helper']=verify_G27(N,T,W,gp)
   scalar=json.loads((O/'24-S18-two-actual-PV-true-timed-scalar.json').read_text());report['helper_diagnostic_completed']=scalar['diagnostic_completed'];report['helper_quality_and_formal_acceptance_false']=scalar['quality_acceptance']is False and scalar['formal_acceptance']is False;report['helper_reported_errors']=scalar['errors']
   if not(scalar['diagnostic_completed']is True and scalar['quality_acceptance']is False and scalar['formal_acceptance']is False and scalar['errors']==[]):status=1
 except BaseException as error:report['errors'].append({'type':type(error).__name__,'detail':str(error)});traceback.print_exc();status=1
 finally:
  report['outer_original_video_inode_and_PCM_restored']=report['restoration'].get('normal_work_inode_and_PCM_restored')is True
  report['original_normal_W_snapshot_exact_after']=before is not None and snapshot(W)==before
  report['caller_diagnostic_completed']=report.get('helper_diagnostic_completed')is True and report.get('helper_quality_and_formal_acceptance_false')is True and not report['errors'] and report['outer_original_video_inode_and_PCM_restored']and report['original_normal_W_snapshot_exact_after']
  if not report['caller_diagnostic_completed']:status=1
  (O/'24-onlyS18-two-PV-actual-ROOT97c-binding-and-setup.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return status
if __name__=='__main__':sys.exit(main())
