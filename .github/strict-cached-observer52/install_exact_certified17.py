from pathlib import Path
import os,json,hashlib,shutil
N=Path('.github/strict-cached-observer52');T=Path('official-main/视频/工具');P=N/'certified17';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'manifest.json')=='0bbff31f0d45b9412ec0e1a9f68b0e9603f199c2495f071320b18e82b192008f'
d=json.loads((P/'manifest.json').read_text());records=[]
for row in d['core_files']:
 src=P/row['file'];dst=Path('official-main')/row['target'];assert sha(src)==row['patched_sha256'];assert sha(dst)==row['original_sha256'];shutil.copyfile(src,dst);records.append({'target':row['target'],'sha256':sha(dst)})
stamp=d['actual_native_fastcheck_stamp'];src=P/stamp['file'];assert sha(src)==stamp['sha256'];dst=Path('official-main')/stamp['target'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';S=M/'spoken-whole-track-diagnostic/video';S.mkdir(parents=True,exist_ok=True)
context={}
for name in ['读音改正.json','按语境读音.json']:
 src=T/'发音词典'/name;assert src.is_file();dst=S/name;assert not dst.exists();shutil.copyfile(src,dst);context[name]=sha(dst)
Path('observer52-public').mkdir(exist_ok=True);Path('observer52-public/exact-certified17-and-original-dictionary-context.json').write_text(json.dumps({'kind':'diagnostic-runtime-installation-not-formal-QA','actual_certified17_contract_sha256':sha(P/'manifest.json'),'files':records,'actual_native_stamp_sha256':sha(P/stamp['file']),'shadow_original_dictionary_context':context},ensure_ascii=False,indent=2)+'\n')
