"""Isolated original A23 selftest candidate: no production edits or TTS."""
import pathlib,importlib.util,json,hashlib,re,types,tempfile,os,difflib,contextlib,io
B=pathlib.Path(__file__).parent;P=B.parent/'diagnose16-pronunciation-readonly.py';spec=importlib.util.spec_from_file_location('actual_original_phonemes',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original=(m.T/'读音核对.py').read_text();old="        keep_w = PRON_WORDS.pop(w); got = {line for _, line, bad in check(no) if bad}; PRON_WORDS[w] = keep_w"
new="""        # Keep the compound registry intact while injecting its real uncorrected
        # espeak pronunciation. Popping Haber-Bosch also changes the replacement
        # count for Haber inside that compound and aborts before check() can
        # identify the intentionally wrong pronunciation.
        keep_w = PRON_WORDS[w]
        PRON_WORDS[w] = re.sub(r'[,;:.!?]', '', KT.tokenizer.phonemize(w, 'en-us')).strip()
        try:
            got = {line for _, line, bad in check(no) if bad}
        finally:
            PRON_WORDS[w] = keep_w"""
assert original.count(old)==1;candidate=original.replace(old,new);(B/'读音核对-selftest-candidate.py').write_text(candidate);(B/'selftest-candidate.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='original/视频/工具/读音核对.py',tofile='candidate/视频/工具/读音核对.py')))
ns=m.ns;ns.update({'json':json,'os':os,'__file__':str(B/'只读原读音核对.py'),'R':types.SimpleNamespace(strip_gloss=lambda x:re.sub(r'\{\{.*?\}\}','',x))});exec(m.source[m.source.index('# 朗读用的数字读法'):m.source.index('def say(t):')],ns)
# The exact original dictionaries were read from pinned public Git blobs.
for name in ['读音改正.json','按语境读音.json']:(B/'发音词典'/name).write_bytes((m.T/'发音词典'/name).read_bytes())
# Instantiate the original/candidate checker after its producer import line:
# no model session or waveform is needed, only the real Tokenizer above.
def load(code):exec(compile(code[code.index('TD = '):code.rindex("if __name__")],'isolated-original-A23-checker','exec'),ns)
load(original);cwd=pathlib.Path.cwd();report={'kind':'isolated-real-tokenizer-original-A23-selftest-candidate','production_source_dictionary_core_or_cache_modified':False,'TTS_model_inference_performed':False,'quality_acceptance':False,'original_program_SHA256':hashlib.sha256(original.encode()).hexdigest(),'candidate_program_SHA256':hashlib.sha256(candidate.encode()).hexdigest(),'patch_changes_only_selftest_fault_injection':True}
with tempfile.TemporaryDirectory(prefix='A23-candidate-readonly-') as tmp:
 tmp=pathlib.Path(tmp);(tmp/'scripts').mkdir();(tmp/'scripts/16.json').write_bytes(m.Q.read_bytes());os.chdir(tmp)
 try:
  baseline=ns['check']('16');report['unchanged_normal_path_original_bad_count']=sum(bool(bad) for _,_,bad in baseline)
  before=dict(ns['PRON_WORDS']);out=io.StringIO()
  try:
   with contextlib.redirect_stdout(out):ok=ns['selftest']('16')
   report['original_selftest_result_before_patch']=ok
  except BaseException as e:report['original_selftest_exception_before_patch']={'type':type(e).__name__,'message':str(e)}
  # The original raises after pop and does not restore: reset only this private
  # namespace to the true original dict before testing candidate behavior.
  ns['PRON_WORDS'].clear();ns['PRON_WORDS'].update(before);load(candidate);captured=io.StringIO()
  with contextlib.redirect_stdout(captured):ok=ns['selftest']('16')
  after=ns['check']('16');assert ok and after==baseline and ns['PRON_WORDS']==before
  log=captured.getvalue();(B/'candidate-original-selftest.log').write_text(log);report.update({'candidate_full_original_selftest_returned_true':bool(ok),'candidate_exact_normal_check_output_preserved':after==baseline,'candidate_all_PRON_WORDS_original_keys_values_restored':ns['PRON_WORDS']==before,'candidate_full_selftest_raw_log_SHA256':hashlib.sha256(log.encode()).hexdigest(),'actual_K102_per_word_lines':[x for x in log.splitlines() if 'K102' in x],'actual_original_selftest_summary':log.splitlines()[-1]})
 finally:os.chdir(cwd)
(B/'selftest-candidate-isolated-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
