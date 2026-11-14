#!/usr/bin/env python3
"""Source52 private two-NV candidate measurement. Strict cached mothers; no acceptance.

Run by the sole CI owner with the original certified17 tools and private cache.
Only scalar measurements/hashes leave the private runner. No CF or source edit.
"""
import argparse, ast, copy, gc, hashlib, importlib.util, json, os, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
import soundfile as sf

MAKER='23d886be9cf999eabc682159e1ab2fc2cf6c4ccb0597f32d60d5e90a34606c0e'
CONTRACT='9d133939b08a08b78cb6810028708618b92a2f2449cf56a67bd9b82506887b79'
WHOLE='5c4a2e62624ade5d119086c9525a8d90588efc7507fdbdd04678219dd8f4a156'
REQUEST='c00eb5707f1b269d2ce88fed455f592962d674d46e3bf172ba00cfe6597245f3'
WORKING='8844aaef1329e717baeebd1d6044b866304d942cd192b17283032e90d17da2c5'
OLD='2a92386d5f459ad115685d5c3904cc2cf834659f44f6b836caf0bcbc70245c24'
STATUS='d03d1af8dd06aaefe98ff33b03476ff36d5b2141bb709191825a296c2b1c0ef9'

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def arrsha(x): return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def safe(v):
    if isinstance(v,dict):return {str(k):safe(x)for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [safe(x)for x in v]
    if isinstance(v,np.integer):return int(v)
    if isinstance(v,np.bool_):return bool(v)
    if isinstance(v,(float,np.floating)):return float(v)if np.isfinite(v)else None
    return v
def read(p): return json.loads(Path(p).read_text())
def same(a,b): return json.dumps(a,sort_keys=True,ensure_ascii=False)==json.dumps(b,sort_keys=True,ensure_ascii=False)
def bare(d): return [d['title_en']]+[' '.join(re.sub(r'\*\*','',re.sub(r'\{\{.*?\}\}','',c['en'])).strip() for c in s['chunks']) for s in d['sentences']]
def functions(path,names,ns):
    tree=ast.parse(path.read_text()); nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'#unchanged-function-AST','exec'),ns)

