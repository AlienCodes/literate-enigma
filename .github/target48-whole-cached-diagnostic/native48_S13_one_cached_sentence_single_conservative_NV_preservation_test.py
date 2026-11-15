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
for key in ('tools', 'video-root', 'request', 'baseline-source', 'cache-identity', 'gain-decision', 'whole-tuple-measurement', 'whole-report', 'failed-proof', 'original-report2', 'actual-nine-report', 'preservation-proposal', 'local-input-decision', 'output'):
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
assert digest(args.local_input_decision)=='879bd090a5a8fead18384bc9d367f6a7d28b4b5557d53234f7fb65f823d75cc5'
local_decision=json.loads(args.local_input_decision.read_text())
assert local_decision['source_unchanged']==NEW_SHA and local_decision['do_not_modify_running_three_case_native_43659597655']is True
assert local_decision['scope']=='Only cached S13 baseline hard identity to actual295/935f and one in-memory candidate through original NV guard and mapper; no whole, G36, TTS, encoded media or production source/CF writes.'
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
scratch = M/'_source48_S13_single_conservative_preservation_test'
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
    'kind': 'source48_S13_one_cached_sentence_single_conservative_NV_preservation_candidate_diagnostic',
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
assert digest(args.original_report2)=='4e12f649e521a860ed416c4d098be57a1c177455411ef22b240fb3c563aa2153'
whole=json.loads(args.whole_report.read_text());actual=whole['phases']['selected_new0193']
audit=json.loads(args.original_report2.read_text());assert len(audit['texts'])==18 and len(audit['extra_runs'])==0
assert whole['exact_scope_proved']and whole['errors']==[]
programs={'纯人声核对.py':'1050d1df51eb21ed0dbd19e9a97a8325c4dbfa1f58e9834760f8e5e5ba0b414f','疑点清单.py':'c55db5722dd2792d51d12efc3ea8225edb1bcec236b69c684ee220f79cf6ecea'}
assert {name:digest(T/name)for name in programs}==programs

