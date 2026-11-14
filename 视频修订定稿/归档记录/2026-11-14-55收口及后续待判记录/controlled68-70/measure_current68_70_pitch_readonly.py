"""Diagnostic pitch only, exact native hashes first; no profile/source edits."""
import datetime, hashlib, importlib.util, json, pathlib, subprocess, tempfile
import numpy as np
import parselmouth
import soundfile as sf

B = pathlib.Path(__file__).parent
CI = pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch')

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

base = module('readonly68_70_original_replay', B / 'replay_cache_provenance.py')
U = module('unchanged_public_audio_numeric_pitch', CI / 'audio-qc.py')
assert sha(CI / 'audio-qc.py') == '3a2bd846386b16bd74e9785c548e97283131efcad9989b9e886f64e86e57c7c6'
orig = base.orig

for n in ['68', '70']:
    folder = B / n
    src = pathlib.Path('/workspace/work/video-audit70-20261113/payload/视频/脚本') / (n + '.json')
    raw_source = src.read_bytes()
    source = json.loads(raw_source)
    status_path = folder / (n + '-status.json')
    status = json.loads(status_path.read_text())
    diag_path = folder / (n + '-reference-gain-diagnostic.json')
    diag = json.loads(diag_path.read_text())
    old_path = folder / (n + '-accepted-public.mp4')
    audit_path = folder / 'actual-native-hash-bound-fulltrack-measurement' / (n + '-audio-audit.json')
    audit = json.loads(audit_path.read_text())
    assert sha(src) == status['request_source_sha256'][f'视频/脚本/{n}.json']
    assert sha(old_path) == status['accepted_source']['sha256']
    assert hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(old_path),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest() == status['accepted_source']['aac_adts_sha256']
    expected_count = len(source['sentences']) + 1
    spans = audit['measured_voice_spans']
    assert audit['sentence_mapping_valid'] is True and len(spans) == expected_count
    meta = diag['public_producer_timing_metadata']['segments']
    anchors = []
    for key in ['S3','S10','S16']:
        start,end = meta[key][0]['时刻']
        anchors.append([start + .15, min(end - .15, start + 2.5)])
    report = dict(article=n, kind='exact-native-hash-bound-all-sentence-pitch-diagnostic',
        quality_acceptance=False, production_delivery_eligible=False, profile_enabled=False,
        official_native_video_produced=False, source_sha256=sha(src),
        actual_native_status_sha256=sha(status_path), actual_native_run=43543967031,
        program_sha256=sha(__file__), numeric_utility_sha256=sha(CI/'audio-qc.py'),
        original_maker_sha256=hashlib.sha256(orig.m.source.encode()).hexdigest(),
        original_clean_sha256=hashlib.sha256(orig.m.clean.encode()).hexdigest(),
        old_accepted_video_sha256=sha(old_path),
        old_accepted_AAC_ADTS_sha256=status['accepted_source']['aac_adts_sha256'],
        original_producer_timing_metadata_sha256=sha(diag_path),
        independent_voice_map_report_sha256=sha(audit_path),
        pitch_count_and_cent_thresholds_unchanged=True,
        no_source_cache_core_or_existing_QC_profile_modified=True,
        no_new_source_candidate_or_gain_fitting=True)
    with tempfile.TemporaryDirectory(prefix='private-current-'+n+'-pitch-', dir='/dev/shm') as td:
        td=pathlib.Path(td);cache=td/'cache';cache.mkdir()
        audio,_ = orig.build(source,cache)
        wav=td/'actual.wav';sf.write(wav,audio,24000)
        assert sha(wav) == diag['wav_sha256']
        aac=td/'actual-audio-only.m4a'
        subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
        ash=hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest()
        assert ash == status['canonical_aac_adts_sha256']
        old=U.decode(old_path);new=U.decode(aac)
        lag,lags=U.alignment_lag(old,new,anchors)
        alignment_ok=abs(lag)/48000 <= .02 and max(lags)-min(lags) <= round(.006*48000)
        aligned=U.align_new(new,lag,len(old))
        report.update(actual_native_WAV_sha256=sha(wav),actual_native_AAC_ADTS_sha256=ash,
            full_WAV_and_AAC_exact_actual_native_before_measurement=True,
            alignment_reference_spans=anchors,alignment_lag_samples=lag,local_lags_samples=lags,
            original_alignment_thresholds_passed=alignment_ok,
            decoded_duration_delta_s=(len(new)-len(old))/48000)
        rows=[]
        for i,(start,end) in enumerate(spans):
            tracks=[parselmouth.Sound(v[round(start*48000):round(end*48000)],sampling_frequency=48000).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=400).selected_array['frequency'] for v in (old,aligned)]
            size=min(map(len,tracks));a,b=(x[:size]for x in tracks);keep=(a>0)&(b>0)
            cents=abs(1200*np.log2(b[keep]/a[keep]))
            median=float(np.median(cents))if len(cents)else None;p90=float(np.percentile(cents,90))if len(cents)else None
            rows.append(dict(sentence='title'if i==0 else'S'+str(i),start_s=start,end_s=end,
                voiced_pairs=len(cents),median_absolute_cents=median,p90_absolute_cents=p90,
                passed=bool(len(cents)>10 and median<=40 and p90<=150)))
        report.update(pitch_comparison=rows,all_title_and_body_pitch_checks_passed=all(x['passed']for x in rows),
            checks_do_not_replace_original_pipeline_or_full_controlled_profile=True)
    assert src.read_bytes() == raw_source
    report.update(private_reconstructed_PCM_and_AAC_deleted=True,no_PCM_GT_cache_or_dense_audio_arrays_exported=True,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    target=folder/(n+'-current-native-all-sentence-pitch-diagnostic.json')
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(article=n,exact_WAV_AAC=True,pitch_all_passed=report['all_title_and_body_pitch_checks_passed'],sentences=len(rows),alignment=alignment_ok,report=str(target),sha256=sha(target)),ensure_ascii=False),flush=True)
