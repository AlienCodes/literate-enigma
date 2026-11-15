"""Only actual user137 source16 controlled Origin report; original checks are consumed unchanged."""
import json
from pathlib import Path
PROFILE=json.loads(Path(__file__).with_name('exact137-source16-instrument-binding.json').read_text())
def require(ok,message):
 if not ok:raise ValueError(message)
def actual_source16_repair_scope(review,native,raw_audio,article):
 p=PROFILE
 require(article==native.get('article')==raw_audio.get('article')=='16','Only exact user137 source16 acoustic instrument')
 require(native.get('passed')is True and native.get('canonical_pipeline_passed')is True and native.get('stage')=='final4K-passed','Source16 original full native gates must actually pass')
 require(raw_audio.get('kind')=='controlled_audio_repair'and raw_audio.get('passed')is True and raw_audio.get('repair_applied')is True and raw_audio.get('diagnostic_only')is False and raw_audio.get('production_delivery_eligible')is True and native.get('approved_audio_qc')==raw_audio,'Source16 actual production report missing, diagnostic, failed or replaced')
 require(raw_audio.get('original_quality_gates_modified')is False and raw_audio.get('requires_separate_original_complete_pipeline_pass')is True and raw_audio.get('private_raw_GT_or_cache_arrays_exported')is False,'Original quality/actual private-data role differs')
 scope=native.get('approved_audio_repair_scope',{});req=native.get('request_source_sha256',{})
 require(scope.get('kind')=='controlled_audio_repair'and scope.get('repair_applied')is True and scope.get('actual_original_full_pipeline_passed_first')is True and scope.get('whole_track_actual_audio_and_approved_unchanged_regions_required')is True,'Source16 actual native repair scope absent')
 require(req.get('视频/脚本/16.json')==scope.get('request_source_sha256')==review.get('request_source_sha256')==p['request_source_sha256']and req.get('视频/工具/初稿生成/gen16.py')==p['request_generator_sha256'],'Actual137 request/GEN differs')
 require(review.get('tool')=='audio16-origin-qc.py'and native.get('approved_audio_qc_program_sha256')==raw_audio.get('program_sha256')==review.get('program_sha256')==p['program_sha256']and scope.get('reference_file_sha256')==raw_audio.get('reference_sha256')==review.get('reference_file_sha256')==p['reference_sha256'],'Actual Origin instrument/reference differs')
 require(native.get('core_repair_manifest_sha256')==p['core_manifest_sha256']and native.get('exact_original_correct_Origin_cache_verified')is True,'Actual corrected Origin producer/cache not verified')
 require(native.get('final_wav_sha256')==raw_audio.get('actual_producer_PCM_sha256')==p['expected_raw_WAV_sha256']and native.get('canonical_aac_adts_sha256')==p['expected_new_AAC_ADTS_sha256']and raw_audio.get('canonical_sha256')==native.get('canonical_video_sha256'),'Actual new Origin raw/canonical/AAC differs')
 require(native.get('accepted_source',{}).get('sha256')==raw_audio.get('accepted_sha256')==p['accepted_video_sha256']and native.get('accepted_source',{}).get('aac_adts_sha256')==p['accepted_AAC_ADTS_sha256']and native.get('accepted_prior_aac_identical')is False,'Keep original pronunciation and corrected voice honestly distinct')
 rows=raw_audio.get('checks',[]);names={x.get('name')for x in rows};require(rows and len(names)==len(rows)and set(p['required_original_check_names'])<=names and all(x.get('passed')is True for x in rows),'Actual original Origin QC incomplete, duplicate or failed')
 require(raw_audio.get('certified_correct_Origin_cache_readback',{}).get('sha256')==p['cache_readback_sha256']and raw_audio.get('approved_correct_Origin_reference_evidence')==p['correct_Origin_reference_evidence'],'Actual native cache readback/provenance differs')
 return True
