from pathlib import Path
import hashlib,json,shutil
P=Path('.github/target54-S6-cached-probe/certified5');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'manifest.json')=='24766577a0001a4920f21cf4887c4cff080d233c34d57cf45a83b7ac660cdcac'
d=json.loads((P/'manifest.json').read_text())
for row in d['core_files']:
 src=P/row['file'];dst=Path('official-main')/row['target'];assert sha(src)==row['patched_sha256'];assert sha(dst)==row['original_sha256'];shutil.copyfile(src,dst)
for key in ['reviewed_regression_resource','actual_native_fastcheck_stamp']:
 row=d[key];src=P/row['file'];dst=Path('official-main')/row['target'];expected=row.get('sha256')or row.get('patched_sha256');assert sha(src)==expected;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
