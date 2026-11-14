"""Narrow final18 contract and real decoder diagnostics; no production pass claims."""
from pathlib import Path
from types import SimpleNamespace
import ast
import copy
import hashlib
import importlib.util
import json

H=Path(__file__).parent
B=H.parent
P=H/'illustrated_tail.py'
OLD=B/'article28-user-review-20261114/hold18-integrator/illustrated_tail.py'
POLICY=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-051.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('normal18',P);M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
assert sha(OLD)=='a05b4455de5225bfca0f5f2ee8fa31ce59d15cd3556dd831228a754fc290831a'
assert sha(POLICY)==M.FINAL_HOLD18_POLICY_SHA256
wrong=H/'wrong-policy-diagnostic.json';wrong.write_text('{"not_the_approved_policy":true}\n')
rows=[]
def args(sid='36',hold=18,preview=0,policy=POLICY,fixture=False):
    return SimpleNamespace(source_id=sid,final_last_body_hold_frames=hold,preview_last_body_hold_frames=preview,final_hold_policy=policy,validation_fixture=fixture)
def check(name,a,t,frames,expected):
    try: result=M.final_hold_contract(a,t,frames);accepted,error=True,None
    except Exception as e: result,accepted,error=None,False,str(e)
    assert accepted is expected,(name,accepted,error)
    rows.append(dict(name=name,kind='unit_contract_not_native_delivery',expected_accept=expected,actual_accept=accepted,result=result,error=error))
t=dict(kind='last-body-hold18-then-summary60',last_body_hold_frames=18,finalization_authorized=True,preview_only=False,source_voice_endpoint_seconds=157.33)
for sid in sorted(M.FINAL_HOLD18_SOURCE_IDS): check('authorized_final_'+sid,args(sid),t,4738,True)
for sid in ['01','07','28','35','61','70']: check('unfinalized_or_preview_'+sid,args(sid),t,4738,False)
for n in [9,17,19,8,10,-1,.6,'18',True]: check('wrong_final_count_'+repr(n),args(hold=n),t,4738,False)
for policy in [None,wrong,H/'absent-policy.json']: check('wrong_policy_'+str(policy),args(policy=policy),t,4738,False)
check('reject_mixed_final_preview',args(preview=18),t,4738,False)
check('reject_synthetic_final',args(fixture=True),t,4738,False)
for k,v in [('kind','preview-last-body-hold18-then-summary60'),('kind','immediate-standalone-summary'),('finalization_authorized',False),('finalization_authorized',1),('preview_only',True),('preview_only',0),('last_body_hold_frames',17),('last_body_hold_frames',True),('preview_last_body_hold_frames',18)]:
    q=copy.deepcopy(t);q[k]=v;check('wrong_metadata_'+k+'_'+str(v),args(),q,4738,False)
for k in ['finalization_authorized','preview_only','last_body_hold_frames']:
    q=copy.deepcopy(t);q.pop(k);check('missing_'+k,args(),q,4738,False)
for frame in [4729,4737,4739,4747]: check('wrong_ceiling_or_gap_'+str(frame),args(),t,frame,False)
for endpoint,frame in [(157.4,4740),(.4,30),(.7,39)]:
    q=copy.deepcopy(t);q['source_voice_endpoint_seconds']=endpoint
    check('exact_06_gap_fraction_'+str(endpoint),args(),q,frame,True)
q=copy.deepcopy(t);q['source_voice_endpoint_seconds']=157.4
check('upper_gap_boundary_exclusive',args(),q,4741,False)
check('early_gap_below_06',args(),q,4739,False)
check('final_metadata_without_cli',args(hold=0,policy=None),t,4738,False)
check('policy_without_cli',args(hold=0),dict(kind='immediate-standalone-summary'),None,False)

# Legacy default and article28 preview functions remain literally AST identical.
of={n.name:n for n in ast.parse(OLD.read_text()).body if isinstance(n,ast.FunctionDef)}
nf={n.name:n for n in ast.parse(P.read_text()).body if isinstance(n,ast.FunctionDef)}
unchanged=[n for n in of if n not in ('main','provenance')]
assert all(ast.dump(of[n])==ast.dump(nf[n]) for n in unchanged)
legacy=[]
for gap in [0,.005,1/30-.0000001]:
    a=args(sid='53',hold=0,policy=None);q=dict(kind='immediate-standalone-summary',source_voice_endpoint_seconds=.4-gap)
    assert M.final_hold_contract(a,q,12) is False and M.preview_hold_contract(a,q,12) is False
    legacy.append(dict(kind='default0',gap=gap,passed=True))
pt=dict(kind='preview-last-body-hold18-then-summary60',preview_only=True,preview_last_body_hold_frames=18,source_voice_endpoint_seconds=157.33)
pa=args(sid='28',hold=0,preview=18,policy=None)
assert M.final_hold_contract(pa,pt,4738) is False and M.preview_hold_contract(pa,pt,4738) is True
legacy.append(dict(kind='source28_preview18',passed=True))
dec=[]
for name,expected in [('decoder19_actual_same_page',True),('decoder19_actual_last_hold_changed',False),('decoder19_actual_first_hold_changed',False),('decoder18_actual_missing_hold',False)]:
    p=OLD.parent/(name+'.mp4')
    try:r=M.verify_final_hold(p,19);accepted,error=True,None
    except Exception as e:r,accepted,error=None,False,str(e)
    assert accepted is expected,(name,accepted,error)
    dec.append(dict(kind='actual_existing_small_encoded_decoder_diagnostic_not_native_delivery',name=name,path=str(p),sha256=sha(p),expected_accept=expected,actual_accept=accepted,error=error,result=r))
out=H/'normal18-scope-fraction-legacy-and-actual-decoder-tests.json'
r=dict(passed=True,program_sha256=sha(P),original_a05_sha256=sha(OLD),policy_sha256=sha(POLICY),only_authorized_final_source_ids=sorted(M.FINAL_HOLD18_SOURCE_IDS),normal_contract_tests=rows,legacy_default_and_preview_tests=legacy,original_functions_AST_identical=unchanged,actual_decoder_tests=dec,test_count=len(rows)+len(legacy)+len(dec),exact_rational_gap_interval='[18/30,19/30)',real_normal_final_new_body_full_positive_pending=True,no_formal_production_pass_claimed=True)
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=True,tests=r['test_count'],program_sha256=sha(P),report_sha256=sha(out))))
