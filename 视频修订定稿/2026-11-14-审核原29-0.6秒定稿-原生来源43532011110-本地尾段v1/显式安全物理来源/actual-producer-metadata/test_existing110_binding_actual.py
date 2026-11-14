from pathlib import Path
import ast,copy,hashlib,importlib.util,json,tempfile
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=W/'illustrated_tail110.py';sp=importlib.util.spec_from_file_location('exact_actual110_binding',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
ready=json.loads((W/'ready-book39-source29.json').read_text());up=json.loads(Path(ready['upstream_record']).read_text());status=json.loads((Path(ready['upstream_record']).parent/'29-upstream-summary-status.json').read_text());src=Path(ready['actual_request_source']);approved=next(r for r in json.loads(Path(ready['actual_layout_approval']).read_text())['articles']if r['source_id']=='29')
result=m.source_layout_binding(src,'29',status,approved);assert result['source_role']=='already-validated-final-source'
rejected=[]
for label,mode in [('wrong-original-request','request'),('wrong-old-status','old'),('wrong-approved-row','row'),('changed-final-source','source')]:
 s=copy.deepcopy(status);r=copy.deepcopy(approved)
 with tempfile.TemporaryDirectory(dir='/dev/shm')as temp:
  source=src
  if mode=='request':s['request_source_sha256']['视频/脚本/29.json']='0'*64
  elif mode=='old':s['inherited_original_summary_status_sha256']='0'*64
  elif mode=='row':r['summary_rgb_sha256']='0'*64
  else:source=Path(temp)/'changed.json';source.write_bytes(src.read_bytes()+b'\n')
  try:m.source_layout_binding(source,'29',s,r)
  except AssertionError:rejected.append(label)
  else:raise AssertionError(label)
old=Path('/workspace/work/review35-source53-hold06-20261114/illustrated_tail061.py');func=lambda b:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(b).body if isinstance(n,ast.FunctionDef)};a,b=func(old.read_text()),func(p.read_text());same=[n for n in a if n not in {'main','final_hold_contract','source_layout_binding'}];assert all(a[n]==b[n]for n in same)
report={'kind':'post-export-exact-existing-final-source-role-binding-tests','passed':True,'actual_source_role_positive':result,'actual_negative_cases_rejected':rejected,'original_physical_AAC_clock_picture_hold_decoder_functions_AST_exact':same,'helper_path':str(p),'helper_sha256':sha(p),'no_media_or_frozen_handoff_mutation':True,'original_candidate8023_test_report_kept_as_history':True}
out=W/'source29-exact-existing-final-source-role-tests-v2.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(out,sha(out))
