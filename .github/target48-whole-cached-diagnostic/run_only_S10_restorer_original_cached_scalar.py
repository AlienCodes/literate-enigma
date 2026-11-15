from pathlib import Path
import hashlib,json,os,re,sys,subprocess
N=Path(__file__).resolve().parent;d=json.loads((N/'only-S10-restorer-invocation.json').read_text())
for row in d['files'].values():assert hashlib.sha256((N/row['name']).read_bytes()).hexdigest()==row['sha256']
public=Path(os.environ['GITHUB_WORKSPACE'])/'target48-whole-public';public.mkdir(exist_ok=True)
values={key:str(N/row['name'])for key,row in d['files'].items()};values.update(T=str(Path(os.environ['GITHUB_WORKSPACE'])/'official-main/视频/工具'),M=str(Path(os.environ['RUNNER_TEMP'])/'completion-machine'));values['public-output']=str(public)
def substitute(x):
 return re.sub(r'\{([A-Za-z0-9_-]+)\}',lambda m:values[m[1]],x)
argv=[substitute(x)for x in d['CLI'][1:]];assert os.environ['STRICT_CACHE']=='1'and os.environ['XG_NOPUSH']=='1'
subprocess.run([sys.executable,*argv],check=True)
