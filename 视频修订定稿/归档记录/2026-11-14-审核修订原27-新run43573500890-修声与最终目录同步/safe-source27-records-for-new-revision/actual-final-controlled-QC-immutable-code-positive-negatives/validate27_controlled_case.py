"""Real original-cache two-source replay, original PV transfer, and QC tests."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile
import numpy as np
import soundfile as sf

H=Path(__file__).parent;B=H.parent
CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch')
OUT=H/'controlled-QC-real-verification';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v);return v
C=module('unchanged27_numeric_common',CI/'audio-controlled-qc.py')
U=module('unchanged27_numeric_utility',CI/'audio-qc.py')
original_context=B/'audio-a21-actual-first-4K-20261114/probe_minimal_encoded_boost.py'
context={'__file__':str(original_context),'__name__':'original27_source_punctuation_and_level_context'}
exec(compile(original_context.read_text().split('for no in sys.argv')[0],str(original_context)+'#definitions-only','exec'),context)
o=context['r']
T=o.m.T
old_path=H/'candidate-payload/视频/脚本/27.json';new_path=B/'payload/视频/脚本/27.json';gen_path=B/'payload/视频/工具/初稿生成/gen27.py'
assert sha(old_path)=='1e7b2a55ff5df575a9065fe5f827cfd4c42b55832dd1a535e44e9f7048fe31d4'
assert sha(new_path)=='e1214d8e9314a1cb54da82e2532889198bec555d6be9189fbfb43b5fdedcd728'
assert sha(gen_path)=='8509dd84018445aadb204b6bd9b2e7a609dbf65aed59e4a725f515053a820dbb'
accepted=H/'27-original-accepted-public.mp4';assert sha(accepted)=='4ab9da92fd3f57c226bd064c4c076d3f3b5428545542410d83ddc7cd90d9075e'
proposal_path=H/'private-audio-opening-candidates/27-two-opening-mixed-gain-QC-profile-proposal-v1.json';proposal=json.loads(proposal_path.read_text())
sources={'old':json.loads(old_path.read_text()),'new':json.loads(new_path.read_text())};new_bytes=new_path.read_bytes();capture={};label='';real_scope=o.scope
def scope(d,si,cache):
    ns,text=real_scope(d,si,cache);original=ns['句增益']
    def wrapped(*args,**kw):
        result=original(*args,**kw)
        capture[label]['S'+str(si)]={'tmap':copy.deepcopy(args[7]),'gaps':copy.deepcopy(args[5]),'auto':copy.deepcopy(result[2]),'manual':copy.deepcopy(result[3])}
        return result
    ns['句增益']=wrapped;return ns,text
o.scope=scope
expected={'old':('e15a2d05428e3219216ac8d10780669007f903071b0fcfc3c6bf377c517b8d7f','14bc91c62e66921fb55a215a42ce2db6a5544316600687b535a468770ae28252'),
          'new':('def5cf361fc57229ff8e14bf8db379fa60ca876b4ecde7eae6689444d4416ea7','d619f0175ab2c57c6a5b77b9c6f0d62cd5b9fc2c548ec3900a45b3c44919b6f9')}
report={'article':'27','diagnostic_only':True,'production_delivery_eligible':False,'official_video_produced':False,'all_tests_passed':False,'source_core_or_existing_cache_modified':False,'program_sha256':sha(__file__),'profile_proposal_sha256':sha(proposal_path),'tests':[]}
with tempfile.TemporaryDirectory(prefix='private27_exact_controlled_QC_',dir='/dev/shm')as td:
    td=Path(td);cache=td/'cache';cache.mkdir();work=td/'work';(work/'scripts').mkdir(parents=True);(work/'work_27').mkdir();request=td/'request';(request/'视频/脚本').mkdir(parents=True);(request/'视频/工具/初稿生成').mkdir(parents=True)
    wavs={};encoded={};allparts={};bindings={}
    for label,data in sources.items():
        capture[label]={};audio,parts=o.build(data,cache);wav=td/(label+'.wav');sf.write(wav,audio,24000);aac=td/(label+'.m4a')
        subprocess.run([o.FF,'-y','-v','error','-i',str(wav),'-af',o.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
        assert (sha(wav),C.aac_sha(aac))==expected[label],(label,sha(wav),C.aac_sha(aac))
        bindings[label]={'WAV_sha256':sha(wav),'AAC_ADTS_sha256':C.aac_sha(aac),'MD5_first12':hashlib.md5(wav.read_bytes()).hexdigest()[:12],'samples':len(audio)}
        wavs[label]=wav;encoded[label]=aac;allparts[label]=parts
    report['four_full_WAV_AAC_bindings']=bindings
    assert C.aac_sha(accepted)==expected['old'][1]
    groups={}
    for part in allparts['new']:
        name=part['sentence']
        if name=='title':continue
        row=capture['new'][name];auto=row['auto'];manual=row['manual']or{};tmap=row['tmap'];gaps=row['gaps'];start=part['start_s']
        groups[name]=[{'段':i+1,'增益':round(auto.get(i+1,0.)+float(manual.get(str(i+1),0.)),3),'停顿':round(float(gaps[i]),3)if i<len(gaps)else None,'时刻':[round(start+a,4),round(start+b,4)]}for i,(_,_,a,b)in enumerate(tmap)]
    shutil.copyfile(wavs['new'],work/'work_27/a.wav');(work/'scripts/27.json').write_bytes(new_bytes);(work/'work_27/分段.json').write_text(json.dumps(groups,ensure_ascii=False));(work/'work_27/词尾除阻.json').write_text('[]')
    os.link(encoded['new'],work/'27.mp4')  # Original AUDIO_ONLY mapper input; no video is synthesized.
    shutil.copyfile(new_path,request/'视频/脚本/27.json');shutil.copyfile(gen_path,request/'视频/工具/初稿生成/gen27.py')
    core=lambda d:{k:v for k,v in d.items()if k not in('核对确认','区间声音指纹')}
    metadata={'no','title_en','title_zh','title_fx','sentences','核对确认','区间声音指纹','结尾解说','术语','allow_clash','说明放宽特批','换行变更记录','字号上限'}
    controls={k:v for k,v in sources['new'].items()if k not in metadata}
    units={}
    for target in proposal['targets']:
        name=target['sentence']+'#1';units[name]={'span_s':groups[target['sentence']][0]['时刻'],'public_measurement_span_s':target['public_measurement_span_s'],'gain_delta_dB':target['additional_gain_db'],'word':target['word'],'raw_to_public_clock_diagnostic':target['raw_to_public_clock_diagnostic']}
    anchors=[]
    for name in ['S3','S8','S16']:
        a,b=groups[name][0]['时刻'];anchors.append([a+.15,min(b-.1,a+1.25)])
    profile={'article':'27','enabled':True,'state':'exact-root-authorized-source-two-measured-gains-only','diagnostic_evidence_does_not_claim_native_4K_pass':True,'source_application_report_sha256':sha(H/'measured-audio-source-application/report.json'),'profile_proposal_sha256':sha(proposal_path),'fingerprints':{'request_source_sha256':sha(new_path),'request_generator_sha256':sha(gen_path),'actual_raw_WAV_sha256':expected['new'][0],'accepted_video_sha256':sha(accepted),'accepted_AAC_ADTS_sha256':expected['old'][1],'canonical_AAC_ADTS_sha256':expected['new'][1]},'existing_review_only_top_level_keys':['核对确认','区间声音指纹'],'approved_request_nonreview_document_sha256':C.canonical(core(sources['new'])),'approved_actual_nonreview_document_sha256':[C.canonical(core(sources['new']))],'approved_audio_controls':controls,'raw_WAV_shape':{'rate':24000,'channels':1,'width':2,'samples':3603240},'alignment_reference_spans':anchors,'approved_opening_units':units,'approved_producer_group_metadata':groups,'original_tool_sha256':json.loads((CI/'audio-controlled-qc-reference.json').read_text())['profiles']['67']['original_tool_sha256'],'unchanged_original_thresholds':{'whole_track_delta_LU':.8,'outside_gain_dB':.35,'outside_NCC':.985,'outside_residual_SNR_dB':22,'outside_frame_gain_p95_dB':.8,'controlled_gain_dB_tolerance':.35,'controlled_LU_delta_tolerance':.55,'pitch_median_cents':40,'pitch_p90_cents':150}}
    evidence_path=OUT/'S12-existing-accepted-exact-sample-evidence.json';evidence=json.loads(evidence_path.read_text());assert evidence['root_conditions_satisfied']
    pwin,pcontext=evidence['public_exact_sample_proof']
    profile['baseline_existing_unchanged_S12_2']={'sentence':'S12','independent_R_segment':2,'public_window_s':[99.2,101.4],'public_context_s':[92.8,101.6],'exact_original_R_finding':evidence['old_original_raw_suppression_findings'][0],'public_window_float32_sha256':pwin['old_sha256'],'public_context_float32_sha256':pcontext['old_sha256'],'native_prefix_representation':'WAV_PCM16_read_as_float32','native_WAV_PCM16_read_as_float32_prefix_sha256':evidence['native_prefix_24k_float32']['WAV_PCM16_roundtrip_float32_actual_old_sha256'],'pre_SF_original_build_float32_prefix_sha256':evidence['native_prefix_24k_float32']['pre_SF_original_build_float32_old_and_new_sha256'],'original_S12_producer_group_metadata':groups['S12'],'actual_old_and_new_original_R_evidence_sha256':sha(evidence_path),'authorization':'Root exact single already-accepted S12#2 condition; retain raw failures, no threshold/audio/source changes; changed public sample must reject.'}
    reference=CI/'audio27-controlled-qc-reference.json';reference.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n');shutil.copyfile(reference,OUT/'actual-frozen-reference.json')
    for basename,args in [('original-confirmation-transfer',[str(T/'确认平移.py'),'27',str(wavs['old']),'--写入']),('original-PV',[str(T/'纯人声核对.py'),'27']),('original-PV-selftest',[str(T/'纯人声核对.py'),'27','--自检'])]:
        env={**os.environ,'PATH':str(Path(sys.executable).parent)+os.pathsep+os.environ.get('PATH','')}
        p=subprocess.run([sys.executable,*args],cwd=work,env=env,capture_output=True,text=True);(OUT/(basename+'.log')).write_text(p.stdout+'\n'+p.stderr);report[basename]={'exit':p.returncode,'last_lines':p.stdout.strip().splitlines()[-4:],'actual_BAD_lines':[s for s in p.stdout.splitlines()if' BAD'in s]}
    after=json.loads((work/'scripts/27.json').read_text());assert core(after)==core(sources['new']);assert sha(work/'work_27/a.wav')==expected['new'][0]
    Q=module('actual27_controlled_case',CI/'audio27-controlled-qc.py')
    args=argparse.Namespace(article='27',accepted_source=str(accepted),canonical_video=str(encoded['new']),work=str(work),request=str(request),output=str(OUT/'27-actual-diagnostic-positive.json'),actual_source=None,raw_pcm=None,tools=str(T),reference=str(reference),diagnostic=True)
    code=Q.audit(args);positive=json.loads(Path(args.output).read_text());report['positive_exit']=code;report['positive_error']=positive.get('error');report['positive_failed_checks']=[r for r in positive['checks']if not r['passed']];assert code==0 and positive['passed']and positive['diagnostic_only']and not positive['production_delivery_eligible'],report['positive_failed_checks']or positive.get('error')
    report['tests'].append({'name':'exact-real-original-cache-audio-diagnostic-positive','passed':True,'official_native_or_production_acceptance_claimed':False,'report_sha256':sha(args.output)})
    old=U.decode(accepted);new=U.decode(encoded['new']);lag,_=U.alignment_lag(old,new,anchors);aligned=U.align_new(new,lag,len(old));bad=aligned.copy();lo,hi=round(3.2*48000),round(4.2*48000);assert 20*np.log10(np.sqrt(np.mean(old[lo:hi]**2)))>-40;bad[lo:hi]*=10**(6/20);checks=[];C.outside_measurements(U,old,bad,[u['span_s']for u in units.values()],checks);failed=[x for x in checks if not x['passed']];assert any(x['name']=='every-untouched-active-one-second-block-preserved'for x in failed)
    s12bad=aligned.copy();s12bad[round(100.*48000)]+=2**-15
    changed_S12=Q.exact_existing_S12(profile,old,s12bad,work/'work_27/a.wav',evidence['old_original_raw_suppression_findings'],evidence['new_original_raw_suppression_findings'],groups['S12'])
    assert not changed_S12['preservation_conditions_passed']
    report['tests'].append({'name':'actual-S12-public-decoded-one-sample-change-strictly-rejected','passed':True,'changed_sample_time_s':100.,'delta':2**-15,'actual_numeric_preservation_result':changed_S12})
    report['tests'].append({'name':'real-decoded-outside-voiced-block-plus6dB-rejected-numerically','passed':True,'actual_public_decoded_mutation_span_s':[3.2,4.2],'failed_original_numeric_checks':failed})
    clip=aligned.copy();clip[lo]=1.1;assert not(np.isfinite(clip).all()and float(np.max(abs(clip)))<1.)
    report['tests'].append({'name':'actual-decoded-digital-clipping-negative','passed':True,'actual_sample':1.1,'original_no_clipping_condition':False})
    wrong=copy.deepcopy(after);wrong['分段增益dB']['S13']['1']=-3.5;wrongpath=td/'wrong-controls.json';wrongpath.write_text(json.dumps(wrong,ensure_ascii=False));negative=copy.copy(args);negative.actual_source=str(wrongpath);negative.output=str(OUT/'27-wrong-control-negative.json');code=Q.audit(negative);doc=json.loads(Path(negative.output).read_text());failed=[r['name']for r in doc['checks']if not r['passed']];assert code!=0 and not doc['production_delivery_eligible']and'exact-entire-actual-nonreview-document'in failed and'all-approved-audio-controls-exact'in failed
    report['tests'].append({'name':'wrong-effective-source-gain-rejected','passed':True,'failed_checks':failed,'report_sha256':sha(negative.output)})
    assert new_path.read_bytes()==new_bytes
report.update(all_tests_passed=True,private_generated_PCM_AAC_and_cloned_sources_deleted=True,no_PCM_GT_cache_exported=True,helper_program_sha256=sha(CI/'audio27-controlled-qc.py'),reference_sha256=sha(CI/'audio27-controlled-qc-reference.json'))
p=OUT/'actual-positive-and-negative-tests.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item()if isinstance(x,np.generic)else str(x))+'\n');print(json.dumps({'all_tests_passed':True,'helper_sha256':report['helper_program_sha256'],'reference_sha256':report['reference_sha256'],'report_sha256':sha(p),'positive_check_count':len(positive['checks'])},ensure_ascii=False))
