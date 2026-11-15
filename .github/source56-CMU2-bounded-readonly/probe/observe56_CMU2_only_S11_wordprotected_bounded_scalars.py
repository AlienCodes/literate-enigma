"""CODE ONLY: one exact cached S11; original acoustic algorithms, scalar output.

The caller initializes a NEW isolated W with the frozen source bytes. This probe
never installs or writes a source, creates audio, runs a whole build, accepts a
cut, synthesizes, or computes missing gain mathematics.
"""
from pathlib import Path
import argparse, ast, contextlib, copy, gc, hashlib, importlib.util, io, json
import math, os, re, sys, traceback

PROFILE_SHA256 = '6a26cf82c83342bc43e1abee1b5ae09159a94210e24377f39c5dd31c88afdc41'
SOURCE_NO, BOOK_ORDER, TARGET = '56', 65, 'S11'
DISPLAY = 'The compromise, struck without Wallace, may have kept rivalry over precedence at bay.'
PROJECTED = 'The compromise struck without Wallace, may have kept rivalry over precedence at bay.'
ENVELOPE = [1.95, 2.70]
MATH_NAME = '调平_f8530296a68d023c59d49bcc027d1e23c0bd9a2c.json'
MATH_SHA = '98c2e92f9fe36307e60e0a857a97d5595015278b2add1fed2bcea10248eb43d6'
FLAGS = ['STRICT_CACHE', 'XG_NOPUSH', 'AUDIO_ONLY', 'XG_KEEP_REVIEWED_GAIN',
         'XG_KEEP_REVIEWED_ENDING', 'XG_KEEP_REVIEWED_CUTS']
OVERRIDES = ['VOICE', 'AFFILE', 'OLD_IV_VOID', 'ONLY', 'BREATH_FRAC', 'CACHE_LOG']


def require(value, message):
    if not value:
        raise AssertionError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def typed(value):
    if isinstance(value, dict):
        return ('dict', tuple((key, typed(item)) for key, item in value.items()))
    if isinstance(value, (tuple, list)):
        return (type(value).__name__, tuple(typed(item) for item in value))
    return (type(value).__name__, value)


def real_file(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), 'A pinned input must be a regular non-symlink file: ' + str(p))
    return p


def inventory(path):
    p = Path(path)
    require(p.is_dir() and not p.is_symlink(), 'Inventory requires an existing real directory')
    return {x.name: digest(real_file(x)) for x in p.iterdir() if x.is_file()}


def directory_snapshot(path):
    p = Path(path)
    if not os.path.lexists(p):
        return {'exists': False}
    require(p.is_dir() and not p.is_symlink(), 'Snapshot directory must be real')
    files = {}
    for x in sorted(p.rglob('*')):
        require(not x.is_symlink(), 'Do not follow a work/source symlink')
        if x.is_file():
            files[str(x.relative_to(p))] = {'bytes': x.stat().st_size, 'sha256': digest(x)}
    return {'exists': True, 'inode': p.stat().st_ino, 'files': files}


def load_module(name, path):
    require(name not in sys.modules, 'Fresh diagnostic module name required')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bind_inputs(folder, profile):
    bound = {}
    for role, row in profile['inputs'].items():
        rel = Path(row['file'])
        require(not rel.is_absolute() and '..' not in rel.parts, 'Input escaped frozen namespace')
        p = real_file(Path(folder) / rel)
        require(p.stat().st_size == row['bytes'] and digest(p) == row['sha256'], 'Wrong frozen input ' + role)
        bound[role] = p
    return bound


def runtime_local_paths(T, M, W, expected):
    """Use original G27 precedence (../tts, W); pin full bytes before import."""
    result = {}
    for name, wanted in expected.items():
        require(name and '/' not in name and '\\' not in name and '.' not in name, 'Only finite local module basenames')
        require(digest(real_file(Path(T) / (name + '.py'))) == wanted, 'Original T runtime module differs: ' + name)
        choices = [Path(W) / (name + '.py')] if name == 'make_video' else [Path(M) / 'tts' / (name + '.py'), Path(W) / (name + '.py')]
        actual = next((p for p in choices if os.path.lexists(p)), None)
        require(actual is not None and digest(real_file(actual)) == wanted, 'Actual original G27 runtime module missing/changed: ' + name)
        result[name] = actual.resolve()
    return result


def verify_loaded_local_modules(paths, expected):
    result = {}
    for name, path in paths.items():
        if name == 'make_video' or name not in sys.modules:
            continue
        module = sys.modules[name]
        actual = real_file(getattr(module, '__file__', ''))
        require(actual.resolve() == path and digest(actual) == expected[name], 'Loaded actual module path/bytes differ: ' + name)
        result[name] = {'file': str(actual), 'sha256': digest(actual)}
    return result


