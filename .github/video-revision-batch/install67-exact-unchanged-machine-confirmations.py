#!/usr/bin/env python3
"""Root-approved transfer of six unchanged source67 machine-ASR notes.

Runtime W only. Every old/new WAV, AAC and full sentence crop must be exact.
This does not run or replace ASR, change voice, or apply to changed S9.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import wave

HERE=Path(__file__).resolve().parent
APPROVED=('S1','S3','S4','S6','S15','S17')

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def canonical(data):
    return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def aac_sha(path):
    raw=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(path),'-map','0:a:0','-c:a','copy','-f','adts','-'])
    return hashlib.sha256(raw).hexdigest()

def read_PCM(path):
    with wave.open(str(path),'rb')as f:
        shape=dict(rate=f.getframerate(),channels=f.getnchannels(),width=f.getsampwidth(),samples=f.getnframes())
        data=f.readframes(f.getnframes())
    return shape,data

def exact_sentence(old,new,row):
    lo,hi=row['sample_span_24k'];a=old[lo*2:hi*2];b=new[lo*2:hi*2]
    wanted=row['PCM16_sample_bytes_sha256']
    assert a==b and len(a)==2*row['sample_count'],'Whole sentence samples changed: '+row['sentence']
    ah,bh=hashlib.sha256(a).hexdigest(),hashlib.sha256(b).hexdigest()
    assert ah==bh==wanted,'Whole sentence crop identity differs: '+row['sentence']
    return dict(sentence=row['sentence'],sample_span_24k=[lo,hi],sample_count=len(a)//2,
        old_PCM16_sha256=ah,new_PCM16_sha256=bh,whole_sentence_sample_exact=True,different_samples=0)

def install(args):
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    report=dict(article='67',kind='root-approved-six-specific-unchanged-sentence-machine-ASR-confirmation-transfer',
        runtime_confirmation_transfer_applied=False,quality_acceptance=False,
        original_ASR_models_comparison_rules_thresholds_and_selftests_unchanged=True,
        new_ASR_results_or_human_listening_not_claimed=True,program_sha256=sha(__file__),
        no_TTS_audio_or_cache_mutation=True)
    try:
        refpath=Path(args.reference or HERE/'install67-exact-unchanged-machine-confirmations-reference.json')
        ref=json.loads(refpath.read_text());report['reference_sha256']=sha(refpath)
        assert ref['article']=='67'and tuple(ref['approved_sentences'])==APPROVED
        assert ref['proposal_sha256']=='ff49e6d2a23d07127ef423259e21c1c526195ae60a1e6032aa1b0bc24b4ddb74'
        assert ref['authorization_kind']=='root-implementation-decision-after-review-not-user-verbatim'
        work=Path(args.work).resolve();actualpath=work/'scripts/67.json'
        requestpath=Path(args.request).resolve()/'视频/脚本/67.json';oldsource=Path(args.old_source).resolve()
        assert actualpath.resolve()!=requestpath.resolve(),'Runtime actual source must be separate from request.'
        oldwav=Path(args.old_wav).resolve();newwav=work/'work_67/a.wav'
        actual=json.loads(actualpath.read_text());request=json.loads(requestpath.read_text());old=json.loads(oldsource.read_text())
        assert sha(requestpath)==ref['request_source_sha256']and sha(oldsource)==ref['old_source_sha256']
        assert sha(oldwav)==ref['old_WAV_sha256']and sha(newwav)==ref['new_WAV_sha256']
        assert hashlib.md5(oldwav.read_bytes()).hexdigest()[:12]==ref['old_PCM_MD5_first12']
        assert hashlib.md5(newwav.read_bytes()).hexdigest()[:12]==ref['new_PCM_MD5_first12']
        oldaac,newaac=aac_sha(args.old_audio),aac_sha(args.actual_audio)
        assert oldaac==ref['old_AAC_sha256']and newaac==ref['new_AAC_sha256']
        baseline=json.loads(Path(args.baseline_proof).read_text())
        assert baseline['old_source_sha256']==ref['old_source_sha256']
        assert baseline['actual_old_pcm_sha256']==ref['old_WAV_sha256']
        assert baseline['old_reconstructed_aac_adts_sha256']==ref['old_AAC_sha256']
        assert baseline['old_pcm_matches_independently_bound_reference']is True
        assert baseline['old_reconstructed_aac_exactly_matches_prior_public_native']is True
        # This reference is the real prior-public native render, which is not
        # the legacy accepted comparison voice. Preserve that distinction.
        report['actual_prior_public_native_double_hash_binding']=dict(
            old_WAV_sha256=sha(oldwav),old_AAC_sha256=oldaac,
            new_WAV_sha256=sha(newwav),new_AAC_sha256=newaac,
            prior_public_native_bound=True,
            original_legacy_accepted_voice_match=baseline.get('old_reconstructed_aac_exactly_matches_accepted'))
        helper=HERE/'audio67-controlled-qc.py';profilepath=HERE/'audio67-controlled-qc-reference.json'
        assert sha(helper)==ref['controlled_helper_sha256']and sha(profilepath)==ref['controlled_reference_sha256']
        spec=importlib.util.spec_from_file_location('root67_exact_controlled_binding',helper)
        mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
        profile=json.loads(profilepath.read_text())['profiles']['67']
        accepted,details=mod.original_consent_actual_binding(actual,request,profile)
        assert accepted,'Actual nonreview source not exactly the approved request/original G35/consent variant.'
        assert {k:actual.get(k)for k in profile['approved_audio_controls']}==profile['approved_audio_controls']
        oldshape,oldpcm=read_PCM(oldwav);newshape,newpcm=read_PCM(newwav)
        assert oldshape==newshape==ref['WAV_shape']
        rows=[exact_sentence(oldpcm,newpcm,row)for row in ref['sentences']]
        assert tuple(row['sentence']for row in rows)==APPROVED and 'S9'not in APPROVED
        current_CF=actual.get('核对确认',{}).get('机器复听',{})
        original_CF=old.get('核对确认',{}).get('机器复听',{})
        changed=copy.deepcopy(actual);target=changed['核对确认']['机器复听'];states=[]
        for row in ref['sentences']:
            name=row['sentence'];expected=row['old_confirmation']
            assert original_CF.get(name)==expected and canonical(expected)==row['old_confirmation_canonical_sha256']
            assert expected['配音指纹']==ref['old_PCM_MD5_first12']and len(str(expected.get('依据','')))>=20
            si=int(name[1:])-1
            assert actual['sentences'][si]['chunks']==request['sentences'][si]['chunks']
            assert ' '.join(c['en']for c in actual['sentences'][si]['chunks'])==row['script_English']
            proposed={**expected,'配音指纹':ref['new_PCM_MD5_first12'],
                '依据':expected['依据']+row['exact_sample_inheritance_note']}
            assert current_CF.get(name)in(expected,proposed),'Unexpected current machine CF: '+name
            target[name]=proposed;states.append(dict(sentence=name,old_confirmation_preserved=expected,
                new_confirmation=proposed,already_exactly_installed=current_CF.get(name)==proposed))
        other={k:v for k,v in current_CF.items()if k not in APPROVED}
        assert {k:v for k,v in target.items()if k not in APPROVED}==other
        assert target.get('S9')==current_CF.get('S9'),'Changed S9 cannot be renewed.'
        before=copy.deepcopy(actual);after=copy.deepcopy(changed)
        for doc in(before,after):
            for key in APPROVED:doc['核对确认']['机器复听'].pop(key)
        assert before==after,'A change escaped the six approved machine confirmation entries.'
        assert {k:v for k,v in actual.items()if k!='核对确认'}=={k:v for k,v in changed.items()if k!='核对确认'}
        report.update(whole_sentence_comparisons=rows,actual_nonreview_binding=details,
            six_specific_confirmation_changes=states,S9_confirmation_unchanged=True,
            all_other_source_fields_exact=True,actual_source_sha256_before=sha(actualpath),
            only_runtime_confirmation_metadata_changed=True)
        if not args.diagnostic:
            assert args.write_runtime,'Explicit runtime-write mode required.'
            temporary=actualpath.with_name(actualpath.name+'.specific67-ASR-tmp')
            temporary.write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n')
            os.replace(temporary,actualpath)
            assert json.loads(actualpath.read_text())==changed
            report['runtime_confirmation_transfer_applied']=True
        report['actual_source_sha256_after']=sha(actualpath)
        assert sha(requestpath)==ref['request_source_sha256']and sha(oldsource)==ref['old_source_sha256']
        assert sha(oldwav)==ref['old_WAV_sha256']and sha(newwav)==ref['new_WAV_sha256']
        report.update(passed=True,diagnostic_only=bool(args.diagnostic),request_and_audio_unchanged=True,
            raw_ASR_differences_not_erased_from_original_failed_records=True)
    except BaseException as exc:report.update(passed=False,error=dict(type=type(exc).__name__,detail=str(exc)))
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return 0 if report.get('passed')else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['work','request','old-source','old-wav','old-audio','actual-audio','baseline-proof','output']:
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--reference');parser.add_argument('--write-runtime',action='store_true')
    parser.add_argument('--diagnostic',action='store_true');sys.exit(install(parser.parse_args()))
