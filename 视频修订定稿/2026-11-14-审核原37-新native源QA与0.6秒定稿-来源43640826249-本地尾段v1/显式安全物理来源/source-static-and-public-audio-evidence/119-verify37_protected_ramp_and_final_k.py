from pathlib import Path
O=Path(__file__).parent;s=(O/'replay37_actual.py').read_text();prefix=s[:s.index(';assert sha(src)')];exec(compile(prefix,'original37-readonly-setup','exec'));import copy,datetime
base=json.loads(src.read_text());out=[]
for label,inc in [('current',None),('minimal_candidate',{'S10':{'1':1.0},'S13':{'1':.75}})]:
 d=copy.deepcopy(base)
 if inc:d['分段增益dB']=inc
 ns,t=r.scope(d,13,cache);pieces=[];gaps=[];p0=0;lst=ns['list_commas'](t)
 for mt in re.finditer(r'[,;:](?=\s)',t):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start()in lst else .4)
 pieces.append((p0,len(t)));clips,tmap=ns['sentence_audio'](t,pieces,gaps);pre=np.concatenate(clips);clips,v,agn,pgn=ns['句增益'](d,d['no'],12,t,pieces,gaps,clips,tmap,pre);ns['test_ph']='k';z=r.m.measure(ns,v,len(v));last=clips[-1];out.append({'case':label,'first_piece_manual_gain':None if inc is None else .75,'S13_original_ramp5':d['段内渐变dB']['S13']['5'],'S13_original_final_graft':d['词尾除阻']['S13'],'S13_final_piece_pre_normalized_float32_sha256':hashlib.sha256(np.ascontiguousarray(last,np.float32).tobytes()).hexdigest(),'S13_aftergain_final_k_original_A21':z})
assert out[0]['S13_final_piece_pre_normalized_float32_sha256']==out[1]['S13_final_piece_pre_normalized_float32_sha256'];assert out[0]['S13_aftergain_final_k_original_A21']==out[1]['S13_aftergain_final_k_original_A21'];p=O/'37-original-postgain-final-k-and-protected-ramp-comparison.json';p.write_text(json.dumps({'kind':'source37-user129130-original-postgain-protected-S13-ramp-final-k','rows':out,'final_piece_waveform_and_A21_metrics_exact':True,'target_first_piece_endphonemes_are_s_not_plosives':True,'no_source_or_checker_or_new_TTS_changes':True},ensure_ascii=False,indent=2,default=lambda z:float(z))+'\n');print(json.dumps({'path':str(p),'sha256':sha(p),'rows':out},ensure_ascii=False))
