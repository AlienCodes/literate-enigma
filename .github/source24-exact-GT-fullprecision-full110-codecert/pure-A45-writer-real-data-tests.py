from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tempfile
import argparse
_parser=argparse.ArgumentParser();_parser.add_argument('--tools',type=Path,required=True);_parser.add_argument('--output-dir',type=Path,required=True);_a=_parser.parse_args()
PKG=Path(__file__).resolve().parent;D=_a.output_dir;D.mkdir(parents=True,exist_ok=True)
O=PKG/'original-source/视频/工具/区间作废.py';C=_a.tools/'区间作废.py';CAUSE=PKG/'fixtures/actual-A45-writer-cause.json';cause=json.loads(CAUSE.read_text());source=PKG/'fixtures/A45-actual-current-source34af.json';failed=PKG/'fixtures/A45-actual-failed-source-cf301.json';measurement=PKG/'fixtures/A45-actual-selected-gain-whole8b86.json';maker=_a.tools/'make_video.py';delivery=_a.tools/'交付核查.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sp(p):p=Path(p);return{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(name,path):s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
checks=[];old=load('original_A45_writer',O);data=json.loads(source.read_text());badactual=json.loads(failed.read_text());actual=json.loads(measurement.read_text())['phases']['selected_gain_shadow']['actual_voice_fingerprint_table']['指纹'];assert actual['S18']=='e43769675c69' and data['分段增益dB']['S18']['2']==-1.109697858091752

def yes(name,condition=True):assert condition,name;checks.append({'name':name,'passed':True})
def reject(name,fn):
 try:fn();raise RuntimeError('Bad case admitted '+name)
 except (SystemExit,ValueError,AssertionError,TypeError,KeyError):pass
 checks.append({'name':name,'passed':True})
for key,path in [('current_input',source),('actual_failed_source',failed),('actual_measurement',measurement),('original_utility',O)]:yes('actual evidence hardpin '+key,sha(path)==cause[key]['sha256']and path.stat().st_size==cause[key]['bytes'])
yes('actual originalmaker unchanged0e6',sha(maker)=='0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36')
tree=ast.parse(maker.read_text());names={'_SPOKEN_COMMA_ALLOWED','_speech_comma_spec','_speech_source_context','_speech_rule','_speech_mother_guard'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names or isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id in names for x in n.targets)];e={'re':re};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-original-maker-pure-spec-A45>','exec'),e)
def original_guard(d,raw):
 spec=e['_speech_comma_spec'](d,'S18');e['SPOKEN_COMMA']={('24','S18'):spec};e['_SPOKEN_SOURCE_NO']=str(d.get('no'));e['VFP']={spec['original']:d.get('区间声音指纹',{}).get('S18')};e['_speech_mother_guard'](spec['original'],raw)
