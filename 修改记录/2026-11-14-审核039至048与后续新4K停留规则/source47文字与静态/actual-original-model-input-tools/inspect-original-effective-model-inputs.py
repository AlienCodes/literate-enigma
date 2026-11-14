"""Read-only input trace; tokenizer only, never TTS/waveform/render/cache writes."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,re,subprocess,sys
import numpy as np
B=Path('/workspace/work/video-audit70-20261113');O=Path(__file__).resolve().parent
FROZEN=Path('/workspace/work/video-official-ready41-core3-frozen-20261114/.github/video-revision-batch')
REQUEST=FROZEN/'request/14/视频/脚本/14.json';FILES=B/'next-passed-native/43543967031/14/artifact-files'
s=importlib.util.spec_from_file_location('original_readonly',B/'audio65-69-source-readonly/replay_original_sources.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
sha=lambda z:hashlib.sha256(z).hexdigest();canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
render=(r.m.T/'render.py').read_text();rt={'re':re};exec(compile(ast.Module(body=[n for n in ast.parse(render).body if isinstance(n,ast.FunctionDef)and n.name=='strip_gloss'],type_ignores=[]),'original-strip_gloss','exec'),rt)
def plain(x):return re.sub(r'\*\*','',rt['strip_gloss'](x)).strip()
controls=['非人声区间','停顿删除区间','停顿插入点','词尾除阻','停顿处除阻','除阻加强','结尾句','列举逗号','合成标点','分段增益dB','段内渐变dB','句子增益dB']
registry_fields=['区间声音指纹',*controls]

def source_inputs(path):
 raw=Path(path).read_bytes();d=json.loads(raw);bare=[' '.join(plain(c['en'])for c in s['chunks'])for s in d['sentences']]
 context=[]
 for p in sorted((FROZEN/'context/视频/脚本').glob('*.json')):
  x=json.loads(p.read_text())
  for key in registry_fields:
   for label,value in x.get(key,{}).items():
    if label=='标题':
     if x['title_en']==d['title_en']:context.append({'file':str(p.relative_to(FROZEN)),'field':key,'label':label,'keyed_title':x['title_en'],'value':value})
    elif re.fullmatch(r'S\d+',str(label)):
     t=' '.join(plain(c['en'])for c in x['sentences'][int(label[1:])-1]['chunks'])
     if t in bare:context.append({'file':str(p.relative_to(FROZEN)),'field':key,'label':label,'keyed_sentence':t,'value':value})
 # Same frozen crossarticle registries, with the selected article taking precedence.
 synth={}
 for row in context:
  if row['field']=='合成标点':synth[(row['file'],row['label'])]=(row['keyed_sentence'],[tuple(z)for z in row['value']])
 for label,items in d.get('合成标点',{}).items():synth[('target-final.json',label)]=(bare[int(label[1:])-1],[tuple(z)for z in items])
 rows=[];plans=[]
 def capture_input(n,text,speed,method,label,role):
  def capture(text,voice,speed,lang,**kw):
   mid=r.m.models['kokoro-v1.0.onnx'if method=='create'else'kokoro-v1.0-timed.onnx'];vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest();key=hashlib.sha1(repr((method,mid,text,vh,float(speed),lang,sorted(kw.items()))).encode()).hexdigest()+'.pkl'
   z={'sentence':label,'role':role,'method':method,'speed':float(speed),'lang':lang,'kw':kw,'effective_input_text':text,'effective_input_sha256':sha(text.encode()),'expected_exact_cache_key':key,'voice_array_sha1':vh,'model_identifier':mid};plans.append(z);return z
  n['SYNTH_PUNCT']=synth;n['_SP_CACHE']={};kw={'clause_pause':0,'sentence_pause':0}if method=='create_timed'else{}
  return n['_pron'](capture)(n['spoken'](text),voice=n['V'],speed=speed,lang='en-us',**kw)
 n,_=r.scope(d,1,Path('/nonexistent-read-only-cache-placeholder'))
 titlebare=plain(d['title_en']);titleplan=capture_input(n,titlebare,.95,'create','标题','producer-title-raw')
 for i,(s,t)in enumerate(zip(d['sentences'],bare),1):
  label='S'+str(i);n,_=r.scope(d,i,Path('/nonexistent-read-only-cache-placeholder'));n['SYNTH_PUNCT']=synth;n['_SP_CACHE']={};lst=n['list_commas'](t);punc=[{'character':m.group(),'character_index':m.start(),'base_gap_s':.2 if m.start()in lst else .4}for m in re.finditer(r'[,;:](?=\s)',t)]
  lead=.4 if i==1 else .3+(.2 if s['para']!=d['sentences'][i-2]['para']else 0)
  e=d.get('结尾句',{}).get(label)
  if not e:speeds=[('whole-default',.95,t)]
  elif '整句语速'in e:speeds=[('ending-whole',float(e['整句语速']),t)]
  else:speeds=[('ending-front',float(e['前段语速']),n['_ending_front'](t)if e.get('前段单独合成')else t),('ending-slow',float(e['最后一段语速']),t)]
  for role,speed,txt in speeds:
   for method in ['create','create_timed']:capture_input(n,txt,speed,method,label,'producer-'+role)
  rows.append({'sentence':label,'paragraph':s['para'],'lead_s':lead,'cleaned_whole_English':t,'spoken_whole_English':n['spoken'](t),'base_punctuation':punc,'effective_ending_final_gap_s':float(e['最后一段前停顿'])if e and '最后一段前停顿'in e else None,'source_DSP':{key:copy.deepcopy(d.get(key,{}).get(label))for key in controls},'interval_validity_fp':d.get('区间声音指纹',{}).get(label),'cleaned_chunks':[plain(c['en'])for c in s['chunks']]})
 # Raw donor material is an actual waveform dependency whenever the source graft asks for it.
 kinds=sorted({v[1]for z in d.get('词尾除阻',{}).values()for v in z.values()}|{v[2]for z in d.get('停顿处除阻',{}).values()for v in z.values()})
 for k in kinds:
  txt,_=n['DONOR'][k];capture_input(n,txt,.95,'create','供体','producer-donor-'+k)
 semantic={'article_no':d['no'],'title_audio_cleaned':titlebare,'title_audio_spoken':n['spoken'](titlebare),'sentence_rows':rows,'waveform_control_top_level':{key:d.get(key)for key in controls},'title_DSP':{key:d.get(key,{}).get('标题')for key in ['非人声区间','词尾除阻','除阻加强']},'model_input_plans':plans,'timing_constants_s':{'initial_silence':.4,'title_after':.6,'first_lead':.4,'sentence_hold':.7,'nonfirst_lead':.3,'new_paragraph_extra':.2,'comma':.4,'list_comma':.2,'post_voice_total':2.0},'global_normalization_peak':.89,'sample_rate':24000,'default_speed':.95,'S12_and_other_legacy_DSP_conditions':'14<26: no automatic gain; 14<46: no new tail gain guard','cross_article_matching_audio_registries':context}
 return {'source_file':str(path),'source_file_sha256':sha(raw),'audio_semantics_sha256':sha(canonical(semantic)),'audio_semantics':semantic}

if __name__=='__main__':
 baseline=source_inputs(REQUEST);oldactual=source_inputs(FILES/'14-actual-working-source.json');prep=json.loads((FILES/'14-checker-reference-preparation.json').read_text());nativecalls=prep['reference_calls'];matches=[]
 for z in baseline['audio_semantics']['model_input_plans']:
  if z['role']=='producer-donor-t':continue
  found=[c for c in nativecalls if c['exact_native_cache_key']==z['expected_exact_cache_key']]
  matches.append({'sentence':z['sentence'],'role':z['role'],'method':z['method'],'expected_exact_cache_key':z['expected_exact_cache_key'],'actual_native_reference_key_observed':bool(found),'input_sha_matches_actual':any(c['cache_input_text_sha256']==z['effective_input_sha256']for c in found),'note':'Ending-specific speed mothers are not enumerated in this checker prep JSON; no bytes synthesized or cache inferred.'if not found else 'actual native key+effective text SHA both compared'})
 # These are actual semantic differences, e.g. formal interval fp recording, not new waveform controls.
 def diff(a,b,p=''):
  if type(a)!=type(b):return [{'path':p,'before':a,'after':b}]
  if isinstance(a,dict):return sum([diff(a.get(k),b.get(k),p+'/'+str(k))for k in sorted(set(a)|set(b))],[])
  if isinstance(a,list):
   if len(a)!=len(b):return [{'path':p,'before':a,'after':b}]
   return sum([diff(v,w,p+'/'+str(i))for i,(v,w)in enumerate(zip(a,b))],[])
  return []if a==b else[{'path':p,'before':a,'after':b}]
 report={'kind':'article14-frozen-passed-original-audio-input-baseline-readonly','quality_acceptance_new_source':False,'awaiting_parent_stable_new_source_hash':True,'original_maker_sha256':sha(r.m.source.encode()),'render_strip_gloss_program_sha256':sha(render.encode()),'actual_original_pipeline':'strip_gloss removes {{...}}, then ** removal and trim per chunk, join with single spaces, spoken numeric/quote normalization, synth punctuation map, original pronunciation/context wrapper, fixed raw/timed model+voice/speed, unchanged DSP, para lead gaps, whole normalization and original AF/AAC','baseline_request':baseline,'baseline_actual_working':oldactual,'request_to_actual_audio_semantic_differences':diff(baseline['audio_semantics'],oldactual['audio_semantics']),'actual_native_preparation_effective_input_crosschecks':matches,'actual_native_model_sha256':prep['models_sha256'],'actual_native_voice_file_sha256':prep['fixed_voice_sha256'],'runtime_core_manifest_sha256':sha((FROZEN/'certified-core/manifest.json').read_bytes()),'runtime_context_manifest_sha256':sha((FROZEN/'context/manifest.json').read_bytes()),'original_AF_text_sha256':sha(r.AF.encode()),'original_AF':r.AF,'no_TTS_no_audio_video_generation_no_cache_read_or_write_no_source_or_program_mutation':True,'display_fields_not_passed_to_waveform':['chunks.zh','chunks.align','chunks.note','bold emphasis after ** stripping','inline gloss {{...}}','title_zh','title_fx','font_size_en','font_size_zh','术语','核对确认'],'caution':'chunk boundaries can affect visual/highlight reference checks; original body waveform is synthesized per cleaned whole sentence. Runtime tools/dictionaries must remain the frozen version; actual new MP4 AAC packet identity is still needed after authorized rendering.'}
 out=O/'14-frozen-audio-input-baseline-v1.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('REPORT',out,'SHA',sha(out.read_bytes()),'diffs',json.dumps(report['request_to_actual_audio_semantic_differences'],ensure_ascii=False))
