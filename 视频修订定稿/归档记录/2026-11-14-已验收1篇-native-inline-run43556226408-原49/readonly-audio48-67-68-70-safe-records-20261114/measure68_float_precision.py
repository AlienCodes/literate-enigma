"""Quantify PCM precision for exact archived gain ratios. No fitted gain search."""
import copy,hashlib,importlib.util,io,json,pathlib,subprocess,tempfile
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent;f=B/'68';P=B/'replay_cache_provenance.py';spec=importlib.util.spec_from_file_location('readonly68_precision',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
orig=m.orig;scope0=orig.scope;sha=lambda x:hashlib.sha256(x).hexdigest()
commit='2499c73c1d4709ab955d7a6164e7179c35dfc6cd'
def old_cache_reference(d,si,cache):
    ns,t=scope0(d,si,cache);fn=ns['_auto_level']
    def lev(clips,tmap,gaps,no='',rounds=2):
        import 响度一致性核对 as LQ
        if not any(x>=LQ.IN_GAP for x in gaps):return fn(clips,tmap,gaps,no,rounds)
        mat=b''.join(np.ascontiguousarray(x,np.float32).tobytes()for x in clips);common=(str(no),list(gaps),[(round(t[2],4),round(t[3],4))for t in tmap])
        ok='调平_'+hashlib.sha1(mat+repr(common).encode()).hexdigest()+'.json';nk='调平_'+hashlib.sha1(mat+repr(common+(('K134等效',)if ns['_短起'](no)else())).encode()).hexdigest()+'.json'
        val=subprocess.check_output(['git','cat-file','blob',commit+':视频/配音缓存/'+ok],cwd='/workspace/work/github-publication/target',stderr=subprocess.PIPE);(cache/nk).write_bytes(val)
        return fn(clips,tmap,gaps,no,rounds)
    ns['_auto_level']=lev;return ns,t
def sf16(a):
    b=io.BytesIO();sf.write(b,a,24000,format='WAV',subtype='PCM_16');raw=b.getvalue();b.seek(0);pcm=sf.read(b,dtype='int16')[0];return raw,pcm
def metrics(x,y):
    diff=y.astype(np.int32)-x.astype(np.int32);ii=np.flatnonzero(diff)
    out=dict(different_PCM16_samples=len(ii),max_abs_LSB=int(np.max(np.abs(diff))),first_difference_s=None if not len(ii)else int(ii[0])/24000,last_difference_s=None if not len(ii)else int(ii[-1])/24000)
    return out
targetdata=json.loads((f/'68-proposed-source-old-voice-controls.json').read_text())
literal=json.loads((f/'68-proposed-transparent-effective-gains-source.json').read_text());ratio=copy.deepcopy(literal)
native=json.loads((f/'68-original-cache-provenance-diagnostic.json').read_text())['modes'][0];old=json.loads((f/'68-actual-historical-original-reconstruction.json').read_text())
np0={p['sentence']:p for p in native['parts']};formula=[]
for part in old['parts']:
    lab=part['sentence']
    if lab=='title':continue
    oldauto={int(k):v for k,v in part['automatic_level'].items()};oldmanual={int(k):v for k,v in (part['manual_segment_level']or{}).items()};newauto={int(k):v for k,v in np0[lab]['automatic_level'].items()}
    for k in sorted(set(oldauto)|set(oldmanual)|set(newauto)):
        oa=oldauto.get(k,0);om=oldmanual.get(k,0);na=newauto.get(k,0)
        if oa==na:continue
        oa32=np.float32(10**(oa/20));om32=np.float32(10**(om/20));na32=np.float32(10**(na/20))
        target32=np.float32(oa32*om32);r32=np.float32(target32/na32);db=float(20*np.log10(float(r32)))
        ratio.setdefault('分段增益dB',{}).setdefault(lab,{})[str(k)]=db
        formula.append(dict(sentence=lab,segment=k,archived_old_auto_dB=oa,archived_old_manual_dB=om,current_auto_dB=na,
            old_auto_float32=float(oa32),old_manual_float32=float(om32),current_auto_float32=float(na32),
            transparent_exact_float32_coefficient_ratio=float(r32),ratio_dB_for_original_source_loader=db))
(f/'68-proposed-transparent-float32-ratio-source.json').write_text(json.dumps(ratio,ensure_ascii=False,indent=2)+'\n')
report=dict(source_id='68',quality_acceptance=False,purpose='quantify literal historical-gain and exact float32 coefficient-ratio representations; no audio-fit or gain search',
    program_sha256=sha(pathlib.Path(__file__).read_bytes()),exact_ratio_formulas=formula,representations=[])
with tempfile.TemporaryDirectory(prefix='private68-float-precision-',dir='/dev/shm')as td:
    td=pathlib.Path(td);refcache=td/'reference-cache';refcache.mkdir();orig.scope=old_cache_reference
    try:ref,_=orig.build(targetdata,refcache)
    finally:orig.scope=scope0
    refr,refq=sf16(ref);assert sha(refr)==old['reconstructed_historical_WAV_sha256']
    report['diagnostic_reference_entire_WAV_matches_actual_historical_old']=True
    for label,d in [('literal_archived_effective_dB',literal),('exact_archived_float32_coefficient_ratio',ratio)]:
        cache=td/label;cache.mkdir();a,parts=orig.build(d,cache);raw,q=sf16(a)
        row=dict(label=label,WAV_sha256=sha(raw),WAV_exact_old=raw==refr,**metrics(refq,q))
        row['per_sentence_differences']=[]
        for pp in parts:
            lo=max(0,round(pp['start_s']*24000));hi=min(len(q),round(pp['end_s']*24000));z=metrics(refq[lo:hi],q[lo:hi])
            if z['different_PCM16_samples']:row['per_sentence_differences'].append(dict(sentence=pp['sentence'],**z))
        if row['WAV_exact_old']:
            wav=td/'exact.wav';aac=td/'exact.m4a';wav.write_bytes(raw);subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
            ash=sha(subprocess.check_output(['ffmpeg','-v','error','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']));row['AAC_ADTS_sha256']=ash;row['AAC_exact_old']=ash==old['old_accepted_anchor']['aac_adts_sha256']
        report['representations'].append(row);print(label,row,flush=True)
report['no_real_source_cache_algorithm_or_threshold_changed']=True;report['private_diagnostic_audio_deleted']=True
out=f/'68-exact-gain-ratio-PCM-precision-report.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('reportSHA',sha(out.read_bytes()),flush=True)
