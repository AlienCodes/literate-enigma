"""Pinned original raw/timed cache provenance in memory; emit scalars only."""
from pathlib import Path
import subprocess,pickle,json,hashlib
import numpy as np
B=Path('/workspace/work/video-audit70-20261113');O=B/'audio51-remaining-edits';R=Path('/workspace/work/github-publication/target');PIN='64621068034f8b6e09836a6d97210a0e9b2f1ed6'
p=json.loads((B/'ci-direct-43526354790-51/51-checker-reference-preparation.json').read_text())
rows=[]
for lab in ['S2','S4','S10','S12','S18']:
 row=next(r for r in p['reference_calls'] if r['sentence']==lab and r['reference_kind']=='whole-default-raw')
 key=row['exact_native_cache_key'];path='视频/配音缓存/'+key
 raw=subprocess.check_output(['git','cat-file','blob',PIN+':'+path],cwd=R)
 marker=subprocess.check_output(['git','cat-file','blob',PIN+':'+path+'.单线程'],cwd=R).decode().strip()
 h=hashlib.sha256(raw).hexdigest();assert marker==h[:16]
 a,sr=pickle.loads(raw);assert type(a) is np.ndarray and a.dtype==np.float32 and a.ndim==1 and sr==24000
 out={'sentence':lab,'exact_native_key_from_actual_preparation':key,'repository_commit':PIN,'repository_path':path,'pkl_full_sha256':h,'native_marker':marker,'marker_matches_full_original_cache_bytes':True,'schema':{'container':'tuple2','dtype':str(a.dtype),'shape':list(a.shape),'sample_rate':sr,'raw_array_sha256':hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()},'no_waveform_bytes_exported':True}
 if lab=='S4':
  tr=next(r for r in p['reference_calls'] if r['sentence']==lab and r['reference_kind']=='whole-default-timed');tb=subprocess.check_output(['git','cat-file','blob',PIN+':视频/配音缓存/'+tr['exact_native_cache_key']],cwd=R);v=pickle.loads(tb);sc=len(a)/len(v[0])
  out['word_label_correction_context']={'source_unchanged_English':row['source_slice'],'timed_cache_key':tr['exact_native_cache_key'],'timed_cache_full_sha256':hashlib.sha256(tb).hexdigest(),'timed_phonemes_near_raw_2_0_to_3_5s':[{'phoneme':t.phoneme,'start':t.start*sc,'end':t.end*sc} for t in v[2] if 2<t.start*sc<3.5],'interpretation':'thirty-nine followed by a Boston; old basis word ordinance is misplaced in this sentence. Timed phonemes label words only and are not a cut/pass criterion.'}
 rows.append(out)
report={'purpose':'Pinned original create mother cache hashes for comparison to upcoming native full per-key manifest; diagnostic only','quality_acceptance':False,'native_individual_full_hash_match_not_yet_claimed':True,'records':rows}
(O/'51-original-mother-cache-scalar-bindings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'records':[{k:r[k] for k in ['sentence','exact_native_key_from_actual_preparation','pkl_full_sha256']} for r in rows]}))
