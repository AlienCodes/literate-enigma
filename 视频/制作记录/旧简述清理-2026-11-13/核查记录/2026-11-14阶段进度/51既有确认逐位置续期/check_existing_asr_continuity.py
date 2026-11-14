"""Prove continuity for six existing ASR confirmations using real public decodes."""
from pathlib import Path
import hashlib,json
import numpy as np
import soundfile as sf

B=Path('/workspace/work/video-audit70-20261113');O=B/'audio51-remaining-edits'
D=B/'readonly-audio-replay-43528832985/51-reference-gain-diagnostic.json'
S=B/'payload/视频/脚本/51.json';F=B/'ci-direct-43526354790-51/51-status.json'
Q=O/'51-public-actual-change-qc-with-native-timings.json'
old_file=B/'audio51-independent/51-accepted-decoded.wav';new_file=B/'audio51-independent/51-failed-decoded.wav'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ah(a):return hashlib.sha256(np.ascontiguousarray(a,dtype=np.float64).tobytes()).hexdigest()
def evidence(a,b):
 assert len(a)==len(b)
 identical=bool(np.array_equal(a,b) and ah(a)==ah(b))
 return {'decoded_sample_count':len(a),'decoded_dtype':'float64','whole_region_bit_identical':identical,'accepted_decoded_sha256':ah(a),'actual_decoded_sha256':ah(b),'different_sample_count':int(np.count_nonzero(a!=b))}
def fit(a,b):
 gain=float(a@b/(a@a+1e-30));res=b-gain*a
 return {'gain_db':float(20*np.log10(abs(gain)+1e-30)),'correlation':float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)+1e-30)),'gain_compensated_residual_snr_db':float(10*np.log10((np.mean((gain*a)**2)+1e-30)/(np.mean(res**2)+1e-30)))}
x=json.loads(D.read_text());source=json.loads(S.read_text());q=json.loads(Q.read_text());failed=json.loads(F.read_text())
old,sr=sf.read(old_file,dtype='float64');new,sr2=sf.read(new_file,dtype='float64');assert sr==sr2==48000
segments=x['public_producer_timing_metadata']['segments'];fp=x['official_abnormal_edit_scalars']['current_pcm_md5_first12']
rows=[];updates={}
for label in ['S2','S5','S6','S12','S16','S18']:
 original=source['核对确认']['机器复听'][label];parts=segments[label]
 lo=parts[0]['时刻'][0]-.1;hi=parts[-1]['时刻'][1]+.1;k0,k1=round(lo*sr),round(hi*sr)
 a,b=old[k0:k1],new[k0:k1];proof=evidence(a,b)
 record={'sentence':label,'source_English':' '.join(c['en'] for c in source['sentences'][int(label[1:])-1]['chunks']),'existing_confirmation':original,'native_actual_segment_times':parts,'actual_public_sentence_window_seconds':[lo,hi],'margin_seconds':.1,'whole_sentence_comparison':proof}
 if label=='S2':
  assert not proof['whole_region_bit_identical']
  change_lo,change_hi=19.55,22.18;c0,c1=round(change_lo*sr),round(change_hi*sr)
  unchanged_old=np.concatenate([old[k0:c0],old[c1:k1]]);unchanged_new=np.concatenate([new[k0:c0],new[c1:k1]])
  clean=evidence(unchanged_old,unchanged_new);clean['fit']=fit(unchanged_old,unchanged_new)
  record['all_samples_outside_approved_audio_change_window']={'approved_change_window_seconds':[change_lo,change_hi],'compared_windows_seconds':[[lo,change_lo],[change_hi,hi]],**clean}
  piece_proofs=[]
  for part in parts:
   p0,p1=part['时刻'];i0,i1=round(p0*sr),round(p1*sr);old_part,new_part=old[i0:i1],new[i0:i1]
   piece={'piece':part['段'],'actual_time_seconds':[p0,p1],**evidence(old_part,new_part),'direct_waveform_fit':fit(old_part,new_part)}
   if part['段']==3:
    ts=np.arange(i0,i1)/sr;gain=-2+4.5*(ts-p0)/(p1-p0);pred=old_part*10**(gain/20)
    piece['approved_delta_gain_endpoints_db']=[-2,2.5];piece['approved_ramp_prediction_fit']=fit(pred,new_part)
   elif part['段']==2:assert piece['whole_region_bit_identical']
   piece_proofs.append(piece)
  record['per_actual_piece_comparison']=piece_proofs
  record['original_full_actual_audio_qc_ramp_checks']=[r for r in q['checks'] if r['name'] in ['actual-approved-smooth-ramp','actual-ramp-same-waveform-no-new-distortion','actual-pitch-preserved:oll_wright']]
  assert all(r['passed'] for r in record['original_full_actual_audio_qc_ramp_checks'])
  suffix=f"2026-11-14 本轮声音连续性实证：当前配音指纹{fp}，完整producer PCM SHA256 {x['wav_sha256']}。S2真实段时刻10.770–24.225 s，第2段15.950–19.295 s与旧已验成片逐字节相同；第1/4段解码AAC存在微小残差，声波相关系数分别0.999999999997和0.999999907，局部增益分别约0 dB和−0.0000365 dB，不夸称逐样本相同。第3段19.675–22.030 s按获准连续增益差−2→+2.5 dB预测，实际声波形状及oll wright音高由20项真实音轨辅助检查通过。本次不新增拼写/外语或ASR例外，只保留原oll/all识别依据并续当前指纹。详见51-existing-ASR-confirmation-continuity.json。"
 else:
  assert proof['whole_region_bit_identical']
  suffix=f"2026-11-14 本轮声音连续性实证：当前配音指纹{fp}，完整producer PCM SHA256 {x['wav_sha256']}。按真实分段记录取整句{lo:.3f}–{hi:.3f} s（两侧各100 ms）直接比较新旧公开MP4解码，{len(a)}个48 kHz float64样本逐字节完全相同，SHA256 {ah(a)}。原句词音与原误识别解释均未变；本次只续已有确认的当前指纹，不新增ASR依据或豁免。详见51-existing-ASR-confirmation-continuity.json。"
 updates[label]={**original,'配音指纹':fp,'依据':original['依据']+'；'+suffix}
 record['minimal_update']={'old_fingerprint':original['配音指纹'],'new_fingerprint':fp,'existing_original_ASR_basis_retained_verbatim':True,'new_ASR_exception_introduced':False}
 rows.append(record)
