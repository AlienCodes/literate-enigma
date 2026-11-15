"""Stdlib data, original-function AST and fake-command shell routes; no models/audio."""
from pathlib import Path
import argparse,ast,copy,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tempfile
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guard',D/'reviewed_none_ending24.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
results=[]
def check(name,fn):
 fn();results.append({'name':name,'passed':True})
def datawrite(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def setup(base):
 root=base/'root';tools=root/'视频/工具';work=base/'work';req=root/'.github/video-revision-batch/request/24'
 for p in (tools,work/'scripts',req/'视频/脚本'):p.mkdir(parents=True,exist_ok=True)
 for dest in (req/'视频/脚本/24.json',work/'scripts/24.json'):shutil.copyfile(D/'fixtures/measured-c153-shadow.json',dest)
 for name in (H.PROFILE_NAME,H.REPORT_NAME,H.INTAKE_NAME):shutil.copyfile(D/'fixtures'/name,req/name)
 shutil.copyfile(D/'reviewed_none_ending24.py',root/'.github/video-revision-batch'/H.HELPER_NAME)
 for dest in (tools/'make_video.py',work/'make_video.py'):shutil.copyfile(D/'fixtures/make_video.py',dest)
 return root,tools,work,req

def run_guard_case(name,mutate=None,reject=False):
 with tempfile.TemporaryDirectory(prefix='none24-pure-')as td:
  root,t,w,q=setup(Path(td));args=[root,t,w,'24','1']
  if mutate:mutate(root,t,w,q,args)
  before={str(p):sha(p)for p in Path(td).rglob('*')if p.is_file()}
  failed=None
  try:proof=H.verify(*args)
  except (ValueError,KeyError,TypeError,FileNotFoundError)as e:failed=e
  after={str(p):sha(p)for p in Path(td).rglob('*')if p.is_file()}
  assert before==after,'Guard wrote files'
  if reject:assert failed is not None,name+' unexpectedly accepted'
  else:assert failed is None,repr(failed);assert proof['preserve_missing_ending_entry']and not proof['quality_acceptance']
 results.append({'name':name,'passed':True,'expected_reject':reject,'source_or_audio_written':False})

def jsonmut(path,key,value):
 d=json.loads(path.read_text());d[key]=value;datawrite(path,d)
def profilemut(key,val):return lambda r,t,w,q,a:jsonmut(q/H.PROFILE_NAME,key,val)
def sourceboth(key,val):
 def change(r,t,w,q,a):
  for p in [q/'视频/脚本/24.json',w/'scripts/24.json']:jsonmut(p,key,val)
  d=json.loads((q/H.PROFILE_NAME).read_text());d['immutable_request_SHA256']=sha(q/'视频/脚本/24.json');datawrite(q/H.PROFILE_NAME,d)
 return change

def route_case(name,no='24',keep='1',marker=True,bad=False,helper_bad=False,expect_original=False,expect_reject=False):
 with tempfile.TemporaryDirectory(prefix='none24-route-')as td:
  base=Path(td);r,t,w,q=setup(base);bin=base/'bin';bin.mkdir();log=base/'calls.jsonl'
  stub='''#!REAL
import json,os,sys
if sys.argv[1]in ['-','-c']:os.execv('REAL',['REAL',*sys.argv[1:]])
with open(os.environ['FAKE_COMMAND_LOG'],'a')as f:f.write(json.dumps(sys.argv[1:])+chr(10))
print('保持已审 接点样本 问题数 0 写入 句子： 分段增益dB 人看')
'''.replace('REAL',sys.executable)
  py=bin/'python3';py.write_text(stub);py.chmod(0o700)
  (t/'快速重建核查.sh').write_text('#!/bin/bash\necho "问题数 0 指纹"\n')
  if no!='24':shutil.copyfile(w/'scripts/24.json',w/f'scripts/{no}.json')
  if not marker:(q/H.PROFILE_NAME).unlink()
  if bad:jsonmut(q/H.PROFILE_NAME,'raw_fingerprint','wrong')
  if helper_bad:(r/'.github/video-revision-batch'/H.HELPER_NAME).write_text('# wrong helper\n')
  env={**os.environ,'PATH':str(bin)+':'+os.environ['PATH'],'XG_P':str(r),'XG_TOOLS':str(t),'XG_KEEP_REVIEWED_ENDING':keep,'XG_KEEP_REVIEWED_GAIN':'1','XG_KEEP_REVIEWED_CUTS':'1','FAKE_COMMAND_LOG':str(log),'PYTHONDONTWRITEBYTECODE':'1'}
  res=subprocess.run(['bash',D/'草稿声音.sh',no],cwd=w,env=env,capture_output=True,text=True)
  calls=[json.loads(s)for s in log.read_text().splitlines()]if log.exists()else[]
  constructor=[c for c in calls if Path(c[0]).name=='结尾句接点.py']
  if expect_reject:assert res.returncode!=0,(name,res.stdout,res.stderr);assert not constructor
  else:assert res.returncode==0,(name,res.stdout,res.stderr);assert bool(constructor)==expect_original,(name,calls)
  if expect_original:
   assert len(constructor)==1
   assert ('--保持已审接点'in constructor[0])==(keep=='1')
  elif not expect_reject:assert '保持已审 NONE'in res.stdout
  assert '--保持已审增益'in str(calls)if not expect_reject else True
 results.append({'name':name,'passed':True,'original_constructor_called':expect_original,'expected_reject':expect_reject,'commands_were_fakes_no_model_calls':True})

run_guard_case('exact-real-c153-request-and-canonical-none-positive')
run_guard_case('source-id-argument-wrong',lambda r,t,w,q,a:a.__setitem__(3,'35'),True)
run_guard_case('KEEP-ending-zero-reject',lambda r,t,w,q,a:a.__setitem__(4,'0'),True)
for k,v in [('source_id','35'),('target_sentence','S17'),('speed',.94),('speed',1),('comma_gap_seconds',.38),('raw_fingerprint',None),('raw_fingerprint','44b73111'),('raw_fingerprint','wrong'),('manual_gain_dB',{'S18':{'2':-1.1}}),('immutable_request_SHA256','0'*64),('immutable_target_record_SHA256','0'*64),('canonical_target_record_SHA256','0'*64),('actual_measured_whole_report_SHA256','0'*64),('actual_measured_whole_intake_SHA256','0'*64)]:run_guard_case('marker-'+k+'-'+str(v),profilemut(k,v),True)
for val in [None,{'S18':{}},{'S18':{'前段语速':.9,'最后一段语速':.78,'最后一段前停顿':.7}},{'S17':{}}]:run_guard_case('source-existing-ending-'+str(val),sourceboth('结尾句',val),True)
for val in [{'S18':{'1':H.GAIN}},{'S18':{'1':0.,'2':H.GAIN}},{'S18':{'2':-1.1}},{'S18':{'2':H.GAIN},'S17':{'1':0.}}]:run_guard_case('source-wrong-gain-'+str(val),sourceboth('分段增益dB',val),True)
run_guard_case('source-wrong-rawFP',sourceboth('区间声音指纹',{'S18':'wrong'}),True)
run_guard_case('target-old-NV-reject',sourceboth('非人声区间',{'S18':[[0.,.1]]}),True)
run_guard_case('target-old-cut-reject',sourceboth('停顿删除区间',{'S18':[[1.,2.]]}),True)
run_guard_case('target-second-comma-schema-reject',sourceboth('朗读删逗号',{'S18':{'篇号':24,'原文':H.DISPLAY,'逗号序号':[2]}}),True)
run_guard_case('maker-bytes-changed',lambda r,t,w,q,a:(t/'make_video.py').write_text((t/'make_video.py').read_text()+'\n# deliberately wrong maker bytes\n'),True)
# Independently exercise original constant parser on same-byte mismatch guard.
run_guard_case('work-maker-bytes-changed',lambda r,t,w,q,a:(w/'make_video.py').write_text('# changed\n'),True)
run_guard_case('actual-whole-evidence-changed',lambda r,t,w,q,a:(q/H.REPORT_NAME).write_text('{}'),True)
run_guard_case('actual-intake-evidence-changed',lambda r,t,w,q,a:(q/H.INTAKE_NAME).write_text('{}'),True)
run_guard_case('explicit-marker-symlink-reject',lambda r,t,w,q,a:((q/H.PROFILE_NAME).rename(q/'saved-case.json'),(q/H.PROFILE_NAME).symlink_to(q/'saved-case.json')),True)
# Exact real original maker functions extracted as AST, not imported (no model setup).
mt=ast.parse((D/'fixtures/make_video.py').read_text())
nodes=[n for n in mt.body if isinstance(n,(ast.FunctionDef,ast.Assign))and((isinstance(n,ast.FunctionDef)and n.name in ['_speech_comma_spec','_speech_rule','_speech_source_context','_speech_mother_guard'])or(isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='_SPOKEN_COMMA_ALLOWED'for x in n.targets)))]
ns={'re':re};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<original-maker-pure-AST>','exec'),ns)
d=json.loads((D/'fixtures/measured-c153-shadow.json').read_text());rule=ns['_speech_comma_spec'](d,'S18');assert rule['needs_mother_binding']and rule['projected']==H.DISPLAY.replace('and,','and',1)
results.append({'name':'original-parser-exact-NONE-projects-first-comma-only','passed':True})
bad=copy.deepcopy(d);bad['结尾句']={'S18':{'前段语速':.9,'最后一段语速':.78,'最后一段前停顿':.7}}
try:ns['_speech_comma_spec'](bad,'S18');raise AssertionError('Original parser admitted constructed ending')
except SystemExit as e:assert '结尾接点'in str(e)
results.append({'name':'original-parser-still-rejects-constructed-target-ending','passed':True})
ns.update({'SPOKEN_COMMA':{('24','S18'):rule},'_SPOKEN_SOURCE_NO':'24','VFP':{H.DISPLAY:H.RAW_FP}});ns['_speech_mother_guard'](H.DISPLAY,H.RAW_FP)
for v in [None,'44b73111','wrong']:
 ns['VFP']={}if v is None else{H.DISPLAY:v}
 try:ns['_speech_mother_guard'](H.DISPLAY,H.RAW_FP);raise AssertionError('A45 admitted wrongFP')
 except SystemExit as e:assert 'A45'in str(e)
