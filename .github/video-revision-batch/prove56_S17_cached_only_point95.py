"""Bounded source56 S17 cached equivalence only; not GT, TTS, whole production or QA."""
from pathlib import Path
import argparse,ast,copy,gc,hashlib,importlib.util,json,os,sys,traceback
sys.dont_write_bytecode=True
NO='56';SENTENCE='Wallace never named the theory after himself.'
MAKER='1b87c1d4d1685bdd59325587184cca35f853354a015e6fe89c11f150cd2a6239'
CERT='c05b6ed258dc9783bdb453f1e7382dac8b40d27f66ac30c26b3ee079c3933c19'
STAMP='9aa653ec47c686d9bb0b6c4393444bb50c3c8d2d249fe10a843b0959854f7ea6'
def require(ok,msg):
    if not ok:raise AssertionError(msg)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def typed(x):
    if isinstance(x,dict):return ('dict',tuple((k,typed(v))for k,v in x.items()))
    if isinstance(x,list):return ('list',tuple(typed(v)for v in x))
    return(type(x).__name__,x)
def validate_sources(before,after,ending):
    require(str(before['no'])==str(after['no'])==NO and len(before['sentences'])==len(after['sentences'])==17,'Wrong finite source56 shape')
    require('结尾句'not in before and typed(after['结尾句'])==typed({'S17':ending}),'Only exact approved new ending role')
    inv=copy.deepcopy(after);del inv['结尾句'];require(typed(inv)==typed(before),'Only allowed S17 transparent ending field may differ')
    require(typed(ending)==typed({'整句语速':.95}),'Only the exact original whole-sentence .95 one-field transparent metadata is authorized')
def compare_results(a,b):
    for k in ['raw','timed','native_tokens','normalized_tokens','raw_fingerprint','clips','tmap','postprocessed','automatic_gain','manual_gain','last_head_cuts']:
        require(typed(a[k])==typed(b[k]),'S17 cached raw/timed/labels/complete postprocessing changed: '+k)
    return True

