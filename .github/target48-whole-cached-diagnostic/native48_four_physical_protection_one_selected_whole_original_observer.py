"""Observe one selected original AUDIO_ONLY build; export only actual voice/clock scalars.

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
for key in ('tools', 'video-root', 'request', 'baseline-source', 'cache-identity', 'gain-decision', 'whole-tuple-measurement', 'whole-reference', 'three-local-report', 'S13-local-report', 'physical-selection', 'source-freeze', 'output'):
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
assert identity['request_source_sha256'] == OLD_SHA, 'The unchanged mother identity belongs to prior0193; new73ac changes only4 NV controls.'
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

assert digest(args.whole_reference)=='295fd087864e9ffbd2ad63edddb2da5d10af818b960c8a030e1ccdbd5537c591'
assert digest(args.three_local_report)=='7a570f33c18598db9796fa2d26ab9aee5ca34323af5d6ed6f024d635b99bd7b7'
assert digest(args.S13_local_report)=='be565ef812107585735061f6e01fb2a25d613a6a69ce0a8b422e22947a788dd5'
assert digest(args.physical_selection)=='11df709068690c56d4ee5be2cd2b46e19ddaf105e11ab8f7e5330ff392ec3f66'
assert digest(args.source_freeze)=='d0d614e58f0cef3b711fb3e9035dd527dcadb7ffa1b346704ba99a096eca664e'
reference=json.loads(args.whole_reference.read_text())['phases']['selected_new0193']
physical=json.loads(args.physical_selection.read_text())
assert physical['baseline_source_SHA256']==OLD_SHA and physical['no_CF_adoption_in_this_selection']is True
assert physical['only_possible_new_math']=='Only original S9 auto-level for exact eeef output/214200 new tuple, if cache truly absent; must produce{} or hard-stop. No old cache renaming, S15 or other math/TTS.'
local_rows={x['sentence']:x for p in (args.three_local_report,args.S13_local_report)for x in json.loads(p.read_text())['cases']}
assert set(local_rows)=={'S9','S10','S12','S13'}
for selected in physical['selected_exact_controls']:
    sid=selected['sentence'];assert old['非人声区间'][sid]==selected['current_authored_NV']
    assert new['非人声区间'][sid]==selected['unique_in_memory_candidate_NV']
    assert local_rows[sid]['candidate_pre_level_output_sha256_NOT_final_mastered']==selected['candidate_pre_level_output_sha256_NOT_final_mastered']
    assert local_rows[sid]['preserved_raw_w_sample_range']==selected['preserved_raw_w_sample_range']
restored_original=copy.deepcopy(new);restored_original['非人声区间']=old['非人声区间'];assert restored_original==old
expected_cache={x['name']:x for x in json.loads(args.whole_reference.read_text())['actual_used_source48_private_cache_entries_scalar_only']}
protected=['title']+['S'+str(i)for i in range(1,18)if'S'+str(i)not in local_rows]
assert len(protected)==14

# All rejectable preflight happens before normal-native namespace mutation.
# Each phase retains original source-first / fresh-import ordering.
scratch = M/'_source48_selected_four_protection_one_whole_diagnostic'
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
    'kind': 'source48_four_actual_local_protection_selected_only_strict_cached_original_whole_observer',
    'article': '48', 'book_order': 42, 'helper_sha256': digest(__file__),
    'diagnostic_only': True, 'production_delivery_eligible': False,
    'quality_acceptance': False, 'formal_2ASR8R_full_native_and_V3_not_replaced': True,
    'source_request_sha256': NEW_SHA, 'baseline_current_request_sha256': OLD_SHA,
    'baseline_role': 'Prior0193 actual295 is a scalar physical-identity reference only; no baseline AudioOnly rebuild. Accepted legacy provenance remains separate.',
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
allowed_new_S9_cache = {}
report['prior0193_whole_reference_only_not_rebuilt']=True
report['root_four_physical_selection_sha256']=digest(args.physical_selection)
report['source_and_GEN_only_four_NV_freeze_sha256']=digest(args.source_freeze)
report['local_candidate_reports_sha256']=[digest(args.three_local_report),digest(args.S13_local_report)]
report['actual_fresh_final_four_restored_ranges_vs_raw_required']=True


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


def run_phase(label, input_bytes, expected_source):
    gc.collect()
    source.write_bytes(input_bytes)
    assert digest(source) == expected_source
    os.chdir(W)
    sys.path.insert(0, str(W))
    # These original modules carry mutable render state; each build gets a fresh
    # import of the exact same physical native runtime bytes.
    for module in ('render', 'title2', 'clean', '出片指纹'):
        sys.modules.pop(module, None)
    spec = importlib.util.spec_from_file_location('original48_whole_'+label, W/'make_video.py')
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    assert m.PRON_WORDS['Yuan'] == 'juːˈɑːn'
    assert m._OLDF and digest(m._OLDF) == OLD_REGISTRY_SHA
    assert m._CTX_PATH and digest(m._CTX_PATH) == CTX_SHA
    loaded_dict = next(Path(p) for p in (m._PRON_PATH,'读音改正.json','/home/user/postgraduate-vocabulary/视频/工具/发音词典/读音改正.json') if Path(p).is_file())
    assert digest(loaded_dict) == DICT_SHA
    m._REPO_CACHE = str(M/'forbid-public-private-cache-export')
    assert not Path(m._REPO_CACHE).exists()
    np, SR = m.np, m.SR
    current = json.loads(source.read_text())
    own_sentences=[' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in row['chunks'])for row in current['sentences']]
    assert all(m.SENT_NO.get(sent)=='48'for sent in own_sentences)
    result = {'source_sha256': expected_source, 'sample_rate': SR,
              'actual_own_17_sentence_SENT_NO':[m.SENT_NO.get(sent)for sent in own_sentences],
              'actual_own_S15_plain_English_sha256':hashlib.sha256(own_sentences[14].encode()).hexdigest(),
              'AF_sha256': digest(M/'tts/AF.txt'), 'AF_expression': m.AF,
              'original_speed': m.SPEED, 'observed_sentences': {}, 'cached_model_calls': 0,
              'original_old_cache_registry_sha256': digest(m._OLDF) if m._OLDF else None,
              'original_g26_generated_but_not_promoted_as_formal_acceptance': True}
    report['phases'][label] = result
    waves = {}
    raw_mothers = {}
    restoration_checks = {}
    active_gain_sid = None
    import ast
    dossier_path=T/'疑点清单.py'
    assert digest(dossier_path)=='c55db5722dd2792d51d12efc3ea8225edb1bcec236b69c684ee220f79cf6ecea'
    original_to_w=[n for n in ast.parse(dossier_path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='to_w']
    assert len(original_to_w)==1
    mapper_env={'SR':SR};mapper_ast=ast.Module(body=original_to_w,type_ignores=[]);ast.fix_missing_locations(mapper_ast)
    exec(compile(mapper_ast,str(dossier_path),'exec'),mapper_env);to_w=mapper_env['to_w']

    # Reject absent portable keys before the original wrapper can migrate an old
    # path key. Original _pron and original _条目核对 still decide the exact entry.
    for method, obj, model_name in (('create', m.k, 'kokoro-v1.0.onnx'),
                                    ('create_timed', m.KT, 'kokoro-v1.0-timed.onnx')):
        original_call = getattr(obj, method)

        def guarded(text, voice, speed=1.0, lang='en-us', _fn=original_call,
                    _method=method, _model=model_name, **kw):
            assert os.environ.get('STRICT_CACHE')=='1' and lang=='en-us' and np.array_equal(voice,m.V)  # Original ending has authorized0.78 speed; exact cache key pins speed.
            captured = []

            def capture(actual_text, voice, speed=1.0, lang='en-us', **actual_kw):
                mid = m._portable_mid(str(M/'tts'/_model))
                voice_id = hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                key = hashlib.sha1(repr((_method, mid, actual_text, voice_id,
                                        float(speed), lang, sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
                path = CACHE/key
                assert path.is_file()and key in expected_cache, 'STRICT_CACHED_EXPECTED_PORTABLE_KEY_MISSING '+key
                assert digest(path)==expected_cache[key]['sha256']
                assert hashlib.sha256(actual_text.encode()).hexdigest()==expected_cache[key]['actual_model_input_sha256']
                if expected_cache[key].get('single_thread_marker_sha256'):
                    assert digest(CACHE/(key+'.单线程'))==expected_cache[key]['single_thread_marker_sha256']
                m._条目核对(str(path))
                item = {'name': key, 'sha256': digest(path), 'method': _method,
                        'actual_model_input_sha256': hashlib.sha256(actual_text.encode()).hexdigest()}
                marker = CACHE/(key+'.单线程')
                if marker.exists():
                    item['single_thread_marker_sha256'] = digest(marker)
                    item['single_thread_marker_value'] = marker.read_text().strip()
                captured.append(item)

            m._pron(capture)(text, voice=voice, speed=speed, lang=lang, **kw)
            assert len(captured) == 1
            used[captured[0]['name']] = captured[0]
            result['cached_model_calls'] += 1
            value=_fn(text, voice=voice, speed=speed, lang=lang, **kw)
            if _method=='create':
                for sid in local_rows:
                    if text==m.spoken(own_sentences[int(sid[1:])-1]):raw_mothers[sid]=np.asarray(value[0],np.float32).copy()
            return value

        setattr(obj, method, guarded)

    gain_original, title_original, sf_original = m.句增益, m.title_audio, m.sf.write
    level_original=m._auto_level

    def array_sha(array):
        return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()

    def observe_title(title):
        value = title_original(title)
        waves['title'] = value
        assert array_sha(value)==reference['title_pre_master_PCM_sha256'], 'Protected title PCM changed'
        return value

    def selected_level(clips,tmap,gaps,no='',rounds=2):
        if active_gain_sid!='S9':
            assert os.environ.get('STRICT_CACHE')=='1'
            return level_original(clips,tmap,gaps,no,rounds)
        row=local_rows['S9'];concatenated=np.concatenate(clips)
        assert str(no)=='48'and rounds==2 and len(concatenated)==row['candidate_samples']==214200
        assert array_sha(concatenated)==row['candidate_pre_level_output_sha256_NOT_final_mastered']=='eeef7ffdbd92214262d32425b0ff4eb4aff7e0f792575d047a468855c03a38ce'
        assert [list(x)for x in m.LAST['cuts']]==row['candidate_actual_original_pipeline']['cuts']
        assert [list(x)for x in tmap]==row['candidate_tmap']
        signature=repr((str(no),list(gaps),[(round(t[2],4),round(t[3],4))for t in tmap])+(('K134等效',)if m._短起(no)else()))
        name='调平_'+hashlib.sha1(b''.join(np.ascontiguousarray(c,np.float32).tobytes()for c in clips)+signature.encode()).hexdigest()+'.json'
        path=CACHE/name;exists=path.is_file()
        info={'name':name,'actual_prelevel_SHA256':array_sha(concatenated),'samples':len(concatenated),
              'actual_signature':signature,'actual_raw_cuts':[list(x)for x in m.LAST['cuts']],
              'cache_existed_before_original_function':exists,'original_math_derived_only_if_missing':not exists}
        result['actual_new_S9_G51']=info
        if exists:
            out=level_original(clips,tmap,gaps,no,rounds)
        else:
            assert not allowed_new_S9_cache and os.environ.get('STRICT_CACHE')=='1'
            try:
                # This single original ffmpeg math call may write only its new
                # exact cache key. Every model-call guard still requires STRICT1.
                os.environ.pop('STRICT_CACHE')
                out=level_original(clips,tmap,gaps,no,rounds)
            finally:os.environ['STRICT_CACHE']='1'
            assert path.is_file();allowed_new_S9_cache[name]=digest(path)
        info['actual_original_gains']={str(k):v for k,v in out.items()};info['sha256']=digest(path)
        assert out=={}and json.loads(path.read_text())=={},'New S9 originalmath changed gain; stop for root review.'
        return out

    def observe_gain(data, no, si, sent, pieces, gaps, clips, tmap, audio):
        nonlocal active_gain_sid
        sid='S'+str(si+1);active_gain_sid=sid
        if sid in local_rows:
            row=local_rows[sid]
            assert array_sha(audio)==row['candidate_pre_level_output_sha256_NOT_final_mastered']and len(audio)==row['candidate_samples']
            assert [list(x)for x in m.LAST['cuts']]==row['candidate_actual_original_pipeline']['cuts']
            assert [list(x)for x in tmap]==row['candidate_tmap']
        try:value=gain_original(data,no,si,sent,pieces,gaps,clips,tmap,audio)
        finally:active_gain_sid=None
        clips_after,pcm,auto,manual=value;waves[sid]=pcm
        observed={'plain_English_sha256':hashlib.sha256(sent.encode()).hexdigest(),
                  'pre_master_PCM_sha256':array_sha(pcm),'PCM_dtype':str(pcm.dtype),'samples':len(pcm),'duration_s':len(pcm)/SR,
                  'automatic_gain_dB':{str(k):v for k,v in auto.items()},'manual_gain_dB':manual,
                  'actual_raw_w_fingerprint':m.SENT_FP.get(sent),'actual_raw_cuts':[list(x)for x in m.LAST['cuts']],
                  'piece_clips_sha256':[array_sha(x)for x in clips_after]}
        result['observed_sentences'][sid]=observed
        if sid in local_rows:
            row=local_rows[sid]
            assert auto=={}and manual is None and array_sha(pcm)==row['candidate_pre_level_output_sha256_NOT_final_mastered']
            assert observed['actual_raw_w_fingerprint']==row['raw_w_fingerprint']
            assert sid in raw_mothers
            raw=raw_mothers[sid];w0=m.clean_tail(raw);w=m._keep_tail(raw,w0,m._head_offset(raw,w0))
            assert hashlib.md5(np.ascontiguousarray(w).tobytes()).hexdigest()[:12]==row['raw_w_fingerprint']
            it={'segs':[(int(a),int(b),float(t),[(int(x),int(y))for x,y in rm])for a,b,t,rm in m.LAST['segs']]}
            a,b=row['preserved_raw_w_sample_range'];indices=[];source_indices=[]
            for j in range(len(pcm)):
                windex=to_w(it,j/SR)
                if windex is not None and a<=windex<b:indices.append(j);source_indices.append(windex)
            indices=np.asarray(indices,np.int64);source_indices=np.asarray(source_indices,np.int64)
            assert np.array_equal(source_indices,np.arange(a,b,dtype=np.int64)), 'Final mapper did not retain the complete selected range '+sid
            actual_values=pcm[indices];original_values=w[a:b]
            check={'sentence':sid,'raw_w_fingerprint':row['raw_w_fingerprint'],'raw_w_sample_range':[a,b],
                   'selected_raw_samples':b-a,'actual_final_mapped_samples':len(indices),
                   'actual_final_output_index_first_last':[int(indices[0]),int(indices[-1])],
                   'actual_final_output_indices_sha256':array_sha(indices),
                   'raw_original_selected_float_SHA256':array_sha(original_values),
                   'actual_final_pre_master_selected_float_SHA256':array_sha(actual_values),
                   'final_pre_master_values_equal_original_raw':bool(np.array_equal(actual_values,original_values)),
                   'final_pre_master_mismatched_samples':int(np.count_nonzero(actual_values!=original_values)),
                   'original_non_gain_normalization_must_be_measured_at_actual_build_write':True}
            result.setdefault('four_final_restored_sample_values_independent_vs_raw',{})[sid]=check
            assert check['final_pre_master_values_equal_original_raw'], 'Final restored sample values changed '+sid
            restoration_checks[sid]=(indices,original_values)
        else:
            oldrow=reference['observed_sentences'][sid]
            assert all(observed[k]==oldrow[k]for k in ('plain_English_sha256','pre_master_PCM_sha256','PCM_dtype','samples','automatic_gain_dB','manual_gain_dB','actual_raw_w_fingerprint','actual_raw_cuts','piece_clips_sha256')), 'Protected sentence physical identity changed '+sid
        return value

    def observe_write(path, actual_mastered, rate, *a, **kw):
        if Path(path) == Path('work_48/a.wav'):
            frame = inspect.currentframe().f_back
            assert frame.f_code is m.build.__code__ and rate == SR
            raw_parts = frame.f_locals['audio']
            pre = np.concatenate(raw_parts)
            peak = float(np.max(np.abs(pre)))
            actual_formula = pre/np.abs(pre).max()*.89
            assert np.array_equal(actual_mastered, actual_formula), 'Original maker normalization differs.'
            assert len(waves) == 18 and set(waves) == {'title'}|{'S'+str(i) for i in range(1,18)}
            cursor, positions = 0, {}
            for part in raw_parts:
                for sid, pcm in waves.items():
                    if part is pcm:
                        assert sid not in positions
                        positions[sid] = (cursor, cursor+len(pcm))
                cursor += len(part)
            assert len(positions) == 18 and cursor == len(pre)
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
            assert peak==reference['actual_original_mastering']['pre_master_absolute_peak'], 'Global peak changed unexpectedly; no assumed master identity.'
            comparisons=[]
            for sid in protected:
                lo,hi=positions[sid];expected=reference['actual_sample_clock'][sid]
                pre_expected=reference['title_pre_master_PCM_sha256']if sid=='title'else reference['observed_sentences'][sid]['pre_master_PCM_sha256']
                same_pre=array_sha(waves[sid])==pre_expected
                same_post=array_sha(actual_mastered[lo:hi])==expected['observed_post_master_float_PCM_sha256']
                comparisons.append({'segment':sid,'pre_master_exact_to_actual295':same_pre,'post_master_float_exact_to_actual295':same_post,
                                    'samples':hi-lo,'actual_clock_start_s':lo/SR,'reference_clock_start_s':expected['start_s']})
                assert same_pre and same_post,'Protected physical float identity failed '+sid
            report['protected_title_and13_sentence_physical_identity']=comparisons
            report['all_protected_title_and13_pre_and_post_master_exact295']=all(x['pre_master_exact_to_actual295']and x['post_master_float_exact_to_actual295']for x in comparisons)
            assert set(restoration_checks)==set(local_rows)
            for sid,(indices,raw_values)in restoration_checks.items():
                lo,hi=positions[sid];actual_values=actual_mastered[lo+indices]
                original_expected=raw_values/np.float32(peak)*.89
                check=result['four_final_restored_sample_values_independent_vs_raw'][sid]
                check.update({'actual_mastered_float_selected_SHA256':array_sha(actual_values),
                              'raw_original_under_actual_normalization_selected_SHA256':array_sha(original_expected),
                              'actual_original_master_peak':peak,'original_formula':'raw_original / np.float32(actualbuildpeak) * .89',
                              'final_mastered_selected_values_equal_raw_under_original_normalization':bool(np.array_equal(actual_values,original_expected)),
                              'final_mastered_mismatched_samples':int(np.count_nonzero(actual_values!=original_expected)),
                              'global_output_index_first_last':[int(lo+indices[0]),int(lo+indices[-1])]})
                assert check['final_mastered_selected_values_equal_raw_under_original_normalization'],'Normalized restored sample value mismatch '+sid
        return sf_original(path, actual_mastered, rate, *a, **kw)

    m.title_audio, m.句增益, m.sf.write, m._auto_level = observe_title, observe_gain, observe_write, selected_level
    output_audio = scratch/(label+'-actual-original-canonical.m4a')
    try:
        m.build(str(source), str(output_audio))
    finally:
        m.sf.write = sf_original
        m._auto_level=level_original
    assert digest(source) == expected_source
    assert work.is_dir() and (work/'a.wav').is_file()
    assert 'actual_original_mastering' in result
    value, sr = m.sf.read(work/'a.wav')
    result['actual_complete_WAV'] = {
        'file_sha256': digest(work/'a.wav'), 'file_bytes': (work/'a.wav').stat().st_size,
        'sample_rate': sr, 'samples': len(value), 'duration_s': len(value)/sr,
        'subtype': m.sf.info(work/'a.wav').subtype,
    }
    assert sr == SR and len(value) == result['actual_original_mastering']['pre_master_samples']
    assert m.sf.info(work/'a.wav').subtype=='PCM_16'
    for sid,(indices,raw_values)in restoration_checks.items():
        clock=result['actual_sample_clock'][sid]
        original_normalized=raw_values/np.float32(result['actual_original_mastering']['pre_master_absolute_peak'])*.89
        expected_wav=scratch/(label+'-'+sid+'-private-original-sf-PCM16-quantization.wav')
        # Use exactly the original native sf.write/read conversion, rather than
        # a hand-coded float64 multiplier or an approximate rounding rule.
        sf_original(expected_wav,original_normalized,SR)
        expected_quantized,expected_rate=m.sf.read(expected_wav)
        assert expected_rate==SR and m.sf.info(expected_wav).subtype==m.sf.info(work/'a.wav').subtype=='PCM_16'
        actual_quantized=value[clock['start_sample']+indices]
        check=result['four_final_restored_sample_values_independent_vs_raw'][sid]
        check.update({'original_normalized_raw_dtype':str(original_normalized.dtype),
                      'actual_full_WAV_decoded_dtype':str(value.dtype),'expected_original_sf_PCM16_decoded_dtype':str(expected_quantized.dtype),
                      'expected_original_sf_PCM16_selected_samples_SHA256':array_sha(expected_quantized),
                      'actual_full_WAV_PCM16_selected_samples_SHA256':array_sha(actual_quantized),
                      'original_sf_write_read_PCM16_quantization_equal_per_sample':bool(np.array_equal(expected_quantized,actual_quantized)),
                      'PCM16_quantized_mismatched_samples':int(np.count_nonzero(expected_quantized!=actual_quantized)),
                      'no_float64_multiplier_or_handwritten_quantization_rule_used':True})
        assert check['original_sf_write_read_PCM16_quantization_equal_per_sample'],'Actual PCM16 restored values mismatch original sf quantization '+sid
    result['actual_complete_AAC'] = audio_metadata(output_audio)
    result['actual_full_WAV_original_PV_fingerprint_md5_12']=hashlib.md5((work/'a.wav').read_bytes()).hexdigest()[:12]
    result['actual_voice_fingerprint_table'] = json.loads((work/'句子声音指纹.json').read_text())
    result['actual_original_piece_time_table'] = json.loads((work/'分段.json').read_text())
    assert not result['actual_voice_fingerprint_table']['作废'], 'A45 invalidation leaked into formal0193/baseline.'
    result['no_picture_rendered'] = not any(work.glob('*.png'))
    assert result['no_picture_rendered']
    target = scratch/(label+'-private-original-work48')
    work.rename(target)
    report['phases'][label] = result
    sys.modules.pop(spec.name, None)
    del m
    gc.collect()


try:
    if not envdir.exists():
        envdir.symlink_to(T/'环境',target_is_directory=True)
        environment_link_created=True
    assert digest(envdir/'模型校验码.json')==REGISTRY_SHA
    if scripts_was_symlink:
        other_json_bytes={p.name:p.read_bytes()for p in scripts.glob('*.json')if p.name!='48.json'}
        scripts.rename(prior_scripts_link)
        scripts.mkdir()
        for name,content in other_json_bytes.items():(scripts/name).write_bytes(content)
        source_isolated=True
    else:
        if source.exists()or source.is_symlink():source.rename(prior_source_entry)
        source_isolated=True
    if work.exists()or work.is_symlink():work.rename(prior_work)
    work_isolated=True
    run_phase('selected_four_protection',new_source_bytes,NEW_SHA)
    actual_new=report['phases']['selected_four_protection']
    assert len(actual_new['observed_sentences'])==17
    assert actual_new['observed_sentences']['S15']['automatic_gain_dB']=={'1':-6.0}
    assert actual_new['observed_sentences']['S15']['manual_gain_dB']=={'1':1.0}
    assert actual_new['observed_sentences']['S15']['actual_raw_w_fingerprint']=='4e8bece5aaea'
    assert actual_new['observed_sentences']['S15']['actual_raw_cuts']==[[25440,33120,.38],[165240,175800,.38],[277200,286680,.38]]
    for name,expected in required.items():
        if name.endswith('.pkl'):
            assert used[name]['sha256']==expected and used[name]['actual_model_input_sha256']==identity['post_pron_input_sha256']
    report['actual_global_scale_ratio_new_over_prior295']=actual_new['actual_original_mastering']['logical_normalization_scale']/reference['actual_original_mastering']['logical_normalization_scale']
    report['actual_all_sentence_clock_deltas_s']={sid:actual_new['actual_sample_clock'][sid]['start_s']-reference['actual_sample_clock'][sid]['start_s']for sid in reference['actual_sample_clock']}
    report['all_four_final_restored_values_exact_raw_and_normalized']=all(x['final_pre_master_values_equal_original_raw']and x['final_mastered_selected_values_equal_raw_under_original_normalization']and x['original_sf_write_read_PCM16_quantization_equal_per_sample']for x in actual_new['four_final_restored_sample_values_independent_vs_raw'].values())
    assert report['all_four_final_restored_values_exact_raw_and_normalized']
    report['S9_only_missing_original_math_result_empty']=actual_new['actual_new_S9_G51']['actual_original_gains']=={}
    report['no_baseline_rebuild_or_other_new_math']=True
    report['diagnostic_completed'] = True
except BaseException as error:
    report['diagnostic_completed'] = False
    report['errors'].append({'type': type(error).__name__, 'detail': str(error)})
    traceback.print_exc()
finally:
    if work_isolated and (work.exists()or work.is_symlink()):
        work.rename(scratch/'incomplete-private-work48')
    if prior_work.exists()or prior_work.is_symlink():prior_work.rename(work)
    if scripts_was_symlink:
        if prior_scripts_link.exists()or prior_scripts_link.is_symlink():
            if scripts.exists():
                assert not scripts.is_symlink()
                for p in scripts.iterdir():
                    assert p.is_file()and p.suffix=='.json'
                    p.unlink()
                scripts.rmdir()
            prior_scripts_link.rename(scripts)
    elif source_isolated:
        source.unlink(missing_ok=True)
        if prior_source_entry.exists()or prior_source_entry.is_symlink():prior_source_entry.rename(source)
    if environment_link_created:envdir.unlink()
    after_cache = inventory()
    report['private_cache_inventory_count'] = len(before_cache)
    report['private_cache_inventory_sha256'] = json_digest(before_cache)
    report['all_existing_private_cache_files_exact_before_after'] = all(after_cache.get(k)==v for k,v in before_cache.items())
    actual_added={k:v for k,v in after_cache.items()if k not in before_cache}
    report['only_new_private_cache_files']=actual_added
    report['only_allowed_new_S9_G51_cache_written']=actual_added==allowed_new_S9_cache
    if before_cache != after_cache:
        report['private_cache_differences'] = [name for name in sorted(set(before_cache)|set(after_cache))
                                               if before_cache.get(name) != after_cache.get(name)]
    report['actual_used_source48_private_cache_entries_scalar_only'] = list(used.values())
    report['normal_W_scripts48_exact_restored'] = source.read_bytes() == prior_source if prior_source is not None else not source.exists()
    report['original_script_inode_or_link_restored_not_rewritten'] = True
    report['normal_W_preexisting_work48_PCM_exact_restored'] = digest(work/'a.wav') == prior_wav if prior_wav is not None else True
    report['all_other_W_source_scripts_exact'] = all(Path(p).is_file() and digest(p) == h for p,h in other_scripts_before.items())
    report['original_maker_file_exact_after'] = digest(W/'make_video.py') == MAKER_SHA
    report['all_original_seven_runtime_core_files_exact_after'] = {
        name: digest(T/name) for name in FIVECORE_FILES} == FIVECORE_FILES
    report['original_request_and_baseline_files_exact_after'] = digest(request) == NEW_SHA and digest(args.baseline_source) == OLD_SHA
    report['exact_scope_proved'] = bool(report.get('diagnostic_completed') and
        report.get('all_protected_title_and13_pre_and_post_master_exact295') and report.get('all_four_final_restored_values_exact_raw_and_normalized') and report.get('S9_only_missing_original_math_result_empty') and report['only_allowed_new_S9_G51_cache_written'] and
        report['all_existing_private_cache_files_exact_before_after'] and
        report['normal_W_scripts48_exact_restored'] and report['normal_W_preexisting_work48_PCM_exact_restored'] and
        report['all_other_W_source_scripts_exact'] and report['original_maker_file_exact_after'] and
        report['all_original_seven_runtime_core_files_exact_after'] and
        report['original_request_and_baseline_files_exact_after'])
    report['formal_all_original_gates_still_required'] = True
    report['exact_reference_and_selection_files_unchanged']=digest(args.whole_reference)=='295fd087864e9ffbd2ad63edddb2da5d10af818b960c8a030e1ccdbd5537c591'and digest(args.physical_selection)=='11df709068690c56d4ee5be2cd2b46e19ddaf105e11ab8f7e5330ff392ec3f66'
    report['exact_scope_proved']=report['exact_scope_proved']and report['exact_reference_and_selection_files_unchanged']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=lambda x:x.item())+'\n')
    print(json.dumps({'diagnostic_completed':report.get('diagnostic_completed'),
        'exact_scope_proved':report['exact_scope_proved'], 'output_sha256':digest(args.output),
        'errors':report['errors'], 'new_inference_authorized_or_performed':False,
        'raw_PCM_models_private_cache_GT_exported':False}, ensure_ascii=False))
sys.exit(0 if report.get('exact_scope_proved') else 1)
