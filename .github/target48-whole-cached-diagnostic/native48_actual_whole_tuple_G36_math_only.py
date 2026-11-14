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
for key in ('tools', 'video-root', 'request', 'baseline-source', 'cache-identity', 'gain-decision', 'missing-witness', 'output', 'cache-path-output'):
    P.add_argument('--' + key, type=Path, required=True)
args = P.parse_args()
T, M = args.tools.resolve(), args.video_root.resolve()
W, CACHE = M / 'video', M / 'tts/cache_tts'
OLD_SHA = '4f146ce6a70bb0bf5d2c6e1f6b47bd6a2bcc2f311be7a948092d7bde1a08f449'
NEW_SHA = '0193cbd1859525690e12a470c517cce2f120a1054b204fcfa3c0c392c92abbd7'
MAKER_SHA = '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
IDENTITY_SHA = '866551b0635e6797cb0b3e032ae73e4ad783af602e39e07cde9b34ba1c4d16cf'
GAIN_DECISION_SHA = 'edbfc9c3441fd32b31908fdbb4e194f0dc2099aec274b1642e9e4005bf6d944c'
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
assert digest(args.cache_identity) == IDENTITY_SHA
assert digest(args.gain_decision) == GAIN_DECISION_SHA
gain_decision = json.loads(args.gain_decision.read_text())
assert gain_decision['request_source_SHA256_remains'] == NEW_SHA
assert gain_decision['selected_gain'] == {'source_id':'48','sentence':'S15','piece':'1','manual_dB':1.0,'original_actual_G36_dB':-6.0,'effective_combined_dB':-5.0}
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

# The native normal machine owns these files. Only the small source48 namespace
# and its original work directory are temporarily swapped, then restored exactly.
scratch = M/'_source48_original_whole_tuple_G36_only'
assert not scratch.exists(), 'Use a fresh isolated diagnostic machine/run.'
scratch.mkdir()
source = W/'scripts/48.json'
source.parent.mkdir(exist_ok=True)
prior_source = source.read_bytes() if source.exists() else None
scripts = source.parent
other_scripts_before = {str(p): digest(p) for p in scripts.glob('*.json') if p.name != '48.json'}
prior_source_entry = scratch/'preexisting-script48-untouched'
prior_scripts_link = scratch/'preexisting-scripts-symlink-untouched'
scripts_was_symlink = scripts.is_symlink()
if scripts_was_symlink:
    # The normal machine may link scripts directly into the immutable request.
    # Move the link itself and copy only tiny JSON metadata into a new local dir.
    other_json_bytes = {p.name: p.read_bytes() for p in scripts.glob('*.json') if p.name != '48.json'}
    scripts.rename(prior_scripts_link)
    scripts.mkdir()
    for name, content in other_json_bytes.items():
        (scripts/name).write_bytes(content)
elif source.exists() or source.is_symlink():
    # Rename preserves the original inode/link; never write through a request link.
    source.rename(prior_source_entry)
work = W/'work_48'
prior_work = scratch/'preexisting-work48-untouched'
prior_wav = digest(work/'a.wav') if (work/'a.wav').is_file() else None
if work.exists() or work.is_symlink():
    work.rename(prior_work)
before_cache = inventory()
environment_link_created = False
envdir = W/'环境'
if not envdir.exists():
    assert digest(T/'环境/模型校验码.json') == REGISTRY_SHA
    envdir.symlink_to(T/'环境', target_is_directory=True)
    environment_link_created = True
