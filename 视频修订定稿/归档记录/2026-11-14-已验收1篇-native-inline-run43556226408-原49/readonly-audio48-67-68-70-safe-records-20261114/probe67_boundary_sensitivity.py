"""Original rules, actual-native-bound audio, boundary sensitivity only."""
import hashlib,importlib.util,json,pathlib,subprocess,tempfile
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent;f=B/'67';P=B/'replay_cache_provenance.py';s=importlib.util.spec_from_file_location('readonly67_sensitivity',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);orig=m.orig
AP=pathlib.Path('/workspace/work/audio-repair67-70/audit_audio.py');s=importlib.util.spec_from_file_location('unchanged_supplementary_sensitivity',AP);A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
sha=lambda x:hashlib.sha256(x).hexdigest();req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request/67/视频/脚本/67.json');data=json.loads(req.read_text());st=json.loads((f/'67-status.json').read_text());d=json.loads((f/'actual-native-hash-bound-fulltrack-measurement/67-audio-audit.json').read_text());dg=json.loads((f/'67-reference-gain-diagnostic.json').read_text())
spans={}
measured=next(x for x in d['all_body_sentences_including_S1']['sentences']if x['sentence']=='S9')['parts']
spans['independently_measured_MP4']=[(x['start'],x['end'])for x in measured]
spans['actual_native_producer_tmap']=[tuple(x['时刻'])for x in dg['public_producer_timing_metadata']['segments']['S9']]
report=dict(source_id='67',quality_acceptance=False,purpose='original current suppression-rule boundary sensitivity around actual S9 part3, without changing any audio or thresholds',program_sha256=sha(pathlib.Path(__file__).read_bytes()),cases=[])
with tempfile.TemporaryDirectory(prefix='private67-boundary-only-',dir='/dev/shm')as td:
    td=pathlib.Path(td);cache=td/'cache';cache.mkdir();a,_=orig.build(data,cache);wav=td/'native.wav';aac=td/'native.m4a';sf.write(wav,a,24000)
    assert sha(wav.read_bytes())==st['final_wav_sha256']
    subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
    ah=sha(subprocess.check_output(['ffmpeg','-v','error','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']));assert ah==st['canonical_aac_adts_sha256'];report['entire_actual_native_WAV_and_AAC_hashes_exact']=True
    tools,R,Q,hashes,load=A.canonical_files(td/'original-tools','67',data,False);TM=R.momentary(str(aac));report['unchanged_tool_sha256']=hashes
    report['unchanged_original_thresholds']={k:getattr(R,k)for k in ['IN_DIP_G','IN_DIP_PK','IN_ADJ']}
    for label,parts in spans.items():
        rows=[];target=parts[2]
        for ds in [-.04,-.02,0,.02,.04]:
            for de in [-.04,-.02,0,.02,.04]:
                lo,hi=target[0]+ds,target[1]+de;raw,pk=R.段量(TM,lo,hi);effective=R.等效(raw,lo,hi,True);neighbors=[]
                for ni in [1,3]:
                    x,y=parts[ni];nr,npk=R.段量(TM,x,y);ne=R.等效(nr,x,y,True);dgain=float(ne-effective);dpeak=float(npk-pk)
                    neighbors.append(dict(neighbor_part=ni+1,effective_difference_lu=dgain,peak_difference_lu=dpeak,reported_suppression=dgain>R.IN_DIP_G and dpeak>R.IN_DIP_PK))
                rows.append(dict(start_s=lo,end_s=hi,span_duration_s=hi-lo,raw_lufs=float(raw),effective_lufs=float(effective),peak_lufs=float(pk),neighbors=neighbors,any_original_suppression=any(x['reported_suppression']for x in neighbors)))
        report['cases'].append(dict(boundary_basis=label,original_target_span_s=list(target),original_target_duration_s=target[1]-target[0],rows=rows,
            original_suppression_perturbation_count=sum(x['any_original_suppression']for x in rows),perturbation_count=25,
            stable_same_result_across_20_40ms=all(x['any_original_suppression']for x in rows)or not any(x['any_original_suppression']for x in rows)))
report['no_TTS_no_source_cache_core_algorithm_or_threshold_changed']=True;report['private_diagnostic_audio_deleted']=True
out=f/'67-S9-original-rule-boundary-sensitivity.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print([(x['boundary_basis'],x['original_suppression_perturbation_count'],x['stable_same_result_across_20_40ms'])for x in report['cases']],'reportSHA',sha(out.read_bytes()),flush=True)
