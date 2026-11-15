"""Only S18 old3/new2 cached speech clip scalar observation. No gain selection or quality pass."""
from pathlib import Path
import argparse,ast,contextlib,copy,gc,hashlib,importlib.util,inspect,json,math,os,shutil,sys,tempfile,traceback
sys.dont_write_bytecode=True
SOURCE = '533d34bb3261935549042a5863a1fa4e65c816bbb218964e017bc9867bc72c16'
SHADOW = 'e31e54fddbb46d3b7852891d676655fde985005376e5b93ac0534d685aaca2b2'
BASELINE = 'c8903792176bbbe068af89d4826bfe19376f71bc61a121b065539644caafd834'
MAKER = '0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
ROOT_INTAKE = 'c794ef9d1a0d0876acfa2c83353fea2a45ee7695444613bf67bf84a2d2806c82'
FIXTURE = 'f072ed0438ff2f68357649a57f6aee6cfe2ec4dfcd06569f8ae34ab5b270b3ce'
PROVIDER = '32602bee21b14ed161fdfd3c8b921b267782ad143a49c3ebd256c16c473808f5'
DICT = '5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
CTX = '4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
OLDREG = '91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
REGISTRY = 'dfde6c065a3558b74923ce82865a3b01dae1f839af4456b74de55dc3ff492312'
VOICE = '1f97658bb5a4280cc3f6c01dc644dff471bf57c970fc8b99f3049d6991c4f6c8'
MODELS = {'kokoro-v1.0.onnx':'7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5',
          'kokoro-v1.0-timed.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
          'voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
FLAGS = ('STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS')
DSP_KEYS = ('非人声区间','词尾除阻','除阻加强','停顿插入点','停顿删除区间','停顿处除阻',
            '分段增益dB','段内渐变dB','句子增益dB','分段包络dB','列举逗号','结尾句','合成标点','区间声音指纹','朗读删逗号')
PROFILE_SHA='ca5ae863de6dff795637c9edfbb2b6cf32a4f1732c790586abc6bf7ddee8e2c4'
WHOLE_SHA='f062e84d92fa4d095be81a310cbd6ec6edae5b8755fd3e26d67215dff84434f0'
def require(value, message):
    if not value:
        raise AssertionError(message)

def read(path):
    return json.loads(Path(path).read_text())

def verify_request(request, shadow, history):
    require(str(request.get('no')) == '24' and len(request['sentences']) == 18,
            'Wrong source/sentence count')
    restored = copy.deepcopy(shadow)
    rows = history['retired_entries']
    require(len(rows) == 9, 'Exactly nine old S18 leaves must be retired')
    require(len({tuple(x['JSON_path']) for x in rows}) == 9, 'Duplicate retirement path')
    for row in rows:
        parent = restored
        for key in row['JSON_path'][:-1]:
            parent = parent[key]
        key = row['JSON_path'][-1]
        require(key not in parent, 'Retired old target leaf still active')
        parent[key] = row['exact_old_value']
    require(restored == request, 'Nine-leaf inverse must reconstruct entire immutable request')
    require(request['sentences'] == shadow['sentences'], 'Retirement changed display text')
    require(not shadow.get('结尾句', {}).get('S18'), 'No S18 ENDING is permitted')
    return True

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

def validate_certificate(tools, manifest, certificate):
    require(len(manifest['files']) == 17, 'Expected exact 17 runtime files')
    require(certificate.get('overlay_manifest') == manifest and
            len(certificate.get('source68_code_adoption_SHA256', '')) == 64 and
            len(certificate.get('source35_code_adoption_SHA256', '')) == 64,
            'Actual combined20 certificate must bind this runtime contract and separate68/35 code adoption')
    for row in manifest['files']:
        rel = Path(row['path']).relative_to('视频/工具')
        require(sha(tools / rel) == row['patch_SHA256'], 'Runtime contract mismatch: ' + str(rel))
    stamp_path = tools / '新管/快测通过.json'
    stamp = read(stamp_path)
    require(len(stamp['程序']) == 110 and stamp['程序']['make_video.py'] == MAKER[:16],
            'A new actual 110-program stamp for0e6c4 spoken20 is required')
    require(sha(stamp_path) != '3c251c77fb58b775ae1389a52ce31467686201ba98b842af545f2923357a6c32',
            'Old17 stamp is historical only')
    require(certificate.get('passed') is True and
            certificate.get('original_full_fastcheck_passed') is True and
            certificate.get('new_actual_110_program_stamp_created_after_full_quickcheck') is True and
            certificate.get('real_fastcheck_stamp_SHA256') == sha(stamp_path),
            'Actual new fullquick certificate/stamp mismatch')
    checks = certificate.get('checks', [])
    require(any(x.get('name') == 'original-full-fastcheck' and x.get('exit') == 0 for x in checks),
            'Original fullquick successful execution record missing')
    require(certificate.get('production_audio_or_video_acceptance') is False,
            'Code certificate must not claim article acceptance')
    return sha(stamp_path)

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

def validate_sources(baseline,request,shadow,history):
    verify_request(request,shadow,history)
    require(str(baseline['no'])=='24'and len(baseline['sentences'])==18,'Exact original baseline article18 sentences required')
    plain=lambda d:[' '.join(c['en'].replace('**','').strip()for c in s['chunks'])for s in d['sentences']]
    require(plain(baseline)==plain(request)==plain(shadow),'Visible English text outside approved projection changed')
    require(baseline['title_en']==request['title_en']==shadow['title_en'],'Title model input changed')
    for sid in ['标题']+['S'+str(i)for i in range(1,18)]:
        require(typed(effective_controls(baseline,sid))==typed(effective_controls(shadow,sid)), 'Non-target effective DSP changed: '+sid)
    require(shadow['朗读删逗号']['S18']=={'篇号':24,'原文':'Precision put six ashore within reach of help and, a century on, brought their ship back into view.','逗号序号':[1]},'Exact private target speech schema required')
    return True

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

sha=digest
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


def validate_observation(observed, expected):
    require(typed(observed)==typed(expected['S18']), 'S18 original before/pre-master/clips/tmap/cuts/fingerprint/gains differ from actual f062')
    require(observed['automatic_gain_dB']=={} and observed['manual_gain_dB'] is None,
            'No original target gain may be selected or changed')
    require(expected['actual_piece_gain_dB']==[0.0]*len(observed['actual_pieces']), 'All actual original piece gains must remain zero')
    return True


def summary(np, array, sample_rate):
    require(array.dtype==np.float32 and array.ndim==1 and len(array)>0 and bool(np.all(np.isfinite(array))), 'Original finite float32 clip required')
    magnitude=np.abs(array);i=int(np.argmax(magnitude));rms=float(np.sqrt(np.mean(array.astype(np.float64)**2)))
    return {'samples':len(array),'dtype':str(array.dtype),'shape':[len(array)],
            'PCM_sha256':hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest(),
            'duration_s':len(array)/sample_rate,'absolute_peak':float(magnitude[i]),
            'first_absolute_peak_local_sample':i,'signed_first_peak_value':float(array[i]),
            'samples_at_absolute_peak':int(np.count_nonzero(magnitude==magnitude[i])),
            'RMS_linear':rms,'RMS_dBFS':20*math.log10(rms+1e-20),
            'nonzero_sample_count':int(np.count_nonzero(array))}


def load_original_meter(tools, profile):
    path=tools/'响度一致性核对.py'
    require(digest(path)==profile['meter_module_SHA256'], 'Original loudness meter module differs')
    tree=ast.parse(path.read_text())
    for name,want in profile['original_meter_function_AST_SHA256'].items():
        require(ast_sha(next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name))==want, 'Original meter function AST differs: '+name)
    spec=importlib.util.spec_from_file_location('_original24_S18_observation_meter',path)
    meter=importlib.util.module_from_spec(spec);spec.loader.exec_module(meter)
    require(digest(meter.FF)==profile['original_meter_FFmpeg_SHA256'], 'Original imageio ffmpeg meter binary differs')
    return meter


