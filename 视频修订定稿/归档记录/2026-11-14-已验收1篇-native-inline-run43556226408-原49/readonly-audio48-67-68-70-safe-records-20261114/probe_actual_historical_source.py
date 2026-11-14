"""Reconstruct historical public final-push source with its original maker/clean.

Only exact archived code, source, voice, pronunciation, G72 raw mothers and level
JSON are used. No estimated gains. Private diagnostic audio is removed on exit.
"""
import ast,datetime,hashlib,importlib.util,io,json,pathlib,subprocess,sys,tempfile,traceback
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent
P=B/'replay_cache_provenance.py';spec=importlib.util.spec_from_file_location('readonly_base_historical',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
orig=m.orig;sha=lambda x:hashlib.sha256(x).hexdigest()
REPO='/workspace/work/github-publication/target'
COMMITS={'67':'35f90ba0552524301ce93831279155aa1984a61e','68':'2499c73c1d4709ab955d7a6164e7179c35dfc6cd','70':'b098d633cb67999f66767564e0f93f722fec9640'}
original_git=orig.m.git
original_scope=orig.scope
def main(no):
    commit=COMMITS[no];f=B/no;st=json.loads((f/f'{no}-status.json').read_text())
    def get(path):return subprocess.check_output(['git','cat-file','blob',commit+':'+path],cwd=REPO,stderr=subprocess.PIPE)
    source=get('视频/脚本/'+no+'.json');maker=get('视频/工具/make_video.py');clean=get('视频/工具/clean.py')
    af=get('视频/工具/配音/AF.txt').decode().strip();voice=get('视频/工具/配音/voice_mb.npy')
    pron=get('视频/工具/发音词典/读音改正.json');ctx=get('视频/工具/发音词典/按语境读音.json')
    rep=dict(source_id=no,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),quality_acceptance=False,
        purpose='exact archived historical final-push source + original maker/clean + same G72 raw mothers + historical original level JSON',
        program_sha256=sha(pathlib.Path(__file__).read_bytes()),historical_commit=commit,
        historical_source_sha256=sha(source),historical_maker_sha256=sha(maker),historical_clean_sha256=sha(clean),
        historical_AF_sha256=sha(af.encode()),historical_voice_file_sha256=sha(voice),
        historical_pronunciation_sha256=sha(pron),historical_context_pronunciation_sha256=sha(ctx),
        old_accepted_anchor=st['accepted_source'])
    (f/f'{no}-historical-final-push-source.json').write_bytes(source)
    levels=[]
    def historical_git(path):
        if path.startswith('视频/配音缓存/调平_'):
            raw=get(path);levels.append(dict(path=path,commit=commit,sha256=sha(raw),value=json.loads(raw)));return raw
        return original_git(path)
    def historical_scope(d,si,cache):
        ns,t=original_scope(d,si,cache)
        # Compatibility only for the read-only exact-cache loader, not a producer
        # function: the historical producer had no K134 key suffix at all.
        if '_短起' not in ns:ns['_短起']=lambda no:False
        return ns,t
    try:
        orig.m.source=maker.decode();orig.m.tree=ast.parse(maker);orig.m.clean=clean.decode();orig.m.clean_tree=ast.parse(clean)
        orig.m.V=np.load(io.BytesIO(voice));orig.pron=json.loads(pron);orig.ctx=json.loads(ctx)
        orig.m.git=historical_git;orig.scope=historical_scope
        with tempfile.TemporaryDirectory(prefix=f'private-{no}-historical-original-',dir='/dev/shm')as td:
            td=pathlib.Path(td);cache=td/'cache';cache.mkdir();audio,parts=orig.build(json.loads(source),cache)
            wav=td/'historical.wav';aac=td/'historical.m4a';sf.write(wav,audio,24000)
            subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',af,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
            ash=sha(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']))
            rep.update(reconstructed_historical_WAV_sha256=sha(wav.read_bytes()),reconstructed_historical_AAC_ADTS_sha256=ash,
                exact_reconstruction_AAC_matches_old_accepted=ash==st['accepted_source']['aac_adts_sha256'],
                exact_reconstruction_AAC_matches_native_failed=ash==st.get('canonical_aac_adts_sha256'),
                duration_s=len(audio)/24000,parts=parts)
    except BaseException as ex:
        rep['error']=dict(type=type(ex).__name__,detail=str(ex),traceback=traceback.format_exc());print(traceback.format_exc(),flush=True)
    rep['historical_existing_level_JSON_provenance']=levels
    rep['G72_raw_mother_scalar_provenance']=list(orig.m.cache_rows.values())
    rep['no_TTS_no_production_no_source_or_existing_cache_or_core_changed']=True
    rep['private_diagnostic_audio_deleted']=True
    out=f/f'{no}-actual-historical-original-reconstruction.json';out.write_text(json.dumps(rep,ensure_ascii=False,indent=2,default=lambda x:float(x)if isinstance(x,np.floating)else int(x)if isinstance(x,np.integer)else str(x))+'\n')
    print(no,'historical oldAAC exact',rep.get('exact_reconstruction_AAC_matches_old_accepted'),'error',rep.get('error',{}).get('detail'),'reportSHA',sha(out.read_bytes()),flush=True)
    orig.m.git=original_git;orig.scope=original_scope
if __name__=='__main__':
    for a in sys.argv[1:]:main(a)
