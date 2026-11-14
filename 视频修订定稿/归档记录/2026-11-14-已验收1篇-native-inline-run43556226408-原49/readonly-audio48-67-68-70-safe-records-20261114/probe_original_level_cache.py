"""Historical same-input cached-level candidate, not inferred dB or acceptance.

Read exact old no-K134 cache JSON when present. Feed its original bytes to the
unchanged maker auto-level reader in an isolated temporary cache. No repository,
production cache, source, controls, or core changes. Never infer absent entries.
"""
import datetime,hashlib,importlib.util,json,pathlib,subprocess,sys,tempfile,traceback
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent
P=B/'replay_cache_provenance.py';s=importlib.util.spec_from_file_location('readonly_replay_base',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
orig=m.orig;sha=lambda x:hashlib.sha256(x).hexdigest()
original_scope=orig.scope
records=[]
def historical_scope(d,si,cache):
    ns,text=original_scope(d,si,cache);original_auto=ns['_auto_level']
    def previous_stored_level(clips,tmap,gaps,no='',rounds=2):
        import 响度一致性核对 as LQ
        if not any(g>=LQ.IN_GAP for g in gaps):return original_auto(clips,tmap,gaps,no,rounds)
        material=b''.join(np.ascontiguousarray(c,np.float32).tobytes()for c in clips)
        common=(str(no),list(gaps),[(round(t[2],4),round(t[3],4))for t in tmap])
        previous='调平_'+hashlib.sha1(material+repr(common).encode()).hexdigest()+'.json'
        current='调平_'+hashlib.sha1(material+repr(common+(('K134等效',)if ns['_短起'](no)else())).encode()).hexdigest()+'.json'
        raw=orig.m.git('视频/配音缓存/'+previous)
        value=json.loads(raw);assert isinstance(value,dict)and all(str(k).isdigit()and isinstance(v,(int,float))for k,v in value.items())
        (cache/current).write_bytes(raw)
        records.append(dict(sentence='S'+str(si),unchanged_raw_clips_sha256=sha(material),previous_existing_key=previous,
            current_cache_key=current,previous_bytes_sha256=sha(raw),previous_existing_value=value,
            original_repository_commit=orig.m.PIN,temporary_cache_only=True))
        return original_auto(clips,tmap,gaps,no,rounds)
    ns['_auto_level']=previous_stored_level
    return ns,text

def main(no):
    global records
    records=[];f=B/no;st=json.loads((f/f'{no}-status.json').read_text());dg=json.loads((f/f'{no}-reference-gain-diagnostic.json').read_text())
    req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request')/no/f'视频/脚本/{no}.json';raw=req.read_bytes()
    assert sha(raw)==st['request_source_sha256'][f'视频/脚本/{no}.json']
    rep=dict(source_id=no,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),quality_acceptance=False,
        purpose='test only existing historical same-input auto-level JSON via unchanged original cache reader; no inferred dB',
        program_sha256=sha(pathlib.Path(__file__).read_bytes()),source_sha256=sha(raw),original_maker_sha256=sha(orig.m.source.encode()),
        accepted_old_AAC_ADTS_sha256=st['accepted_source']['aac_adts_sha256'],actual_native_AAC_ADTS_sha256=st.get('canonical_aac_adts_sha256'))
    try:
        with tempfile.TemporaryDirectory(prefix=f'private-{no}-old-level-candidate-',dir='/dev/shm')as td:
            td=pathlib.Path(td);cache=td/'cache';cache.mkdir();orig.scope=historical_scope
            try:a,parts=orig.build(json.loads(raw),cache)
            finally:orig.scope=original_scope
            wav=td/'candidate.wav';aac=td/'candidate.m4a';sf.write(wav,a,24000)
            subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
            ash=sha(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']))
            rep.update(candidate_WAV_sha256=sha(wav.read_bytes()),candidate_AAC_ADTS_sha256=ash,
                exact_candidate_AAC_matches_old_accepted=ash==st['accepted_source']['aac_adts_sha256'],
                exact_candidate_AAC_matches_current_native=ash==st.get('canonical_aac_adts_sha256'),
                duration_s=len(a)/24000,parts=parts)
    except BaseException as e:
        rep['error']=dict(type=type(e).__name__,detail=str(e),traceback=traceback.format_exc());print(traceback.format_exc(),flush=True)
    rep['actual_existing_historical_level_entries']=records
    rep['no_parameter_estimates_no_TTS_no_source_or_existing_cache_or_core_changed']=True
    rep['private_candidate_audio_deleted']=True
    out=f/f'{no}-existing-historical-level-candidate.json';out.write_text(json.dumps(rep,ensure_ascii=False,indent=2,default=lambda x:float(x)if isinstance(x,np.floating)else int(x)if isinstance(x,np.integer)else str(x))+'\n')
    print(no,'oldAAC exact',rep.get('exact_candidate_AAC_matches_old_accepted'),'error',rep.get('error',{}).get('type'),'reportSHA',sha(out.read_bytes()),flush=True)
if __name__=='__main__':
    for a in sys.argv[1:]:main(a)
