#!/usr/bin/env python3
"""Private K125 regression inputs. This never changes production synth.py.

K125 tests donor-gain arithmetic on a fixed, G72-verified original raw input.
It does not claim a cross-machine TTS resynthesis test has passed. Processed
audio is never accepted as an input. Only the exact public 46 fixture is allowed.
"""
import argparse, copy, hashlib, json, os, pickle, runpy, shutil, sys
from pathlib import Path
import numpy as np

FIXTURE_SHA='8b1bc928de1f39b967471bab1fd8a6c1963102ff29d495db41bfeeafcf92ca4a'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def raw_sha(a): return hashlib.sha256(np.ascontiguousarray(a,dtype=np.float32).tobytes()).hexdigest()

def guard_namespace(tools):
    source=(Path(tools)/'make_video.py').read_text()
    ns={'os':os,'sys':sys,'json':json,'_hl':hashlib,'__file__':str(Path(tools)/'make_video.py')}
    exec(source[source.index('def _portable_mid(model):'):source.index('def _cached(obj,meth,model):')],ns)
    return ns

def load_entry(root,manifest,key,guard):
    if key not in manifest['entries']: raise RuntimeError('K125_FIXED_RAW_MISSING_KEY '+key)
    item=manifest['entries'][key];p=Path(root)/key
    if not p.is_file(): raise RuntimeError('K125_FIXED_RAW_MISSING_FILE '+key)
    guard['_条目核对'](str(p))
    if sha(p)!=item['sha256']: raise RuntimeError('K125_FIXED_RAW_SHA_MISMATCH '+key)
    with p.open('rb') as f:value=pickle.load(f)
    if raw_sha(value[0])!=item['raw_sha256']:raise RuntimeError('K125_FIXED_RAW_ARRAY_MISMATCH '+key)
    return value

def freeze(cache,key_log,target,tools,gt,script):
    assert sha(script)==FIXTURE_SHA,'Only the exact public 46 K125 fixture is allowed.'
    cache=Path(cache);target=Path(target);target.mkdir(parents=True,exist_ok=True)
    guard=guard_namespace(tools)
    keys=sorted({x for x in Path(key_log).read_text().splitlines() if x.endswith('.pkl')})
    assert keys,'The actual original producer raw-input key log is empty.'
    manifest={'schema':1,'kind':'K125 fixed raw regression inputs; not a production TTS reference mode',
              'fixture_sha256':FIXTURE_SHA,'entries':{},'independent_gt_exact_raw_matches':[]}
    for key in keys:
        p=cache/key;guard['_条目核对'](str(p))
        shutil.copy2(p,target/key)
        mark=Path(str(p)+'.单线程')
        if mark.exists():shutil.copy2(mark,Path(str(target/key)+'.单线程'))
        with p.open('rb') as f:value=pickle.load(f)
        manifest['entries'][key]={'sha256':sha(p),'raw_sha256':raw_sha(value[0]),
                                  'samples':len(value[0]),'single_thread_mark_preserved':mark.exists()}
    # Read-only search for an original independent, UNTRANSFORMED raw array.
    # Exact equality only: never reverse gains/edits out of an expected GT.
    by_raw={v['raw_sha256']:k for k,v in manifest['entries'].items()}
    sizes={v['samples'] for v in manifest['entries'].values()}
    for p in sorted(Path(gt).glob('46_*.npy')):
        a=np.load(p,mmap_mode='r')
        if a.ndim==1 and a.dtype==np.float32 and len(a) in sizes:
            h=raw_sha(a)
            if h in by_raw:manifest['independent_gt_exact_raw_matches'].append({'key':by_raw[h],'file':p.name,'sha256':sha(p)})
    manifest_path=target/'manifest.json'
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    for key in keys:load_entry(target,manifest,key,guard)
    return manifest_path,sha(manifest_path),manifest

def integrity_controls(root,manifest,tools):
    guard=guard_namespace(tools);root=Path(root);key=next(iter(manifest['entries']));p=root/key
    original=p.read_bytes();bad_rejected=False;missing_rejected=False
    try:
        p.write_bytes(original+b'K125_corrupt_raw')
        try:load_entry(root,manifest,key,guard)
        except (RuntimeError,SystemExit):bad_rejected=True
    finally:p.write_bytes(original)
    moved=root/(key+'.missing-probe');p.rename(moved)
    try:
        try:load_entry(root,manifest,key,guard)
        except RuntimeError as e:missing_rejected='K125_FIXED_RAW_MISSING_FILE' in str(e)
    finally:moved.rename(p)
    load_entry(root,manifest,key,guard)
    assert bad_rejected and missing_rejected,'Fixed raw tamper/missing controls must both stop.'
    return {'bad_raw_sha_rejected':bad_rejected,'missing_raw_rejected':missing_rejected}

def synth(source,manifest_path,lock,tools):
    assert sha(Path('scripts/46.json'))==FIXTURE_SHA,'Only the exact 46 regression fixture is allowed.'
    assert sha(manifest_path)==lock,'K125 fixed-input manifest changed.'
    manifest=json.loads(Path(manifest_path).read_text());assert manifest['fixture_sha256']==FIXTURE_SHA
    assert os.environ.get('STRICT_CACHE')=='1','Fixed regression source must forbid cache fallback.'
    assert not os.environ.get('OLD_IV_VOID'),'A45 cannot be disabled for a regression fixture.'
    guard=guard_namespace(tools);root=Path(manifest_path).parent
    for key in manifest['entries']:load_entry(root,manifest,key,guard)
    source_root=Path(os.environ['VIDEO_ROOT'])
    assert sha(source_root/'video/scripts/46.json')==FIXTURE_SHA,'The actual synth input must be the exact public 46 regression fixture.'
    private_root=root/'reference-model-root';private_tts=private_root/'tts'
    private_tts.mkdir(parents=True,exist_ok=True)
    for p in (source_root/'tts').iterdir():
        if p.name=='cache_tts':continue
        dest=private_tts/p.name
        if not dest.exists():dest.symlink_to(p.resolve(),target_is_directory=p.is_dir())
    if not (private_tts/'cache_tts').exists():(private_tts/'cache_tts').symlink_to(root,target_is_directory=True)
    if not (private_root/'video').exists():(private_root/'video').symlink_to(source_root/'video',target_is_directory=True)
    os.environ['VIDEO_ROOT']=str(private_root)
    model=private_tts/'kokoro-v1.0.onnx'
    mid=guard['_portable_mid'](str(model))
    sys.path.insert(0,str(private_tts))
    from kokoro_onnx import Kokoro
    original=Kokoro.from_session
    def factory(text,voice,speed=1.0,lang='en-us',**kw):
        vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest() if not isinstance(voice,str) else voice
        key=hashlib.sha1(repr(('create',mid,text,vh,float(speed),lang,sorted(kw.items()))).encode()).hexdigest()+'.pkl'
        return load_entry(root,manifest,key,guard)
    def fixed_session(*args,**kwargs):
        obj=original(*args,**kwargs);obj.create=factory;return obj
    # Dependency injection exists only in this temporary test process. The
    # real canonical synth.py file, normal entry point and its rules stay intact.
    Kokoro.from_session=fixed_session
    sys.argv=[str(source),'46']
    runpy.run_path(str(source),run_name='__main__')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--synth',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--lock',required=True);p.add_argument('--tools',required=True);a=p.parse_args()
    synth(Path(a.synth),Path(a.manifest),a.lock,Path(a.tools))
