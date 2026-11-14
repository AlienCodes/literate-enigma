"""Actual bash command-routing + unchanged automatic-cut real-S14 fixture.
Other stage commands are explicit routing stubs, never official gate passes.
"""
import pathlib,json,hashlib,shutil,subprocess,tempfile,os,sys,difflib
B=pathlib.Path(__file__).parent;ROOT=B.parent;REQ=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request/02/视频/脚本/02.json');original=(B/'original-5core-草稿声音.sh').read_bytes();candidate=(B/'草稿声音.sh').read_bytes();AUTO=pathlib.Path('/workspace/work/audit-repo/视频/工具/自动切点.py');auto=AUTO.read_bytes();origdata=json.loads(REQ.read_text());raw_before=REQ.read_bytes();PYS='/workspace/work/video-venv/bin/python'
with tempfile.TemporaryDirectory(prefix='KEEP-CUTS-real-S14-routing-',dir='/workspace/work/video-private-reference-analysis') as td:
 td=pathlib.Path(td);T=td/'tools';T.mkdir();(T/'自动切点.py').write_bytes(auto)
 prefix="import sys,os,pathlib,json,importlib.util\nsp=importlib.util.spec_from_file_location('bootstrap_real_S14',"+repr(str(B/'bootstrap_real_S14.py'))+")\nm=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)\nno=sys.argv[1];outdir='.'\nif 'WRITE' in globals():\n globals().update(m.namespace(no,WRITE))\nelse:\n m.trace('疑点清单.py',sys.argv[1:])\nos.makedirs(outdir, exist_ok=True)\n"
 (T/'疑点清单.py').write_text(prefix)
 stub="import sys,os,pathlib,json\np=pathlib.Path(os.environ['ROUTING_FIXTURE_TRACE'])\nwith p.open('a') as f:f.write(json.dumps({'tool':pathlib.Path(__file__).name,'args':sys.argv[1:],'explicit_routing_stub_not_quality_gate':True},ensure_ascii=False)+'\\n')\nprint('[ROUTING FIXTURE ONLY] 保持已审 接点样本 问题数 未作真实核查；句子：写入/停止仅为grep路由覆盖')\n"
 for n in ['方法进化表.py','区间作废.py','结尾句接点.py','词尾辅音核对.py','句内响度.py','确认按位置迁移.py','读音核对.py']:(T/n).write_text(stub)
 (T/'快速重建核查.sh').write_text('#!/bin/bash\npython3 "'+str(T/'快速重建核查-fixture.py')+'" "$@"\n');(T/'快速重建核查-fixture.py').write_text(stub)
 cases=[]
 for name,body,mode,kind in [('original-default',original,None,'actual-PV-scan'),('candidate-unset',candidate,None,'actual-PV-scan'),('candidate-zero',candidate,'0','actual-PV-scan'),('candidate-preserve',candidate,'1','actual-PV-scan'),('candidate-negative-zero',candidate,'0','voiced-negative'),('candidate-negative-preserve',candidate,'1','voiced-negative')]:
  W=td/name;W.mkdir();(W/'scripts').mkdir();source=W/'scripts/02.json';source.write_bytes(raw_before);shell=W/'草稿声音.sh';shell.write_bytes(body);trace=W/'route.jsonl';env={**os.environ,'XG_TOOLS':str(T),'XG_KEEP_REVIEWED_GAIN':'1','XG_KEEP_REVIEWED_ENDING':'1','ROUTING_FIXTURE_TRACE':str(trace),'ROUTING_CANDIDATE_KIND':kind,'PATH':str(pathlib.Path(PYS).parent)+os.pathsep+os.environ.get('PATH',''),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','STRICT_CACHE':'1'}
  env.pop('XG_KEEP_REVIEWED_CUTS',None)
  if mode is not None:env['XG_KEEP_REVIEWED_CUTS']=mode
  p=subprocess.run(['bash',str(shell),'02'],cwd=W,env=env,capture_output=True,text=True);stdout=p.stdout+p.stderr;(B/f'{name}-routing-full.log').write_text(stdout);calls=[json.loads(x) for x in trace.read_text().splitlines()];result=json.loads(source.read_text());changed=source.read_bytes()!=raw_before
  row={'case':name,'mode':mode,'fixture':kind,'bash_exit':p.returncode,'source_bytes_changed':changed,'S14_NV_after':result['非人声区间']['S14'],'calls':calls,'source_SHA256_after':hashlib.sha256(source.read_bytes()).hexdigest(),'stdout_SHA256':hashlib.sha256(stdout.encode()).hexdigest(),'unmodified_original_auto_SHA256':hashlib.sha256((T/'自动切点.py').read_bytes()).hexdigest(),'non_auto_commands_are_routing_stubs_not_quality_acceptance':True};cases.append(row);print(name,p.returncode,'changed',changed,'NV',row['S14_NV_after'],flush=True)
 assert cases[0]['calls']==cases[1]['calls']==cases[2]['calls']
 assert cases[0]['source_SHA256_after']==cases[1]['source_SHA256_after']==cases[2]['source_SHA256_after']
 assert cases[0]['S14_NV_after']==origdata['非人声区间']['S14']+[[4.183958,4.275,'紧贴词尾']]
 preserve=cases[3];assert preserve['bash_exit']==0 and not preserve['source_bytes_changed']
 auto_calls=[c for c in preserve['calls'] if c['tool']=='自动切点.py'];assert len(auto_calls)==4 and all('--写入' not in c['args'] for c in auto_calls)
 expected_other=[c for c in cases[0]['calls'] if c['tool']!='自动切点.py'];assert expected_other==[c for c in preserve['calls'] if c['tool']!='自动切点.py']
 assert '  删 S14' in (B/'candidate-preserve-routing-full.log').read_text()
 for row in cases[4:]:assert row['bash_exit']==0 and not row['source_bytes_changed']
 assert '疑点里有 ≥-30 dB' in (B/'candidate-negative-zero-routing-full.log').read_text() or '交人看 1' in (B/'candidate-negative-zero-routing-full.log').read_text()
 assert all(c['unmodified_original_auto_SHA256']==hashlib.sha256(auto).hexdigest() for c in cases)
 report={'kind':'KEEP_REVIEWED_CUTS-isolated-shell-contract-and-real-auto-S14-tests','quality_acceptance':False,'native_full_qualities_not_executed_in_routing_harness':True,'original_shell_SHA256':hashlib.sha256(original).hexdigest(),'candidate_shell_SHA256':hashlib.sha256(candidate).hexdigest(),'original_automatic_algorithm_file_unchanged_SHA256':hashlib.sha256(auto).hexdigest(),'default_unset_and_zero_exact_original_command_trace_equal':True,'default_unset_and_zero_exact_original_source_output_equal':True,'mode1_original_algorithm_still_executed_all_three_rounds_and_final_readonly_scan':True,'mode1_actual_original_S14_proposal_printed_and_source_bytes_unchanged':True,'mode1_other_original_command_argument_sequence_retained_including_end_writer_gain_migration_checks':True,'actual_voiced_negative_cannot_create_NV_in_both_modes':True,'source_core_PAY_or_actual_cache_modified':False,'cases':cases}
 assert REQ.read_bytes()==raw_before
 (B/'isolated-routing-and-real-algorithm-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='cases'},ensure_ascii=False))
