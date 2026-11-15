"""Two source-first original AUDIO_ONLY observations; scalar evidence, never formal QA.

No native model method may run. Existing model/cache bytes are pinned. Only the
selected target's exact original G36 mathematics may create one missing JSON when
explicitly allowed by the separate source-specific root execution adoption.
"""
from pathlib import Path
from fractions import Fraction
import argparse, ast, contextlib, copy, gc, hashlib, importlib.util, inspect, json
import math, os, re, shutil, subprocess, sys, tempfile, traceback
sys.dont_write_bytecode = True
SOURCE_NO = '35'
BOOK_ORDER = 54
TARGET = 'S15'
COUNT = 21
PROFILE_SHA256 = '7e5cb923c53fba859718e37d254f39c26dfd348cecb86e007339f19a3884fb85'
MAKER_SHA256 = '0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
CERTIFICATE_SHA256 = '50a3abb8d8388ba4587eed0baab4eed5b57afad9fc73cbdb1aa4b48bbaa56c01'
STAMP_SHA256 = '7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41'
OVERLAY_SHA256 = '4b8f093bfe6bf48c0933b457007cb006f33a00450a718c10c1faa9961294b73d'
REGISTRY_SHA256 = 'dfde6c065a3558b74923ce82865a3b01dae1f839af4456b74de55dc3ff492312'
DICT_SHA256 = '5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
CTX_SHA256 = '4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
OLD_REGISTRY_SHA256 = '91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
AUDIO_KEYS = ['非人声区间','词尾除阻','停顿处除阻','除阻加强','停顿删除区间','停顿插入点',
              '区间声音指纹','分段增益dB','句子增益dB','段内渐变dB','结尾句','合成标点','列举逗号']
phase_arrays, phase_post_arrays, phase_int16_arrays = {}, {}, {}
CACHE = None

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def json_digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()

def audio_metadata(path):
    streams = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    packet = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_packets',
        '-show_entries', 'packet=pts,dts,duration,pts_time,dts_time,duration_time,size,flags,side_data_list',
        '-of', 'json', str(path)]))['packets']
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                             '-c:a', 'copy', '-f', 'adts', '-'], check=True, capture_output=True)
    return {'file_sha256': digest(path), 'file_bytes': path.stat().st_size,
            'AAC_ADTS_sha256': hashlib.sha256(result.stdout).hexdigest(),
            'AAC_ADTS_bytes': len(result.stdout), 'packet_count': len(packet),
            'full_actual_packet_clock_metadata_sha256': json_digest(packet),
            'first_packet': packet[0] if packet else None,
            'last_packet': packet[-1] if packet else None,
            'sum_packet_duration_units': sum(int(p.get('duration', 0)) for p in packet),
            'audio_streams': [s for s in streams['streams'] if s['codec_type'] == 'audio'],
            'format_duration_s': streams['format'].get('duration'),
            'actual_original_AudioOnly_canonical_2s_tail_not_final_06_image_card_audio': True}

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

def require(value, message):
    if not value: raise AssertionError(message)

def command(argv):
    return subprocess.check_output([str(x) for x in argv])

def inventory(directory):
    return {p.name: digest(p) for p in Path(directory).iterdir() if p.is_file()}

def typed(value):
    if isinstance(value, dict): return ('dict', tuple((k, typed(v)) for k,v in value.items()))
    if isinstance(value, list): return ('list', tuple(typed(v) for v in value))
    return (type(value).__name__, value)

def dsp(data, sid):
    return {k: copy.deepcopy(data.get(k, {}).get(sid) if isinstance(data.get(k, {}), dict)
                             else data.get(k)) for k in AUDIO_KEYS}

def validate_adoption(value, helper_sha, intake_sha, allow_math):
    require(not str(value.get('kind','')).startswith('TEMPLATE') and value.get('this_template_grants_execution') is not False, 'A preparation template is not a root execution adoption')
    required = {'source_id': SOURCE_NO, 'book_order': BOOK_ORDER, 'target_sentence': TARGET,
                'helper_sha256': helper_sha, 'profile_sha256': PROFILE_SHA256,
                'strict_cached_whole_two_phase_authorized': True,
                'actual_two_mother_intake_sha256': intake_sha,
                'only_selected_target_original_math_if_missing_authorized': allow_math,
                'new_target_or_non_target_TTS_authorized': False}
    require(all(type(value.get(k)) is type(v) and value.get(k) == v for k,v in required.items()),
            'Exact separate whole-observer root adoption fields required')

