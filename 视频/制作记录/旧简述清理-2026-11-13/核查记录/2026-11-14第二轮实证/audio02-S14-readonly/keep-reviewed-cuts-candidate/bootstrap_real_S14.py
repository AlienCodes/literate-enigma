"""Development namespace fixture: real G72 S14 + original PV/to_w functions.
Not a full dossier/model/official-QC execution. No raw arrays leave this process.
"""
import json,sys,os,pathlib,importlib.util,ast,hashlib,contextlib,io
import numpy as np
B=pathlib.Path('/workspace/work/video-audit70-20261113/audio02-S14-readonly');BASE=pathlib.Path('/workspace/work/audit-repo/视频/工具')
def trace(tool,args,**extra):
 p=pathlib.Path(os.environ['ROUTING_FIXTURE_TRACE']);
 with p.open('a') as f:f.write(json.dumps({'tool':tool,'args':args,**extra},ensure_ascii=False)+'\n')
def namespace(no,write):
 spec=importlib.util.spec_from_file_location('original_cached_funcs',B.parent/'audio-a21-15-17-18-30-readonly/reproduce_a21_cache_only.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 data=json.loads(pathlib.Path(f'scripts/{no}.json').read_text());ns,text=m.scope_for(data,14);raw,_=ns['k'].create(ns['spoken'](text),voice=ns['V'],speed=ns['SPEED'],lang='en-us');w0=ns['clean_tail'](raw);out,ends,tmap,last=m.sentence(ns,text)
 pvcode=(BASE/'纯人声核对.py').read_text();pvn={'np':np,'SR':24000,'F':120}
 exec(compile(ast.Module(body=[n for n in ast.parse(pvcode).body if isinstance(n,ast.FunctionDef) and n.name in ('spec','per','segments','scan')],type_ignores=[]),'unchanged_original_PV_functions','exec'),pvn)
 dossier=(BASE/'疑点清单.py').read_text();exec(compile(ast.Module(body=[n for n in ast.parse(dossier).body if isinstance(n,ast.FunctionDef) and n.name in ('to_w','spec','per')],type_ignores=[]),'unchanged_original_dossier_functions','exec'),ns)
 off=round(114.72*24000);it={'si':14,'off':off,'n':len(out),'w0':w0,'segs':last['segs'],'toks':last['toks'],'scale':last['scale'],'head':last['head']}
 gain=json.loads((B.parent/'ready41-monitor/02-artifact/02-reference-gain-diagnostic.json').read_text())['default_audit_gain']
 q=np.floor(out.astype(float)*gain*32768)/32768
 cands=[{'kind':x[0],'t0':x[1]+off/24000,'t1':x[2]+off/24000,'db':x[3],'c':x[4],'per':x[5],'lo':x[6]} for x in pvn['scan'](q)]
 if os.environ.get('ROUTING_CANDIDATE_KIND')=='voiced-negative':
  F=120;env=np.sqrt(np.mean(w0[:len(w0)//F*F].reshape(-1,F)**2,axis=1));pos=int(np.argmax(env))*F;hit=None
  for a,b,t,rm in it['segs']:
   if a<=pos<b:
    v=pos-a;v-=sum(min(v,y)-x for x,y in rm if x<v);hit=t+v/24000;break
  assert hit is not None
  cands=[{'kind':'explicit-real-voiced-negative-fixture','t0':off/24000+hit,'t1':off/24000+hit+.015,'db':0,'c':0,'per':0,'lo':0}]
 trace('自动切点.py',[no]+(['--写入'] if write else []),namespace_fixture='real-original-S14-only-no-full-QC',actual_candidate_count=len(cands),candidate_kind=os.environ.get('ROUTING_CANDIDATE_KIND','actual-PV-scan'),raw_mother_SHA=[r['pkl_full_sha256'] for r in m.cache_rows.values()])
 ns.update({'no':no,'outdir':'.','F5':120,'cands':cands,'info':[it],'WRITE':write,'np':np,'json':json,'os':os,'sys':sys,'SR':24000})
 return ns
