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
for key in ('tools', 'video-root', 'request', 'baseline-source', 'cache-identity', 'gain-decision', 'whole-tuple-measurement', 'output'):
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
scratch = M/'_source48_whole_cached_diagnostic'
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
    'kind': 'source48_correct_dictionary_context_strict_cached_whole_AudioOnly_actual_scope_diagnostic',
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

    # Reject absent portable keys before the original wrapper can migrate an old
    # path key. Original _pron and original _条目核对 still decide the exact entry.
    for method, obj, model_name in (('create', m.k, 'kokoro-v1.0.onnx'),
                                    ('create_timed', m.KT, 'kokoro-v1.0-timed.onnx')):
        original_call = getattr(obj, method)

        def guarded(text, voice, speed=1.0, lang='en-us', _fn=original_call,
                    _method=method, _model=model_name, **kw):
            captured = []

            def capture(actual_text, voice, speed=1.0, lang='en-us', **actual_kw):
                mid = m._portable_mid(str(M/'tts'/_model))
                voice_id = hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                key = hashlib.sha1(repr((_method, mid, actual_text, voice_id,
                                        float(speed), lang, sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
                path = CACHE/key
                assert path.is_file(), 'STRICT_CACHED_PORTABLE_KEY_MISSING '+key
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
            return _fn(text, voice=voice, speed=speed, lang=lang, **kw)

        setattr(obj, method, guarded)

    gain_original, title_original, sf_original = m.句增益, m.title_audio, m.sf.write

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
        return sf_original(path, actual_mastered, rate, *a, **kw)

    m.title_audio, m.句增益, m.sf.write = observe_title, observe_gain, observe_write
    output_audio = scratch/(label+'-actual-original-canonical.m4a')
    try:
        m.build(str(source), str(output_audio))
    finally:
        m.sf.write = sf_original
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
    result['actual_complete_AAC'] = audio_metadata(output_audio)
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
    run_phase('baseline_current4f', old_source_bytes, OLD_SHA)
    run_phase('selected_new0193', new_source_bytes, NEW_SHA)
    import numpy as np
    compared = []
    for sid in ['title']+['S'+str(i) for i in range(1,18) if i != 15]:
        a, b = phase_arrays['baseline_current4f'][sid], phase_arrays['selected_new0193'][sid]
        exact = a.dtype == b.dtype and a.shape == b.shape and bool(np.array_equal(a,b))
        compared.append({'segment': sid, 'actual_pre_master_samples_exact': exact,
                         'old_samples': len(a), 'new_samples': len(b),
                         'old_dtype': str(a.dtype), 'new_dtype': str(b.dtype),
                         'old_actual_PCM_sha256': hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest(),
                         'new_actual_PCM_sha256': hashlib.sha256(np.ascontiguousarray(b).tobytes()).hexdigest()})
    report['non_target_title_and16_sentence_pre_master_identity'] = compared
    report['all_non_target16_sentence_pre_master_PCM_exact'] = all(x['actual_pre_master_samples_exact'] for x in compared)
    report['target_S15_changed_as_explicitly_authorized'] = not np.array_equal(
        phase_arrays['baseline_current4f']['S15'], phase_arrays['selected_new0193']['S15'])
    assert report['phases']['selected_new0193']['observed_sentences']['S15']['automatic_gain_dB'] == {'1': -6.0}
    assert report['phases']['selected_new0193']['observed_sentences']['S15']['manual_gain_dB'] == {'1': 1.0}
    assert report['phases']['selected_new0193']['observed_sentences']['S15']['actual_raw_w_fingerprint'] == '4e8bece5aaea'
    assert report['phases']['baseline_current4f']['observed_sentences']['S15']['actual_raw_w_fingerprint'] == old['区间声音指纹']['S15']
    assert report['phases']['selected_new0193']['observed_sentences']['S15']['actual_raw_cuts'] == [
        [25440,33120,0.38], [165240,175800,0.38], [277200,286680,0.38]]
    for name, expected in required.items():
        if name.endswith('.pkl'):
            assert used[name]['sha256'] == expected
            assert used[name]['actual_model_input_sha256'] == identity['post_pron_input_sha256']
    report['actual_global_scale_ratio_new_over_old'] = (
        report['phases']['selected_new0193']['actual_original_mastering']['logical_normalization_scale'] /
        report['phases']['baseline_current4f']['actual_original_mastering']['logical_normalization_scale'])
    report['actual_target_and_later_clock_deltas_s'] = {
        sid: report['phases']['selected_new0193']['actual_sample_clock'][sid]['start_s'] -
        report['phases']['baseline_current4f']['actual_sample_clock'][sid]['start_s']
        for sid in ['S15','S16','S17']}
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
    report['all_existing_private_cache_files_exact_before_after'] = before_cache == after_cache
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
        report.get('all_non_target16_sentence_pre_master_PCM_exact') and
        report['all_existing_private_cache_files_exact_before_after'] and
        report['normal_W_scripts48_exact_restored'] and report['normal_W_preexisting_work48_PCM_exact_restored'] and
        report['all_other_W_source_scripts_exact'] and report['original_maker_file_exact_after'] and
        report['all_original_seven_runtime_core_files_exact_after'] and
        report['original_request_and_baseline_files_exact_after'])
    report['formal_all_original_gates_still_required'] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=lambda x:x.item())+'\n')
    print(json.dumps({'diagnostic_completed':report.get('diagnostic_completed'),
        'exact_scope_proved':report['exact_scope_proved'], 'output_sha256':digest(args.output),
        'errors':report['errors'], 'new_inference_authorized_or_performed':False,
        'raw_PCM_models_private_cache_GT_exported':False}, ensure_ascii=False))
sys.exit(0 if report.get('exact_scope_proved') else 1)
