import hashlib,json,tempfile,types,unittest
from pathlib import Path
import seed_source48_one_public_zip_git as seed
import resume_a0ba_with_exact_backup_seed_skip as skip
import streaming_git_data_asset_transport_proxy_v2 as original
from test_streaming_git_data_asset_transport_proxy_v2 import FakeGit
class Contracts(unittest.TestCase):
 def test_standard_Git_objects_real_fixture_independent_SHA_and_no_source_copy(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);source=root/'input.fixture';data=b'\0\xffonly synthetic Git fixture\n'*100;source.write_bytes(data);blob=seed.gitsha('blob',data);tree,commit,stamp=seed.identities(blob,'2026-11-15T01:02:03Z');g=root/'objects.git'
   seed.local_objects(g,source,blob,tree,commit,stamp)
   self.assertEqual(seed.run(['git','--git-dir='+str(g),'rev-parse',commit+'^{tree}']),tree)
   self.assertEqual(seed.run(['git','--git-dir='+str(g),'rev-list','--parents',commit]),commit)
   self.assertEqual(source.read_bytes(),data);self.assertFalse(any(p.suffix in {'.zip','.pack'}for p in root.rglob('*')))
   seed.run(['git','--git-dir='+str(g),'fsck','--full'])
 def fixture(self,fail=None):
  b=types.SimpleNamespace(path=Path('never-read.fixture'),size=skip.SIZE,sha256=skip.ZIP,git_sha=skip.BLOB)
  files=[{'repo_path':'视频修订定稿/fixture/public.fixture','bytes':skip.SIZE,'sha256':skip.ZIP,'git_blob_sha':skip.BLOB}];trees,hashes=original.make_trees(files)
  bundle={'blobs':{skip.BLOB:b},'files':files,'trees':trees,'hashes':hashes,'prefix':'视频修订定稿/fixture','meta':{'asset_branch':'codex/passed4k-assets-123-48-hold18-postonly-v1'},'commit':original.commit_spec(hashes[''],'2026-11-15T01:02:03Z')}
  class Client(FakeGit):pass
  module=types.SimpleNamespace(GitDataClient=Client,require=original.require);records=[];before=Client.verify_blob;skip.install_exact_skip(module,records.append);self.assertIs(Client.verify_blob,before)
  return bundle,Client(bundle,fail),records,module,b
 def test_exact_seed_route_skips_only_POST_and_original_full_raw_guard_runs(self):
  b,c,records,_,_=self.fixture();original.publish_repository(c,skip.REPO,b,lambda row:None)
  self.assertNotIn('post_blob',c.calls);self.assertIn('verify_blob',c.calls);self.assertEqual(len(records),1);self.assertIn('POST-not-executed-or-claimed',records[0]['route'])
  self.assertIn('git/refs',c.posts)
 def test_wrong_raw_even_after_exact_seed_skip_still_blocks_ref(self):
  b,c,records,_,_=self.fixture('raw')
  with self.assertRaises(original.GuardError):original.publish_repository(c,skip.REPO,b,lambda row:None)
  self.assertNotIn('git/refs',c.posts);self.assertEqual(len(records),1)
 def test_other_repository_or_blob_preserves_original_POST(self):
  b,c,records,_,blob=self.fixture();c.post_blob('alienalgorithm/postgraduate-vocabulary',blob);self.assertIn('post_blob',c.calls);self.assertFalse(records)
  c.calls=[];other=types.SimpleNamespace(git_sha='0'*40,size=1,sha256='0'*64);c.post_blob(skip.REPO,other);self.assertIn('post_blob',c.calls);self.assertFalse(records)
 def test_wrong_exact_target_bytes_or_SHA_rejected_without_POST(self):
  for size,sha in [(skip.SIZE-1,skip.ZIP),(skip.SIZE,'0'*64)]:
   b,c,records,_,_=self.fixture();wrong=types.SimpleNamespace(git_sha=skip.BLOB,size=size,sha256=sha)
   with self.assertRaises(original.GuardError):c.post_blob(skip.REPO,wrong)
   self.assertNotIn('post_blob',c.calls);self.assertFalse(records)
if __name__=='__main__':unittest.main(verbosity=2)
