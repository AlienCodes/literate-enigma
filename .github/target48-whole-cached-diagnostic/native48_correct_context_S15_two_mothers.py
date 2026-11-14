"""Root9085: only the two missing correct-context S15 mothers, then real levels.

Source0193 and all other voice entries stay unchanged. Only scalar evidence is
public; the two original private mothers/markers and one G36 entry remain private.
"""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, math, os, sys, tempfile, traceback
sys.dont_write_bytecode = True
P = argparse.ArgumentParser()
for key in ('tools','video-root','request','missing-witness','root-decision',
            'previous-cache-identity','output','cache-path-output'):
    P.add_argument('--'+key, type=Path, required=True)
a = P.parse_args()
T, M = a.tools.resolve(), a.video_root.resolve()
W, C = M/'video', M/'tts/cache_tts'
SOURCE = '0193cbd1859525690e12a470c517cce2f120a1054b204fcfa3c0c392c92abbd7'
MAKER = '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
DECISION = '9085c1e96739cc3bcc9c62b060ad645dd8516291a688a06c6a4770b9df5be30c'
WITNESS = '5ae376ceca2a8b77051632b54aaaa1712fe336f3fafd31edeae7ac026f32e0bb'
DICT = '5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
CTX = '4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
OLDREG = '91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
PREVIOUS = 'c6cb359c94df07c51a19fa3e9c7863751dfd15c47bd7f860a889fcce16b02c88'
RAWKEY = '586bd56cd87532d8969be74dde574dc5ef09a448.pkl'
PLAIN_INPUT = 'ce441f0cdd60bde03e9829ad7e04a2cf1b2e40a1cab98430fb455e63ddb466fa'
CORE = {'草稿声音.sh':'43fc6a1acdae6bb1c2252178bf034407400bbbe92eb1752053f3047da9760491',
        '句内响度.py':'9c5691cf59dc7776e822461044e50031ff118de29d7ae0769781a1cc66664bea',
        '独立复核/synth.py':'a0c9cad9ac953e68768470e8181f7e325c8ee8ff08ca57b68bbd136b99b83264',
        '结尾句接点.py':'1a5d43c4f5483014b69bbea7ad43dddb0333a9a80e29bb2b4c8029d8915ff798',
        '读音核对.py':'50f4363bb2fc2930be59904cdccfa44fd46f14393a0385c7846028ee25b4e84c',
        '新管/回归基准_27.json':'b8ddb4656ae27cbfc7ec8e3b99511983b4e568997bd4ad4ee33c364f3926ae94',
        '新管/快测通过.json':'bb75875985ff106abe142caf7ecbf0a5eb76a1412309bf78d77bf146f64512af'}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def inventory():return {p.name:sha(p) for p in C.iterdir() if p.is_file()}

assert sha(a.request)==SOURCE and sha(a.root_decision)==DECISION
assert sha(a.missing_witness)==WITNESS and sha(a.previous_cache_identity)==PREVIOUS
assert not os.environ.get('STRICT_CACHE'), 'Only authorized new S15 entries may be missing.'
assert os.environ.get('XG_NOPUSH')=='1' and not os.environ.get('OLD_IV_VOID')
assert not os.environ.get('VOICE') and not os.environ.get('AFFILE')
for flag in ('XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS'):
    assert os.environ.get(flag)=='1'
