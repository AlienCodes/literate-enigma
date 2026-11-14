#!/usr/bin/env python3
"""Read-only whole-fingerprint inventory and exact old/current PCM evidence.

No acceptance, fingerprint renewal, GT reconstruction, or waveform export.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
import soundfile as sf


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprints(document):
    rows=[]
    for category, entries in document.get('核对确认',{}).items():
        if not isinstance(entries,dict):continue
        for key,value in entries.items():
            if isinstance(value,dict) and '配音指纹' in value:
                rows.append((category,key,value))
    return rows


def comparison(old,new,sr,old_span,new_span):
    a=old[round(old_span[0]*sr):round(old_span[1]*sr)]
    b=new[round(new_span[0]*sr):round(new_span[1]*sr)]
    result={'old_span_seconds':old_span,'actual_span_seconds':new_span,
            'old_sample_count':len(a),'actual_sample_count':len(b),'dtype':str(a.dtype),
            'old_decoded_pcm_sha256':hashlib.sha256(a.tobytes()).hexdigest(),
            'actual_decoded_pcm_sha256':hashlib.sha256(b.tobytes()).hexdigest(),
            'whole_crop_samples_identical':bool(len(a)>0 and np.array_equal(a,b))}
    if len(a)==len(b) and len(a):
        aa,bb=a.astype(np.float64),b.astype(np.float64)
        result['different_sample_count']=int(np.count_nonzero(a!=b))
        result['maximum_absolute_difference_PCM16']=float(np.max(np.abs(aa-bb)))
        denom=float(np.dot(aa,aa))
        gain=float(np.dot(aa,bb)/denom) if denom else None
        result['least_squares_gain_db']=float(20*np.log10(gain)) if gain and gain>0 else None
        result['ncc']=float(np.dot(aa,bb)/(np.linalg.norm(aa)*np.linalg.norm(bb))) if np.any(aa) and np.any(bb) else None
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['old-wav','actual-wav','old-source','actual-source','old-segments','actual-segments','baseline-proof','output']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--dossier',type=Path)
    a=p.parse_args()
    before=json.loads(a.old_source.read_text());after=json.loads(a.actual_source.read_text())
    proof=json.loads(a.baseline_proof.read_text())
    old,sr=sf.read(a.old_wav,dtype='int16');new,new_sr=sf.read(a.actual_wav,dtype='int16')
    assert old.ndim==new.ndim==1 and sr==new_sr==24000
    old_fp=hashlib.md5(a.old_wav.read_bytes()).hexdigest()[:12]
    actual_fp=hashlib.md5(a.actual_wav.read_bytes()).hexdigest()[:12]
    baseline_valid=bool(proof.get('old_pcm_matches_accepted_confirmation_fingerprint') is True and proof.get('actual_old_pcm_md5_first12')==old_fp)
    old_segments=json.loads(a.old_segments.read_text());new_segments=json.loads(a.actual_segments.read_text())
    old_rows=fingerprints(before);rows=[];retained=set()
    sentence_comparisons={}
    for sentence,records in new_segments.items():
        prior=old_segments.get(sentence)
        if not prior or not records:continue
        old_span=[prior[0]['时刻'][0],prior[-1]['时刻'][1]]
        new_span=[records[0]['时刻'][0],records[-1]['时刻'][1]]
        sentence_comparisons[sentence]=comparison(old,new,sr,old_span,new_span)
    for category,key,value in fingerprints(after):
        matching=[(k,v) for c,k,v in old_rows if c==category and (k==key or (str(v.get('依据','')) and str(value.get('依据','')).startswith(str(v['依据']))))]
        old_key,old_value=next(((k,v) for k,v in matching if k==key), matching[0] if len(matching)==1 else (None,None))
        if old_value is not None:retained.add((category,old_key))
        row={'category':category,'actual_key':key,'actual_confirmation_fingerprint':value['配音指纹'],
             'current_fingerprint_matches':value['配音指纹']==actual_fp,'existing_accepted_key':old_key,
             'existing_accepted_fingerprint':old_value.get('配音指纹') if old_value else None,
             'current_basis_sha256':hashlib.sha256(str(value.get('依据','')).encode()).hexdigest(),
             'native_old_pcm_binding_valid':baseline_valid}
        if old_value is not None:
            current_clock=re.fullmatch(r'([\d.]+)[–-]([\d.]+)s',key)
            old_clock=re.fullmatch(r'([\d.]+)[–-]([\d.]+)s',old_key)
            if current_clock and old_clock:
                row['exact_declared_interval_comparison']=comparison(old,new,sr,list(map(float,old_clock.groups())),list(map(float,current_clock.groups())))
            sentence=re.search(r'S(\d+)',key) or re.search(r'S(\d+)',str(value.get('依据','')))
            if sentence and 'S'+sentence.group(1) in sentence_comparisons:
                row['sentence']='S'+sentence.group(1)
                row['whole_sentence_comparison']=sentence_comparisons[row['sentence']]
            row['same_existing_type']=old_value.get('类型')==value.get('类型')
        row['automatic_renewal_performed']=False
        rows.append(row)
    result={'article':after['no'],'purpose':'exact actual private PCM continuity scalars and whole-fingerprint inventory only',
            'quality_acceptance':False,'automatic_confirmation_renewals':False,'private_waveform_or_GT_exported':False,
            'old_source_sha256':sha(a.old_source),'actual_source_sha256':sha(a.actual_source),
            'old_pcm_sha256':sha(a.old_wav),'actual_pcm_sha256':sha(a.actual_wav),
            'old_pcm_md5_first12':old_fp,'actual_pcm_md5_first12':actual_fp,
            'native_old_pcm_binding_valid':baseline_valid,'original_baseline_proof':proof,
            'whole_sentence_comparisons':sentence_comparisons,'whole_fingerprint_confirmations':rows,
            'prior_fingerprint_entries_not_retained':[{'category':category,'old_key':key,
                'old_confirmation_fingerprint':value['配音指纹'],
                'observation':'No same-key or unique existing-basis continuation in actual source; not auto renewed.'}
                for category,key,value in old_rows if (category,key) not in retained]}
    if a.dossier and a.dossier.is_file():
        allowed={'kind','t0','t1','db','c','per','lo','id','si','pos','w0','w1'}
        result['actual_dossier_scalar_candidates']=[{k:v for k,v in item.items() if k in allowed and isinstance(v,(str,int,float,bool,type(None)))} for item in json.loads(a.dossier.read_text())]
        result['actual_dossier_sha256']=sha(a.dossier)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'article':after['no'],'confirmation_count':len(rows),'native_old_pcm_binding_valid':baseline_valid,'quality_acceptance':False}))


if __name__=='__main__':main()
