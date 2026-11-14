#!/usr/bin/env python3
"""Exact source60 approved sole first-piece +2dB repair supplement.

Called after the unchanged official native draft/final/stamp gates. It never
synthesizes, repairs, changes a source/threshold, exports PCM, or replaces ASR.
Diagnostic mode cannot certify production. All waveform inputs are measured.
"""
import argparse
import contextlib
import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import wave

import numpy as np

HERE=Path(__file__).resolve().parent
SR=48000

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()

def canonical(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()

def safe(value):
    if isinstance(value,dict):return {str(k):safe(v)for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [safe(v)for v in value]
    if isinstance(value,np.integer):return int(value)
    if isinstance(value,(float,np.floating)):return float(value)if np.isfinite(value)else None
    if isinstance(value,np.bool_):return bool(value)
    return value

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value
    spec.loader.exec_module(value);return value

def capture(cmd):return subprocess.check_output([str(x)for x in cmd])

def aac(path):
    return capture(['ffmpeg','-v','error','-nostdin','-i',path,
        '-map','0:a:0','-c:a','copy','-f','adts','-'])

def adts_packets(data):
    packets=[];pos=0
    while pos<len(data):
        if not(data[pos]==255 and data[pos+1]&240==240):raise ValueError('Invalid ADTS sync.')
        n=((data[pos+3]&3)<<11)|(data[pos+4]<<3)|(data[pos+5]>>5)
        if n<=7 or pos+n>len(data):raise ValueError('Invalid ADTS frame size.')
        packets.append(data[pos:pos+n]);pos+=n
    if pos!=len(data):raise ValueError('Incomplete ADTS input.')
    return packets

def spoken(data):
    return [data['title_en']]+[' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en'])
        for c in sentence['chunks'])for sentence in data['sentences']]

def actual_nonreview_binding(actual,requested,profile):
    """Allow only the original maker's exact pending-consent history move.

    The original prefix and quote remain exact; the maker's ISO date is not
    predicted from this machine's wall date. All other nonreview data still
    has to equal the frozen requested document after this one move is undone.
    """
    current=copy.deepcopy(actual)
    keys=('换行变更已获同意','换行变更记录')
    moved=any(requested.get(k)!=actual.get(k)for k in keys)
    if moved:
        consent=requested.get(keys[0]);before=requested.get(keys[1],[]);after=actual.get(keys[1],[])
        if not(isinstance(consent,dict)and consent and keys[0]not in actual and
               isinstance(before,list)and isinstance(after,list)and len(after)==len(before)+1 and
               after[:-1]==before and isinstance(after[-1],dict)):
            return False,{'original_pending_consent_consumed':True,'exact_history_move_valid':False}
        last=after[-1];day=last.get('日期','')
        if not(isinstance(day,str)and re.fullmatch(r'\d{4}-\d{2}-\d{2}',day)and
               {k:v for k,v in last.items()if k!='日期'}==consent):
            return False,{'original_pending_consent_consumed':True,'exact_history_move_valid':False}
        try:datetime.date.fromisoformat(day)
        except ValueError:return False,{'original_pending_consent_consumed':True,'exact_history_move_valid':False}
        current[keys[0]]=copy.deepcopy(consent)
        if keys[1]in requested:current[keys[1]]=copy.deepcopy(before)
        else:current.pop(keys[1],None)
    core={k:v for k,v in current.items()if k not in profile['review_only_top_level_keys']}
    valid=canonical(core)==profile['approved_nonreview_document_sha256']
    return valid,{'original_pending_consent_consumed':moved,
        'exact_history_move_valid':bool(moved),'all_other_nonreview_document_exact':valid}

def control_valid(data,p):
    controls={k:data.get(k)for k in p['approved_audio_controls']};old=copy.deepcopy(controls)
    try:old['分段增益dB']['S11']['1']=-1.
    except (KeyError,TypeError):return False
    return controls==p['approved_audio_controls']and old==p['original_audio_controls']and data['分段增益dB']['S11']['1']==1.0

def nonclipped(audio):
    return bool(len(audio)>0 and np.isfinite(audio).all()and np.max(np.abs(audio))<1.)

def support_valid(raw,p):
    return all(hashlib.sha256(raw[a:b].tobytes()).hexdigest()==row['PCM16_sample_bytes_sha256']
        for row in p['raw_outside_changed_support']for a,b in [row['sample_span_24k']])

