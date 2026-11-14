"""Contract tests are labelled unit/legacy-fixture diagnostics, never actual preview delivery."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,subprocess,sys
H=Path(__file__).parent;B=H.parents[1];O=B/'illustrated-tail';P=H/'illustrated_tail.py';F=O/'validation-only';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('isolated_hold9',P);M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
records=[]
def check(name,args,timing,frames,expected):
 try:r=M.preview_hold_contract(SimpleNamespace(source_id=args[0],preview_last_body_hold_frames=args[1],validation_fixture=args[2]),timing,frames);passed=True;error=None
 except Exception as e:r=None;passed=False;error=str(e)
 assert passed is expected,(name,passed,error)
 records.append({'name':name,'kind':'unit_contract_not_native_media','expected_accept':expected,'actual_accept':passed,'return':r,'error':error})
t={'kind':'preview-last-body-hold9-then-summary60','preview_only':True,'preview_last_body_hold_frames':9,'source_voice_endpoint_seconds':157.31666666666666}
check('authorized28exact9',('28',9,False),t,4729,True)
for sid in ['01','14','17','27','29','70']:check('reject_other_article_'+sid,(sid,9,False),t,4729,False)
for hold in [8,10,-1,0.3,'9',True]:check('reject_hold_'+repr(hold),('28',hold,False),t,4729,False)
for field,value in [('kind','immediate-standalone-summary'),('kind','preview-last-body-hold10-then-summary60'),('preview_only',False),('preview_only',1),('preview_last_body_hold_frames',8),('preview_last_body_hold_frames',True)]:
 q=copy.deepcopy(t);q[field]=value;check('reject_declaration_'+field+'_'+str(value),('28',9,False),q,4729,False)
check('reject_synthetic_preview',('28',9,True),t,4729,False)
for frames in [4728,4730]:check('reject_wrong_frame_boundary_'+str(frames),('28',9,False),t,frames,False)
check('reject_preview_decl_without_cli',('28',0,False),t,4729,False)
for gap in [0,0.005,1/30-0.0000001]:check('legacy_default_immediate_'+str(gap),('53',0,False),{'kind':'immediate-standalone-summary','source_voice_endpoint_seconds':.4-gap},12,True)
check('legacy_default_reject_pause',('53',0,False),{'kind':'immediate-standalone-summary','source_voice_endpoint_seconds':.1},12,False)
check('legacy_synthetic_default',('01',0,True),{'source_voice_endpoint_seconds':.395},12,True)
origast=ast.parse((H/'illustrated_tail.original-dc204b.py').read_text());newast=ast.parse(P.read_text());origf={n.name:n for n in origast.body if isinstance(n,ast.FunctionDef)};newf={n.name:n for n in newast.body if isinstance(n,ast.FunctionDef)}
unchanged=[n for n in origf if n not in('provenance','main')];assert all(ast.dump(origf[n])==ast.dump(newf[n])for n in unchanged)
# Run the genuine pre-existing4K synthetic fixture through the actual CLI, with the exact same art/summary/IDR/AAC assertions. It remains synthetic/non-deliverable.
manifest=Path('/workspace/work/punk-print-20261113-v3/book-illustrations70.json');rows=json.loads(manifest.read_text())['illustrations'];image=next(r['approved_book_illustration_path']for r in rows if r['source_id']=='01')
base=[sys.executable,P,'--source-id','01','--input',F/'synthetic-idr.mp4','--verification',F/'idr-proof.json','--illustration-manifest',manifest,'--order-manifest',B/'publication-order-manifest-readonly.json','--crop-review',O/'illustration-crop-review70.json','--illustration',image,'--summary-image',B/'final-layout/cards/01.png','--layout-approval',O/'approved-video-layouts70.json','--output',H/'legacy-synthetic-compatibility-only.mp4','--report',H/'legacy-synthetic-compatibility-report.json','--work',H,'--overwrite','--validation-fixture']
with(H/'legacy-synthetic-compatibility.log').open('w')as log:rc=subprocess.run(list(map(str,base)),stdout=log,stderr=subprocess.STDOUT).returncode
assert rc==0,(H/'legacy-synthetic-compatibility.log').read_text()[-2000:];r=json.loads((H/'legacy-synthetic-compatibility-report.json').read_text());assert r['passed']and r['production_delivery_eligible']is False and r['kind']=='approved-book-illustration60-then-approved-summary60';assert r['body_coded_pictures_identical']and r['aac_packet_payload_and_absolute_timings_identical'];assert'preview_only'not in r
for label,extra,replace in [('preview_wrong_article',['--preview-last-body-hold-frames','9'],None),('invalid_hold8',['--preview-last-body-hold-frames','8'],None),('invalid_hold10',['--preview-last-body-hold-frames','10'],None),('wrong_image',[],('illustration',next(z['approved_book_illustration_path']for z in rows if z['source_id']=='22'))),('missing_idr',[],('input',F/'synthetic-no-idr.mp4'))]:
 cmd=list(base)
 if replace:
  key,value=replace;cmd[cmd.index('--'+key)+1]=value
  if key=='input':cmd[cmd.index('--verification')+1]=F/'no-idr-proof.json'
 out=H/f'{label}-rejection.json';cmd[cmd.index('--report')+1]=out
 with(H/f'{label}.log').open('w')as log:rr=subprocess.run(list(map(str,cmd+extra)),stdout=log,stderr=subprocess.STDOUT).returncode
 q=json.loads(out.read_text());assert rr!=0 and q['passed']is False;records.append({'name':label,'kind':'actual_legacy_fixture_CLI_negative','expected_reject':True,'actual_exit':rr,'error':q['error'],'report':str(out),'report_sha256':sha(out)})
result={'kind':'isolated_article28_hold9_contract_and_actual_legacy_fixture_checks','passed':True,'program_sha256':sha(P),'original_program_sha256':sha(H/'illustrated_tail.original-dc204b.py'),'all_original_non_main_non_provenance_functions_AST_identical':unchanged,'unit_and_scope_tests':records,'test_count':len(records),'legacy_real_fixture_full_postprocessor_passed':True,'legacy_fixture_report_sha256':sha(H/'legacy-synthetic-compatibility-report.json'),'original_default_kind_and_nonproduction_eligibility_preserved':True,'genuine_source28_preview_positive_still_pending':True,'no_formal_production_pass_claimed':True};out=H/'hold9-contract-and-legacy-compatibility-tests.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'tests':len(records),'program_sha256':sha(P),'report_sha256':sha(out)},ensure_ascii=False))
