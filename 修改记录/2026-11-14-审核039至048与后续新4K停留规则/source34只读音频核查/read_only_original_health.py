from pathlib import Path
import sys,json,hashlib,importlib.util,subprocess
OUT=Path('/workspace/work/tetris34-audio-user-review-20261114');T=Path('/workspace/work/audit-repo/视频/工具')
sys.path.insert(0,str(T));p=T/'音频体检.py';spec=importlib.util.spec_from_file_location('original34health',p);Q=importlib.util.module_from_spec(spec);spec.loader.exec_module(Q)
mp=Path('/workspace/work/video-audit70-20261113/next-passed-native/43533004625/34/34-4K-正文后插图2秒-简述2秒.mp4');sp=Path('/workspace/work/video-revision-delivery/next-passed-validated/43533004625/34/final-source/视频/脚本/34.json');d=json.loads(sp.read_text())
import re
texts=[d['title_en']]+[' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en'])for c in s['chunks'])for s in d['sentences']]
Q.文本=lambda no:texts
base=json.loads((T/'音频体检基准.json').read_text());a=Q.读(str(mp));m=Q.指标(a,'34');notes=[];bad=Q.超限(m,base,d.get('核对确认',{}).get('句首突起',{}),notes)
R=Q.R;tm=R.momentary(str(mp));spans=Q.句段(a);groups={f'S{i}':[{'时刻':[st/R.SR,en/R.SR]}]for i,(st,en)in enumerate(spans[1:],1)}
seg=OUT/'actual-public34-original-segments.json';seg.write_text(json.dumps(groups,ensure_ascii=False,indent=2)+'\n')
inside=R.句内(str(mp),a,tm,str(seg));ib=R.句内报(inside)
report={'kind':'readonly-actual34-original-full-track-audio-health-and-level-check','video_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'original_health_program_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'original_R_program_sha256':hashlib.sha256(Path(R.__file__).read_bytes()).hexdigest(),'original_health_baseline_sha256':hashlib.sha256((T/'音频体检基准.json').read_bytes()).hexdigest(),'actual_English_text_source_sha256':hashlib.sha256(sp.read_bytes()).hexdigest(),'actual_title_plus_sentence_count':len(texts),'actual_silence_detected_segment_count':len(spans),'all_original_health_metrics':m,'original_health_failures':bad,'original_confirmation_notes':notes,'original_within_sentence_adjacent_comparisons':inside,'original_within_sentence_level_failures':ib,'passed_original_measured_health_and_levels':not bad and not ib,'no_source_audio_or_program_change':True,'no_human_listening_claim':True}
(OUT/'actual-full-track-original-health-and-levels.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