def validate_data(profile, source, actual):
    require((profile['source_id'], profile['book_order'], profile['target_sentence']) ==
            (SOURCE_NO, BOOK_ORDER, TARGET), 'Wrong exact target profile')
    require(str(source.get('no')) == SOURCE_NO and len(source['sentences']) == 17, 'Wrong source or sentence count')
    sent = ' '.join(c['en'].replace('**', '') for c in source['sentences'][10]['chunks'])
    require(sent == DISPLAY, 'Exact unmodified S11 display and both commas required')
    require(typed(source.get('朗读删逗号', {}).get(TARGET)) == typed(
        {'篇号': 56, '原文': DISPLAY, '逗号序号': [1]}), 'Only first spoken comma may be removed')
    require(profile['probe_envelope_w_seconds'] == ENVELOPE and profile['BREATH_FRAC'] == .70,
            'No envelope or original threshold change is authorized')
    # The complete source SHA is bound before this function. This additional
    # equality makes unknown target DSP fail independently of known-key loops.
    target = {k: copy.deepcopy(v.get(TARGET)) for k, v in source.items()
              if isinstance(v, dict) and TARGET in v}
    require(typed(target) == typed(profile['all_source_top_dict_target_entries']), 'Unknown or changed target controls')
    require(actual['source_id'] == SOURCE_NO and actual['book_order'] == BOOK_ORDER and
            actual['diagnostic_completed'] is True and actual['physical_metadata_precheck_ready'] is True and actual['quality_acceptance'] is False and actual['errors'] == [], 'Real completed identity-only precheck of failed native required; not native quality')
    phase = actual['phases']['selected']
    require(phase['source_sha256'] == profile['inputs']['source']['sha256'], 'Actual reference is for a different source')
    require(phase['actual_complete_WAV']['file_sha256'] == profile['actual_whole_WAV_sha256'] and
            phase['actual_complete_WAV']['file_md5'] == profile['actual_whole_WAV_md5'], 'Wrong existing whole evidence role')
    require(typed(phase['observed_sentences'][TARGET]) == typed(profile['actual_target_observation']),
            'Exact current native target evidence required')
    require(typed(profile['existing_G36']) == typed({'name': MATH_NAME, 'sha256': MATH_SHA}), 'Only one existing original G36 key')
    return sent, phase


def require_existing_math(cache, key):
    require(key is not None and '调平_' + key + '.json' == MATH_NAME, 'Unknown G36 key; never calculate')
    p = real_file(Path(cache) / MATH_NAME)
    require(digest(p) == MATH_SHA, 'Missing/changed original G36; never calculate')
    return p


def validate_model_tuple(m, np, text, voice, speed, lang, kw, method, sent):
    require(os.environ.get('STRICT_CACHE') == '1' and text == m.spoken(sent) == DISPLAY and
            type(speed) is float and speed == .95 and lang == 'en-us' and
            np.array_equal(voice, m.V), 'Only the exact current S11 cache tuple is authorized')
    expected = {} if method == 'create' else {'clause_pause': 0, 'sentence_pause': 0}
    require(method in ('create', 'create_timed') and typed(kw) == typed(expected), 'Wrong exact target typed kwargs')


def target_model_guard(m, cache, method, model, original, sent, entries, used):
    np = m.np
    def guarded(text, voice, speed=1.0, lang='en-us', **kw):
        validate_model_tuple(m, np, text, voice, speed, lang, kw, method, sent)
        seen = []
        def capture(actual_text, voice, speed=1.0, lang='en-us', **actual_kw):
            row = entries[method]
            mid = m._portable_mid(str(Path(cache).parent / model))
            vh = hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
            key = hashlib.sha1(repr((method, mid, actual_text, vh, float(speed), lang,
                                       sorted(actual_kw.items()))).encode()).hexdigest() + '.pkl'
            require(key == row['name'] and hashlib.sha256(actual_text.encode()).hexdigest() == '7ab4087b2c5293e715b5a63769102df98c294a405f7d0e5368c328f51388492a' and actual_kw == ({'is_phonemes':True} if method=='create' else {'is_phonemes':True,'clause_pause':0,'sentence_pause':0}), 'Unexpected new CMU2 post-pron phoneSHA/key/typed kwargs')
            p, marker = real_file(Path(cache) / key), real_file(Path(cache) / row['marker_name'])
            require(digest(p) == row['pkl_SHA256'] and digest(marker) == row['marker_SHA256'] and
                    marker.read_text().strip() == row['marker_value'], 'Only exact saved mother and marker may be read')
            m._条目核对(str(p))
            seen.append({'method': method, 'name': key, 'pkl_sha256': digest(p),
                         'post_pron_input_sha256': hashlib.sha256(actual_text.encode()).hexdigest(),
                         'kwargs': actual_kw})
        m._pron(capture)(text, voice=voice, speed=speed, lang=lang, **kw)
        require(len(seen) == 1, 'Original pronunciation capture ABI changed')
        value = original(text, voice=voice, speed=speed, lang=lang, **kw)
        row = entries[method]
        array = value[0]
        require(value[1] == row['SR'] == 24000 and str(array.dtype) == row['dtype'] and len(array) == row['samples'] and
                hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest() == row['array_SHA256'],
                'Existing cached mother ndarray differs')
        if method == 'create_timed':
            require(len(value) == 3 and len(value[2]) == row['timed_token_count'], 'Cached timed-token ABI changed')
        used.append(seen[0])
        return value
    return guarded


@contextlib.contextmanager
def process_state(work,support,restoration,module_names=(),local_roots=()):
 modules,env=dict(sys.modules),dict(os.environ);cwd,path,trace,bytecode=Path.cwd(),list(sys.path),sys.gettrace(),sys.dont_write_bytecode
 try:
  require(trace is None,'Do not replace unknown trace hook');sys.dont_write_bytecode=True
  for name in set(('render','title2','clean','出片指纹','响度一致性核对'))|set(module_names):sys.modules.pop(name,None)
  with support.environment_and_cwd(work,restoration):yield
 finally:
  sys.settrace(trace);os.chdir(cwd);sys.path[:]=path;os.environ.clear();os.environ.update(env);sys.dont_write_bytecode=bytecode
  restored=restore_original_local_modules(modules,local_roots);restoration['process_module_lifecycle']=restored
  restoration['all_process_modules_restored']=all(v is True for v in restored.values()if type(v)is bool)
  restoration['trace_cwd_path_environment_bytecode_restored']=sys.gettrace()is trace and Path.cwd()==cwd and sys.path==path and dict(os.environ)==env and sys.dont_write_bytecode==bytecode


