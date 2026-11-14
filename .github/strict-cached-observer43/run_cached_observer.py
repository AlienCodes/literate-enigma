from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
N=Path(__file__).resolve().parent
d=json.loads((N/'invocation.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
M=Path(os.environ['RUNNER_TEMP'])/'completion-machine'
T=Path(os.environ['GITHUB_WORKSPACE'])/'official-main/视频/工具'
assert os.environ['STRICT_CACHE']=='1' and os.environ['XG_NOPUSH']=='1'
for name,expected in d['private_existing_cache_files'].items():
    original=M/'tts/spoken-comma-whole-reference-cache'/name
    assert sha(original)==expected
    target=M/'tts/cache_tts'/name
    if target.exists():assert sha(target)==expected
    else:shutil.copyfile(original,target)
for name,expected in d['included_files'].items():assert sha(N/name)==expected
helper=N/d['helper'];assert sha(helper)==d['helper_sha256']
O=Path(os.environ['GITHUB_WORKSPACE'])/('observer'+d['article']+'-public')
O.mkdir(exist_ok=True)
mapping={'tools':str(T),'video_root':str(M),'namespace':str(N),'output':str(O/('source'+d['article']+'-strict-cached-observation.json'))}
arguments=[part.format_map(mapping) for part in d['arguments']]
subprocess.run([sys.executable,str(helper),*arguments],check=True)
