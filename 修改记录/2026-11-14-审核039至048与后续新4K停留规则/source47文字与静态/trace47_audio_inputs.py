"""Read-only effective model input and DSP comparison; never synthesize audio."""
import hashlib,importlib.util,json
from pathlib import Path
H=Path(__file__).parent;B=H.parent;F=B/'next-passed-native/43533004625/47/files'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('unchanged_original_input_capture',B/'audio14-color-review-input-invariance/inspect14_audio_inputs.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert hashlib.sha256(m.r.m.source.encode()).hexdigest()=='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
paths={'request':H/'before/视频/脚本/47.json','accepted_actual':F/'47-source.json','candidate':H/'candidate-payload/视频/脚本/47.json'}
rows={k:m.source_inputs(p)for k,p in paths.items()}
for d in rows.values():
 semantic=d['audio_semantics'];semantic.pop('S12_and_other_legacy_DSP_conditions');semantic['article_control_condition']='47>=26: original automatic gain rule active; 47>=46: existing original ending condition unchanged';d['audio_semantics_sha256']=hashlib.sha256(m.canonical(semantic)).hexdigest()
a=rows['request']['audio_semantics'];assert all(r['audio_semantics']==a for r in rows.values())
prep=F/'47-checker-reference-preparation.json';p=json.loads(prep.read_text());calls=p['reference_calls'];matched=[]
for plan in a['model_input_plans']:
 hit=[r for r in calls if r['exact_native_cache_key']==plan['expected_exact_cache_key']]
 matched.append({'sentence':plan['sentence'],'role':plan['role'],'method':plan['method'],'expected_cache_key':plan['expected_exact_cache_key'],'actual_old_native_key_observed':bool(hit),'actual_old_effective_input_sha_match':any(r['cache_input_text_sha256']==plan['effective_input_sha256']for r in hit),'is_separate_donor':plan['sentence']=='供体'})
assert all(x['actual_old_native_key_observed']and x['actual_old_effective_input_sha_match']for x in matched if not x['is_separate_donor'])
report={'article':'47','book_order':'28','kind':'read-only-original-effective-model-input-and-DSP-invariance','passed_input_invariance':True,'new_video_or_audio_generated':False,'new_video_quality_acceptance':False,'original_maker_sha256':hashlib.sha256(m.r.m.source.encode()).hexdigest(),'title_and_all_14_sentence_rows_chunks_paragraphs_punctuation_timing_and_all_DSP_exact':True,'all_effective_model_input_plans_equal':True,'actual_effective_model_input_count':len(a['model_input_plans']),'actual_old_native_preparation':{'path':str(prep),'sha256':sha(prep),'crosschecks':matched,'model_sha256':p['models_sha256'],'fixed_voice_file_sha256':p['fixed_voice_sha256']},'audio_semantics_sha256':rows['candidate']['audio_semantics_sha256'],'sources':rows,'control_top_level':m.controls,'plain_pipeline':'Original render.strip_gloss, emphasis removal and exact chunk join; original spoken numeric/quote normalization and original pronunciation wrapper; model and voice cache keys captured without TTS or cache writes.','qualification':'Input equality is proved for this own actual accepted47 preparation. The new native MP4 must still pass all official audio gates and exact accepted AAC packet comparison after authorized render; this report does not claim a new MP4 exists.'}
out=H/'original-audio-input-invariance.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'plans':len(a['model_input_plans']),'sha256':sha(out)},ensure_ascii=False))
