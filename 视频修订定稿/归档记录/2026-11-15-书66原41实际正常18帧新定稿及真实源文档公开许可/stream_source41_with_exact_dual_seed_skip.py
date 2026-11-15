"""CODE-ONLY exact source41/book66 seeded publicZIP skip around the unchanged builder.
Only that exact blob in the two fixed repositories skips POST; mandatory original
whole-raw verify_blob, trees, commit, create-only ref, and three input pins remain.
Default plans locally; actual invocation requires a real dual-seed proof/adoption.
"""
from pathlib import Path
import argparse,hashlib,json,sys,types
from safe_transport_observer import safe_chain,safe_stage
CODE='db2eed59a37b1d8ceb076bb75d91d47bb82cf56a79497ec96e501f636823652f'
SEED_CODE='022a6b57dcdcd863cca63426d06c70545f972b7e5b07528a57ca7d6f23888f1c'
BLOB='910dc6f8ffc103946677473e0ab22ea7e12c07a7';ZIP='a0a8a4c7707e19748379bc347fa18ceea7e9b524269e8b6584733d05e367d714';SIZE=47854907
HS='aef997eb1826fcbf36472cf361392c681420c58cd15c8c39627779918618663f';PS='34a897121eb2a9fcd532204fd810246676b7968e3386210ab44db7869eb7cf4c';IS='7cc31d717733832a85634d62ae5da6763cca78d5b13f1c9edd5e0b4f0ab7ec1c'
WORK_DIR='/workspace/work/video-archive-batches-20261114/book66-source41-full-host-isolated-assets-f16klbmc/run43723634020-41-book66-review-normal18-v1';HANDOFF='/workspace/work/review41-finalV3/43723634020-normal18/archive-handoff.json'
REPOS={'alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma'};SEED_REF='codex/source41-book66-exact-public-nativeZIP-seed-20261115';SEED_TREE='f83cb3367da3525eacbff631b9ff372ed5c55037';SEED_COMMIT='aecaa00cb48ee684b1b19dc8bfcec36a76741a99'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def install_exact_skip(module,record):
    original=module.GitDataClient.post_blob
    def post(self,repo,blob):
        if repo in REPOS and blob.git_sha==BLOB:
            module.require(blob.size==SIZE and blob.sha256==ZIP,'Exact dual-seed ZIP bytes/SHA scope mismatch')
            record({'repository':repo,'git_blob_sha':BLOB,'bytes':SIZE,'sha256':ZIP,'route':'existing-dual-seed-blob-POST-not-executed-or-claimed','following_original_verify_blob_is_still_mandatory':True});return
        return original(self,repo,blob)
    module.GitDataClient.post_blob=post
    return original

def validate_seed_proof(proof):
    assert proof['kind']=='actual-source41-book66-single-public-ZIP-two-repository-seed-fullraw-proof'
    assert proof['source_id']=='41'and proof['book_order']=='66'and proof['native_source_run']==43723634020
    assert proof['handoff_sha256']==HS and proof['prepared_sha256']==PS and proof['index_sha256']==IS
    assert proof['ZIP_bytes']==SIZE and proof['ZIP_SHA256']==ZIP and proof['git_blob_sha']==BLOB
    assert proof['seed_ref']==SEED_REF and proof['seed_tree']==SEED_TREE and proof['seed_commit']==SEED_COMMIT
    assert proof['network_executed']is True and proof['approved_seed_code_sha256']==SEED_CODE
    assert proof['git_fsck_exit_code']==0 and proof['only_own_seed_Git_removed_after_dual_raw_and_fsck']is True and proof['source_and_all_frozen_controls_unchanged']is True
    assert proof['protected_refs_before']==proof['protected_refs_after']
    expected={'alienalgorithm/postgraduate-vocabulary:main','AlienCodes/literate-enigma:codex/all-deliverables-20261113','AlienCodes/literate-enigma:master'}
    assert set(proof['protected_refs_before'])==expected and proof['protected_refs_before']['AlienCodes/literate-enigma:master']=='6355a02864ebae616b693200d9d26f74f5da80e9'
    rows=proof['actual_rows'];assert len(rows)==2 and {x['repository']for x in rows}==REPOS
    for row in rows:
        assert row['http_status']==200 and row['bytes']==SIZE and row['sha256']==ZIP and row['git_blob_sha']==BLOB and row['entire_raw_HTTP_verified']is True
        assert row['seed_ref']==SEED_REF and row['seed_commit']==SEED_COMMIT
    return proof