def bind_inputs(folder, profile):
    result = {}
    for role, row in profile['inputs'].items():
        rel = Path(row['file'])
        require(not rel.is_absolute() and '..' not in rel.parts, 'Input path outside frozen inputs')
        p = Path(folder) / rel
        require(p.is_file() and p.stat().st_size == row['bytes'] and digest(p) == row['sha256'],
                'Wrong frozen input: ' + role)
        result[role] = p
    return result

def block_native(module, support, events):
    """Disable real cached native closure endpoints and both opposite object methods."""
    cells = []
    def forbidden(*a, **kw):
        events.append('forbidden_original_native_method_entry')
        raise AssertionError('No target or non-target original model inference is authorized')
    for obj, method in ((module.k,'create'), (module.KT,'create_timed')):
        outer = getattr(obj, method)
        cached = support.closure_cell(outer, 'fn').cell_contents
        native_cell = support.closure_cell(cached, 'fn')
        cells.append((native_cell, native_cell.cell_contents)); native_cell.cell_contents = forbidden
    opposite = [(module.k,'create_timed',module.k.create_timed),
                (module.KT,'create',module.KT.create)]
    for obj, name, old in opposite: setattr(obj, name, forbidden)
    def restore():
        for cell, original in cells: cell.cell_contents = original
        for obj, name, original in opposite: setattr(obj, name, original)
    return restore

