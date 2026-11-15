import json,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import observe_frozen_proxy_v2_once as o
class GuardError(RuntimeError):pass
class ObserverTests(unittest.TestCase):
 def test_exact_owned_status_templates_only_and_no_text_saved(self):
  outer=GuardError('Transport stopped');inner=GuardError('Blob POST failed status 502; no ref progression');outer.__context__=inner
  self.assertEqual([x['HTTP_status_from_exact_owned_template']for x in o.safe_chain(outer,GuardError)],[None,502])
  for error in [GuardError('SECRET https://host/token status 403'),GuardError('Blob POST failed status 502; no ref progression SECRET'),ValueError('Blob POST failed status 502; no ref progression')]:
   text=json.dumps(o.safe_chain(error,GuardError));self.assertNotIn('SECRET',text);self.assertNotIn('https:',text);self.assertNotIn('502',text);self.assertNotIn('403',text)
  self.assertEqual(o.safe_chain(GuardError('Git API GET failed status 403; no ref progression'),GuardError)[0]['HTTP_status_from_exact_owned_template'],403)
 def test_stage_strips_branches_URL_and_any_credentials(self):
  result=o.safe_stage({'method':'POST','git_endpoint':'https://host/SECRET','response':'SECRET','url':'SECRET'});self.assertEqual(result,{'method':'POST'})
  self.assertEqual(o.safe_stage({'method':'GET','git_endpoint':'git/ref/heads/SECRET'}),{'method':'GET','Git_endpoint_category':'git/ref/heads'})
 def run_fixture(self,broken_receipt=False):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);module=root/'frozen.fixture';module.write_text('not executable fixture');w=root/'work';w.mkdir();receipt=root/'streaming-observer-fixture.json';approval=root/'approval.json';approval.write_text(json.dumps({'safe_exception_observer_sha256':'observer-fixture'}));original=GuardError('Transport stopped');original.__context__=GuardError('Blob POST failed status 502; no ref progression')
   def fake_main():
    a=w/'streaming-attempt-new';a.mkdir();p=a/'stopped-not-READY.json';p.write_text('bad json'if broken_receipt else json.dumps({'safe_Git_stage':{'method':'POST','git_endpoint':'git/blobs','response':'SECRET'}}));raise original
   core=types.SimpleNamespace(GuardError=GuardError,main=fake_main);spec=types.SimpleNamespace(name='offline_observer_fixture',loader=types.SimpleNamespace(exec_module=lambda _:None))
   argv=['observer','--module',str(module),'--receipt',str(receipt),'--','--work-dir',str(w),'--approval',str(approval)]
   with patch('sys.argv',argv),patch.object(o,'digest',side_effect=lambda p:o.MODULE_SHA if Path(p)==module else 'observer-fixture'),patch.object(o.importlib.util,'spec_from_file_location',return_value=spec),patch.object(o.importlib.util,'module_from_spec',return_value=core):
    with self.assertRaises(GuardError)as caught:o.main()
   self.assertIs(caught.exception,original)
   if not broken_receipt:
    result=json.loads(receipt.read_text());self.assertEqual(result['safe_exception_chain'][1]['HTTP_status_from_exact_owned_template'],502);self.assertNotIn('SECRET',receipt.read_text());self.assertTrue(result['same_original_exception_reraised'])
 def test_real_observer_main_reraises_identical_original_exception(self):self.run_fixture()
 def test_broken_log_does_not_replace_original_exception(self):self.run_fixture(True)
if __name__=='__main__':unittest.main(verbosity=2)