def main():
    p=argparse.ArgumentParser()
    for k in ['tools','video-root','task','before','request','contract','output']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();report={'source_id':NO,'book_order':65,'bounded_sentence':'S17','cached_equivalence_passed':False,'quality_acceptance':False,'whole_native_or_4K_quality_acceptance':False,'no_new_TTS_or_math_authorized':True,'forbidden_model_events':[],'errors':[],'restoration':{},'phases':{}}
    old_inventory=None;observer=None;M=a.video_root.resolve();W=M/'video';T=a.tools.resolve();cache=M/'tts/cache_tts';actual_a=W/'work_56/a.wav';actual_a_before=digest(actual_a)if actual_a.exists()else None;output=a.output.resolve()
    try:
        require(not output.is_relative_to(M),'Public scalar output must remain outside private machine')
        c=json.loads(a.contract.read_text());require(c['source_id']==NO and c['book_order']==65,'Wrong bounded contract')
        for name,path in [('helper',Path(__file__)),('before',a.before),('request',a.request),('certificate',a.task/'actual-spoken22-certification.json'),('observer',a.task/'original56_whole_observer.py'),('support',a.task/'original56_mother_scope_support.py')]:
            require(digest(path)==c['file_SHA256'][name],'Wrong bounded pin: '+name)
        require(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER and digest(T/'新管/快测通过.json')==STAMP and digest(a.task/'actual-spoken22-certification.json')==CERT,'Exact actual22 programs/certificate/stamp required')
        require({k:digest(M/'tts'/k)for k in c['actual_model_SHA256']}==c['actual_model_SHA256'] and digest(M/'tts/voice_mb.npy')==c['actual_voice_SHA256'],'Actual unchanged model and voice files required')
        require(digest(M/'tts/AF.txt')==c['actual_original_AF_SHA256'],'Original complete-track AF input differs')
        require(all(os.environ.get(k)=='1'for k in ['STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']),'Exact formal strict modes required')
        require(not any(os.environ.get(k)for k in ['OLD_IV_VOID','VOICE','AFFILE']),'Unapproved source invalidation/voice/filter override')
        data=[json.loads(a.before.read_text()),json.loads(a.request.read_text())];ending=c['ending'];validate_sources(data[0],data[1],ending)
        observer=load('_actual_original56_whole_observer_for_bounded_functions',a.task/'original56_whole_observer.py');support=load('_actual_original56_cache_scope',a.task/'original56_mother_scope_support.py');require(observer.SOURCE_NO==support.SOURCE_NO==NO and observer.MAKER_SHA256==MAKER and observer.CERTIFICATE_SHA256==CERT,'Wrong unmodified whole/support functions')
        mathfile=cache/'调平_22842078959011da4b6986b549453b7eafee80d9.json';require(digest(mathfile)=='98c2e92f9fe36307e60e0a857a97d5595015278b2add1fed2bcea10248eb43d6','Only already restored strict original S11 math is permitted')
        old_inventory=observer.inventory(cache);used={}
        with support.environment_and_cwd(W,report['restoration']):
            for label,src,path in [('before',data[0],a.before),('transparent',data[1],a.request)]:
                with support.source_namespace(W,path.read_bytes(),report['restoration']):
                    for name in ('render','title2','clean','出片指纹'):sys.modules.pop(name,None)
                    name='_source56_S17_original_'+label;spec=importlib.util.spec_from_file_location(name,W/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[name]=m;restore=None
                    try:
                        spec.loader.exec_module(m);m._SPOKEN_SOURCE_NO=NO;np=m.np
                        require(Path(m._CACHE).resolve()==cache,'Wrong actual original cache path')
                        require(m.SPEED==.95 and m._OLDF and digest(m._OLDF)==observer.OLD_REGISTRY_SHA256 and digest(m._CTX_PATH)==observer.CTX_SHA256 and digest(m._cand)==observer.DICT_SHA256,'Wrong actual source/model/dictionary/default speed inputs')
                        require(str(m.SENT_NO.get(SENTENCE))==NO,'Exact S17 own-source context required')
                        require(digest(T/'环境/模型校验码.json')==digest(W/'环境/模型校验码.json')==observer.REGISTRY_SHA256,'Original portable model registry differs')
                        m._REPO_CACHE=str(M/'forbid-S17-proof-public-cache-export');require(not Path(m._REPO_CACHE).exists(),'Forbidden public cache export role already exists')
                        restore=observer.block_native(m,support,report['forbidden_model_events']);row={'cached_model_calls':0};spoken=m.spoken(SENTENCE)
                        for method,obj,model in [('create',m.k,'kokoro-v1.0.onnx'),('create_timed',m.KT,'kokoro-v1.0-timed.onnx')]:
                            guarded=observer.strict_cached_guard(m,np,cache,method,model,getattr(obj,method),used,row)
                            def finite(text,voice,speed=1.,lang='en-us',_method=method,_guard=guarded,**kw):
                                require(text==spoken and type(speed)in (float,int)and float(speed)==.95 and lang=='en-us','Only exact existing S17 .95 input allowed')
                                require(kw==({}if _method=='create'else{'clause_pause':0,'sentence_pause':0}),'Unexpected original S17 call kwargs')
                                return _guard(text,voice=voice,speed=speed,lang=lang,**kw)
                            setattr(obj,method,finite)
                        def forbid_math(*x,**y):raise AssertionError('No S17 G36 mathematics is authorized')
                        m._auto_level=forbid_math
                        text=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(x['en'])).strip()for x in src['sentences'][-1]['chunks']);require(text==SENTENCE and not list(m._speech_marks(text)),'Wrong exact S17 or unexpected punctuation')
                        require(typed(m.ENDING.get(text))==typed(None if label=='before'else ending),'Actual source-first ENDING binding differs')
                        raw,_=m.k.create(spoken,voice=m.V,speed=.95,lang='en-us');raw=np.asarray(raw,np.float32);tb,_,ts=m.KT.create_timed(spoken,voice=m.V,speed=.95,lang='en-us',clause_pause=0,sentence_pause=0);sc=len(raw)/len(tb)
                        array=lambda z:{'samples':len(z),'dtype':str(np.asarray(z).dtype),'sha256':hashlib.sha256(np.ascontiguousarray(z).tobytes()).hexdigest()}
                        normalized=[(t.phoneme,float(t.start*sc),float(t.end*sc))for t in ts];native=[(t.phoneme,float(t.start),float(t.end))for t in ts]
                        if label=='transparent':
                            require(np.array_equal(raw,m._ending_raw(text,ending)),'Original whole-speed raw branch differs')
                            require(typed(normalized)==typed([(t.phoneme,float(t.start),float(t.end))for t in m._ending_toks(text,ending)]),'Original whole-speed token mapping differs')
                        clips,tmap=m.sentence_audio(text,[(0,len(text))],[]);clips,processed,agn,pgn=m.句增益(src,NO,16,text,[(0,len(text))],[],clips,tmap,np.concatenate(clips))
                        result={'raw':array(raw),'timed':array(tb),'native_tokens':{'count':len(native),'sha256':hashlib.sha256(json.dumps(native,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()},'normalized_tokens':{'count':len(normalized),'sha256':hashlib.sha256(json.dumps(normalized,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()},'raw_fingerprint':m.SENT_FP[text],'clips':[array(x)for x in clips],'tmap':tmap,'postprocessed':array(processed),'automatic_gain':agn,'manual_gain':pgn,'last_head_cuts':{'head':m.LAST['head'],'cuts':m.LAST['cuts']},'cached_model_calls':row['cached_model_calls']}
                        require(result['postprocessed']['sha256']==c['actual_previous_selected_S17_pre_master_SHA256'],'S17 processed samples do not match the actual previous selected whole report')
                        report['phases'][label]=result
                    finally:
                        if restore is not None:restore()
                        sys.modules.pop(name,None);del m;gc.collect()
        compare_results(report['phases']['before'],report['phases']['transparent']);require(not report['forbidden_model_events'],'Forbidden native inference attempted');report['actual_used_existing_cache_entries']=list(used.values());report['actual_primary_whole_identity_still_required']=c['required_formal_whole_identity'];report['cached_equivalence_passed']=True
    except BaseException as e:
        report['errors'].append({'type':type(e).__name__,'message':str(e)});traceback.print_exc()
    finally:
        report['original_private_cache_full_inventory_before_after_exact']=old_inventory is not None and observer.inventory(cache)==old_inventory
        report['actual_normal_a_wav_absence_or_hash_restored']=(digest(actual_a)if actual_a.exists()else None)==actual_a_before
        report['normal_a_wav_before']=actual_a_before
        report['cached_equivalence_passed']=bool(report['cached_equivalence_passed']and report['original_private_cache_full_inventory_before_after_exact']and report['actual_normal_a_wav_absence_or_hash_restored']and all(report['restoration'].get(k)is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored']))
        output.parent.mkdir(parents=True,exist_ok=True);require(not output.exists(),'Never overwrite a prior proof');output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return 0 if report['cached_equivalence_passed']else 1
if __name__=='__main__':sys.exit(main())