def restore_original_local_modules(snapshot,roots=()):
 local={'make_video','render','title2','title_anim','clean','出片指纹','响度一致性核对','对正量'}
 local.update(k for k in set(snapshot)|set(sys.modules) if k.startswith('_CMU2_') or k.startswith('_original_56_strict_whole_'))
 roots=[Path(p).resolve() for p in roots];path_aliases=[]
 for k,v in list(sys.modules.items()):
  f=getattr(v,'__file__',None)
  if not isinstance(f,(str,bytes)):continue
  try:
   p=Path(f).resolve()
   if p.is_file() and any(p.is_relative_to(r) for r in roots):local.add(k);path_aliases.append(k)
  except (OSError,TypeError,ValueError):continue
 added_third_party={k:v for k,v in sys.modules.items() if k not in snapshot and k not in local}
 for k in local:
  if k in snapshot:sys.modules[k]=snapshot[k]
  else:sys.modules.pop(k,None)
 return {'all_original_local_module_objects_restored':all((sys.modules.get(k) is snapshot[k]) if k in snapshot else k not in sys.modules for k in local),'all_preexisting_module_objects_preserved':all(sys.modules.get(k) is v for k,v in snapshot.items()),'all_added_third_party_module_objects_retained':all(sys.modules.get(k) is v for k,v in added_third_party.items()),'retained_added_third_party_module_count':len(added_third_party),'actual_T_W_inputs_path_aliases_restored':sorted(path_aliases),'third_party_C_extensions_never_purged':True}

def original_dossier_parts(path, expected_sha, np, SR, env5, aud_db):
    require(digest(path) == expected_sha, 'Wrong original dossier bytes')
    tree = ast.parse(Path(path).read_text())
    names = {'to_w', 'words', 'per', 'spec', 'breath_after'}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require(len(nodes) == len(names), 'Original dossier function ABI changed')
    candidates = [n for n in tree.body if isinstance(n, ast.For) and
                  isinstance(n.target, ast.Name) and n.target.id == 'it' and
                  isinstance(n.iter, ast.Name) and n.iter.id == 'info']
    require(len(candidates) == 1, 'Unique original A19 candidate loop required')
    ns = {'np': np, 'SR': SR, 'F5': int(.005 * SR), '_env5': env5, 'AUD_DB': aud_db,
          'BREATH_GAP': .10}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    return ns, candidates[0]


def original_auto_loop(path, expected_sha):
    require(digest(path) == expected_sha, 'Wrong original automatic-cut bytes or threshold')
    tree = ast.parse(Path(path).read_text())
    loops = [n for n in tree.body if isinstance(n, ast.For) and
             isinstance(n.target, ast.Tuple) and [x.id for x in n.target.elts] == ['n_', 'c']]
    require(len(loops) == 1, 'Unique original candidate loop required')
    loop = loops[0]
    gates = [n for n in ast.walk(loop) if isinstance(n, ast.If) and any(
        isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == 'get' and
        x.args and isinstance(x.args[0], ast.Constant) and x.args[0].value == 'BREATH_FRAC'
        for x in ast.walk(n.test))]
    require(len(gates) == 1, 'Unique original unchanged breath gate required')
    # Compilation uses the original AST unchanged; trace only reads its state.
    require(ast.dump(loop, include_attributes=True) == ast.dump(loops[0], include_attributes=True), 'AST inverse differs')
    return loop, gates[0].lineno


def frame_profile(np, SR, w, ns, start, stop, ref):
    rows = []
    for i in range(start, stop - 60, 60):
        x = w[i:i + 60]
        centroid, low = ns['spec'](w[max(0, i - 90):i + 150])
        periodicity = ns['per'](w[max(0, i - 210):i + 270])
        level = float(20 * np.log10(np.sqrt(np.mean(x ** 2)) / ref + 1e-9))
        zc = [(i + j) / SR for j in range(1, len(x)) if x[j - 1] * x[j] <= 0]
        rows.append({'sample': i, 'w_s': i / SR, 'dB_2p5ms': level,
            'centroid_Hz': centroid, 'below150Hz_dB': low, 'periodicity20ms': periodicity,
            'audible_original_gt_minus50dB': bool(level > -50),
            'breath_original_predicate': bool(1800 < centroid < 3800 and low < -10 and periodicity < .35),
            'all_zero_crossing_w_s': zc})
    return rows


