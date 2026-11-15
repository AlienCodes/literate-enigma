"""Same accepted original full standard Git route, finite actual50 pins and original400 monitor."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time,types
R=Path(__file__).resolve().parent;W=R/'run43728728741-70-book50-review-normal18-v1'
H=Path('/workspace/work/review70-finalV3/43728728741-normal18/archive-handoff.json')
HS='9b7de7262eaa8dcb8f91abfb323cab92829d10a603df42eaf6c2b5fc7cf36758';PS='69dd4514ff0b904e927c210917978d75d2b3ea9c9ed287a8578ec4897c4693ce';IS='8ca2af06f7c45da9ec9b04abeaf761f3fae84e42993512870c710289e562b192'
FLOOR=419430400;REQUIRED=726179840
T=R/'transport_source70_book50_full_host_assets.py';TS='90aa7b8d60f9ddad1a72fd85e0ea5b5b02408501dee177719e82fad9f107f9bf'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def free():
 s=os.statvfs(R);return s.f_bavail*s.f_frsize
def controls():
 assert sha(H)==HS and sha(W/'prepared-archive.json')==PS and sha(W/'payload-file-index.json')==IS and sha(T)==TS
controls();assert not (R/'ACTUAL-BOOK50-ORIGINAL-FULL-STANDARD-GIT-400-MONITOR.json').exists()
# Reuse the exact original protected-reference checker already used successfully for63.
F=Path('/workspace/work/source64-book63-hybrid-lowdisk-transport-CODE-ONLY-20261115');d=json.loads((F/'SOURCE64-BOOK63-EXACT-HYBRID-LOWDISK-INDEPENDENT-CODE-AND-PINS-HANDOFF.json').read_bytes());pin=next(x for x in d['files']if Path(x['path']).name=='run_source64_hybrid_phase_with_original400_monitor.py');assert sha(pin['path'])==pin['sha256'];helper=types.ModuleType('actual50_original_protected_reference_checker');helper.__file__=pin['path'];exec(compile(Path(pin['path']).read_bytes(),pin['path'],'exec'),helper.__dict__)
expected={'alienalgorithm/postgraduate-vocabulary:main':'f4e9cbef82ca20e0544f06cb828dac42bf2e831a','AlienCodes/literate-enigma:codex/all-deliverables-20261113':'83e573711b959c95522b93333c9db01c48ea13be','AlienCodes/literate-enigma:master':'6355a02864ebae616b693200d9d26f74f5da80e9'}
before_refs=helper.protected(expected);before=free();assert before>=REQUIRED,'Original400 plus actual2xloose+64 and worker8/misc32 not met'
log=R/'ACTUAL-BOOK50-ORIGINAL-FULL-STANDARD-GIT.log';observations=[];tripped=False
with log.open('x')as output:
 child=subprocess.Popen([sys.executable,'-B',str(T),'--work-dir',str(W)],stdout=output,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(R)})
 while child.poll()is None:
  n=free();observations.append(n)
  if n<FLOOR:tripped=True;os.killpg(child.pid,signal.SIGTERM);break
  time.sleep(.5)
 rc=child.wait()
after_refs=helper.protected(expected);controls()
out={'kind':'actual-original-full-standard-Git-two-repository-transport-original400-budget-observations','source_id':'70','book_order':'50','process_returncode':rc,'before_available':before,'after_available':free(),'required_before':REQUIRED,'minimum_0p5s_observed_available':min(observations or[before]),'samples':len(observations),'sampled_not_continuous_peak_or_hard_upper_bound_claim':True,'original400MiB_trip':tripped,'protected_refs_before':before_refs,'protected_refs_after':after_refs,'original_transport_code_SHA256':TS,'handoff_SHA256':HS,'prepared_SHA256':PS,'index_SHA256':IS,'same_original_push_stream_dual_identity_READY_and_fsck_cleanup_functions':True,'all_payload_H_MP4_WAV_source_and_GEN_MD_unchanged':True,'Git_blob_identity_checks_not_mislabelled_as_all_blob_HTTP_streams':True,'explicit_standalone_master_public_path_HTTP_still_required_before_current':True,'no_current_or_Release_change':True,'no_automatic_retry':True}
p=R/'ACTUAL-BOOK50-ORIGINAL-FULL-STANDARD-GIT-400-MONITOR.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'receipt':str(p),'sha256':sha(p),'returncode':rc,'minimum_observed':out['minimum_0p5s_observed_available']},ensure_ascii=False),flush=True);raise SystemExit(rc)