def main():
    p=argparse.ArgumentParser()
    for name in ('tools','video-root','request-source','working-source','old-source','whole-reference','mother-contract','failure-status','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); T=a.tools.resolve(); M=a.video_root.resolve(); O=a.output.resolve()
    assert os.environ.get('XG_NOPUSH')=='1' and os.environ.get('STRICT_CACHE')=='1'
    assert not os.environ.get('VOICE') and not os.environ.get('AFFILE') and not os.environ.get('OLD_IV_VOID')
    assert sha(T/'make_video.py')==MAKER and sha(a.mother_contract)==CONTRACT and sha(a.whole_reference)==WHOLE
    for f,h in [(a.request_source,REQUEST),(a.working_source,WORKING),(a.old_source,OLD),(a.failure_status,STATUS)]: assert sha(f)==h
    request=read(a.request_source); current=read(a.working_source); old=read(a.old_source)
    assert all(str(d['no'])=='52' and len(d['sentences'])==18 for d in (old,request,current))
    assert bare(old)==bare(request)==bare(current)
    # The failed working file may contain only original G35 note wrapping and
    # original-tool nonvoice CF migration. Everything else is exactly request.
    x,y=copy.deepcopy(request),copy.deepcopy(current)
    x['核对确认']['非人声']=y['核对确认']['非人声']={}
    x['sentences'][17]['chunks'][1]['note']=y['sentences'][17]['chunks'][1]['note']='S18_G35_original_wrapping_only'
    assert same(x,y)
    rawnotes=[d['sentences'][17]['chunks'][1]['note'] for d in (request,current)]
    norm=lambda s:re.sub(r'\s+','',s).replace('▹','')
    assert norm(rawnotes[0])==norm(rawnotes[1])
    assert not current.get('结尾句',{}).get('S18')
    original_files={str(f):sha(f) for f in (a.request_source,a.working_source,a.old_source,a.whole_reference,a.mother_contract,a.failure_status)}
    whole=next(r for r in read(a.whole_reference)['cases'] if r['source_id']==52)
    mother=read(a.mother_contract); cache=M/'tts/cache_tts'; assert cache.is_dir()
    before={q.name:(q.stat().st_size,q.stat().st_mtime_ns) for q in cache.iterdir() if q.is_file()}
    model_before={n:sha(M/'tts'/n) for n in mother['models']}; assert model_before==mother['models']
    # No installation or aliasing of model cache entries. The prior reference
    # prep must already have restored every required original entry.
    for c in mother['case_evidence']:
        if c['source_id']!=52: continue
        for z in c['model_inputs']:
            assert sha(cache/z['cache_key'])==z['cache_PKL_SHA256']
            assert sha(cache/(z['cache_key']+'.单线程'))==z['single_thread_marker_SHA256']
    PR=M/'source52-two-NV-private-candidate-observer'; assert not PR.exists(), 'fresh owned private namespace required'
    W=PR/'video'; (W/'scripts').mkdir(parents=True); (PR/'tts').symlink_to(M/'tts',target_is_directory=True)
    assert (PR/'tts').resolve()==(M/'tts').resolve()
    os.environ['AUDIO_ONLY']='1'; os.environ['TMPDIR']=str(PR/'tmp'); Path(os.environ['TMPDIR']).mkdir(); tempfile.tempdir=None
    pvpath=T/'纯人声核对.py'; spec=importlib.util.spec_from_file_location('source52_original_purevoice_readonly',pvpath)
    pv=importlib.util.module_from_spec(spec); spec.loader.exec_module(pv)
    assert pv.SR==24000 and pv.F==120
    current=copy.deepcopy(request)  # original c00 request, not migrated working metadata
    candidate=copy.deepcopy(current)
    proposal={'S4':[[4.985,5.2185,'紧贴词头']],'S18':[[2.71,3.015]]}
    for sid,ivs in proposal.items():
        assert sid not in candidate.get('非人声区间',{})
        candidate.setdefault('非人声区间',{})[sid]=copy.deepcopy(ivs)
    measured_mother_pins={c['sentence']:c['actual_raw_fingerprint']for c in read(a.mother_contract)['case_evidence']if c['source_id']==52}
    assert measured_mother_pins=={'S4':'f2954ac315f1','S18':'88dadf11eead'}
    for sid in proposal:
        assert sid not in candidate.get('区间声音指纹',{})
        candidate.setdefault('区间声音指纹',{})[sid]=measured_mother_pins[sid]
    reduced=copy.deepcopy(candidate)
    for sid in proposal:
        del reduced['非人声区间'][sid]
        del reduced['区间声音指纹'][sid]
    assert same(reduced,current)
    new_math_names=set()
    report={'kind':'source52-private-two-NV-original-algorithm-measured-candidate-not-production','diagnostic_only':True,'audio_or_video_accepted':False,'source_or_confirmation_written':False,'private_PCM_models_cache_exported':False,'new_inference':False,'new_math_cache_derivation':'Only actual new S4 candidate tuple may use unchanged original_auto_level ffmpeg math; S18 one piece has no G36; every model call remains hard STRICT','maker_sha256':MAKER,'failure_status_sha256':STATUS,'request_source_sha256':REQUEST,'failed_working_source_sha256':WORKING,'old_actual_source_sha256':OLD,'whole_reference_sha256':WHOLE,'PV_program_sha256':sha(pvpath),'original_pause_program_sha256':sha(T/'标点停顿核对.py'),'original_position_program_sha256':sha(T/'停顿位置精确核对.py'),'cases':[],'observation_completed':False}
    baseline_arrays={}; baseline_pcm=None; baseline_segments=None
    oldcwd=Path.cwd(); oldpath=list(sys.path); previous_env={k:os.environ.get(k) for k in ('AUDIO_ONLY','TMPDIR')}
    def run(stage,data):
        nonlocal baseline_pcm,baseline_segments
        source=W/'scripts/52.json'; source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        os.chdir(W); sys.path[:0]=[str(T),str(W)]
        text=(T/'make_video.py').read_text().split('if __name__')[0]
        hook="    XF_OUT=float(os.environ.get('XF_OUT','0.06'))"
        hook2='    clips=[];tmap=[];t=0.0;prev=0;segs=[];pgts=[]\n'
        assert text.count(hook)==text.count(hook2)==1
        text=text.replace(hook,'    _OBS_CUTS.extend(copy.deepcopy(cuts))\n'+hook).replace(hook2,'    _OBS_W.append(w.copy())\n'+hook2,1)
        rawhook='    w=clean_tail(raw)\n'; prehook='    if sent in NONVOICE: w=_nonvoice(w,NONVOICE[sent],sent)'
        assert text.count(rawhook)==text.count(prehook)==1
        text=text.replace(rawhook,rawhook+'    _OBS_RAW.append(np.asarray(raw,np.float32).copy())\n').replace(prehook,'    _OBS_PRISTINE.append(w.copy())\n'+prehook)
        ns={'__name__':'source52_observer_'+stage,'__file__':str(T/'make_video.py'),'_OBS_CUTS':[],'_OBS_W':[],'_OBS_RAW':[],'_OBS_PRISTINE':[],'copy':copy}
        exec(compile(text,str(T/'make_video.py')+'#original-two-record-hooks','exec'),ns)
        assert ns['SENT_NO'].get(bare(data)[4])=='52'
        ns['_SPOKEN_SOURCE_NO']='52'
        # Original STRICT cache is never temporarily disabled. Existing-entry
        # SHA/marker checks stay in the original functions.
        for obj,name in [(ns['k'],'create'),(ns['KT'],'create_timed')]:
            fn=getattr(obj,name)
            def guarded(*ar,_fn=fn,**kw):
                assert os.environ.get('STRICT_CACHE')=='1', 'no model call outside STRICT'
                return _fn(*ar,**kw)
            setattr(obj,name,guarded)
        functions(T/'标点停顿核对.py',['breath_after'],ns)
        functions(T/'停顿位置精确核对.py',['logmel','dtw_map'],ns)
        functions(T/'可闻声保全核对.py',['lost_frames','check_sentence'],ns)
        ns['F5']=120
        math_records=[]; original_level=ns['_auto_level']; original_cache=ns['_CACHE']; original_repo=ns['_REPO_CACHE']
        tree=ast.parse((T/'make_video.py').read_text()); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_auto_level'); keyexpr=next(n.value for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_k'for t in n.targets))
        def candidate_level(clips,tmap,gaps,no='',rounds=2):
            assert os.environ.get('STRICT_CACHE')=='1' and str(no)=='52' and rounds==2
            key=eval(compile(ast.Expression(body=keyexpr),str(T/'make_video.py')+'#original-key-expression','eval'),ns,dict(clips=clips,tmap=tmap,gaps=gaps,no=no))
            name='调平_'+key+'.json'
            if (cache/name).is_file():return original_level(clips,tmap,gaps,no,rounds)
            sid=state['sid']; assert stage=='candidate_twoNV' and sid=='S4', 'Only actual new S4 G36 tuple may derive original math; S18 one piece has no G36'
            assert data['非人声区间'][sid]==proposal[sid] and ns['SENT_FP'][bare(data)[int(sid[1:])]]==next(c['actual_raw_fingerprint']for c in mother['case_evidence']if c['source_id']==52 and c['sentence']==sid)
            pin={'key':key,'source_id':'52','sentence':sid,'clip_SHA256':[arrsha(z)for z in clips],'clip_samples':[len(z)for z in clips],'tmap':copy.deepcopy(tmap),'gaps':list(gaps),'rounds':rounds}
            private_math=PR/('only-original-math-'+sid);private_math.mkdir(exist_ok=False);ns['_CACHE']=str(private_math);ns['_REPO_CACHE']=str(PR/'nonexistent-no-export')
            os.environ.pop('STRICT_CACHE')
            try:value=original_level(clips,tmap,gaps,no,rounds)
            finally:os.environ['STRICT_CACHE']='1';ns['_CACHE']=original_cache;ns['_REPO_CACHE']=original_repo
            q=private_math/name;assert q.is_file();stored=read(q);assert {int(k):float(v)for k,v in stored.items()}==value
            target=cache/name;assert not target.exists();target.write_bytes(q.read_bytes());new_math_names.add(name)
            assert original_level(clips,tmap,gaps,no,rounds)==value
            private_save=M/'tts/source52-two-NV-candidate-reference-cache';private_save.mkdir(exist_ok=True);saved=private_save/name
            if saved.exists():assert sha(saved)==sha(q)
            else:saved.write_bytes(q.read_bytes())
            assert sha(saved)==sha(q)
            math_records.append({'private_original_math_save_directory':str(private_save),'private_saved_filename':name,'private_saved_full_SHA256':sha(saved),'actual_original_math_input_tuple':pin,'actual_filename':name,'actual_JSON_sha256':sha(q),'actual_value':stored,'new_model_inference':False,'original_algorithm_unchanged':True})
            return value
        ns['_auto_level']=candidate_level
        state={'sid':None,'counter':0}; rec={}; observations={}; arrays={}
        orig_s=ns['sentence_audio']; orig_g=ns['句增益']; orig_t=ns['title_audio']
        def title(text):
            out=orig_t(text); arrays['title']=out.copy(); rec['title']={'samples':len(out),'pre_master_float32_sha256':arrsha(out)}; return out
        def sentence(sent,pieces,gaps):
            state['counter']+=1; sid='S'+str(state['counter']); state['sid']=sid
            assert sent==bare(data)[state['counter']]
            ns['_OBS_CUTS'].clear(); ns['_OBS_W'].clear();ns['_OBS_RAW'].clear();ns['_OBS_PRISTINE'].clear()
            clips,tm=orig_s(sent,pieces,gaps); out=np.concatenate(clips)
            rec[sid]={'before_gain_float32_sha256':arrsha(out),'before_gain_clips':[{'samples':len(z),'sha256':arrsha(z)}for z in clips],'tmap':copy.deepcopy(tm),'gaps':list(gaps),'raw_fingerprint':ns['SENT_FP'][sent],'cuts':copy.deepcopy(ns['LAST']['cuts'])}
            if sid in ('S4','S5','S18'):
                w=ns['_OBS_W'][0];last=copy.deepcopy(ns['LAST']);pristine=ns['_OBS_PRISTINE'][0];raw=ns['_OBS_RAW'][0]
                if sid in ('S4','S18'):
                    actual_case=next(c for c in mother['case_evidence']if c['source_id']==52 and c['sentence']==sid)
                    assert ns['SENT_FP'][sent]==actual_case['actual_raw_fingerprint']
                    if stage=='baseline_current':assert same(tm,actual_case['actual_processed_tmap'])and same(last['cuts'],actual_case['actual_processed_cuts'])
                obs={'pristine_w_float32_sha256':arrsha(pristine),'original_raw_array_sha256':arrsha(raw),'raw_w_float32_sha256':arrsha(w),'raw_w_samples':len(w),'LAST_head':last['head'],'LAST_hs':last['hs'],'cuts_w_samples':copy.deepcopy(ns['_OBS_CUTS']),'processed_before_gain_float32_sha256':arrsha(out),'processed_samples':len(out),'tmap':copy.deepcopy(tm),'gaps':list(gaps),'tokens':[],'punctuation':[]}
                tb,_,sp=ns['KT'].create_timed(ns['spoken'](sent),voice=ns['V'],speed=ns['SPEED'],lang='en-us',clause_pause=0,sentence_pause=0)
                toks=list(sp); mp,cost=ns['dtw_map'](ns['logmel'](np.asarray(tb,float)),ns['logmel'](np.asarray(w,float)))
                to_w=lambda t:float(np.interp(t*100,np.arange(len(mp)),mp))/100
                obs['original_logmel_DTW_cost']=cost
                for tok in toks:
                    obs['tokens'].append({'phoneme':tok.phoneme,'timed_start':float(tok.start),'timed_end':float(tok.end),'DTW_w_start':to_w(tok.start),'DTW_w_end':to_w(tok.end)})
                idx=[i for i,t in enumerate(toks)if t.phoneme in ',;:']; nosound=set(',;:.!?\"\'“”‘’()[]—–-…')
                for gi,(i,(ca,cb,*_)) in enumerate(zip(idx,last['cuts'])):
                    prv=next(z for z in reversed(toks[:i])if z.phoneme.strip()and z.phoneme not in nosound); nxt=next(z for z in toks[i+1:]if z.phoneme.strip()and z.phoneme not in nosound)
                    e=ns['_env5'](out); F=120; aa=int(tm[gi][3]*24000)//F; bb=int(tm[gi+1][2]*24000)//F
                    while aa>0 and e[aa-1]<ns['AUD_DB']: aa-=1
                    while bb<len(e)and e[bb]<ns['AUD_DB']: bb+=1
                    heard=(bb-aa)*F/24000; bg=ns['breath_after'](out,tm[gi+1][2])
                    obs['punctuation'].append({'ordinal':gi+1,'cut_w_seconds':[ca/24000,cb/24000],'prior_last_phoneme':prv.phoneme,'prior_last_phoneme_start_w':to_w(prv.start),'next_first_phoneme':nxt.phoneme,'next_first_phoneme_start_w':to_w(nxt.start),'expected_gap':gaps[gi],'actual_heard_gap':heard,'original_duration_predicate':bool(abs(heard-gaps[gi])<=.04),'original_A19_breath_after_seconds':bg,'original_A19_failed':bool(bg>=.10),'processed_silence_end_seconds':tm[gi+1][2]})
                ref5=float(np.sqrt(np.mean(w[:len(w)//120*120].reshape(-1,120)**2,axis=1)).max())
                table=[]
                # Native w coordinate (not whole/AAC clock); broad enough to
                # inspect smog coda, low-level interval and following vowel.
                regions={'S4':[(0,.16),(2.10,2.36),(4.65,5.55)],'S5':[(0,.16)],'S18':[(1.60,1.90),(2.35,3.40),(5.15,5.56)]}[sid]
                for lo,hi in regions:
                    for pos in range(int(lo*24000),min(len(w)-480,int(hi*24000)),60):
                        z=w[pos:pos+120]; c,l=pv.spec(z); q=w[max(0,pos-180):pos+300]
                        table.append({'w_seconds':pos/24000,'relative_dB_2p5ms':float(20*np.log10(np.sqrt(np.mean(w[pos:pos+60]**2))/(ref5+1e-12)+1e-12)),'relative_dB_5ms':float(20*np.log10(np.sqrt(np.mean(z**2))/(ref5+1e-12)+1e-12)),'relative_dB_10ms':float(20*np.log10(np.sqrt(np.mean(w[pos:pos+240]**2))/(ref5+1e-12)+1e-12)),'centroid_Hz_5ms':c,'below150Hz_energy_dB_5ms':l,'periodicity_20ms':pv.per(q),'zero_crossing_rate_5ms':float(np.mean(np.signbit(z[1:])!=np.signbit(z[:-1]))),'pristine_relative_dB_5ms':float(20*np.log10(np.sqrt(np.mean(pristine[pos:pos+120]**2))/(ref5+1e-12)+1e-12))})
                obs['local_original_PV_spectrum_energy_table']=table
                allowed=[(round(float(iv[0])*24000),round(float(iv[1])*24000))for iv in data.get('非人声区间',{}).get(sid,[])]
                obs['private_candidate_only_NV']=proposal.get(sid,[])if stage=='candidate_twoNV'else[]
                obs['original_audible_preservation_failures']=ns['check_sentence'](sid,raw,out,last['head'],last['segs'],allowed,last['toks'],last['scale'],int(round(-last['segs'][0][2]*24000)))
                if sid in proposal:
                    changed=ns['_nonvoice'](pristine,proposal[sid],sent);mask=np.zeros(len(pristine),bool);endpoints=[]
                    for iv in proposal[sid]:
                        i,j=round(iv[0]*24000),round(iv[1]*24000);mask[i:j]=True
                        lv=lambda q:float(20*np.log10(np.sqrt(np.mean(q**2))/(ref5+1e-12)+1e-12))
                        endpoints.append({'candidate_w_interval':iv,'sample_interval':[i,j],'outside_adjacent5ms_dB':[lv(pristine[i-120:i]),lv(pristine[j:j+120])],'max_original_interval_5ms_dB':float(ns['_env5'](pristine)[i//120:j//120].max()),'right_endpoint_zero_cross_or_small_sample':bool(pristine[j-1]*pristine[j]<=0 or abs(pristine[j])<=1e-4),'all_original_samples_outside_interval_exact':bool(np.array_equal(pristine[~mask],changed[~mask]))})
                    obs['original_NV_guard_on_pristine_passed']=True;obs['pristine_NV_endpoint_measurements']=endpoints
                    obs['only_declared_NV_samples_changed_in_direct_original_NV_operation']=bool(np.array_equal(pristine[~mask],changed[~mask]))
                    # Explicit edge regions are measured identically, no claim
                    # that DTW token duration alone identifies a breath.
                    edges={'S4':[(4.70,4.985),(5.2185,5.55)],'S18':[(2.55,2.71),(3.015,3.30)]}[sid]
                    obs['protected_word_edge_direct_NV_identity']=[{'w_interval':[lo,hi],'pristine_sha256':arrsha(pristine[round(lo*24000):round(hi*24000)]),'after_NV_sha256':arrsha(changed[round(lo*24000):round(hi*24000)]),'exact':bool(np.array_equal(pristine[round(lo*24000):round(hi*24000)],changed[round(lo*24000):round(hi*24000)]))}for lo,hi in edges]
                F5=120;loud=int(np.argmax(np.sqrt(np.mean(out[:len(out)//F5*F5].reshape(-1,F5)**2,axis=1))))*F5
                badout=out.copy();badout[loud:loud+F5]=0
                obs['original_audible_preservation_loud5ms_zero_negative_rows']=ns['check_sentence'](sid+'-negative',raw,badout,last['head'],last['segs'],allowed,last['toks'],last['scale'],int(round(-last['segs'][0][2]*24000)))
                observations[sid]=obs
            return clips,tm
        def gain(d,no,si,sent,pieces,gaps,clips,tm,out):
            result=orig_g(d,no,si,sent,pieces,gaps,clips,tm,out); z=result[1]; sid=state['sid']; arrays[sid]=z.copy(); rec[sid].update(samples=len(z),pre_master_float32_sha256=arrsha(z),automatic_level=result[2],manual_segment_level=result[3]); return result
        ns['title_audio']=title; ns['sentence_audio']=sentence; ns['句增益']=gain
        out=PR/(stage+'.m4a'); ns['build'](str(source),str(out)); wp=W/'work_52/a.wav'; rawsha=sha(wp); md5=hashlib.md5(wp.read_bytes()).hexdigest()[:12]
        ac=hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(out),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest()
        expected=whole['candidate']
        if stage=='baseline_current':
            assert rawsha==expected['raw_WAV_sha256']and ac==expected['AAC_ADTS_sha256']and md5=='83aba46b585d','baseline must exactly match the actual failed current full track'
        else:assert rawsha!=expected['raw_WAV_sha256'] and ac!=expected['AAC_ADTS_sha256']
        samples,sr=sf.read(wp,dtype='float64'); assert sr==24000
        segments=read(W/'work_52/分段.json'); gr=read(W/'work_52/词尾除阻.json'); fp=md5; rows=[]
        for f in pv.scan(samples):
            k=pv.key(f); cf=data.get('核对确认',{}).get('非人声',{}).get(k)
            g=next((z for z in gr if f[0]in('孤立杂音','噗声','呼吸声')and z['开始']-.005<=f[1]and f[2]<=z['结束']+.005),None)
            matched=isinstance(cf,dict)and cf.get('配音指纹')==fp
            accepted,why=pv.确认可收('52',f,cf,samples)if matched else(False,'missing key or current voice fingerprint mismatch')
            if g: accepted=True; why='original A21 graft interval'
            sid=next((sid for sid,r in segments.items()if r[0]['时刻'][0]-.06<=f[1]<=r[-1]['时刻'][1]+.06),None)
            rows.append({'tuple':list(f),'key':k,'actual_measurement':pv.实测(f),'sentence':sid,'source_confirmation':cf,'fingerprint_matches':matched,'original_confirmation_accepted':bool(accepted),'original_reason':why,'original_looks_like_breath':bool(pv.像吸气(f)),'original_graft_evidence':g})
        result={'stage':stage,'whole_WAV_sha256':rawsha,'whole_WAV_md5_first12':md5,'whole_AAC_ADTS_sha256':ac,'whole_bound_to_actual436437_diagnostic':stage=='baseline_current','actual_new_candidate_identity_not_guessed':stage=='candidate_twoNV','private_phase_source_sha256':sha(source),'baseline_phase_is_original_request_c00':stage=='baseline_current','candidate_source_is_exact_c00_plus_two_NV_and_two_new_mother_data_pins':stage=='candidate_twoNV','original_auto_level_new_candidate_math_records':math_records,'sentence_records':rec,'actual_segment_clock':segments,'purevoice_scan_events':rows,'PV_unconfirmed_count':sum(not z['original_confirmation_accepted']for z in rows),'new_mother_observations':observations,'master_pre_peak':max(float(np.abs(z).max())for z in arrays.values())}
        if stage=='baseline_current':assert result['master_pre_peak']==expected['master_pre_peak']
        if stage=='baseline_current':
            baseline_arrays.update(arrays); baseline_pcm=samples; baseline_segments=segments
        else:
            comparisons={}
            for sid,z in arrays.items():
                oz=baseline_arrays[sid]; item={'same_samples':len(oz)==len(z),'pre_master_array_equal':bool(np.array_equal(oz,z)),'old_sha256':arrsha(oz),'new_sha256':arrsha(z)}
                if sid=='title': comparisons[sid]=item; continue
                orng=baseline_segments[sid]; nrng=segments[sid]; old_start=round(orng[0]['时刻'][0]*24000); new_start=round(nrng[0]['时刻'][0]*24000)
                old_end=round(orng[-1]['时刻'][1]*24000); new_end=round(nrng[-1]['时刻'][1]*24000)
                ozq=baseline_pcm[old_start:old_end]; nzq=samples[new_start:new_end]
                item['whole_sentence_quantized_PCM_equal']=bool(np.array_equal(ozq,nzq)); item['old_quantized_float64_sha256']=arrsha(ozq); item['new_quantized_float64_sha256']=arrsha(nzq)
                item['old_fullclock_seconds']=[old_start/24000,old_end/24000];item['new_fullclock_seconds']=[new_start/24000,new_end/24000]
                item['plus_minus40ms_boundary_PCM_equal']=bool(np.array_equal(baseline_pcm[max(0,old_start-960):old_end+960],samples[max(0,new_start-960):new_end+960]))
                if sid not in ('S4','S18'): assert item['pre_master_array_equal']and item['whole_sentence_quantized_PCM_equal']and item['plus_minus40ms_boundary_PCM_equal']
                comparisons[sid]=item
            result['old_to_current_actual_sentence_PCM_identity']=comparisons
            crops=[]
            for row in rows:
                sid=row['sentence']; f=row['tuple']
                if not sid: continue
                ns0=segments[sid][0]['时刻'][0]; os0=baseline_segments[sid][0]['时刻'][0]; n0=max(0,round((f[1]-.04)*24000));n1=min(len(samples),round((f[2]+.04)*24000));o0=round(n0+(os0-ns0)*24000);o1=round(n1+(os0-ns0)*24000)
                crops.append({'event_key':row['key'],'sentence':sid,'clock_correct_native_sample_windows':{'old':[o0,o1],'current':[n0,n1]},'exact_samples':bool(np.array_equal(baseline_pcm[o0:o1],samples[n0:n1])),'old_sha256':arrsha(baseline_pcm[o0:o1]),'current_sha256':arrsha(samples[n0:n1]),'old_confirmation_reuse_prohibited':sid in('S4','S18')})
            result['PV_event_context_plus_minus40ms_exact_comparisons']=crops
        result['source_effective_control_delta_from_original_c00']={'only_two_NV_candidate_leaves':proposal if stage=='candidate_twoNV'else{},'new_measured_mother_data_pins':measured_mother_pins if stage=='candidate_twoNV'else{},'mother_pins_are_new_actual9d133_not_old_CF_renewal':True,'all_other_source_fields_deep_exact':True,'production_source_changed':False}
        result['actual_original_display_chunk_timetable']= (W/'work_52/list.txt').read_text()
        try:
            def mod(name,path):
                sp=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(sp);sys.modules[name]=v;sp.loader.exec_module(v);return v
            RR=mod('source52_private_original_R_'+stage,T/'响度一致性核对.py');RR.FF='ffmpeg';Q=mod('source52_private_original_Q8_'+stage,T/'音频体检.py')
            pcm=RR.pcm(str(out));moment=RR.momentary(str(out));metrics=Q.指标(pcm,'52');qb=[];qb=Q.超限(metrics,read(T/'音频体检基准.json'),Q.确认('52'),qb)
            with tempfile.TemporaryDirectory(prefix='source52-private-original-R-')as td:
                alias=Path(td)/'52.mp4';alias.symlink_to(out);I,sg,levels,rbad,summary=RR.check(str(alias),pcm)
            inside=RR.句内(str(out),pcm,moment,str(W/'work_52/分段.json'));ibad=RR.句内报(inside)
            result['original_fulltrack_Q8_R_withinR']={'completed':True,'Q8_metrics':metrics,'Q8_failures':qb,'integrated_LUFS':I,'R_sentence_levels':levels,'R_failures':rbad,'R_summary':summary,'within_R_comparisons':inside,'within_R_failures':ibad,'original_thresholds_unchanged':True,'all_passed':not qb and not rbad and not ibad,'ASR_not_run_here':True}
        except BaseException as exc:result['original_fulltrack_Q8_R_withinR']={'completed':False,'error':{'type':type(exc).__name__,'detail':str(exc)},'not_accepted':True}
        report['cases'].append(result)
        # Only owned diagnostic media are deleted; original caches/source stay.
        wp.unlink();out.unlink(); del arrays,ns;gc.collect()
    try:
        run('baseline_current',current);run('candidate_twoNV',candidate);report['observation_completed']=True
    except BaseException as exc:
        report['error']={'type':type(exc).__name__,'detail':str(exc)}; raise
    finally:
        os.chdir(oldcwd);sys.path[:]=oldpath
        after={q.name:(q.stat().st_size,q.stat().st_mtime_ns)for q in cache.iterdir()if q.is_file()}
        report['all_existing_private_cache_stats_unchanged']=all(after.get(k)==v for k,v in before.items());report['new_cache_files']=sorted(set(after)-set(before));report['only_original_math_new_cache_files']=set(report['new_cache_files'])==new_math_names;report['models_byte_exact_after']={n:sha(M/'tts'/n)for n in mother['models']}==model_before;report['input_files_byte_exact_after']=all(sha(Path(k))==v for k,v in original_files.items())
        report['source_or_confirmation_written']=False
        assert report['all_existing_private_cache_stats_unchanged']and report['only_original_math_new_cache_files']and report['models_byte_exact_after']and report['input_files_byte_exact_after']
        O.parent.mkdir(parents=True,exist_ok=True);O.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'diagnostic_only':True,'observation_completed':report['observation_completed'],'output':str(O),'sha256':sha(O)},ensure_ascii=False))
if __name__=='__main__': main()
