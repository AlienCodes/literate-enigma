"""Quantify encoded filter/codec propagation already observed in candidate QC."""
from pathlib import Path
import json,tempfile,copy,numpy as np,soundfile as sf
OUT=Path('/workspace/work/dolly62-audio-user-review-20261114')
defs=OUT/'private_full_candidate_original_qc.py'
exec(compile(defs.read_text().split('\nreport={')[0],str(defs)+'#definitions-only','exec'))
proof=json.loads((OUT/'private-full-candidate-original-QC.json').read_text())
def compare(a,c):
 a=np.asarray(a,float);c=np.asarray(c,float);delta=c-a
 energy=float(np.sum(a*a));err=float(np.sum(delta*delta))
 return {'sample_count':len(a),'different_sample_count':int(np.sum(a!=c)),'max_abs_difference':float(np.max(np.abs(delta)))if len(a)else 0,'difference_rms_dbfs':rmsdb(delta),'baseline_rms_dbfs':rmsdb(a),'SNR_db':float(10*np.log10(energy/err))if err and energy else None,'waveform_NCC':float(np.corrcoef(a,c)[0,1])if energy and len(a)>1 else None,'all_samples_equal':bool(np.array_equal(a,c))}
with tempfile.TemporaryDirectory(prefix='private62-codec-locality-',dir='/dev/shm')as td:
 td=Path(td);cache=td/'cache';cache.mkdir()
 source=copy.deepcopy(d);source['停顿插入点']['S15']['2'][0]=3.584083
 wave,parts=r.build(source,cache);wav=td/'62.wav';sf.write(wav,wave,24000)
 assert sha(wav.read_bytes())==proof['candidate_identity']['WAV_sha256']
 aac=td/'62.m4a';run([r.FF,'-y','-v','error','-nostdin','-i',str(wav),'-af',r.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)])
 assert sha(adts(aac))==proof['candidate_identity']['AAC_ADTS_sha256']
 actual=decode(mp);candidate=decode(aac);assert len(actual)==len(candidate)
 spans={
 'target_boundary_and_pause_window':[113.38,113.90],
 'subsequent_four_from_her_cell_line_control':[113.90,115.13],
 'late_codec_propagation_tail':[114.30,114.93],
 'all_audio_before_changed_codec_support':[0,113.408],
 'all_audio_after_changed_codec_support':[114.92266666666667,len(actual)/48000],
 }
 comparisons={name:{'public_clock_s':[lo,hi],**compare(actual[round(lo*48000):round(hi*48000)],candidate[round(lo*48000):round(hi*48000)])}for name,(lo,hi)in spans.items()}
 both=np.ones(len(actual),bool);both[round(113.38*48000):round(113.90*48000)]=False
 comparisons['all_samples_outside_actual_target_PCM_junction_plus_context']=compare(actual[both],candidate[both])
 output={'kind':'private-full62-native-codec-locality-measurement-addendum','candidate_WAV_sha256':sha(wav.read_bytes()),'candidate_AAC_sha256':sha(adts(aac)),'comparison_sample_rate':48000,'baseline_video_sha256':sha(mp.read_bytes()),'codec_propagation_does_not_mean_source_PCM_outside_window_changed':True,'actual_AF_and_AAC_difference_support_s':proof['codec_preservation']['public_decoded_change_support_s'],'comparisons':comparisons,'no_source_or_program_or_approved_media_change':True,'no_new_TTS':True,'private_PCM_AAC_cache_not_exported':True,'native_ASR_still_required':True}
 (OUT/'private-full-candidate-codec-locality-addendum.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(output,ensure_ascii=False))
