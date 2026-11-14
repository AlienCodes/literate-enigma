"""Isolated +0.8dB S9#3 proposal; preserve every latest existing repair.

This is an independently measured new repair proposal, not a rollback or old-AAC
fit. Current source, original current K134 cache, code and thresholds stay intact.
"""
import copy,datetime,hashlib,importlib.util,json,pathlib,subprocess,tempfile
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent;f=B/'67';P=B/'replay_cache_provenance.py';spec=importlib.util.spec_from_file_location('readonly67_repair',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);o=m.orig
AP=pathlib.Path('/workspace/work/audio-repair67-70/audit_audio.py');spec=importlib.util.spec_from_file_location('original_unchanged67_audit',AP);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
sha=lambda x:hashlib.sha256(x).hexdigest();req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request/67/视频/脚本/67.json');raw=req.read_bytes();data=json.loads(raw);candidate=copy.deepcopy(data)
assert not candidate.get('分段增益dB',{}).get('S9',{}).get('3')
candidate.setdefault('分段增益dB',{}).setdefault('S9',{})['3']=.8
cp=f/'67-proposed-S9-part3-plus0p8-source.json';cp.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
assert candidate['sentences']==data['sentences']and candidate['段内渐变dB']==data['段内渐变dB']
st=json.loads((f/'67-status.json').read_text());diag=json.loads((f/'67-reference-gain-diagnostic.json').read_text());interval=diag['public_producer_timing_metadata']['segments']['S9'][2]['时刻']
out=f/'proposed-S9-part3-plus0p8-fulltrack-measurement';out.mkdir(exist_ok=True)
rep=dict(source_id='67',quality_acceptance=False,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    purpose='minimal new current-source segment gain repair proposal after stable original-rule detection; pending root review and actual original production gates',
    program_sha256=sha(pathlib.Path(__file__).read_bytes()),original_current_maker_sha256=sha(o.m.source.encode()),original_supplemental_audit_sha256=sha(AP.read_bytes()),
    current_source_sha256=sha(raw),candidate_source_sha256=sha(cp.read_bytes()),candidate_source_path=str(cp),
    only_source_candidate_change='/分段增益dB/S9/3: absent to +0.8dB',reason='Current native has original suppression at S9#3 in all25 boundary variants for both independently measured and producer boundaries. +0.8 gives peak margin4.6-.8=3.8dB under original4.0 rule without altering any existing repair.',
    existing_S1_name_gain_and_ramp_preserved=True,existing_S9_part4_gain_preserved=True,existing_S15_K134_approved_phrase_balance_preserved=True,
    actual_current_K134_cache_unchanged=True,all_visible_body_translation_notes_summary_unchanged=True,original_detected_target_interval_s=interval)
with tempfile.TemporaryDirectory(prefix='private67-S9-proposal-',dir='/dev/shm')as td:
    td=pathlib.Path(td);cache=td/'cache';cache.mkdir();base,_=o.build(data,cache);basewav=td/'actual-native.wav';sf.write(basewav,base,24000)
    assert sha(basewav.read_bytes())==st['final_wav_sha256'];new,parts=o.build(candidate,cache);assert len(base)==len(new)
    lo,hi=[round(x*24000)for x in interval];mask=np.ones(len(base),dtype=bool);mask[lo:hi]=False
    rep['all_preencoding_samples_outside_actual_target_segment_exact']=bool(np.array_equal(base[mask],new[mask]));rep['outside_target_base_array_sha256']=sha(base[mask].tobytes());rep['outside_target_candidate_array_sha256']=sha(new[mask].tobytes());rep['same_total_sample_count']=len(base)
    diff=np.flatnonzero(base!=new);rep['actual_changed_preencoding_span_s']=None if not len(diff)else[int(diff[0])/24000,int(diff[-1])/24000]
    wav=td/'proposal.wav';aac=td/'proposal.m4a';sf.write(wav,new,24000)
    subprocess.run([o.FF,'-y','-loglevel','error','-i',str(wav),'-af',o.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
    rep['candidate_WAV_sha256']=sha(wav.read_bytes());rep['candidate_AAC_ADTS_sha256']=sha(subprocess.check_output(['ffmpeg','-v','error','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']))
    r=A.audit('67',video=aac,out_dir=out,asr=False);rep['original_fulltrack_supplementary_numeric_checks_passed']=r['numerical_audio_checks_passed'];rep['original_fulltrack_failures']=r['failures'];rep['all_title_and_body_sentence_mapping_valid']=r['sentence_mapping_valid'];rep['actual_measurement_report']=str(out/'67-audio-audit.json');rep['actual_measurement_report_sha256']=sha((out/'67-audio-audit.json').read_bytes())
    tools,R,Q,hashes,load=A.canonical_files(td/'boundary-tools','67',candidate,False);TM=R.momentary(str(aac));sourceReport=json.loads((f/'actual-native-hash-bound-fulltrack-measurement/67-audio-audit.json').read_text());measured=next(x for x in sourceReport['all_body_sentences_including_S1']['sentences']if x['sentence']=='S9')['parts']
    sets={'independent_baseline_boundaries':[(x['start'],x['end'])for x in measured],'actual_native_producer_tmap':[tuple(x['时刻'])for x in diag['public_producer_timing_metadata']['segments']['S9']]};results=[]
    for label,spans in sets.items():
        rows=[]
        for ds in [-.04,-.02,0,.02,.04]:
            for de in [-.04,-.02,0,.02,.04]:
                x,y=spans[2][0]+ds,spans[2][1]+de;v,p=R.段量(TM,x,y);v=R.等效(v,x,y,True);ns=[]
                for ni in [1,3]:
                    a,b=spans[ni];nv,npk=R.段量(TM,a,b);nv=R.等效(nv,a,b,True);dg=float(nv-v);dp=float(npk-p);ns.append(dict(neighbor=ni+1,effective_difference_lu=dg,peak_difference_lu=dp,suppression=dg>R.IN_DIP_G and dp>R.IN_DIP_PK))
                rows.append(dict(start_s=x,end_s=y,neighbors=ns,suppression=any(z['suppression']for z in ns)))
        results.append(dict(boundary_basis=label,suppression_count=sum(x['suppression']for x in rows),total=25,rows=rows))
    rep['original_rule_20_40ms_boundary_sensitivity']=results
rep['no_TTS_no_production_no_source_or_existing_cache_or_core_or_threshold_changed']=True;rep['private_proposal_audio_deleted']=True
p=f/'67-S9-part3-plus0p8-proposal-report.json';p.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print('67 proposal numeric',rep['original_fulltrack_supplementary_numeric_checks_passed'],'outsideExact',rep['all_preencoding_samples_outside_actual_target_segment_exact'],'sensitivity',[(x['boundary_basis'],x['suppression_count'])for x in rep['original_rule_20_40ms_boundary_sensitivity']],'reportSHA',sha(p.read_bytes()),flush=True)
