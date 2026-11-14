#!/usr/bin/env python3
"""Diagnostic original recognizers on fifteen actual source60 sentence crops; no acceptance or confirmation write."""
import argparse,hashlib,json,re,runpy,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--tools',type=Path,required=True);p.add_argument('--video',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
r={'article':'60','diagnostic_only':True,'quality_acceptance':False,'automatic_confirmation':False,'human_listening_claimed':False,'private_PCM_GT_cache_models_exported':False,'program_sha256':sha(__file__),'sentences':[]}
try:
 import numpy as np
 import soundfile as sf
 from scipy.signal import resample_poly
 source=a.work/'scripts/60.json';raw=a.work/'work_60/a.wav';meta=a.work/'work_60/分段.json'
 assert sha(raw)=='92062a16c220534fa9c167f12c0660e2c161a317bfe949f993aaaa86b70ffe4c'
 audio=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(a.video),'-map','0:a:0','-c:a','copy','-f','adts','-']);assert hashlib.sha256(audio).hexdigest()=='4dc642494a287329c27d72973254dc11d108797c853a9073790b9cf35cc5c489'
 doc=json.loads(source.read_text());segments=json.loads(meta.read_text());x,sr=sf.read(raw);assert x.ndim==1
 program=a.tools/'机器复听.py';original=runpy.run_path(str(program),run_name='original_source60_readonly_diagnostic');recognizers=original['识别器']();assert set(recognizers)==set(original['路名'])=={'small.en','parakeet'}
 r.update(actual_source_sha256=sha(source),actual_raw_WAV_sha256=sha(raw),actual_video_sha256=sha(a.video),actual_AAC_ADTS_sha256=hashlib.sha256(audio).hexdigest(),actual_segment_metadata_sha256=sha(meta),original_ASR_program_sha256=sha(program))
 for label in [f'S{i}' for i in range(1,16)]:
  pieces=segments[label];lo,hi=float(pieces[0]['时刻'][0]),float(pieces[-1]['时刻'][1]);ref=' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en'])for c in doc['sentences'][int(label[1:])-1]['chunks']);crop=x[int(lo*sr):int(hi*sr)];x16=resample_poly(crop,16000,sr).astype(np.float32)if sr!=16000 else crop.astype(np.float32);merged=[];transcripts,differences=original['各路'](recognizers,ref,x16,merged)
  r['sentences'].append({'sentence':label,'native_seconds':[lo,hi],'reference_text':ref,'original_input_float32_16k_sha256':hashlib.sha256(x16.tobytes()).hexdigest(),'original_input_sample_count':len(x16),'full_transcripts_by_original_recognizer':transcripts,'original_comparison_differences':differences,'original_merged_word_observations':merged})
 r['all_fifteen_original_two_route_texts_collected']=len(r['sentences'])==15
except BaseException as exc:r['diagnostic_error']={'type':type(exc).__name__,'detail':str(exc).replace(str(a.work),'<private-work>').replace(str(a.tools),'<tools>')[:800]}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'article':'60','diagnostic_only':True,'collected_sentence_count':len(r['sentences']),'diagnostic_error':r.get('diagnostic_error')},ensure_ascii=False))