report={'article':'51','purpose':'Actual public sound continuity for six existing sentence-specific ASR confirmations; no new ASR basis or exemption','quality_acceptance':False,'source_audio_or_checkers_modified':False,'base_payload_source_sha256':sha(S),'current_producer_pcm_sha256':x['wav_sha256'],'current_producer_pcm_md5_first12':fp,'original_official_ASR_checker_sha256':sha('/workspace/work/audit-repo/视频/工具/机器复听.py'),'observed_actual_failed_run':43526354790,'observed_original_ASR_status_lines':[line for line in failed.get('failure_details',{}).get('tail',[]) if '机器复听' in line or line.strip().startswith(('S2：','S5：','S6：','S12：','S16：'))],'observations':{'existing_confirmation_count':6,'whole_sentence_bit_identical_count':sum(r['whole_sentence_comparison']['whole_region_bit_identical'] for r in rows),'S2_actual_piece2_bit_identical':True,'S2_pieces1_and4_high_fidelity_with_small_decoded_AAC_residuals_not_claimed_identical':True,'actual_public_audio_qc_passed':q['passed'],'actual_public_audio_qc_check_count':len(q['checks'])},'inputs':{str(p):sha(p) for p in [D,S,F,Q,old_file,new_file]},'rows':rows,'minimal_proposal':{'scope':'Only six preexisting 核对确认.机器复听 records S2/S5/S6/S12/S16/S18: renew actual fingerprint and append per-sentence continuity proof. Preserve every original ASR spelling/foreign-language explanation verbatim. No new ASR claim, exception, audio change, or quality-threshold change.','metadata_updates':{'核对确认':{'机器复听':updates}}},'limits':['This is continuity evidence for previously documented ASR discrepancies, not a new phonetic transcription or new subjective listening approval.','The original 机器复听.py two recognizers and selftests remain authoritative. This report does not forge their output, suppress a new mismatch, or replace final canonical QA.','S2 actual samples inside the approved gain window are intentionally changed; sample identity is claimed only for actual piece2. Other unchanged S2 pieces have very small measured decoded AAC residuals, and are described by their gain/correlation/SNR rather than falsely called identical.','Existing original workflow classifies valid, fingerprint-bound actual-voice explanations as user-listening doubt; original current authorization/finalization rules remain unchanged.']}
(O/'51-existing-ASR-confirmation-continuity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(O/'51-existing-ASR-confirmation-continuity.json'),'unchanged_whole_sentences':report['observations']['whole_sentence_bit_identical_count'],'existing_records_only':6,'quality_acceptance':False},ensure_ascii=False))
