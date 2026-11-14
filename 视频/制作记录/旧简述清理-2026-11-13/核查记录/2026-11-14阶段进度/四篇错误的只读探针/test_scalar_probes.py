"""In-memory fixtures only: verify unchanged native gate results and scalar-only observation."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np

O=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('safe_scalar_probe',O/'probe_hooks/safe_scalar_probe.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
os.environ.update(VIDEO_SAFE_SCALAR_DIR=str(O/'unit-fixture-scalars'),VIDEO_SAFE_SCALAR_ARTICLE='06',
                  VIDEO_SAFE_SCALAR_MAKER=str(O/'original-tools/make_video.py'),
                  VIDEO_SAFE_SCALAR_SOURCE=str(O.parent/'payload/视频/脚本/06.json'))
tree=ast.parse((O/'original-tools/make_video.py').read_text())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_env5','_像吸气帧','_nonvoice'}]
namespace={'np':np,'SR':24000,'AUD_DB':-55}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'original-native-nonvoice-AST','exec'),namespace)
assert P.install()
P._state['fixture_only']=True
P._state['synthetic_validation_fixture']=True
cases=[]
source=json.loads(Path(os.environ['VIDEO_SAFE_SCALAR_SOURCE']).read_text())
label=' '.join(__import__('re').sub(r'\{\{.*?\}\}','',c['en']).replace('**','').strip() for c in source['sentences'][18]['chunks'])


def wave():
    value=np.zeros(24000);value[18000:18120]=1.0;return value


def test(name,a,interval,expected_predicates):
    P._state['_seen'].clear();before=hashlib.sha256(a.tobytes()).hexdigest();count=len(P._state['observations'])
    native_failed=False
    try:namespace['_nonvoice'](a,[interval],label)
    except SystemExit:native_failed=True
    assert native_failed==bool(expected_predicates),name
    assert hashlib.sha256(a.tobytes()).hexdigest()==before,'Input waveform was changed by hook/native copy'
    records=P._state['observations'][count:]
    if expected_predicates:
        assert len(records)==1,records
        assert records[0]['kind']=='nonvoice_original_gate_failure_predicates',records
        assert set(records[0]['failed_predicate_names'])==set(expected_predicates),(name,records)
    else:assert not records,records
    cases.append({'test':name,'original_native_exception_result_unchanged':True,'input_array_unchanged':True,
                  'expected_original_predicates_observed':list(expected_predicates),'passed':True})


test('actual-native-bounds-branch',wave(),[.02,1.5],['invalid_interval_bounds'])
a=wave();a[479:481]=.0005
test('actual-native-attached-start-zero-crossing-branch',a,[.02,.03,'紧贴词尾'],['attached_start_not_zero_crossing'])
a=wave();a[720:840]=.1
test('actual-native-external-post-window-branch',a,[.02,.03,'紧贴词尾'],['external_post5ms_not_quiet'])
a=wave();a[480:720]=.1
test('actual-native-region-level-branches',a,[.02,.03],['region_RMS_above_original_threshold','region_5ms_peak_at_or_above_original_threshold'])
test('actual-native-valid-interval-remains-valid',wave(),[.02,.03],[])
sys.settrace(None)
try:P._safe(np.zeros(5));raise RuntimeError('Probe accepted waveform array')
except TypeError:cases.append({'test':'refuses-waveform-data-object-in-JSON','passed':True})
x=np.linspace(-.2,.2,120);a=2*x
L={'it':{'idx':0,'text':'SYNTHETIC UNIT FIXTURE ONLY'},'A':a.copy(),'gx':x.copy(),'x':x.copy(),
   'a0':0,'p':0,'L0':120,'N':120,'isl':[(0,120)],'sig':np.array([True]),'blk':[(0,120,None)],
   'matched':[],'g':1.0,'c':1.0}
frame=SimpleNamespace(f_locals=L,f_globals={'np':np,'SR':24000,'TOL':2.2/32768},
                      f_code=SimpleNamespace(co_name='audit',co_filename='SYNTHETIC UNIT FIXTURE ONLY'),f_lineno=213)
before=[hashlib.sha256(L[k].tobytes()).hexdigest() for k in ('A','gx','x')]
P._audit_empty(frame);record=P._state['observations'][-1]
assert record['local_LS_gain_ratio_to_used_global_gain']==2
assert record['anchor_residual_max_PCM_LSB_local_LS_fit']==0
assert before==[hashlib.sha256(L[k].tobytes()).hexdigest() for k in ('A','gx','x')]
cases.append({'test':'empty-match-anchor-fit-scalars-only-without-changing-gain-reference-or-input','passed':True})
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_nonvoice')
baseline_hash=P._ast_sha(function)
function._fields=tuple(name for name in function._fields if name!='type_params')
assert P._ast_sha(function)==baseline_hash==P.NONVOICE_AST_SHA
cases.append({'test':'exact-native-AST-pin-portable-between-Python3.11-and3.12-empty-type-params','passed':True})
report={'passed':True,'fixture_only_not_actual_failure_diagnosis':True,'count':len(cases),
        'maker_original_nonvoice_AST_used_unmodified':True,'native_source_audio_cache_GT_or_threshold_modified':False,
        'PCM_or_GT_files_created_or_exported':False,'probe_sha256':hashlib.sha256((O/'probe_hooks/safe_scalar_probe.py').read_bytes()).hexdigest(),
        'tests':cases}
(O/'probe-unit-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'fixture_only':True,'count':len(cases)}))