def observe_original_automatic(path,expected_sha,np,SR,info,cands,dossier_ns,nonvoice,result):
 loop,gate_line=original_auto_loop(path,expected_sha);tree=ast.parse(Path(path).read_text());merges=[n for n in tree.body if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='si_'];require(len(merges)==1,'Original unique merge/schema/nonvoice guard loop required')
 xline=next(n.lineno for n in ast.walk(loop)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Tuple)and any(isinstance(q,ast.Name)and q.id=='x0'for q in t.elts)for t in n.targets));audline=min(n.lineno for n in ast.walk(loop)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='aud'for t in n.targets))
 ns=dict(dossier_ns,np=np,SR=SR,F5=int(.005*SR),info=info,cands=cands,no=SOURCE_NO,os=os,ONLY=[],auto={},human=[]);states={};guard_rows=[];result.update(original_candidate_loop_AST_SHA256=hashlib.sha256(ast.dump(loop,include_attributes=True).encode()).hexdigest(),original_merge_guard_loop_AST_SHA256=hashlib.sha256(ast.dump(merges[0],include_attributes=True).encode()).hexdigest(),all_candidate_guard_states_before_original_gates=states,original_merged_nonvoice_guard_checks=guard_rows)
 def guarded_nonvoice(w,ivs,label):
  for iv in ivs:
   row=measure_interval_scalars(np,SR,w,dossier_ns,iv);row['schema_is_original_merge_output']=True;guard_rows.append(row)
  before=hashlib.sha256(np.ascontiguousarray(w).tobytes()).hexdigest()
  try:
   value=nonvoice(w,ivs,label)
   for row in guard_rows[-len(ivs):]:row['original_nonvoice_guard_passed']=True
   return value
  except BaseException as e:
   for row in guard_rows[-len(ivs):]:row.update(original_nonvoice_guard_passed=False,original_guard_error={'type':type(e).__name__,'detail':str(e)})
   raise
  finally:require(hashlib.sha256(np.ascontiguousarray(w).tobytes()).hexdigest()==before,'Original guard modified input raw array')
 ns['_nonvoice']=guarded_nonvoice;oldtrace=sys.gettrace();require(oldtrace is None and not any(os.environ.get(k)for k in ['ONLY','BREATH_FRAC']),'No trace/threshold override')
 def trace(frame,event,arg):
  if event=='line' and frame.f_globals is ns and frame.f_code.co_filename==str(path) and frame.f_code.co_name=='<module>' and loop.lineno<=frame.f_lineno<=loop.end_lineno and 'n_'in frame.f_locals:
   v=frame.f_locals;n=int(v['n_']);row=states.setdefault(str(n),{'local_candidate_index':n,'original_guard_lines_seen':[]});row['original_guard_lines_seen'].append(frame.f_lineno);row['kind']=v.get('c',{}).get('kind');row['last_original_guard_line']=frame.f_lineno
   if frame.f_lineno>xline and all(k in v for k in ['x0','x1','tl','tr','pl','nl']):
    row.update(automatic_x0_x1_samples_halfopen=[int(v['x0']),int(v['x1'])],left_touches_word=bool(v['tl']),right_touches_word=bool(v['tr']),preceding_loud5ms_frame_indices=[int(x)for x in v['pl']],following_loud5ms_frame_indices=[int(x)for x in v['nl']])
   if frame.f_lineno>audline and 'aud'in v:
    aud=list(v['aud']);row['audible_frame_start_samples']=[int(x)for x in aud]
   if frame.f_lineno==gate_line:
    x0,x1=int(v['x0']),int(v['x1']);require(int(ENVELOPE[0]*SR)<=x0<x1<=int(ENVELOPE[1]*SR),'Automatic candidate escaped approved raw envelope; earlier scalars retained')
    aud=list(v['aud']);bo=[bool(v['breathy'](i))for i in aud];row.update(observed_at_original_70percent_gate=True,breath_boolean_at_original_audible_frames=bo,audible_count=len(aud),breath_count=sum(bo),exact_breath_fraction=float(np.mean(bo))if aud else None,unchanged_threshold=.70,original_70percent_gate_passes=not aud or bool(np.mean(bo)>=.70))
  return trace
 try:
  sys.settrace(trace);exec(compile(ast.Module(body=[loop],type_ignores=[]),str(path),'exec'),ns)
 finally:sys.settrace(oldtrace);result['original_human_rejections_before_merge']=copy.deepcopy(ns['human']);result['original_accepted_unmerged_windows_samples']=copy.deepcopy(ns['auto'])
 # This is the original merge and _nonvoice validation loop only. Never execute
 # its later WRITE block; discard any copied/muted array returned by the guard.
 exec(compile(ast.Module(body=merges,type_ignores=[]),str(path),'exec'),ns)
 result['original_final_human_rejections']=copy.deepcopy(ns['human']);result['original_merged_suggested_schema_not_written']={'S'+str(k):v for k,v in ns['auto'].items()};result['no_merge_writer_or_source_interval_adoption_executed']=True
 return result


