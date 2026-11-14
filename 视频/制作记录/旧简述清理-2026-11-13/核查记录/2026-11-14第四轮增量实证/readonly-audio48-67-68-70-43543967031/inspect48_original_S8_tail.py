"""Read-only original S8 mother/producer tail scalars, no speech confirmation."""
import hashlib,importlib.util,json,pathlib,re,tempfile
import numpy as np
B=pathlib.Path(__file__).parent;f=B/'48';P=B/'replay_cache_provenance.py';s=importlib.util.spec_from_file_location('readonly48_tail',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
o=m.orig;sha=lambda x:hashlib.sha256(x).hexdigest();data=json.loads((f/'48-failed-working-source.json').read_text());diag=json.loads((f/'48-reference-gain-diagnostic.json').read_text())
with tempfile.TemporaryDirectory(prefix='private48-S8-original-tail-',dir='/dev/shm')as td:
    cache=pathlib.Path(td)/'cache';cache.mkdir();ns,sent=o.scope(data,8,cache);pieces=[];gaps=[];p0=0;listed=ns['list_commas'](sent)
    for mt in re.finditer(r'[,;:](?=\s)',sent):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start()in listed else .4)
    pieces.append((p0,len(sent)));clips,tmap=ns['sentence_audio'](sent,pieces,gaps);last=dict(ns['LAST']);before=[];fn=ns['_收句尾']
    def capture(a):before.append(a.copy());return fn(a)
    ns['_收句尾']=capture;clips,a,agn,pgn=ns['句增益'](data,'48',7,sent,pieces,gaps,clips,tmap,np.concatenate(clips))
    raw,_=ns['k'].create(ns['spoken'](sent),voice=ns['V'],speed=ns['SPEED'],lang='en-us')
    w=ns['clean_tail'](raw);w=ns['_keep_tail'](raw,w,ns['_head_offset'](raw,w));fp=hashlib.md5(np.ascontiguousarray(w).tobytes()).hexdigest()[:12]
    assert fp==data['区间声音指纹']['S8']==ns['SENT_FP'][sent]
    start=diag['public_producer_timing_metadata']['segments']['S8'][0]['时刻'][0];rows=[]
    def measure(x):
        x=x.astype(float);pk=np.sqrt(np.mean(x*x));return dict(RMS_dBFS=float(20*np.log10(pk+1e-30)),peak_dBFS=float(20*np.log10(np.max(np.abs(x))+1e-30)))
    source=before[0]if before else a
    for t in np.arange(70.55,70.705,.0025):
        i=round((t-start)*24000);j=min(len(a),i+60)
        if i<0 or j<=i:continue
        rows.append(dict(absolute_time_s=round(float(t),4),pre_tail_processing=measure(source[i:j]),post_tail_processing=measure(a[i:j]),exact_samples_equal=bool(np.array_equal(source[i:j],a[i:j]))))
    toks=[]
    for tok in last['toks'][-16:]:
        toks.append({k:getattr(tok,k)for k in ['phoneme','start','end','start_time','end_time','text']if hasattr(tok,k)and isinstance(getattr(tok,k),(str,int,float))})
    diff=np.flatnonzero(source!=a)
    report=dict(article='48',quality_acceptance=False,purpose='actual original cached S8 raw material and unchanged producer tail processing; does not identify or confirm a phoneme',
        program_sha256=sha(pathlib.Path(__file__).read_bytes()),current_maker_sha256=sha(o.m.source.encode()),spoken_sentence=sent,
        S8_actual_cleaned_mother_MD5_first12=fp,source_A45_fingerprint_matches=True,source_A45_not_invalidated=sent not in ns['VOIDED'],
        original_cached_timed_tail_phonemes=toks,original_timed_to_mother_scale=last['scale'],raw_mother_sample_count=len(raw),sentence_sample_count=len(a),
        sentence_starts_s=start,original_auto_gains=agn,original_manual_gains=pgn,tail_processing_invoked=bool(before),
        actual_tail_processor_changed_samples=len(diff),actual_tail_processor_modified_absolute_range_s=None if not len(diff)else[start+int(diff[0])/24000,start+int(diff[-1])/24000],
        original_LAST_scalar_metadata={k:last[k]for k in ['head','segs','total','cuts','grafts','gaps','hs']},
        local_pre_vs_post_tail_2p5ms_rows=rows,no_raw_or_GT_or_PCM_exported=True,no_source_or_cache_or_core_changed=True)
    report['G72_original_raw_mother_scalar_provenance']=list(o.m.cache_rows.values())
out=f/'48-S8-original-mother-tail-diagnostic.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:float(x)if isinstance(x,np.floating)else int(x)if isinstance(x,np.integer)else str(x))+'\n')
print('48 mother A45 exact',report['source_A45_fingerprint_matches'],'tail operation',report['actual_tail_processor_modified_absolute_range_s'],'timedtail',toks,'reportSHA',sha(out.read_bytes()))
