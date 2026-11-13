from pathlib import Path
import os,json,hashlib,shutil,subprocess,concurrent.futures,datetime,sys,ast,re
B=Path(__file__).resolve().parent;P=B/'payload';M=B/'actual-payload-gen-proof/mirror';T=M/'视频/工具';G=T/'初稿生成';G.mkdir(parents=True,exist_ok=True);(M/'新版定稿').mkdir(parents=True,exist_ok=True);(M/'视频/制作记录').mkdir(parents=True,exist_ok=True);O=B/'actual-payload-gen-proof';(O/'logs').mkdir(exist_ok=True);(O/'outputs').mkdir(exist_ok=True)
BASE=B/'preflight-frozen66-v2-part1/mirror';PY='/workspace/work/video-venv/bin/python';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sys.path.insert(0,str(B));from generator_text_preflight import differences
core={}
for rel in ['初稿生成/核对.py','重点词被去掉.py']:
 s=BASE/'视频/工具'/rel;d=T/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,d);core[rel]=sha(s)
for no in [f'{x:02}' for x in range(1,71)]:
 gen=P/f'视频/工具/初稿生成/gen{no}.py';assert gen.exists();shutil.copyfile(gen,G/gen.name)
 md=next((P/'新版定稿').glob(no+'-*.md'),None) or next((BASE/'新版定稿').glob(no+'-*.md'));shutil.copyfile(md,M/'新版定稿'/md.name)
for root in [P,BASE]:
 s=root/'视频/制作记录/重点词被去掉.json'
 if s.exists():shutil.copyfile(s,M/'视频/制作记录/重点词被去掉.json');break

def one(i):
 no=f'{i:02}';src=P/f'视频/脚本/{no}.json';gen=P/f'视频/工具/初稿生成/gen{no}.py';sb=src.read_bytes();expected=json.loads(sb);gb=gen.read_bytes();w=O/'work'/no;(w/'scripts').mkdir(parents=True,exist_ok=True)
 target=w/f'scripts/{no}.json'
 if target.exists():target.unlink()
 r=subprocess.run([PY,str((G/gen.name).resolve())],cwd=w,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
 stdout=r.stdout+r.stderr;(O/f'logs/{no}.log').write_text(stdout);got=json.loads(target.read_text()) if target.exists() else None;diff=differences(expected,got)
 if target.exists():shutil.copyfile(target,O/f'outputs/{no}.json')
 return {'id':no,'source_sha256':hashlib.sha256(sb).hexdigest(),'actual_PAY_generator_sha256':hashlib.sha256(gb).hexdigest(),'actual_PAY_generator_bytes_copied_exactly':(G/gen.name).read_bytes()==gb,'source_unchanged':src.read_bytes()==sb,'generator_unchanged':gen.read_bytes()==gb,'original_helper_exit':r.returncode,'whole_JSON_exact':r.returncode==0 and not diff,'differences':diff,'English_manuscript_mismatch':'英文不一致'in stdout or '英文（去掉加粗）不一致'in stdout,'log':str((O/f'logs/{no}.log').resolve())}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:rows=sorted(ex.map(one,range(1,71)),key=lambda x:x['id'])
report={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'read-only execution of each ACTUAL existing PAY genNN.py byte-for-byte through original helper, clean independent output directories; not replacement candidate proof','writes_to_production_source_or_generators':False,'original_helpers_sha256':core,'core_unchanged':all(sha(T/rel)==h for rel,h in core.items()),'articles':rows};render=B/'final-layout/official/render.py';node=next(n for n in ast.parse(render.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='strip_gloss');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),str(render),'exec'),ns);norm=lambda x:re.sub(r'\s+',' ',ns['strip_gloss'](x).replace('**','')).strip()
for row in rows:
 no=row['id'];source=json.loads((P/f'视频/脚本/{no}.json').read_text());md=next((M/'新版定稿').glob(no+'-*.md')).read_text();paras=md.split('## 英文',1)[1].split('## 中文',1)[0].strip().split('\n\n');checks=[]
 for pi,pp in enumerate(paras,1):
  got=' '.join(c['en']for sent in source['sentences']if sent['para']==pi for c in sent['chunks']);checks.append({'para':pi,'official_strip_gloss_visible_text_equal_allowing_only_whitespace':norm(got)==norm(pp),'inline_display_markers':re.findall(r'\{\{.*?\}\}',got)})
 row['visible_English_manuscript_equal_after_original_display_gloss_removal']=all(x['official_strip_gloss_visible_text_equal_allowing_only_whitespace']for x in checks)
 if row['English_manuscript_mismatch']:row['helper_English_diagnostic_review']={'classification':'original helper strips bold only; JSON retains inline display/grammar gloss, actual visible English checked with unchanged official render.strip_gloss','paragraphs':checks}
report['original_helper_diagnostic_count']=sum(r['English_manuscript_mismatch']for r in rows);report['all_visible_English_manuscripts_match']=all(r['visible_English_manuscript_equal_after_original_display_gloss_removal']for r in rows)
report['status']='passed_full_JSON_exact_with_documented_display_marker_diagnostics' if report['core_unchanged']and all(r['whole_JSON_exact']and r['source_unchanged']and r['generator_unchanged']and r['visible_English_manuscript_equal_after_original_display_gloss_removal']for r in rows)else'needs_review'
(B/'actual-payload-gen-proof/report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'exact_count':sum(r['whole_JSON_exact']for r in rows),'original_helper_diagnostic_count':report['original_helper_diagnostic_count'],'real_visible_English_mismatch_ids':[r['id']for r in rows if not r['visible_English_manuscript_equal_after_original_display_gloss_removal']]},ensure_ascii=False))
