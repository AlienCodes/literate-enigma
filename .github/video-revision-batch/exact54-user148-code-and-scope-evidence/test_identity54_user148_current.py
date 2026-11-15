"""Pure contract tests. No media quality result or original native pass is simulated."""
import ast, copy, hashlib, importlib.util, json
from pathlib import Path

O=Path(__file__).parent
spec=importlib.util.spec_from_file_location('identity54_tests_target',O/'identity54_user148_current.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=m.read_reference(O/'identity54_user148_current-reference.json')
C=Path('/workspace/work/article54-user147-review-draft-20261114/candidate-payload')
source=json.loads((C/'视频/脚本/54.json').read_text())
auth_path=Path('/workspace/work/article54-user147-review-draft-20261114/native-inputs/54-user-authorization-PROPOSAL.json')
base={'canonical_pipeline_passed':True,'request_files':{rel:m.file_measurement(C/rel)for rel in p['request_files']},
      'requested_source':source,'current_source':copy.deepcopy(source),
      'authorization_file':m.file_measurement(auth_path),'authorization':json.loads(auth_path.read_text()),
      'root_actual_S6_decision':copy.deepcopy(p['root_actual_S6_decision']),
      'actual_S6_report':copy.deepcopy(p['actual_S6_report']),'core_manifest':copy.deepcopy(p['core_manifest']),
      'runtime_files':copy.deepcopy(p['runtime_files']),'current_audio':copy.deepcopy(p['current_audio']),
      'legacy_audio':copy.deepcopy(p['legacy_provenance'])}
results=[]
def run(name,edit=None):
 v=copy.deepcopy(base)
 if edit:edit(v)
 result=m.validate_values(v,p)
 expected=edit is None
 assert result['identity_binding_passed'] is expected,(name,result)
 assert result['formal_quality_acceptance']is False and result['repair_applied']is False
 assert result['actual_source_and_final_media_V3_still_required']is True
 results.append({'name':name,'expected_identity_passed':expected,'actual_identity_passed':result['identity_binding_passed'],'correct_rejection_or_scalar_fixture':True,'failed_predicates':[x['name']for x in result['checks']if not x['passed']]})
run('exact_scalar_contract_fixture_only_not_actual_gate_or_media_pass')
for rel in p['request_files']:
 run('wrong_request_file:'+rel,lambda v,rel=rel:v['request_files'][rel].update(sha256='0'*64))
run('changed_CF_same_actual_source_rejected',lambda v:v['current_source']['核对确认']['响度骤降']['95.6–96.0s'].update(依据='changed'))
run('source_note_even_one_space_rejected',lambda v:v['current_source']['sentences'][-1]['chunks'][-1].update(note=v['current_source']['sentences'][-1]['chunks'][-1]['note']+' '))
run('wrong_authorization_bytes',lambda v:v['authorization_file'].update(sha256='0'*64))
run('review102_cannot_be_final148',lambda v:v['authorization'].update(review_only=True,user_individual_finalization_authorized=False))
for key in ('root_actual_S6_decision','actual_S6_report','core_manifest'):
 run('wrong_actual_file:'+key,lambda v,key=key:v[key].update(sha256='0'*64))
for rel in p['runtime_files']:
 run('wrong_actual_runtime:'+rel,lambda v,rel=rel:v['runtime_files'][rel].update(sha256='0'*64))
run('wrong_whole_WAV',lambda v:v['current_audio'].update(whole_WAV_sha256='0'*64))
run('legacy_AAC_as_current',lambda v:v['current_audio'].update(AAC_ADTS_sha256=p['legacy_provenance']['AAC_ADTS_sha256']))
run('wrong_absolute_clock',lambda v:v['current_audio'].update(absolute_packet_projection_sha256='0'*64))
run('wrong_packet_count',lambda v:v['current_audio'].update(packets=p['current_audio']['packets']+1))
run('wrong_legacy_video',lambda v:v['legacy_audio'].update(video_sha256='0'*64))
run('current_as_legacy',lambda v:v['legacy_audio'].update(AAC_ADTS_sha256=p['current_audio']['AAC_ADTS_sha256']))
run('canonical_false_is_not_identity_admission',lambda v:v.update(canonical_pipeline_passed=False))
original=ast.parse(Path('/workspace/work/native-inline-engine-reviewed52-v36-final99d-exact19-CF/delivery.py').read_text())
actual=ast.parse((O/'identity54_user148_current.py').read_text())
astsame={}
for name in ('require','digest','command','actual_aac'):
 a=next(x for x in original.body if isinstance(x,ast.FunctionDef)and x.name==name)
 b=next(x for x in actual.body if isinstance(x,ast.FunctionDef)and x.name==name)
 astsame[name]=ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
 assert astsame[name]
report={'kind':'pure-source54-user148-identity-binding-data-and-original-packet-function-tests','all_tests_passed':True,'cases':results,'count':len(results),'actual_request_file_SHA_checks_performed':True,'actual_native_acoustic_checks_executed':False,'actual_media_QA_pass_claimed':False,'original_function_AST_exact':astsame}
(O/'pure-identity-binding-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'count':len(results),'original4_function_AST_exact':astsame}))