assert Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent.resolve()
assert sha(T/'发音词典/读音改正.json')==DICT and sha(T/'发音词典/按语境读音.json')==CTX
assert {key:sha(T/key) for key in CORE}==CORE
assert sha(W/'make_video.py')==sha(T/'make_video.py')==MAKER
witness=json.loads(a.missing_witness.read_text())
assert witness['source_request_sha256']==SOURCE and witness['baseline_current_request_sha256']=='4f146ce6a70bb0bf5d2c6e1f6b47bd6a2bcc2f311be7a948092d7bde1a08f449'
assert witness['errors']==[{'type':'AssertionError','detail':'STRICT_CACHED_PORTABLE_KEY_MISSING '+RAWKEY}]
assert len(witness['phases']['baseline_current4f']['observed_sentences'])==17
assert list(witness['phases']['selected_new0193']['observed_sentences'])==['S'+str(i)for i in range(1,15)]
assert witness['phases']['baseline_current4f']['original_old_cache_registry_sha256']==OLDREG
prior=json.loads(a.previous_cache_identity.read_text())
oldfive=prior['all_five_restored_files_require_actual_fullSHA_readback']
assert {key:sha(C/key)for key in oldfive}==oldfive
assert {name:sha(M/'tts'/name)for name in prior['original_models_fullSHA']}==prior['original_models_fullSHA']
assert sha(M/'tts/voice_mb.npy')==prior['original_voice_sha256']
before=inventory()
before_pcm={str(p):sha(p)for p in W.glob('work_*/a.wav')}
before_sources={str(p):sha(p)for p in (W/'scripts').glob('*.json')}
scratch=M/'_only48_correct_context_S15_private'
assert not scratch.exists();scratch.mkdir()
log=scratch/'cache-log.txt';os.environ['CACHE_LOG']=str(log)
request=json.loads(a.request.read_text())
report={'kind':'onlyS15_correct_original_dictionary_context_two_mothers_and_actual_level_diagnostic',
        'source_id':'48','book_order':42,'request_sha256':SOURCE,'helper_sha256':sha(__file__),
        'root_decision_sha256':DECISION,'actual_missing_key_witness_sha256':WITNESS,
        'conditional_new_model_scope_actual_witness_satisfied':True,
        'correct_current_dictionary_sha256':DICT,'correct_context_dictionary_sha256':CTX,
        'old_cache_registry_sha256':OLDREG,'original_maker_sha256':MAKER,
        'source_GEN_MD_not_modified':True,'new_NV_or_CF_created':False,
        'no_raw_GT_models_or_cache_bytes_in_public_artifact':True,
        'formal_freeze0fff_stays_hold_until_root_new_gain_selection':True,
        'quality_acceptance':False,'production_delivery_eligible':False,
        'full_native2ASR8R_and_fullV3_separate_required':True,'cache_entries':[]}
