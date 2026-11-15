from pathlib import Path
O=Path(__file__).parent;s=(O/'replay52_actual.py').read_text();prefix=s[:s.index(';assert sha(src)')];exec(compile(prefix,'original52-readonly-setup','exec'));import copy,datetime
q=json.loads(src.read_text());out=[]
for g in [0,1.25,1.5,2.0]:
 cand=copy.deepcopy(q)
 if g:cand['分段增益dB']={'S1':{'2':g},'S5':{'1':g}}
 for si,bi,ph in [(1,2,'d'),(5,1,'k')]:
  ns,t=r.scope(cand,si,cache);pieces=[];gaps=[];p0=0;listed=ns['list_commas'](t)
  for mt in re.finditer(r'[,;:](?=\s)',t):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start()in listed else .4)
  pieces.append((p0,len(t)));clips,tmap=ns['sentence_audio'](t,pieces,gaps);before=np.concatenate(clips);P=sum(len(c)for c in clips[:2*bi-1]);clips,vo,agn,pgn=ns['句增益'](cand,cand['no'],si-1,t,pieces,gaps,clips,tmap,before)
  def calc(a):
   import scipy.signal as ss
   ref=float(np.sqrt(np.mean(a[:len(a)//120*120].astype(float).reshape(-1,120)**2,1)).max());hp=ss.sosfiltfilt(ns['HP'],a.astype(float));z=ns['release'](a,hp,P,ref,deep=ph in 'tkp');extra=None if z is None else{'centroid_Hz':ns['centroid'](a,*z[3]),'periodicity':ns['periodicity'](a,*z[3]),'below800_peak_dB':ns['lf_peak'](a,*z[3])};return {'release_metrics':z,'original_rule_disposition':'voiced_stop_info_not_judged'if ph in 'dbɡg'else('passed'if ns['judge'](a,z,ph)else'not_passed'),'double_release':ns['双爆破'](a,hp,z,ref)if ph in'tkp'else None,'spectrum':extra}
  out.append({'sentence':'S'+str(si),'piece':bi,'manual_gain':g,'phoneme':ph,'original_auto_gain':agn,'official_original_A21_pre_G36_view':calc(before),'additional_post_effective_gain_supplement':calc(vo),'supplement_does_not_relabel_historical_native_result':True,'original_S5_51ms_plus3_boost_preserved':cand.get('除阻加强',{}).get('S'+str(si))})
p=O/'52-original-A21-formal-view-and-postgain-supplement-v2.json';p.write_text(json.dumps({'kind':'source52-exact-original-A21-rule-applicability-and-postgain-gain-candidate-comparison','source_id':'52','frozen_book_order':'41','original_A21_source_sha256':sha(Path('/workspace/work/audit-repo/视频/工具/词尾辅音核对.py')),'rows':out,'old_scratch_generic_judge_is_not_formal_for_voiced_d':True,'no_tool_threshold_CF_source_TTS_native_changes':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2,default=lambda x:float(x))+'\n');print(json.dumps({'path':str(p),'sha256':sha(p),'rows':out},ensure_ascii=False))