def original_meter_lufs(np,sf,meter,array,sample_rate,private_parent):
    """Only lossless private FLOAT input to original ebur128 null reader; never production encoding."""
    before=hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest();tdpath=None
    try:
        with tempfile.TemporaryDirectory(prefix='_source24_S18_meter_FLOAT_',dir=private_parent)as td:
            tdpath=Path(td);path=tdpath/'exact-float-clip.wav'
            sf.write(path,array,sample_rate,subtype='FLOAT')
            observed,rate=sf.read(path,dtype='float32');info=sf.info(path)
            require(rate==sample_rate and info.subtype=='FLOAT'and observed.dtype==np.float32 and np.array_equal(observed,array), 'Private FLOAT container must preserve every sample including peaks above1')
            TM=meter.momentary(str(path))
            value=meter.段响度(TM,0.0,len(array)/sample_rate)
            result={'original_meter_gated_LUFS':None if value is None else float(value),
                    'original_meter_function':'unmodified momentary -> 段响度 -> gated; start0/end exact clip duration',
                    'original_momentary_blocks':len(TM),'FLOAT_input_roundtrip_array_exact':True,
                    'temporary_FLOAT_peak_above1_preserved':bool(np.array_equal(observed,array)),
                    'lossy_or_production_audio_video_encoding':False}
    finally:
        if tdpath is not None:require(not tdpath.exists(), 'Private meter PCM directory must be deleted even on failure')
        require(hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()==before,'Meter changed original array')
    result['private_FLOAT_input_removed']=True
    return result