results.append({'name':'original-A45-newFP-positive-and-none-old-wrong-negative','passed':True})
route_case('explicit-valid-case-skips-only-ending')
route_case('missing-marker-old-source24-route',marker=False,expect_original=True)
route_case('other-source-old-reviewed-route',no='35',expect_original=True)
route_case('KEEP0-original-construction-even-present-marker',keep='0',expect_original=True)
route_case('bad-marker-hard-stops-no-original-fallback',bad=True,expect_reject=True)
route_case('wrong-helper-byte-hard-stops-no-original-fallback',helper_bad=True,expect_reject=True)
# Full byte inverse and syntax prove everything outside one exact constructor segment unchanged.
original=(D/'original-草稿声音.sh').read_text();candidate=(D/'草稿声音.sh').read_text()
start=original.index('    python3 $T/结尾句接点.py');end=original.index('    if [ "$ending_rc"',start)
newstart=candidate.index('    reviewed_none_root=');newend=candidate.index('    if [ "$ending_rc"',newstart)
assert candidate[:newstart]+original[start:end]+candidate[newend:]==original
assert subprocess.run(['bash','-n',D/'草稿声音.sh'],capture_output=True).returncode==0
results.append({'name':'shell-one-constructor-block-whole-byte-inverse-and-bash-syntax','passed':True})
p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args()
report={'kind':'source24-reviewed-NONE-stdlib-data-original-AST-and-fake-shell-route-tests','passed':True,'test_count':len(results),'checks':results,'new_model_calls':0,'whole_audio_runs':0,'native_runs':0,'original_full110_run_here':False,'fixture_only_not_quality_acceptance':True}
if a.output:a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'tests':len(results),'new_model_calls':0}))
