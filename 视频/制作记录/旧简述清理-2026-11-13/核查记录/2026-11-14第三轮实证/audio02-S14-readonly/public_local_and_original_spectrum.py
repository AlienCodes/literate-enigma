import pathlib,json,hashlib,subprocess,importlib.util,ast,contextlib,io,numpy as np
from scipy import signal
from PIL import Image,ImageDraw
B=pathlib.Path(__file__).parent;spec=importlib.util.spec_from_file_location('unchanged_original_S14',B/'reconstruct_original_S14.py');m=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(m)
code=pathlib.Path('/workspace/work/video-audit70-20261113/audio07-original-post-readonly/public-original-code/纯人声核对.py').read_text();ns={'np':np,'SR':24000};exec(compile(ast.Module(body=[x for x in ast.parse(code).body if isinstance(x,ast.FunctionDef) and x.name in ('per','spec')],type_ignores=[]),'original_purevoice_numeric_functions','exec'),ns)
def decode(p,sr):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-map','0:a:0','-vn','-ac','1','-ar',str(sr),'-f','f32le','-']),np.float32).astype(float)
a24=decode(B/'02-accepted-public.mp4',24000);b24=decode(B/'02-current-failed-public.mp4',24000);rows=[];start=114.72
for lo,hi in [(.35,.75),(1.1,1.4),(2.4,2.8),(3.6,4.0)]:
 t=m.a[round(lo*24000):round(hi*24000)].astype(float);p=round((start+lo)*24000);pad=2400;search=a24[p-pad:round((start+hi)*24000)+pad];c=signal.correlate(search,t,'valid',method='fft');j=int(np.argmax(c));x=search[j:j+len(t)];g=float(t@x/(t@t+1e-30));rows.append({'original_sentence_span':[lo,hi],'independent_public_minus_producer_seconds':(j-pad)/24000,'NCC':float(t@x/(np.linalg.norm(t)*np.linalg.norm(x)+1e-30)),'fitted_gain':g})
clock=float(np.median([x['independent_public_minus_producer_seconds'] for x in rows]));pred_start=m.segmap[0]['producer_start_s']+clock;pred_end=start+len(m.a)/24000+clock
original_spec=[]
for lo,hi in [(4.14,4.19),(4.183958,4.195),(4.195,4.27),(4.27,4.28)]:
 x=m.w[round(lo*24000):round(hi*24000)].astype(float);centroid,lf=ns['spec'](x);periods=[ns['per'](m.w[p:p+480].astype(float)) for p in range(round(lo*24000),max(round(lo*24000)+1,round(hi*24000)-480),60)];original_spec.append({'w_interval_s':[lo,hi],'original_spec_magnitude_centroid_Hz':centroid,'original_spec_low150_fraction_dB':lf,'original_per_median_20ms':float(np.median(periods)),'relative_RMS_dB':float(20*np.log10(np.sqrt(np.mean(x*x))/(m.ref+1e-30)+1e-30))})
public=[]
for lo,hi in [(118.8,118.97),(pred_start,pred_end),(119.00,119.07),(119.08,119.5)]:
 x=a24[round(lo*24000):round(hi*24000)];y=b24[round(lo*24000):round(hi*24000)];public.append({'public_interval_s':[lo,hi],'accepted_RMS_dBFS':float(20*np.log10(np.sqrt(np.mean(x*x))+1e-30)),'current_RMS_dBFS':float(20*np.log10(np.sqrt(np.mean(y*y))+1e-30)),'sample_count':len(x),'np_array_equal':bool(np.array_equal(x,y)),'accepted_SHA256_float64':hashlib.sha256(x.tobytes()).hexdigest(),'current_SHA256_float64':hashlib.sha256(y.tobytes()).hexdigest()})
# Public excerpts and visualization only; never serialize cached mother PCM.
clips=[]
for name,file in [('accepted','02-accepted-public.mp4'),('current','02-current-failed-public.mp4')]:
 p=B/f'02-S14-{name}-public-word-context.wav';subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-ss','118.4','-i',str(B/file),'-t','1.1','-map','0:a:0','-vn','-c:a','pcm_s16le',str(p)],check=True);clips.append({'file':p.name,'source_MP4_SHA256':hashlib.sha256((B/file).read_bytes()).hexdigest(),'start_s':118.4,'duration_s':1.1,'public_MP4_derived':True,'SHA256':hashlib.sha256(p.read_bytes()).hexdigest()})
im=Image.new('RGB',(1200,420),'white');dr=ImageDraw.Draw(im);lo,hi=118.7,119.25
for val,col in [(a24,'#666666'),(b24,'#d22d33')]:
 pts=[]
 for st in np.arange(lo,hi,.0025):
  x=val[round(st*24000):round((st+.005)*24000)];db=20*np.log10(np.sqrt(np.mean(x*x))+1e-30);pts.append((70+(st-lo)/(hi-lo)*1060,350-(max(-100,min(-20,db))+100)/80*270))
 dr.line(pts,fill=col,width=2)
for x in [pred_start,pred_end]:
 xx=70+(x-lo)/(hi-lo)*1060;dr.line((xx,65,xx,350),fill='#2266bb',width=2)
dr.text((30,10),'02 actual public audio: accepted gray / current red; 5ms RMS',fill='black');dr.text((30,30),f'Blue: independently mapped original deletion {pred_start:.6f}--{pred_end:.6f}s',fill='black');dr.text((70,370),str(lo),fill='black');dr.text((1090,370),str(hi),fill='black');image=B/'02-S14-actual-public-waveform.png';im.save(image)
r={'kind':'02-direct-public-word-window-and-original-official-spectrum','quality_acceptance':False,'original_to_accepted_public_clock_independent_matches':rows,'mapped_public_minus_producer_clock_seconds':clock,'predicted_public_changed_word_tail_interval_s':[pred_start,pred_end],'actual_public_window_measurements':public,'unchanged_original_purevoice_numeric_code_SHA256':hashlib.sha256(code.encode()).hexdigest(),'original_spec_per_raw_mother_scalar_frames':original_spec,'original_mother_arrays_not_exported':True,'public_MP4_derived_clips':clips,'public_only_waveform_figure':image.name,'public_figure_SHA256':hashlib.sha256(image.read_bytes()).hexdigest()};(B/'02-public-word-window-and-raw-spectrum-proof.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'clock_s':clock,'mapped_deleted_interval':[pred_start,pred_end],'public':public,'officialrawspec':original_spec},ensure_ascii=False))
