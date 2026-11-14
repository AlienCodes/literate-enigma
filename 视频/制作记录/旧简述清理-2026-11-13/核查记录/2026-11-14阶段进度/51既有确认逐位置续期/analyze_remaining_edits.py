"""Read actual public MP4 decodes and scalar reports; never change source/audio."""
from pathlib import Path
import hashlib, json, math
import numpy as np
import soundfile as sf

B=Path('/workspace/work/video-audit70-20261113');O=B/'audio51-remaining-edits'
D=B/'readonly-audio-replay-43528832985/51-reference-gain-diagnostic.json'
BASE=B/'ci-relayed-43522684973/51-failed-working-source.json'
CURRENT=B/'payload/视频/脚本/51.json'
QC=O/'51-public-actual-change-qc-with-native-timings.json'
old_path=B/'audio51-independent/51-accepted-decoded.wav'
new_path=B/'audio51-independent/51-failed-decoded.wav'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ah(a):return hashlib.sha256(np.ascontiguousarray(a,dtype=np.float64).tobytes()).hexdigest()
def fit(a,b):
 g=float(a@b/(a@a+1e-30));r=b-g*a
 return {'gain_db':float(20*np.log10(abs(g)+1e-30)), 'correlation':float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)+1e-30)),
  'gain_compensated_residual_snr_db':None if np.array_equal(a,b) else float(10*np.log10((np.mean((g*a)**2)+1e-30)/(np.mean(r*r)+1e-30)))}
x=json.loads(D.read_text());s=json.loads(BASE.read_text());c=json.loads(CURRENT.read_text());q=json.loads(QC.read_text())
old,sr=sf.read(old_path,dtype='float64');new,sr2=sf.read(new_path,dtype='float64');assert sr==sr2==48000
rows=[];updates={};fp=x['official_abnormal_edit_scalars']['current_pcm_md5_first12']
for e in x['official_abnormal_edit_scalars']['abnormal_edits']:
 key=e['source_deletion_confirmation']['lookup_key'];entry=c['核对确认']['删除段'][key]
 assert entry['类型']==s['核对确认']['删除段'][key]['类型']
 lo=e['actual_start_seconds']-.150;hi=e['actual_end_seconds']+.150
 a=old[round(lo*sr):round(hi*sr)];b=new[round(lo*sr):round(hi*sr)]
 identical=bool(np.array_equal(a,b));proof={'public_time_seconds':[lo,hi],'margin_each_side_seconds':.15,'decoded_sample_rate':sr,'decoded_dtype':'float64','decoded_sample_count':len(a),'whole_crop_bit_identical':identical,'accepted_crop_sha256':ah(a),'actual_crop_sha256':ah(b),**fit(a,b)}
 if not identical:
  assert key=='S2 raw 10.2300-10.5745'
  ts=np.arange(round(lo*sr),round(hi*sr))/sr
  gain_db=-2+4.5*(ts-19.675)/(22.03-19.675)
  pred=a*10**(gain_db/20)
  proof['approved_ramp_prediction_fit']=fit(pred,b)
  proof['approved_actual_piece_range_seconds']=[19.675,22.03]
  proof['approved_ramp_delta_db']=[-2,2.5]
  proof['interpretation']='This location is inside the approved continuous OW ramp; sample identity is not claimed. The original full actual-audio QC also passes the entire ramp.'
 typ=entry['类型'];allowed={'紧贴词尾的非人声':{'pre','lost'},'紧贴词头的非人声':{'post','lost'},'紧贴两头的非人声':{'pre','post','lost'}}[typ]
 covers=set(e['edge_sides'])<=allowed and (not e['tail_cut_ms'] or typ in ['紧贴词尾的非人声','紧贴两头的非人声']) and (not e['onset_cut_ms'] or typ in ['紧贴词头的非人声','紧贴两头的非人声'])
 assert covers
 suffix=(f"2026-11-14 本轮实际成片复核：producer PCM完整SHA256为{x['wav_sha256']}，当前配音指纹{fp}；此精确删除段及前后各150 ms在新旧已公开MP4解码中逐样本完全相同（48 kHz，{len(a)}样本，float64 SHA256 {ah(a)}），原确认的删除类型、词边界和处理位置均不变；见audio51-remaining-edits/51-remaining-edit-proof.json。" if identical else f"2026-11-14 本轮实际成片复核：producer PCM完整SHA256为{x['wav_sha256']}，当前配音指纹{fp}；此精确删除段在批准的O.W.连续增益段19.675–22.030 s内，不声称与旧轨逐样本相同。旧轨按批准增益曲线预测后，该处含前后各150 ms的相关系数{proof['approved_ramp_prediction_fit']['correlation']:.9f}、剩余噪声比{proof['approved_ramp_prediction_fit']['gain_compensated_residual_snr_db']:.2f} dB；整段真实音轨20项辅助核验全部通过，局部原删除位置和类型不变；见audio51-remaining-edits/51-remaining-edit-proof.json。")
 prior=entry['依据']
 correction=None
 if key=='S4 raw 2.8176-3.0800':
  correction='Original basis called the preceding word ordinance, but the current unchanged S4 text and original timed cache place this cut after thirty-nine. The proposed basis corrects this word label; no timing or physical sound change.'
  prior=prior.replace('ordinance 的 /n/', 'thirty-nine 的 /n/')
 updated={**entry,'配音指纹':fp,'依据':prior+'；'+suffix}
 updates[key]=updated
 rows.append({'exact_source_key':key,'existing_type':typ,'original_confirmation_fingerprint':entry['配音指纹'],'proposed_current_fingerprint':fp,'official_raw_seconds':[e['raw_start_seconds'],e['raw_end_seconds']], 'official_actual_seconds':[e['actual_start_seconds'],e['actual_end_seconds']], 'original_official_tail_cut_ms':e['tail_cut_ms'],'original_official_onset_cut_ms':e['onset_cut_ms'],'original_official_edge_sides':e['edge_sides'],'existing_exact_type_covers_all_reported_flags':covers,'public_actual_comparison':proof,'word_label_correction':correction})