keys=[]
try:
    os.chdir(W);sys.path.insert(0,str(W))
    s=importlib.util.spec_from_file_location('correct_original48_onlyS15',W/'make_video.py')
    m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
    m._REPO_CACHE=str(M/'forbid-public-private-cache-export');assert not Path(m._REPO_CACHE).exists()
    assert m.PRON_WORDS['Yuan']=='juːˈɑːn'
    assert m._OLDF and sha(m._OLDF)==OLDREG and m._CTX_PATH and sha(m._CTX_PATH)==CTX
    actual_dict=next(Path(p)for p in (m._PRON_PATH,'读音改正.json','/home/user/postgraduate-vocabulary/视频/工具/发音词典/读音改正.json')if Path(p).is_file())
    assert sha(actual_dict)==DICT
    report['actual_loaded_dictionary']=str(actual_dict)
    for obj in (m.k,m.KT):
        sessions=[v for v in vars(obj).values()if hasattr(v,'get_session_options')]
        assert sessions
        for session in sessions:
            options=session.get_session_options();assert options.intra_op_num_threads==options.inter_op_num_threads==1
    np,SR=m.np,m.SR
    sent=' '.join(m.R.strip_gloss(c['en']).replace('**','').strip()for c in request['sentences'][14]['chunks'])
    text=m.spoken(sent);assert hashlib.sha256(text.encode()).hexdigest()==PLAIN_INPUT
    assert sent==prior['exact_new_plain_English']
    for table in (m.NONVOICE,m.GRAFT,m.BOOST,m.PGRAFT,m.DEL_AT,m.INSERT_AT):
        assert sent not in table, 'New S15 cannot reuse an old clock.'
    captured={}
    for method,obj,kwargs,model in [('create',m.k,{},'kokoro-v1.0.onnx'),
           ('create_timed',m.KT,{'clause_pause':0,'sentence_pause':0},'kokoro-v1.0-timed.onnx')]:
        expected=[]
        def capture(actual_text,voice,speed=1.0,lang='en-us',**kw):
            mid=m._portable_mid(str(M/'tts'/model))
            assert mid==model+':'+prior['original_models_fullSHA'][model][:16]
            voiceid=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
            key=hashlib.sha1(repr((method,mid,actual_text,voiceid,float(speed),lang,sorted(kw.items()))).encode()).hexdigest()+'.pkl'
            expected.append((key,hashlib.sha256(actual_text.encode()).hexdigest(),actual_text,kw))
        m._pron(capture)(text,voice=m.V,speed=m.SPEED,lang='en-us',**kwargs)
        assert len(expected)==1
        key,inputsha,input_text,actualkw=expected[0]
        assert inputsha!=PLAIN_INPUT and actualkw.get('is_phonemes')is True
        if method=='create':assert key==RAWKEY
        assert key not in oldfive
        captured[method]={'key':key,'input_sha256':inputsha,'phonemes':input_text,'kwargs':kwargs}
        keys.extend([key,key+'.单线程'])
    assert captured['create']['input_sha256']==captured['create_timed']['input_sha256']
    report['actual_correct_post_pron_input_sha256']=captured['create']['input_sha256']
    report['actual_correct_post_pron_phonemes']=captured['create']['phonemes']
    report['plain_English_spoken_input_sha256']=PLAIN_INPUT
    calls=[]
    for method,obj in [('create',m.k),('create_timed',m.KT)]:
        original=getattr(obj,method)
        def guarded(t,voice,speed=1.0,lang='en-us',_method=method,_fn=original,**kw):
            assert t==text and speed==m.SPEED and lang=='en-us', 'Non-target TTS input forbidden.'
            assert np.array_equal(voice,m.V), 'Original narrator vector must remain exact.'
            calls.append(_method)
            return _fn(t,voice=voice,speed=speed,lang=lang,**kw)
        setattr(obj,method,guarded)
    values={}
    for method,obj in [('create',m.k),('create_timed',m.KT)]:
        key=captured[method]['key'];value=getattr(obj,method)(text,voice=m.V,speed=m.SPEED,lang='en-us',**captured[method]['kwargs'])
        path,marker=C/key,C/(key+'.单线程')
        assert marker.is_file()and marker.read_text().strip()==sha(path)[:16]
        m._条目核对(str(path));values[method]=value
        report['cache_entries'].append({'method':method,'exact_cache_key':key,
            'actual_model_input_sha256':captured[method]['input_sha256'],'actual_pkl_sha256':sha(path),
            'actual_marker_sha256':sha(marker),'actual_marker_value':marker.read_text().strip(),
            'actual_array_sha256':hashlib.sha256(np.ascontiguousarray(value[0]).tobytes()).hexdigest(),
            'array_samples':len(value[0]),'sample_rate':value[1],
            'preexisted':key in before,'new_original_model_inference':key not in before,
            'timed_token_count':len(value[2])if method=='create_timed'else None})
    pieces,gaps,p0=[],[],0;listing=m.list_commas(sent)
    for match in m.re.finditer(r'[,;:](?=\s)',sent):
        pieces.append((p0,match.end()));p0=match.end()+1
        gaps.append(m.P_LIST if match.start()in listing else m.P_COMMA)
    pieces.append((p0,len(sent)))
    clips,tmap=m.sentence_audio(sent,pieces,gaps)
    base_request=copy.deepcopy(request)
    base_request.get('分段增益dB',{}).pop('S15',None)
    base,basewave,auto,manual=m.句增益(base_request,'48',14,sent,pieces,gaps,[x.copy()for x in clips],tmap,np.concatenate(clips))
    plus_request=copy.deepcopy(base_request);plus_request.setdefault('分段增益dB',{})['S15']={'1':1.0}
    plus,pluswave,auto2,manual2=m.句增益(plus_request,'48',14,sent,pieces,gaps,[x.copy()for x in clips],tmap,np.concatenate(clips))
    assert auto==auto2 and not manual and manual2=={'1':1.0}
    assert len(basewave)==len(pluswave)
    report['source_plain_English']=sent
    report['original_G36_automatic_gains']={str(k):v for k,v in auto.items()}
    report['candidate_manual_gains']={'baseline0':manual,'plus1':manual2}
    report['actual_new_raw_w_fingerprint']=m.SENT_FP[sent]
    report['actual_new_raw_punctuation_cuts']=[list(x)for x in m.LAST['cuts']]
    report['actual_new_processed_samples']=len(basewave)
    report['actual_piece_levels']=[]
    for i,(c0,c1,t0,t1)in enumerate(tmap):
        row={'piece':i+1,'text':sent[c0:c1],'span_s':[t0,t1]}
        for label,wave in [('baseline0',basewave),('plus1',pluswave)]:
            x=wave[round(t0*SR):round(t1*SR)].astype(float)
            row[label]={'RMS_dBFS':20*math.log10(float(np.sqrt(np.mean(x*x)))+1e-20),
                        'peak_dBFS':20*math.log10(float(np.max(np.abs(x)))+1e-20)}
        row['piece_samples_exact_between_candidates']=bool(np.array_equal(base[2*i],plus[2*i]))
        report['actual_piece_levels'].append(row)
    diff=np.flatnonzero(basewave!=pluswave);end=round(tmap[0][3]*SR)
    report['actual_changed_samples_between_candidates']={'count':len(diff),
        'first_sample':int(diff[0])if len(diff)else None,'last_sample':int(diff[-1])if len(diff)else None,
        'first_piece_end_sample':end,'all_later_samples_exact':bool(np.array_equal(basewave[end:],pluswave[end:])),
        'later_changed_samples':int(np.count_nonzero(basewave[end:]!=pluswave[end:]))}
    ls=importlib.util.spec_from_file_location('correct48_original_LU',T/'响度一致性核对.py');L=importlib.util.module_from_spec(ls);ls.loader.exec_module(L)
    common=max(float(np.max(np.abs(basewave))),float(np.max(np.abs(pluswave))))
    report['actual_original_LU_comparison']={'program_sha256':sha(T/'响度一致性核对.py'),
        'same_reference_peak':common,'source48_short_equivalent_mode':L.短起('48'),
        'original_adjacent_limit_LU':L.IN_ADJ,'candidates':{}}
    for label,wave in [('baseline0',basewave),('plus1',pluswave)]:
        wav=scratch/(label+'-meter-private.wav')
        padded=np.concatenate([np.zeros(round(.5*SR),np.float32),wave,np.zeros(round(.5*SR),np.float32)])
        m.sf.write(wav,padded/common*.89,SR);TM=L.momentary(str(wav));levels=[]
        for i,(_,_,t0,t1)in enumerate(tmap):
            value=L.等效(L.段响度(TM,.5+t0,.5+t1),t0,t1,L.短起('48'))
            _,peak=L.段量(TM,.5+t0,.5+t1)
            levels.append({'piece':i+1,'gated_LUFS':float(value)if value is not None else None,'maximum400ms_LUFS':float(peak)})
        ds=[levels[i]['gated_LUFS']-levels[i-1]['gated_LUFS']if levels[i]['gated_LUFS']is not None and levels[i-1]['gated_LUFS']is not None else None for i in range(1,len(levels))]
        report['actual_original_LU_comparison']['candidates'][label]={'pieces':levels,
            'adjacent_LU_differences':ds,'all_adjacent_within_original_limit':all(v is not None and abs(v)<=L.IN_ADJ for v in ds)}
    wav=scratch/'actual-correct-S15-baseline-private.wav';audio=scratch/'actual-correct-S15-baseline-private.m4a'
    m.sf.write(wav,basewave/max(1e-12,float(np.max(np.abs(basewave))))*.89,SR)
    import subprocess
    subprocess.run([m.FF,'-v','error','-y','-i',str(wav),'-af',m.AF,'-c:a','aac','-b:a','192k',str(audio)],check=True)
    aps=importlib.util.spec_from_file_location('correct48_original_twoASR',T/'机器复听.py');ASR=importlib.util.module_from_spec(aps);aps.loader.exec_module(ASR)
    x16=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(audio),'-f','f32le','-ac','1','-ar','16000','-']),dtype=np.float32)
    transcripts,differences=ASR.各路(ASR.识别器(),sent,x16)
    report['actual_original_two_route_S15_transcripts']=transcripts
    report['actual_original_two_route_S15_differences']=differences
    report['new_ASR_CF_created']=False
    report['private_baseline_diagnostic_AAC_sha256']=sha(audio)
    report['not_a_whole_track_AAC_or_formal_mastering_claim']=True
    report['all_TTS_method_calls_target_only']=calls
    report['actual_new_original_TTS_inference_count']=sum(x['new_original_model_inference']for x in report['cache_entries'])
    assert report['actual_new_original_TTS_inference_count']<=2
    report['diagnostic_completed']=True
