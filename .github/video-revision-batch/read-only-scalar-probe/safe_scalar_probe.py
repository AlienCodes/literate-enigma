"""Observe original empty-match / nonvoice failures; write scalar JSON only.

No native function, argument, frame local, threshold, reference, waveform, cache,
or source is changed. Native exceptions and exit status remain untouched. Enable
only on the selected native worker using VIDEO_SAFE_SCALAR_DIR and ARTICLE.
"""
import atexit
import ast
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

AUDIT_SHA='bfe12dab6bec96c9b765faea286ae30a067589f6c5ef78461b21d12b955f1e22'
NONVOICE_AST_SHA='cb28e3a860ed5d13226fc5ebd34861ed4aa9039b8f947ca0cebdc4d915dabbf9'
_state=None


def _sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda:source.read(1048576),b''):h.update(block)
    return h.hexdigest()


def _safe(value):
    if value is None or type(value) in (str,bool,int):return value
    if type(value) is float:return value if math.isfinite(value) else None
    if isinstance(value,dict):return {str(k):_safe(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        if len(value)>16 and all(not isinstance(v,dict) for v in value):raise TypeError('Scalar probe refuses long arrays.')
        if len(value)>128:raise TypeError('Scalar probe refuses excessive observation arrays.')
        return [_safe(v) for v in value]
    raise TypeError('Scalar probe refuses non-scalar data objects.')


def _write():
    if not _state or not _state['observations']:return
    data={k:v for k,v in _state.items() if not k.startswith('_')}
    data['updated_utc']=datetime.now(timezone.utc).isoformat()
    target=Path(_state['_path']);target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(_safe(data),ensure_ascii=False,indent=2)+'\n')
    os.replace(temporary,target)


def _source_info(label=None):
    target=os.environ.get('VIDEO_SAFE_SCALAR_SOURCE')
    if not target:
        root=os.environ.get('VIDEO_ROOT')
        target=str(Path(root)/'video/scripts'/(_state['article']+'.json')) if root else 'scripts/'+_state['article']+'.json'
    path=Path(target);out={'actual_source_file_exists':path.is_file()}
    if path.is_file():
        out['actual_working_source_sha256']=_sha(path)
        if label is not None:
            data=json.loads(path.read_text())
            for i,sentence in enumerate(data.get('sentences',[]),1):
                text=' '.join(re.sub(r'\{\{.*?\}\}','',c['en']).replace('**','').strip() for c in sentence['chunks'])
                if text==label:out['source_sentence']='S'+str(i);break
    return out


def _context(frame):
    root=os.environ.get('VIDEO_ROOT','')
    return {'python_version':sys.version.split()[0],
            'native_function':frame.f_code.co_name,'native_code_filename':frame.f_code.co_filename,
            'native_line':frame.f_lineno,'selftest_copy':('自检_' in root),
            'STRICT_CACHE':os.environ.get('STRICT_CACHE'),**_source_info()}


def _audit_empty(frame):
    L=frame.f_locals;G=frame.f_globals;np=G['np'];sr=int(G['SR'])
    item=L['it'];idx=int(item['idx']);A=L['A'];gx=L['gx'];raw=L['x'];n0=int(L['a0']);p=L.get('p');length=int(L['L0'])
    record={'kind':'audit_empty_exact_match_segments','native_exception_expected':'IndexError at unguarded segs[0]/segs[-1]',
            'article':_state['article'],'reference_item_index':idx,'reference_item':'title' if idx<0 else 'S'+str(idx+1),
            'reference_text_sha256':hashlib.sha256(str(item['text']).encode()).hexdigest(),
            'reference_samples':int(L['N']),'reference_duration_seconds':int(L['N'])/sr,
            'working_PCM_samples':int(len(A)),'working_PCM_duration_seconds':len(A)/sr,
            'audible_island_count':len(L['isl']),'signal_block_count':int(np.count_nonzero(L['sig'])),
            'walked_signal_blocks':len(L['blk']),'matched_blocks':len(L['matched']),'exact_match_segments':0,
            'anchor_NCC':float(L['c']),'anchor_raw_sample':n0,'anchor_length_samples':length,
            'global_gain_used':float(L['g']),'unchanged_TOL_in_PCM_LSB':float(G['TOL'])*32768,
            'candidate_gain_fit_is_diagnostic_only':True,'no_gain_or_TOL_applied_or_changed':True,**_context(frame)}
    gain_regions=item.get('分段增益') or []
    record.update({'reference_gain_region_count':len(gain_regions),
                   'reference_gain_region_metadata_sha256':hashlib.sha256(json.dumps(gain_regions,separators=(',',':')).encode()).hexdigest(),
                   'reference_gain_min_dB':min((float(r[2]) for r in gain_regions),default=0.0),
                   'reference_gain_max_dB':max((float(r[2]) for r in gain_regions),default=0.0)})
    segment_file=os.environ.get('VIDEO_SAFE_SCALAR_SEGS')
    if segment_file:
        path=Path(segment_file);record['actual_working_segment_metadata_exists']=path.is_file()
        if path.is_file():
            segs=json.loads(path.read_text()).get('S'+str(idx+1),[]) if idx>=0 else []
            gains=[float(r['增益']) for r in segs if '增益' in r]
            record.update({'actual_working_segment_metadata_sha256':_sha(path),
                           'actual_working_segment_count':len(segs),'actual_working_gain_record_count':len(gains),
                           'actual_working_gain_min_dB':min(gains,default=0.0),'actual_working_gain_max_dB':max(gains,default=0.0)})
    if p is not None and p>=0 and p+length<=len(A) and n0+length<=len(gx):
        a=A[int(p):int(p)+length];x=gx[n0:n0+length]
        denominator=float(np.dot(x,x))
        if denominator>0:
            ratio=float(np.dot(a,x)/denominator)
            fixed=float(np.max(np.abs(a-x)))
            fitted=float(np.max(np.abs(a-x*ratio)))
            record.update({'anchor_output_sample':int(p),'local_LS_gain_ratio_to_used_global_gain':ratio,
                           'anchor_residual_max_PCM_LSB_current_gain':fixed*32768,
                           'anchor_residual_max_PCM_LSB_local_LS_fit':fitted*32768,
                           'local_anchor_passes_existing_TOL_after_scalar_fit':bool(fitted<=G['TOL'])})
    _state['observations'].append(record);_write()


def _nonvoice_failure(frame,error):
    L=frame.f_locals;G=frame.f_globals;np=G['np'];w=L['w'];x0=int(L['x0']);x1=int(L['x1']);F0=int(L['F0'])
    flag=str(L.get('flag',''));breath=bool(L.get('吸_',False));threshold=-24 if breath else -30
    iv=L['iv'];bounds=bool(0<x0<x1<len(w));checks={'invalid_interval_bounds':not bounds}
    record={'kind':'nonvoice_original_gate_failure_predicates','article':_state['article'],
            'source_interval':[float(iv[0]),float(iv[1]),flag],
            'source_label_sha256':hashlib.sha256(str(L['label']).encode()).hexdigest(),
            'sample_rate':int(G['SR']),'interval_start_sample':x0,'interval_end_sample':x1,
            'interval_samples':x1-x0,'working_sentence_samples':len(w),'working_sentence_seconds':len(w)/int(G['SR']),
            'bounds_valid':bounds,'interval_exceeds_end_by_samples':max(0,x1-len(w)),
            'interval_start_at_or_before_zero':bool(x0<=0),
            'interval_end_at_or_after_sentence_end':bool(x1>=len(w)),
            'source_interval_order_and_nonnegative_times_valid':bool(0<x0<x1),
            'breath_exception_originally_selected':breath,'unchanged_region_threshold_dB':threshold,
            'unchanged_external_silence_threshold_dB':float(G['AUD_DB']),
            'unchanged_zero_crossing_abs_threshold':1e-4,
            'original_gate_exception_preserved':True,'original_exception_message':str(error)[:400],
            **_context(frame),**_source_info(str(L['label']))}
    if bounds:
        lv=L['lv0'];env=L['e0'][x0//F0:x1//F0]
        region_rms=float(lv(w[x0:x1]));env_peak=float(env.max()) if len(env) else None
        pre=w[x0-F0:x0];post=w[x1:x1+F0]
        pre_db=float(lv(pre)) if len(pre) else None;post_db=float(lv(post)) if len(post) else None
        z0=bool(w[x0-1]*w[x0]>0 and abs(w[x0])>1e-4)
        z1=bool(w[x1-1]*w[x1]>0 and abs(w[x1])>1e-4)
        checks.update({'region_RMS_above_original_threshold':region_rms>threshold,
                       'region_5ms_peak_at_or_above_original_threshold':env_peak is not None and env_peak>=threshold,
                       'external_pre5ms_not_quiet':flag not in ('紧贴词尾','紧贴两头') and pre_db is not None and pre_db>=G['AUD_DB'],
                       'external_post5ms_not_quiet':flag not in ('紧贴词头','紧贴两头') and post_db is not None and post_db>=G['AUD_DB'],
                       'attached_start_not_zero_crossing':flag in ('紧贴词尾','紧贴两头') and z0,
                       'attached_end_not_zero_crossing':flag in ('紧贴词头','紧贴两头') and z1})
        record.update({'region_RMS_dB':region_rms,'region_5ms_peak_dB':env_peak,
                       'pre5ms_samples':len(pre),'post5ms_samples':len(post),'pre5ms_dB':pre_db,'post5ms_dB':post_db,
                       'attached_start_sample_abs':float(abs(w[x0])),'attached_end_sample_abs':float(abs(w[x1]))})
    record['original_failure_predicates']=checks
    record['failed_predicate_names']=[key for key,value in checks.items() if value]
    _state['observations'].append(record);_write()


def _verify_nonvoice_body():
    path=Path(os.environ['VIDEO_SAFE_SCALAR_MAKER'])
    raw=path.read_text();tree=ast.parse(raw)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_nonvoice')
    digest=_ast_sha(function)
    return digest==NONVOICE_AST_SHA,{'maker_file_sha256':_sha(path),'nonvoice_AST_sha256':digest}


def _ast_sha(function):
    # Producer uses Python3.11; the local pinned image environment is3.12.
    # Ignore only the empty type_params field introduced in3.12, preserving
    # every actual argument, constant, operation and branch in the function.
    def project(value):
        if isinstance(value,ast.AST):
            fields=[]
            for name in value._fields:
                child=getattr(value,name,None)
                if name=='type_params' and not child:continue
                fields.append([name,project(child)])
            return {'node':type(value).__name__,'fields':fields}
        if isinstance(value,list):return [project(v) for v in value]
        return value
    return hashlib.sha256(json.dumps(project(function),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def _trace(frame,event,arg):
    try:
        if event=='call':
            name=frame.f_code.co_name
            if name=='audit' and str(frame.f_locals.get('no','')).zfill(2)==_state['article']:
                path=Path(frame.f_code.co_filename)
                if path.is_file() and _sha(path)==AUDIT_SHA:return _trace
            if name=='_nonvoice' and {'w','ivs','label'}<=set(frame.f_locals):
                # A core selftest may call another article's examples. Never
                # mislabel those as this worker's actual source sentence.
                if 'source_sentence' not in _source_info(str(frame.f_locals['label'])):return None
                if not _state['_nonvoice_verified']:
                    ok,evidence=_verify_nonvoice_body();_state['_nonvoice_verified']=ok
                    _state['native_nonvoice_identity']=evidence
                if _state['_nonvoice_verified']:return _trace
            return None
        L=frame.f_locals
        if frame.f_code.co_name=='audit' and event=='line' and frame.f_lineno==213 and L.get('segs')==[]:
            key=('empty',id(frame),int(L['it']['idx']))
            if key not in _state['_seen']:_state['_seen'].add(key);_audit_empty(frame)
        if frame.f_code.co_name=='_nonvoice' and event=='exception' and isinstance(arg[1],SystemExit) and '非人声区间不对' in str(arg[1]):
            key=('nonvoice',id(frame),int(L.get('x0',-1)),int(L.get('x1',-1)))
            if key not in _state['_seen']:_state['_seen'].add(key);_nonvoice_failure(frame,arg[1])
        return _trace
    except Exception as error:
        # Diagnosis failure is recorded, never converted into a native pass/fail.
        if _state is not None:
            _state['observations'].append({'kind':'safe_scalar_probe_error','error_type':type(error).__name__,'error':str(error)[:200]})
            try:_write()
            except Exception:pass
        return None


def install():
    global _state
    folder=os.environ.get('VIDEO_SAFE_SCALAR_DIR');no=os.environ.get('VIDEO_SAFE_SCALAR_ARTICLE','').zfill(2)
    if not folder or not re.fullmatch(r'\d{2}',no) or no not in {'06','54','57','67'}:return False
    if sys.gettrace() is not None:return False  # do not replace an existing debugger/trace
    _state={'article':no,'pid':os.getpid(),'diagnostic_only':True,'quality_acceptance':False,
            'native_function_arguments_source_audio_reference_and_thresholds_changed':False,
            'PCM_GT_cache_payload_or_numeric_waveform_arrays_exported':False,
            'probe_program_sha256':_sha(__file__),'observations':[],
            '_path':str(Path(folder)/f'{no}-safe-scalar-{os.getpid()}.json'),
            '_seen':set(),'_nonvoice_verified':False}
    atexit.register(_write);sys.settrace(_trace);return True