def measure(np,sf,meter,array,sample_rate,old_peak,private_parent):
    before=hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()
    raw=summary(np,array,sample_rate);raw.update(original_meter_lufs(np,sf,meter,array,sample_rate,private_parent))
    # Same original ordered division/multiplication, using ONE actual old whole-master peak for every clip.
    common=array/np.float32(old_peak)*0.89
    require(common.dtype==np.float32,'Original ordered common-master view dtype differs')
    oldbasis=summary(np,common,sample_rate);oldbasis.update(original_meter_lufs(np,sf,meter,common,sample_rate,private_parent))
    require(hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()==before,'Measurement changed original gain callback clip')
    return {'original_pre_master':raw,'one_common_old_whole_master_basis':oldbasis,
            'common_old_master_peak_denominator':old_peak,'ordered_view_formula':'clip / np.float32(actual_old_whole_peak) * 0.89',
            'independent_per_clip_normalization_or_gain_selection':False,'original_clip_bytes_unchanged':True}


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


def observe_phase(label,source_bytes,expected,a,profile,report,meter):
    T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts';state={}
    result={'source_sha256':expected['source_SHA256'],'cached_model_calls':0,'_active_segment':'S18'}
    report['phases'][label]=result
    with environment_and_cwd(W,state),source_namespace(W,source_bytes,state):
        source=W/'scripts/24.json';require(digest(source)==expected['source_SHA256'],'Exact source-first phase bytes required')
        name='_original24_S18_fiveclip_'+label;previous={k:sys.modules.get(k)for k in ['render','title2','clean','出片指纹']}
        for key in previous:sys.modules.pop(key,None)
        require(name not in sys.modules,'Fresh S18 maker namespace required');spec=importlib.util.spec_from_file_location(name,W/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[name]=m
        native=[];saved={};used={};return_arrays=None
        try:
            spec.loader.exec_module(m);m._SPOKEN_SOURCE_NO='24'
            require(digest(inspect.getsourcefile(type(m.k)))==PROVIDER and m._OLDF and digest(m._OLDF)==OLDREG,'Original provider/G72 registry required')
            require(m._cand and digest(m._cand)==DICT and m._CTX_PATH and digest(m._CTX_PATH)==CTX,'Original alias dictionary context required')
            require(digest(M/'tts/AF.txt')==expected['AF_sha256'] and m.AF==expected['AF_expression'],'Original AF bytes/expression required; AF is not applied by this local observer')
            m._REPO_CACHE=str(M/'_source24_S18_public_export_forbidden');require(not Path(m._REPO_CACHE).exists(),'Public cache export sentinel must not exist')
            np,SR=m.np,m.SR;require(SR==24000 and m.SPEED==.95,'Exact source24 SR/speed required')
            data=json.loads(source.read_text());own=[' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in s['chunks'])for s in data['sentences']]
            require(len(own)==18 and all(m.SENT_NO.get(s)=='24'for s in own),'Source-first all18 SENT_NO ownership required')
            logical=m.spoken(own[17]);native=block_original_native(m,W)
            saved={k:getattr(m,k)for k in ['build','title_audio','_auto_level']};saved['k.create']=m.k.create;saved['KT.create_timed']=m.KT.create_timed
            def forbidden(*args,**kw):raise AssertionError('No whole build/title/other sentence/G36/native inference is authorized')
            m.build=m.title_audio=m._auto_level=forbidden
            for method,obj in [('create',m.k),('create_timed',m.KT)]:setattr(obj,method,only_target_wrapper(getattr(obj,method),method,m,expected,C,np,used,result,logical))
            maker_text=(W/'make_video.py').read_text();pre,nodes=original_build_fragments(maker_text)
            require(ast_sha(ast.Module(body=pre,type_ignores=[]))==profile['original_build_prelude_AST_SHA256']and ast_sha(ast.Module(body=nodes,type_ignores=[]))==profile['original_build_target_assembly_AST_SHA256'],'Exact original build target fragment AST required')
            require(ast_sha(ast.parse(inspect.getsource(m.句增益)).body[0])==profile['original_gain_function_AST_SHA256'],'Original gain function AST required')
            gain_original=m.句增益;captured={}
            def observe_gain(data,no,si,sent,pieces,gaps,clips,tmap,audio):
                require(str(no)=='24'and si==17 and sent==own[17],'Only original S18 gain callback allowed')
                captured['before_gain']=audio.copy();captured['pre_clips']=[c.copy()for c in clips];captured['tmap']=copy.deepcopy(tmap)
                value=gain_original(data,no,si,sent,pieces,gaps,clips,tmap,audio);captured['returned']=value
                return value
            ns=dict(m.__dict__);ns.update(d=copy.deepcopy(data),no='24',si=17,s=copy.deepcopy(data['sentences'][17]),句增益=observe_gain)
            exec(compile(ast.Module(body=pre,type_ignores=[]),str(W/'make_video.py')+':original-build-display-prelude','exec'),ns)
            ns['s']=ns['d']['sentences'][17];ns['ch']=ns['s']['chunks']
            exec(compile(ast.Module(body=nodes,type_ignores=[]),str(W/'make_video.py')+':original-build-S18-only-fragment','exec'),ns)
            require('returned'in captured,'Exactly one original S18 gain callback required')
            clips,pcm,auto,manual=captured['returned'];arrsha=lambda v:hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest();before=captured['before_gain'];pieces,gaps=ns['pieces'],ns['gaps'];tmap=ns['tmap']
            observed={'plain_English_sha256':hashlib.sha256(ns['sent'].encode()).hexdigest(),'before_gain_PCM_sha256':arrsha(before),'before_gain_dtype':str(before.dtype),'before_gain_samples':len(before),'pre_master_PCM_sha256':arrsha(pcm),'PCM_dtype':str(pcm.dtype),'samples':len(pcm),'duration_s':len(pcm)/SR,'automatic_gain_dB':{str(k):v for k,v in auto.items()},'manual_gain_dB':manual,'exact_effective_DSP':effective_controls(ns['d'],'S18'),'actual_raw_w_fingerprint':m.SENT_FP.get(ns['sent']),'actual_raw_cuts':[list(x)for x in m.LAST['cuts']],'actual_fades':[list(t)for t in m.LAST.get('fades',[])],'actual_grafts':copy.deepcopy(m.LAST.get('grafts',[])),'actual_head':m.LAST['head'],'actual_internal_hs':m.LAST['hs'],'pre_gain_piece_clips_sha256':[arrsha(v)for v in captured['pre_clips']],'pre_gain_tmap':[list(t)for t in captured['tmap']],'piece_clips_sha256':[arrsha(v)for v in clips],'actual_pieces':[list(t)for t in pieces],'actual_gaps':list(gaps)}
            result['actual_S18_observation_before_hard_assert']=observed;validate_observation(observed,expected)
            require(result['cached_model_calls']==2 and len(result['actual_original_mother_reads_by_segment'])==2,'Exactly two cached S18 mother reads, zero inference required')
            require(typed(list(used.values()))==typed(expected['used_cache']),'Original postpron cache keys/markers/fullPKL must match f062')
            require(len(clips)==2*len(pieces)-1 and len(pieces)==(3 if label=='baseline_current'else 2),'Exactly old3/new2 speech clips required')
            require(np.array_equal(np.concatenate(clips),pcm),'Original all-zero gain PCM must equal exact clips concatenation')
            result['S18_hard_identity_exact_to_actual_f062']=True;result['actual_original_S18_piece_gain_dB']=[auto.get(i+1,0.0)+float((manual or{}).get(str(i+1),0))for i in range(len(pieces))]
            require(result['actual_original_S18_piece_gain_dB']==expected['actual_piece_gain_dB'],'Actual all-zero piece gain map differs')
            result['speech_clips']=[];result['silence_clips']=[]
            for i,v in enumerate(clips):
                if i%2==0:
                    j=i//2;row={'one_based_speech_piece':j+1,'original_clips_index':i,'display_character_span':list(pieces[j]),'actual_display_English':ns['sent'][pieces[j][0]:pieces[j][1]],'actual_local_tmap':list(tmap[j])};row.update(measure(np,m.sf,meter,v,SR,profile['common_old_master_peak'],M));result['speech_clips'].append(row)
                else:
                    row={'original_clips_index':i,'actual_silence_duration_s':len(v)/SR,'requested_build_gap_before_original_sentence_processing':gaps[i//2],**summary(np,v,SR)};result['silence_clips'].append(row)
            require(all(arrsha(v)==h for v,h in zip(clips,expected['S18']['piece_clips_sha256']))and arrsha(pcm)==expected['S18']['pre_master_PCM_sha256'],'Scalar/meter observation changed any original callback array')
            return_arrays={'speech':[clips[2*j].copy()for j in range(len(pieces))],'first_actual_silence':clips[1].copy(),'SR':SR}
            result['original_gain_inputs_and_outputs_byteexact_after_measurement']=True
        finally:
            if saved:
                for key in ['build','title_audio','_auto_level']:setattr(m,key,saved[key])
                m.k.create=saved['k.create'];m.KT.create_timed=saved['KT.create_timed']
            restore_native(native)
            first={}
            for kind,target,value in native:
                key=(kind,id(target))if kind=='cell'else(kind,id(target[0]),target[1])
                if key not in first:first[key]=(kind,target,value)
            native_exact=all((target.cell_contents is value)if kind=='cell'else(getattr(target[0],target[1])is value)for kind,target,value in first.values())
            if saved:native_exact=native_exact and all(getattr(m,k)is saved[k]for k in ['build','title_audio','_auto_level'])and m.k.create is saved['k.create']and m.KT.create_timed is saved['KT.create_timed']
            result['original_methods_native_closures_restored']=bool(native_exact);require(native_exact,'Original methods/native creator closures must restore before namespace removal')
            sys.modules.pop(name,None)
            for key,value in previous.items():
                sys.modules.pop(key,None)
                if value is not None:sys.modules[key]=value
            report['phase_restore'][label]=state
            del m;gc.collect()
    return return_arrays


def run(a):
    report={'kind':'source24_S18_old3_new2_original_clip_scalar_not_gain_selection','source_id':'24','book_order':49,'completed':False,'quality_acceptance':False,'formal_acceptance':False,'gain_or_source_CF_selection_performed':False,'no_whole_build_non_target_inference_G36_ASR_GT_render_or_production_lossy_encoding':True,'private_temporary_meter_FLOAT_PCM_inputs_expected_and_deleted':True,'phases':{},'phase_restore':{},'errors':[]}
    T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts';before=None;envcreated=False
    try:
        require(digest(a.profile)==PROFILE_SHA,'Exact S18 five-clip profile required');profile=read(a.profile)
        for key,want in profile['input_sha256'].items():require(digest(getattr(a,key))==want,'Wrong immutable measurement input: '+key)
        require(digest(a.whole_report)==WHOLE_SHA,'Actual whole f062 required; no new whole build allowed')
        whole=read(a.whole_report);require(whole['diagnostic_completed']and whole['exact_scope_proved'],'Original actual completed whole identity observation required')
        request,shadow,baseline,history=(read(p)for p in[a.request,a.shadow,a.baseline_source,a.history]);validate_sources(baseline,request,shadow,history)
        require(all(os.environ.get(k)=='1'for k in FLAGS)and os.environ.get('AUDIO_ONLY')=='1','Original strict/keep flags must match prior observer')
        require(not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID']),'No voice/AF/old fingerprint overrides')
        require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent,'Original canonical alias required')
        require(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER,'Exact original certified20 producer required');validate_certificate(T,read(a.overlay),read(a.certification))
        require(digest(T/'新管/快测通过.json')=='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41','True original20 stamp required')
        require(digest(T/'发音词典/读音改正.json')==DICT and digest(T/'发音词典/按语境读音.json')==CTX and digest(T/'环境/模型校验码.json')==REGISTRY,'Original dictionary/registry context required')
        require({n:digest(M/'tts'/n)for n in MODELS}==MODELS and digest(M/'tts/voice_mb.npy')==VOICE,'Original full model/voice bytes required')
        fixture=read(a.cache_identity);require(digest(a.cache_identity)==FIXTURE and fixture['request_SHA256']==SOURCE and fixture['shadow_SHA256']==SHADOW and fixture['maker_SHA256']==MAKER,'Actual two-mother fixture required')
        for name,want in fixture['actual_four_private_files'].items():require(digest(C/name)==want,'Actual selected private cache leaf differs')
        save=read(a.cache_save)['actions_caches'];require(len(save)==1 and save[0]['key']=='Linux-native24-exact-S18-first-spoken-comma-43702270266'and save[0]['version']=='4b2cb80918783a01e1492bc465a077d0af810af0637e4fdbff5650db20d481f1','Exact original saved cache paths/version proof required')
        for phase in profile['phases'].values():
            for row in phase['used_cache']:
                p=C/row['name'];require(digest(p)==row['sha256'],'Original actual S18 fullPKL differs');mark=C/(row['name']+'.单线程');require(mark.exists()==('single_thread_marker_sha256'in row),'Original marker presence differs')
                if mark.exists():require(digest(mark)==row['single_thread_marker_sha256']and mark.read_text().strip()==row['single_thread_marker_value'],'Original marker bytes differ')
        meter=load_original_meter(T,profile);public=T.parent/'配音缓存';require(public.is_dir()and C.is_dir()and(W/'scripts').is_dir(),'Original normal namespaces required')
        envdir=W/'环境';envexisted=os.path.lexists(envdir)
        if envdir.exists():require(digest(envdir/'模型校验码.json')==REGISTRY,'Work portable registry before mutation differs')
        inputs={str(getattr(a,k)):v for k,v in profile['input_sha256'].items()};public_before={p.name:digest(p)for p in public.iterdir()if p.is_file()};scripts_before={p.name:p.read_bytes()for p in(W/'scripts').glob('*.json')};work=W/'work_24';workinode=work.lstat().st_ino if os.path.lexists(work)else None;wav=digest(work/'a.wav')if(work/'a.wav').is_file()else None;before={p.name:digest(p)for p in C.iterdir()if p.is_file()}
        if not envdir.exists():envdir.symlink_to(T/'环境',target_is_directory=True);envcreated=True
        arrays={}
        for label,source in [('baseline_current',a.baseline_source),('selected_private_shadow',a.shadow)]:arrays[label]=observe_phase(label,source.read_bytes(),profile['phases'][label],a,profile,report,meter)
        import numpy as np
        import soundfile as sf
        old,new=arrays['baseline_current'],arrays['selected_private_shadow'];require(old['SR']==new['SR']==24000,'Original rate required')
        union=np.concatenate(old['speech'][:2]);span=np.concatenate([old['speech'][0],old['first_actual_silence'],old['speech'][1]])
        report['first_content_comparison']={'old_first_two_speech_union_without_gap':measure(np,sf,meter,union,24000,profile['common_old_master_peak'],M),'old_first_two_span_including_actual_first_gap':measure(np,sf,meter,span,24000,profile['common_old_master_peak'],M),'old_first_gap_samples':len(old['first_actual_silence']),'old_first_gap_seconds':len(old['first_actual_silence'])/24000,'new_first_piece_measurement_reference':'phases.selected_private_shadow.speech_clips[0]','old_union_excludes_gap_and_no_resynthesis_or_production_audio_created':True}
        report['same_tail_comparison']={'old_piece3_reference':'phases.baseline_current.speech_clips[2]','new_piece2_reference':'phases.selected_private_shadow.speech_clips[1]','both_common_basis_uses_actual_old_whole_peak':profile['common_old_master_peak'],'no_independent_piece_normalization_or_gain_choice':True}
        report['completed']=True
    except BaseException as e:
        report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc()
    finally:
        if before is not None:
            if envcreated:
                require((W/'环境').is_symlink()and(W/'环境').resolve()==(T/'环境').resolve(),'Unexpected new work env link');(W/'环境').unlink()
            report['all_existing_private_cache_full_bytes_unchanged']={p.name:digest(p)for p in C.iterdir()if p.is_file()}==before
            report['public_repository_cache_bytes_unchanged']={p.name:digest(p)for p in public.iterdir()if p.is_file()}==public_before
            report['all_immutable_inputs_bytes_unchanged']=all(digest(p)==v for p,v in inputs.items())
            report['normal_all_source_scripts_bytes_unchanged']={p.name:p.read_bytes()for p in(W/'scripts').glob('*.json')}==scripts_before
            report['normal_work24_inode_and_WAV_untouched']=(work.lstat().st_ino if os.path.lexists(work)else None)==workinode and(digest(work/'a.wav')if(work/'a.wav').is_file()else None)==wav
            report['work_environment_existence_restored']=os.path.lexists(W/'环境')==envexisted
            report['original_runtime_models_voice_dictionaries_exact_after']=(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER and all(digest(T/Path(r['path']).relative_to('视频/工具'))==r['patch_SHA256']for r in read(a.overlay)['files'])and {n:digest(M/'tts'/n)for n in MODELS}==MODELS and digest(M/'tts/voice_mb.npy')==VOICE and digest(T/'发音词典/读音改正.json')==DICT and digest(T/'发音词典/按语境读音.json')==CTX)
            report['both_source_namespace_env_restored']=len(report['phase_restore'])==2 and all(x.get('normal_scripts_namespace_restored')and x.get('environment_cwd_sys_path_restored')for x in report['phase_restore'].values())
            report['all_private_meter_temp_containers_removed']=not list(M.glob('_source24_S18_meter_FLOAT_*'))
            report['completed']=bool(report['completed']and all(report[k]for k in ['all_existing_private_cache_full_bytes_unchanged','public_repository_cache_bytes_unchanged','all_immutable_inputs_bytes_unchanged','normal_all_source_scripts_bytes_unchanged','normal_work24_inode_and_WAV_untouched','work_environment_existence_restored','original_runtime_models_voice_dictionaries_exact_after','both_source_namespace_env_restored','all_private_meter_temp_containers_removed']))
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    return 0 if report['completed']else 1


def main():
    p=argparse.ArgumentParser()
    for name in ['tools','video-root','profile','request','shadow','history','GEN','MD','baseline-source','baseline-reference','cache-identity','cache-save','mother-report','root-intake','overlay','certification','whole-report','diagnosis-H','original-profile','output']:p.add_argument('--'+name,type=Path,required=True)
    return run(p.parse_args())


if __name__=='__main__':sys.exit(main())
