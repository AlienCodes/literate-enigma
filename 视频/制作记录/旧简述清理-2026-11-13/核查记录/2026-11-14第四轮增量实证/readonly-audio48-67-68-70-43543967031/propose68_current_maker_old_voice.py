"""Isolated data-only restoration candidate under unchanged CURRENT maker.

Every proposed gain is an archived original value; every cache row uses the same
verified raw clips and maps to an actual archived prior JSON. No fitting, inference,
source application, production, or quality-acceptance claim occurs here.
"""
import copy,datetime,hashlib,importlib.util,json,pathlib,subprocess,tempfile,traceback
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent;P=B/'replay_cache_provenance.py';s=importlib.util.spec_from_file_location('readonly68_current',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
orig=m.orig;sha=lambda x:hashlib.sha256(x).hexdigest();f=B/'68';commit='2499c73c1d4709ab955d7a6164e7179c35dfc6cd'
req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request/68/视频/脚本/68.json');raw=req.read_bytes();data=json.loads(raw)
old=json.loads((f/'68-historical-final-push-source.json').read_text());candidate=copy.deepcopy(data)
candidate['分段增益dB']['S2']=copy.deepcopy(old['分段增益dB']['S2'])
cp=f/'68-proposed-source-old-voice-controls.json';cp.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
assert candidate['sentences']==data['sentences']
rep=dict(source_id='68',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),quality_acceptance=False,
    purpose='isolated archived-data candidate under exact unchanged current maker, pending root review and original production gates',
    program_sha256=sha(pathlib.Path(__file__).read_bytes()),original_current_maker_sha256=sha(orig.m.source.encode()),
    original_current_clean_sha256=sha(orig.m.clean.encode()),current_source_sha256=sha(raw),candidate_source_sha256=sha(cp.read_bytes()),
    historical_control_commit=commit,source_candidate_path=str(cp),current_source_or_core_or_existing_cache_modified=False,
    candidate_control_before=data['分段增益dB'],candidate_control_after=candidate['分段增益dB'],
    full_visible_sentences_translations_notes_summary_unchanged=True)
assert rep['original_current_maker_sha256']=='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
st=json.loads((f/'68-status.json').read_text());actual_old=json.loads((f/'68-actual-historical-original-reconstruction.json').read_text());assert actual_old['exact_reconstruction_AAC_matches_old_accepted']
scope0=orig.scope;levels=[]
def scope(d,si,cache):
    ns,t=scope0(d,si,cache);fn=ns['_auto_level']
    def level(clips,tmap,gaps,no='',rounds=2):
        import 响度一致性核对 as LQ
        if not any(g>=LQ.IN_GAP for g in gaps):return fn(clips,tmap,gaps,no,rounds)
        material=b''.join(np.ascontiguousarray(c,np.float32).tobytes()for c in clips);common=(str(no),list(gaps),[(round(t[2],4),round(t[3],4))for t in tmap])
        oldkey='调平_'+hashlib.sha1(material+repr(common).encode()).hexdigest()+'.json'
        newkey='调平_'+hashlib.sha1(material+repr(common+(('K134等效',)if ns['_短起'](no)else())).encode()).hexdigest()+'.json'
        before=orig.m.git('视频/配音缓存/'+newkey)
        after=subprocess.check_output(['git','cat-file','blob',commit+':视频/配音缓存/'+oldkey],cwd='/workspace/work/github-publication/target',stderr=subprocess.PIPE)
        av=json.loads(after);assert isinstance(av,dict)and all(isinstance(v,(int,float))for v in av.values())
        (cache/newkey).write_bytes(after)
        levels.append(dict(sentence='S'+str(si),raw_clips_sha256=sha(material),native_key=newkey,native_original_SHA256=sha(before),native_original_value=json.loads(before),
            restored_value=av,historical_key=oldkey,historical_SHA256=sha(after),historical_commit=commit,changed=before!=after,
            candidate_cache_file=str(f/'candidate-cache'/newkey)))
        if before!=after:
            (f/'candidate-cache').mkdir(exist_ok=True);(f/'candidate-cache'/newkey).write_bytes(after)
        return fn(clips,tmap,gaps,no,rounds)
    ns['_auto_level']=level
    return ns,t
try:
    orig.scope=scope
    with tempfile.TemporaryDirectory(prefix='private68-current-maker-data-only-',dir='/dev/shm')as td:
        td=pathlib.Path(td);cache=td/'cache';cache.mkdir();a,parts=orig.build(candidate,cache)
        wav=td/'candidate.wav';aac=td/'candidate.m4a';sf.write(wav,a,24000)
        subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
        ash=sha(subprocess.check_output(['ffmpeg','-v','error','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']));wsh=sha(wav.read_bytes())
        rep.update(candidate_WAV_sha256=wsh,historical_exact_old_WAV_sha256=actual_old['reconstructed_historical_WAV_sha256'],
            current_maker_candidate_WAV_exact_historical_old=wsh==actual_old['reconstructed_historical_WAV_sha256'],
            candidate_AAC_ADTS_sha256=ash,accepted_AAC_ADTS_sha256=st['accepted_source']['aac_adts_sha256'],
            current_maker_candidate_AAC_exact_actual_old_accepted=ash==st['accepted_source']['aac_adts_sha256'],duration_s=len(a)/24000,parts=parts)
except BaseException as ex:
    rep['error']=dict(type=type(ex).__name__,detail=str(ex),traceback=traceback.format_exc());print(traceback.format_exc(),flush=True)
finally:orig.scope=scope0
rep['actual_level_cache_candidates']=levels;rep['changed_level_cache_count']=sum(x['changed']for x in levels)
rep['private_diagnostic_audio_deleted']=True;rep['no_TTS_no_production_no_existing_source_or_cache_or_core_modified']=True
out=f/'68-current-maker-data-restoration-candidate-report.json';out.write_text(json.dumps(rep,ensure_ascii=False,indent=2,default=lambda x:float(x)if isinstance(x,np.floating)else int(x)if isinstance(x,np.integer)else str(x))+'\n')
print('68 current maker old AAC exact',rep.get('current_maker_candidate_AAC_exact_actual_old_accepted'),'WAV exact',rep.get('current_maker_candidate_WAV_exact_historical_old'),'changed caches',rep['changed_level_cache_count'],'reportSHA',sha(out.read_bytes()),flush=True)
