"""Scalar-only original-cache S15 junction tradeoff; no exported private audio."""
from pathlib import Path
import json, hashlib, tempfile, copy
import numpy as np
OUT=Path('/workspace/work/dolly62-audio-user-review-20261114')
path=OUT/'inspect_actual_junction.py'
exec(compile(path.read_text().split('\nwith tempfile.TemporaryDirectory')[0],str(path)+'#definitions-only','exec'))
original_cut=3.580083
with tempfile.TemporaryDirectory(prefix='private62-tradeoff-',dir='/dev/shm') as td:
 cache=Path(td)/'cache';cache.mkdir()
 sc,txt,baseline,tm,agn=build_one(d,cache)
 raw,_=sc['k'].create(sc['spoken'](txt),voice=sc['V'],speed=sc['SPEED'],lang='en-us');mother=sc['clean_tail'](raw)
 assert hashlib.sha256(baseline.tobytes()).hexdigest()==part['pre_normalized_array_SHA256']
 # Bind clean-mother samples to their unchanged original source samples on each side.
 # A42 only inserts zeros and uses an 8 ms cosine ramp; the .4 s block does not delete samples.
 # Relative processed offsets include the earlier comma handling and sentence-head cleanup.
 def mapped(x,ct,pos,lo,hi):
  ci=round(pos*fs);start=round(lo*fs);stop=round(hi*fs)
  before=x[round(ct[1][3]*fs)-(ci-start):round(ct[1][3]*fs)-(ci-min(stop,ci))] if start<ci else np.empty(0,np.float32)
  after=x[round(ct[2][2]*fs)+max(0,start-ci):round(ct[2][2]*fs)+(stop-ci)] if stop>ci else np.empty(0,np.float32)
  out=np.concatenate([before,after]); assert len(out)==stop-start,(pos,lo,hi,len(out),stop-start)
  return out
 # Feature windows are acoustic observations, not model labels: the timed model
 # drifts here and puts /f/ too late. Bound native raw spectrum places /f/ around these spans.
 windows={'high_frequency_z_tail_candidate':[3.575,3.5875],
          'f_fricative_observed':[3.5875,3.5975],
          'f_core_conservative':[3.590,3.595],
          'four_vowel_onset':[3.600,3.625]}
 rows=[]
 for pos in [3.580083,3.5825,3.584083,3.585,3.587667]:
  dd=copy.deepcopy(d);dd['停顿插入点']['S15']['2']=[pos,'交界'];ss,tt,x,ct,ag=build_one(dd,cache)
  row={'cut_clean_mother_s':pos,'automatic_level_unchanged':ag==agn,'sentence_samples_unchanged':len(x)==len(baseline),'windows':{}}
  for name,(lo,hi) in windows.items():
   v=mapped(x,ct,pos,lo,hi);b=mapped(baseline,tm,original_cut,lo,hi)
   row['windows'][name]={'clean_mother_span_s':[lo,hi],'candidate_rms_dbfs_pre_normalization':rmsdb(v),'delta_vs_actual_native_db':rmsdb(v)-rmsdb(b),'every_sample_equal_to_original':np.array_equal(v,b)}
  lo=pos;hi=3.5875
  # Residual high-frequency tail incorrectly following pause is only inferred
  # through spectral transition; its exact articulatory boundary is not ground truth.
  v=mapped(x,ct,pos,lo,hi) if hi>lo else np.empty(0,np.float32)
  row['possible_z_residue_after_pause']={'duration_ms':max(0,hi-lo)*1000,'energy_sample_sum':float(np.sum(v.astype(float)**2)), 'rms_dbfs_pre_normalization':rmsdb(v) if len(v) else None}
  row['source_control_leaf_only']='停顿插入点.S15.2[0]'
  rows.append(row)
 out={'kind':'private-original-function-local-cutpoint-tradeoff-scalar-only','actual_original_binding_passed':True,'video_sha256':bind['accepted_actual_mp4_sha256'] if 'accepted_actual_mp4_sha256' in bind else '76ed237782d65e7bd19fd1c14891b55fd6b7014a43f7562f4d2faaf471a8b8af','sample_rate':fs,'original_native_cut_s':original_cut,'positions_tested':rows,'bound_actual_raw_timed_model_disagrees_with_acoustic_f_start':True,'phonetic_windows_are_spectral_estimates_not_human_verified_transcription':True,'private_mother_PCM_cache_not_exported':True,'new_TTS':False,'formal_source_or_accepted_media_modified':False}
 (OUT/'S15-private-cutpoint-tradeoff.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(rows,ensure_ascii=False,indent=2))
