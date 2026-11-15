from pathlib import Path
import hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parent;d=json.loads((N/'local513d-invocation.json').read_text())
for row in d['files'].values():assert hashlib.sha256((N/row['name']).read_bytes()).hexdigest()==row['sha256']
O=Path(os.environ['GITHUB_WORKSPACE'])/'target48-whole-public';O.mkdir(exist_ok=True)
mapping={'T':str(Path(os.environ['GITHUB_WORKSPACE'])/'official-main/视频/工具'),'M':str(Path(os.environ['RUNNER_TEMP'])/'completion-machine'),'scalarJSON':str(O/'48-current513d-twelve-PV-and-two-HL-original-cached-scalar.json')}
mapping.update({k:str(N/v['name'])for k,v in d['files'].items()})
arguments=[mapping.get(x,x)for x in d['arguments']]
assert os.environ['STRICT_CACHE']=='1'and os.environ['XG_NOPUSH']=='1'
subprocess.run([sys.executable,str(N/d['files']['helper']['name']),*arguments],check=True)