assert digest(args.actual_nine_report)=='935f09429d3fe439c1ee68244057ec9254708db40ef770f540b1482a73cae764'
assert digest(args.preservation_proposal)=='c1bb14263a6365cbd6c1915dacf774f2d9aa6e1e57b9825901e0140cde4477b5'
nine=json.loads(args.actual_nine_report.read_text());assert nine['diagnostic_completed']and nine['exact_scope_proved']and not nine['errors']
proposal=json.loads(args.preservation_proposal.read_text())
assert local_decision['selected_in_memory_only_candidate']==proposal['unique_candidate']
assert local_decision['preserved_raw_w_sample_range']==proposal['preserved_raw_w_sample_range']==[134293,134839]
cases={'S13':[134293,134839]}
expected_cache={row['name']:row for row in whole['actual_used_source48_private_cache_entries_scalar_only']}
report['actual_whole_report_sha256']=digest(args.whole_report)
report['root_exact_local_input_selection_decision_sha256']=digest(args.local_input_decision)
report['actual_nine_sentence_edge_spectrum_report_sha256']=digest(args.actual_nine_report)
report['unique_candidate_proposal_sha256']=digest(args.preservation_proposal)
report['scope']='Only baseline and one conservative in-memory NV candidate for1 cached S13 sentence; exact originalguard/sentence_audio; no automatic-level function call/new G36, whole/encoder/render/TTS, source/CF/gain/cut override writes.'
report['production_source_CF_NV_gain_or_physical_cut_override_written']=False
report['semantic_lexical_classification_not_proved_by_numeric_guard']=True
report['source0193_and_GEN404_remain_unchanged']=True
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
            assert os.environ.get('STRICT_CACHE')=='1'and speed==m.SPEED and lang=='en-us'and np.array_equal(voice,m.V)
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
            return _fn(text,voice=voice,speed=speed,lang=lang,**kw)
        setattr(obj,method,guard)
    import ast
    dossier=ast.parse((T/'疑点清单.py').read_text());nodes=[n for n in dossier.body if isinstance(n,ast.FunctionDef)and n.name in ('to_w','words','per','spec')]
    assert len(nodes)==4;env={'np':np,'SR':SR};mod=ast.Module(body=nodes,type_ignores=[]);ast.fix_missing_locations(mod);exec(compile(mod,str(T/'疑点清单.py'),'exec'),env)
    per,spectral,words,to_w=(env[n]for n in ('per','spec','words','to_w'))

    # New level derivation is outside this local guard/mapper test.  The soleS13
    # baseline sentence has no auto/manual gain in the actual295 record.
    def forbidden_level(*unused_a,**unused_kw):
        raise AssertionError('No automatic-level math or cache lookup is permitted in this local test.')
    m._auto_level=forbidden_level
    rows=[];report['cases']=rows
    def snapshot_last():
        return {'segs':[(int(a),int(b),float(t),[(int(x),int(y))for x,y in rm])for a,b,t,rm in m.LAST['segs']],
                'cuts':[list(x)for x in m.LAST['cuts']], 'fades':[list(x)for x in m.LAST['fades']],
                'hs':int(m.LAST['hs']),'head':int(m.LAST['head']),'total':float(m.LAST['total'])}
    def mapper(it,n):
        # Use the original dossier's sample-coordinate mapper without modifying
        # it, including cap removals and sentence head trimming.
        return np.asarray([-1 if (w_:=to_w(it,j/SR))is None else int(w_)for j in range(n)],dtype=np.int64)
    def array_sha(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
    for sid,(keep_a,keep_b)in cases.items():
        report['in_progress_sentence']=sid
        si=int(sid[1:])-1;sent=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in new['sentences'][si]['chunks'])
        assert m.SENT_NO[sent]=='48'
        ref=actual['observed_sentences'][sid]
        assert ref['automatic_gain_dB']=={} and ref['manual_gain_dB']is None
        assert new.get('分段增益dB',{}).get(sid)in(None,{})
        original_controls=copy.deepcopy(new['非人声区间'][sid]);candidate_controls=copy.deepcopy(original_controls)
        assert sid=='S13' and candidate_controls[-1]==[5.595542,5.800208,'紧贴两头']
        candidate_controls[-1]=[134839/SR,5.800208,'紧贴两头']
        assert candidate_controls[-1]==local_decision['selected_in_memory_only_candidate']
        assert proposal['preserved_raw_w_sample_range']==[keep_a,keep_b]
        assert m.NONVOICE[sent]==original_controls
        raw,_=m.k.create(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us')
        w0=m.clean_tail(raw);head=m._head_offset(raw,w0);w=m._keep_tail(raw,w0,head)
        raw_sha,w_sha=array_sha(raw),array_sha(w)
        assert hashlib.md5(np.ascontiguousarray(w).tobytes()).hexdigest()[:12]==ref['actual_raw_w_fingerprint']
        baseline_guard=m._nonvoice(w,original_controls,sent)
        candidate_guard=m._nonvoice(w,candidate_controls,sent)
        mask=np.zeros(len(w),dtype=bool);mask[keep_a:keep_b]=True
        assert np.array_equal(candidate_guard[~mask],baseline_guard[~mask])
        assert np.array_equal(candidate_guard[mask],w[mask])
        assert array_sha(raw)==raw_sha and array_sha(w)==w_sha
        assert not np.shares_memory(baseline_guard,w)and not np.shares_memory(candidate_guard,w)
        pieces=[];gaps=[];p0=0;listing=m.list_commas(sent)
        for match in m.re.finditer(r'[,;:](?=\s)',sent):
            pieces.append((p0,match.end()));p0=match.end()+1;gaps.append(m.P_LIST if match.start()in listing else m.P_COMMA)
        pieces.append((p0,len(sent)))
        clips,tmap=m.sentence_audio(sent,pieces,gaps);before=np.concatenate(clips);before_it=snapshot_last()
        assert array_sha(before)==ref['pre_master_PCM_sha256']and len(before)==ref['samples']
        assert before_it['cuts']==ref['actual_raw_cuts']
        if 'tmap'in ref:assert [list(x)for x in tmap]==ref['tmap']
        m.NONVOICE[sent]=candidate_controls
        try:
            newclips,newtmap=m.sentence_audio(sent,pieces,gaps);after=np.concatenate(newclips);after_it=snapshot_last()
        finally:
            m.NONVOICE[sent]=original_controls
        assert m.NONVOICE[sent]==original_controls
        before_map,after_map=mapper(before_it,len(before)),mapper(after_it,len(after))
        assert all(int(x)<len(w)for x in before_map if x>=0)and all(int(x)<len(w)for x in after_map if x>=0)
        # A raw sample may be retained at most once; inserted silences map -1.
        bi=np.flatnonzero(before_map>=0);ai=np.flatnonzero(after_map>=0)
        assert len(np.unique(before_map[bi]))==len(bi)and len(np.unique(after_map[ai]))==len(ai)
        bindex=np.full(len(w),-1,dtype=np.int64);aindex=np.full(len(w),-1,dtype=np.int64)
        bindex[before_map[bi]]=bi;aindex[after_map[ai]]=ai
        common=(bindex>=0)&(aindex>=0);outside=common&~mask
        changed_outside=np.flatnonzero(before[bindex[outside]]!=after[aindex[outside]])
        old_nonzero=bi[before[bi]!=0];lost=old_nonzero[aindex[before_map[old_nonzero]]<0]
        common_nonzero=old_nonzero[aindex[before_map[old_nonzero]]>=0]
        altered=common_nonzero[before[common_nonzero]!=after[aindex[before_map[common_nonzero]]]]
        # Hard requirements preserve all previously retained nonzero voice and
        # shared physical output outside the exact restore interval.
        row={'sentence':sid,'raw_w_fingerprint':ref['actual_raw_w_fingerprint'],
             'current_authored_NV':original_controls,'unique_in_memory_candidate_NV':candidate_controls,
             'original_guard_passed_baseline_and_candidate':True,
             'preserved_raw_w_sample_range':[keep_a,keep_b],'restored_raw_samples':keep_b-keep_a,
             'candidate_guard_diff_only_inside_preserved_range':True,
             'restored_samples_equal_exact_original_raw':True,'raw_and_w_model_input_arrays_unchanged':True,
             'restored_nonzero_raw_samples':int(np.count_nonzero(w[keep_a:keep_b])),
             'baseline_pre_master_sha256':array_sha(before),'actual295_expected_pre_master_sha256':ref['pre_master_PCM_sha256'],
             'baseline_samples':len(before),'candidate_pre_level_output_sha256_NOT_final_mastered':array_sha(after),
             'candidate_samples':len(after),'candidate_minus_baseline_samples':len(after)-len(before),
             'baseline_actual_original_pipeline':before_it,'candidate_actual_original_pipeline':after_it,
             'baseline_tmap':[list(x)for x in tmap],'candidate_tmap':[list(x)for x in newtmap],
             'shared_mapped_raw_samples_outside_restore_range':int(np.count_nonzero(outside)),
             'shared_physical_output_changed_outside_restore_range_samples':len(changed_outside),
             'old_retained_nonzero_samples':len(old_nonzero),'old_retained_nonzero_samples_newly_dropped':len(lost),
             'old_retained_nonzero_samples_value_changed':len(altered),
             'candidate_no_new_auto_level_math_and_not_final_gain_or_QA':True,
             'actual_mapper_not_an_assumed_fixed_cut_or_clock':True}
        endpoint=keep_b
        if endpoint is not None:
            F5=round(.005*SR);refpeak=float(np.sqrt(np.mean(w[:len(w)//F5*F5].reshape(-1,F5)**2,axis=1)).max())
            lv=lambda z:20*math.log10(float(np.sqrt(np.mean(z*z)))/refpeak+1e-9)
            row['new_zero_crossing_endpoint']={'sample':endpoint,'seconds':endpoint/SR,
                'left_value':float(w[endpoint-1]),'right_value':float(w[endpoint]),
                'product':float(w[endpoint-1]*w[endpoint]),
                'preceding5ms_dB':lv(w[endpoint-F5:endpoint]),'following5ms_dB':lv(w[endpoint:endpoint+F5])}
        rows.append(row)
        assert len(changed_outside)==0,'Candidate changed retained raw-mapped sound outside exactrestore '+sid
        assert len(lost)==0 and len(altered)==0,'Candidate altered/dropped existing retained voice '+sid
    report['actual_used_existing_cached_entries_scalar_only']=list(used.values())
    report['actual_new_model_inference_count']=0
    report['whole_audio_not_rebuilt']=True;report['new_G36_math_count']=0
    report['no_production_source_CF_or_control_change']=True
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
    report['request_whole_and_original_report2_exact_after']=digest(request)==NEW_SHA and digest(args.whole_report)=='295fd087864e9ffbd2ad63edddb2da5d10af818b960c8a030e1ccdbd5537c591'and digest(args.original_report2)=='4e12f649e521a860ed416c4d098be57a1c177455411ef22b240fb3c563aa2153'
    report['actual_nine_report_exact_after']=digest(args.actual_nine_report)=='935f09429d3fe439c1ee68244057ec9254708db40ef770f540b1482a73cae764'
    report['unique_candidate_proposal_exact_after']=digest(args.preservation_proposal)=='c1bb14263a6365cbd6c1915dacf774f2d9aa6e1e57b9825901e0140cde4477b5'
    report['root_local_input_decision_exact_after']=digest(args.local_input_decision)=='879bd090a5a8fead18384bc9d367f6a7d28b4b5557d53234f7fb65f823d75cc5'
    report['exact_scope_proved']=bool(report.get('diagnostic_completed')and report['all_existing_private_cache_files_exact_before_after']and report['normal_W_scripts48_exact_restored']and report['normal_W_preexisting_work48_PCM_exact_restored']and report['all_other_W_source_scripts_exact']and report['original_maker_file_exact_after']and report['all_original_seven_runtime_core_files_exact_after']and report['request_whole_and_original_report2_exact_after']and report['actual_nine_report_exact_after']and report['unique_candidate_proposal_exact_after']and report['root_local_input_decision_exact_after'])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    print(json.dumps({'diagnostic_completed':report.get('diagnostic_completed'),'exact_scope_proved':report['exact_scope_proved'],'errors':report['errors'],'output_sha256':digest(args.output)},ensure_ascii=False))
sys.exit(0 if report['exact_scope_proved']else 1)