def numeric_selftest(p,actual,raw_sha,raw,new_audio):
    wrong=copy.deepcopy(actual);wrong['分段增益dB']['S11']['1']=-1.
    changed=raw.copy();changed[100]^=1
    clipped=new_audio.copy();clipped[min(len(clipped)-1,round(102.9*SR))]=1.
    return {'actual_candidate_positive_passed':bool(control_valid(actual,p)and support_valid(raw,p)and nonclipped(new_audio)and raw_sha==p['fingerprints']['actual_raw_WAV_sha256']),
        'wrong_source_control_rejected':not control_valid(wrong,p),'actual_one_sample_outside_target_mutation_rejected':not support_valid(changed,p),
        'actual_target_clipping_mutation_rejected':not nonclipped(clipped),'mutated_audio_not_written':True,'native_ASR_not_simulated':True}

@contextlib.contextmanager
def directory(path):
    before=Path.cwd();os.chdir(path)
    try:yield
    finally:os.chdir(before)
def audit(args):
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    checks=[]
    report=dict(article='60',kind='controlled_audio_repair',passed=False,repair_applied=False,
        diagnostic_only=bool(args.diagnostic),production_delivery_eligible=False,
        official_full_gates_are_separate_required_precondition=True,
        official_gates_replaced_or_thresholds_modified=False,subjective_listening_claimed=False,
        private_caches_GT_or_PCM_exported=False,program_sha256=sha(__file__))
    def add(name,passed,**kw):checks.append(dict(name=name,passed=bool(passed),**safe(kw)))
    try:
        profile_path=Path(args.reference or HERE/'audio60-controlled-qc-reference.json')
        p=json.loads(profile_path.read_text());report['reference_file_sha256']=sha(profile_path)
        assert args.article==p['article']=='60'and p.get('enabled')is True
        assert p['review_only_top_level_keys']==['核对确认','区间声音指纹']
        utility=Path(args.numeric_utilities or HERE/'audio-qc.py')
        assert sha(utility)==p['numeric_utilities_sha256'],'Pinned numeric utilities changed.'
        U=module('source60_pinned_numeric_utilities',utility)
        request=Path(args.request).resolve();work=Path(args.work).resolve()
        reqpath=request/'视频/脚本/60.json';genpath=request/'视频/工具/初稿生成/gen60.py'
        actualpath=Path(args.actual_source or work/'scripts/60.json')
        rawpath=Path(args.raw_pcm or work/'work_60/a.wav')
        requested=json.loads(reqpath.read_text());actual=json.loads(actualpath.read_text())
        oldaac=aac(args.accepted_source);newaac=aac(args.canonical_video)
        fingerprints=dict(request_source_sha256=sha(reqpath),request_generator_sha256=sha(genpath),
            actual_full_source_sha256=sha(actualpath),actual_raw_WAV_sha256=sha(rawpath),
            accepted_video_sha256=sha(args.accepted_source),canonical_video_sha256=sha(args.canonical_video),
            accepted_AAC_ADTS_sha256=hashlib.sha256(oldaac).hexdigest(),
            canonical_AAC_ADTS_sha256=hashlib.sha256(newaac).hexdigest())
        report.update(fingerprints=fingerprints,source_current_sha256=fingerprints['actual_full_source_sha256'],
            accepted_sha256=fingerprints['accepted_video_sha256'],canonical_sha256=fingerprints['canonical_video_sha256'],
            source_authorization_ids=p['source_authorization_ids'])
        for key,want in p['fingerprints'].items():add('exact-approved-fingerprint:'+key,fingerprints[key]==want,actual=fingerprints[key],expected=want)
        for label,data in [('requested',requested),('actual',actual)]:
            core={k:v for k,v in data.items()if k not in p['review_only_top_level_keys']}
            if label=='actual':
                valid,consent_evidence=actual_nonreview_binding(actual,requested,p)
                add(label+'-entire-nonreview-source',valid,**consent_evidence)
            else:add(label+'-entire-nonreview-source',canonical(core)==p['approved_nonreview_document_sha256'])
            add(label+'-exact-sole-S11-gain-plus2-control',control_valid(data,p))
            add(label+'-all-original-spoken-English-preserved',canonical(spoken(data))==p['spoken_title_and_sentences_sha256'])
        if not all(x['passed']for x in checks):raise ValueError('Exact source/raw/AAC binding failed; audio measurements cannot excuse it.')
        if not args.diagnostic:
            statuspath=Path(args.official_status or output.parent/'60-status.json')
            status=json.loads(statuspath.read_text())
            add('unchanged-official-native-pipeline-already-passed',
                status.get('canonical_pipeline_passed')is True and
                status.get('canonical_video_sha256')==fingerprints['canonical_video_sha256']and
                status.get('canonical_aac_adts_sha256')==fingerprints['canonical_AAC_ADTS_sha256']and
                status.get('final_wav_sha256')==fingerprints['actual_raw_WAV_sha256'],
                actual_status_file_sha256=sha(statuspath),ASR_not_replaced_by_this_helper=True)
            if not checks[-1]['passed']:raise ValueError('Actual original native gates/status not bound first.')
        with wave.open(str(rawpath),'rb')as wav:
            shape=dict(rate=wav.getframerate(),channels=wav.getnchannels(),width=wav.getsampwidth(),samples=wav.getnframes())
            raw=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2')
        add('exact-original-PCM16-shape-and-duration',shape==p['raw_WAV_shape'],actual=shape)
        for row in p['raw_outside_changed_support']+p['unchanged_title_and_other_14_sentences']+[p['S11_remaining_two_segments']]:
            lo,hi=row['sample_span_24k'];digest=hashlib.sha256(raw[lo:hi].tobytes()).hexdigest()
            add('native-raw-sample-exact:'+row.get('sentence',row.get('name','S11-other-pieces')),
                digest==row['PCM16_sample_bytes_sha256'],sample_span_24k=[lo,hi],actual_sha256=digest)
        info=json.loads(capture(['ffprobe','-v','error','-show_streams','-of','json',args.canonical_video]))
        audio=[s for s in info['streams']if s['codec_type']=='audio'];video=[s for s in info['streams']if s['codec_type']=='video']
        add('original-audio-codec-clock',len(audio)==1 and audio[0]['codec_name']=='aac'and
            int(audio[0]['sample_rate'])==48000 and int(audio[0]['channels'])==1)
        if not args.diagnostic:add('actual-canonical-4K-present',len(video)==1 and(video[0]['width'],video[0]['height'])==(3840,2160))
        op,npk=adts_packets(oldaac),adts_packets(newaac)
        changed=[i for i,(a,b)in enumerate(zip(op,npk))if a!=b]
        add('exact-AAC-packet-locality-and-all-other-packets-preserved',
            len(op)==len(npk)==p['AAC_packet_count']and changed==p['changed_AAC_packet_indices_0_based'],
            old_packet_count=len(op),new_packet_count=len(npk),changed_packet_indices_0_based=changed)
        old,new=U.decode(args.accepted_source),U.decode(args.canonical_video)
        add('decoded-sample-clock-and-duration-preserved',len(old)==len(new)==p['public_decoded_samples_total'])
        add('actual-no-clipping-or-nonfinite',nonclipped(new),sample_peak_dbfs=float(20*np.log10(np.max(abs(new))+1e-30)))
        lo,hi=[round(x*SR)for x in p['public_decoded_change_support_s']]
        add('decoded-all-samples-before-and-after-codec-context-exact',
            np.array_equal(old[:lo],new[:lo])and np.array_equal(old[hi:],new[hi:]),
            measured_context_s=p['public_decoded_change_support_s'])
        measured=np.flatnonzero(old!=new)
        actual_support=[measured[0]/SR,(measured[-1]+1)/SR]if len(measured)else None
        add('actual-decoded-change-support-bound-to-approved-measurement',actual_support==p['public_decoded_change_support_s'],actual=actual_support)
        omt,og,olog=U.r128(args.accepted_source);nmt,ng,nlog=U.r128(args.canonical_video)
        (output.parent/'60-controlled-accepted-r128.log').write_text(olog)
        (output.parent/'60-controlled-actual-r128.log').write_text(nlog)
        report.update(accepted_global=og,actual_global=ng)
        add('actual-true-peak-below-zero',ng['true_peak_dbtp']<0,actual_dbtp=ng['true_peak_dbtp'])
        add('whole-track-original-level-preserved',abs(ng['integrated_lufs']-og['integrated_lufs'])<=p['original_thresholds']['whole_track_delta_LU'],delta_lu=ng['integrated_lufs']-og['integrated_lufs'])
        tools=Path(args.tools or HERE.parents[1]/'视频/工具').resolve()
        for name,want in p['original_tool_sha256'].items():assert sha(tools/name)==want,'Original tool changed: '+name
        sys.path.insert(0,str(tools));R=module('响度一致性核对',tools/'响度一致性核对.py');R.FF='ffmpeg'
        Q=module('source60_unchanged_original_health',tools/'音频体检.py')
        with directory(work):
            samples=R.pcm(str(Path(args.canonical_video).resolve()));moments=R.momentary(str(Path(args.canonical_video).resolve()))
            metrics=Q.指标(samples,'60');baseline=json.loads((tools/'音频体检基准.json').read_text());notes=[]
            bad=Q.超限(metrics,baseline,Q.确认('60'),notes);I,segs,levels,rbad,summary=R.check(str(Path(args.canonical_video).resolve()),samples)
        add('all-eight-unchanged-original-health-rules',not bad,metrics=metrics,failures=bad,original_confirmation_notes=notes)
        add('unchanged-original-whole-sentence-R-rule',not rbad,failures=rbad,summary=summary)
        segments=Q.句段(samples);add('independent-title-and-all15-body-sentences-mapped',len(segments)==16)
        with tempfile.TemporaryDirectory(prefix='source60-original-timings-')as td:
            segmentfile=Path(td)/'work_60/分段.json';segmentfile.parent.mkdir()
            segmentfile.write_text(json.dumps({f'S{i}':[{'时刻':[a/SR,b/SR]}]for i,(a,b)in enumerate(segments[1:],1)}))
            inside=R.句内(str(Path(args.canonical_video).resolve()),samples,moments,str(segmentfile));ibad=R.句内报(inside)
        add('unchanged-original-within-sentence-R-rule',not ibad,failures=ibad,comparisons=inside)
        report['original_full_track_supplement']=dict(metrics=metrics,global_lufs=I,sentence_lufs=levels,summary=summary,
            suppressed_segment_rule_not_added=True,official_ASR_and_original_gates_separate=True)
        groups=json.loads((work/'work_60/分段.json').read_text())['S11'];want=p['approved_S11_producer_group_metadata'];tol=p['group_time_tolerance_s']
        metadata=(len(groups)==len(want)and all(a['段']==b['段']and float(a['增益'])==float(b['增益'])and a['停顿']==b['停顿']and
            all(abs(x-y)<=tol for x,y in zip(a['时刻'],b['时刻']))for a,b in zip(groups,want)))
        add('S11-real-producer-sole-gain-times-and-original-pauses',metadata,actual=groups,expected=want,tolerance_s=tol)
        report['approved_audio_repair_scope']=dict(source_control_leaf=p['source_control_leaf'],target_span_s=p['target_source_span_s'],
            unchanged_title_and_other_14_sentences=True,S11_other_two_punctuation_pieces_unchanged=True,ASR_confirmations_not_renewed_by_this_helper=True)
        pitch={}
        for row in p['sentence_spans_s']:
            a,b=[round(x*SR)for x in row['span_s']];ok,values=U.pitch_preservation(old[a:b],new[a:b]);pitch[row['sentence']]=values
            add('original-pitch-preserved:'+row['sentence'],ok,**values)
        report['pitch_comparison']=pitch
        a,b=[round(x*SR)for x in p['target_source_span_s']];ok,pitchrow=U.pitch_preservation(old[a:b],new[a:b]);add('target-phrase-original-pitch-preserved',ok,**pitchrow)
        fit=U.fit(old[a:b],new[a:b]);limits=p['original_thresholds']
        add('actual-target-gain-and-preserved-voice-shape',abs(fit['gain_db']-2.)<=limits['gain_tolerance_dB']and fit['correlation']>=limits['gain_fit_minimum_correlation']and fit['gain_compensated_residual_snr_db']>=limits['gain_compensated_minimum_SNR_dB'],**fit)
        report['target_before']=U.measure(old,p['target_source_span_s'],omt);report['target_after']=U.measure(new,p['target_source_span_s'],nmt)
        selftest=numeric_selftest(p,actual,fingerprints['actual_raw_WAV_sha256'],raw,new)
        add('real-candidate-positive-and-local-mutation-negatives',all(v for k,v in selftest.items()if k not in('mutated_audio_not_written','native_ASR_not_simulated')),**selftest)
        report['passed']=bool(checks)and all(x['passed']for x in checks)
        report['repair_applied']=report['passed'];report['production_delivery_eligible']=report['passed']and not args.diagnostic
    except BaseException as exc:report['error']=dict(type=type(exc).__name__,detail=str(exc))
    report['checks']=checks;output.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n')
    return 0 if report['passed']else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--article',default='60')
    for name in ['accepted-source','canonical-video','work','request','output']:parser.add_argument('--'+name,required=True)
    for name in ['actual-source','raw-pcm','tools','reference','numeric-utilities','official-status']:parser.add_argument('--'+name)
    parser.add_argument('--diagnostic',action='store_true');sys.exit(audit(parser.parse_args()))
