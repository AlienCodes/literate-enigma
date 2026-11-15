"""Observe only the existing current S10 cached restorer/line window w7.75-8.45; no whole build.

This is a private-cache diagnostic, never an acoustic acceptance or new AAC policy.
No original maker/checker source is modified and no new model inference is allowed.
"""
from pathlib import Path
import argparse
import copy
import gc
import hashlib
import importlib.util
import inspect
import json
import math
import os
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
P = argparse.ArgumentParser()
for key in ('tools', 'video-root', 'request', 'baseline-source', 'cache-identity', 'gain-decision', 'whole-tuple-measurement', 'whole-report', 'windows', 'S9-cache-save', 'failed-source', 'failed-proof', 'output'):
    P.add_argument('--' + key, type=Path, required=True)
args = P.parse_args()
T, M = args.tools.resolve(), args.video_root.resolve()
W, CACHE = M / 'video', M / 'tts/cache_tts'
OLD_SHA = '0193cbd1859525690e12a470c517cce2f120a1054b204fcfa3c0c392c92abbd7'
NEW_SHA = '4980ad358636619218f20a8edb618ae543432b82c2124cfac8058790be5e8361'
WINDOW_INPUT_SHA = '639c69e137244f75f941c92cfde837cb2385eb18413624f0d1281fdc20edc87c'
MAKER_SHA = '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
IDENTITY_SHA = '29f7d58ebd14d3ee50c1a779eb7dc95ecb60fd10f9812bff788bdfcf5af8ebe1'
GAIN_DECISION_SHA = '8ca6078044bb7fea7d308c387f8c0ecc104ab00fbb5639cb61895e61b71739db'
DICT_SHA = '5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
CTX_SHA = '4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
OLD_REGISTRY_SHA = '91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
CORE_CONTRACT_SHA = '24766577a0001a4920f21cf4887c4cff080d233c34d57cf45a83b7ac660cdcac'
REGISTRY_SHA = 'dfde6c065a3558b74923ce82865a3b01dae1f839af4456b74de55dc3ff492312'
FIVECORE_FILES = {
    '草稿声音.sh': '43fc6a1acdae6bb1c2252178bf034407400bbbe92eb1752053f3047da9760491',
    '句内响度.py': '9c5691cf59dc7776e822461044e50031ff118de29d7ae0769781a1cc66664bea',
    '独立复核/synth.py': 'a0c9cad9ac953e68768470e8181f7e325c8ee8ff08ca57b68bbd136b99b83264',
    '结尾句接点.py': '1a5d43c4f5483014b69bbea7ad43dddb0333a9a80e29bb2b4c8029d8915ff798',
    '读音核对.py': '50f4363bb2fc2930be59904cdccfa44fd46f14393a0385c7846028ee25b4e84c',
    '新管/回归基准_27.json': 'b8ddb4656ae27cbfc7ec8e3b99511983b4e568997bd4ad4ee33c364f3926ae94',
    '新管/快测通过.json': 'bb75875985ff106abe142caf7ecbf0a5eb76a1412309bf78d77bf146f64512af',
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def inventory():
    return {p.name: digest(p) for p in CACHE.iterdir() if p.is_file()}


def json_digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def plain(data):
    return [' '.join(c['en'].replace('**', '').strip() for c in s['chunks'])
            for s in data['sentences']]


request = args.request.resolve()
if request.is_dir():
    choices = [request/'视频/脚本/48.json', request/'48.json']
    request = next(p for p in choices if p.is_file() and digest(p) == NEW_SHA)
assert digest(request) == NEW_SHA
assert digest(args.baseline_source) == OLD_SHA
assert digest(args.whole_tuple_measurement) == '15489d7d69af8dba0d68584873e90353527305e5c63b7f2041ccafa5e7796367'
whole_tuple_measurement=json.loads(args.whole_tuple_measurement.read_text())
assert whole_tuple_measurement['exact_scope_proved'] is True and whole_tuple_measurement['actual_new_model_inference_count']==0
assert whole_tuple_measurement['actual_original_G36_gains']=={'1':-6.0}
assert whole_tuple_measurement['derived_private_G36_file']=={'name':'调平_3089bf1e9ad992be5bc42ea6c586ae366b1b1a40.json','sha256':'97a5f23cc0e52dfaecc16f35e57b6adcf5c6c538b0c45f4bf2974e471f332be2'}
assert digest(args.cache_identity) == IDENTITY_SHA
assert digest(args.gain_decision) == GAIN_DECISION_SHA
gain_decision = json.loads(args.gain_decision.read_text())
assert gain_decision['kind']=='root_source48_actual_proper_whole_SENT_NO3089_measurement_plus1_reconfirmation'
assert gain_decision['actual_report']['SHA256']==digest(args.whole_tuple_measurement)
assert gain_decision['actual_only_name24840_samples_changed'] is True
assert gain_decision['no_source_EN_CN_note_CF_NV_or_cut_override_or_threshold_change'] is True
assert gain_decision['correct_second_raw_cut165240_is_existing_original_tail_treatment_not_a_new_authored_cut'] is True
assert gain_decision['actual_original_G36']==whole_tuple_measurement['derived_private_G36_file']
assert gain_decision['formal_quality_acceptance'] is False
assert Path('/home/user/postgraduate-vocabulary').resolve() == T.parent.parent.resolve()
assert digest(T/'发音词典/读音改正.json') == DICT_SHA
assert digest(T/'发音词典/按语境读音.json') == CTX_SHA
assert digest(W/'make_video.py') == MAKER_SHA
assert digest(T/'make_video.py') == MAKER_SHA
assert {name: digest(T/name) for name in FIVECORE_FILES} == FIVECORE_FILES
assert os.environ.get('STRICT_CACHE') == '1', 'Strict original-cache mode is compulsory.'
assert os.environ.get('XG_NOPUSH') == '1'
assert os.environ.get('AUDIO_ONLY') == '1', 'No visual/video build is authorized.'
assert not os.environ.get('OLD_IV_VOID'), 'Formal S15 cleanup already happened in0193.'
for flag in ('XG_KEEP_REVIEWED_GAIN', 'XG_KEEP_REVIEWED_ENDING', 'XG_KEEP_REVIEWED_CUTS'):
    assert os.environ.get(flag) == '1', flag
assert not os.environ.get('VOICE') and not os.environ.get('AFFILE')
identity = json.loads(args.cache_identity.read_text())
assert identity['root_actual_whole3089_gain_reconfirmation_sha256']==GAIN_DECISION_SHA
assert identity['root_gain_selection']=={'source_id':'48','sentence':'S15','piece':'1','manual_dB':1.0,'original_actual_G36_dB':-6.0,'effective_combined_dB':-5.0}
assert identity['root_gain_selection_pending'] is False
assert identity['request_source_sha256'] == OLD_SHA  # Same correct mothers, ancestor0193 identity; only4 NV controls changed in73ac.
assert identity['dictionary_sha256'] == DICT_SHA and identity['context_dictionary_sha256'] == CTX_SHA
assert identity['post_pron_input_sha256'] == '5a1097e3add28dcb0b71f5140cc03b29cc258437d8610d8c2001e683cd29e8dd'
required = identity['all_five_restored_files_require_actual_fullSHA_readback']
assert len(required) == 5 and {name: digest(CACHE/name) for name in required} == required
assert {name: digest(M/'tts'/name) for name in identity['original_models_fullSHA']} == identity['original_models_fullSHA']
assert digest(M/'tts/voice_mb.npy') == identity['original_voice_sha256']
old, new = json.loads(args.baseline_source.read_text()), json.loads(request.read_text())
old_source_bytes, new_source_bytes = args.baseline_source.read_bytes(), request.read_bytes()
assert str(old['no']) == str(new['no']) == '48' and len(old['sentences']) == len(new['sentences']) == 17
changed_English = [i+1 for i, (a, b) in enumerate(zip(plain(old), plain(new))) if a != b]
assert changed_English == []
assert plain(new)[14] == identity['exact_new_plain_English']
assert new['分段增益dB']['S15'] == {'1': 1.0}
assert 'S15' not in new.get('非人声区间', {}) and 'S15' not in new.get('区间声音指纹', {})
assert '130.59–130.60s' not in new['核对确认'].get('非人声', {})

# All rejectable preflight happens before normal-native namespace mutation.
# Each phase retains original source-first / fresh-import ordering.
scratch = M/'_source48_current513d_S10_restorer_one_cached_local'
assert not scratch.exists(), 'Use a fresh isolated diagnostic machine/run.'
source = W/'scripts/48.json'
scripts = source.parent
assert scripts.is_dir()
prior_source = source.read_bytes()if source.exists()else None
other_scripts_before={str(p):digest(p)for p in scripts.glob('*.json')if p.name!='48.json'}
prior_source_entry=scratch/'preexisting-script48-untouched'
prior_scripts_link=scratch/'preexisting-scripts-symlink-untouched'
scripts_was_symlink=scripts.is_symlink()
source_isolated=False
work=W/'work_48'
prior_work=scratch/'preexisting-work48-untouched'
work_isolated=False
prior_wav=digest(work/'a.wav')if (work/'a.wav').is_file()else None
before_cache=inventory()
environment_link_created=False
envdir=W/'环境'
assert digest(T/'环境/模型校验码.json')==REGISTRY_SHA
if envdir.exists():assert digest(envdir/'模型校验码.json')==REGISTRY_SHA
scratch.mkdir()
report = {
    'kind': 'source48_current513d_only_current_S10_restorer_original_cached_scalar',
    'article': '48', 'book_order': 42, 'helper_sha256': digest(__file__),
    'diagnostic_only': True, 'production_delivery_eligible': False,
    'quality_acceptance': False, 'formal_2ASR8R_full_native_and_V3_not_replaced': True,
    'source_request_sha256': NEW_SHA, 'baseline_current_request_sha256': OLD_SHA,
    'baseline_role': 'Prior0193 is readonly correct-mother/source ancestry; only current57f6 actual physical reference is used; no prior baseline is rebuilt.',
    'baseline_is_historical_legacy_f7d': False,
    'exact_private_cache_identity_sha256': IDENTITY_SHA,
    'actual_correct_context_gain_reselection_decision_sha256': GAIN_DECISION_SHA,
    'original_dictionary_sha256': DICT_SHA, 'context_dictionary_sha256': CTX_SHA,
    'original_old_cache_registry_sha256': OLD_REGISTRY_SHA,
    'prior_plain_context_identity_c6cb_and_freeze0fff_not_used': True,
    'required_five_new_S15_private_cache_files': required,
    'actual_source_installed_whole3089_tuple_measurement_sha256':digest(args.whole_tuple_measurement),
    'original_small55b4_is_history_not_whole_binding':True,
    'same_original_maker_sha256': MAKER_SHA,
    'required_original_fivecore_contract_sha256': CORE_CONTRACT_SHA,
    'actual_original_fivecore_seven_runtime_files': FIVECORE_FILES,
    'source16_sixcore_or_source17_profile_used': False,
    'old_and_new_model_inference_forbidden': True,
    'raw_PCM_GT_models_or_private_cache_bytes_not_exported': True,
    'phases': {}, 'errors': [],
}
phase_arrays = {}
used = {}


assert digest(args.whole_report)=='57f6f444908d130a327a172a7e2d9e871eb80ded982f515fb101c3e72c292655'
whole=json.loads(args.whole_report.read_text());actual=whole['phases']['selected_four_protection']
assert whole['exact_scope_proved'] is True and whole['errors']==[]
assert actual['actual_complete_WAV']['file_sha256']=='f8a78e41fad39456656a3063817678023403bed0bc657ebc240e85c97ea20cfe'
assert actual['actual_complete_AAC']['AAC_ADTS_sha256']=='d77ff0f972b81aa5c44a6203b01ca2a55266862817d9650fac37e970cd449b4f'
assert digest(args.failed_source)=='ecd41e64c7787233054975d4b02998a1767a9fb1c7b304f3568e81eb498b950e'
assert digest(args.failed_proof)=='1e0ee40d157a39f09589bdbece6d2f5e5935d99a24f4d18c667de59459395ca1'
failed_source=json.loads(args.failed_source.read_text());failed_proof=json.loads(args.failed_proof.read_text())
assert failed_proof['acceptance'] is False and failed_proof['passed'] is False
assert failed_proof['official_fingerprint_matches_current_video_source_and_pcm'] is True
assert failed_proof['source_sha256']==digest(args.failed_source)
assert failed_proof['internal_pcm_sha256']==actual['actual_complete_WAV']['file_sha256']
assert failed_proof['aac_adts_sha256']==actual['actual_complete_AAC']['AAC_ADTS_sha256']
assert failed_source['sentences'][9]==new['sentences'][9]
assert failed_source['非人声区间']['S10']==new['非人声区间']['S10']
assert failed_source['核对确认']['机器复听']['S10']['配音指纹']=='8253a58195c8'
assert digest(T/'疑点清单.py')=='c55db5722dd2792d51d12efc3ea8225edb1bcec236b69c684ee220f79cf6ecea'
assert digest(args.windows)==WINDOW_INPUT_SHA
selection=json.loads(args.windows.read_text())
assert selection['source_request_sha256']==NEW_SHA
assert selection['sentence_ids']==['S10']and selection['raw_w_window_seconds']==[7.75,8.45]
assert selection['actual_current_WAV_FP']=='513d66309055'
assert selection['expected_S10']==actual['observed_sentences']['S10']
assert selection['expected_S10_clock']==actual['actual_sample_clock']['S10']
assert selection['actual077_report_sha256']=='077cabca58a700b7b3f0b84f4cf39460e05d3f442a9197204bbad20cb5e05326'
priorcase=selection['expected_actual077_S10_case']
assert priorcase['sentence']=='S10'and priorcase['raw_w_fingerprint']==selection['expected_S10']['actual_raw_w_fingerprint']
assert priorcase['actual_pre_master_PCM_sha256']==selection['expected_S10']['pre_master_PCM_sha256']and priorcase['actual_post_master_float_PCM_sha256']==selection['expected_S10_clock']['observed_post_master_float_PCM_sha256']
assert priorcase['samples']==selection['expected_S10']['samples']and priorcase['actual_sentence_start_sample']==selection['expected_S10_clock']['start_sample']and priorcase['exact_to_current57f6']is True
assert digest(args.S9_cache_save)=='0587799ef08a4c86d5a0102c13f6edf0a7a47187f8f9e723b6d276e8d21a28a8'
save=json.loads(args.S9_cache_save.read_text())
assert save['private_key']=='Linux-native48-four-protection-S9-G51-43663443133'
assert save['filename']=='调平_f17212ff25b6c3d8b0582cdfcfff978551a0ecac.json'
assert digest(CACHE/save['filename'])==save['SHA256']=='44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
assert json.loads((CACHE/save['filename']).read_text())=={}
cases=['S10']
expected_cache={row['name']:row for row in whole['actual_used_source48_private_cache_entries_scalar_only']}
report['actual_current_whole_report_sha256']=digest(args.whole_report)
report['actual_failed_formal_source_sha256']=digest(args.failed_source)
report['actual_failed_formal_proof_sha256']=digest(args.failed_proof)
report['exact_window_selection_sha256']=digest(args.windows)
report['source_CF_or_physical_controls_written']=False
report['old_8253_machine_CF_is_history_not_renewed']=True
report['scope']='Only one current4980 S10 cached sentence, original raw w7.75-8.45 spectrum/wordslot and original mapper scalar. Current pre/post hard57f6; no whole/GT/TTS/newG36/encoding/render, no8253 renewal or sourceCF mutation.'
raw_store={};active_sid=None;active_sent=None
try:
    if not envdir.exists():envdir.symlink_to(T/'环境',target_is_directory=True);environment_link_created=True
    if scripts_was_symlink:
        other_json_bytes={p.name:p.read_bytes()for p in scripts.glob('*.json')if p.name!='48.json'}
        scripts.rename(prior_scripts_link);scripts.mkdir()
        for name,content in other_json_bytes.items():(scripts/name).write_bytes(content)
        source_isolated=True
    else:
        if source.exists()or source.is_symlink():source.rename(prior_source_entry)
        source_isolated=True
    source.write_bytes(new_source_bytes);assert digest(source)==NEW_SHA
    os.chdir(W);sys.path.insert(0,str(W))
    for name in ('render','title2','clean','出片指纹'):sys.modules.pop(name,None)
    spec0=importlib.util.spec_from_file_location('only48_old11_original',W/'make_video.py');m=importlib.util.module_from_spec(spec0);sys.modules[spec0.name]=m;spec0.loader.exec_module(m)
    assert m.PRON_WORDS['Yuan']=='juːˈɑːn'and digest(m._OLDF)==OLD_REGISTRY_SHA and digest(m._CTX_PATH)==CTX_SHA
    m._REPO_CACHE=str(M/'forbid-public-private-cache-export');assert not Path(m._REPO_CACHE).exists()
    np,SR=m.np,m.SR
    for method,obj,model in [('create',m.k,'kokoro-v1.0.onnx'),('create_timed',m.KT,'kokoro-v1.0-timed.onnx')]:
        original=getattr(obj,method)
        def guard(text,voice,speed=1.0,lang='en-us',_fn=original,_method=method,_model=model,**kw):
            assert os.environ.get('STRICT_CACHE')=='1'and lang=='en-us'and np.array_equal(voice,m.V)
            captured=[]
            def capture(actual_text,voice,speed=1.0,lang='en-us',**actual_kw):
                mid=m._portable_mid(str(M/'tts'/_model));vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                key=hashlib.sha1(repr((_method,mid,actual_text,vh,float(speed),lang,sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
                assert key in expected_cache and(CACHE/key).is_file(),'Only actual295 cached input permitted: '+key
                row=expected_cache[key];assert digest(CACHE/key)==row['sha256']and row['method']==_method
                assert hashlib.sha256(actual_text.encode()).hexdigest()==row['actual_model_input_sha256']
                if row.get('single_thread_marker_sha256'):assert digest(CACHE/(key+'.单线程'))==row['single_thread_marker_sha256']
                m._条目核对(str(CACHE/key));captured.append(key)
            m._pron(capture)(text,voice=voice,speed=speed,lang=lang,**kw);assert len(captured)==1
            used[captured[0]]={'name':captured[0],'sha256':digest(CACHE/captured[0]),'method':_method,'actual_model_input_sha256':expected_cache[captured[0]]['actual_model_input_sha256']}
            value=_fn(text,voice=voice,speed=speed,lang=lang,**kw)
            if _method=='create'and active_sid is not None and active_sid!='S17'and text==m.spoken(active_sent):raw_store[active_sid]=np.asarray(value[0],np.float32).copy()
            return value
        setattr(obj,method,guard)
    import ast
    dossier=ast.parse((T/'疑点清单.py').read_text());nodes=[n for n in dossier.body if isinstance(n,ast.FunctionDef)and n.name in ('to_w','words','per','spec')]
    assert len(nodes)==4;env={'np':np,'SR':SR};mod=ast.Module(body=nodes,type_ignores=[]);ast.fix_missing_locations(mod);exec(compile(mod,str(T/'疑点清单.py'),'exec'),env)
    per,spectral,words,to_w=(env[n]for n in ('per','spec','words','to_w'))
    report['case_identity']=[];report['restorer_raw_profiles']=[]
    for sid in cases:
        active_sid=sid;si=int(sid[1:])-1
        sent=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in new['sentences'][si]['chunks']);active_sent=sent
        assert m.SENT_NO[sent]=='48'
        pieces=[];gaps=[];p0=0;listing=m.list_commas(sent)
        for match in m.re.finditer(r'[,;:](?=\s)',sent):pieces.append((p0,match.end()));p0=match.end()+1;gaps.append(m.P_LIST if match.start()in listing else m.P_COMMA)
        pieces.append((p0,len(sent)))
        clips,tmap=m.sentence_audio(sent,pieces,gaps)
        _,pcm,auto,manual=m.句增益(new,'48',si,sent,pieces,gaps,clips,tmap,np.concatenate(clips))
        ref=actual['observed_sentences'][sid];clock=actual['actual_sample_clock'][sid]
        assert hashlib.sha256(np.ascontiguousarray(pcm).tobytes()).hexdigest()==ref['pre_master_PCM_sha256']and len(pcm)==ref['samples']
        normalized=pcm/np.float32(actual['actual_original_mastering']['pre_master_absolute_peak'])*.89
        assert hashlib.sha256(np.ascontiguousarray(normalized).tobytes()).hexdigest()==clock['observed_post_master_float_PCM_sha256']
        assert sid in raw_store,'Original S17 ending raw or normal fullmother was not captured.'
        raw=raw_store[sid];w0=m.clean_tail(raw);head=m._head_offset(raw,w0);w=m._keep_tail(raw,w0,head)
        rawfp=hashlib.md5(np.ascontiguousarray(w).tobytes()).hexdigest()[:12];assert rawfp==ref['actual_raw_w_fingerprint']
        it={'segs':[tuple(x[:3])+(list(x[3]),)for x in m.LAST['segs']],'toks':[(x.phoneme,x.start,x.end)for x in m.LAST['toks']],'scale':m.LAST['scale'],'head':m.LAST['head']}
        F5=round(.005*SR);reference=float(np.sqrt(np.mean(w[:len(w)//F5*F5].reshape(-1,F5)**2,axis=1)).max())
        lv=lambda z:20*math.log10(float(np.sqrt(np.mean(z*z)))/reference+1e-9)if len(z)else-99.
        def profile(a,b):
            vals=[]
            for t in np.arange(max(0,a),min(len(w)/SR,b),.0025):
                i=round(float(t)*SR);x=w[i:i+60];c,lo=spectral(w[max(0,i-90):i+150]);pp=per(w[max(0,i-210):i+270]);zs=[round((i+j)/SR,6)for j in range(1,len(x))if x[j-1]*x[j]<=0]
                vals.append({'w_s':float(t),'dB_2_5ms':lv(x),'preceding5ms_dB':lv(w[max(0,i-120):i]),'following5ms_dB':lv(w[i:i+120]),'periodicity20ms':pp,'low150Hz_dB_10ms':lo,'centroid_Hz_10ms':c,'first4_zero_crossing_w_s':zs[:4]})
            return vals
        report['case_identity'].append({'sentence':sid,'raw_w_fingerprint':rawfp,'actual_pre_master_PCM_sha256':ref['pre_master_PCM_sha256'],'actual_post_master_float_PCM_sha256':clock['observed_post_master_float_PCM_sha256'],'samples':len(pcm),'exact_to_current57f6':True,'automatic_gain_dB':{str(k):v for k,v in auto.items()},'manual_gain_dB':manual,'actual_raw_cuts':[list(x)for x in m.LAST['cuts']],'actual_sentence_start_sample':clock['start_sample']})
        assert ref==selection['expected_S10']and clock==selection['expected_S10_clock']
        a,b=selection['raw_w_window_seconds'];lo,hi=round(a*SR),round(b*SR)
        assert 0<=lo<hi<=len(w)
        # The unchanged original to_w is evaluated on each actual output sample.
        # This is a local reverse lookup, not an invented alternate mapper.
        raw_indices=[];output_indices=[]
        for output_index in range(len(pcm)):
            wi=to_w(it,output_index/SR)
            if wi is not None and lo<=wi<hi:raw_indices.append(wi);output_indices.append(output_index)
        ri=np.asarray(raw_indices,dtype=np.int64);oi=np.asarray(output_indices,dtype=np.int64)
        wanted=np.arange(lo,hi,dtype=np.int64)
        assert len(ri)==len(wanted)and np.array_equal(ri,wanted),'Original mapper did not preserve the exact complete requested raw window.'
        selected_raw=w[ri];selected_pre=pcm[oi]
        expected_post=selected_raw/np.float32(actual['actual_original_mastering']['pre_master_absolute_peak'])*.89
        selected_post=normalized[oi]
        pre_diff=int(np.count_nonzero(selected_pre!=selected_raw));post_diff=int(np.count_nonzero(selected_post!=expected_post))
        bad_pre=np.flatnonzero(selected_pre!=selected_raw)
        bad_post=np.flatnonzero(selected_post!=expected_post)
        def mismatch_ranges(indices):
            out=[]
            if not len(indices):return out
            cuts=np.r_[0,np.flatnonzero(np.diff(indices)>1)+1,len(indices)]
            for x,y in zip(cuts[:-1],cuts[1:]):
                ids=indices[x:y];rr=selected_raw[ids];cc=selected_pre[ids]
                out.append({'raw_w_first_sample':int(ri[ids[0]]),'raw_w_end_sample_exclusive':int(ri[ids[-1]]+1),'raw_w_start_s':float(ri[ids[0]]/SR),'raw_w_end_s':float((ri[ids[-1]]+1)/SR),'samples':int(len(ids)),'current_output_first_last_indices':[int(oi[ids[0]]),int(oi[ids[-1]])],'raw_relative_RMS_dB':lv(rr),'current_relative_RMS_dB':lv(cc),'current_zero_sample_count':int(np.count_nonzero(cc==0)),'nonzero_changed_sample_count':int(np.count_nonzero(cc!=0)),'max_abs_difference':float(np.max(np.abs(cc-rr))),'raw_abs_peak':float(np.max(np.abs(rr)))})
            return out
        current_frames=[];raw_frames=profile(a,b)
        for frame in raw_frames:
            wi=round(frame['w_s']*SR)
            if not lo<=wi<hi:continue
            ci=int(oi[wi-lo]);x=pcm[ci:ci+60]
            c,lf=spectral(pcm[max(0,ci-90):ci+150]);pp=per(pcm[max(0,ci-210):ci+270])
            pc,plf=spectral(normalized[max(0,ci-90):ci+150]);pper=per(normalized[max(0,ci-210):ci+270])
            current_frames.append({'raw_w_s':frame['w_s'],'current_output_sample':ci,'current_global_s':float((clock['start_sample']+ci)/SR),'current_pre_dB_2_5ms_same_original_raw_reference':lv(x),'current_pre_preceding5ms_dB':lv(pcm[max(0,ci-120):ci]),'current_pre_following5ms_dB':lv(pcm[ci:ci+120]),'current_pre_periodicity20ms':pp,'current_pre_low150Hz_dB_10ms':lf,'current_pre_centroid_Hz_10ms':c,'current_post_dB_2_5ms_same_original_raw_reference':lv(normalized[ci:ci+60]),'current_post_preceding5ms_dB':lv(normalized[max(0,ci-120):ci]),'current_post_following5ms_dB':lv(normalized[ci:ci+120]),'current_post_periodicity20ms':pper,'current_post_low150Hz_dB_10ms':plf,'current_post_centroid_Hz_10ms':pc,'raw_current_mismatched_samples_in_2_5ms':int(np.count_nonzero(pcm[ci:ci+60]!=w[wi:wi+60]))})
        subwindows=[]
        for wa,wb in [(7.75,7.84),(7.84,8.23),(8.23,8.34),(8.34,8.45)]:
            ids=np.flatnonzero((ri>=round(wa*SR))&(ri<round(wb*SR)))
            rs=selected_raw[ids];cs=selected_pre[ids];ps=selected_post[ids];es=expected_post[ids]
            mismatch=cs!=rs
            subwindows.append({'raw_w_seconds':[wa,wb],'mapped_samples':int(len(ids)),'pre_mismatched_samples':int(np.count_nonzero(mismatch)),'post_mismatched_samples':int(np.count_nonzero(ps!=es)),'current_zero_at_raw_mismatch_samples':int(np.count_nonzero(cs[mismatch]==0)),'current_nonzero_at_raw_mismatch_samples':int(np.count_nonzero(cs[mismatch]!=0)),'raw_relative_RMS_dB':lv(rs),'current_pre_relative_RMS_dB':lv(cs),'current_post_relative_RMS_dB':lv(ps),'first_last_raw_mismatch_sample':[int(ri[ids[np.flatnonzero(mismatch)[0]]]),int(ri[ids[np.flatnonzero(mismatch)[-1]]])]if np.any(mismatch)else None})
        report['raw_current_comparison_PREASSERT']={'raw_window_sample_count':int(len(ri)),'four_exact_requested_subwindows':subwindows,'original_mapper_complete16800_positions_coverage_already_hard_passed':True,'actual_fullsentence_pre_post_and_rawfp_already_hard_passed':True,'pre_master_mismatched_samples':pre_diff,'post_master_mismatched_samples':post_diff,'all_current_mismatches_are_zeros':bool(len(bad_pre)>0 and np.all(selected_pre[bad_pre]==0)),'first_last_raw_mismatch_samples':[int(ri[bad_pre[0]]),int(ri[bad_pre[-1]])]if len(bad_pre)else None,'first16_raw_mismatch_indices':[int(x)for x in ri[bad_pre[:16]]],'last16_raw_mismatch_indices':[int(x)for x in ri[bad_pre[-16:]]],'pre_mismatch_ranges':mismatch_ranges(bad_pre),'post_mismatch_coordinates_with_raw_pre_context':mismatch_ranges(bad_post),'raw_window_float_SHA256':hashlib.sha256(np.ascontiguousarray(selected_raw).tobytes()).hexdigest(),'actual_pre_window_float_SHA256':hashlib.sha256(np.ascontiguousarray(selected_pre).tobytes()).hexdigest(),'raw_expected_normalized_window_SHA256':hashlib.sha256(np.ascontiguousarray(expected_post).tobytes()).hexdigest(),'actual_post_window_float_SHA256':hashlib.sha256(np.ascontiguousarray(selected_post).tobytes()).hexdigest(),'original_purify_static_rule':'Original4c85 _purify zeroes below-AUD_DB continuous runs>=15ms without changing length; to_w maps positions only. This static possibility is not asserted as the actual cause.','original_purify_or_other_transform_not_replayed_or_changed':True,'original_zero_difference_assertion_still_enforced_after_observation':True}
        token_slots=[{'phoneme':str(ph),'original_timed_start_s':float(st),'original_timed_end_s':float(en),'scaled_w_start_s':float((st*it['scale']*SR-it['head'])/SR),'scaled_w_end_s':float((en*it['scale']*SR-it['head'])/SR)}for ph,st,en in it['toks']if st is not None and en is not None and (en*it['scale']*SR-it['head'])/SR>=a-.025 and (st*it['scale']*SR-it['head'])/SR<=b+.025]
        word_slots=[{'phoneme_word':str(ph),'w_start_s':float(st),'w_end_s':float(en)}for ph,st,en in words(it)if en>=a-.025 and st<=b+.025]
        report['restorer_raw_profiles'].append({'sentence':sid,'current_whole_fingerprint_from_actual_failed_whole_not_local':'513d66309055','raw_w_span_s':[a,b],'raw_w_fingerprint':rawfp,'window_reference_definition':'Original c55 dossier per/spec functions; original 5ms-max reference of the unchanged current S10 raw w. Each frame includes 2.5ms RMS, 10ms spectrum and 20ms periodicity, with original numeric formulas.','raw_2_5ms_profile':raw_frames,'current_processed_2_5ms_profile_same_original_reference':current_frames,'nearby_cached_timed_word_slots_annotation_only':word_slots,'nearby_cached_timed_phoneme_slots_annotation_only':token_slots,'original_mapper_segments':it['segs'],'actual_raw_window_samples':hi-lo,'actual_mapped_window_samples':len(ri),'raw_indices_sha256':hashlib.sha256(ri.tobytes()).hexdigest(),'output_indices_sha256':hashlib.sha256(oi.tobytes()).hexdigest(),'raw_original_window_float_SHA256':hashlib.sha256(np.ascontiguousarray(selected_raw).tobytes()).hexdigest(),'actual_pre_master_window_float_SHA256':hashlib.sha256(np.ascontiguousarray(selected_pre).tobytes()).hexdigest(),'actual_post_master_window_float_SHA256':hashlib.sha256(np.ascontiguousarray(selected_post).tobytes()).hexdigest(),'raw_under_actual_original_mastering_window_float_SHA256':hashlib.sha256(np.ascontiguousarray(expected_post).tobytes()).hexdigest(),'window_pre_master_values_equal_raw':pre_diff==0,'window_pre_master_mismatched_samples':pre_diff,'window_post_master_values_equal_normalized_raw':post_diff==0,'window_post_master_mismatched_samples':post_diff,'first_last_output_indices':[int(oi[0]),int(oi[-1])],'first_last_global_sample_indices':[int(clock['start_sample']+oi[0]),int(clock['start_sample']+oi[-1])],'no_acoustic_or_semantic_acceptance_or_CF_written':True,'no_original_PCM_or_GT_exported_or_encoded':True})
        report['pre_assert_observation_complete']=True
        report['actual_used_private_cache_entries_scalar_only']=list(used.values())
        assert pre_diff==post_diff==0,'Current mapper output differs from original raw restorer window.'
    assert len(report['restorer_raw_profiles'])==1 and len(report['case_identity'])==1
    report['actual_used_private_cache_entries_scalar_only']=list(used.values())
    report['actual_new_model_inference_count']=0;report['new_G36_math_count']=0;report['whole_audio_not_rebuilt']=True;report['no_GT_or_render_or_source_CF_write']=True
    report['diagnostic_completed']=True
except BaseException as error:
    report['diagnostic_completed']=False;report['errors'].append({'type':type(error).__name__,'detail':str(error)});traceback.print_exc()
finally:
    if scripts_was_symlink:
        if prior_scripts_link.exists()or prior_scripts_link.is_symlink():
            if scripts.exists():
                assert not scripts.is_symlink()
                for p in scripts.iterdir():assert p.is_file()and p.suffix=='.json';p.unlink()
                scripts.rmdir()
            prior_scripts_link.rename(scripts)
    elif source_isolated:
        source.unlink(missing_ok=True)
        if prior_source_entry.exists()or prior_source_entry.is_symlink():prior_source_entry.rename(source)
    if environment_link_created:envdir.unlink()
    after=inventory();report['all_existing_private_cache_files_exact_before_after']=before_cache==after
    report['normal_W_scripts48_exact_restored']=source.read_bytes()==prior_source if prior_source is not None else not source.exists()
    report['normal_W_preexisting_work48_PCM_exact_restored']=digest(work/'a.wav')==prior_wav if prior_wav is not None else True
    report['all_other_W_source_scripts_exact']=all(Path(p).is_file()and digest(p)==v for p,v in other_scripts_before.items())
    report['original_maker_file_exact_after']=digest(W/'make_video.py')==MAKER_SHA
    report['all_original_seven_runtime_core_files_exact_after']={name:digest(T/name)for name in FIVECORE_FILES}==FIVECORE_FILES
    report['request_whole_and_failed_formal_proof_exact_after']=digest(request)==NEW_SHA and digest(args.whole_report)=='57f6f444908d130a327a172a7e2d9e871eb80ded982f515fb101c3e72c292655'and digest(args.failed_source)=='ecd41e64c7787233054975d4b02998a1767a9fb1c7b304f3568e81eb498b950e'and digest(args.failed_proof)=='1e0ee40d157a39f09589bdbece6d2f5e5935d99a24f4d18c667de59459395ca1'
    report['current_window_inputs_exact_after']=digest(args.windows)==WINDOW_INPUT_SHA
    report['exact_scope_proved']=bool(report.get('diagnostic_completed')and report['all_existing_private_cache_files_exact_before_after']and report['normal_W_scripts48_exact_restored']and report['normal_W_preexisting_work48_PCM_exact_restored']and report['all_other_W_source_scripts_exact']and report['original_maker_file_exact_after']and report['all_original_seven_runtime_core_files_exact_after']and report['request_whole_and_failed_formal_proof_exact_after']and report['current_window_inputs_exact_after'])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    print(json.dumps({'diagnostic_completed':report.get('diagnostic_completed'),'exact_scope_proved':report['exact_scope_proved'],'errors':report['errors'],'output_sha256':digest(args.output)},ensure_ascii=False))
sys.exit(0 if report['exact_scope_proved']else 1)