def strict_cached_guard(module, np, cache, method, model_name, outer, used, result):
    def guarded(text, voice, speed=1.0, lang='en-us', **kw):
        captured = []
        def capture(actual_text, voice, speed=1.0, lang='en-us', **actual_kw):
            mid = module._portable_mid(str(cache.parent / model_name))
            voice_id = hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
            key = hashlib.sha1(repr((method, mid, actual_text, voice_id, float(speed),
                                    lang, sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
            path = cache/key
            require(path.is_file(), 'STRICT_CACHED_PORTABLE_KEY_MISSING ' + key)
            module._条目核对(str(path))
            item = {'name':key,'sha256':digest(path),'method':method,
                    'actual_model_input_sha256':hashlib.sha256(actual_text.encode()).hexdigest()}
            marker = cache/(key+'.单线程')
            if marker.exists():
                item['single_thread_marker_sha256']=digest(marker)
                item['single_thread_marker_value']=marker.read_text().strip()
            captured.append(item)
        module._pron(capture)(text, voice=voice, speed=speed, lang=lang, **kw)
        require(len(captured)==1, 'Original pronunciation cache-key capture ABI')
        used[captured[0]['name']] = captured[0]
        result['cached_model_calls'] += 1
        return outer(text, voice=voice, speed=speed, lang=lang, **kw)
    return guarded

def auto_key(module, clips, tmap, gaps, no):
    """Evaluate only the original pinned _k expression; never synthesize or recalculate levels."""
    import 响度一致性核对 as LQ
    groups=[[0]]
    for k2 in range(1,len(tmap)):
        if gaps[k2-1] >= LQ.IN_GAP: groups.append([k2])
        else: groups[-1].append(k2)
    if len(groups)<2: return None
    tree=ast.parse(inspect.getsource(module._auto_level))
    nodes=[n for n in tree.body[0].body if isinstance(n,ast.Assign)
           and any(isinstance(t,ast.Name) and t.id=='_k' for t in n.targets)]
    require(len(nodes)==1, 'Original G51 key assignment ABI')
    expression=ast.Expression(body=nodes[0].value)
    return eval(compile(expression,'<pinned-original-G51-key>','eval'),
                {'np':module.np,'_hl':module._hl,'_短起':module._短起},
                {'clips':clips,'tmap':tmap,'gaps':gaps,'no':no})

def math_guard(module, original, phase, state, profile, result, new_math):
    def observed(clips, tmap, gaps, no='', rounds=2):
        require(str(no)==SOURCE_NO and rounds==2, 'Original source/rounds changed')
        # Inspect the original function, not this observational wrapper, for its exact key expression.
        current=module._auto_level; module._auto_level=original
        try: key=auto_key(module,clips,tmap,gaps,no)
        finally: module._auto_level=current
        sid=state.get('sid')
        if phase=='selected' and sid==TARGET:
            require(profile['allow_selected_target_G36_math'] is True, 'Single-piece selected target must not call G36')
        row={'sentence':sid,'phase':phase,'original_key':key,'source_no':str(no),
             'clip_SHA256':[hashlib.sha256(module.np.ascontiguousarray(x).tobytes()).hexdigest() for x in clips],
             'clip_samples':[len(x) for x in clips], 'gaps':list(gaps),
             'original_tmap':copy.deepcopy(tmap), 'original_rounds':rounds,
             'actual_math_created':False}
        if key is None:
            value=original(clips,tmap,gaps,no,rounds)
            require(value=={}, 'Original one-group empty gain return changed')
            row['value']=value; result['original_G36_calls'].append(row); return value
        name='调平_'+key+'.json'; path=CACHE/name; existed=path.is_file()
        row.update({'file':name,'existed':existed})
        if not existed:
            require(phase=='selected' and sid==TARGET and profile['allow_selected_target_G36_math'] is True,
                    'Missing non-target or baseline G36 must stay strict: '+name)
            require(not new_math, 'At most one actual new target G36 JSON may be derived')
            require(os.environ.get('STRICT_CACHE')=='1', 'Math enters from original strict mode')
            os.environ.pop('STRICT_CACHE')
            try: value=original(clips,tmap,gaps,no,rounds)
            finally: os.environ['STRICT_CACHE']='1'
            require(path.is_file(), 'Original target G36 did not write its actual normal-cache key')
            row['actual_math_created']=True
            new_math[name]={'sha256':digest(path),'value':json.loads(path.read_text()),
                            'source_id':SOURCE_NO,'target_sentence':TARGET,'strict_readback_exact':False}
            require(typed(value)==typed(original(clips,tmap,gaps,no,rounds)), 'New target G36 strict readback changed')
            new_math[name]['strict_readback_exact']=True
        else:
            value=original(clips,tmap,gaps,no,rounds)
        row.update({'sha256':digest(path),'value':value,'strict_after':os.environ.get('STRICT_CACHE')=='1'})
        result['original_G36_calls'].append(row)
        return value
    return observed

@contextlib.contextmanager
def work_namespace(work, scratch, restoration):
    existed=os.path.lexists(work); inode=work.lstat().st_ino if existed else None
    prior_pcm=digest(work/'a.wav') if (work/'a.wav').is_file() else None
    backup=scratch/'normal-preexisting-work-inode'; moved=False
    try:
        if existed: os.replace(work,backup); moved=True
        yield
    finally:
        if os.path.lexists(work):
            destination=scratch/'incomplete-private-work'
            require(not os.path.lexists(destination), 'Private failed-work namespace collision')
            os.replace(work,destination)
        if moved: os.replace(backup,work)
        require(os.path.lexists(work)==existed, 'Normal work existence changed')
        if existed: require(work.lstat().st_ino==inode, 'Normal work inode changed')
        require((digest(work/'a.wav') if (work/'a.wav').is_file() else None)==prior_pcm,
                'Normal prior complete PCM changed')
        restoration['normal_work_inode_and_PCM_restored']=True

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


def run_phase(label, input_bytes, expected_source, paths, support, profile, report, used, new_math):
    gc.collect()
    T,M,W=paths['T'],paths['M'],paths['W']; source=W/('scripts/'+SOURCE_NO+'.json')
    work=W/('work_'+SOURCE_NO); scratch=paths['scratch']
    source.write_bytes(input_bytes); require(digest(source)==expected_source,'Phase source installation mismatch')
    for name in ('render','title2','clean','出片指纹'): sys.modules.pop(name,None)
    module_name='_original_'+SOURCE_NO+'_strict_whole_'+label
    require(module_name not in sys.modules,'Fresh per-phase maker module required')
    spec=importlib.util.spec_from_file_location(module_name,W/'make_video.py')
    m=importlib.util.module_from_spec(spec); sys.modules[module_name]=m
    restore_native=None; sf_true=None
    try:
        spec.loader.exec_module(m)
        m._SPOKEN_SOURCE_NO=SOURCE_NO
        require(Path(m._CACHE).resolve()==CACHE.resolve(),'Observed normal cache is not the actual original cache path')
        require(m._OLDF and digest(m._OLDF)==OLD_REGISTRY_SHA256,'Original G72 registry mismatch')
        require(m._CTX_PATH and digest(m._CTX_PATH)==CTX_SHA256 and digest(m._cand)==DICT_SHA256,
                'Source-first fresh maker loaded wrong dictionary context')
        require(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER_SHA256,'Maker bytes changed')
        m._REPO_CACHE=str(M/('forbid-original-whole-'+SOURCE_NO+'-public-cache-export'))
        require(not Path(m._REPO_CACHE).exists(),'Private output sentinel already exists')
        np,SR=m.np,m.SR; current=json.loads(source.read_text())
        own=[' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip() for c in s['chunks'])
             for s in current['sentences']]
        require(all(str(m.SENT_NO.get(s))==SOURCE_NO for s in own),'Own per-phase sentence source context differs')
        result={'source_sha256':expected_source,'sample_rate':SR,'original_speed':m.SPEED,
                'AF_sha256':digest(M/'tts/AF.txt'),'AF_expression':m.AF,
                'actual_own_sentence_source_numbers':[m.SENT_NO.get(s)for s in own],
                'observed_sentences':{},'cached_model_calls':0,'original_G36_calls':[]}
        report['phases'][label]=result; waves={}
        restore_native=block_native(m,support,report['forbidden_model_events'])
        for method,obj,model in [('create',m.k,'kokoro-v1.0.onnx'),('create_timed',m.KT,'kokoro-v1.0-timed.onnx')]:
            setattr(obj,method,strict_cached_guard(m,np,CACHE,method,model,getattr(obj,method),used,result))
        auto_original=m._auto_level; state={'sid':None}
        m._auto_level=math_guard(m,auto_original,label,state,profile,result,new_math)
        gain_original,title_original,sf_true=m.句增益,m.title_audio,m.sf.write
        def actual_original_sf_output(path,actual_mastered,rate,*a,**kw):
            if Path(path)==Path('work_'+SOURCE_NO+'/a.wav'):
                phase_post_arrays[label]=np.ascontiguousarray(actual_mastered).copy()
            return sf_true(path,actual_mastered,rate,*a,**kw)
        sf_original=actual_original_sf_output
        def array_sha(array):
                return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()

        def observe_title(title):
                value = title_original(title)
                waves['title'] = value
                return value

        def observe_gain(data, no, si, sent, pieces, gaps, clips, tmap, audio):
                value = gain_original(data, no, si, sent, pieces, gaps, clips, tmap, audio)
                clips_after, pcm, auto, manual = value
                sid = 'S'+str(si+1)
                waves[sid] = pcm
                result['observed_sentences'][sid] = {
                    'plain_English_sha256': hashlib.sha256(sent.encode()).hexdigest(),
                    'pre_master_PCM_sha256': array_sha(pcm), 'PCM_dtype': str(pcm.dtype),
                    'samples': len(pcm), 'duration_s': len(pcm)/SR,
                    'automatic_gain_dB': {str(k): v for k,v in auto.items()},
                    'manual_gain_dB': manual, 'actual_raw_w_fingerprint': m.SENT_FP.get(sent),
                    'actual_raw_cuts': [list(x) for x in m.LAST['cuts']],
                    'piece_clips_sha256': [array_sha(x) for x in clips_after],
                }
                return value

        def observe_write(path, actual_mastered, rate, *a, **kw):
                if Path(path) == Path('work_35/a.wav'):
                    frame = inspect.currentframe().f_back
                    assert frame.f_code is m.build.__code__ and rate == SR
                    raw_parts = frame.f_locals['audio']
                    pre = np.concatenate(raw_parts)
                    peak = float(np.max(np.abs(pre)))
                    actual_formula = pre/np.abs(pre).max()*.89
                    assert np.array_equal(actual_mastered, actual_formula), 'Original maker normalization differs.'
                    assert len(waves) == 22 and set(waves) == {'title'}|{'S'+str(i) for i in range(1,22)}
                    cursor, positions = 0, {}
                    for part in raw_parts:
                        for sid, pcm in waves.items():
                            if part is pcm:
                                assert sid not in positions
                                positions[sid] = (cursor, cursor+len(pcm))
                        cursor += len(part)
                    assert len(positions) == 22 and cursor == len(pre)
                    result['actual_original_pre_master_peak_ownership_metadata']=premaster_peak_metadata(np,raw_parts,waves,positions,pre,peak,SR,'S15')
                    result['title_pre_master_PCM_sha256'] = array_sha(waves['title'])
                    result['actual_original_mastering'] = {
                        'pre_master_full_PCM_sha256': array_sha(pre), 'pre_master_dtype': str(pre.dtype),
                        'pre_master_samples': len(pre), 'pre_master_absolute_peak': peak,
                        'actual_maker_formula': 'A = concatenate(actual audio list); A = A / abs(A).max() * 0.89',
                        'logical_normalization_scale': .89/peak,
                        'observed_normalized_full_PCM_sha256': array_sha(actual_mastered),
                        'observed_normalized_absolute_peak': float(np.max(np.abs(actual_mastered))),
                        'original_ordered_formula_exact_to_sf_write_argument': True,
                        'source_of_raw_parts': 'actual original build frame audio list, not a guessed reconstruction',
                    }
                    result['actual_sample_clock'] = {}
                    for sid, (lo, hi) in positions.items():
                        view = actual_mastered[lo:hi]
                        result['actual_sample_clock'][sid] = {
                            'start_sample': lo, 'end_sample_exclusive': hi,
                            'start_s': lo/SR, 'end_s': hi/SR,
                            'observed_post_master_float_PCM_sha256': array_sha(view),
                            'observed_post_master_RMS_dBFS': 20*math.log10(float(np.sqrt(np.mean(view.astype(float)**2)))+1e-20),
                        }
                    phase_arrays[label] = waves
                return sf_original(path, actual_mastered, rate, *a, **kw)
        def gain_scope(*a,**kw):
            state['sid']='S'+str(a[2]+1)
            try: return observe_gain(*a,**kw)
            finally: state['sid']=None
        m.title_audio,m.句增益,m.sf.write=observe_title,gain_scope,observe_write
        output_audio=scratch/(label+'-actual-original-canonical.m4a')
        try: m.build(str(source),str(output_audio))
        finally: m.sf.write=sf_true; m._auto_level=auto_original
        require(digest(source)==expected_source,'Original build changed private source bytes')
        require('actual_original_mastering' in result,'Original whole audio write not observed')
        value,sr=m.sf.read(work/'a.wav'); actual16,sr16=m.sf.read(work/'a.wav',dtype='int16')
        require(sr==sr16==SR and len(value)==result['actual_original_mastering']['pre_master_samples'],
                'Actual complete WAV clock mismatch')
        phase_int16_arrays[label]=actual16
        result['actual_complete_WAV']={'file_sha256':digest(work/'a.wav'),'file_bytes':(work/'a.wav').stat().st_size,
            'sample_rate':sr,'samples':len(value),'duration_s':len(value)/sr,'subtype':m.sf.info(work/'a.wav').subtype}
        result['actual_complete_AAC']=audio_metadata(output_audio)
        packet_evidence=actual_aac(output_audio)
        result['actual_codec_packet_payload_side_and_absolute_clock']={k:v for k,v in packet_evidence.items() if k!='projection'}
        result['actual_voice_fingerprint_table']=json.loads((work/'句子声音指纹.json').read_text())
        result['actual_original_piece_time_table']=json.loads((work/'分段.json').read_text())
        require(not result['actual_voice_fingerprint_table']['作废'],'No old-scope invalidation is permitted')
        for sid,row in result['observed_sentences'].items():row['effective_source_DSP']=dsp(current,sid)
        require(not any(work.glob('*.png')),'A picture was unexpectedly rendered')
        result['no_picture_rendered']=True
        if label=='baseline':
            expected=profile['baseline_audio']
            require(result['actual_complete_WAV']['file_sha256']==expected['WAV_sha256'],'Baseline whole WAV differs from real prior native')
            for k in ('aac_adts_sha256','packet_projection_sha256','packet_count'):
                require(packet_evidence[k]==expected[k],'Baseline native AAC/absolute clock mismatch: '+k)
            result['actual_prior_native_WAV_AAC_and_entire_clock_reproduced']=True
        else:
            target_calls=[r for r in result['original_G36_calls']if r['sentence']==TARGET]
            require((profile['allow_selected_target_G36_math'] and len(target_calls)==1) or (not profile['allow_selected_target_G36_math'] and not target_calls),
                    'Selected target original G36 call count differs from preserved punctuation plan')
            for row in profile['new_target_cache_inputs']:
                require(row['name']in used and used[row['name']]['sha256']==row['sha256'],
                        'Selected target did not actually read both new original mother keys')
        target=scratch/(label+'-private-original-work'+SOURCE_NO)
        require(not target.exists(),'Private phase destination already exists'); os.replace(work,target)
        result['private_work_preserved_path']=str(target)
    finally:
        try:
            if sf_true is not None: m.sf.write=sf_true
            if restore_native is not None: restore_native()
        finally:
            sys.modules.pop(module_name,None)
            del m; gc.collect()

def compare_phases(profile,report):
    import numpy as np
    unchanged=['title']+['S'+str(i)for i in range(1,COUNT+1)if 'S'+str(i)!=TARGET]
    checks=[];old=report['phases']['baseline'];new=report['phases']['selected']
    for sid in unchanged:
        a,b=phase_arrays['baseline'][sid],phase_arrays['selected'][sid]
        pre=a.dtype==b.dtype and a.shape==b.shape and bool(np.array_equal(a,b))
        ac,bc=old['actual_sample_clock'][sid],new['actual_sample_clock'][sid]
        x=phase_post_arrays['baseline'][ac['start_sample']:ac['end_sample_exclusive']]
        y=phase_post_arrays['selected'][bc['start_sample']:bc['end_sample_exclusive']]
        u=phase_int16_arrays['baseline'][ac['start_sample']:ac['end_sample_exclusive']]
        v=phase_int16_arrays['selected'][bc['start_sample']:bc['end_sample_exclusive']]
        post=x.dtype==y.dtype and x.shape==y.shape and bool(np.array_equal(x,y))
        pcm16=u.dtype==v.dtype and u.shape==v.shape and bool(np.array_equal(u,v))
        effective=True if sid=='title' else typed(old['observed_sentences'][sid]['effective_source_DSP'])==typed(new['observed_sentences'][sid]['effective_source_DSP'])
        row={'segment':sid,'pre_master_array_exact':pre,'effective_source_DSP_exact':effective,
             'post_master_float_array_exact':post,'actual_WAV_PCM16_array_exact':pcm16,
             'baseline_pre_SHA256':hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest(),
             'selected_pre_SHA256':hashlib.sha256(np.ascontiguousarray(b).tobytes()).hexdigest(),
             'baseline_post_SHA256':hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest(),
             'selected_post_SHA256':hashlib.sha256(np.ascontiguousarray(y).tobytes()).hexdigest(),
             'baseline_PCM16_SHA256':hashlib.sha256(np.ascontiguousarray(u).tobytes()).hexdigest(),
             'selected_PCM16_SHA256':hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest(),
             'baseline_clock':ac,'selected_clock':bc}
        checks.append(row)
    report['all_non_target_title_and_sentence_identity']=checks
    report['all_non_target_pre_master_and_effective_DSP_exact']=all(x['pre_master_array_exact'] and x['effective_source_DSP_exact']for x in checks)
    report['all_non_target_post_master_float_and_PCM16_exact']=all(x['post_master_float_array_exact'] and x['actual_WAV_PCM16_array_exact']for x in checks)
    report['actual_global_master_scale_ratio_selected_over_baseline']=new['actual_original_mastering']['logical_normalization_scale']/old['actual_original_mastering']['logical_normalization_scale']
    require(report['all_non_target_pre_master_and_effective_DSP_exact'],'A non-target original waveform or effective DSP changed')
    require(report['all_non_target_post_master_float_and_PCM16_exact'],'Non-target mastered samples changed; retain actual ratio and fail scope')
    report['target_pre_master_array_changed']=not np.array_equal(phase_arrays['baseline'][TARGET],phase_arrays['selected'][TARGET])

def main():
    global CACHE
    p=argparse.ArgumentParser()
    for key in ('tools','video-root','inputs','profile','execution-adoption','output','cache-path-output'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--execution-adoption-sha256',required=True)
    a=p.parse_args();T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';CACHE=M/'tts/cache_tts'
    report={'kind':'source'+SOURCE_NO+'_actual_original_strict_cached_two_phase_whole_scalar_observation',
        'source_id':SOURCE_NO,'book_order':BOOK_ORDER,'target_sentence':TARGET,'quality_acceptance':False,
        'formal_acceptance':False,'production_delivery_eligible':False,'diagnostic_completed':False,
        'exact_scope_proved':False,'no_new_TTS_authorized':True,'forbidden_model_events':[],
        'phases':{},'errors':[],'restoration':{},'immutable_owner_source_GEN_MD_or_CF_written':False,
        'per_phase_W_script_is_private_temporary_source_and_restored':True}
    before=None;public_before=None;inputs=None;profile=None;scratch=None;new_math={};used={};support=None
    try:
        require(digest(a.profile)==PROFILE_SHA256,'Wrong source-specific frozen whole profile')
        profile=json.loads(a.profile.read_text());require(profile['source_id']==SOURCE_NO and profile['target_sentence']==TARGET,'Wrong profile source scope')
        inputs=bind_inputs(a.inputs,profile)
        require(digest(a.execution_adoption)==a.execution_adoption_sha256 and len(a.execution_adoption_sha256)==64,'Separate actual root adoption SHA must be literal-pinned')
        validate_adoption(json.loads(a.execution_adoption.read_text()),digest(__file__),profile['inputs']['mother_intake']['sha256'],profile['allow_selected_target_G36_math'])
        require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent,'Original canonical ROOT alias differs')
        require(not a.output.resolve().is_relative_to(M),'Only safe scalar output outside private machine')
        require(all(os.environ.get(k)=='1'for k in ['STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']),'Original strict reviewed modes required')
        require(not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID']),'Unapproved voice/filter/old-scope override')
        require(digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER_SHA256,'Exact spoken20 maker required')
        require(digest(T/'发音词典/读音改正.json')==DICT_SHA256 and digest(T/'发音词典/按语境读音.json')==CTX_SHA256,'Original dictionary context differs')
        require(digest(T/'环境/模型校验码.json')==digest(W/'环境/模型校验码.json')==REGISTRY_SHA256,'Original portable registry differs')
        ms=importlib.util.spec_from_file_location('_whole_'+SOURCE_NO+'_existing_mother_scope',inputs['mother_helper'])
        support=importlib.util.module_from_spec(ms);ms.loader.exec_module(support)
        require(support.SOURCE_NO==SOURCE_NO and support.TARGET==TARGET,'Wrong original target helper')
        support.validate_certificate(T,json.loads(inputs['overlay'].read_text()),json.loads(inputs['certificate'].read_text()))
        identity=json.loads(inputs['identity'].read_text());root=json.loads(inputs['mother_intake'].read_text())
        require(root['source_id']==SOURCE_NO and root['target_sentence']==TARGET and root['actual_private_cache_key']==profile['actual_mother_private_cache_key'] and root['actual_private_cache_version']==profile['actual_mother_private_cache_version'],'Wrong actual mother intake/cache provenance')
        require(identity['request_SHA256']==profile['inputs']['source']['sha256'] and identity['shadow_SHA256']==profile['inputs']['shadow']['sha256'] and identity['maker_SHA256']==MAKER_SHA256 and identity['actual_new_code_certificate_SHA256']==CERTIFICATE_SHA256 and identity['actual_new_110_stamp_SHA256']==STAMP_SHA256,'Actual mother fixture source/code roles differ')
        baseline_status=json.loads(inputs['baseline_status'].read_text())
        require(baseline_status.get('passed') is True and baseline_status.get('canonical_pipeline_passed') is True and baseline_status['final_wav_sha256']==profile['baseline_audio']['WAV_sha256'] and baseline_status['canonical_aac_adts_sha256']==profile['baseline_audio']['aac_adts_sha256'],'Actual prior native baseline status and audio roles differ')
        require(identity['actual_four_private_files']==profile['actual_four_private_files'],'Wrong exact selected private mother fixture')
        require(all(digest(CACHE/name)==h for name,h in profile['actual_four_private_files'].items()),'New mother/marker fullSHA mismatch')
        require({k:digest(M/'tts'/k)for k in identity['models_SHA256']}==identity['models_SHA256'] and digest(M/'tts/voice_mb.npy')==identity['voice_SHA256'],'Original actual model/voice fullSHA mismatch')
        owner,selected=json.loads(inputs['source'].read_text()),json.loads(inputs['shadow'].read_text())
        baseline=json.loads(inputs['baseline'].read_text());history=json.loads(inputs['history'].read_text())
        support.verify_request(owner,selected,history)
        require(all(str(x['no'])==SOURCE_NO and len(x['sentences'])==COUNT for x in [owner,selected,baseline]),'Wrong actual baseline/request sentence scope')
        require(baseline['title_en']==selected['title_en'],'Non-target title changed')
        bare=lambda d:[' '.join(re.sub(r'\*\*|\{\{.*?\}\}','',c['en']).strip()for c in s['chunks'])for s in d['sentences']]
        require(bare(baseline)==bare(selected),'Display English changed outside exact spoken schema')
        require(all(typed(dsp(baseline,'S'+str(i)))==typed(dsp(selected,'S'+str(i)))for i in range(1,COUNT+1)if 'S'+str(i)!=TARGET),'Non-target typed source DSP changed')
        before=inventory(CACHE);public_before=inventory(T.parent/'配音缓存')
        scratch=M/('_source'+SOURCE_NO+'_strict_cached_two_phase_whole');require(not scratch.exists(),'Fresh private diagnostic namespace required');scratch.mkdir()
        paths={'T':T,'M':M,'W':W,'scratch':scratch}
        report.update({'helper_sha256':digest(__file__),'profile_sha256':PROFILE_SHA256,'actual_root_execution_adoption_sha256':a.execution_adoption_sha256,'actual_inputs':{k:digest(v)for k,v in inputs.items()},'actual_used_cache_entries':[],'original_source_first_fresh_import_per_phase':True})
        with support.environment_and_cwd(W,report['restoration']):
            with work_namespace(W/('work_'+SOURCE_NO),scratch,report['restoration']):
                for label,role in [('baseline','baseline'),('selected','shadow')]:
                    report['restoration']['normal_scripts_namespace_restored']=False
                    with support.source_namespace(W,inputs[role].read_bytes(),report['restoration']):
                        run_phase(label,inputs[role].read_bytes(),profile['inputs'][role]['sha256'],paths,support,profile,report,used,new_math)
        report['both_actual_original_whole_observations_completed']=True
        compare_phases(profile,report)
        require(not report['forbidden_model_events'],'Forbidden model endpoint was reached')
        report['diagnostic_completed']=True
    except BaseException as error:
        report['errors'].append({'type':type(error).__name__,'detail':str(error)});traceback.print_exc()
    finally:
        try:
            if before is not None:
                after=inventory(CACHE);allowed=set(new_math)
                report['all_existing_private_cache_files_exact_before_after']=all(after.get(n)==h for n,h in before.items())
                report['only_actual_new_target_original_G36_JSON_added']=set(after)-set(before)==allowed and not(set(before)-set(after))
                report['actual_new_target_original_G36']=new_math
                report['public_cache_bytes_exact_before_after']=inventory(T.parent/'配音缓存')==public_before
                report['actual_used_cache_entries']=list(used.values())
                report['original_tools_and_work_maker_bytes_exact_after']=digest(T/'make_video.py')==digest(W/'make_video.py')==MAKER_SHA256
                report['all_frozen_inputs_exact_after']=all(digest(v)==profile['inputs'][k]['sha256']for k,v in inputs.items())
                report['runtime_contract_files_exact_after']=all(digest(T/Path(r['path']).relative_to('视频/工具'))==r['patch_SHA256']for r in json.loads(inputs['overlay'].read_text())['files'])
                report['normal_original110_stamp_exact_after']=digest(T/'新管/快测通过.json')==STAMP_SHA256
                guards=['all_existing_private_cache_files_exact_before_after','only_actual_new_target_original_G36_JSON_added','public_cache_bytes_exact_before_after','original_tools_and_work_maker_bytes_exact_after','all_frozen_inputs_exact_after','runtime_contract_files_exact_after','normal_original110_stamp_exact_after']
                report['exact_scope_proved']=bool(report['diagnostic_completed'] and all(report.get(k)is True for k in guards) and all(report['restoration'].get(k)is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored']))
            math_save_integrity=bool(new_math and all(v.get('strict_readback_exact') is True for v in new_math.values())
                and all(report.get(k)is True for k in guards)
                and all(report['restoration'].get(k)is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored'])
                and not report['forbidden_model_events'])
            report['actual_original_math_private_save_integrity_proved_not_whole_acceptance']=math_save_integrity
            if math_save_integrity:
                directory=M/'tts'/('source'+SOURCE_NO+'-only-target-whole-original-math-cache')
                require(not directory.exists(),'Fresh actual private math-save namespace required');directory.mkdir()
                saved=[]
                for name,item in new_math.items():
                    destination=directory/name;shutil.copyfile(CACHE/name,destination)
                    require(digest(destination)==item['sha256'],'New private math-save copy mismatch');saved.append(str(destination))
                runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual Actions run ID required to emit cache save identity')
                key='Linux-native'+SOURCE_NO+'-only-target-whole-original-math-'+runid
                a.cache_path_output.parent.mkdir(parents=True,exist_ok=True)
                with a.cache_path_output.open('a')as out:out.write('cache_key='+key+'\ncache_paths<<WHOLE_TARGET_MATH_PATHS\n'+'\n'.join(saved)+'\nWHOLE_TARGET_MATH_PATHS\n')
                report['private_original_math_save']={'cache_key':key,'exact_paths':saved,'files':new_math,'save_success_not_claimed':True}
        except BaseException as error:
            report['exact_scope_proved']=False
            report['diagnostic_completed']=False
            report['errors'].append({'type':type(error).__name__,'detail':str(error),'during':'restore-identity-or-private-save-finalization'})
            traceback.print_exc()
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
        print(json.dumps({'output_sha256':digest(a.output),'diagnostic_completed':report['diagnostic_completed'],'exact_scope_proved':report['exact_scope_proved'],'errors':report['errors'],'new_model_inference_authorized':False,'production_or_formal_acceptance':False},ensure_ascii=False))
    return 0 if report['exact_scope_proved'] else 1

if __name__=='__main__': sys.exit(main())
