#!/usr/bin/env python3
"""Exact source62 approved 96-sample pause-boundary repair supplement.

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
AUTH_RECORDS={'049':'14a3dcb5cad24d463eb3643c3e8d64e54c8b925591ad61aaecc2380b95be08e1',
    '051':'4bcae46b68b9584f107966f683af580b474fa9835f101834fe55ed6968dfc36b',
    '052':'767aeeb3159afe9c74399844b9a6688c2c474dc68f0456547aaea8f92c2a7b7f'}

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

def control_valid(data,profile):
    controls={k:data.get(k)for k in profile['approved_audio_controls']}
    changed=copy.deepcopy(controls)
    try:changed['停顿插入点']['S15']['2'][0]=profile['source_control_leaf']['old_JSON_numeric_literal']
    except (KeyError,TypeError,IndexError):return False
    point=data['停顿插入点']['S15']['2']
    leaf=profile['source_control_leaf']
    return (controls==profile['approved_audio_controls'] and changed==profile['original_audio_controls']
        and point==[leaf['new_JSON_numeric_literal'],'交界']
        and round(point[0]*24000)==leaf['new_sample_round_24k']
        and leaf['new_sample_round_24k']-leaf['old_sample_round_24k']==96
        and leaf['samples_deleted']==0 and leaf['pause_samples']==9600)

def nonclipped(audio):
    return bool(len(audio)>0 and np.isfinite(audio).all() and np.max(np.abs(audio))<1.)

def numeric_selftest(profile,actual,raw_sha,new_audio):
    good=(control_valid(actual,profile) and raw_sha==profile['fingerprints']['actual_raw_WAV_sha256']
          and nonclipped(new_audio))
    wrong=copy.deepcopy(actual);wrong['停顿插入点']['S15']['2'][0]=3.587667
    clipped=np.asarray(new_audio).copy();clipped[min(len(clipped)-1,round(113.86*SR))]=1.
    return {'actual_candidate_positive_passed':bool(good),
        'wrong_3_587667_control_rejected':not control_valid(wrong,profile),
        'wrong_raw_fingerprint_rejected':('0'*64!=profile['fingerprints']['actual_raw_WAV_sha256']),
        'actual_local_clipping_mutation_rejected':not nonclipped(clipped),
        'mutated_audio_not_written':True,'native_ASR_not_simulated':True}

@contextlib.contextmanager
def directory(path):
    before=Path.cwd();os.chdir(path)
    try:yield
    finally:os.chdir(before)

def audit(args):
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    checks=[]
    report=dict(article='62',kind='controlled_audio_repair',passed=False,repair_applied=False,
        diagnostic_only=bool(args.diagnostic),production_delivery_eligible=False,
        official_full_gates_are_separate_required_precondition=True,
        official_gates_replaced_or_thresholds_modified=False,subjective_listening_claimed=False,
        private_caches_GT_or_PCM_exported=False,program_sha256=sha(__file__))
    def add(name,passed,**kw):checks.append(dict(name=name,passed=bool(passed),**safe(kw)))
    try:
        profile_path=Path(args.reference or HERE/'audio62-controlled-qc-reference.json')
        p=json.loads(profile_path.read_text());report['reference_file_sha256']=sha(profile_path)
        assert args.article==p['article']=='62'and p.get('enabled')is True
        assert p['source_authorization_ids']==['049','051','052']
        assert {row['id']:row['sha256']for row in p['source_authorization_records']}==AUTH_RECORDS
        assert p['review_only_top_level_keys']==['核对确认','区间声音指纹']
        utility=Path(args.numeric_utilities or HERE/'audio-qc.py')
        assert sha(utility)==p['numeric_utilities_sha256'],'Pinned numeric utilities changed.'
        U=module('source62_pinned_numeric_utilities',utility)
        request=Path(args.request).resolve();work=Path(args.work).resolve()
        reqpath=request/'视频/脚本/62.json';genpath=request/'视频/工具/初稿生成/gen62.py'
        actualpath=Path(args.actual_source or work/'scripts/62.json')
        rawpath=Path(args.raw_pcm or work/'work_62/a.wav')
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
            add(label+'-exact-one-96sample-insertion-control',control_valid(data,p))
            add(label+'-all-original-spoken-English-preserved',canonical(spoken(data))==p['spoken_title_and_sentences_sha256'])
        if not all(x['passed']for x in checks):raise ValueError('Exact source/raw/AAC binding failed; audio measurements cannot excuse it.')
        if not args.diagnostic:
            statuspath=Path(args.official_status or output.parent/'62-status.json')
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
        for row in p['raw_outside_changed_support']+p['unchanged_title_and_other_18_sentences']+[p['raw_four_vowel']]:
            lo,hi=row['sample_span_24k'];digest=hashlib.sha256(raw[lo:hi].tobytes()).hexdigest()
            add('native-raw-sample-exact:'+row.get('sentence',row.get('name','four-vowel')),
                digest==row['PCM16_sample_bytes_sha256'],sample_span_24k=[lo,hi],actual_sha256=digest)
        info=json.loads(capture(['ffprobe','-v','error','-show_streams','-of','json',args.canonical_video]))
        audio=[s for s in info['streams']if s['codec_type']=='audio'];video=[s for s in info['streams']if s['codec_type']=='video']
        add('original-audio-codec-clock',len(audio)==1 and audio[0]['codec_name']=='aac'and
            int(audio[0]['sample_rate'])==48000 and int(audio[0]['channels'])==1)
        if not args.diagnostic:add('actual-canonical-4K-present',len(video)==1 and(video[0]['width'],video[0]['height'])==(3840,2160))
        op,npk=adts_packets(oldaac),adts_packets(newaac)
        changed=[i for i,(a,b)in enumerate(zip(op,npk))if a!=b]
        add('exact-37-AAC-packet-locality-and-all-other-packets-preserved',
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
        (output.parent/'62-controlled-accepted-r128.log').write_text(olog)
        (output.parent/'62-controlled-actual-r128.log').write_text(nlog)
        report.update(accepted_global=og,actual_global=ng)
        add('actual-true-peak-below-zero',ng['true_peak_dbtp']<0,actual_dbtp=ng['true_peak_dbtp'])
        add('whole-track-original-level-preserved',abs(ng['integrated_lufs']-og['integrated_lufs'])<=p['original_thresholds']['whole_track_delta_LU'],delta_lu=ng['integrated_lufs']-og['integrated_lufs'])
        tools=Path(args.tools or HERE.parents[1]/'视频/工具').resolve()
        for name,want in p['original_tool_sha256'].items():assert sha(tools/name)==want,'Original tool changed: '+name
        sys.path.insert(0,str(tools));R=module('响度一致性核对',tools/'响度一致性核对.py');R.FF='ffmpeg'
        Q=module('source62_unchanged_original_health',tools/'音频体检.py')
        with directory(work):
            samples=R.pcm(str(Path(args.canonical_video).resolve()));moments=R.momentary(str(Path(args.canonical_video).resolve()))
            metrics=Q.指标(samples,'62');baseline=json.loads((tools/'音频体检基准.json').read_text());notes=[]
            bad=Q.超限(metrics,baseline,Q.确认('62'),notes);I,segs,levels,rbad,summary=R.check(str(Path(args.canonical_video).resolve()),samples)
        add('all-eight-unchanged-original-health-rules',not bad,metrics=metrics,failures=bad,original_confirmation_notes=notes)
        add('unchanged-original-whole-sentence-R-rule',not rbad,failures=rbad,summary=summary)
        segments=Q.句段(samples);add('independent-title-and-all19-body-sentences-mapped',len(segments)==20)
        with tempfile.TemporaryDirectory(prefix='source62-original-timings-')as td:
            segmentfile=Path(td)/'work_62/分段.json';segmentfile.parent.mkdir()
            segmentfile.write_text(json.dumps({f'S{i}':[{'时刻':[a/SR,b/SR]}]for i,(a,b)in enumerate(segments[1:],1)}))
            inside=R.句内(str(Path(args.canonical_video).resolve()),samples,moments,str(segmentfile));ibad=R.句内报(inside)
        add('unchanged-original-within-sentence-R-rule',not ibad,failures=ibad,comparisons=inside)
        report['original_full_track_supplement']=dict(metrics=metrics,global_lufs=I,sentence_lufs=levels,summary=summary,
            suppressed_segment_rule_not_added=True,official_ASR_and_original_gates_separate=True)
        groups=json.loads((work/'work_62/分段.json').read_text())['S15'];want=p['approved_S15_producer_group_metadata'];tol=p['group_time_tolerance_s']
        metadata=(len(groups)==len(want)and all(a['段']==b['段']and float(a['增益'])==float(b['增益'])and a['停顿']==b['停顿']and
            all(abs(x-y)<=tol for x,y in zip(a['时刻'],b['时刻']))for a,b in zip(groups,want)))
        add('S15-real-producer-gains-times-and-standard-pauses',metadata,actual=groups,expected=want,tolerance_s=tol)
        pause=groups[2]['时刻'][0]-groups[1]['时刻'][1]
        add('S15-moved-insertion-boundary-0_4s-no-deletion',abs(pause-.4)<=2*tol,actual_pause_s=pause,deleted_mother_samples=0,
            raw_control_sample_move=96)
        import parselmouth
        pitch={}
        for name,start,end in [('title'if i==0 else'S'+str(i),a/SR,b/SR)for i,(a,b)in enumerate(segments)]:
            a,b=round(start*SR),round(end*SR);ok,row=U.pitch_preservation(old[a:b],new[a:b]);pitch[name]=row
            add('original-pitch-preserved:'+name,ok,**row)
        report['pitch_comparison']=pitch
        a,b=[round(x*SR)for x in p['F0_control_public_span_s']]
        f0=[parselmouth.Sound(v[a:b],sampling_frequency=SR).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=450).selected_array['frequency']for v in(old,new)]
        keep=(f0[0]>0)&(f0[1]>0);add('four-phrase-F0-clock-and-voicing-preserved',np.array_equal(f0[0]>0,f0[1]>0)and keep.sum()>10 and
            float(np.max(abs(f0[1][keep]-f0[0][keep])))<.1,voiced_pairs=int(keep.sum()),max_delta_Hz=float(np.max(abs(f0[1][keep]-f0[0][keep]))))
        selftest=numeric_selftest(p,actual,fingerprints['actual_raw_WAV_sha256'],new)
        add('real-candidate-positive-and-local-mutation-negatives',all(v for k,v in selftest.items()if k not in('mutated_audio_not_written','native_ASR_not_simulated')),**selftest)
        report['passed']=bool(checks)and all(x['passed']for x in checks)
        report['repair_applied']=report['passed'];report['production_delivery_eligible']=report['passed']and not args.diagnostic
    except BaseException as exc:report['error']=dict(type=type(exc).__name__,detail=str(exc))
    report['checks']=checks;output.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n')
    return 0 if report['passed']else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--article',default='62')
    for name in ['accepted-source','canonical-video','work','request','output']:parser.add_argument('--'+name,required=True)
    for name in ['actual-source','raw-pcm','tools','reference','numeric-utilities','official-status']:parser.add_argument('--'+name)
    parser.add_argument('--diagnostic',action='store_true');sys.exit(audit(parser.parse_args()))
