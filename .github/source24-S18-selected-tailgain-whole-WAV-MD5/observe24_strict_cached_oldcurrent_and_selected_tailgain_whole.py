"""Source24 two-phase original AUDIO_ONLY observation; no quality acceptance.

Code preparation only until root adopts this complete helper. Every actual model
method is cache-only; new synthesis and all G36 mathematics are hard forbidden.
"""
from pathlib import Path
import argparse, ast, contextlib, copy, gc, hashlib, importlib.util, inspect
import json, math, os, shutil, subprocess, sys, tempfile, traceback
from fractions import Fraction
sys.dont_write_bytecode = True
SOURCE = '533d34bb3261935549042a5863a1fa4e65c816bbb218964e017bc9867bc72c16'
SHADOW = 'e31e54fddbb46d3b7852891d676655fde985005376e5b93ac0534d685aaca2b2'
BASELINE = 'c8903792176bbbe068af89d4826bfe19376f71bc61a121b065539644caafd834'
MAKER = '0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
PROFILE_SHA = '118272fb1aa93b2d73f6946d313de3e09003ea5935e537bc7e5bf218b604321f'
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

def command(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def actual_aac(path):
    """Hash copied ADTS plus exact rational timestamp/payload/priming projection. Never rebase PTS."""
    raw = json.loads(command(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_streams', '-show_packets', '-show_data_hash', 'sha256', '-of', 'json', str(path)]))
    require(len(raw.get('streams', [])) == 1, f'No unique actual audio stream: {path}')
    stream = raw['streams'][0]; require(stream['codec_name'] == 'aac', f'Expected copied AAC: {path}')
    timebase = Fraction(stream['time_base']); packets = []
    for pkt in raw['packets']:
        timing = []
        for key in ('pts', 'dts', 'duration'):
            require(key in pkt, f'Cannot prove exact packet {key}: {path}')
            value = int(pkt[key]) * timebase
            timing.append([value.numerator, value.denominator])
        side = [{k: s[k] for k in sorted(s) if k != 'side_data_size'} for s in pkt.get('side_data_list', [])]
        require(pkt.get('data_hash'), f'No actual packet payload hash: {path}')
        packets.append({'timing_rationals': timing, 'size': int(pkt['size']), 'payload_sha256': pkt['data_hash'], 'side_data': side})
    codec = {k: stream.get(k) for k in ('codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout')}
    projection = {'codec': codec, 'packets': packets}
    encoded = json.dumps(projection, sort_keys=True, separators=(',', ':')).encode()
    with tempfile.TemporaryDirectory(prefix='actual-aac-') as td:
        adts = Path(td) / 'audio.aac'
        command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-vn', '-c:a', 'copy', '-f', 'adts', str(adts)])
        return {'aac_adts_sha256': digest(adts), 'packet_projection_sha256': hashlib.sha256(encoded).hexdigest(),
                'packet_count': len(packets), 'projection': projection}

sha = digest


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


def premaster_peak_metadata(np, raw_parts, waves, positions, pre, peak, sample_rate, target_segment):
    """Read only the exact original audio-list/callback arrays; export scalars."""
    def summary(array, start):
        magnitude=np.abs(array)
        local=int(np.argmax(magnitude)) if len(array) else None
        maximum=float(magnitude[local]) if local is not None else 0.0
        return {'samples':len(array),'dtype':str(array.dtype),'absolute_peak':maximum,
                'first_peak_local_sample':local,
                'first_peak_global_sample':start+local if local is not None else None,
                'first_peak_global_seconds':(start+local)/sample_rate if local is not None else None,
                'signed_first_peak_sample_value':float(array[local]) if local is not None else None,
                'samples_at_this_absolute_peak':int(np.count_nonzero(magnitude==maximum)),
                'contains_actual_whole_peak':bool(local is not None and maximum==peak)}
    segments=[]
    for sid,(lo,hi) in positions.items():
        row={'segment':sid,'start_sample':lo,'end_sample_exclusive':hi}
        row.update(summary(waves[sid],lo));segments.append(row)
    parts=[];cursor=0
    for index,part in enumerate(raw_parts):
        names=[sid for sid,pcm in waves.items() if part is pcm]
        row={'original_audio_list_index':index,'callback_segments_by_object_identity':names,
             'start_sample':cursor,'end_sample_exclusive':cursor+len(part),
             'part_role':'actual_callback_segment' if names else 'unmapped_original_audio_list_part'}
        row.update(summary(part,cursor));parts.append(row);cursor+=len(part)
    first=int(np.argmax(np.abs(pre))) if len(pre) else None
    owning_parts=[r for r in parts if first is not None and r['start_sample']<=first<r['end_sample_exclusive']]
    non_target=[r for r in segments if r['segment']!=target_segment]
    peak_non_target=max((r['absolute_peak'] for r in non_target),default=0.0)
    return {'kind':'read_only_actual_original_pre_master_audio_list_peak_ownership',
            'original_whole_pre_master_absolute_peak':peak,'target_segment':target_segment,
            'non_target_callback_count':len(non_target),
            'whole_first_absolute_peak_sample':first,
            'whole_first_absolute_peak_seconds':first/sample_rate if first is not None else None,
            'whole_first_peak_signed_sample_value':float(pre[first]) if first is not None else None,
            'whole_first_peak_owning_original_parts':owning_parts,
            'all_original_parts_tied_at_whole_absolute_peak':[r for r in parts if r['contains_actual_whole_peak']],
            'all_callback_segments_tied_at_whole_absolute_peak':[r['segment'] for r in segments if r['contains_actual_whole_peak']],
            'all_non_target_callback_absolute_peak':peak_non_target,
            'all_non_target_callback_peak_segments':[r['segment'] for r in non_target if r['absolute_peak']==peak_non_target],
            'actual_callback_segment_peaks':segments,'every_original_audio_list_part_peaks':parts,
            'original_audio_list_total_samples':cursor,
            'metadata_only_no_gain_or_DSP_or_normalization_selected':True}


def observe_phase(label,input_bytes,expected_source,a,profile,report,scratch,arrays,wavarrays):
    T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts';work=W/'work_24'
    require(not work.exists()and not work.is_symlink(),'Phase must start with no old working audio')
    state={};name='_original24_strict_whole_'+label
    with environment_and_cwd(W,state),source_namespace(W,input_bytes,state):
        source=W/'scripts/24.json';require(digest(source)==expected_source,'Source-first exact bytes required')
        previous_modules={k:sys.modules.get(k)for k in ['render','title2','clean','出片指纹']}
        for key in previous_modules:sys.modules.pop(key,None)
        require(name not in sys.modules,'Fresh module namespace required')
        spec=importlib.util.spec_from_file_location(name,W/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[name]=m
        sf_original=None;native_originals=[];observed={};waves={};before_waves={};used={};result={'source_sha256':expected_source,'observed_sentences':{},'cached_model_calls':0}
        report['phases'][label]=result
        try:
            spec.loader.exec_module(m);m._SPOKEN_SOURCE_NO='24'
            require(digest(inspect.getsourcefile(type(m.k)))==PROVIDER,'Original provider32602 required')
            require(m._OLDF and digest(m._OLDF)==OLDREG,'Original G72 registry required')
            require(m._cand and digest(m._cand)==DICT and m._CTX_PATH and digest(m._CTX_PATH)==CTX,'Actual original dictionary context missing')
            m._REPO_CACHE=str(M/'forbid-source24-observer-public-export');require(not Path(m._REPO_CACHE).exists(),'Public export sentinel already exists')
            np,SR=m.np,m.SR;require(SR==24000 and m.SPEED==.95,'Original24 speed/sample rate required')
            current=json.loads(source.read_text())
            own=[' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in s['chunks'])for s in current['sentences']]
            require(all(m.SENT_NO.get(s)=='24'for s in own),'Installed source-first SENT_NO must own all18 sentences')
            result.update(actual_own18_SENT_NO=[m.SENT_NO.get(s)for s in own],AF_sha256=digest(M/'tts/AF.txt'),AF_expression=m.AF,original_speed=m.SPEED)
            native_originals=block_original_native(m,W)
            for method,obj,model in [('create',m.k,'kokoro-v1.0.onnx'),('create_timed',m.KT,'kokoro-v1.0-timed.onnx')]:
                setattr(obj,method,strict_cached_guard(m,np,C,method,model,getattr(obj,method),used,result))
            def no_math(*a,**kw):raise AssertionError('Source24 never authorizes _auto_level/G36 in this observer')
            m._auto_level=no_math
            gain_original,title_original,sentence_original,sf_original=m.句增益,m.title_audio,m.sentence_audio,m.sf.write
            def array_sha(array):return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()
            def observe_title(title):
                result['_active_segment']='title'
                try:
                    value=title_original(title);waves['title']=value;before_waves['title']=value.copy();return value
                finally:result['_active_segment']=None
            def observe_sentence(sent,pieces,gaps):
                matches=[i for i,x in enumerate(own)if x==sent]
                require(len(matches)==1,'Actual sentence must have one source-local segment')
                result['_active_segment']='S'+str(matches[0]+1)
                try:return sentence_original(sent,pieces,gaps)
                finally:result['_active_segment']=None
            def observe_gain(data,no,si,sent,pieces,gaps,clips,tmap,audio):
                sid='S'+str(si+1);before_waves[sid]=audio.copy()
                pre_clips=[array_sha(x)for x in clips];pre_times=copy.deepcopy(tmap)
                value=gain_original(data,no,si,sent,pieces,gaps,clips,tmap,audio)
                clips_after,pcm,auto,manual=value;require(auto=={},'Source24 G36 must remain inactive')
                waves[sid]=pcm
                result['observed_sentences'][sid]={
                    'plain_English_sha256':hashlib.sha256(sent.encode()).hexdigest(),
                    'before_gain_PCM_sha256':array_sha(before_waves[sid]),'before_gain_dtype':str(before_waves[sid].dtype),'before_gain_samples':len(before_waves[sid]),
                    'pre_master_PCM_sha256':array_sha(pcm),'PCM_dtype':str(pcm.dtype),'samples':len(pcm),'duration_s':len(pcm)/SR,
                    'automatic_gain_dB':{str(k):v for k,v in auto.items()},'manual_gain_dB':manual,
                    'exact_effective_DSP':effective_controls(data,sid),'actual_raw_w_fingerprint':m.SENT_FP.get(sent),
                    'actual_raw_cuts':[list(x)for x in m.LAST['cuts']],'actual_fades':copy.deepcopy(m.LAST.get('fades',[])),
                    'actual_grafts':copy.deepcopy(m.LAST.get('grafts',[])),'actual_head':m.LAST['head'],'actual_internal_hs':m.LAST['hs'],
                    'pre_gain_piece_clips_sha256':pre_clips,'pre_gain_tmap':pre_times,
                    'piece_clips_sha256':[array_sha(x)for x in clips_after],'actual_pieces':list(pieces),'actual_gaps':list(gaps)}
                return value
            def observe_write(path,actual_mastered,rate,*aa,**kw):
                if Path(path)==Path('work_24/a.wav'):
                    frame=inspect.currentframe().f_back
                    require(frame.f_code is m.build.__code__ and rate==SR,'Original build/sf.write frame required')
                    raw_parts=frame.f_locals['audio'];pre=np.concatenate(raw_parts);peak=float(np.max(np.abs(pre)))
                    actual_formula=pre/np.abs(pre).max()*.89
                    require(np.array_equal(actual_mastered,actual_formula),'Original ordered normalization differs')
                    require(set(waves)=={'title'}|{'S'+str(i)for i in range(1,19)},'Exactly title+18 actual sentence callbacks required')
                    cursor=0;positions={}
                    for part in raw_parts:
                        for sid,pcm in waves.items():
                            if part is pcm:require(sid not in positions,'Duplicate part identity');positions[sid]=(cursor,cursor+len(pcm))
                        cursor+=len(part)
                    require(len(positions)==19 and cursor==len(pre),'Original build audio-list identity incomplete')
                    result['actual_original_pre_master_peak_ownership_metadata']=premaster_peak_metadata(np,raw_parts,waves,positions,pre,peak,SR,'S18')
                    result['title_pre_master_PCM_sha256']=array_sha(waves['title'])
                    result['actual_original_mastering']={'pre_master_full_PCM_sha256':array_sha(pre),'pre_master_dtype':str(pre.dtype),'pre_master_samples':len(pre),
                        'pre_master_absolute_peak':peak,'logical_normalization_scale':.89/peak,'observed_normalized_full_PCM_sha256':array_sha(actual_mastered),
                        'actual_maker_formula':'A = concatenate(actual audio list); A = A / abs(A).max() * 0.89','original_ordered_formula_exact_to_sf_write_argument':True,
                        'source_of_raw_parts':'actual original build frame audio list, not guessed reconstruction'}
                    result['actual_sample_clock']={}
                    for sid,(lo,hi)in positions.items():
                        view=actual_mastered[lo:hi]
                        result['actual_sample_clock'][sid]={'start_sample':lo,'end_sample_exclusive':hi,'start_s':lo/SR,'end_s':hi/SR,
                            'observed_post_master_float_PCM_sha256':array_sha(view),'observed_post_master_RMS_dBFS':20*math.log10(float(np.sqrt(np.mean(view.astype(float)**2)))+1e-20)}
                    arrays[label]={'before_gain':before_waves,'pre_master':waves}
                return sf_original(path,actual_mastered,rate,*aa,**kw)
            m.title_audio,m.sentence_audio,m.句增益,m.sf.write=observe_title,observe_sentence,observe_gain,observe_write
            output=scratch/(label+'-actual-original-canonical.m4a')
            m.build(str(source),str(output))
            require(digest(source)==expected_source and (work/'a.wav').is_file(),'Original phase output/source missing')
            require('actual_original_mastering'in result,'Original sf.write observation missing')
            inf=m.sf.info(work/'a.wav');require(inf.samplerate==SR and inf.channels==1 and inf.subtype=='PCM_16','Original actual WAV format changed')
            result['actual_complete_WAV']={'file_sha256':digest(work/'a.wav'),'file_bytes':(work/'a.wav').stat().st_size,'sample_rate':SR,'samples':inf.frames,'duration_s':inf.frames/SR,'subtype':inf.subtype,
                'file_md5':hashlib.md5((work/'a.wav').read_bytes()).hexdigest(),
                'file_md5_first12':hashlib.md5((work/'a.wav').read_bytes()).hexdigest()[:12]}
            aac=actual_aac(output)
            result['actual_complete_AAC']={k:v for k,v in aac.items()if k!='projection'}
            result['actual_complete_AAC']['codec']=aac['projection']['codec']
            wavarrays[label]={}
            with m.sf.SoundFile(work/'a.wav')as wav:
                for sid,clock in result['actual_sample_clock'].items():
                    wav.seek(clock['start_sample']);v=wav.read(clock['end_sample_exclusive']-clock['start_sample'],dtype='int16')
                    wavarrays[label][sid]=v;clock['actual_WAV_PCM16_segment_sha256']=array_sha(v)
            result['actual_voice_fingerprint_table']=json.loads((work/'句子声音指纹.json').read_text())
            result['actual_original_piece_time_table']=json.loads((work/'分段.json').read_text())
            require(not result['actual_voice_fingerprint_table']['作废'],'No A45 invalidation/override authorized')
            require(not list(work.glob('*.png')),'AUDIO_ONLY must render no pictures')
            if label=='baseline_current':
                ref=json.loads(a.baseline_reference.read_text())
                require(result['actual_complete_WAV']['file_sha256']==ref['RAW_SHA256'],'Baseline current fullWAV not actual3c7')
                for k in ['aac_adts_sha256','packet_count','packet_projection_sha256']:
                    require(result['actual_complete_AAC'][k]==ref[k],'Baseline current AAC/count/absolute-clock differs: '+k)
                result['actual_current_identity_matches_original_native43543967031']=True
            result['actual_used_cache_scalar_only']=list(used.values())
            destination=scratch/(label+'-private-original-work24');require(not destination.exists(),'Private phase work already exists');work.rename(destination)
            result['private_work_not_artifacted']=True
        finally:
            if sf_original is not None:m.sf.write=sf_original
            restore_native(native_originals)
            sys.modules.pop(name,None)
            for key,value in previous_modules.items():
                sys.modules.pop(key,None)
                if value is not None:sys.modules[key]=value
            report['phase_restore'][label]=state
            del m;gc.collect()



SELECTED_TAIL_GAIN_DB = -1.109697858091752

def validate_selected_gain_shadow(request, historical_shadow, selected, history):
    verify_request(request, historical_shadow, history)
    require('分段增益dB' not in historical_shadow, 'Historical shadow unexpectedly contains gain')
    require(typed(selected.get('分段增益dB')) == typed({'S18': {'2': SELECTED_TAIL_GAIN_DB}}),
            'Only exact original legal S18 speech piece2 manual gain is authorized')
    inverse = copy.deepcopy(selected)
    inverse.pop('分段增益dB')
    require(typed(inverse) == typed(historical_shadow), 'Selected gain escapes one-leaf inverse')
    require(selected['sentences'] == historical_shadow['sentences'], 'Gain changed text')
    require(not selected.get('句子增益dB', {}).get('S18'), 'Sentence gain is forbidden')
    return True

def validate_selected_gain_GEN(path, selected):
    tree = ast.parse(Path(path).read_text())
    get = lambda key: next(n.value for n in tree.body if isinstance(n, ast.Assign) and
        any(isinstance(t, ast.Name) and t.id == key for t in n.targets))
    sentences, data = ast.literal_eval(get('S')), ast.literal_eval(get('out'))
    require(data.get('sentences') == [], 'Pure original S/out GEN required')
    for para, chunks in sentences:
        current_chunks = []
        for chunk in chunks:
            align = [list(pair) for pair in chunk[0]]
            row = {'en': ' '.join(en for en, zh in align if en != '\n'),
                   'zh': ''.join(zh for en, zh in align), 'align': align}
            if len(chunk) > 1:
                row['note'] = chunk[1]
            current_chunks.append(row)
        data['sentences'].append({'para': para, 'chunks': current_chunks})
    require(typed(data) == typed(selected), 'Selected S/out GEN entire JSON differs')
    return True

def require_original_target_raw_scope_and_selected_gain(report, historical_whole):
    # Only scalar comparisons. Original model/gain/mastering callbacks are unchanged.
    old = report['phases']['baseline_current']['observed_sentences']['S18']
    new = report['phases']['selected_gain_shadow']['observed_sentences']['S18']
    prior_old = historical_whole['phases']['baseline_current']['observed_sentences']['S18']
    prior_new = historical_whole['phases']['selected_private_shadow']['observed_sentences']['S18']
    wire = lambda value: json.loads(json.dumps(value, default=lambda x: x.item()))
    require(typed(wire(old)) == typed(prior_old), 'Baseline original S18 entire scalar row changed')
    unchanged_fields = ('plain_English_sha256', 'before_gain_PCM_sha256', 'before_gain_dtype',
        'before_gain_samples', 'PCM_dtype', 'samples', 'duration_s', 'actual_raw_w_fingerprint',
        'actual_raw_cuts', 'actual_fades', 'actual_grafts', 'actual_head', 'actual_internal_hs',
        'pre_gain_piece_clips_sha256', 'pre_gain_tmap', 'actual_pieces', 'actual_gaps')
    for field in unchanged_fields:
        require(typed(wire(new[field])) == typed(prior_new[field]),
                'Selected original S18 source/raw/pre-gain metadata changed: ' + field)
    require(new['automatic_gain_dB'] == {} and
            typed(new['manual_gain_dB']) == typed({'2': SELECTED_TAIL_GAIN_DB}),
            'Original selected gain callback did not return exactly piece2-only manual gain')
    require(len(new['piece_clips_sha256']) == 3, 'Selected S18 requires original speech/gap/speech')
    require(new['piece_clips_sha256'][:2] == prior_new['piece_clips_sha256'][:2],
            'Selected first speech or original digital silence changed')
    require(new['piece_clips_sha256'][2] != prior_new['piece_clips_sha256'][2],
            'Authorized second speech gain was not applied')
    actual_controls = copy.deepcopy(new['exact_effective_DSP'])
    require(typed(actual_controls.pop('分段增益dB')) == typed({'2': SELECTED_TAIL_GAIN_DB}),
            'Selected effective piece2 gain differs')
    require(typed(actual_controls) == typed(prior_new['exact_effective_DSP']),
            'Selected S18 effective DSP escaped one manual piece gain')
    for phase, previous in [('baseline_current', 'baseline_current'),
                            ('selected_gain_shadow', 'selected_private_shadow')]:
        reads = [x for x in report['phases'][phase]['actual_original_mother_reads_by_segment'] if x['segment'] == 'S18']
        old_reads = [x for x in historical_whole['phases'][previous]['actual_original_mother_reads_by_segment'] if x['segment'] == 'S18']
        require(typed(reads) == typed(old_reads), 'Historical actual S18 mothers/arrays/keys changed: ' + phase)
    require(report['actual_master_coefficient_ratio_new_over_old'] == 1.0,
            'Selected real whole master coefficient must remain exactly1')
    require(report['all_title_and17_non_target_actual_mastered_WAV_PCM16_exact'],
            'All non-target actual output PCM16 must remain sample-exact')
    for sid in ['title'] + ['S' + str(i) for i in range(1, 18)]:
        old_clock = report['phases']['baseline_current']['actual_sample_clock'][sid]
        new_clock = report['phases']['selected_gain_shadow']['actual_sample_clock'][sid]
        require(old_clock['observed_post_master_float_PCM_sha256'] == new_clock['observed_post_master_float_PCM_sha256'],
                'Non-target actual post-master float differs: ' + sid)
    report['actual_new_gain_scope_firstspeech_and_gap_exact_tail2_only'] = True
    report['all_title_and17_non_target_actual_post_master_float_exact'] = True
    report['historical_fixture_source_shadow_roles_preserved_not_rewritten'] = True
    return True


def run(a):
    report={'kind':'source24_original_STRICT_selected_one_tailpiece_gain_two_phase_whole_observer_not_quality_acceptance','source_id':'24','book_order':49,
            'diagnostic_completed':False,'exact_scope_proved':False,'quality_acceptance':False,'formal_acceptance':False,
            'source_request_GEN_MD_not_changed':True,'private_shadow_is_not_final_source_or_CF_selection':True,
            'no_TTS_GT_ASR_or_picture_render_authorized':True,'no_G36_or_STRICT_relaxation_authorized':True,
            'phases':{},'phase_restore':{},'errors':[]}
    T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts'
    before=None;input_pins=None;work=W/'work_24';envcreated=False;env_was_present=None;work_isolated=False;arrays={};wavarrays={}
    scratch=M/'_source24_STRICT_selected_tailgain_two_phase_original_whole_observation'
    prior_work=scratch/'preexisting-original-work24-inode'
    try:
        require(digest(a.profile)==PROFILE_SHA,'Whole observer immutable input profile differs')
        profile=json.loads(a.profile.read_text())
        for label,want in profile['input_sha256'].items():require(digest(getattr(a,label))==want,'Wrong frozen input: '+label)
        require(digest(a.root_intake)==ROOT_INTAKE and digest(a.cache_identity)==FIXTURE,'Actual root two-mother/save intake required')
        require(digest(a.request)==SOURCE and digest(a.shadow)==SHADOW and digest(a.baseline_source)==BASELINE,'Exact three source roles required')
        request,shadow,baseline,history=(json.loads(p.read_text())for p in [a.request,a.shadow,a.baseline_source,a.history])
        validate_sources(baseline,request,shadow,history)
        selected_gain = read(a.gain_shadow)
        validate_selected_gain_shadow(request,shadow,selected_gain,history)
        validate_selected_gain_GEN(a.gain_GEN,selected_gain)
        gain_adoption = read(a.root_gain)
        require(gain_adoption['source_id']=='24' and gain_adoption['book_order']==49 and typed(gain_adoption['selected_original_source_field'])==typed({'分段增益dB':{'S18':{'2':SELECTED_TAIL_GAIN_DB}}}) and gain_adoption['actual_measurement_complete_not_quality'] is True and gain_adoption['first_piece_gain_unchanged'] is True and gain_adoption['sentence_gain_not_added'] is True,'Actual ROOT exact piece2 selection required')
        require(gain_adoption['measurement']['sha256']==digest(a.five_clip_report),'Root-selected actual five-clip measurement differs')
        report['actual_gain_adoption_sha256'] = digest(a.root_gain)
        report['historical_request_shadow_actual_fixture_roles'] = {'request':SOURCE,'shadow':SHADOW,'fixture':FIXTURE}
        report['selected_gain_shadow_sha256'] = digest(a.gain_shadow)
        require(all(os.environ.get(k)=='1'for k in FLAGS)and os.environ.get('AUDIO_ONLY')=='1','Whole observation requires all original strict/keep/AUDIO_ONLY flags')
        require(not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID']),'Voice/AF/A45 overrides forbidden')
        require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent,'Original canonical alias required')
        require(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER,'Exact certified20 producer required')
        validate_certificate(T,json.loads(a.overlay.read_text()),json.loads(a.certification.read_text()))
        require(digest(T/'新管/快测通过.json')=='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41','Actual20 stamp7d7 required')
        require(digest(T/'发音词典/读音改正.json')==DICT and digest(T/'发音词典/按语境读音.json')==CTX,'Original dictionaries required')
        require(digest(T/'环境/模型校验码.json')==REGISTRY,'Original portable registry required')
        require({n:digest(M/'tts'/n)for n in MODELS}==MODELS and digest(M/'tts/voice_mb.npy')==VOICE,'Actual full original model/voice bytes required')
        fixture=json.loads(a.cache_identity.read_text());require(fixture['request_SHA256']==SOURCE and fixture['shadow_SHA256']==SHADOW and fixture['maker_SHA256']==MAKER,'Actual target fixture scope differs')
        require(len(fixture['actual_four_private_files'])==4,'Exactly four actual restored private leaves required')
        for name,want in fixture['actual_four_private_files'].items():require(digest(C/name)==want,'Actual target private file differs: '+name)
        saveproof=json.loads(a.cache_save.read_text())['actions_caches'];require(len(saveproof)==1 and saveproof[0]['key']=='Linux-native24-exact-S18-first-spoken-comma-43702270266'and saveproof[0]['version']=='4b2cb80918783a01e1492bc465a077d0af810af0637e4fdbff5650db20d481f1','Actual saved cache key/path version proof differs')
        require(not scratch.exists(),'Use fresh native diagnostic namespace')
        require(C.is_dir()and (W/'scripts').is_dir(),'Original native private cache and scripts directories required')
        public=T.parent/'配音缓存';require(public.is_dir(),'Original public registry/cache directory required')
        envdir=W/'环境'
        env_was_present=os.path.lexists(envdir)
        if envdir.exists():require(digest(envdir/'模型校验码.json')==REGISTRY,'Work portable registry must match before mutation')
        public_before={p.name:digest(p)for p in public.iterdir()if p.is_file()}
        input_pins={str(getattr(a,k)):v for k,v in profile['input_sha256'].items()}
        scripts_before={p.name:p.read_bytes()for p in (W/'scripts').glob('*.json')}
        work_inode=work.lstat().st_ino if os.path.lexists(work)else None
        work_wav=digest(work/'a.wav')if (work/'a.wav').is_file()else None
        before={p.name:digest(p)for p in C.iterdir()if p.is_file()}
        scratch.mkdir()
        if os.path.lexists(work):work.rename(prior_work)
        work_isolated=True
        if not envdir.exists():envdir.symlink_to(T/'环境',target_is_directory=True);envcreated=True
        require(digest(envdir/'模型校验码.json')==REGISTRY,'Work portable registry must match')
        observe_phase('baseline_current',a.baseline_source.read_bytes(),BASELINE,a,profile,report,scratch,arrays,wavarrays)
        observe_phase('selected_gain_shadow',a.gain_shadow.read_bytes(),profile['input_sha256']['gain_shadow'],a,profile,report,scratch,arrays,wavarrays)
        import numpy as np
        compared=[]
        for sid in ['title']+['S'+str(i)for i in range(1,18)]:
            row={'segment':sid}
            for stage in ['before_gain','pre_master']:
                x,y=arrays['baseline_current'][stage][sid],arrays['selected_gain_shadow'][stage][sid]
                row[stage+'_samples_exact']=x.dtype==y.dtype and x.shape==y.shape and bool(np.array_equal(x,y))
                row[stage+'_old_SHA256']=hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
                row[stage+'_new_SHA256']=hashlib.sha256(np.ascontiguousarray(y).tobytes()).hexdigest()
            x,y=wavarrays['baseline_current'][sid],wavarrays['selected_gain_shadow'][sid]
            row['actual_mastered_WAV_PCM16_samples_exact']=x.dtype==y.dtype and x.shape==y.shape and bool(np.array_equal(x,y))
            row['old_samples'],row['new_samples']=len(x),len(y)
            oldreads=[x for x in report['phases']['baseline_current']['actual_original_mother_reads_by_segment']if x['segment']==sid]
            newreads=[x for x in report['phases']['selected_gain_shadow']['actual_original_mother_reads_by_segment']if x['segment']==sid]
            row['actual_original_mother_cache_keys_fullPKL_and_unprocessed_arrays_exact']=bool(oldreads)and typed(oldreads)==typed(newreads)
            if sid!='title':row['effective_DSP_types_exact']=typed(report['phases']['baseline_current']['observed_sentences'][sid]['exact_effective_DSP'])==typed(report['phases']['selected_gain_shadow']['observed_sentences'][sid]['exact_effective_DSP'])
            compared.append(row)
        report['title_and17_non_target_actual_PCM_scope']=compared
        require(all(r['before_gain_samples_exact']and r['pre_master_samples_exact']and r['actual_original_mother_cache_keys_fullPKL_and_unprocessed_arrays_exact']and r.get('effective_DSP_types_exact',True)for r in compared),'A non-target actual PCM/effective-DSP scope differs')
        report['all_title_and17_non_target_before_and_after_gain_PCM_exact']=True
        report['all_title_and17_non_target_actual_mastered_WAV_PCM16_exact']=all(r['actual_mastered_WAV_PCM16_samples_exact']for r in compared)
        report['actual_master_coefficient_ratio_new_over_old']=report['phases']['selected_gain_shadow']['actual_original_mastering']['logical_normalization_scale']/report['phases']['baseline_current']['actual_original_mastering']['logical_normalization_scale']
        report['target_S18_before_after_gain_samples_changed']=not np.array_equal(arrays['baseline_current']['pre_master']['S18'],arrays['selected_gain_shadow']['pre_master']['S18'])
        require_original_target_raw_scope_and_selected_gain(report,read(a.prior_whole))
        fixture=json.loads(a.cache_identity.read_text());used={x['name']:x for x in report['phases']['selected_gain_shadow']['actual_used_cache_scalar_only']}
        for row in fixture['actual_inputs']:
            require(row['exact_native_cache_key']in used and used[row['exact_native_cache_key']]['sha256']==fixture['actual_four_private_files'][row['exact_native_cache_key']],'Actual selected new mother was not read exactly')
        report['diagnostic_completed']=True
    except BaseException as e:
        report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc()
    finally:
        if before is not None:
            if prior_work.exists()or prior_work.is_symlink():
                if work.exists()or work.is_symlink():
                    failure=scratch/'incomplete-private-work24';require(not failure.exists(),'Failure work collision');work.rename(failure)
                prior_work.rename(work)
            elif work_isolated and(work.exists()or work.is_symlink()):
                failure=scratch/'incomplete-private-work24';require(not failure.exists(),'Failure work collision');work.rename(failure)
            if env_was_present is False and os.path.lexists(W/'环境'):
                require((W/'环境').is_symlink()and (W/'环境').resolve()==(T/'环境').resolve(),'Unexpected new environment entry; do not unlink')
                (W/'环境').unlink()
            after={p.name:digest(p)for p in C.iterdir()if p.is_file()}
            report['all_existing_private_cache_files_exact_before_after']=before==after
            report['public_repository_cache_exact']={p.name:digest(p)for p in public.iterdir()if p.is_file()}==public_before
            report['immutable_input_bytes_exact']=all(digest(p)==v for p,v in input_pins.items())
            report['normal_all_source_scripts_exact']={p.name:p.read_bytes()for p in (W/'scripts').glob('*.json')}==scripts_before
            report['normal_work24_original_inode_restored']=(work.lstat().st_ino if os.path.lexists(work)else None)==work_inode
            report['normal_preexisting_work24_WAV_exact']=(digest(work/'a.wav')if (work/'a.wav').is_file()else None)==work_wav
            report['original_producer_T_W_fullSHA_exact']=digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER
            report['original17_runtime_models_voice_and_dictionaries_exact_after']=(all(digest(T/Path(row['path']).relative_to('视频/工具'))==row['patch_SHA256']for row in json.loads(a.overlay.read_text())['files'])and {n:digest(M/'tts'/n)for n in MODELS}==MODELS and digest(M/'tts/voice_mb.npy')==VOICE and digest(T/'发音词典/读音改正.json')==DICT and digest(T/'发音词典/按语境读音.json')==CTX)
            report['both_phase_source_namespace_environment_restorations_true']=len(report['phase_restore'])==2 and all(x.get('normal_scripts_namespace_restored')and x.get('environment_cwd_sys_path_restored')for x in report['phase_restore'].values())
            report['exact_scope_proved']=bool(report['diagnostic_completed']and all(report[k]for k in ['all_existing_private_cache_files_exact_before_after','public_repository_cache_exact','immutable_input_bytes_exact','normal_all_source_scripts_exact','normal_work24_original_inode_restored','normal_preexisting_work24_WAV_exact','original_producer_T_W_fullSHA_exact','original17_runtime_models_voice_and_dictionaries_exact_after','both_phase_source_namespace_environment_restorations_true']))
        report['formal_original_full_gates_2ASR_sourceQA_and_finalV3_still_required']=True
        report['raw_WAV_PCM_GT_models_private_cache_or_AAC_not_exported']=True
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    return 0 if report['exact_scope_proved']else 1


def main():
    p=argparse.ArgumentParser()
    for name in ['tools','video-root','profile','request','shadow','history','GEN','MD','baseline-source','baseline-reference','cache-identity','cache-save','mother-report','root-intake','overlay','certification','gain-shadow','gain-GEN','root-gain','prior-whole','five-clip-report','output']:
        p.add_argument('--'+name,type=Path,required=True)
    return run(p.parse_args())


if __name__=='__main__':sys.exit(main())