def load_exact_source_module(file):
    raw=Path(file).read_bytes();assert hashlib.sha256(raw).hexdigest()==CODE
    name='exact_source41_book66_seeded_stream_runtime';assert name not in sys.modules,'Preloaded runtime refused'
    module=types.ModuleType(name);module.__file__=str(file);module.__package__='';sys.modules[name]=module
    try:exec(compile(raw,str(file),'exec'),module.__dict__)
    except BaseException:sys.modules.pop(name,None);raise
    return module

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--module',required=True);parser.add_argument('--seed-proof');parser.add_argument('--seed-proof-sha256');parser.add_argument('--receipt');parser.add_argument('--execute',action='store_true');parser.add_argument('module_args',nargs=argparse.REMAINDER);a=parser.parse_args()
    file=Path(a.module).resolve();assert file==Path(__file__).with_name('streaming_git_data_asset_transport_proxy_v2.py').resolve()and sha(file)==CODE
    args=a.module_args[1:]if a.module_args[:1]==['--']else a.module_args
    def value(k):return args[args.index(k)+1]
    assert str(Path(value('--work-dir')).resolve())==WORK_DIR and str(Path(value('--handoff')).resolve())==HANDOFF
    assert value('--handoff-sha256')==HS and value('--prepared-sha256')==PS and value('--index-sha256')==IS
    m=load_exact_source_module(file)
    if not a.execute:
        b=m.prepare_bundle(WORK_DIR,HANDOFF,HS,PS,IS)
        print(json.dumps({'kind':'source41-book66-dual-seed-skip-wrapper-local-plan','network_executed':False,'files':len(b['files']),'unique_blobs':len(b['blobs']),'asset_commit':b['commit']['sha'],'payload_root_tree':b['hashes'][''],'requires_actual_dual_seed_proof':True,'only_exact_public_ZIP_POST_will_skip_after_real_seed':True,'original_raw_tree_commit_ref_guards_retained':True}));return
    assert a.seed_proof and a.seed_proof_sha256 and a.receipt and '--execute'in args
    approval=json.loads(Path(value('--approval')).read_text())
    assert approval['kind']=='root-reviewed-exact-source41-streaming-asset-transport'and approval['approved']is True and approval['only_new_isolated_ref_or_exact_readonly_resume']is True
    assert approval['handoff_sha256']==HS and approval['prepared_sha256']==PS and approval['index_sha256']==IS
    assert approval['exact_dual_seed_skip_wrapper_sha256']==sha(__file__)and approval['approved_seed_proof_sha256']==a.seed_proof_sha256
    assert approval['approved_module_sha256']==CODE and approval['source_id']=='41'and approval['new_id']=='66'
    assert sha(a.seed_proof)==a.seed_proof_sha256;proof=validate_seed_proof(json.loads(Path(a.seed_proof).read_bytes()))
    out=Path(a.receipt).resolve();assert out.parent==Path(WORK_DIR).parent and out.name.startswith('actual-book66-exact-dual-seed-wrapper-')and not out.exists()
    token=m.subprocess.check_output(['gh','auth','token'],text=True).strip();client=m.GitDataClient(token)
    for repo in sorted(REPOS):assert client.api(repo,'git/ref/heads/'+SEED_REF)['object']['sha']==SEED_COMMIT
    records=[];before_verify=m.GitDataClient.verify_blob;install_exact_skip(m,records.append);assert m.GitDataClient.verify_blob is before_verify
    w=Path(WORK_DIR);before={d.name for d in w.glob('streaming-attempt-*')};sys.argv=[str(file),*args]
    base={'kind':'actual-source41-book66-exact-dual-seed-blob-route-not-READY','module_sha256':CODE,'wrapper_sha256':sha(__file__),'seed_proof_sha256':a.seed_proof_sha256,'whole_transport_role':'standard-Git-one-ZIP-dual-seed-then-bounded-streaming-builder','builder_itself_has_no_local_Git_not_claimed_for_whole_transport':True,'only_two_repositories_exact_one_blob_POST_skipped_not_claimed201':True,'original_whole_raw_tree_commit_ref_and_three_frozen_input_guards_unchanged':True}
    def write(result):
        with out.open('x')as stream:json.dump(result,stream,indent=2);stream.write('\n')
    try:m.main()
    except Exception as error:
        try:
            stage=None
            for d in sorted(w.glob('streaming-attempt-*')):
                if d.name not in before and(d/'stopped-not-READY.json').exists():stage=safe_stage(json.loads((d/'stopped-not-READY.json').read_text()).get('safe_Git_stage'))
            write({**base,'failed':True,'route_records':records,'safe_exception_chain':safe_chain(error,m.GuardError),'safe_stage':stage,'same_original_exception_reraised':True})
        except Exception:pass
        raise
    else:write({**base,'failed':False,'route_records':records,'READY_or_current_created_by_wrapper':False})
if __name__=='__main__':main()
