"""One reviewed exact hybrid phase. Default is local plan; no automatic retry.
Seed uses original standard Git, then its own Git is cleared after actual raw/fsck.
Stream uses the unchanged bounded builder plus exact proven-existing-ZIP routing.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,signal,subprocess,sys,time
F=Path(__file__).resolve().parent
W=Path('/workspace/work/video-archive-batches-20261114/book69-source59-full-host-isolated-assets-kgdiql_1/run43723690942-59-book69-review-normal18-v1');R=W.parent
H='/workspace/work/review59-finalV3/43723690942-normal18/archive-handoff.json';HS='bbecdf45996de7fe67f23a0031a5a9c377a7f6ddf7d18b96fb14e26b52160d8c';PS='aa845a2d1dd80807cc41502db719cc519a51ec9d362924176549d1db0feedf4f';IS='de64cdc34021525f81051e115a063a393f78cadc3e0d2a5f7eb82d6fcd912d2f'
FLOOR=419430400;STREAM_REQUIRED=469762048

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def free():
    st=os.statvfs(R);return st.f_bavail*st.f_frsize

def protected(expected):
    keys={'alienalgorithm/postgraduate-vocabulary:main','AlienCodes/literate-enigma:codex/all-deliverables-20261113','AlienCodes/literate-enigma:master'}
    assert isinstance(expected,dict)and set(expected)==keys and expected['AlienCodes/literate-enigma:master']=='6355a02864ebae616b693200d9d26f74f5da80e9'
    assert all(re.fullmatch('[0-9a-f]{40}',v)for v in expected.values())
    out={}
    for key,head in expected.items():
        repo,branch=key.split(':',1);found=subprocess.check_output(['gh','api',f'repos/{repo}/git/ref/heads/{branch}','--jq','.object.sha'],text=True).strip()
        assert found==head,'Protected reference changed; stop before further writes';out[key]=found
    return out

def seed_local_plan():
    output=subprocess.check_output([sys.executable,'-B',str(F/'seed_source59_one_public_zip_dual_git.py'),'--work-dir',str(W),'--handoff',H],text=True)
    plan=json.loads(output);assert plan['handoff_sha256']==HS and plan['prepared_sha256']==PS and plan['index_sha256']==IS
    return plan

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',required=True,choices=['seed','stream']);parser.add_argument('--approval');parser.add_argument('--seed-proof');parser.add_argument('--seed-proof-sha256');parser.add_argument('--attempt-id');parser.add_argument('--execute',action='store_true');a=parser.parse_args()
    seed=seed_local_plan();required=seed['required_available_before_seed']if a.phase=='seed'else STREAM_REQUIRED
    if not a.execute:
        print(json.dumps({'kind':'exact-source59-book69-hybrid-phase-local-only-plan','phase':a.phase,'seed_plan':seed,'required_available_before_selected_phase':required,'original400MiB_reserve':FLOOR,'stream_builder_controlled_metadata_budget':8*1024*1024,'worker8MiB_misc32MiB_are_additional':True,'network_executed':False,'requires_separate_explicit_exact_code_and_input_adoption':True}));return
    assert a.approval and a.attempt_id and re.fullmatch('[A-Za-z0-9][A-Za-z0-9-]{0,63}',a.attempt_id)
    approval=json.loads(Path(a.approval).read_bytes());assert approval['approved']is True and approval['approved_monitor_sha256']==sha(__file__)
    assert approval['source_id']=='59'and approval['new_id']=='69'
    assert approval['handoff_sha256']==HS and approval['prepared_sha256']==PS and approval['index_sha256']==IS
    if a.phase=='seed':
        assert approval['kind']=='root-approved-source59-book69-exact-public-ZIP-two-repository-Git-seed'
        assert approval['approved_seed_code_sha256']==sha(F/'seed_source59_one_public_zip_dual_git.py')
        cmd=[sys.executable,'-B',F/'seed_source59_one_public_zip_dual_git.py','--work-dir',W,'--handoff',H,'--approval',a.approval,'--execute']
    else:
        assert approval['kind']=='root-reviewed-exact-source59-streaming-asset-transport'and a.seed_proof and a.seed_proof_sha256
        assert approval['approved_module_sha256']==sha(F/'streaming_git_data_asset_transport_proxy_v2.py')and approval['exact_dual_seed_skip_wrapper_sha256']==sha(F/'stream_source59_with_exact_dual_seed_skip.py')and approval['approved_seed_proof_sha256']==a.seed_proof_sha256
        wrapper_receipt=R/('actual-book69-exact-dual-seed-wrapper-'+a.attempt_id+'.json')
        assert not wrapper_receipt.exists()
        cmd=[sys.executable,'-B',F/'stream_source59_with_exact_dual_seed_skip.py','--module',F/'streaming_git_data_asset_transport_proxy_v2.py','--seed-proof',a.seed_proof,'--seed-proof-sha256',a.seed_proof_sha256,'--receipt',wrapper_receipt,'--execute','--','--work-dir',W,'--handoff',H,'--handoff-sha256',HS,'--prepared-sha256',PS,'--index-sha256',IS,'--approval',a.approval,'--execute']
    before_refs=protected(approval['expected_protected_refs']);before=free();assert before>=required,'Original400MiB plus measured seed or bounded stream budget not met'
    out=R/('ACTUAL-BOOK69-HYBRID-'+a.phase+'-'+a.attempt_id+'-400-MONITOR.json');log=out.with_suffix('.log');assert not out.exists()and not log.exists()
    observations=[];tripped=False
    with log.open('x')as stream:
        child=subprocess.Popen(list(map(str,cmd)),stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(R),'EXACT59_BOOK69_SEED_ORIGINAL400_MONITORED':'1'})
        while child.poll()is None:
            n=free();observations.append(n)
            if n<FLOOR:
                tripped=True;os.killpg(child.pid,signal.SIGTERM);break
            time.sleep(.5)
        rc=child.wait()
    # This phase never modifies canonical refs. Detect external/racing changes too.
    after_refs=protected(approval['expected_protected_refs'])
    proof={'kind':'actual-exact-source59-book69-hybrid-phase-budget-observations','phase':a.phase,'process_returncode':rc,'before_available':before,'after_available':free(),'required_before':required,'minimum_0p5s_observed_available':min(observations or[before]),'samples':len(observations),'sampled_not_continuous_peak_or_hard_upper_bound_claim':True,'original400MiB_trip':tripped,'protected_refs_before':before_refs,'protected_refs_after':after_refs,'approval_SHA256':sha(a.approval),'no_automatic_retry':True,'requires_original_dual_blob_and_two_whole_MP4_HTTP_READY_and_CAS_current_after_stream':True,'whole_transport_includes_one_standard_Git_seed_not_claimed_Git_free':True}
    with out.open('x')as stream:json.dump(proof,stream,indent=2);stream.write('\n')
    print(json.dumps({'phase':a.phase,'returncode':rc,'receipt':str(out),'receipt_sha256':sha(out),'minimum_observed':proof['minimum_0p5s_observed_available']}));raise SystemExit(rc)
if __name__=='__main__':main()
