from pathlib import Path
import os,json,subprocess,sys,hashlib,shutil
B=Path(__file__).resolve().parent;M=B/'preflight-frozen66-v2-part1/mirror';W=M/'_22-width-overlay-work';W.mkdir(exist_ok=True);(W/'scripts').mkdir(exist_ok=True)
if not (W/'fonts').exists():(W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True)
src=B/'payload/视频/脚本/22.json';d=json.loads(src.read_text());before=d.get('说明放宽特批',{}).get('S19');assert before is not None
old_sha=hashlib.sha256(src.read_bytes()).hexdigest();d['说明放宽特批'].pop('S19')
(W/'scripts/22.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'VIDEO_S':'1','PYTHONDONTWRITEBYTECODE':'1'};env['PATH']='/workspace/work/video-venv/bin:'+env.get('PATH','')
O=B/'preflight22-width-overlay-review';O.mkdir(exist_ok=True)
with (O/'original-repair.log').open('w') as out:r=subprocess.run(['/workspace/work/video-venv/bin/python',M/'视频/工具/新管/修.py','22'],cwd=W,env=env,stdout=out,stderr=subprocess.STDOUT)
after=json.loads((W/'scripts/22.json').read_text());sys.path.insert(0,str(M/'视频/工具'));from 译文核查 import 指纹
recp=M/'视频/制作记录/逐句确认/22.json';rec=json.loads(recp.read_text());review=next(x for x in json.loads((B/'confirmation-tail-review-21-48.json').read_text())['rows'] if x['id']=='22');rec['S19']={'指纹':指纹(after['sentences'][-1]),'结论':review['suggested_conclusion'],'时间':'2026-11-13T00:00'};recp.write_text(json.dumps(rec,ensure_ascii=False,indent=1)+'\n')
with (O/'original-text-gate.log').open('w') as out:g=subprocess.run(['/workspace/work/video-venv/bin/python',M/'视频/工具/踩坑核查.py','22','出片'],cwd=W,env=env,stdout=out,stderr=subprocess.STDOUT)
shutil.copyfile(W/'scripts/22.json',O/'22-after-original-repair.json')
report={'article':'22','source_sha256':old_sha,'source_unchanged':hashlib.sha256(src.read_bytes()).hexdigest()==old_sha,'overlay':[{'path':'/说明放宽特批/S19','before':before,'after':'field removed; exact old wording preserved in pending history','reason':'old 1.2 body-relative note width contradicts newly authorized standalone full-screen summary and causes original L19 display bullets to overwrite tagged source text'}],'original_repair_exit':r.returncode,'original_gate_exit':g.returncode,'errors':[x for x in (O/'original-text-gate.log').read_text().splitlines() if x.strip().startswith(('✘','？'))],'repaired_source_for_review':str((O/'22-after-original-repair.json').resolve())};(B/'preflight22-width-overlay-proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