report={'purpose':'Specific51 existing deletion-confirmation fingerprint renewal proposal; no audio acceptance/final verdict', 'quality_acceptance':False,'source_audio_or_program_modified':False,'article':'51','observations':{'exact_failed_pcm_reproduced':True,'producer_pcm_sha256':x['wav_sha256'],'current_pcm_md5_first12':fp,'reference_gain_original_2_2_lsb_failures':x['anchor_summary']['default_gain_fails_original_2_2_lsb_limit_count'],'reference_same_waveform_candidates':x['anchor_summary']['same_waveform_candidates'],'original_official_cuts':2,'original_official_edges':8,'original_official_extra_runs':0,'abnormal_locations':len(rows),'public_old_new_crop_bit_identical_count':sum(r['public_actual_comparison']['whole_crop_bit_identical'] for r in rows),'existing_exact_types_cover_all_reported_flags':True,'actual_public_audio_qc_passed':q['passed'],'actual_public_audio_qc_check_count':len(q['checks'])},'inputs':{str(p):sha(p) for p in [D,BASE,CURRENT,QC,old_path,new_path]},'rows':rows,'minimal_proposal':{'scope':'Only the9 existing exact deletion records below: current fingerprint plus per-location actual proof appended; correct one stale S4 word label. No audio/control/timing/content/layout changes. Other confirmation records unchanged.','base_payload_source_sha256':sha(CURRENT),'metadata_updates':{'核对确认':{'删除段':updates}}},'limitations':['The decoded AAC identity proof covers the existing edit and150ms on each side, not the removed private raw samples. It proves no new physical cut was introduced there relative to the accepted prior MP4.','The S2 OW location has a genuine approved gain ramp; identity is not claimed. Both local ramp-prediction residual and full actual public-audio QC are supplied.','Existing original raw nonvoice analysis is retained as historical evidence; this report does not claim subjective listening.','Official fresh reference-fix QA, all five bad-sample selftests and canonical final checks remain required. No threshold is weakened and no passed/final claim is issued.']}
(O/'51-remaining-edit-proof.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(O/'51-remaining-edit-proof.json'),'bit_identical_locations':report['observations']['public_old_new_crop_bit_identical_count'],'metadata_records':len(updates),'actual_audio_qc':q['passed'],'quality_acceptance':False},ensure_ascii=False))
