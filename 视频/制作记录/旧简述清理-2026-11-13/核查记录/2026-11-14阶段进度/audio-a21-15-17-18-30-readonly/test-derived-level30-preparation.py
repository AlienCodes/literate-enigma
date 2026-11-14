"""Real original-math development fixture; not a native final-video acceptance."""
import pathlib,ast,types,sys,importlib.util,json,os,tempfile,hashlib,subprocess
import numpy as np,soundfile as sf
B=pathlib.Path(__file__).parent;PRIVATE=pathlib.Path('/workspace/work/video-private-reference-analysis');Q=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/prepare-derived-level30.py')
spec=importlib.util.spec_from_file_location('exact_level_preparation',Q);q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
spec=importlib.util.spec_from_file_location('level30_probe',B/'30-auto-level-key-probe.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
m=probe.m;new=probe.new;ns,sent=m.scope_for(new,9);pieces=[];gaps=[];p0=0;lst=ns['list_commas'](sent)
import re
for p in re.finditer(r'[,;:](?=\s)',sent):pieces.append((p0,p.end()));p0=p.end()+1;gaps.append(.2 if p.start() in lst else .4)
pieces.append((p0,len(sent)));clips,tmap=ns['sentence_audio'](sent,pieces,gaps)
original=m.source;tree=ast.parse(original);funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_auto_level','_short起','_短起','_to_repo')]
sys.path.insert(0,str(m.T));report={'kind':'real-original-G36-math-development-tests','new_native_production_or_video_pass_not_claimed':True,'helper_SHA256':q.sha(Q),'original_maker_SHA256':hashlib.sha256(original.encode()).hexdigest(),'private_raw_cache_bytes_exported':False}
with tempfile.TemporaryDirectory(prefix='level30-original-math-fixture-',dir=PRIVATE) as td:
 td=pathlib.Path(td);cache=td/'cache';cache.mkdir();public=td/'public';public.mkdir();disabled=td/'no-export'
 # Genuine original cache entries only, kept private and removed with fixture.
 for key in m.cache_rows:
  (cache/key).write_bytes(m.git('视频/配音缓存/'+key))
 old='调平_9df6a5142a93c3be736350dd3c3d6203b0cd6eba.json';(cache/old).write_bytes(m.git('视频/配音缓存/'+old))
 before=q.inventory(cache);module=types.ModuleType('unchanged_original_auto_level')
 module.__dict__.update({'json':json,'np':np,'os':os,'_hl':hashlib,'_CACHE':str(cache),'_REPO_CACHE':str(public),'SR':24000,'sf':sf})
 exec(compile(ast.Module(body=funcs,type_ignores=[]),'original_make_video_functions','exec'),module.__dict__)
 os.environ['STRICT_CACHE']='1'
 a=q.ensure_level(module,clips,tmap,gaps,cache,disabled);assert a['created_exact_derived_JSON'] and a['private_cache_additions']==[q.EXPECTED_NAME]
 midway=q.inventory(cache);b=q.ensure_level(module,clips,tmap,gaps,cache,disabled);assert not b['created_exact_derived_JSON'] and q.inventory(cache)==midway
 bad=[c.copy() for c in clips];bad[0][1000]+=.0001
 try:q.ensure_level(module,bad,tmap,gaps,cache,disabled);raise AssertionError('non-target-input unexpectedly allowed')
 except AssertionError as e:assert 'approved exact G36 key' in str(e)
 assert q.inventory(cache)==midway and os.environ['STRICT_CACHE']=='1'
 assert all(midway[k]==v for k,v in before.items()) and q.inventory(public)=={}
 report.update({'exact_new_missing_key_genuinely_computed_by_original_function':a,'existing_exact_key_reread_writes_nothing':b,'wrong_clip_bytes_rejected_before_any_write':True,'all_real_preexisting_mother_and_old_JSON_SHA_unchanged':True,'strict_restored_after_real_math':True,'private_fixture_removed_on_exit':True,'original_auto_level_function_AST_SHA256':hashlib.sha256(ast.dump(next(x for x in funcs if x.name=='_auto_level'),include_attributes=False).encode()).hexdigest(),'protected_real_preexisting_cache_files':len(before)})
out=B/'prepare-derived-level30-development-validation.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'report':str(out),'helperSHA':report['helper_SHA256'],'actual_original_fixture_gains':a['actual_original_returned_gain_dB'],'new_key':q.EXPECTED_NAME,'tests_passed':True},ensure_ascii=False))
