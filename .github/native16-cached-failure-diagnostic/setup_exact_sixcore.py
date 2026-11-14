from pathlib import Path
import hashlib,json,os,shutil,subprocess
R=Path(os.environ['GITHUB_WORKSPACE'])/'official-main';T=R/'视频/工具';P=Path(os.environ['GITHUB_WORKSPACE'])/'.github/native16-cached-failure-diagnostic';M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';W=M/'video';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();C=P/'certified-core';assert sha(C/'manifest.json')=='b49d7f411cf135a10c7d2d62f6f472aed95c0f166591036b9034f27cf46f76c3';d=json.loads((C/'manifest.json').read_text())
for row in d['core_files']:
 src=C/row['file'];dst=R/row['target'];assert sha(src)==row['patched_sha256']and sha(dst)==row['original_sha256'];shutil.copyfile(src,dst)
for key in ['reviewed_regression_resource','actual_native_fastcheck_stamp']:
 row=d[key];src=C/row['file'];assert sha(src)==row['sha256'];shutil.copyfile(src,R/row['target'])
alias=Path('/home/user/postgraduate-vocabulary');subprocess.run(['sudo','mkdir','-p',str(alias.parent)],check=True)
if alias.is_symlink():subprocess.run(['sudo','rm',str(alias)],check=True)
if not alias.exists():subprocess.run(['sudo','ln','-s',str(R),str(alias)],check=True)
assert alias.resolve()==R.resolve()
e={**os.environ,'XG_P':str(R),'XG_TOOLS':str(T),'XG_WORK':str(W),'XG_NOPUSH':'1','STRICT_CACHE':'1'}
subprocess.run(['python',str(T/'新管/印章.py')],check=True,cwd=R,env=e)
subprocess.run(['python',str(T/'出片指纹.py'),'--拷',str(W)],check=True,cwd=R,env=e)
if not(W/'环境').exists():(W/'环境').symlink_to(T/'环境',target_is_directory=True)
(W/'scripts').mkdir(exist_ok=True);shutil.copyfile(P/'16-failed-working-source.json',W/'scripts/16.json')
subprocess.run(['python',str(P/'verify_native16_cache.py'),'--video-root',str(M),'--request',str(P/'16-failed-working-source.json'),'--contract',str(P/'native16-Origin-cache-contract.json'),'--verify-ordinary-next-mother','--output',str(Path(os.environ['GITHUB_WORKSPACE'])/'native16-public/16-exact-original-cache-readback.json')],check=True,cwd=W,env=e)
print('Original actual6core stamp and all four exact mother files read back; no inference.',flush=True)