except BaseException as error:
    report['diagnostic_completed']=False;report['error']={'type':type(error).__name__,'detail':str(error)};traceback.print_exc()
finally:
    after=inventory()
    levels={line.strip()for line in log.read_text().splitlines()if line.startswith('调平_')}if log.exists()else set()
    report['original_G36_cache_filenames']=sorted(levels)
    allowed=set(keys)|levels
    report['all_existing_private_cache_files_exact']=all(after.get(key)==value for key,value in before.items())
    report['only_authorized_correct_S15_new_private_files']=set(after)-set(before)<=allowed
    report['all_preexisting_work_PCM_exact']=all(Path(p).is_file()and sha(p)==value for p,value in before_pcm.items())
    report['all_normal_source_scripts_exact']=all(Path(p).is_file()and sha(p)==value for p,value in before_sources.items())
    report['original_requested0193_bytes_exact']=sha(a.request)==SOURCE
    report['all_original7_core_files_exact']={key:sha(T/key)for key in CORE}==CORE
    report['original_dictionary_and_context_exact_after']=sha(T/'发音词典/读音改正.json')==DICT and sha(T/'发音词典/按语境读音.json')==CTX
    report['original_models_and_voice_exact_after']=({name:sha(M/'tts'/name)for name in prior['original_models_fullSHA']}==prior['original_models_fullSHA']and sha(M/'tts/voice_mb.npy')==prior['original_voice_sha256'])
    report['old_wrong_context_five_files_preserved_exact']={key:sha(C/key)for key in oldfive}==oldfive
    report['new_private_files']=[{'name':key,'sha256':after[key]}for key in sorted(set(after)-set(before))]
    ready=bool(report.get('diagnostic_completed')and len(levels)==1 and
        report['all_existing_private_cache_files_exact']and report['only_authorized_correct_S15_new_private_files']and
        report['all_preexisting_work_PCM_exact']and report['all_normal_source_scripts_exact']and
        report['original_requested0193_bytes_exact']and report['all_original7_core_files_exact']and
        report['original_dictionary_and_context_exact_after']and report['original_models_and_voice_exact_after'])
    report['actual_correct_mother_identity_and_measurements_ready_for_root_selection']=ready
    if ready:
        files=sorted(set(keys)|levels);assert len(files)==5
        runid=os.environ.get('GITHUB_RUN_ID','');assert runid.isdigit()
        key='Linux-native48-correctcontext-YuanLongping-'+runid
        fixture={'kind':'source48_correct_original_dictionary_context_private_mother_identity_gain_selection_pending',
            'source_id':'48','request_source_sha256':SOURCE,'root_decision_sha256':DECISION,
            'missing_key_witness_sha256':WITNESS,'dictionary_sha256':DICT,'context_dictionary_sha256':CTX,
            'actual_native_run':runid,'actual_native_head':os.environ.get('GITHUB_SHA'),
            'private_Actions_cache_key':key,'five_private_files_require_fullSHA_readback':{name:after[name]for name in files},
            'all_five_restored_files_require_actual_fullSHA_readback':{name:after[name]for name in files},
            'cache_entries':report['cache_entries'],'post_pron_input_sha256':report['actual_correct_post_pron_input_sha256'],
            'actual_new_raw_w_fingerprint':report['actual_new_raw_w_fingerprint'],
            'actual_original_G36_gains':report['original_G36_automatic_gains'],
            'actual_raw_punctuation_cuts':report['actual_new_raw_punctuation_cuts'],
            'actual_auto_level_filename':next(iter(levels)),
            'original_models_fullSHA':prior['original_models_fullSHA'],'original_voice_sha256':prior['original_voice_sha256'],
            'original_maker_sha256':MAKER,'exact_new_plain_English':report['source_plain_English'],
            'root_gain_selection_pending':True,'formal_acceptance_or_ready0fff_not_claimed':True,
            'next':'Root selects new actual baseline0/plus1 gain, paired sourceGEN freeze if changed; wholecached newWAV/AAC and all16 pre-master PCM identity under original context; originalfull2ASR8R/output/fullV3 remain mandatory.'}
        fixture_path=a.output.parent/'48-correct-context-S15-private-cache-identity.json'
        fixture_path.parent.mkdir(parents=True,exist_ok=True);fixture_path.write_text(json.dumps(fixture,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
        report['correct_context_private_cache_identity_fixture']={'file':fixture_path.name,'sha256':sha(fixture_path)}
        with a.cache_path_output.open('a')as f:
            f.write('cache_key='+key+'\ncache_paths<<CORRECT48PRIVATE\n'+'\n'.join(str(C/name)for name in files)+'\nCORRECT48PRIVATE\n')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    print(json.dumps({'diagnostic_completed':report.get('diagnostic_completed'),'correct_context_mothers_and_measurements_ready':ready,
        'output_sha256':sha(a.output),'error':report.get('error'),'formal_acceptance':False},ensure_ascii=False))
sys.exit(0 if report.get('actual_correct_mother_identity_and_measurements_ready_for_root_selection')else 1)