def acoustic_diagnostic(m,T,phase,pcm,w0,profile,result):
 np,SR=m.np,m.SR;ns,a19_loop=original_dossier_parts(T/'疑点清单.py',profile['tools']['疑点清单.py'],np,SR,m._env5,m.AUD_DB);clock=phase['actual_sample_clock'][TARGET]
 it={'si':11,'sent':DISPLAY,'off':clock['start_sample'],'n':len(pcm),'segs':[tuple(x[:3])+(list(x[3]),)for x in m.LAST['segs']],'toks':[(x.phoneme,x.start,x.end)for x in m.LAST['toks']],'scale':m.LAST['scale'],'head':m.LAST['head'],'cuts':m.LAST['cuts'],'tmap':copy.deepcopy(profile['original_tmap']),'w0':w0,'out':pcm}
 sha=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest();result.update(actual_original_LAST={k:copy.deepcopy(m.LAST[k])for k in ['head','hs','scale','segs','total','cuts','gaps','fades','grafts']},raw_clean_tail_float32_SHA256=sha(w0),actual_clean_FP=m.SENT_FP[DISPLAY],full_raw8c48_is_not_clean9d0=True,original_timed_token_count=len(it['toks']))
 words=ns['words'](it);result['original_words_near_probe_as_phoneme_groups']=[list(x)for x in words if x[2]>ENVELOPE[0]-.2 and x[1]<ENVELOPE[1]+.2];result['timed_labels_are_annotations_not_true_word_or_noise_verdict']=True
 count=len(w0)//int(.005*SR);ref=np.sqrt(np.mean(w0[:count*120].reshape(count,120)**2,axis=1)).max();result['w_envelope_frames']=frame_profile(np,SR,w0,ns,int(ENVELOPE[0]*SR),int(ENVELOPE[1]*SR),ref)
 result['actual_original_edges_raw_clean']=list(m._edges(w0));result['native_suggested_interval_readonly_measurement']=measure_interval_scalars(np,SR,w0,ns,profile['native_suggested_interval_not_adopted'])
 # Always emit the full real interval scalars before invoking its original guard.
 try:
  discarded=m._nonvoice(w0,[profile['native_suggested_interval_not_adopted']],'readonly-native-suggestion-guard-only');result['native_suggested_interval_readonly_measurement']['original_nonvoice_guard_passed']=True;del discarded
 except SystemExit as e:result['native_suggested_interval_readonly_measurement'].update(original_nonvoice_guard_passed=False,original_guard_error=str(e))
 normalized=pcm/np.float32(phase['actual_original_mastering']['pre_master_absolute_peak'])*.89;require(sha(normalized)==clock['observed_post_master_float_PCM_sha256'],'Exact ordered new99c native normalization differs')
 buf=io.BytesIO();m.sf.write(buf,normalized,SR,format='WAV',subtype='PCM_16');buf.seek(0);quantized,rate=m.sf.read(buf);require(rate==SR and len(quantized)==len(pcm),'Original PCM16 in-memory ABI')
 context=np.zeros(phase['actual_complete_WAV']['samples'],float);context[clock['start_sample']:clock['end_sample_exclusive']]=quantized;pv=load_module('_source56_only_S11_CMU2_original_PV',T/'纯人声核对.py');flags=pv.scan(context);result['actual_original_PV_flags_sparse_S11_context_not_whole_scan']=[list(f)for f in flags]
 cands=[dict(kind=f[0],t0=f[1],t1=f[2],db=f[3],c=f[4],per=f[5],lo=f[6])for f in flags];ns.update(info=[it],cands=cands);exec(compile(ast.Module(body=[a19_loop],type_ignores=[]),str(T/'疑点清单.py'),'exec'),ns);cands.sort(key=lambda c:c['t0']);result['all_original_candidates_scalar_before_any_auto_guard']=copy.deepcopy(cands);mapped=[];scoped=[]
 for local_id,c in enumerate(cands,1):
  p0=ns['to_w'](it,(round(c['t0']*SR)-it['off'])/SR);p1=ns['to_w'](it,(round(c['t1']*SR)-it['off']-1)/SR);row={**c,'local_candidate_index':local_id,'native_full_article_candidate_id_not_inferred':True,'original_to_w_samples_halfopen':[p0,None if p1 is None else p1+1]};mapped.append(row)
  inside=p0 is not None and p1 is not None and int(ENVELOPE[0]*SR)<=p0<=p1<int(ENVELOPE[1]*SR);row['inside_declared_probe_envelope']=inside
  if inside:scoped.append(c)
 result['all_original_mapped_candidate_positions']=mapped;result['outside_envelope_candidate_ids_not_auto_measured']=[r['local_candidate_index']for r in mapped if not r['inside_declared_probe_envelope']];result['original_automatic_observation']={}
 observe_original_automatic(T/'自动切点.py',profile['tools']['自动切点.py'],np,SR,[it],scoped,ns,m._nonvoice,result['original_automatic_observation'])
 result.update(original_PCM16_sparse_context={'one_target_only_not_whole_reconstruction':True,'quantized_target_sha256':sha(quantized),'no_audio_container_or_array_exported':True},no_cut_selected_or_applied_to_source_or_exported_audio=True,original_nonvoice_guard_copy_return_discarded=True,A19_removed_or_quality_passed_not_claimed=True)
 return result


def validate_execution_adoption(path,literal,profile,inp):
 require(re.fullmatch('[0-9a-f]{64}',literal or '') and real_file(path) and digest(path)==literal,'Actual independent parent execution record/literal required')
 r=json.loads(Path(path).read_text());require(r['kind']=='ROOT-DELEGATED-parent-independent-source56-CMU2-S11-bounded-readonly-execution-adoption' and r['independent_review_passed'] is True,'Actual delegated parent scope review required')
 require(r['program_SHA256']==digest(__file__) and r['profile_SHA256']==PROFILE_SHA256 and r['ROOT_message_scope_evidence_SHA256']==profile['inputs']['actual_ROOT_message_scope_not_native_envelope']['sha256'],'Actual parent record binds another code/profile/conversation ROOT scope')
 require(r['source_id']=='56' and r['target_sentence']=='S11' and r['current_request_SHA256']==profile['inputs']['source']['sha256'] and r['CTX_SHA256']==profile['context_sha256'] and r['candidate']==[2.195,2.46625,'紧贴词头'] and r['readonly_existing_f853_only'] is True and r['new_TTS_math_cut_CF_or_checker_change_authorized'] is False,'Wrong actual closed CMU2 readonly scope')
 return r

