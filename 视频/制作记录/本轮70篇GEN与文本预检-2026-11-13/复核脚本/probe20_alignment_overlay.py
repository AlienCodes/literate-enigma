from pathlib import Path
import os,json,subprocess,sys,hashlib,shutil,copy,importlib.util
B=Path(__file__).resolve().parent;M=B/'preflight-frozen66-v2-part2/mirror';W=M/'_20-alignment-overlay-work';W.mkdir(exist_ok=True);(W/'scripts').mkdir(exist_ok=True)
if not (W/'fonts').exists():(W/'fonts').symlink_to(M/'视频/工具/fonts',target_is_directory=True)
src=B/'payload/视频/脚本/20.json';before=json.loads(src.read_text());d=copy.deepcopy(before);a=d['sentences'][5]['chunks'][1]['align'];assert a[0]==['who lived about 5,300 years ago,','生活在约5,300年前，'];d['sentences'][5]['chunks'][1]['align']=[['who lived','生活在'],['about 5,300 years ago,','约5,300年前，']]+a[1:]
quote='最后这个，最后这个字体，最后这个字体一定要认认真真的去根据屏幕进行适当的放大，然后好好排版，一定要就是居中排版，弄得特别好看。'
d.setdefault('换行变更已获同意',{})['S6']='用户 2026-11-13 原话：“'+quote+'”本轮已审核任务摘录要求S6第二视觉行完整到ago，第三行从between开始；本字段只登记该既定视觉分行。'
if 'joints' not in d.get('allow_clash',[]):d.setdefault('allow_clash',[]).append('joints')
old_sha=hashlib.sha256(src.read_bytes()).hexdigest();O=B/'preflight20-alignment-overlay-review';O.mkdir(exist_ok=True);(O/'20-candidate.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(W/'scripts/20.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
# Refresh actual pending document and explicit current focus data in the mirror, not production JSON.
shutil.copyfile(B/'payload/视频/制作记录/20_待改清单.md',M/'视频/制作记录/20_待改清单.md')
for no in ['03','22']:shutil.copyfile(B/f'payload/视频/脚本/{no}.json',M/f'视频/脚本/{no}.json')
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'VIDEO_S':'1','PYTHONDONTWRITEBYTECODE':'1'};env['PATH']='/workspace/work/video-venv/bin:'+env.get('PATH','')
with (O/'original-repair.log').open('w') as out:r=subprocess.run(['/workspace/work/video-venv/bin/python',M/'视频/工具/新管/修.py','20'],cwd=W,env=env,stdout=out,stderr=subprocess.STDOUT)
with (O/'original-text-gate.log').open('w') as out:g=subprocess.run(['/workspace/work/video-venv/bin/python',M/'视频/工具/踩坑核查.py','20','出片'],cwd=W,env=env,stdout=out,stderr=subprocess.STDOUT)
after=json.loads((W/'scripts/20.json').read_text());shutil.copyfile(W/'scripts/20.json',O/'20-after-original-repair.json')
layout=[]
for scale in (1,2):
 os.environ['VIDEO_S']=str(scale);spec=importlib.util.spec_from_file_location('probe20_render_'+str(scale),B/'final-layout/official/render.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R);R.F=str(M/'视频/工具/fonts')+'/'
 body=copy.deepcopy(d);R.拆出简述页(body);R.apply_script(body);colors=R.分色(body);R.unify_colors(colors,body['sentences']);s=body['sentences'][5];ch=[[tuple(p) for p in c['align']] for c in s['chunks']];notes=[c.get('note') for c in s['chunks']];co=R.sent_colors(colors,s);es=min(R.max_es(ch,co,notes),100*scale);R.ES_FIXED=es;rs,h,w,dim=R._measure(ch,co,notes,es,R._grouping(ch,co));enrows=[]
 for rr in rs:
  for row in rr:
   if isinstance(row,tuple):enrows.extend(''.join(t for t,_ in line) for line in R.layout(row[1]['se'],dim[1],R.MAXW2))
   else:enrows.append(' '.join(''.join(t for t,_ in cell['se']) for cell in row))
 expected=['Known as Ötzi, the natural mummy was a man','who lived about 5,300 years ago,','between 3350 and 3105 BC.'];path=O/f'20-S6-split-{R.W}x{R.H}.png';R.frame_interlinear(ch,co,'',.5,str(path),active=1,notes=notes)
 layout.append({'scale':scale,'font':es,'height':h,'width':w,'bounds':[R.MAXW2,R.MAXH2],'fits':h<=R.MAXH2 and w<=R.MAXW2,'english_rows':enrows,'exact_requested_rows':enrows==expected,'orphans':R.orphan_lines(ch,co,notes,es),'wide_notes':R.wide_notes(ch,co,notes,es),'preview':str(path)})
report={'article':'20','source_sha256':old_sha,'source_unchanged':hashlib.sha256(src.read_bytes()).hexdigest()==old_sha,'candidate_sha256':hashlib.sha256((O/'20-candidate.json').read_bytes()).hexdigest(),'changes':'split seven-word align group into2+4 words, retain original newline sentinel and exact per-chunk en/zh; add explicitly authorized joints reuse and actual top-level S6 visual-layout record','spoken_chunk_fields_exact':all((a['en'],a['zh'])==(b['en'],b['zh']) for sa,sb in zip(before['sentences'],d['sentences']) for a,b in zip(sa['chunks'],sb['chunks'])),'original_repair_exit':r.returncode,'original_gate_exit':g.returncode,'errors':[x for x in (O/'original-text-gate.log').read_text().splitlines() if x.strip().startswith(('✘','？'))],'layout':layout,'candidate':str((O/'20-candidate.json').resolve())};(B/'preflight20-alignment-overlay-proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
