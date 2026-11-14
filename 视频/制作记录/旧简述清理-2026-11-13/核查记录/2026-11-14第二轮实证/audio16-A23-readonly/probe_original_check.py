"""Run unchanged original A23 checker functions against real Tokenizer only."""
import pathlib,importlib.util,tempfile,json,os,types,re,hashlib
P=pathlib.Path('/workspace/work/video-audit70-20261113/diagnose16-pronunciation-readonly.py');spec=importlib.util.spec_from_file_location('original_phoneme_probe',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ns=m.ns;ns.update({'json':json,'os':os,'__file__':str(m.B/'只读原读音核对.py'),'R':types.SimpleNamespace(strip_gloss=lambda x:re.sub(r'\{\{.*?\}\}','',x))})
original=m.source;exec(original[original.index('# 朗读用的数字读法'):original.index('def say(t):')],ns)
source=(m.T/'读音核对.py').read_text();exec(source[source.index('TD = '):source.index('# 罗马数字')],ns)
oldcwd=pathlib.Path.cwd()
with tempfile.TemporaryDirectory(prefix='A23-readonly-check-') as tmp:
 tmp=pathlib.Path(tmp);(tmp/'scripts').mkdir();(tmp/'scripts/16.json').write_bytes(m.Q.read_bytes());os.chdir(tmp)
 try:
  base=ns['check']('16');before={l for _,l,bad in base if bad};word='Haber-Bosch';keep=ns['PRON_WORDS'][word];ns['PRON_WORDS'][word]=re.sub(r'[,;:.!?]','',ns['KT'].tokenizer.phonemize(word,'en-us')).strip()
  try:fault=ns['check']('16')
  finally:ns['PRON_WORDS'][word]=keep
  after=ns['check']('16');assert after==base
 finally:os.chdir(oldcwd)
added=[l for _,l,bad in fault if bad and l not in before];target=[x for x in added if re.search(r'\] Haber-Bosch ',x)];assert target,'Real original check failed to detect proposed actual wrong compound pronunciation.'
r={'kind':'unchanged-original-A23-check-real-tokenizer-fault-probe','quality_acceptance':False,'production_dictionary_or_checker_or_source_modified':False,'TTS_inference_or_cache_write':False,'original_check_program_SHA256':hashlib.sha256(source.encode()).hexdigest(),'original_baseline_bad_line_count':len(before),'actual_compound_bad_really_detected_by_original_check':True,'actual_added_BAD_lines':added,'actual_added_target_BAD_lines':target,'full_original_check_output_restored_after_dictionary_restoration':True,'fault_is_key_preserving_real_raw_espeak_IPA_value_in_private_python_namespace_only':True}
out=m.B/'16-key-preserving-fault-original-check-proof.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
