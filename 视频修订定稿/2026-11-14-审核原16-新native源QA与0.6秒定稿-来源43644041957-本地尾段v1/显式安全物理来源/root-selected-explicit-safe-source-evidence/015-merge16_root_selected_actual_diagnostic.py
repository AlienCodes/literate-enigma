"""Root-selected exact metadata and genuine display-timing correction only."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
H=Path(__file__).parent;C=H/'candidate-payload';B=Path('/workspace/work/video-audit70-20261113');O=H/'root-selected-actual-native-diagnostic';O.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();j=lambda p:json.loads(Path(p).read_text());dump=lambda p,d:Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');root=Path('/dev/shm/root-source16-seven-identity-FP-new-PV-and-genuine-left-highlight-selection-decision.json');assert sha(root)=='18d6ea90ffed5f23082e9015ceda4ebd8a29eac1c3160a5b9790ae8d799043e5';D=j(root)
sp=importlib.util.spec_from_file_location('original_gen16_text_preflight',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P)
rels={'source':'视频/脚本/16.json','GEN':'视频/工具/初稿生成/gen16.py','MD':'新版定稿/16-the-bread-made-from-air.md'};expected={'source':'f649978f37e3e2db20a7f2ece52e1fa835095c65f680143d7809cd65d79f1fb9','GEN':'982567e7f680fd594cc089027e7361ac55479abc128c017d905fd5aceac06f77','MD':'8f8947e036a02d5ad1af0106e00b56d0a9a2b8137a83181e97e40c9c1a08c01a'}
for k,rel in rels.items():assert sha(C/rel)==expected[k],(k,sha(C/rel))
prior=O/'before-root-selected';prior.mkdir(exist_ok=True)
for k,rel in rels.items():
 q=prior/rel;q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copyfile(C/rel,q)
old=j(C/rels['source']);new=copy.deepcopy(old);ops=D['seven_existing_typed_only_exact_operations']+D['separate_new_S15_operations'];beforeproof=[]
for op in ops:
 w=new
 for key in op['path'][:-1]:w=w[key]
 key=op['path'][-1]
 if 'before'in op:assert w.get(key)==op['before']
 else:assert op['before_absent']and key not in w
 beforeproof.append({'path':op['path'],'before_or_absence_exact':True});w[key]=copy.deepcopy(op['after'])
diff=P.differences(old,new);assert len(diff)==12,(len(diff),diff)
assert all(old[k]==new[k]for k in old if k not in ['核对确认','高亮开始'])
for r in D['seven_existing_typed_only_exact_operations']:
 k=r['path'][2];x=copy.deepcopy(new['核对确认']['删除段'][k]);x['配音指纹']='630cbdf1eae2';assert x==old['核对确认']['删除段'][k]
assert old['核对确认']['短语']==new['核对确认']['短语'];assert old['sentences']==new['sentences'];assert new['高亮开始']=={**old['高亮开始'],'S15 第2块':112.32};assert old['核对确认']['非人声'].items()<=new['核对确认']['非人声'].items()
# Pure generator contains the complete revised JSON seed, including the exact metadata.
gen,issues=P.pure_generator(new);assert gen and not issues;dump(C/rels['source'],new);(C/rels['GEN']).write_text(gen);assert sha(C/rels['MD'])==expected['MD']
shutil.copyfile(root,O/root.name);history={'kind':'retired-inaccurate-S15-highlight-confirmation-verbatim-history-only','never_load_into_current_confirmation':True,'retired':old['核对确认']['高亮']['S15 第2块'],'reason':'Old basis incorrectly called punctuation Haber-comma and onsetleft111.956; actual clause startsHaber afterorigin comma. True originalDTWmethodAleft112.32 selected by root with fresh objectivebasis.','root_decision_sha256':sha(root),'old_request_source_sha256':expected['source']};dump(O/'retired-old-S15-highlight-confirmation-history-only.json',history)
record={'kind':'source16-exact-root-selected-source-GEN-merge-no-audio-change','source_id':'16','book_order':'45','root_decision':{'path':str(root),'sha256':sha(root)},'before':expected,'after':{k:sha(C/r)for k,r in rels.items()},'before_operation_matches':beforeproof,'exact12_leaf_changes':diff,'source_and_GEN_only_modified':True,'MD_byte_exact':True,'all18_sentence_words_notes_foci_and_summary_exact':True,'existing_relative_of_T22_and_authorization_metadata_preserved':True,'all_audio_DSP_speed_pitch_gain_cut_pause_voice_settings_exact':True,'only_visual_timing_request_changed':'S15 第2块112.0→112.32; no spoken sample change','all_existing_seven_CF_type_basis_verbatim':True,'new_S15_purevoice_confirmation_is_new_actual837_not_old_migration':True,'retired_wrong_highlight_basis_preserved_as_history_only':True,'failed6cdf_not_adopted_as_request_source':True,'failed_stage_G35_VFP_and_other_CF_migrations_not_imported':True,'expected_new_wholevoice':{'PCM_SHA256':'317ece6e3e20f4b97323c5e3235b552b72a905c9551c3502c7d38888efe46532','PCM_MD5_first12':'8372545e9b06','AAC_SHA256':'f858c0d2d9ed55a2c405609eda0e7fb4d7d8e38ee3bf4766cf4be2bf956be80f'},'no_new_voice_or_cache_G36_model_or_CORE_run':True,'native_full_gate_video_final_acceptance_not_claimed':True,'PDF_PAY_main_remote_unchanged':True};dump(O/'actual-root-selected-source-GEN-merge.json',record);print(json.dumps(record['after'],ensure_ascii=False));print('record_sha256',sha(O/'actual-root-selected-source-GEN-merge.json'))