assert digest(envdir/'模型校验码.json') == REGISTRY_SHA
report = {
    'kind': 'source48_actual_whole_tuple_only_original_G36_math_and_zero_plus1_diagnostic',
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



EXPECTED = '调平_3089bf1e9ad992be5bc42ea6c586ae366b1b1a40.json'
SMALL = '调平_55b4f1b37a71b4de9c91b384a2cee79d0d89761c.json'
assert digest(args.missing_witness) == 'cb0669640e33791adade21bbd5fd49f7e8b0fc2c940a9335edcbe92ad48292b4'
witness = json.loads(args.missing_witness.read_text())
assert witness['source_request_sha256'] == NEW_SHA and witness['exact_private_cache_identity_sha256'] == IDENTITY_SHA
assert len(witness['phases']['baseline_current4f']['observed_sentences']) == 17
assert list(witness['phases']['selected_new0193']['observed_sentences']) == ['S'+str(i) for i in range(1,15)]
assert len(witness['errors']) == 1 and EXPECTED in witness['errors'][0]['detail']
assert not (CACHE/EXPECTED).exists(), 'This one pure-math derivation is authorized only after the actual missing-key witness.'
report['actual_missing_whole_G36_witness_sha256'] = digest(args.missing_witness)
report['derivation_is_only_original_auto_level_math_no_model_inference'] = True
report['old_small_G36_cache_copied_or_renamed'] = False
report['whole_diagnostic_and_formal_gates_still_pending'] = True
contexts = {}
private = {}

def context(label, content, expected_source):
    source.write_bytes(content)
    assert digest(source) == expected_source
    os.chdir(W)
    sys.path.insert(0,str(W))
    for name in ('render','title2','clean','出片指纹'):
        sys.modules.pop(name,None)
    spec = importlib.util.spec_from_file_location('actual48_G36_tuple_'+label,W/'make_video.py')
    m = importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    assert m.PRON_WORDS['Yuan']=='juːˈɑːn'
    assert digest(m._OLDF)==OLD_REGISTRY_SHA and digest(m._CTX_PATH)==CTX_SHA
    m._REPO_CACHE=str(M/'forbid-public-private-cache-export');assert not Path(m._REPO_CACHE).exists()
    np,SR=m.np,m.SR
    sent=identity['exact_new_plain_English']
    expected_mothers = {row['method']:row for row in identity['cache_entries']}
    for method,obj,model in [('create',m.k,'kokoro-v1.0.onnx'),('create_timed',m.KT,'kokoro-v1.0-timed.onnx')]:
        original=getattr(obj,method)
        def guard(text,voice,speed=1.0,lang='en-us',_fn=original,_method=method,_model=model,**kw):
            assert text==m.spoken(sent) and speed==m.SPEED and lang=='en-us' and np.array_equal(voice,m.V)
            captured=[]
            def capture(actual_text,voice,speed=1.0,lang='en-us',**actual_kw):
                mid=m._portable_mid(str(M/'tts'/_model)); vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                key=hashlib.sha1(repr((_method,mid,actual_text,vh,float(speed),lang,sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
                row=expected_mothers[_method]
                assert key==row['exact_cache_key'] and (CACHE/key).is_file(), 'No model inference or alternate key authorized: '+key
                assert digest(CACHE/key)==row['actual_pkl_sha256']
                assert digest(CACHE/(key+'.单线程'))==row['actual_marker_sha256']
                assert hashlib.sha256(actual_text.encode()).hexdigest()==identity['post_pron_input_sha256']
                m._条目核对(str(CACHE/key)); captured.append(key)
            m._pron(capture)(text,voice=voice,speed=speed,lang=lang,**kw)
            assert len(captured)==1
            used[captured[0]]={'name':captured[0],'sha256':digest(CACHE/captured[0]),'method':_method,'read_only_cached_call':True}
            return _fn(text,voice=voice,speed=speed,lang=lang,**kw)
        setattr(obj,method,guard)
    # Exactly the original build() comma parsing, with original listing rules.
    pieces=[];gaps=[];p0=0;lst=m.list_commas(sent)
    for match in m.re.finditer(r'[,;:](?=\s)',sent):
        pieces.append((p0,match.end()));p0=match.end()+1
        gaps.append(m.P_LIST if match.start() in lst else m.P_COMMA)
    pieces.append((p0,len(sent)))
    clips,tmap=m.sentence_audio(sent,pieces,gaps)
    signature=repr(('48',list(gaps),[(round(t[2],4),round(t[3],4))for t in tmap])+(('K134等效',)if m._短起('48')else()))
    key='调平_'+hashlib.sha1(b''.join(np.ascontiguousarray(c,np.float32).tobytes()for c in clips)+signature.encode()).hexdigest()+'.json'
    installed=json.loads(content)
    own_sentences=[' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in row['chunks'])for row in installed['sentences']]
    assert all(m.SENT_NO.get(own)=='48'for own in own_sentences)
    info={'installed_source_sha256':digest(source),'installed_source_own_17_sentence_SENT_NO':[m.SENT_NO.get(own)for own in own_sentences],
          'installed_source_own_S15_plain_English_sha256':hashlib.sha256(own_sentences[14].encode()).hexdigest(),'new_S15_actual_SENT_NO':m.SENT_NO.get(sent),
          'original_余音删法_for_new_S15':m.余音删法(sent),'no_argument':'48',
          'original_G36_key':key,'key_metadata_repr':signature,'pieces':[list(x)for x in pieces],
          'gaps':list(gaps),'tmap':[list(x)for x in tmap],
          'clip_samples':[len(x)for x in clips],
          'clip_sha256':[hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()for x in clips],
          'concatenated_prelevel_PCM_sha256':hashlib.sha256(np.concatenate(clips).tobytes()).hexdigest(),
          'actual_raw_w_fingerprint':m.SENT_FP[sent],
          'actual_raw_cuts':[list(x)for x in m.LAST['cuts']],
          'actual_fades':[list(x)for x in m.LAST['fades']]}
    assert info['actual_raw_w_fingerprint']=='4e8bece5aaea'
    contexts[label]=info;private[label]=(clips,tmap,gaps)
    if label=='small_import_with_old4f':
        assert key==SMALL, 'The exact former small setup must reproduce its actual G36 key.'
        assert m.SENT_NO.get(sent) is None and m.余音删法(sent) is False
        assert digest(CACHE/key)==required[SMALL]
        return
    assert key==EXPECTED, 'The real source-installed tuple must reproduce the actual whole missing key.'
    assert m.SENT_NO.get(sent)=='48' and m.余音删法(sent) is True
    # One function, one exact input tuple, one new cache file. No caller/model can
    # infer: guarded cache/model entrypoints above reject every absent/other key.
    # Only original _auto_level's pure ffmpeg mathematics sees STRICT unset.
    original_auto=m._auto_level
    assert original_auto.__code__.co_filename==str(W/'make_video.py')
    assert os.environ.pop('STRICT_CACHE')=='1'
    try:
        automatic=original_auto(clips,tmap,gaps,'48')
    finally:
        os.environ['STRICT_CACHE']='1'
    assert (CACHE/EXPECTED).is_file()
    assert {int(k):float(v)for k,v in json.loads((CACHE/EXPECTED).read_text()).items()}==automatic
    report['original_G36_pure_math_derivation_count']=1
    report['actual_original_G36_gains']={str(k):v for k,v in automatic.items()}
    report['derived_private_G36_file']={'name':EXPECTED,'sha256':digest(CACHE/EXPECTED)}
    base_data=copy.deepcopy(new);base_data.get('分段增益dB',{}).pop('S15',None)
    base,basewave,auto0,manual0=m.句增益(base_data,'48',14,sent,pieces,gaps,[x.copy()for x in clips],tmap,np.concatenate(clips))
    plus,pluswave,auto1,manual1=m.句增益(new,'48',14,sent,pieces,gaps,[x.copy()for x in clips],tmap,np.concatenate(clips))
    assert auto0==auto1==automatic and not manual0 and manual1=={'1':1.0}
    report['actual_piece_levels']=[]
    for i,(c0,c1,t0,t1)in enumerate(tmap):
        row={'piece':i+1,'text':sent[c0:c1],'span_s':[t0,t1]}
        for name,wave in [('baseline0',basewave),('plus1',pluswave)]:
            x=wave[round(t0*SR):round(t1*SR)].astype(float)
            row[name]={'RMS_dBFS':20*math.log10(float(np.sqrt(np.mean(x*x)))+1e-20),
                       'peak_dBFS':20*math.log10(float(np.max(np.abs(x)))+1e-20)}
        report['actual_piece_levels'].append(row)
    diff=np.flatnonzero(basewave!=pluswave);end=round(tmap[0][3]*SR)
    report['actual_changed_samples_between_candidates']={'count':len(diff),'first_sample':int(diff[0])if len(diff)else None,
          'last_sample':int(diff[-1])if len(diff)else None,'first_piece_end_sample':end,
          'all_later_samples_exact':bool(np.array_equal(basewave[end:],pluswave[end:]))}
    ls=importlib.util.spec_from_file_location('actual_whole48_original_LU',T/'响度一致性核对.py')
    L=importlib.util.module_from_spec(ls);ls.loader.exec_module(L)
    common=max(float(np.max(np.abs(basewave))),float(np.max(np.abs(pluswave))))
    report['actual_original_LU_comparison']={'program_sha256':digest(T/'响度一致性核对.py'),
        'same_reference_peak':common,'source48_short_equivalent_mode':L.短起('48'),
        'original_adjacent_limit_LU':L.IN_ADJ,'candidates':{}}
    for label,wave in [('baseline0',basewave),('plus1',pluswave)]:
        wav=scratch/(label+'-meter-private.wav')
        padded=np.concatenate([np.zeros(round(.5*SR),np.float32),wave,np.zeros(round(.5*SR),np.float32)])
        m.sf.write(wav,padded/common*.89,SR);TM=L.momentary(str(wav));levels=[]
        for i,(_,_,t0,t1)in enumerate(tmap):
            value=L.等效(L.段响度(TM,.5+t0,.5+t1),t0,t1,L.短起('48'));_,peak=L.段量(TM,.5+t0,.5+t1)
            levels.append({'piece':i+1,'gated_LUFS':float(value)if value is not None else None,'maximum400ms_LUFS':float(peak)})
        ds=[levels[i]['gated_LUFS']-levels[i-1]['gated_LUFS']if levels[i]['gated_LUFS']is not None and levels[i-1]['gated_LUFS']is not None else None for i in range(1,len(levels))]
        report['actual_original_LU_comparison']['candidates'][label]={'pieces':levels,'adjacent_LU_differences':ds,
            'all_adjacent_within_original_limit':all(v is not None and abs(v)<=L.IN_ADJ for v in ds)}
    report['actual_whole_tuple_auto_matches_root_prior_selected_minus6']=automatic=={1:-6.0}
    report['manual_plus1_is_measured_candidate_root_reconfirmation_pending']=True
    args.cache_path_output.parent.mkdir(parents=True,exist_ok=True)
    args.cache_path_output.write_text(str((CACHE/EXPECTED).resolve())+'\n')

try:
    context('small_import_with_old4f',old_source_bytes,OLD_SHA)
    context('actual_whole_import_with_selected0193',new_source_bytes,NEW_SHA)
    import numpy as np
    a,b=contexts['small_import_with_old4f'],contexts['actual_whole_import_with_selected0193']
    report['actual_contexts']=contexts
    report['actual_tuple_differences']={key:{'former_small':a[key],'actual_whole':b[key]}for key in a if a[key]!=b[key]}
    report['per_clip_array_equal']=[bool(x.shape==y.shape and np.array_equal(x,y))for x,y in zip(private['small_import_with_old4f'][0],private['actual_whole_import_with_selected0193'][0])]
    report['diagnostic_completed']=True
except BaseException as error:
    report['diagnostic_completed']=False;report['errors'].append({'type':type(error).__name__,'detail':str(error)})
    traceback.print_exc()
finally:
    if work.exists() or work.is_symlink():work.rename(scratch/'incomplete-private-work48')
    if prior_work.exists() or prior_work.is_symlink():prior_work.rename(work)
    source.unlink(missing_ok=True)
    if scripts_was_symlink:
        for p in scripts.iterdir():
            assert p.is_file()and p.suffix=='.json';p.unlink()
        scripts.rmdir();prior_scripts_link.rename(scripts)
    elif prior_source_entry.exists()or prior_source_entry.is_symlink():prior_source_entry.rename(source)
    if environment_link_created:envdir.unlink()
    after=inventory();changed=[name for name in before_cache if after.get(name)!=before_cache[name]]
    added=sorted(set(after)-set(before_cache))
    report['all_existing_private_cache_files_exact_before_after']=not changed
    report['actual_added_private_cache_files']={name:after[name]for name in added}
    report['only_actual_whole_G36_cache_added']=added==[EXPECTED]and not changed
    report['actual_new_model_inference_count']=0
    report['actual_used_cached_S15_mothers_scalar_only']=list(used.values())
    report['normal_W_scripts48_exact_restored']=source.read_bytes()==prior_source if prior_source is not None else not source.exists()
    report['normal_W_preexisting_work48_PCM_exact_restored']=digest(work/'a.wav')==prior_wav if prior_wav is not None else True
    report['all_other_W_source_scripts_exact']=all(Path(p).is_file()and digest(p)==h for p,h in other_scripts_before.items())
    report['original_maker_file_exact_after']=digest(W/'make_video.py')==MAKER_SHA
    report['all_original_seven_runtime_core_files_exact_after']={name:digest(T/name)for name in FIVECORE_FILES}==FIVECORE_FILES
    report['original_request_and_baseline_files_exact_after']=digest(request)==NEW_SHA and digest(args.baseline_source)==OLD_SHA
    report['exact_scope_proved']=bool(report.get('diagnostic_completed')and report['only_actual_whole_G36_cache_added']and
      report['normal_W_scripts48_exact_restored']and report['normal_W_preexisting_work48_PCM_exact_restored']and
      report['all_other_W_source_scripts_exact']and report['original_maker_file_exact_after']and report['all_original_seven_runtime_core_files_exact_after']and
      report['original_request_and_baseline_files_exact_after'])
    report['formal_all_original_gates_still_required']=True
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    print(json.dumps({'diagnostic_completed':report.get('diagnostic_completed'),'exact_scope_proved':report['exact_scope_proved'],
       'output_sha256':digest(args.output),'errors':report['errors'],'new_model_inference_count':0},ensure_ascii=False))
sys.exit(0 if report['exact_scope_proved']else 1)
