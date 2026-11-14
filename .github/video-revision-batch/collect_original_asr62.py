#!/usr/bin/env python3
"""Readonly current62 whole-S15 and original pieces2-4/piece3 dual-ASR evidence.

This is never a quality verdict, never renews a confirmation, and exports no
private PCM. Both models and the comparison are the unchanged official program.
"""
import argparse,hashlib,json,os,re,runpy
from pathlib import Path
EXPECTED_WAV='c5330026dbc9f81d0c7546a1716b9dade9960f44311862a5feb3e4aa0749d7c3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--tools',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 report={'article':'62','sentence':'S15','kind':'actual-current62-original-dual-ASR-three-contexts','diagnostic_only':True,'acceptance':False,'automatic_confirmation_or_renewal':False,'private_PCM_GT_or_cache_exported':False,'native_run_id':os.environ.get('GITHUB_RUN_ID'),'native_HEAD':os.environ.get('GITHUB_SHA')}
 try:
  import numpy as np,soundfile as sf
  from scipy.signal import resample_poly
  source=a.work/'scripts/62.json';wav=a.work/'work_62/a.wav';seg=a.work/'work_62/分段.json';assert sha(wav)==EXPECTED_WAV
  data=json.loads(source.read_text());assert str(data['no'])=='62' and data['停顿插入点']['S15']['2']==[3.584083,'交界']
  rows=json.loads(seg.read_text())['S15'];assert len(rows)==5
  text=' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en']).strip()for c in data['sentences'][14]['chunks'])
  pieces=[];prev=0
  for m in re.finditer(r'[,;:](?=\s)',text):pieces.append(text[prev:m.end()].strip());prev=m.end()+1
  pieces.append(text[prev:].strip());assert len(pieces)==5
  program=a.tools/'机器复听.py';original=runpy.run_path(str(program),run_name='actual62_readonly_ASR_diagnostic')
  rec=original['识别器']();assert set(rec)==set(original['路名'])=={'small.en','parakeet'}
  x,sr=sf.read(wav);assert x.ndim==1 and sr==24000
  report.update(source_sha256=sha(source),actual_raw_WAV_sha256=sha(wav),actual_raw_md5_first12=hashlib.md5(wav.read_bytes()).hexdigest()[:12],original_ASR_program_sha256=sha(program),actual_segmentation_sha256=sha(seg),all_original_piece_references=pieces)
  out=[]
  for label,indices in [('whole-S15',[0,1,2,3,4]),('pieces2-4',[1,2,3]),('piece3-four-insertion',[2])]:
   lo=float(rows[indices[0]]['时刻'][0]);hi=float(rows[indices[-1]]['时刻'][1]);assert 0<=lo<hi<len(x)/sr
   crop=x[int(lo*sr):int(hi*sr)];y=resample_poly(crop,16000,sr).astype(np.float32);reference=' '.join(pieces[i]for i in indices);merged=[]
   transcripts,differences=original['各路'](rec,reference,y,merged)
   out.append({'context':label,'original_piece_numbers':[i+1 for i in indices],'actual_native_seconds':[lo,hi],'reference_text':reference,'sample_rate':16000,'sample_count':len(y),'input_float32_sample_sha256':hashlib.sha256(y.tobytes()).hexdigest(),'full_transcripts_by_original_recognizer':transcripts,'original_comparison_differences':differences,'original_merged_word_observations':merged})
  report['actual_original_dual_ASR_contexts']=out
 except (Exception,SystemExit)as e:
  report['diagnostic_error']={'type':type(e).__name__,'message':str(e).replace(str(a.work),'<private-work>').replace(str(a.tools),'<original-tools>')[:1200]}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'article':'62','diagnostic_only':True,'actual_three_dual_contexts_collected':len(report.get('actual_original_dual_ASR_contexts',[]))==3,'diagnostic_error':report.get('diagnostic_error')},ensure_ascii=False))
if __name__=='__main__':main()
