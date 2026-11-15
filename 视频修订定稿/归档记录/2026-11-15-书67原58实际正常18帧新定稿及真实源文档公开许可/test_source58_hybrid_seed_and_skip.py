"""Synthetic/offline transport contract tests; no real POST/push/ref/current changes."""
import ast,contextlib,copy,hashlib,io,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import seed_source58_one_public_zip_dual_git as seed
import stream_source58_with_exact_dual_seed_skip as skip
import streaming_git_data_asset_transport_proxy_v2 as original
import run_source58_hybrid_phase_with_original400_monitor as monitor
from test_streaming_git_data_asset_transport_proxy_v2 import FakeGit
F=Path(__file__).resolve().parent
REFS={'alienalgorithm/postgraduate-vocabulary:main':'1'*40,'AlienCodes/literate-enigma:codex/all-deliverables-20261113':'2'*40,'AlienCodes/literate-enigma:master':seed.MASTER}

def seedproof():
    return {'kind':'actual-source58-book67-single-public-ZIP-two-repository-seed-fullraw-proof','source_id':'58','book_order':'67','native_source_run':43736478355,'handoff_sha256':skip.HS,'prepared_sha256':skip.PS,'index_sha256':skip.IS,'ZIP_bytes':skip.SIZE,'ZIP_SHA256':skip.ZIP,'git_blob_sha':skip.BLOB,'seed_ref':skip.SEED_REF,'seed_tree':skip.SEED_TREE,'seed_commit':skip.SEED_COMMIT,'network_executed':True,'approved_seed_code_sha256':skip.SEED_CODE,'git_fsck_exit_code':0,'only_own_seed_Git_removed_after_dual_raw_and_fsck':True,'source_and_all_frozen_controls_unchanged':True,'protected_refs_before':REFS,'protected_refs_after':REFS,'actual_rows':[{'repository':repo,'http_status':200,'bytes':skip.SIZE,'sha256':skip.ZIP,'git_blob_sha':skip.BLOB,'entire_raw_HTTP_verified':True,'seed_ref':skip.SEED_REF,'seed_commit':skip.SEED_COMMIT}for repo in sorted(skip.REPOS)]}

