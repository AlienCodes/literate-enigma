#!/usr/bin/env python3
"""Install only root-selected source18 metadata after exact actual voice binding.

The nine deletion-region comparisons are pinned prior real measurements. This
does not repeat them or claim listening, and never writes request/audio files.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def canonical(doc):
    return hashlib.sha256(json.dumps(doc,ensure_ascii=False,sort_keys=True,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()

def require(ok, message):
    if not ok:
        raise AssertionError(message)

def aac_sha(path):
    p = subprocess.Popen(['ffmpeg','-v','error','-nostdin','-i',str(path),
        '-map','0:a:0','-c:a','copy','-f','adts','-'],stdout=subprocess.PIPE)
    h = hashlib.sha256()
    for b in iter(lambda:p.stdout.read(1048576), b''):
        h.update(b)
    require(p.wait()==0,'AAC extraction failed')
    return h.hexdigest()

def clock(path):
    out = subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0',
        '-show_streams','-show_packets','-of','json',str(path)])
    d = json.loads(out)
    require(len(d['streams'])==1,'Exactly one audio stream required')
    stream_keys=('codec_name','codec_type','sample_rate','channels','channel_layout',
        'time_base','start_pts','start_time','duration_ts','duration','extradata_size')
    packet_keys=('pts','pts_time','dts','dts_time','duration','duration_time','size','flags','side_data_list')
    projection={'stream':{k:d['streams'][0][k] for k in stream_keys if k in d['streams'][0]},
        'packets':[{k:p[k] for k in packet_keys if k in p} for p in d['packets']]}
    return len(d['packets']),canonical(projection)

def without_targets(doc, ref):
    result = copy.deepcopy(doc)
    for row in ref['nine']:
        result['核对确认']['删除段'][row['key']].pop('配音指纹',None)
    result['核对确认']['响度骤降'].pop(ref['one']['key'],None)
    # Only the two exact observed complete G35 notes; no whitespace/general note waiver.
    note = result['sentences'][15]['chunks'][1]['note']
    pair = ref['exact_original_G35_last_note_variants']
    require(note in (pair['request_before_G35'], pair['actual_failed_after_G35']),
        'Last note is not either exact observed original G35 stage')
    result['sentences'][15]['chunks'][1]['note'] = pair['actual_failed_after_G35']
    return result

def install(args):
    output = Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    report={'article':'18','kind':'specific-nine-existing-FP-and-one-objective-word-basis-correction',
        'program_sha256':sha(__file__),'quality_acceptance':False,'review_only':True,
        'new_human_listening_or_ASR_transcript_claimed':False,
        'prior_GT_comparisons_not_claimed_reexecuted':True,'PV_changes':[],
        'runtime_metadata_applied':False,'no_TTS_or_audio_core_threshold_mutation':True}
    try:
        refpath = Path(args.reference or HERE/'install18-specific-nine-and-one-reference.json')
        ref = json.loads(refpath.read_text())
        require(ref['article']=='18' and len(ref['nine'])==9,'Wrong exact scope')
        require(ref['root_decision_sha256']=='c70db70f96af4d8ee7c0efc6fced36e5fdc40b3b69b44cfd9df4a6cb0858cb15','Wrong root selection')
        require(ref['nine_proposal_sha256']=='2709d7cccae41ffdb854a1007360e9e28ab64b5b7d2032b243814925a968843e','Wrong nine proposal')
        require(ref['one_proposal_sha256']=='89504f9e6a7b5525c0f71f5375193b8f7f443f473bf2cf2ddce7134d97d62044','Wrong separate correction')
        request = Path(args.request).resolve(); work = Path(args.work).resolve()
        req = request/'视频/脚本/18.json'; actual = work/'scripts/18.json'; wav = work/'work_18/a.wav'
        require(req.resolve()!=actual.resolve(),'Cannot write immutable request')
        require(sha(req)==ref['request_sha256'],'Request source changed')
        require(sha(request/'视频/工具/初稿生成/gen18.py')==ref['GEN_sha256'],'GEN changed')
        require(sha(wav)==ref['actual_WAV_sha256'],'Current whole PCM changed')
        require(hashlib.md5(wav.read_bytes()).hexdigest()[:12]==ref['actual_fingerprint'],'Current fingerprint changed')
        aa=aac_sha(args.actual_audio); oldaac=aac_sha(args.accepted_source)
        require(aa==ref['actual_AAC_sha256'],'Current whole AAC changed')
        require(oldaac==ref['legacy_accepted_AAC_sha256'],'Must use genuine legacy accepted AAC, not prior3p5')
        count,projection=clock(args.actual_audio)
        require(count==ref['actual_packet_count'] and projection==ref['actual_clock_projection_sha256'],'Current absolute audio clock changed')
        for pin in ref['evidence']:
            ep=HERE/pin['file'];require(sha(ep)==pin['sha256'],'Pinned actual prior evidence changed: '+pin['file'])
        doc=json.loads(actual.read_text())
        outside_hash=canonical(without_targets(doc,ref))
        allowed_stages={ref['outside_ten_target_fields_canonical_sha256']:'observed-post-draft',
            ref['exact_original_pre_draft_stage']['outside_ten_target_fields_canonical_sha256']:'original-pre-draft-mapper-replay'}
        report.update(actual_source_sha256_before=sha(actual),actual_outside_target_canonical_sha256=outside_hash,
            exact_original_stage_binding=allowed_stages.get(outside_hash))
        require(outside_hash in allowed_stages,
            'Actual source is not either complete exact original stage; no PV or field may be ignored')
        revised=copy.deepcopy(doc)
        changes=[]
        for row in ref['nine']:
            before=doc['核对确认']['删除段'][row['key']]
            require(before in (row['before'],row['after']),'Nine-entry type, basis or fingerprint mismatch: '+row['key'])
            require({k:v for k,v in row['before'].items() if k!='配音指纹'}==
                {k:v for k,v in row['after'].items() if k!='配音指纹'},'Nine-entry basis mutation forbidden')
            revised['核对确认']['删除段'][row['key']]=copy.deepcopy(row['after'])
            changes.append({'category':'删除段','key':row['key'],'only_fingerprint_changed':True})
        one=ref['one'];prior=doc['核对确认']['响度骤降'][one['key']]
        require(prior in (one['before'],one['after']),'Separate loudness entry differs')
        require(one['before']['低']==one['after']['低']==6.3,'Original depth6.3 must remain')
        revised['核对确认']['响度骤降'][one['key']]=copy.deepcopy(one['after'])
        require(without_targets(doc,ref)==without_targets(revised,ref),'Change escaped selected metadata')
        require(revised['核对确认']['非人声']==doc['核对确认']['非人声'],'PV changes forbidden')
        report.update(reference_sha256=sha(refpath),actual_WAV_sha256=sha(wav),
            actual_AAC_sha256=aa,legacy_accepted_AAC_sha256=oldaac,
            actual_packet_count=count,actual_clock_projection_sha256=projection,
            nine_selected_changes=changes,additional_objective_correction=one,
            historical_wrong_dormant_basis_explicitly_rejected=True,
            all_other_source_fields_exact=True,actual_source_sha256_before=sha(actual),
            original_numeric_6p3_plus_point3_and_all_original_quality_gates_unchanged=True)
        if not args.diagnostic:
            require(args.write_runtime,'Explicit --write-runtime required')
            temp=actual.with_name(actual.name+'.specific18-metadata-tmp')
            temp.write_text(json.dumps(revised,ensure_ascii=False,indent=2)+'\n')
            os.replace(temp,actual)
            require(json.loads(actual.read_text())==revised,'Runtime write readback differs')
            report['runtime_metadata_applied']=True
        require(sha(req)==ref['request_sha256'] and sha(wav)==ref['actual_WAV_sha256'],
            'Immutable source or audio changed')
        report.update(passed=True,diagnostic_only=bool(args.diagnostic),
            actual_source_sha256_after=sha(actual),full_native_acceptance_not_granted=True)
    except BaseException as exc:
        report.update(passed=False,error={'type':type(exc).__name__,'detail':str(exc)})
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return 0 if report.get('passed') else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('work','request','actual-audio','accepted-source','output'):
        p.add_argument('--'+k,required=True)
    p.add_argument('--reference');p.add_argument('--write-runtime',action='store_true')
    p.add_argument('--diagnostic',action='store_true');sys.exit(install(p.parse_args()))
