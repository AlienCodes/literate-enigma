"""Observe two original AUDIO_ONLY builds; export only genuine whole-track scalars.

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
for key in ('tools', 'video-root', 'request', 'baseline-source', 'cache-identity', 'gain-decision', 'whole-tuple-measurement', 'whole-report', 'failed-proof', 'output'):
    P.add_argument('--' + key, type=Path, required=True)
args = P.parse_args()
T, M = args.tools.resolve(), args.video_root.resolve()
W, CACHE = M / 'video', M / 'tts/cache_tts'
OLD_SHA = '4f146ce6a70bb0bf5d2c6e1f6b47bd6a2bcc2f311be7a948092d7bde1a08f449'
NEW_SHA = '0193cbd1859525690e12a470c517cce2f120a1054b204fcfa3c0c392c92abbd7'
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
assert identity['request_source_sha256'] == NEW_SHA
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
assert changed_English == [15]
assert plain(new)[14] == identity['exact_new_plain_English']
assert new['分段增益dB']['S15'] == {'1': 1.0}
assert 'S15' not in new.get('非人声区间', {}) and 'S15' not in new.get('区间声音指纹', {})
assert '130.59–130.60s' not in new['核对确认'].get('非人声', {})

# All rejectable preflight happens before normal-native namespace mutation.
# Each phase retains original source-first / fresh-import ordering.
scratch = M/'_source48_only_S15_spectral_PV_scalar'
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
    'kind': 'source48_only_correct_S15_existing_PV_flags_cached_original_spectral_scalar_diagnostic',
    'article': '48', 'book_order': 42, 'helper_sha256': digest(__file__),
    'diagnostic_only': True, 'production_delivery_eligible': False,
    'quality_acceptance': False, 'formal_2ASR8R_full_native_and_V3_not_replaced': True,
    'source_request_sha256': NEW_SHA, 'baseline_current_request_sha256': OLD_SHA,
    'baseline_role': 'Original current4f strict-cached reproduction, not an accepted legacy video/audio.',
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



assert digest(args.whole_report)=='295fd087864e9ffbd2ad63edddb2da5d10af818b960c8a030e1ccdbd5537c591'
assert digest(args.failed_proof)=='abca791f93135f13e69026c912e4e5bec2558a2d41de9044373fd17861220aca'
whole=json.loads(args.whole_report.read_text());failed=json.loads(args.failed_proof.read_text())
assert whole['diagnostic_completed'] and whole['exact_scope_proved']and whole['errors']==[]
actual=whole['phases']['selected_new0193'];target=actual['observed_sentences']['S15'];clock=actual['actual_sample_clock']['S15']
assert failed['internal_pcm_sha256']==actual['actual_complete_WAV']['file_sha256']
assert failed['aac_adts_sha256']==actual['actual_complete_AAC']['AAC_ADTS_sha256']
assert failed['video_sha256']=='02246013ab9a58b57f604cc916ad2adca84597b6b668338c2f7f3e8523a1b2dc'
programs={'纯人声核对.py':'1050d1df51eb21ed0dbd19e9a97a8325c4dbfa1f58e9834760f8e5e5ba0b414f',
          '疑点清单.py':'c55db5722dd2792d51d12efc3ea8225edb1bcec236b69c684ee220f79cf6ecea',
          '逐段看声音.py':'9f956136a1de9d2a886509b99c3023dd0a19b5d1f6aa6e2a55f8755b2148d295'}
assert {name:digest(T/name)for name in programs}==programs
report['existing_actual_failed_video_proof_sha256']=digest(args.failed_proof)
report['actual_complete_strict_whole_report_sha256']=digest(args.whole_report)
report['original_diagnostic_programs']=programs
report['scope']='Only existing S15 raw/timed cached sentence; original source-installed treatment+G36/manual gain, exact actual S15 PCM hash and actual master coefficient. Sparse zero context for original local PV scan; never rebuild other sentences or full whole audio.'
report['private_raw_mother_PCM_PKL_GT_or_audio_windows_exported']=False
report['source_or_CF_or_NV_written']=False
report['human_voice_noise_classification_pending']=True
report['formal_gates_or_acceptance_not_replaced']=True
try:
    if not envdir.exists():
        envdir.symlink_to(T/'环境',target_is_directory=True);environment_link_created=True
    assert digest(envdir/'模型校验码.json')==REGISTRY_SHA
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
    s=importlib.util.spec_from_file_location('only48_S15_spectral_original',W/'make_video.py');m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
    assert m.PRON_WORDS['Yuan']=='juːˈɑːn'and digest(m._OLDF)==OLD_REGISTRY_SHA and digest(m._CTX_PATH)==CTX_SHA
    m._REPO_CACHE=str(M/'forbid-public-private-cache-export');assert not Path(m._REPO_CACHE).exists()
    np,SR=m.np,m.SR
    sent=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in new['sentences'][14]['chunks'])
    assert sent==identity['exact_new_plain_English']and m.SENT_NO[sent]=='48'and m.余音删法(sent)is True
    expected_mothers={r['method']:r for r in identity['cache_entries']}
    for method,obj,model in [('create',m.k,'kokoro-v1.0.onnx'),('create_timed',m.KT,'kokoro-v1.0-timed.onnx')]:
        original=getattr(obj,method)
        def guard(text,voice,speed=1.0,lang='en-us',_fn=original,_method=method,_model=model,**kw):
            assert os.environ.get('STRICT_CACHE')=='1'
            assert text==m.spoken(sent)and speed==m.SPEED and lang=='en-us'and np.array_equal(voice,m.V)
            captured=[]
            def capture(actual_text,voice,speed=1.0,lang='en-us',**actual_kw):
                mid=m._portable_mid(str(M/'tts'/_model));vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                key=hashlib.sha1(repr((_method,mid,actual_text,vh,float(speed),lang,sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
                row=expected_mothers[_method]
                assert key==row['exact_cache_key']and (CACHE/key).is_file(),'Only existing exact S15 mother authorized.'
                assert digest(CACHE/key)==row['actual_pkl_sha256']and digest(CACHE/(key+'.单线程'))==row['actual_marker_sha256']
                assert hashlib.sha256(actual_text.encode()).hexdigest()==identity['post_pron_input_sha256']
                m._条目核对(str(CACHE/key));captured.append(key)
            m._pron(capture)(text,voice=voice,speed=speed,lang=lang,**kw);assert len(captured)==1
            used[captured[0]]={'name':captured[0],'sha256':digest(CACHE/captured[0]),'method':_method,'strict_cache_read_only':True}
            return _fn(text,voice=voice,speed=speed,lang=lang,**kw)
        setattr(obj,method,guard)
    # Original build parsing, original sentence processing and strict original gains.
    pieces=[];gaps=[];p0=0;listing=m.list_commas(sent)
    for match in m.re.finditer(r'[,;:](?=\s)',sent):
        pieces.append((p0,match.end()));p0=match.end()+1;gaps.append(m.P_LIST if match.start()in listing else m.P_COMMA)
    pieces.append((p0,len(sent)))
    raw,_=m.k.create(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us')
    w0=m.clean_tail(raw);w=m._keep_tail(raw,w0,m._head_offset(raw,w0))
    assert hashlib.md5(np.ascontiguousarray(w).tobytes()).hexdigest()[:12]=='4e8bece5aaea'
    clips,tmap=m.sentence_audio(sent,pieces,gaps)
    clips,pcm,auto,manual=m.句增益(new,'48',14,sent,pieces,gaps,clips,tmap,np.concatenate(clips))
    assert hashlib.sha256(np.ascontiguousarray(pcm).tobytes()).hexdigest()==target['pre_master_PCM_sha256']
    assert len(pcm)==target['samples']and {str(k):v for k,v in auto.items()}==target['automatic_gain_dB']and manual==target['manual_gain_dB']
    assert [list(x)for x in m.LAST['cuts']]==target['actual_raw_cuts']
    normalized=pcm/np.float32(actual['actual_original_mastering']['pre_master_absolute_peak'])*.89
    assert hashlib.sha256(np.ascontiguousarray(normalized).tobytes()).hexdigest()==clock['observed_post_master_float_PCM_sha256']
    # The private only-S15 WAV has no artifact path: same original PCM16 writer as
    # whole production, no filtering, smoothing, noise removal or audio mutation.
    privatewav=scratch/'only-S15-original-quantization-private.wav';m.sf.write(privatewav,normalized,SR)
    quantized,rate=m.sf.read(privatewav);assert rate==SR
    assert len(quantized)==len(pcm)
    assert abs(np.max(np.abs(quantized-normalized)))<=1/32768+1e-9
    pv_spec=importlib.util.spec_from_file_location('only48_actual_original_PV',T/'纯人声核对.py');pv=importlib.util.module_from_spec(pv_spec);pv_spec.loader.exec_module(pv)
    # Sparse context contains only zeros and this exact S15 PCM16 slice. It gives
    # the original scan the same sentence boundary/frame phase/global clock.
    sparse=np.zeros(actual['actual_complete_WAV']['samples'],float)
    off=clock['start_sample'];sparse[off:off+len(quantized)]=quantized
    candidates=pv.scan(sparse)
    expected={('呼吸声','124.64–124.72s'),('噗声','124.68–124.70s'),('噗声','124.70–124.72s'),('噗声','124.73–124.75s'),('噗声','131.04–131.05s')}
    assert {(f[0],pv.key(f))for f in candidates}==expected,'Local original scan must reproduce exactly the five actual S15 flags.'
    import ast
    dossier=ast.parse((T/'疑点清单.py').read_text());selected=[x for x in dossier.body if isinstance(x,ast.FunctionDef)and x.name in ('to_w','words','per','spec')]
    assert len(selected)==4
    namespace={'np':np,'SR':SR};module=ast.Module(body=selected,type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,str(T/'疑点清单.py'),'exec'),namespace)
    it={'segs':[tuple(x[:3])+(list(x[3]),)for x in m.LAST['segs']],
        'toks':[(x.phoneme,x.start,x.end)for x in m.LAST['toks']], 'scale':m.LAST['scale'],'head':m.LAST['head']}
    to_w,words,per,spec=(namespace[name]for name in ('to_w','words','per','spec'))
    F5=int(.005*SR);ref=float(np.sqrt(np.mean(w0[:len(w0)//F5*F5].reshape(-1,F5)**2,axis=1)).max())
    lv=lambda x:20*math.log10(float(np.sqrt(np.mean(x*x)))/ref+1e-9)if len(x)else-99.
    report['actual_S15_identity']={'plain_English':sent,'source_installed_SENT_NO':m.SENT_NO[sent],
        'raw_w_fingerprint':m.SENT_FP[sent],'pre_master_PCM_sha256':target['pre_master_PCM_sha256'],
        'post_master_float_PCM_sha256':clock['observed_post_master_float_PCM_sha256'],'actual_original_auto':{str(k):v for k,v in auto.items()},
        'actual_manual':manual,'actual_raw_cuts':[list(x)for x in m.LAST['cuts']],
        'actual_sample_clock':clock,'original_raw_head_samples':it['head'],'raw_tokens_scale':it['scale'],
        'all_actual_pre_and_post_master_S15_scalar_hashes_exact_to295':True}
    rows=[];window_spans=[]
    for f in candidates:
        tc0=(round(f[1]*SR)-off)/SR;tc1=(round(f[2]*SR)-off)/SR
        p0=to_w(it,tc0);p1=to_w(it,max(tc0,tc1-1/SR));assert p0 is not None and p1 is not None
        a,b=p0/SR,(p1+1)/SR;window_spans.append((max(0,a-.08),min(len(w0)/SR,b+.08)))
        nearby=[{'phoneme_word':ph,'w_start_s':st,'w_end_s':en}for ph,st,en in words(it)if en>a-.35 and st<b+.35]
        nearbyphones=[{'phoneme':x,'w_start_s':(st*it['scale']*SR-it['head'])/SR,'w_end_s':(en*it['scale']*SR-it['head'])/SR}for x,st,en in it['toks']if x.strip()and(en*it['scale']*SR-it['head'])/SR>a-.2 and(st*it['scale']*SR-it['head'])/SR<b+.2]
        rows.append({'original_kind':f[0],'actual_global_key':pv.key(f),'actual_global_span_s':[f[1],f[2]],
            'actual_original_PV_metrics':pv.实测(f),'raw_w_span_s':[a,b],'original_to_w_sample_positions':[p0,p1+1],
            'nearby_original_timed_words':nearby,'nearby_original_timed_phonemes':nearbyphones,
            'original_像吸气':bool(pv.像吸气(f)),
            'original_贴词头':bool(pv.贴词头(sparse,f)),'original_爆破起清塞音':bool(pv.爆破起(sparse,f)),
            'original_爆破起浊塞音':bool(pv.爆破起(sparse,f,4*pv.F)),
            'original_贴词尾擦音':bool(pv.贴词尾擦音(sparse,f)),
            'classification_or_confirmation_not_authored':True})
    merged=[]
    for a,b in sorted(window_spans):
        if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
        else:merged.append([a,b])
    profiles=[]
    for a,b in merged:
        values=[]
        for t in np.arange(a,b,.0025):
            i=round(float(t)*SR);x=w0[i:i+60];cent,low=spec(w0[max(0,i-90):i+150])if i>90 else(0.,0.)
            zeros=[round((i+j)/SR,6)for j in range(1,len(x))if x[j-1]*x[j]<=0]
            values.append({'w_s':float(t),'dB_2_5ms':lv(x),'preceding5ms_dB':lv(w0[max(0,i-120):i]),
                'following5ms_dB':lv(w0[i:i+120]),'periodicity20ms':per(w0[max(0,i-210):i+270]),
                'low150Hz_dB_10ms':low,'centroid_Hz_10ms':cent,'first4_zero_crossing_w_s':zeros[:4]})
        profiles.append({'actual_w_window_s':[a,b],'original_dossier_functions':'per/spec/to_w/words exact AST from pinned c55db script','profile':values})
    report['actual_five_original_PV_flags']=rows
    report['actual_raw_w_scalar_profiles']=profiles
    report['global_whole_audio_not_rebuilt']=True
    report['onlyS15_sparse_scan_is_diagnostic_not_wholefp_or_acceptance']=True
    report['original_spectral_labels_not_treated_as_noise_or_confirmation']=True
    report['actual_new_model_inference_count']=0
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
    report['original_request_baseline_whole_and_proof_exact_after']=digest(request)==NEW_SHA and digest(args.baseline_source)==OLD_SHA and digest(args.whole_report)=='295fd087864e9ffbd2ad63edddb2da5d10af818b960c8a030e1ccdbd5537c591'and digest(args.failed_proof)=='abca791f93135f13e69026c912e4e5bec2558a2d41de9044373fd17861220aca'
    report['exact_scope_proved']=bool(report.get('diagnostic_completed')and report['all_existing_private_cache_files_exact_before_after']and report['normal_W_scripts48_exact_restored']and report['normal_W_preexisting_work48_PCM_exact_restored']and report['all_other_W_source_scripts_exact']and report['original_maker_file_exact_after']and report['all_original_seven_runtime_core_files_exact_after']and report['original_request_baseline_whole_and_proof_exact_after'])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    print(json.dumps({'diagnostic_completed':report.get('diagnostic_completed'),'exact_scope_proved':report['exact_scope_proved'],'errors':report['errors'],'output_sha256':digest(args.output),'source_CF_audio_change':False},ensure_ascii=False))
sys.exit(0 if report['exact_scope_proved']else 1)