class Contracts(unittest.TestCase):
    def test_original_Git_helpers_AST_exact_and_real_tiny_fixture(self):
        old=Path('/workspace/work/video-archive-batches-20261114/user128-source48-streaming-host-isolated-assets-th2bb361/operations-user128-source48-current-final/payload/视频修订定稿/归档记录/2026-11-14-用户128书42袁隆平实际新母完整质量及原正常18帧验收定稿/seed_source48_one_public_zip_git.py')
        def fns(path):return {x.name:ast.dump(x,include_attributes=False)for x in ast.parse(path.read_text()).body if isinstance(x,ast.FunctionDef)}
        a,b=fns(old),fns(Path(seed.__file__))
        for name in ['sha','gitsha','pinned','run','identities','local_objects']:self.assertEqual(a[name],b[name])
        with tempfile.TemporaryDirectory(dir=F)as d:
            root=Path(d);source=root/'input.fixture';data=b'\0\xffonly synthetic Git fixture\n'*100;source.write_bytes(data);blob=seed.gitsha('blob',data);tree,commit,stamp=seed.identities(blob,'2026-11-15T01:02:03Z');g=root/'objects.git'
            seed.local_objects(g,source,blob,tree,commit,stamp)
            self.assertEqual(seed.run(['git','--git-dir='+str(g),'rev-parse',commit+'^{tree}']),tree)
            self.assertEqual(seed.run(['git','--git-dir='+str(g),'rev-list','--parents',commit]),commit)
            self.assertEqual(source.read_bytes(),data);self.assertFalse(any(p.suffix in {'.zip','.pack'}for p in root.rglob('*')))
            seed.run(['git','--git-dir='+str(g),'fsck','--full'])
    def fixture(self,fail=None):
        blob=types.SimpleNamespace(path=Path('never-read.fixture'),size=skip.SIZE,sha256=skip.ZIP,git_sha=skip.BLOB)
        files=[{'repo_path':'视频修订定稿/fixture/public.fixture','bytes':skip.SIZE,'sha256':skip.ZIP,'git_blob_sha':skip.BLOB}];trees,hashes=original.make_trees(files)
        bundle={'blobs':{skip.BLOB:blob},'files':files,'trees':trees,'hashes':hashes,'prefix':'视频修订定稿/fixture','meta':{'asset_branch':'codex/passed4k-assets-123-58-hold18-postonly-v1'},'commit':original.commit_spec(hashes[''],'2026-11-15T01:02:03Z')}
        class Client(FakeGit):pass
        module=types.SimpleNamespace(GitDataClient=Client,require=original.require);records=[];before=Client.verify_blob;skip.install_exact_skip(module,records.append);self.assertIs(Client.verify_blob,before)
        return bundle,Client(bundle,fail),records,module,blob
    def test_both_fixed_repositories_skip_only_exact_ZIP_POST_and_original_raw_still_runs(self):
        for repo in skip.REPOS:
            b,c,records,_,_=self.fixture();original.publish_repository(c,repo,b,lambda _:None)
            self.assertNotIn('post_blob',c.calls);self.assertIn('verify_blob',c.calls);self.assertEqual(len(records),1);self.assertIn('POST-not-executed-or-claimed',records[0]['route']);self.assertIn('git/refs',c.posts)
    def test_wrong_raw_after_exact_seed_skip_still_blocks_any_ref(self):
        for repo in skip.REPOS:
            b,c,records,_,_=self.fixture('raw')
            with self.assertRaises(original.GuardError):original.publish_repository(c,repo,b,lambda _:None)
            self.assertNotIn('git/refs',c.posts);self.assertEqual(len(records),1)
    def test_other_blob_including_master_WAV_retains_original_POST(self):
        _,c,records,_,blob=self.fixture()
        for repo in skip.REPOS:
            c.calls=[];other=types.SimpleNamespace(git_sha='0'*40,size=7414124,sha256='8f822a42adab797aeb278971afbcb260944c088a60ca241d416a9c962409daa7');c.post_blob(repo,other);self.assertIn('post_blob',c.calls)
        self.assertFalse(records)
        c.calls=[];c.post_blob('offline-not-supported-repository',blob);self.assertIn('post_blob',c.calls);self.assertFalse(records)
    def test_wrong_exact_target_size_or_SHA_fails_without_POST(self):
        for size,sha in [(skip.SIZE-1,skip.ZIP),(skip.SIZE,'0'*64)]:
            _,c,records,_,_=self.fixture();wrong=types.SimpleNamespace(git_sha=skip.BLOB,size=size,sha256=sha)
            with self.assertRaises(original.GuardError):c.post_blob('AlienCodes/literate-enigma',wrong)
            self.assertNotIn('post_blob',c.calls);self.assertFalse(records)
    def test_real_shape_seedproof_positive_and_exact_negative_bindings(self):
        self.assertEqual(skip.validate_seed_proof(seedproof())['seed_commit'],skip.SEED_COMMIT)
        mutations=[lambda p:p.__setitem__('kind','wrong'),lambda p:p.__setitem__('source_id','40'),lambda p:p.__setitem__('book_order','65'),lambda p:p.__setitem__('handoff_sha256','0'*64),lambda p:p.__setitem__('ZIP_bytes',skip.SIZE-1),lambda p:p.__setitem__('ZIP_SHA256','0'*64),lambda p:p.__setitem__('seed_commit','0'*40),lambda p:p.__setitem__('network_executed',False),lambda p:p.__setitem__('actual_rows',p['actual_rows'][:1]),lambda p:p['actual_rows'][0].__setitem__('http_status',404),lambda p:p['actual_rows'][1].__setitem__('sha256','0'*64),lambda p:p.__setitem__('git_fsck_exit_code',1)]
        for change in mutations:
            p=copy.deepcopy(seedproof());change(p)
            with self.assertRaises(AssertionError):skip.validate_seed_proof(p)
    def test_protected_refs_default_reject_unknown_scope_or_master(self):
        self.assertEqual(seed.expected_refs(REFS),REFS)
        for x in [{**REFS,'AlienCodes/literate-enigma:other':'3'*40},{**REFS,'AlienCodes/literate-enigma:master':'0'*40}]:
            with self.assertRaises(AssertionError):seed.expected_refs(x)
    def test_default_seed_plan_has_no_Git_or_credential_or_network_call_and_missing_approval_rejects(self):
        args=['seed','--work-dir',seed.WORK_DIR,'--handoff',seed.HANDOFF]
        with patch.object(seed,'run',side_effect=AssertionError('network must not run')),patch.object(sys,'argv',args),contextlib.redirect_stdout(io.StringIO())as out:seed.main()
        self.assertFalse(json.loads(out.getvalue())['network_executed'])
        with patch.object(seed,'refs',side_effect=AssertionError('network must not run')),patch.object(sys,'argv',args+['--execute']):
            with self.assertRaises(AssertionError):seed.main()
    def test_source_loader_ignores_pyc_and_refuses_wrong_SHA_or_preloaded_runtime(self):
        name='exact_source58_book67_seeded_stream_runtime';self.assertNotIn(name,sys.modules)
        m=skip.load_exact_source_module(F/'streaming_git_data_asset_transport_proxy_v2.py');self.assertEqual(m.CHUNK,196608)
        try:
            with self.assertRaises(AssertionError):skip.load_exact_source_module(F/'streaming_git_data_asset_transport_proxy_v2.py')
        finally:sys.modules.pop(name,None)
        with tempfile.TemporaryDirectory(dir=F)as d:
            p=Path(d)/'wrong.fixture';p.write_text('raise RuntimeError("must not exec")')
            with self.assertRaises(AssertionError):skip.load_exact_source_module(p)
    def test_400_floor_monitor_stops_group_and_records_failure_no_automatic_retry(self):
        with tempfile.TemporaryDirectory(dir=F)as d:
            r=Path(d);approval=r/'approval.json';approval.write_text(json.dumps({'approved':True,'kind':'root-approved-source58-book67-exact-public-ZIP-two-repository-Git-seed','source_id':'58','new_id':'67','approved_monitor_sha256':monitor.sha(monitor.__file__),'approved_seed_code_sha256':monitor.sha(F/'seed_source58_one_public_zip_dual_git.py'),'handoff_sha256':monitor.HS,'prepared_sha256':monitor.PS,'index_sha256':monitor.IS,'expected_protected_refs':REFS}))
            class Child:
                pid=12345
                def poll(self):return None
                def wait(self):return -15
            with patch.object(monitor,'R',r),patch.object(monitor,'seed_local_plan',return_value={'required_available_before_seed':511295488}),patch.object(monitor,'protected',return_value=REFS),patch.object(monitor,'free',side_effect=[600000000,monitor.FLOOR-1,monitor.FLOOR-1]),patch.object(monitor.subprocess,'Popen',return_value=Child()),patch.object(monitor.os,'killpg')as kill,patch.object(sys,'argv',['monitor','--phase','seed','--approval',str(approval),'--attempt-id','synthetic-floor','--execute']),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit)as e:monitor.main()
            self.assertEqual(e.exception.code,-15);kill.assert_called_once_with(12345,monitor.signal.SIGTERM)
            proof=json.loads(next(r.glob('*MONITOR.json')).read_bytes());self.assertTrue(proof['original400MiB_trip']);self.assertTrue(proof['no_automatic_retry'])
if __name__=='__main__':unittest.main(verbosity=2)
