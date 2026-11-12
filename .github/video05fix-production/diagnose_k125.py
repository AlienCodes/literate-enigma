"""In-place K125 source/reference diagnosis; export scalar evidence only."""
import hashlib, importlib.util, json, os, pickle, shutil, subprocess, tempfile
import numpy as np
from pathlib import Path

def diagnose(root, machine, work, tools, logs, env):
    def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    spec=importlib.util.spec_from_file_location('k125_original_quicktest',tools/'新管/快测.py')
    q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
    q.env0={**{k:v for k,v in env.items() if not k.startswith('GIT_')},
            'XG_QUICKTEST':'1','XG_NO':'27'}
    q.NO='27'
    assert Path(q.T).resolve()==tools.resolve(),'Diagnostic tools must match the real full quicktest.'
    reference=machine/'qc_independent/gt'
    protected={p.name:sha(p) for p in reference.glob('05*') if p.is_file()}
    protected['a.wav']=sha(work/'work_05/a.wav')
    key_log=logs/'05-protected-cache.keys'
    cache_keys=sorted(set(key_log.read_text().splitlines()))
    protected_cache={}
    for key in cache_keys:
        p=machine/'tts/cache_tts'/key
        assert p.exists(),('Protected 05 producer cache entry missing',key)
        protected_cache[key]=sha(p)
        marker=Path(str(p)+'.单线程')
        if marker.exists():protected_cache[key+'.单线程']=sha(marker)
    original_temp=tempfile.TemporaryDirectory
    def summarize(path):
        out={'directory_kept_internal':True}
        for kind in ('好','坏'):
            rp=path/f'qc_{kind}/report2_46.json'
            if not rp.exists(): out[kind]={'report_missing':True};continue
            r=json.loads(rp.read_text());meta=json.loads((path/f'qc_{kind}/gt/46_meta.json').read_text())
            md={it['idx']:it for it in meta}
            out[kind]={'extra_count':len(r.get('extra_runs',[])),
                'extra_first_ranges':r.get('extra_runs',[])[:12],
                'a10_count':sum(bool(e.get('edge_bad')) for t in r['texts'] for e in t['edits']),
                'texts':[{'idx':t['idx'],'anchor_ncc':t['anchor_ncc'],
                    'unmatched_blocks':t['n_unmatched_blocks'],
                    'reference_input_key':Path(md[t['idx']]['file']).name,
                    'reference_sha256':sha(md[t['idx']]['file']),
                    'extra_runs_in_text':sum(t['A_start']<=x[0]<=t['A_end'] for x in r.get('extra_runs',[]))}
                    for t in r['texts']],
                'fact_edges':[{k:e.get(k) for k in ('raw_k1','raw_k2','pre_db','post_db','pre_min_db','post_min_db','lost_max_db','edge_bad','edge_sides','tail_cut_ms','onset_cut_ms')}
                    for t in r['texts'] if t['idx']==3 for e in t['edits'] if 'fact,' in e.get('words','')]}
        audio=path/'video/work_46/a.wav'
        out['processed_audio_sha256']=sha(audio) if audio.exists() else None
        out['script_sha256']=sha(path/'video/scripts/46.json')
        return out
    def run_original(name, w):
        retained=[]
        class Keep(original_temp):
            def __enter__(self):
                value=super().__enter__();retained.append(Path(value));return value
            def __exit__(self,*args): self._finalizer.detach();return False
        oldw=q.W;olde=q.env0;oldt=tempfile.TemporaryDirectory
        cache_log=logs/f'k125-{name}-producer.keys';cache_log.write_text('')
        q.W=str(w);q.env0={**q.env0,'CACHE_LOG':str(cache_log)};tempfile.TemporaryDirectory=Keep
        try: errors=q.供体增益样本()
        finally: q.W=oldw;q.env0=olde;tempfile.TemporaryDirectory=oldt
        paths=[p for p in retained if (p/'video/scripts/46.json').exists()]
        assert len(paths)==1,(name,'unexpected control directories',len(paths))
        report=summarize(paths[0]);report['canonical_selftest_errors']=errors
        report['actual_producer_cache_keys']=sorted(set(cache_log.read_text().splitlines()))
        return paths[0],report
    original_path,original=run_original('original',work)
    evidence={'original':original,'original_quicktest_sha256':sha(tools/'新管/快测.py'),
        'global_pronunciation_sha256':sha(tools/'发音词典/读音改正.json'),
        'raw_data_exported':False}
    # Compare actual producer cache with a new independent single-thread
    # Kokoro session on this host. This does not infer GT from processed audio.
    raw_code=r'''
import hashlib,json,os,numpy as np
from pathlib import Path
import make_video as p
d=json.loads(Path('scripts/46.json').read_text())
meta=json.loads(Path(os.environ['K125_META']).read_text())
fresh=p._单线程会话('../tts/kokoro-v1.0.onnx');fresh.create=p._pron(fresh.create)
rows=[]
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
for it in meta:
 idx=it['idx'];ending=idx>=0 and bool(d.get('结尾句',{}).get('S'+str(idx+1)))
 if ending:rows.append({'idx':idx,'ending_excluded':True});continue
 log=Path(os.environ['K125_RAW_REPORT']).with_suffix('.keys');log.write_text('')
 os.environ['CACHE_LOG']=str(log)
 a,_=p.k.create(p.spoken(it['text']),voice=p.V,speed=.95,lang='en-us')
 b,_=fresh.create(p.spoken(it['text']),voice=p.V,speed=.95,lang='en-us')
 a=np.asarray(a,np.float32);b=np.asarray(b,np.float32);n=min(len(a),len(b))
 delta=a[:n].astype(np.float64)-b[:n].astype(np.float64)
 rows.append({'idx':idx,'producer_cached_raw_sha256':h(a),'independent_current_raw_sha256':h(b),
 'samples_producer':len(a),'samples_current':len(b),'identical':np.array_equal(a,b),
 'raw_ncc':float(np.dot(a[:n].astype(np.float64),b[:n].astype(np.float64))/(np.linalg.norm(a[:n].astype(np.float64))*np.linalg.norm(b[:n].astype(np.float64))+1e-30)),
 'raw_max_abs_delta':float(np.max(np.abs(delta))),
 'actual_cache_keys':list(dict.fromkeys(log.read_text().splitlines())),
 'actual_phonemes_sha256':hashlib.sha256(p.phonemes_of(p._synth_punct(p.spoken(it['text']))).encode()).hexdigest()})
Path(os.environ['K125_RAW_REPORT']).write_text(json.dumps(rows,ensure_ascii=False,indent=2))
'''
    raw_report=logs/'k125-raw-pairs.json'
    with (logs/'k125-raw-pairs.log').open('w') as out:
        proc=subprocess.run(['python3','-c',raw_code],cwd=original_path/'video',
            env={**env,'K125_META':str(original_path/'qc_好/gt/46_meta.json'),'K125_RAW_REPORT':str(raw_report)},
            stdout=out,stderr=subprocess.STDOUT)
    evidence['raw_pair_comparison_exit']=proc.returncode
    if proc.returncode==0:evidence['raw_pairs']=json.loads(raw_report.read_text())
    else:evidence['raw_pair_comparison_error']=(logs/'k125-raw-pairs.log').read_text(errors='replace').splitlines()[-8:]
    if original['canonical_selftest_errors']:
        # Same public 46 fixture, original checker, fresh producer namespace
        # and fresh independent references. Model/voice files are read-only
        # links; no original 05 or shared source/reference cache is replaced.
        isolated=machine/'k125-isolated-current-host';iw=isolated/'video';it=isolated/'tts'
        iw.mkdir(parents=True,exist_ok=True);it.mkdir(exist_ok=True)
        for p in (machine/'tts').iterdir():
            if p.name=='cache_tts':continue
            dest=it/p.name
            if not dest.exists():dest.symlink_to(p,target_is_directory=p.is_dir())
        (it/'cache_tts').mkdir(exist_ok=True)
        for p in work.iterdir():
            if p.is_file() and p.suffix=='.py':shutil.copy2(p,iw/p.name)
        if not (iw/'fonts').exists():(iw/'fonts').symlink_to(work/'fonts',target_is_directory=True)
        (iw/'scripts').mkdir(exist_ok=True)
        isolated_path,rebuilt=run_original('isolated-current-host',iw)
        evidence['isolated_current_host']=rebuilt
        evidence['isolated_fixture_passed_original_good_and_bad']=not rebuilt['canonical_selftest_errors']
        source_keys=original['actual_producer_cache_keys'];fresh_keys=rebuilt['actual_producer_cache_keys']
        evidence['same_actual_producer_cache_input_keys']=source_keys==fresh_keys
        pairs=[]
        for key in sorted(set(source_keys)&set(fresh_keys)):
            a_path=machine/'tts/cache_tts'/key;b_path=it/'cache_tts'/key
            if not (a_path.exists() and b_path.exists()):continue
            with a_path.open('rb') as f:a=np.asarray(pickle.load(f)[0],np.float32)
            with b_path.open('rb') as f:b=np.asarray(pickle.load(f)[0],np.float32)
            pairs.append({'key':key,'source_raw_sha256':hashlib.sha256(a.tobytes()).hexdigest(),
                'new_raw_sha256':hashlib.sha256(b.tobytes()).hexdigest(),
                'source_samples':len(a),'new_samples':len(b),'identical':np.array_equal(a,b)})
        evidence['all_producer_cache_pairs_including_donors']=pairs
    after={p.name:sha(p) for p in reference.glob('05*') if p.is_file()};after['a.wav']=sha(work/'work_05/a.wav')
    evidence['original05_audio_and_reference_files_unchanged']=protected==after
    assert protected==after,'K125 diagnosis changed protected 05 original audio or reference files.'
    after_cache={name:sha(machine/'tts/cache_tts'/name) for name in protected_cache}
    evidence['original05_producer_cache_entries_checked']=len(cache_keys)
    evidence['original05_producer_cache_files_unchanged']=protected_cache==after_cache
    assert protected_cache==after_cache,'K125 diagnosis changed protected original 05 producer cache files.'
    (logs/'k125-scalar-diagnosis.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    return evidence
