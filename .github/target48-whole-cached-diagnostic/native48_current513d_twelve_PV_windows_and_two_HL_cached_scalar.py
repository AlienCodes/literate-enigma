"""Observe10 existing cached sentences for12 specific currentPV windows and2 currentG45 onsets; no whole build.

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
for key in ('tools', 'video-root', 'request', 'baseline-source', 'cache-identity', 'gain-decision', 'whole-tuple-measurement', 'whole-report', 'original-report2', 'pv-report', 'windows', 'S9-cache-save', 'prior-whole', 'output'):
    P.add_argument('--' + key, type=Path, required=True)
args = P.parse_args()
T, M = args.tools.resolve(), args.video_root.resolve()
W, CACHE = M / 'video', M / 'tts/cache_tts'
OLD_SHA = '0193cbd1859525690e12a470c517cce2f120a1054b204fcfa3c0c392c92abbd7'
NEW_SHA = '73ac6fe3fdc0d203eaa1d8a4de6399381f15a14140aaf2dbe6bc4fde30b16610'
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
scratch = M/'_source48_current513d_twelve_specific_PV_and_two_HL'
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
    'kind': 'source48_current513d_twelve_specific_PV_raw_windows_and_two_actual_G45_cached_sentence_scalar',
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




assert digest(args.whole_report)=='57f6f444908d130a327a172a7e2d9e871eb80ded982f515fb101c3e72c292655'
assert digest(args.original_report2)=='3b75c00018bcb4a1e88f64292a1aae6f7be7aa1627e133cf8e50b6380332a227'
whole=json.loads(args.whole_report.read_text());actual=whole['phases']['selected_four_protection']
audit=json.loads(args.original_report2.read_text());assert len(audit['texts'])==18 and len(audit['extra_runs'])==0
assert whole['exact_scope_proved']and whole['errors']==[]
programs={'纯人声核对.py':'1050d1df51eb21ed0dbd19e9a97a8325c4dbfa1f58e9834760f8e5e5ba0b414f','疑点清单.py':'c55db5722dd2792d51d12efc3ea8225edb1bcec236b69c684ee220f79cf6ecea'}
assert {name:digest(T/name)for name in programs}==programs

assert digest(args.pv_report)=='3f5b986629b1f0f2e97f48e2b15929ba16bf77419b87ab40f8acc9c6b6c5b44c'
assert digest(args.windows)=='27bc3b1932d7b8678395ebcfe5c18f34cb83262438cf3cbc05b043f85d10dad0'
assert digest(args.S9_cache_save)=='0587799ef08a4c86d5a0102c13f6edf0a7a47187f8f9e723b6d276e8d21a28a8'
assert digest(args.prior_whole)=='295fd087864e9ffbd2ad63edddb2da5d10af818b960c8a030e1ccdbd5537c591'
selection=json.loads(args.windows.read_text());fullPV=json.loads(args.pv_report.read_text());save=json.loads(args.S9_cache_save.read_text())
assert selection['actual_current_WAV_FP']==actual['actual_full_WAV_original_PV_fingerprint_md5_12']=='513d66309055'
assert save['private_key']=='Linux-native48-four-protection-S9-G51-43663443133'
assert save['filename']=='调平_f17212ff25b6c3d8b0582cdfcfff978551a0ecac.json'
assert digest(CACHE/save['filename'])==save['SHA256']=='44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
assert json.loads((CACHE/save['filename']).read_text())=={}
assert len(selection['PV_windows'])==12 and len(selection['HL_windows'])==2
cases=selection['sentence_ids'];assert cases==['S1','S3','S7','S8','S9','S10','S12','S13','S14','S17']
for row in selection['PV_windows']:
    assert row['exact_actual_original_flag']in fullPV['all_original_flags']
    assert row['sentence']==row['exact_actual_original_flag']['current_actual_sentence_clock'][0]['sentence']
prior=json.loads(args.prior_whole.read_text())['phases']['selected_new0193']
for row in selection['HL_windows']:
    sid=row['sentence'];assert row['prior295_start_sample']==prior['actual_sample_clock'][sid]['start_sample']
    assert row['actual57_start_sample']==actual['actual_sample_clock'][sid]['start_sample']
    assert row['exact_local_sample']==round(row['old_actual009254_onset_global_s']*24000)-row['prior295_start_sample']
    assert row['new_current_global_sample']==row['actual57_start_sample']+row['exact_local_sample']
    assert row['new_current_global_s']==row['new_current_global_sample']/24000

expected_cache={row['name']:row for row in whole['actual_used_source48_private_cache_entries_scalar_only']}
report['actual_current_whole_report_sha256']=digest(args.whole_report)
report['actual_current_full_PV_report_sha256']=digest(args.pv_report)
report['exact_window_selection_sha256']=digest(args.windows)
report['source_CF_or_physical_controls_written']=False
report['scope']='Only10 cached current73ac sentences for12 specified actual PV raw windows plusS10/S13 originalG45 currentclock. Each pre/postmaster hard57f6. No whole/GT/TTS/newG36/render, no8253 renewal or sourceCF mutation.'
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
            used[captured[0]]={'name':captured[0],'sha256':digest(CACHE/captured[0]),'method':_method}
            value=_fn(text,voice=voice,speed=speed,lang=lang,**kw)
            if _method=='create'and active_sid is not None and text==m.spoken(active_sent):raw_store[active_sid]=np.asarray(value[0],np.float32).copy()
            return value
        setattr(obj,method,guard)
    import ast
    dossier=ast.parse((T/'疑点清单.py').read_text());nodes=[n for n in dossier.body if isinstance(n,ast.FunctionDef)and n.name in ('to_w','words','per','spec')]
    assert len(nodes)==4;env={'np':np,'SR':SR};mod=ast.Module(body=nodes,type_ignores=[]);ast.fix_missing_locations(mod);exec(compile(mod,str(T/'疑点清单.py'),'exec'),env)
    per,spectral,words,to_w=(env[n]for n in ('per','spec','words','to_w'))
    pv_spec=importlib.util.spec_from_file_location('only48_old11_originalPV',T/'纯人声核对.py');pv=importlib.util.module_from_spec(pv_spec);pv_spec.loader.exec_module(pv)
    end_original=m._ending_raw
    def observed_ending(sent,params):
        value=end_original(sent,params)
        if active_sid=='S17':raw_store['S17']=np.asarray(value,np.float32).copy()
        return value
    m._ending_raw=observed_ending
    g45path=T/'高亮同步核对.py'
    assert digest(g45path)=='4ff2557b5373fc361491d248a52e301afb5ef33ed003513f93cbbbfc33e29893'
    defs=[n for n in ast.parse(g45path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name in ('是开口','确认可收')]
    assert len(defs)==2
    g45env={'np':np};mod45=ast.Module(body=defs,type_ignores=[]);ast.fix_missing_locations(mod45);exec(compile(mod45,str(g45path),'exec'),g45env)
    report['original_G45_program_sha256']=digest(g45path)
    report['original_G45_function_AST_sha256']={n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()for n in defs}
    report['case_identity']=[];report['specific_PV_raw_profiles']=[];report['actual_current_G45_highlights']=[]
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
        privatewav=scratch/(sid+'-original57f6-quantized-private.wav');m.sf.write(privatewav,normalized,SR);A,rate=m.sf.read(privatewav);assert rate==SR
        report['case_identity'].append({'sentence':sid,'raw_w_fingerprint':rawfp,'actual_pre_master_PCM_sha256':ref['pre_master_PCM_sha256'],'actual_post_master_float_PCM_sha256':clock['observed_post_master_float_PCM_sha256'],'samples':len(pcm),'exact_to_current57f6':True,'automatic_gain_dB':{str(k):v for k,v in auto.items()},'manual_gain_dB':manual,'actual_raw_cuts':[list(x)for x in m.LAST['cuts']],'actual_sentence_start_sample':clock['start_sample'],'original_S17_ending_raw_used':sid=='S17'})
        wanted=[r for r in selection['PV_windows']if r['sentence']==sid]
        if wanted:
            sparse=np.zeros(actual['actual_complete_WAV']['samples'],float);off=clock['start_sample'];sparse[off:off+len(A)]=A
            found=pv.scan(sparse)
            for row in wanted:
                flag=row['exact_actual_original_flag'];matches=[f for f in found if f[0]==flag['kind']and pv.key(f)==flag['key']];assert len(matches)==1
                f=matches[0];assert list(f)==flag['full_original_unrounded_tuple'],'Current actual fullPV tuple not reproduced '+flag['key']
                assert pv.实测(f)==flag['display_metrics']
                a=to_w(it,(round(f[1]*SR)-off)/SR);b=to_w(it,(round(f[2]*SR)-off-1)/SR)
                assert a is not None and b is not None;a,b=a/SR,(b+1)/SR
                report['specific_PV_raw_profiles'].append({'sentence':sid,'key':flag['key'],'actual_current_whole_fingerprint_from_actual_main_not_sparse':'513d66309055','full_original_unrounded_PV_tuple_exact_reproduced':list(f),'all_displayed_metrics_exact':pv.实测(f),'raw_w_span_s':[a,b],'raw_w_fingerprint':rawfp,'original_像吸气':pv.像吸气(f),'original_爆破起清':pv.爆破起(sparse,f),'original_爆破起浊':pv.爆破起(sparse,f,4*pv.F),'nearby_timed_words_annotation_only':[{'phoneme_word':p,'w_start_s':st,'w_end_s':en}for p,st,en in words(it)if en>a-.25 and st<b+.25],'raw_2_5ms_profile':profile(a-.08,b+.08),'no_new_semantic_classification_or_CF_written':True})
        for h in [h for h in selection['HL_windows']if h['sentence']==sid]:
            t=h['exact_local_sample']/SR;assert h['new_current_global_sample']==clock['start_sample']+h['exact_local_sample']
            assert t-2>=0 and t+2<=len(A)/SR
            accepted=bool(g45env['确认可收']('48',A,SR,t));i=round(t*SR);local=A[i-2*SR:i+2*SR];n=len(local)//(2*F5);pk=float(np.sqrt(np.mean(local[:n*2*F5].reshape(n,2*F5)**2,axis=1)).max()+1e-12)
            frames=[{'start_global_s':(clock['start_sample']+x)/SR,'relative_5ms_RMS_dB':20*math.log10(float(np.sqrt(np.mean(A[x:x+F5]**2)))/pk+1e-12)}for x in range(i-6*F5,i+8*F5,F5)]
            report['actual_current_G45_highlights'].append({'sentence':sid,'new_current_global_sample':h['new_current_global_sample'],'new_current_global_s':h['new_current_global_sample']/SR,'actual_original_G45_acceptance':accepted,'actual_current57f6_pre_and_post_identity':True,'original_G45_5ms_frames':frames,'original_local_reference_peak':pk,'source_or_HL_CF_not_written':True})
            assert accepted,'Actual current originalG45 rejected selectedonset '+sid
    assert len(report['specific_PV_raw_profiles'])==12 and len(report['actual_current_G45_highlights'])==2 and len(report['case_identity'])==10
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
    report['request_whole_and_original_report2_exact_after']=digest(request)==NEW_SHA and digest(args.whole_report)=='57f6f444908d130a327a172a7e2d9e871eb80ded982f515fb101c3e72c292655'and digest(args.original_report2)=='3b75c00018bcb4a1e88f64292a1aae6f7be7aa1627e133cf8e50b6380332a227'
    report['current_window_inputs_exact_after']=digest(args.windows)=='27bc3b1932d7b8678395ebcfe5c18f34cb83262438cf3cbc05b043f85d10dad0'and digest(args.pv_report)=='3f5b986629b1f0f2e97f48e2b15929ba16bf77419b87ab40f8acc9c6b6c5b44c'
    report['exact_scope_proved']=bool(report.get('diagnostic_completed')and report['all_existing_private_cache_files_exact_before_after']and report['normal_W_scripts48_exact_restored']and report['normal_W_preexisting_work48_PCM_exact_restored']and report['all_other_W_source_scripts_exact']and report['original_maker_file_exact_after']and report['all_original_seven_runtime_core_files_exact_after']and report['request_whole_and_original_report2_exact_after']and report['current_window_inputs_exact_after'])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    print(json.dumps({'diagnostic_completed':report.get('diagnostic_completed'),'exact_scope_proved':report['exact_scope_proved'],'errors':report['errors'],'output_sha256':digest(args.output)},ensure_ascii=False))
sys.exit(0 if report['exact_scope_proved']else 1)
