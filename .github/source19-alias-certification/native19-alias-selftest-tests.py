#!/usr/bin/env python3
"""Real original source19 pronunciation namespace; no TTS, mock verdict or altered normal dictionary."""
from pathlib import Path
import argparse,ast,contextlib,copy,hashlib,io,json,re
p=argparse.ArgumentParser()
for name in ['tools','requests','old-certified-tool','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();candidate=(a.tools/'读音核对.py').read_text();oldtext=a.old_certified_tool.read_text();assert sha(a.old_certified_tool)=='50f4363bb2fc2930be59904cdccfa44fd46f14393a0385c7846028ee25b4e84c';assert sha(a.tools/'读音核对.py')=='8dcde2ba66ad9405bb58344839ecaaf54aa321c5267d4ef3f286627e11d3f7bb';strip=lambda text:[ast.dump(n,include_attributes=False)for n in ast.parse(text).body if not isinstance(n,ast.FunctionDef)or n.name!='selftest'];assert strip(oldtext)==strip(candidate)
source=Path('scripts/19.json');before_source=source.read_bytes()if source.exists()else None;raw=(a.requests/'19.json').read_bytes();source.write_bytes(raw);dicts={str(p.relative_to(a.tools)):sha(p)for p in(a.tools/'发音词典').glob('*')if p.is_file()}
def load(text):
 ns={'__name__':'real_native19_alias_namespace','__file__':str(a.tools/'读音核对.py')};exec(compile(text[:text.rindex('if __name__')],str(a.tools/'读音核对.py'),'exec'),ns);return ns
old=load(oldtext);normal=old['check']('19');assert sum(bool(bad)for _,_,bad in normal)==0;prior=dict(old['PRON_WORDS']);prior_order=list(old['PRON_WORDS']);log=io.StringIO();error=None
with contextlib.redirect_stdout(log):
 try:old['selftest']('19')
 except SystemExit as e:error=str(e)
 finally:old['PRON_WORDS'].clear();old['PRON_WORDS'].update(prior)
assert error and 'tulip 出现 1 次，整句里正确读音 0 处'in error;assert old['check']('19')==normal
new=load(candidate);assert new['check']('19')==normal;before=dict(new['PRON_WORDS']);keys=list(new['PRON_WORDS']);captured=io.StringIO()
with contextlib.redirect_stdout(captured):result=new['selftest']('19')
assert result is True and new['PRON_WORDS']==before and list(new['PRON_WORDS'])==keys and new['check']('19')==normal
required=['Tulip','tulip','tulips','Mackay',"Mackay's",'Alkmaar','windhandel','Goldgar'];lines=captured.getvalue().splitlines()
for word in required:assert any(f'K102 ② {word}：'in line and '报 BAD（当样本）'in line for line in lines),word
faults=[]
for words in [('Tulip','tulip'),('tulips',),('Mackay',"Mackay's")]:
 prior={w:new['PRON_WORDS'][w]for w in words}
 try:
  for w in words:new['PRON_WORDS'][w]=re.sub(r'[,;:.!?]','',new['KT'].tokenizer.phonemize(w,'en-us')).strip()
  bad=[line for _,line,isbad in new['check']('19')if isbad];assert bad
  for w in words:assert any(re.search(r'\] '+re.escape(w)+r"(['’]s)? ",line)for line in bad),w
  faults.append({'actual_fault_words':list(words),'unchanged_real_check_reported_BAD':bad})
 finally:new['PRON_WORDS'].update(prior)
assert new['PRON_WORDS']==before and list(new['PRON_WORDS'])==keys
# Exact unrelated exceptions still propagate, and finally restores every affected alias.
actual_check=new['check']
def fault_check(no):
 if new['PRON_WORDS']!=before:raise RuntimeError('actual19-unrelated-exception-sentinel')
 return actual_check(no)
new['check']=fault_check;seen=False
with contextlib.redirect_stdout(io.StringIO()):
 try:new['selftest']('19')
 except RuntimeError as e:assert str(e)=='actual19-unrelated-exception-sentinel';seen=True
assert seen and new['PRON_WORDS']==before and list(new['PRON_WORDS'])==keys;new['check']=actual_check;assert new['check']('19')==normal
assert all(sha(a.tools/name)==s for name,s in dicts.items());assert source.read_bytes()==raw
report={'passed':True,'kind':'actual-native-original19-complete-alias-possessive-selftest-regression','all_nonselftest_AST_exact':True,'actual_old_certified_failure':error,'candidate_full_original_selftest_true':True,'all_required_aliases_actual_BAD':required,'real_independent_BAD_faults':faults,'normal_original_check_full_output_exact':True,'all_dictionary_keys_values_order_restored':True,'all_dictionary_files_unchanged':dicts,'unrelated_exception_propagates_and_aliases_restore':True,'source_sha256':hashlib.sha256(raw).hexdigest(),'candidate_sha256':sha(a.tools/'读音核对.py'),'old_certified_selftest_stdout':log.getvalue(),'candidate_selftest_stdout':captured.getvalue(),'TTS_audio_or_video_generated':False,'article_audio_acceptance_claimed':False};a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if before_source is None:source.unlink()
else:source.write_bytes(before_source)
print(json.dumps({k:v for k,v in report.items()if k not in ['all_dictionary_files_unchanged','old_certified_selftest_stdout','candidate_selftest_stdout','real_independent_BAD_faults']},ensure_ascii=False))