original_guard(data,actual['S18']);yes('original actual A45 source24 selected gain bound e437 positive')
reject('original actual A45 missing binding false failedworking',lambda:original_guard(badactual,actual['S18']))
x=copy.deepcopy(data);oldfp=old.记(x,actual);yes('original writer drops only actual S18 and reproduces failed whole12 VFP',len(oldfp)==12 and oldfp==badactual['区间声音指纹']and set(data['区间声音指纹'])-set(oldfp)=={'S18'})
# Every other function and top import/constants/main remain entirebytes same.
src=O.read_text();cand=C.read_text();tf=lambda s:{n.name:n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)};of,cf=tf(src),tf(cand)
yes('all other originalfunctions sourcebytes/AST exact',all(ast.get_source_segment(src,n)==ast.get_source_segment(cand,cf[k]) and ast.dump(n,include_attributes=False)==ast.dump(cf[k],include_attributes=False)for k,n in of.items()if k!='记'))
yes('only extra helper plus 记 changed',set(cf)-set(of)=={'_朗读绑定需记'} and set(of)-set(cf)==set())
# Original unchanged selftest executed in honest isolated sibling layout with real maker/delivery bytes.
with tempfile.TemporaryDirectory(prefix='actual-maker-and-writer-data-only-')as td:
 root=Path(td);oldT=root/'old';newT=root/'candidate';oldT.mkdir();newT.mkdir()
 for folder,path in [(oldT,O),(newT,C)]:
  shutil.copyfile(path,folder/'区间作废.py');shutil.copyfile(maker,folder/'make_video.py');shutil.copyfile(delivery,folder/'交付核查.py')
 new=load('candidate_A45_writer',newT/'区间作废.py')
 oldresult=subprocess.run([sys.executable,str(oldT/'区间作废.py'),'--自检'],text=True,capture_output=True);newresult=subprocess.run([sys.executable,str(newT/'区间作废.py'),'--自检'],text=True,capture_output=True)
 yes('real unchanged originalselftest before and after both pass byteexact stdout',oldresult.returncode==newresult.returncode==0 and oldresult.stdout==newresult.stdout and oldresult.stderr==newresult.stderr)
 out=D/'A45-UNCHANGED-ORIGINAL-SELFTEST-LEGACY-STDOUT.log';out.write_text(newresult.stdout+newresult.stderr)
 before=copy.deepcopy(data);x=copy.deepcopy(data);newfp=new.记(x,actual);yes('real current source keeps only already bound gainonly S18 plus original12',len(newfp)==13 and newfp==data['区间声音指纹']and newfp['S18']==actual['S18'])
 inverse=copy.deepcopy(x);inverse['区间声音指纹'].pop('S18');yes('new vs original output entireJSON only one targetVFP addition',inverse=={**before,'区间声音指纹':oldfp})
 original_guard(x,actual['S18']);yes('original A45 remains positive after writer real13 output')
 # All invalid cases reject before writing; actual-maker guard/parser remains unchanged.
 mutations=[('missing current raw',lambda d,r:r.pop('S18')),('wrong actual raw',lambda d,r:r.__setitem__('S18','0123456789ab')),('raw None',lambda d,r:r.__setitem__('S18',None)),('raw empty',lambda d,r:r.__setitem__('S18','')),('malformed raw',lambda d,r:r.__setitem__('S18','not-12-hex')),('missing old binding',lambda d,r:d['区间声音指纹'].pop('S18')),('old wrong binding',lambda d,r:d['区间声音指纹'].__setitem__('S18','44b73c000000')),('old binding None',lambda d,r:d['区间声音指纹'].__setitem__('S18',None)),('wrong source tuple',lambda d,r:d.__setitem__('no','99')),('wrong schema source',lambda d,r:d['朗读删逗号']['S18'].__setitem__('篇号',25)),('wrong full display',lambda d,r:d['朗读删逗号']['S18'].__setitem__('原文','wrong')),('wrong comma ordinal',lambda d,r:d['朗读删逗号']['S18'].__setitem__('逗号序号',[2])),('same target ENDING',lambda d,r:d.__setitem__('结尾句',{'S18':{'整句语速':.8}})),('same target synth',lambda d,r:d.__setitem__('合成标点',{'S18':[['and,','and;']]})),('table type emptylist',lambda d,r:d.__setitem__('朗读删逗号',[]))]
 for name,mutate in mutations:
  d=copy.deepcopy(data);r=copy.deepcopy(actual);mutate(d,r);snapshot=copy.deepcopy(d)
  reject('new writer rejects '+name,lambda d=d,r=r:new.记(d,r));yes('failure does not mutate source '+name,d==snapshot)
  if name!='malformed raw':reject('actual original parser/A45 rejects '+name,lambda d=d,r=r:original_guard(d,r.get('S18')))
 # A source already damaged by old writer must not magically become an approved binding.
 reject('new writer refuses already failed missing-binding working source',lambda:new.记(copy.deepcopy(badactual),actual))
 # No schema => every legacy outcome remains exactly original, including gains that have no spoken new mother scope.
 for i in range(20):
  d={'no':'24','非人声区间':{'S1':[[.1,.2]]}if i%2 else{},'词尾除阻':{'S2':{'1':[.2,'t']}}if i%3 else{},'分段增益dB':{'S18':{'2':-1.109697858091752}},'区间声音指纹':{'S1':'stale','S18':'stale'},'核对确认':{'删除段':{'S1 x':'basis'}}};a=copy.deepcopy(d);b=copy.deepcopy(d);raw={'S1':'aaa','S2':'bbb','S18':'ccc','S3':''};yes('whole legacy writer output exact '+str(i),old.记(a,raw)==new.记(b,raw)and a==b)
 d=copy.deepcopy(data);d['分段增益dB'].pop('S18');a=copy.deepcopy(d);b=copy.deepcopy(d);yes('valid spoken no needs-binding not added outside originalscope',not e['_speech_comma_spec'](d,'S18')['needs_mother_binding']and old.记(a,actual)==new.记(b,actual)and a==b)
 # CLI realdata case: current raw table from actual cachedwhole, no model/run/sound generation.
 W=root/'actual-work';(W/'scripts').mkdir(parents=True);(W/'work_24').mkdir();(W/'scripts/24.json').write_bytes(source.read_bytes());(W/'work_24/句子声音指纹.json').write_text(json.dumps({'指纹':actual,'作废':[]},ensure_ascii=False));rr=subprocess.run([sys.executable,str(newT/'区间作废.py'),'24','--记指纹'],cwd=W,text=True,capture_output=True);yes('real stdlib CLI only actual data writes13 and e437',rr.returncode==0 and json.loads((W/'scripts/24.json').read_text())['区间声音指纹']==data['区间声音指纹']);(D/'A45-CANDIDATE-STDLIB-CLI-REAL-DATA-STDOUT.log').write_text(rr.stdout+rr.stderr)
result={'kind':'actual-original-maker-pure-A45-and-new-writer-data-only-positive-negative-and-legacy-proof','passed':True,'test_count':len(checks),'checks':checks,'actual_cause':sp(CAUSE),'actual_source':sp(source),'actual_failed_source':sp(failed),'actual_rawtable_measurement':sp(measurement),'unchanged_actual_maker':sp(maker),'candidate':sp(C),'original':sp(O),'original_pure_A45_AST':{n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()for n in nodes if isinstance(n,ast.FunctionDef)},'unmodified_originalselftest_log':sp(D/'A45-UNCHANGED-ORIGINAL-SELFTEST-LEGACY-STDOUT.log'),'new_stdlib_CLI_log':sp(D/'A45-CANDIDATE-STDLIB-CLI-REAL-DATA-STDOUT.log'),'no_models_TTS_G36_GT_ASR_audio_or_native_or_certification_run':True,'quality_acceptance':False};p=D/'ACTUAL-ORIGINAL-A45-AND-WRITER-REAL-DATA-NEGATIVES-LEGACY-SELFTEST-PROOF.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'tests':len(checks),'proof':sp(p)},indent=2))
