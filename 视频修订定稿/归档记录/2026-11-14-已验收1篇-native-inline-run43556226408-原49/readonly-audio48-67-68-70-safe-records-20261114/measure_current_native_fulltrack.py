"""Unmodified original supplementary full-track audio measurement, no delivery.

Only exact native WAV/AAC-hash-matched cache reconstruction may be measured.
Private audio is removed. Original actual native ASR/pre/post reports stay separate.
"""
import datetime,hashlib,importlib.util,json,pathlib,subprocess,tempfile,traceback
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent;P=B/'replay_cache_provenance.py';s=importlib.util.spec_from_file_location('current_native_measurement',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
orig=m.orig;sha=lambda x:hashlib.sha256(x).hexdigest()
AP=pathlib.Path('/workspace/work/audio-repair67-70/audit_audio.py');spec=importlib.util.spec_from_file_location('unchanged_original_supplemental_audit',AP);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
for no in ['67','68','70']:
    f=B/no;out=f/'actual-native-hash-bound-fulltrack-measurement';out.mkdir(exist_ok=True)
    st=json.loads((f/f'{no}-status.json').read_text());dg=json.loads((f/f'{no}-reference-gain-diagnostic.json').read_text())
    req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request')/no/f'视频/脚本/{no}.json';raw=req.read_bytes()
    bind=dict(source_id=no,quality_acceptance=False,purpose='additional original whole-track numeric measurements of exact actual-native hash-bound audio reconstruction; no newly rendered video',
        program_sha256=sha(pathlib.Path(__file__).read_bytes()),original_unchanged_supplementary_audit_path=str(AP),original_unchanged_supplementary_audit_sha256=sha(AP.read_bytes()),
        requested_source_sha256=sha(raw),actual_native_run=43543967031,actual_native_status_sha256=sha((f/f'{no}-status.json').read_bytes()),
        actual_original_native_canonical_pipeline_passed=st['canonical_pipeline_passed'],actual_original_native_ASR_and_selftest_results_retained=True,
        new_ASR_performed=False,temporary_audio_only_container_not_a_delivered_4K=True)
    assert sha(raw)==st['request_source_sha256'][f'视频/脚本/{no}.json']
    try:
        with tempfile.TemporaryDirectory(prefix=f'private-{no}-native-fulltrack-',dir='/dev/shm')as td:
            td=pathlib.Path(td);cache=td/'cache';cache.mkdir();audio,parts=orig.build(json.loads(raw),cache)
            wav=td/'native.wav';aac=td/'native.m4a';sf.write(wav,audio,24000)
            subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
            wsh=sha(wav.read_bytes());ash=sha(subprocess.check_output(['ffmpeg','-v','error','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']))
            bind.update(reconstructed_WAV_sha256=wsh,actual_native_WAV_sha256=st['final_wav_sha256'],reconstructed_AAC_ADTS_sha256=ash,actual_native_AAC_ADTS_sha256=st['canonical_aac_adts_sha256'])
            assert wsh==st['final_wav_sha256']==dg['wav_sha256']and ash==st['canonical_aac_adts_sha256']
            bind['entire_actual_native_WAV_and_AAC_matched_before_measurement']=True
            report=A.audit(no,video=aac,out_dir=out,asr=False)
            bind.update(measured_report=str(out/f'{no}-audio-audit.json'),measured_report_sha256=sha((out/f'{no}-audio-audit.json').read_bytes()),
                exact_original_numeric_audio_checks_passed=report.get('numerical_audio_checks_passed'),
                exact_original_numeric_failures=report['failures'],original_preservation_failures_expected_for_real_changed_audio=report['preservation_failures'],
                measured_all_title_plus_body_mapping_valid=report.get('sentence_mapping_valid'))
    except BaseException as ex:
        bind['error']=dict(type=type(ex).__name__,detail=str(ex),traceback=traceback.format_exc());print(traceback.format_exc(),flush=True)
    bind['private_diagnostic_audio_deleted']=True;bind['no_TTS_no_source_cache_core_or_threshold_changes']=True
    p=out/f'{no}-actual-native-binding-and-limitations.json';p.write_text(json.dumps(bind,ensure_ascii=False,indent=2)+'\n')
    print(no,'original supplementary numeric outcome',bind.get('exact_original_numeric_audio_checks_passed'),'failures',bind.get('exact_original_numeric_failures'),'bindingSHA',sha(p.read_bytes()),flush=True)
