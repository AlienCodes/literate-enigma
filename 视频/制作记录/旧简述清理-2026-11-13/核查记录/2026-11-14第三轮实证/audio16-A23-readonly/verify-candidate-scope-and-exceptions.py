import pathlib,importlib.util,json,ast,hashlib,tempfile,os,contextlib,io
B=pathlib.Path(__file__).parent;p=B/'build-and-test-selftest-candidate.py';spec=importlib.util.spec_from_file_location('candidate_validation_reuse',p);m=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(m)
old=ast.parse(m.original);new=ast.parse(m.candidate)
def without_selftest(t):return [ast.dump(x,include_attributes=False) for x in t.body if not isinstance(x,ast.FunctionDef) or x.name!='selftest']
assert without_selftest(old)==without_selftest(new)
ns=m.ns;original_check=ns['check'];before=dict(ns['PRON_WORDS']);captured=False
# Explicit test sentinel during the first K102 injected mispronunciation. It
# must propagate rather than being converted to a successful detection.
def raising_check(no):
 if ns['PRON_WORDS']!=before:raise RuntimeError('unrelated-checker-exception-test-sentinel')
 return original_check(no)
ns['check']=raising_check;cwd=pathlib.Path.cwd()
with tempfile.TemporaryDirectory(prefix='A23-candidate-exception-') as td:
 td=pathlib.Path(td);(td/'scripts').mkdir();(td/'scripts/16.json').write_bytes(m.m.Q.read_bytes());os.chdir(td)
 try:
  with contextlib.redirect_stdout(io.StringIO()):
   try:ns['selftest']('16')
   except RuntimeError as e:assert str(e)=='unrelated-checker-exception-test-sentinel';captured=True
 finally:os.chdir(cwd);ns['check']=original_check
assert captured and ns['PRON_WORDS']==before
r={'kind':'candidate-exact-scope-and-non-swallowed-exception-proof','candidate_SHA256':hashlib.sha256(m.candidate.encode()).hexdigest(),'all_non_selftest_original_AST_nodes_identical':True,'unrelated_exception_during_fault_injection_propagates_unchanged':True,'selected_PRON_entry_restored_even_after_exception':True,'quality_gate_failure_not_converted_to_success':True,'production_code_modified':False,'TTS_inference_or_cache_write':False,'quality_acceptance':False}
(B/'candidate-scope-and-exception-proof.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
