"""Only current S18 two actual PV flags: strict cached original assembly and true timed labels.
No whole build, model inference, G36, GT, ASR, audio output or confirmation writing.
"""
from pathlib import Path
import argparse,ast,contextlib,copy,gc,hashlib,importlib.util,inspect,io,json,math,os,shutil,sys,tempfile,traceback,types
sys.dont_write_bytecode=True
SOURCE='34afbcb1e517c10db4ebb963bbf59615b1c5cf439fee5156e85b14717f7edb13'
MAKER='0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
PROVIDER='32602bee21b14ed161fdfd3c8b921b267782ad143a49c3ebd256c16c473808f5'
DICT='5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
CTX='4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
OLDREG='91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
REGISTRY='dfde6c065a3558b74923ce82865a3b01dae1f839af4456b74de55dc3ff492312'
VOICE='1f97658bb5a4280cc3f6c01dc644dff471bf57c970fc8b99f3049d6991c4f6c8'
MODELS={'kokoro-v1.0.onnx':'7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5','kokoro-v1.0-timed.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
FLAGS=('STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS')
DSP_KEYS=('非人声区间','词尾除阻','除阻加强','停顿插入点','停顿删除区间','停顿处除阻','分段增益dB','段内渐变dB','句子增益dB','分段包络dB','列举逗号','结尾句','合成标点','区间声音指纹','朗读删逗号')
PROFILE_SHA='a43d607a8edc2eec9220910418a245b8af6562b963f7688eb2315d54125db5bc'


def require(value, message):
    if not value:
        raise AssertionError(message)


def read(path):
    return json.loads(Path(path).read_text())


@contextlib.contextmanager
def source_namespace(work, shadow_bytes, restoration=None):
    """Rename the original scripts inode, including directory links, and restore it."""
    work = Path(work)
    scripts = work / 'scripts'
    existed = os.path.lexists(scripts)
    original_inode = scripts.lstat().st_ino if existed else None
    snapshots = {p.name: p.read_bytes() for p in scripts.glob('*.json')} if existed else {}
    scratch = Path(tempfile.mkdtemp(prefix='_source24_only_S18_namespace_', dir=work.parent))
    backup = scratch / 'original-scripts-inode'
    moved = False
    try:
        if existed:
            os.replace(scripts, backup)
            moved = True
        scripts.mkdir()
        for name, data in snapshots.items():
            (scripts / name).write_bytes(data)
        (scripts / '24.json').write_bytes(shadow_bytes)
        yield
    finally:
        if moved or not existed:
            if os.path.lexists(scripts):
                if scripts.is_symlink() or scripts.is_file():
                    scripts.unlink()
                else:
                    shutil.rmtree(scripts)
            if moved:
                os.replace(backup, scripts)
        shutil.rmtree(scratch)
        require(os.path.lexists(scripts) == existed, 'Scripts existence was not restored')
        if existed:
            require(scripts.lstat().st_ino == original_inode, 'Scripts inode not restored')
            require({p.name: p.read_bytes() for p in scripts.glob('*.json')} == snapshots,
                    'Original normal source scripts changed')
        if restoration is not None:
            restoration['normal_scripts_namespace_restored'] = True


@contextlib.contextmanager
def environment_and_cwd(work, restoration=None):
    keys = set(FLAGS) | {'CACHE_LOG', 'AUDIO_ONLY', 'VOICE', 'AFFILE', 'OLD_IV_VOID'}
    prior = {k: os.environ.get(k) for k in keys}
    cwd, path = Path.cwd(), list(sys.path)
    try:
        os.chdir(work)
        sys.path.insert(0, str(work))
        os.environ['STRICT_CACHE'] = '1'
        os.environ['XG_NOPUSH'] = '1'
        os.environ['AUDIO_ONLY'] = '1'
        os.environ.pop('CACHE_LOG', None)
        yield
    finally:
        os.chdir(cwd)
        sys.path[:] = path
        for key, value in prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        require(all(os.environ.get(k) == v for k, v in prior.items()), 'Environment restore failed')
        if restoration is not None:
            restoration['environment_cwd_sys_path_restored'] = True


def closure_cell(fn, name):
    cells = dict(zip(fn.__code__.co_freevars, fn.__closure__ or ()))
    require(name in cells, 'Original cached/pron closure ABI changed')
    return cells[name]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def typed(v):
    if isinstance(v,dict): return ('dict',tuple(sorted((k,typed(x))for k,x in v.items())))
    if isinstance(v,list): return ('list',tuple(typed(x)for x in v))
    return (type(v).__name__,v)


def effective_controls(data,sid):
    return {key:data[key][sid]for key in DSP_KEYS if isinstance(data.get(key),dict)and sid in data[key]}


def strict_cached_guard(module,np,cache,method,model_name,outer,used,result):
    """Same original48 portable-key/projection guard, with strict-state hard stop."""
    def guarded(text,voice,speed=1.0,lang='en-us',**kw):
        require(os.environ.get('STRICT_CACHE')=='1','All model calls must remain STRICT')
        captured=[]
        def capture(actual_text,voice,speed=1.0,lang='en-us',**actual_kw):
            mid=module._portable_mid(str(cache.parent/model_name))
            voice_id=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
            key=hashlib.sha1(repr((method,mid,actual_text,voice_id,float(speed),lang,sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
            path=cache/key
            require(path.is_file(),'STRICT_CACHED_PORTABLE_KEY_MISSING '+key)
            module._条目核对(str(path))
            item={'name':key,'sha256':digest(path),'method':method,'actual_model_input_sha256':hashlib.sha256(actual_text.encode()).hexdigest()}
            marker=cache/(key+'.单线程')
            if marker.exists():item.update(single_thread_marker_sha256=digest(marker),single_thread_marker_value=marker.read_text().strip())
            captured.append(item)
        module._pron(capture)(text,voice=voice,speed=speed,lang=lang,**kw)
        require(len(captured)==1,'Original pron projection must yield exactly one cache input')
        used[captured[0]['name']]=captured[0]
        result['cached_model_calls']+=1
        value=outer(text,voice=voice,speed=speed,lang=lang,**kw)
        require(isinstance(value,tuple)and len(value)==(2 if method=='create'else 3)and value[1]==24000,'Original cached model tuple schema differs')
        result.setdefault('actual_original_mother_reads_by_segment',[]).append({
            'segment':result.get('_active_segment'),'method':method,'name':captured[0]['name'],'pkl_sha256':captured[0]['sha256'],
            'actual_model_input_sha256':captured[0]['actual_model_input_sha256'],'unprocessed_array_sha256':hashlib.sha256(np.ascontiguousarray(value[0]).tobytes()).hexdigest(),
            'samples':len(value[0]),'dtype':str(value[0].dtype)})
        return value
    return guarded


def block_original_native(module,work):
    originals=[]
    def forbidden(*a,**kw):raise AssertionError('Any original native model method/inference is forbidden in whole observer')
    try:
        for obj,method in [(module.k,'create'),(module.KT,'create_timed')]:
            pron=getattr(obj,method)
            cached=closure_cell(pron,'fn').cell_contents
            require(cached.__code__.co_filename==str(work/'make_video.py'),'Original cached/pron ABI required')
            cell=closure_cell(cached,'fn');originals.append(('cell',cell,cell.cell_contents));cell.cell_contents=forbidden
        for obj,method in [(module.k,'create_timed'),(module.KT,'create')]:
            if hasattr(obj,method):originals.append(('method',(obj,method),getattr(obj,method)));setattr(obj,method,forbidden)
    except BaseException:
        restore_native(originals)
        raise
    return originals


def restore_native(originals):
    for kind,target,value in reversed(originals):
        if kind=='cell':target.cell_contents=value
        else:setattr(target[0],target[1],value)


def ast_sha(node):
    # The exact same original function must pin identically on caller Python3.11 and local3.12.
    node=copy.deepcopy(node)
    for item in ast.walk(node):
        if hasattr(item,'type_params'):
            require(item.type_params==[], 'Nonempty new generic AST parameters not authorized')
            delattr(item,'type_params')
    return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()


def original_build_fragments(maker_text):
    build=next(n for n in ast.parse(maker_text).body if isinstance(n,ast.FunctionDef)and n.name=='build')
    loop=next(n for n in build.body if isinstance(n,ast.For)and isinstance(n.target,ast.Tuple)and [x.id for x in n.target.elts]==['si','s'])
    start=next(i for i,n in enumerate(loop.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='texts'for t in n.targets))
    end=next(i for i,n in enumerate(loop.body)if isinstance(n,ast.Assign)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='句增益')
    pre=[]
    for n in build.body:
        if isinstance(n,ast.Assign)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='拆出简述页':pre.append(n)
        if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='apply_script':pre.append(n)
    return pre,loop.body[start:end+1]


def only_target_wrapper(original,method,module,expected,cache,np,used,result,logical):
    guarded=strict_cached_guard(module,np,cache,method,'kokoro-v1.0.onnx'if method=='create'else'kokoro-v1.0-timed.onnx',original,used,result)
    expected_reads={x['method']:x for x in expected['mother_reads']}
    def wrapper(text,voice,speed=1.0,lang='en-us',**kw):
        require(text==logical and speed==.95 and lang=='en-us','Only exact full S18 original voice tuple is allowed')
        require(np.array_equal(voice,module.V),'Only original full voice array allowed')
        require(typed(kw)==typed({}if method=='create'else{'clause_pause':0,'sentence_pause':0}), 'Original raw/timed kwargs exact typed values required')
        before=len(result.get('actual_original_mother_reads_by_segment',[]));value=guarded(text,voice,speed=speed,lang=lang,**kw)
        reads=result['actual_original_mother_reads_by_segment'];require(len(reads)==before+1 and typed(reads[-1])==typed(expected_reads[method]),'Actual S18 cache key/input/fullPKL/array tuple differs from f062')
        return value
    return wrapper


def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')


def validate_adoption(value, helper_sha, profile_sha):
    require(not str(value.get('kind','')).startswith('TEMPLATE') and value.get('this_template_grants_execution') is not False,
            'A template is not actual finite execution adoption')
    need={'source_id':'24','book_order':49,'target_sentence':'S18','helper_sha256':helper_sha,
          'profile_sha256':profile_sha,'only_S18_cached_local_PV_and_true_timed_phonemes_authorized':True,
          'new_TTS_G36_GT_ASR_whole_native_audio_or_CF_write_authorized':False}
    require(all(type(value.get(k))is type(v)and value.get(k)==v for k,v in need.items()), 'Wrong actual finite cached-only probe adoption')


def validate_observation(observed, expected):
    require(typed(observed)==typed(expected['S18']), 'Actual S18 pre/clips/tmap/cuts/VFP/effectiveDSP/gains differ from actual0bfc whole')
    require(observed['automatic_gain_dB']=={} and observed['manual_gain_dB']=={'2':-1.109697858091752},
            'Only exact existingmanual piece2 gain, no G36/othergain')
    require(observed['actual_raw_w_fingerprint']=='e43769675c69' and observed['actual_raw_cuts']==[[87600,96000,.38]], 'True current raw identity/cuts required')
    return True


def kept_raw_to_processed_segments(last, SR, length):
    """Scalar mapping from original LAST.segs only; does not change any samples."""
    out=[]
    for a,b,t0,rm in last['segs']:
        a,b=int(a),int(b);cursor=0;prev=0
        start=int(round(t0*SR));require(abs(t0*SR-start)<1e-5,'Original sample clock not integral')
        intervals=list(rm)+[(b-a,b-a)]
        for lo,hi in intervals:
            lo,hi=int(lo),int(hi);require(0<=prev<=lo<=hi<=b-a,'Invalid original removal map')
            if lo>prev:
                rawlo,rawhi=a+prev,a+lo;plo,phi=start+cursor,start+cursor+(lo-prev)
                cutlo=max(0,plo);cuthi=min(length,phi)
                if cutlo<cuthi:out.append({'clean_raw_start':rawlo+(cutlo-plo),'clean_raw_end':rawlo+(cuthi-plo),'processed_start':cutlo,'processed_end':cuthi})
                cursor+=lo-prev
            prev=hi
    require(out and all(0<=r['processed_start']<r['processed_end']<=length for r in out),'No valid actual mapper spans')
    for a,b in zip(out,out[1:]):require(a['processed_end']<=b['processed_start'],'Original map overlaps')
    return out


def mapped_raw_interval(raw0, raw1, mapping, head):
    clean0,clean1=raw0-head,raw1-head;out=[]
    for r in mapping:
        lo=max(clean0,r['clean_raw_start']);hi=min(clean1,r['clean_raw_end'])
        if lo<hi:out.append({'clean_raw_samples':[lo,hi],'processed_samples':[r['processed_start']+lo-r['clean_raw_start'],r['processed_start']+hi-r['clean_raw_start']]})
    return out


def load_PV(tools, profile, np):
    path=tools/'纯人声核对.py';require(digest(path)==profile['original_PV_SHA256'],'Original actual0e99 PV checker changed')
    tree=ast.parse(path.read_text());nodes=[]
    for name,want in profile['original_PV_function_AST_SHA256'].items():
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name)
        require(ast_sha(node)==want,'Original PV function AST changed: '+name);nodes.append(node)
    namespace={'np':np,'SR':24000,'F':120}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+':unchanged-original-scalar-functions','exec'),namespace)
    return types.SimpleNamespace(**namespace)


def describe_true_timed_words(m, sent, raw, timed, last, mapping, tools):
    toks=timed[2];SR=m.SR;scale=len(raw[0])/len(timed[0])
    require(len(toks)==105 and all(isinstance(t.phoneme,str) and len(t.phoneme)==1 for t in toks) and math.isclose(scale,last['scale'],rel_tol=0,abs_tol=1e-12),'Actual timed count/single-label ABI/rawscale differs')
    full=''.join(t.phoneme for t in toks)
    require(full==m.phonemes_of(m._synth_punct(m.spoken(sent))), 'Actual complete timed phonemes mismatch original current projected input')
    rows=[]
    for i,t in enumerate(toks):
        require(isinstance(t.phoneme,str)and math.isfinite(t.start)and math.isfinite(t.end)and 0<=t.start<=t.end<=len(timed[0])/SR+1e-5,'Invalid actual timed label')
        lo,hi=int(round(t.start*scale*SR)),int(round(t.end*scale*SR))
        rows.append({'token_index':i,'actual_phoneme':t.phoneme,'actual_timed_start_s':float(t.start),'actual_timed_end_s':float(t.end),
                     'actual_unprocessed_raw_scaled_sample_interval':[lo,hi],
                     'sample_conversion':'original chunk_times int(round(actual timed boundary * actual LAST.scale * SR))',
                     'actual_original_processed_intersections':mapped_raw_interval(lo,hi,mapping,last['head'])})
    # This is the original dossier phonetic grouping ABI, not the producer's
    # display-chunk L14 aligner. It observes the actual complete timed sequence.
    dossier=Path(tools)/'疑点清单.py'
    require(digest(dossier)=='a3b7604fbcbdd31fecd0b548382426e70ddab810fc923ff895027c084f30eab2','Actual stamped original dossier required')
    node=next(n for n in ast.parse(dossier.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='words')
    ns={'SR':SR};exec(compile(ast.Module(body=[node],type_ignores=[]),str(dossier)+':unchanged-original-words','exec'),ns)
    actual_groups=ns['words']({'toks':[(t.phoneme,t.start,t.end)for t in toks],'scale':scale,'head':last['head']})
    index_groups=[];group=[]
    for i,ph in [(i,t.phoneme)for i,t in enumerate(toks)]+[(len(toks),' ')]:
        if not ph.strip():
            if group and ''.join(toks[j].phoneme for j in group).strip(',;:.!?'):index_groups.append((group[0],group[-1]+1))
            group=[]
        else:group.append(i)
    require(len(index_groups)==len(actual_groups),'Original phonetic group index ABI differs')
    display=m.re.findall(r'\S+',sent);require(' '.join(display)==sent,'Display splitting must preserve original punctuation')
    ambiguous=len(display)!=len(actual_groups)
    out=[]
    for j,((phonemes,t0,t1),(lo,hi))in enumerate(zip(actual_groups,index_groups)):
        require(phonemes==''.join(t.phoneme for t in toks[lo:hi]),'Original phonetic group content differs')
        out.append({'token_index_interval':[lo,hi],'actual_joined_timed_phonemes':phonemes,
                    'original_dossier_clean_raw_seconds':[t0,t1],
                    'display_word_with_original_punctuation':None if ambiguous else display[j],
                    'basis':'original dossier.words phonetic group; any equal-count English label is sequential annotation only, not L14 forced alignment, ASR, hearing or word identity proof'})
    return {'all_actual105_timed_tokens':rows,'original_word_token_alignment':out,
            'original_dossier_words_AST_SHA256':ast_sha(node),'english_annotation_ambiguous':ambiguous,
            'display_word_count':len(display),'actual_phonetic_group_count':len(actual_groups),
            'english_annotation_is_only_sequential_not_word_identity_or_quality':True,
            'full_true_joined_phonemes':full,'raw_timed_duration_scale':scale,
            'not_guessed_ship_back_or_stop_consonant':True}


def measure_PV_and_context(m, pcm, expected, tokens, mapping, profile):
    np,SR=m.np,m.SR;post=pcm/np.float32(expected['master_absolute_peak'])*.89
    arrsha=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
    require(post.dtype==np.float32 and arrsha(post)==expected['post_master_float_SHA256'],'Current original orderedmaster S18 float identity mismatch')
    # Exact original libsndfile PCM16 quantization in an in-memory container only, not a production/file audio export.
    stream=io.BytesIO();m.sf.write(stream,post,SR,format='WAV',subtype='PCM_16');stream.seek(0);q,rate=m.sf.read(stream,dtype='int16')
    require(rate==SR and arrsha(q)==expected['actual_WAV_PCM16_segment_sha256'],'Actual original S18 PCM16 slice identity mismatch')
    x=q.astype(np.float64)/32768;PV=load_PV(Path(profile['_actual_tools']),profile,np)
    lead=SR;pad=np.concatenate([np.zeros(lead,np.float64),x,np.zeros(2*SR,np.float64)])
    # The actual whole has >=1.0s digitalgap before this lastsentence and2s after it.
    # Zero padding reproduces its isolated original PV segment, without building a whole or changing output samples.
    allrows=PV.scan(pad);global_start=expected['global_start_s'];wanted=set(expected['expected_requested_PV_displayed_keys']);hits=[]
    for row in allrows:
        local0,local1=row[1]-lead/SR,row[2]-lead/SR
        globalrow=(row[0],local0+global_start,local1+global_start,*row[3:]);key=PV.key(globalrow)
        if key in wanted:require(row[0]=='噗声'and PV.实测(globalrow)==expected['actual_native_rounded_PV_scalar'][key],'Actual original native PV class/rounded scalar differs')
        if key not in wanted:continue
        i0=int(round(local0*SR));i1=int(round(local1*SR));require([i0,i1]==expected['expected_actual_PV_intervals'][key]['local_samples'],'Actual requested PV sample clock differs');contextlo=max(0,i0-int(.060*SR));contexthi=min(len(x),i1+int(.060*SR))
        seg=next((a,b)for a,b in PV.segments(pad)if a<=int(round(row[1]*SR))<b)
        s=pad[seg[0]:seg[1]];n=len(s)//120;ref=float(np.sqrt(np.mean(s[:n*120].reshape(n,120)**2,axis=1)).max())
        frames=[]
        for lo in range(contextlo,contexthi,60):
            hi=min(lo+60,contexthi);v=x[lo:hi];w=x[max(0,lo-240):min(len(x),lo+240)]
            c,low=PV.spec(v);frames.append({'processed_sample_interval':[lo,hi],'local_seconds':[lo/SR,hi/SR],
                'rms_dB_relative_original_PV_segment_5ms_peak':20*math.log10(float(np.sqrt(np.mean(v*v)))/(ref+1e-12)+1e-12),
                'original_spec_centroid_Hz':float(c),'original_spec_low_under150_dB':float(low),
                'original_per_on_20ms_neighborhood':float(PV.per(w))if len(w)>=480 else None,
                'digital_zero':bool(np.all(v==0))})
        matching=[]
        for t in tokens['all_actual105_timed_tokens']:
            if any(max(i0,r['processed_samples'][0])<min(i1,r['processed_samples'][1])for r in t['actual_original_processed_intersections']):matching.append(t['token_index'])
        words=[r for r in tokens['original_word_token_alignment']if any(r['token_index_interval'][0]<=i<r['token_index_interval'][1]for i in matching)]
        hit={'original_PV_full_actual_tuple':list(globalrow),'original_PV_displayed_key':key,'original_PV_rounded_scalar_measurements':PV.实测(globalrow),'actual_local_interval_s':[local0,local1],
             'actual_local_sample_interval':[i0,i1],'actual_overlapping_token_indices':matching,'actual_original_phonetic_group_rows':words,'english_annotation_ambiguous':tokens['english_annotation_ambiguous'],
             'english_annotations_are_sequential_only_not_L14_ASR_hearing_or_word_identity':True,
             'actual_context_overlapping_token_indices':[t['token_index']for t in tokens['all_actual105_timed_tokens']if any(max(contextlo,r['processed_samples'][0])<min(contexthi,r['processed_samples'][1])for r in t['actual_original_processed_intersections'])],
             'context60ms_each_side_2p5ms_acoustic_frames':frames,
             'original_PV_贴词头_observation':bool(PV.贴词头(pad,row)),
             'original_PV_爆破起5ms_observation':bool(PV.爆破起(pad,row)),
             'original_PV_爆破起20ms_observation':bool(PV.爆破起(pad,row,480)),
             'original_PV_贴词尾擦音_observation':bool(PV.贴词尾擦音(pad,row)),
             'no_confirmation_acceptance_or_semantic_claim':True}
        hits.append(hit)
    require({r['original_PV_displayed_key']for r in hits}==wanted,'Original two actual native PV flags did not replay on exact current PCM16 slice; stop rather than guess')
    return {'post_master_float_SHA256':arrsha(post),'actual_PCM16_SHA256':arrsha(q),'samples':len(q),
            'original_PV_all_local_flags':[list(r)for r in allrows],
            'actual_target_two_global_flags':hits,'all_original_flags_remain_diagnostic_not_passed':True,
            'reference_from_original_PV_segments_not_new_threshold':True,
            'no_production_WAV_or_AAC_or_PCM_exported':True}


def observe(a, profile, report):
    T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts';rest={};expected=profile['expected'];report['source_namespace_and_environment_restore']=rest
    result={'cached_model_calls':0,'_active_segment':'S18'};report['S18']=result
    with environment_and_cwd(W,rest),source_namespace(W,a.source.read_bytes(),rest):
        require(digest(W/'scripts/24.json')==SOURCE,'Sourcefirst exactcurrent34af required')
        name='_original24_only_two_actualPV_true_timed';previous={k:sys.modules.get(k)for k in ['render','title2','clean','出片指纹']}
        for k in previous:sys.modules.pop(k,None)
        require(name not in sys.modules,'Freshmaker namespace required');spec=importlib.util.spec_from_file_location(name,W/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[name]=m
        native=[];saved={};used={};values={}
        try:
            spec.loader.exec_module(m);m._SPOKEN_SOURCE_NO='24';require(digest(inspect.getsourcefile(type(m.k)))==PROVIDER,'Actual original provider source required')
            require(m._OLDF and digest(m._OLDF)==OLDREG and digest(m._cand)==DICT and m._CTX_PATH and digest(m._CTX_PATH)==CTX,'Actual originalregistry/dicts required')
            require(digest(M/'tts/AF.txt')==expected['AF_sha256']and m.AF==expected['AF_expression'],'OriginalAF identity required, not applied by scalarprobe')
            require(m.SR==24000 and m.SPEED==.95,'OriginalSR/speed required');np=m.np;data=read(W/'scripts/24.json')
            own=[' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in s['chunks'])for s in data['sentences']];require(len(own)==18 and all(str(m.SENT_NO.get(s))=='24'for s in own),'Freshsource-first SENT_NO identity required')
            logical=m.spoken(own[17]);native=block_original_native(m,W);saved={k:getattr(m,k)for k in ['build','title_audio','_auto_level']};saved['k.create']=m.k.create;saved['KT.create_timed']=m.KT.create_timed
            def forbidden(*a,**kw):raise AssertionError('No whole/title/G36/native inference or other sentence authorized')
            m.build=m.title_audio=m._auto_level=forbidden;m._REPO_CACHE=str(M/'forbidden-source24-only-PV-public-cache-export');require(not Path(m._REPO_CACHE).exists(),'Privateexport sentinel absent')
            for method,obj in [('create',m.k),('create_timed',m.KT)]:
                guard=only_target_wrapper(getattr(obj,method),method,m,expected,C,np,used,result,logical)
                def keepvalue(*args,_method=method,_guard=guard,**kwargs):
                    value=_guard(*args,**kwargs);require(_method not in values,'Only one exactcachedread per method');values[_method]=value;return value
                setattr(obj,method,keepvalue)
            text=(W/'make_video.py').read_text();pre,nodes=original_build_fragments(text)
            require(ast_sha(ast.Module(body=pre,type_ignores=[]))==profile['original_build_prelude_AST_SHA256']and ast_sha(ast.Module(body=nodes,type_ignores=[]))==profile['original_build_target_assembly_AST_SHA256'],'Originaltarget fragment changed')
            require(ast_sha(ast.parse(inspect.getsource(m.句增益)).body[0])==profile['original_gain_function_AST_SHA256'],'Originalgain function changed')
            gain=m.句增益;cap={}
            def observe_gain(data,no,si,sent,pieces,gaps,clips,tmap,audio):
                require(str(no)=='24'and si==17 and sent==own[17],'OnlyactualS18 assembly');cap['before']=audio.copy();cap['preclips']=[v.copy()for v in clips];cap['tmap']=copy.deepcopy(tmap)
                value=gain(data,no,si,sent,pieces,gaps,clips,tmap,audio);cap['value']=value;return value
            ns=dict(m.__dict__);ns.update(d=copy.deepcopy(data),no='24',si=17,s=copy.deepcopy(data['sentences'][17]),句增益=observe_gain)
            exec(compile(ast.Module(body=pre,type_ignores=[]),str(W/'make_video.py')+':original-display-prelude','exec'),ns);ns['s']=ns['d']['sentences'][17];ns['ch']=ns['s']['chunks']
            exec(compile(ast.Module(body=nodes,type_ignores=[]),str(W/'make_video.py')+':original-onlyS18-fragment','exec'),ns)
            clips,pcm,auto,manual=cap['value'];arrsha=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest();last=copy.deepcopy(m.LAST)
            observed={'plain_English_sha256':hashlib.sha256(ns['sent'].encode()).hexdigest(),'before_gain_PCM_sha256':arrsha(cap['before']),'before_gain_dtype':str(cap['before'].dtype),'before_gain_samples':len(cap['before']),'pre_master_PCM_sha256':arrsha(pcm),'PCM_dtype':str(pcm.dtype),'samples':len(pcm),'duration_s':len(pcm)/m.SR,'automatic_gain_dB':{str(k):v for k,v in auto.items()},'manual_gain_dB':manual,'exact_effective_DSP':effective_controls(ns['d'],'S18'),'actual_raw_w_fingerprint':m.SENT_FP.get(ns['sent']),'actual_raw_cuts':[list(x)for x in last['cuts']],'actual_fades':[list(x)for x in last.get('fades',[])],'actual_grafts':last.get('grafts',[]),'actual_head':last['head'],'actual_internal_hs':last['hs'],'pre_gain_piece_clips_sha256':[arrsha(x)for x in cap['preclips']],'pre_gain_tmap':[list(x)for x in cap['tmap']],'piece_clips_sha256':[arrsha(x)for x in clips],'actual_pieces':[list(x)for x in ns['pieces']],'actual_gaps':list(ns['gaps'])}
            result['actual_preassert_S18_identity']=observed;save(a.output,report);validate_observation(observed,expected)
            require(result['cached_model_calls']==2 and set(values)=={'create','create_timed'}and typed(list(used.values()))==typed(expected['used_cache']),'Exactlytwo originalactualcache reads required')
            require(np.array_equal(np.concatenate(clips),pcm),'Original clipconcat identity failed')
            mapping=kept_raw_to_processed_segments(last,m.SR,len(pcm));result['actual_original_LAST_scalar_mapper']={k:v for k,v in last.items()if k in ['scale','head','segs','total','cuts','grafts','gaps','fades','hs']}
            result['derived_kept_raw_to_processed_segments']=mapping
            result['actual_true_timed_and_original_word_mapping']=describe_true_timed_words(m,ns['sent'],values['create'],values['create_timed'],last,mapping,T)
            save(a.output,report)
            pp=dict(profile);pp['_actual_tools']=str(T)
            result['actual_original_PV_and_context']=measure_PV_and_context(m,pcm,expected,result['actual_true_timed_and_original_word_mapping'],mapping,pp)
            require(arrsha(pcm)==expected['S18']['pre_master_PCM_sha256'],'Diagnostic modifiedoriginalsamples')
            require(all(hashlib.sha256(np.ascontiguousarray(values[method][0]).tobytes()).hexdigest()==next(r['unprocessed_array_sha256']for r in expected['mother_reads']if r['method']==method)for method in values),'Observation changed cached mother array')
            report['actual_cached_S18_identity_and_scalar_observation_completed']=True
        finally:
            if saved:
                for k in ['build','title_audio','_auto_level']:setattr(m,k,saved[k])
                m.k.create=saved['k.create'];m.KT.create_timed=saved['KT.create_timed']
            restore_native(native)
            first={}
            for kind,target,value in native:
                key=(kind,id(target))if kind=='cell'else(kind,id(target[0]),target[1])
                if key not in first:first[key]=(kind,target,value)
            native_exact=all((target.cell_contents is value)if kind=='cell'else(getattr(target[0],target[1])is value)for kind,target,value in first.values())
            if saved:native_exact=native_exact and all(getattr(m,k)is saved[k]for k in ['build','title_audio','_auto_level'])and m.k.create is saved['k.create']and m.KT.create_timed is saved['KT.create_timed']
            report['original_native_cells_and_methods_restored']=bool(native_exact)
            sys.modules.pop(name,None)
            for k,value in previous.items():
                sys.modules.pop(k,None)
                if value is not None:sys.modules[k]=value
            del m;gc.collect()
    report['source_namespace_and_environment_restore']=rest


def run(a):
    report={'kind':'source24-onlyS18-two-actual-native-PV-originalcached-true-timed-scalar-not-quality','source_id':'24','book_order':49,'diagnostic_completed':False,'quality_acceptance':False,'formal_acceptance':False,'no_source_CF_gain_or_audio_written':True,'errors':[]}
    T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts';before=None;env_created=False
    try:
        require(digest(a.profile)==PROFILE_SHA,'Exact readonlyprobe profile required');profile=read(a.profile)
        require(len(a.execution_adoption_sha256)==64 and digest(a.execution_adoption)==a.execution_adoption_sha256,'Actualscopefile/fullSHA mandatory')
        validate_adoption(read(a.execution_adoption),digest(__file__),digest(a.profile))
        for name,sp in profile['input_specs'].items():require(digest(a.input_dir/name)==sp['sha256']and(a.input_dir/name).stat().st_size==sp['bytes'],'Wrong immutableprobe input '+name)
        require(digest(a.source)==SOURCE and a.source.resolve()==(a.input_dir/'source.json').resolve(),'Onlycurrent34af source allowed')
        require(all(os.environ.get(k)=='1'for k in FLAGS)and os.environ.get('AUDIO_ONLY')=='1','Originalstrict/keep/audio-only modes required')
        require(not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID']),'No voice/filter/fingerprint overrides')
        require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent,'Originalalias required')
        require(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER,'Actualoriginalmaker required')
        overlay=read(a.input_dir/'overlay18.json');cert=read(a.input_dir/'certificate-b086.json');stamp=read(T/'新管/快测通过.json')
        require(digest(T/'新管/快测通过.json')==profile['actual0e99_stamp_SHA256']and len(stamp['程序'])==110 and cert['passed']is True and cert['overlay_manifest']==overlay and len(overlay['files'])==18,'Genuineactualb08618/0e99110 required')
        require(all(digest(T/Path(r['path']).relative_to('视频/工具'))==r['patch_SHA256']for r in overlay['files']),'Actualoriginal18files changed')
        require(all(digest(T/k)[:16]==v for k,v in stamp['程序'].items()),'Original110 physicalfile stamp mismatch')
        require(digest(T/'发音词典/读音改正.json')==DICT and digest(T/'发音词典/按语境读音.json')==CTX and digest(T/'环境/模型校验码.json')==REGISTRY,'Originaldict/registry mismatch')
        require({n:digest(M/'tts'/n)for n in MODELS}==MODELS and digest(M/'tts/voice_mb.npy')==VOICE,'Actualfixedmodel/voice mismatch')
        identity=read(a.input_dir/'actual-mother-identity.json');api=read(a.input_dir/'actual-mother-cache-API.json')['actions_caches'];require(len(api)==1 and api[0]['key']=='Linux-native24-exact-S18-first-spoken-comma-43702270266'and api[0]['version']=='4b2cb80918783a01e1492bc465a077d0af810af0637e4fdbff5650db20d481f1','Actualfourfile cachekey/version required')
        require(all((C/n).is_file()and not(C/n).is_symlink()and digest(C/n)==h for n,h in identity['actual_four_private_files'].items()),'Wrong actualoldretained targetPKL/markers')
        native_status=read(a.input_dir/'actual-native43757781623-failed-status.json');native_proof=read(a.input_dir/'actual-native43757781623-failed-draft-proof.json')
        require(native_status['passed']is False and isinstance(native_status['request_source_sha256'],dict) and native_status['request_source_sha256']['视频/脚本/24.json']==SOURCE and native_proof['passed']is False and native_proof['internal_pcm_sha256']==profile['expected']['preexisting_whole_WAV_SHA256'],'True failed native source/WAV roles required, not an acceptance claim')
        require([line for line in native_status['failure_details']['public_checker_diagnostics']['做_24/出片后.log']if any(key in line for key in profile['expected']['expected_requested_PV_displayed_keys'])]==profile['expected']['actual_failed_native_requested_PV_lines'],'Only two actual requested original PV rows allowed')
        report['actual_failed_native_evidence']={'status_SHA256':digest(a.input_dir/'actual-native43757781623-failed-status.json'),'draft_proof_SHA256':digest(a.input_dir/'actual-native43757781623-failed-draft-proof.json'),'original_passed':False,'other_GT_and_independent_failure_domains_not_reclassified':True,'actual_requested_PV_stdout_rows':profile['expected']['actual_failed_native_requested_PV_lines']}
        whole=read(a.input_dir/'actual-gainwhole437307-report.json');require(whole['diagnostic_completed']and whole['exact_scope_proved']and whole['phases']['selected_gain_shadow']['actual_complete_WAV']['file_sha256']==profile['expected']['preexisting_whole_WAV_SHA256'],'Actualcurrentwhole evidence required')
        public=T.parent/'配音缓存';require(C.is_dir()and public.is_dir()and(W/'scripts').is_dir(),'Originalnormalprivate/public/source namespaces required')
        inv=lambda directory:{p.name:digest(p)for p in directory.iterdir()if p.is_file()}
        before=inv(C);public_before=inv(public);scripts_before={p.name:p.read_bytes()for p in(W/'scripts').glob('*.json')};work=W/'work_24';inode=work.lstat().st_ino if os.path.lexists(work)else None;wav=digest(work/'a.wav')if(work/'a.wav').is_file()else None
        envdir=W/'环境';env_existed=os.path.lexists(envdir)
        if env_existed:require(digest(envdir/'模型校验码.json')==REGISTRY,'ExistingW registry differs')
        else:envdir.symlink_to(T/'环境',target_is_directory=True);env_created=True
        observe(a,profile,report)
    except BaseException as error:report['errors'].append({'type':type(error).__name__,'detail':str(error)});traceback.print_exc()
    finally:
        try:
            if before is not None:
                if env_created:
                    require((W/'环境').is_symlink()and(W/'环境').resolve()==(T/'环境').resolve(),'Unexpectednew environment alias');(W/'环境').unlink()
                inv=lambda directory:{p.name:digest(p)for p in directory.iterdir()if p.is_file()}
                report['all_private_cache_files_exact_before_after']=inv(C)==before;report['public_repository_cache_exact']=inv(public)==public_before
                report['all_normal_source_scripts_exact']={p.name:p.read_bytes()for p in(W/'scripts').glob('*.json')}==scripts_before
                report['normal_work24_inode_and_WAV_untouched']=(work.lstat().st_ino if os.path.lexists(work)else None)==inode and(digest(work/'a.wav')if(work/'a.wav').is_file()else None)==wav
                report['work_environment_existence_restored']=os.path.lexists(W/'环境')==env_existed
                report['original_runtime_and_dictionary_files_exact_after']=digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER and all(digest(T/Path(r['path']).relative_to('视频/工具'))==r['patch_SHA256']for r in overlay['files'])and digest(T/'发音词典/读音改正.json')==DICT and digest(T/'发音词典/按语境读音.json')==CTX
                keys=['all_private_cache_files_exact_before_after','public_repository_cache_exact','all_normal_source_scripts_exact','normal_work24_inode_and_WAV_untouched','work_environment_existence_restored','original_runtime_and_dictionary_files_exact_after','original_native_cells_and_methods_restored']
                restore=report.get('source_namespace_and_environment_restore',{})
                report['diagnostic_completed']=bool(report.get('actual_cached_S18_identity_and_scalar_observation_completed')and all(report.get(k)is True for k in keys)and restore.get('normal_scripts_namespace_restored')and restore.get('environment_cwd_sys_path_restored'))
        except BaseException as cleanup_error:
            report['diagnostic_completed']=False
            report['errors'].append({'type':type(cleanup_error).__name__,'detail':str(cleanup_error),'stage':'restore-verification'})
            traceback.print_exc()
        save(a.output,report)
    return 0 if report['diagnostic_completed']else 1


def main():
    p=argparse.ArgumentParser()
    for name in ['tools','video-root','profile','source','input-dir','execution-adoption','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--execution-adoption-sha256',required=True)
    return run(p.parse_args())

if __name__=='__main__':sys.exit(main())