def measure_interval_scalars(np,SR,w,ns,iv):
 require(len(iv)in(2,3) and (len(iv)==2 or iv[2] in ('紧贴词尾','紧贴词头','紧贴两头')),'Only original auto-merge interval schema; no invented word flag')
 x0,x1=round(float(iv[0])*SR),round(float(iv[1])*SR);require(int(ENVELOPE[0]*SR)<=x0<x1<=int(ENVELOPE[1]*SR),'Interval outside readonly envelope')
 F5=int(.005*SR);m=len(w)//F5;ref=np.sqrt(np.mean(w[:m*F5].reshape(m,F5)**2,axis=1)).max();env=ns['_env5'](w)
 lv=lambda x:float(20*np.log10(np.sqrt(np.mean(x**2))/(ref+1e-12)+1e-9))
 aud=[i for i in range(x0,x1-60,60)if 20*np.log10(np.sqrt(np.mean(w[i:i+60]**2))/ref+1e-9)>-50];features=frame_profile(np,SR,w,ns,x0,x1,ref);breath=[]
 for i in aud:
  centroid,low=ns['spec'](w[max(0,i-90):i+150]);periodicity=ns['per'](w[max(0,i-210):i+270]);breath.append(bool(1800<centroid<3800 and low<-10 and periodicity<.35))
 return {'suggested_schema_not_source_NV':list(iv),'samples_halfopen':[x0,x1],'original_ref_peak5ms_RMS':float(ref),'full_interval_RMS_dB_same_original_ref':lv(w[x0:x1]),'max_original_5ms_block_dB_in_interval':float(env[x0//F5:x1//F5].max()),'left_external_exact5ms_dB':lv(w[x0-F5:x0]),'right_external_exact5ms_dB':lv(w[x1:x1+F5]),'left_zero_crossing_product':float(w[x0-1]*w[x0]),'right_zero_crossing_product':float(w[x1-1]*w[x1]),'left_abs_sample':float(abs(w[x0])),'right_abs_sample':float(abs(w[x1])),'audible_start_samples_exact_original_range':aud,'breath_boolean_at_original_audible_frames':breath,'audible_count':len(aud),'breath_count':sum(breath),'exact_breath_fraction':float(np.mean(breath))if aud else None,'original_70percent_gate_passes':not aud or bool(np.mean(breath)>=.70),'unchanged_threshold':.70,'entire_window_features':features,'word_safety_or_cut_adoption_claimed':False}

def main():
    parser = argparse.ArgumentParser()
    for key in ['tools', 'video-root', 'inputs', 'profile', 'output']:
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--execution-adoption',type=Path,required=True);parser.add_argument('--execution-adoption-sha256',required=True)
    args = parser.parse_args()
    T, M = args.tools.resolve(), args.video_root.resolve()
    W, C = M / 'video', M / 'tts/cache_tts'
    output = args.output.resolve()
    report = {'kind': 'source56_only_S11_new_CMU2_existing_mothers_A19_bounded_readonly_candidate_scalar',
        'source_id': SOURCE_NO, 'book_order': BOOK_ORDER, 'target_sentence': TARGET,
        'diagnostic_completed': False, 'quality_acceptance': False, 'human_listening_performed': False,
        'source_or_audio_or_confirmation_written': False, 'new_model_or_TTS_or_math_authorized': False,
        'whole_build_GT_ASR_render_authorized': False, 'errors': [], 'restoration': {}, 'forbidden_model_events': []}
    before = public = scripts = work = frozen = inp = profile = None
    entry_modules = dict(sys.modules)
    m = support = observer = None
    methods = cells = []
    restore = old_auto = old_write = old_build = old_title = None
    log = io.StringIO()
    try:
        require(digest(args.profile) == PROFILE_SHA256, 'Wrong exact closed profile')
        profile = json.loads(args.profile.read_text()); inp = bind_inputs(args.inputs, profile)
        validate_execution_adoption(args.execution_adoption,args.execution_adoption_sha256,profile,inp)
        require(not output.exists() and not output.is_relative_to(M), 'Fresh scalar output must be outside private machine')
        source, actual = json.loads(inp['source'].read_text()), json.loads(inp['actual_precheck'].read_text())
        sent, phase = validate_data(profile, source, actual)
        require(all(os.environ.get(k) == '1' for k in FLAGS) and not any(os.environ.get(k) for k in OVERRIDES), 'Exact reviewed strict modes; no overrides')
        require(Path('/home/user/postgraduate-vocabulary').resolve() == T.parent.parent.resolve(), 'Canonical ROOT alias differs')
        require(real_file(W / 'scripts/56.json').read_bytes() == inp['source'].read_bytes(), 'Caller must stage exact same-byte frozen source before probe; probe never writes it')
        require(digest(real_file(T/'发音词典/按语境读音.json'))==digest(real_file(W/'按语境读音.json'))==profile['context_sha256']=='db04a700c9778e45db7c934ce0f4cf8f44349ff3a924599d4194aa90a363440f','Actual new db04 T/W context must precede fresh import')
        require(digest(T / 'make_video.py') == digest(W / 'make_video.py') == profile['maker_sha256'], 'Actual original maker differs')
        for name, expected in profile['tools'].items():
            require(digest(real_file(T / name)) == expected, 'Wrong original pinned diagnostic tool ' + name)
        identity = json.loads(inp['identity'].read_text())
        require(identity['source_id'] == SOURCE_NO and identity['book_order'] == BOOK_ORDER, 'Wrong actual two-mother identity')
        for name, expected in identity['actual_four_private_files'].items():
            require(digest(real_file(C / name)) == expected, 'Exact saved target mother/marker differs')
        require_existing_math(C, 'f8530296a68d023c59d49bcc027d1e23c0bd9a2c')
        require({name: digest(real_file(M / 'tts' / name)) for name in identity['models_SHA256']} == identity['models_SHA256'] and
                digest(real_file(M / 'tts/voice_mb.npy')) == identity['voice_SHA256'], 'Known original model/voice identity differs')
        support = load_module('_source56_only_S11_support', inp['support'])
        observer = load_module('_source56_only_S11_observer', inp['observer'])
        support.validate_certificate(T, json.loads(inp['overlay'].read_text()), json.loads(inp['certificate'].read_text()))
        local_paths = runtime_local_paths(T, M, W, profile['original_G27_local_module_full_sha256'])
        before, public = inventory(C), inventory(T.parent / '配音缓存')
        scripts, work = directory_snapshot(W / 'scripts'), directory_snapshot(W / 'work_56')
        watch = list(inp.values()) + [args.profile, T / 'make_video.py', W / 'make_video.py'] + [T / n for n in profile['tools']] + list(local_paths.values()) + [T / (n + '.py') for n in local_paths]
        watch += [M/'tts'/name for name in identity['models_SHA256']] + [M/'tts/voice_mb.npy',M/'tts/AF.txt',W/'读音改正.json',W/'按语境读音.json']
        require(digest(M/'tts/AF.txt')==profile['AF_SHA256'],'Original AF differs from true99c precheck')
        frozen = {str(p): digest(p) for p in watch}
        with process_state(W, support, report['restoration'], local_paths, [T,W,args.inputs.resolve()]), contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            m = load_module('_source56_only_S11_maker', W / 'make_video.py')
            m._SPOKEN_SOURCE_NO = SOURCE_NO
            sentinel = M / 'forbid-source56-only-S11-breath-probe-public-export'
            require(not sentinel.exists(), 'Private public-export sentinel must be absent')
            m._REPO_CACHE = str(sentinel)
            require(Path(m._CACHE).resolve() == C.resolve() and m.SR == 24000 and type(m.SPEED) is float and m.SPEED == .95, 'Wrong native cache/rate/speed')
            require(m._OLDF and digest(m._OLDF) == profile['old_registry_sha256'] and
                    digest(m._cand) == profile['dictionary_sha256'] and digest(m._CTX_PATH) == profile['context_sha256'] and
                    m.SENT_NO[sent] == SOURCE_NO and m.spoken(sent) == DISPLAY, 'Source-first original context differs')
            frozen[str(real_file(m._OLDF))]=digest(m._OLDF)
            # Load the original local gain dependency now, after purging any
            # preexisting module and before evaluating its original key rule.
            importlib.import_module('响度一致性核对')
            loaded_local = verify_loaded_local_modules(local_paths, profile['original_G27_local_module_full_sha256'])
            require({'clean', 'render', 'title2', '响度一致性核对'} <= set(loaded_local), 'Actual original audio dependencies not observed')
            methods = [(obj, name, getattr(obj, name)) for obj in (m.k, m.KT) for name in ('create', 'create_timed')]
            cells = [(support.closure_cell(support.closure_cell(getattr(obj, name), 'fn').cell_contents, 'fn'), None)
                     for obj, name in [(m.k, 'create'), (m.KT, 'create_timed')]]
            cells = [(cell, cell.cell_contents) for cell, _ in cells]
            restore = observer.block_native(m, support, report['forbidden_model_events'])
            entries = {row['method']: row for row in identity['cache_entries']}; used = []
            for method, obj, model in [('create', m.k, 'kokoro-v1.0.onnx'), ('create_timed', m.KT, 'kokoro-v1.0-timed.onnx')]:
                setattr(obj, method, target_model_guard(m, C, method, model, getattr(obj, method), sent, entries, used))
            old_auto = m._auto_level; math_reads = []
            def existing_math(clips, tmap, gaps, no='', rounds=2):
                require(str(no) == SOURCE_NO and type(rounds) is int and rounds == 2 and os.environ.get('STRICT_CACHE') == '1', 'Wrong original math scope')
                report['actual_S11_math_inputs_before_any_guard']={'clip_samples':[len(x) for x in clips],'clip_dtypes':[str(x.dtype)for x in clips],'clip_SHA256':[hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest()for x in clips],'actual_original_tmap_values':[list(x)for x in tmap],'actual_tmap_outer_type':type(tmap).__name__,'actual_tmap_inner_types':[type(x).__name__ for x in tmap],'gaps':list(gaps),'original_rounds':rounds,'STRICT_CACHE':os.environ.get('STRICT_CACHE')}
                current = m._auto_level; m._auto_level = old_auto
                try:
                    key = observer.auto_key(m, clips, tmap, gaps, no)
                finally:
                    m._auto_level = current
                report['actual_S11_math_inputs_before_any_guard']['actual_original_key']=key
                path = require_existing_math(C, key)
                require(not math_reads, 'Only one existing original S11 G36 read is authorized')
                value = old_auto(clips, tmap, gaps, no, rounds)
                require_existing_math(C, key)
                require(typed(value) == typed({1: -1.5, 2: 1.5}) and os.environ.get('STRICT_CACHE') == '1', 'Original cached gain/strict state differs')
                math_reads.append({'name': path.name, 'sha256': digest(path), 'value': value, 'new_math': False})
                return value
            m._auto_level = existing_math
            def forbidden(*a, **kw):
                raise AssertionError('No whole/title/render/audio-file-write or missing-math path is authorized')
            old_build, old_title = m.build, m.title_audio
            m.build = m.title_audio = forbidden
            old_write = m.sf.write
            def in_memory_only(file, *a, **kw):
                require(isinstance(file, io.BytesIO), 'No physical audio file write authorized')
                return old_write(file, *a, **kw)
            m.sf.write = in_memory_only
            try:
                raw, _ = m.k.create(m.spoken(sent), voice=m.V, speed=m.SPEED, lang='en-us')
                require(hashlib.md5(m.np.ascontiguousarray(raw).tobytes()).hexdigest()[:12]==profile['full_raw_array_MD5_first12']=='8c48a0220dc7','Actual full raw array8c48 role differs from clean9d0')
                w0 = m.clean_tail(raw)
                pieces, gaps, p0 = [], [], 0
                listing = m.list_commas(sent)
                for mark in m._speech_marks(sent):
                    pieces.append((p0, mark.end())); p0 = mark.end() + 1
                    gaps.append(m.P_LIST if mark.start() in listing else m.P_COMMA)
                pieces.append((p0, len(sent)))
                require(len(pieces) == 2 and gaps == [.4], 'Only retained without-Wallace comma pause permitted')
                clips, tmap = m.sentence_audio(sent, pieces, gaps)
                report['actual_before_tmap_guard']={'actual_tmap_values':[list(x)for x in tmap],'actual_tmap_outer_type':type(tmap).__name__,'actual_tmap_inner_types':[type(x).__name__ for x in tmap],'clip_samples':[len(x)for x in clips],'clip_SHA256':[hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest()for x in clips]}
                require(typed([list(x) for x in tmap]) == typed(profile['original_tmap']), 'Actual original tmap differs')
                clips, pcm, auto, manual = m.句增益(source, SOURCE_NO, 10, sent, pieces, gaps, clips, tmap, m.np.concatenate(clips))
                sha = lambda x: hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest()
                target = phase['observed_sentences'][TARGET]
                require(sha(pcm) == target['pre_master_PCM_sha256'] and str(pcm.dtype) == 'float32' and len(pcm) == target['samples'], 'Actual current native premaster target differs')
                require(m.SENT_FP[sent] == target['actual_raw_w_fingerprint'] == '9d0aed73b729' and
                        [list(x) for x in m.LAST['cuts']] == [[51720, 52440, .38]] and
                        typed(auto) == typed({1: -1.5, 2: 1.5}) and manual is None and not m.VOIDED, 'Unknown target physical state')
                raw_before = sha(w0)
                report['acoustics']={};acoustic_diagnostic(m,T,phase,pcm,w0,profile,report['acoustics'])
                require(sha(w0) == raw_before and sha(pcm) == target['pre_master_PCM_sha256'], 'Read-only acoustic diagnostics changed an array')
                require(len(used) == 3 and [r['method'] for r in used] == ['create', 'create', 'create_timed'] and len(math_reads) == 1, 'Unexpected cached call cardinality')
                report.update(actual_cached_reads=used, original_existing_G36_read=math_reads,
                    actual_source_sha256=digest(inp['source']), actual_display=sent, actual_spoken_model_text=m.spoken(sent),
                    actual_S11_premaster_sha256=sha(pcm), actual_raw_fingerprint=m.SENT_FP[sent],
                    no_narrower_cut_or_confirmation_selected=True)
                report['actual_original_loaded_local_modules'] = verify_loaded_local_modules(local_paths, profile['original_G27_local_module_full_sha256'])
            finally:
                m.sf.write = old_write; m._auto_level = old_auto
                m.build, m.title_audio = old_build, old_title
                if restore is not None:
                    restore(); restore = None
                for obj, name, value in methods:
                    setattr(obj, name, value)
                for cell, value in cells:
                    cell.cell_contents = value
                report['restoration']['all_four_original_methods_restored'] = all(getattr(obj, name) is value for obj, name, value in methods)
                report['restoration']['all_native_closure_cells_restored'] = all(cell.cell_contents is value for cell, value in cells)
                report['restoration']['original_auto_level_and_soundfile_write_restored'] = m._auto_level is old_auto and m.sf.write is old_write
                report['restoration']['original_build_and_title_methods_restored'] = m.build is old_build and m.title_audio is old_title
        require(not sentinel.exists(), 'Diagnostic attempted public cache export')
        report['diagnostic_completed'] = True
    except BaseException as error:
        report['errors'].append({'type': type(error).__name__, 'detail': str(error)})
        traceback.print_exc()
    finally:
        # Covers failures during guard installation, before the inner try begins.
        if m is not None:
            if old_write is not None: m.sf.write = old_write
            if old_auto is not None: m._auto_level = old_auto
            if old_build is not None: m.build = old_build
            if old_title is not None: m.title_audio = old_title
        if restore is not None:
            try: restore()
            except BaseException as e: report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'original-native-restore'});report['diagnostic_completed']=False
        for obj, name, value in methods: setattr(obj, name, value)
        for cell, value in cells: cell.cell_contents = value
        lifecycle=restore_original_local_modules(entry_modules,[T,W,args.inputs.resolve()]);report['entry_module_lifecycle']=lifecycle
        report['restoration']['entry_modules_including_support_and_observer_restored']=all(v is True for v in lifecycle.values()if type(v)is bool)
        if before is not None:
            report['all_private_cache_bytes_unchanged'] = inventory(C) == before
            report['all_public_cache_bytes_unchanged'] = inventory(T.parent / '配音缓存') == public
            report['all_source_scripts_inode_and_bytes_unchanged'] = directory_snapshot(W / 'scripts') == scripts
            report['all_normal_work_inode_and_bytes_unchanged'] = directory_snapshot(W / 'work_56') == work
            report['all_frozen_inputs_and_programs_unchanged'] = all(digest(p) == h for p, h in frozen.items())
        checks = ['all_private_cache_bytes_unchanged', 'all_public_cache_bytes_unchanged',
                  'all_source_scripts_inode_and_bytes_unchanged', 'all_normal_work_inode_and_bytes_unchanged',
                  'all_frozen_inputs_and_programs_unchanged']
        restored = ['environment_cwd_sys_path_restored', 'all_process_modules_restored',
                    'trace_cwd_path_environment_bytecode_restored', 'all_four_original_methods_restored',
                    'all_native_closure_cells_restored', 'original_auto_level_and_soundfile_write_restored',
                    'original_build_and_title_methods_restored', 'entry_modules_including_support_and_observer_restored']
        report['diagnostic_completed'] = bool(report['diagnostic_completed'] and
            all(report.get(k) is True for k in checks) and
            all(report['restoration'].get(k) is True for k in restored) and not report['errors'] and not report['forbidden_model_events'])
        report['private_diagnostic_log'] = log.getvalue()
        report['scope_limit'] = 'Scalar observation only; no human listening, quality approval, narrower deletion, interval adoption, source edit, audio export, model execution, new math, whole build, GT, ASR or render.'
        # Parent supplies an exclusive fresh public metadata path. No overwrite.
        require(not output.exists() and not output.is_relative_to(M), 'Never overwrite or write inside private machine')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=lambda x: x.item()) + '\n')
        print(json.dumps({'diagnostic_completed': report['diagnostic_completed'], 'output_sha256': digest(output), 'errors': report['errors']}, ensure_ascii=False))
    return 0 if report['diagnostic_completed'] else 1


if __name__ == '__main__':
    sys.exit(main())
