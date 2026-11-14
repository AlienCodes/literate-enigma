"""Read-only original reference/audit observer AFTER one authorized exact replay.

Does not build audio/video or infer any model. Root must explicitly adopt the
labels-only cached KT I/O adapter described here; original labels mathematics,
synth transformations and audit code bytes remain untouched. This is diagnostic,
never a source confirmation or a replacement for formal native/full-V3 gates.
Private GT/PCM stays in the private scratch directory, never in public artifacts.
"""
from pathlib import Path
import contextlib,hashlib,io,json,os,runpy,sys

SOURCE='0193cbd1859525690e12a470c517cce2f120a1054b204fcfa3c0c392c92abbd7'
WHOLE='295fd087864e9ffbd2ad63edddb2da5d10af818b960c8a030e1ccdbd5537c591'
RAW='57117316e44d9148513d4a63f80a9af5c6dca95f88258a4face5f11f075f5c11'
AAC='8024210e91b17be5e8d8935b03bbce2fe709fc563567becddf86b668461fc1de'
PROGRAMS={'独立复核/synth.py':'a0c9cad9ac953e68768470e8181f7e325c8ee8ff08ca57b68bbd136b99b83264',
 '独立复核/labels.py':'9dc510ac2d7f5ed3f0d5b666c10eea92f2f22c14a9e5681739b87cb376571c2d',
 '独立复核/audit.py':'bfe12dab6bec96c9b765faea286ae30a067589f6c5ef78461b21d12b955f1e22'}

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def observe(m,video_root,official_tools,source_path,whole_report_path,
            replay_canonical_m4a,private_qc_dir,public_scalar_dir,
            *,root_has_adopted_cached_labels_IO=False):
 assert root_has_adopted_cached_labels_IO is True, 'Diagnostic labels IO adapter needs exact root adoption.'
 M,T=Path(video_root).resolve(),Path(official_tools).resolve()
 source_path=Path(source_path);whole_report_path=Path(whole_report_path)
 private_qc_dir=Path(private_qc_dir);public_scalar_dir=Path(public_scalar_dir)
 assert sha(source_path)==SOURCE and sha(whole_report_path)==WHOLE
 source=json.loads(source_path.read_text());whole=json.loads(whole_report_path.read_text())
 assert whole['exact_scope_proved']and whole['errors']==[]
 assert os.environ.get('STRICT_CACHE')=='1'and os.environ.get('XG_NOPUSH')=='1'
 assert os.environ.get('AUDIO_ONLY')=='1'and not os.environ.get('OLD_IV_VOID')
 assert {name:sha(T/name)for name in PROGRAMS}==PROGRAMS
 assert sha(M/'video/make_video.py')==sha(T/'make_video.py')=='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
 assert m.PRON_WORDS['Yuan']=='juːˈɑːn'
 assert m._OLDF and sha(m._OLDF)=='91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
 assert m._CTX_PATH and sha(m._CTX_PATH)=='4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
 wav=M/'video/work_48/a.wav';assert sha(wav)==RAW
 assert hashlib.md5(wav.read_bytes()).hexdigest()[:12]=='3bf9427c6935'
 import subprocess
 adts=subprocess.check_output(['ffmpeg','-v','error','-i',str(replay_canonical_m4a),'-map','0:a:0','-c:a','copy','-f','adts','-'])
 assert hashlib.sha256(adts).hexdigest()==AAC
 assert sha(M/'video/scripts/48.json')==SOURCE
 assert not private_qc_dir.exists();private_qc_dir.mkdir(parents=True)
 assert not public_scalar_dir.exists();public_scalar_dir.mkdir(parents=True)
 cache=M/'tts/cache_tts';before={p.name:sha(p)for p in cache.iterdir()if p.is_file()}
 source_before=sha(source_path);normal_source_before=sha(M/'video/scripts/48.json')
 fades=M/'video/work_48/淡入淡出.json';segments=M/'video/work_48/分段.json'
 assert fades.is_file()and segments.is_file()
 auxiliary_before={str(p):sha(p)for p in (fades,segments)}
 report={'kind':'source48_original_fresh_GT_and_complete_report2_diagnostic_after_exact_cached_replay',
  'source_sha256':SOURCE,'actual_whole_report_sha256':WHOLE,'replay_RAW_sha256':RAW,
  'replay_AAC_ADTS_sha256':AAC,'root_adopted_labels_only_cached_IO':True,
  'no_new_TTS_or_G36_math_or_render':True,'source_or_CF_or_cut_or_threshold_written':False,
  'quality_acceptance':False,'formal_gates_not_replaced':True,
  'original_program_sha256':PROGRAMS,'programs_executed':[],'cached_label_entries':[]}
 oldenv={k:os.environ.get(k)for k in ('VIDEO_ROOT','QC_DIR')};oldargv=list(sys.argv)
 oldcwd=Path.cwd();oldpath=list(sys.path)
 def run_original(rel):
  program=T/rel;out=io.StringIO();sys.argv=[str(program),'48']
  with contextlib.redirect_stdout(out):runpy.run_path(str(program),run_name='__main__')
  text=out.getvalue();log=private_qc_dir/(Path(rel).stem+'-original.log');log.write_text(text)
  report['programs_executed'].append({'program':rel,'sha256':sha(program),'stdout_sha256':sha(log)})
 try:
  os.environ['VIDEO_ROOT']=str(M);os.environ['QC_DIR']=str(private_qc_dir)
  os.chdir(M/'video');sys.path.insert(0,str(M/'video'));sys.path.insert(0,str(M/'tts'))
  # Actual certified a0c original synth has no inference fallback: it validates
  # each raw create mother's original cache fingerprint/schema, then executes
  # its original independent donor/gain/fade transformations to fresh GT files.
  run_original('独立复核/synth.py')
  meta=json.loads((private_qc_dir/'gt/48_meta.json').read_text())
  assert len(meta)==18 and [x['idx']for x in meta]==[-1]+list(range(17))
  report['fresh_reference_scalar_identity']=[{'idx':x['idx'],'text':x['text'],
    'GT_file_sha256':sha(x['file']),'original_recorded_piece_gains':x.get('分段增益')}for x in meta]
  # Original labels.py directly constructs a KT model and would infer. Only its
  # construction-time I/O is redirected to the existing exact correct-context
  # timed-mother cache. Its char/timing/word-label algorithm is byte-exact and
  # labels are explicitly annotation-only, not part of numeric pass/fail.
  import kokoro_onnx
  klass=kokoro_onnx.Kokoro;descriptor=klass.__dict__['from_session']
  original_timed=m.KT.create_timed
  np=m.np
  class CachedTimedOnly:
   tokenizer=m.KT.tokenizer
   def create_timed(self,text,voice,speed=1.0,lang='en-us',**kw):
    captured=[]
    def capture(actual_text,voice,speed=1.0,lang='en-us',**actual_kw):
     mid=m._portable_mid(str(M/'tts/kokoro-v1.0-timed.onnx'))
     vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
     name=hashlib.sha1(repr(('create_timed',mid,actual_text,vh,float(speed),lang,sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
     path=cache/name;assert path.is_file(), 'DIAGNOSTIC_LABELS_CACHED_TIMED_KEY_MISSING '+name
     m._条目核对(str(path))
     captured.append({'name':name,'pkl_sha256':sha(path),'post_pron_input_sha256':hashlib.sha256(actual_text.encode()).hexdigest()})
    m._pron(capture)(text,voice=voice,speed=speed,lang=lang,**kw)
    assert len(captured)==1
    report['cached_label_entries'].append(captured[0])
    return original_timed(text,voice=voice,speed=speed,lang=lang,**kw)
  proxy=CachedTimedOnly()
  try:
   klass.from_session=classmethod(lambda cls,*a,**kw:proxy)
   run_original('独立复核/labels.py')
  finally:
   klass.from_session=descriptor
  labels=json.loads((private_qc_dir/'gt/48_labels.json').read_text())
  assert [r['idx']for r in labels]==[-1]+list(range(17))
  report['labels_IO_role']='Original labels arithmetic, actual correct-context cached timed reference; annotation only. No synthetic transcript or numeric acceptance rule.'
  # Full original meta remains18. audit's original default g over all raw GT
  # peaks is preserved; no single-sentence-local max or producer scale override.
  run_original('独立复核/audit.py')
  p=private_qc_dir/'report2_48.json';txt=private_qc_dir/'report2_48.txt'
  raw=json.loads(p.read_text());assert len(raw['texts'])==18
  report['original_audit_default_g']=raw['g']
  report['original_complete_report2_json_sha256']=sha(p)
  report['original_complete_report2_txt_sha256']=sha(txt)
  report['original_complete_report2_json']=str(p)
  report['original_complete_report2_txt']=str(txt)
  import shutil
  shutil.copyfile(p,public_scalar_dir/'report2_48.json')
  shutil.copyfile(txt,public_scalar_dir/'report2_48.txt')
  assert sha(public_scalar_dir/'report2_48.json')==sha(p)and sha(public_scalar_dir/'report2_48.txt')==sha(txt)
  report['only_original_report2_scalar_files_copied_no_GT_or_PCM']=True
  # Numeric rows below come directly from original report2, never a new gate.
  report['all_edit_rows']=[];report['actual_tail_or_onset_positive_rows']=[]
  report['actual_A10_edge_rows']=[]
  for tr in raw['texts']:
   for edit in tr['edits']:
    sid='标题'if tr['idx']==-1 else 'S'+str(tr['idx']+1)
    key=f"{sid} raw {edit['raw_k1']/24000:.4f}-{edit['raw_k2']/24000:.4f}"
    row={'original_idx':tr['idx'],'source_text':tr['text'],'raw_key':key,
      'original_edit':edit,'existing_old_CF':source.get('核对确认',{}).get('删除段',{}).get(key)}
    report['all_edit_rows'].append(row)
    if edit['tail_cut_ms']>0 or edit['onset_cut_ms']>0:report['actual_tail_or_onset_positive_rows'].append(row)
    if edit['edge_bad']:report['actual_A10_edge_rows'].append(row)
  report['original_extra_runs']=raw['extra_runs']
  report['report2_observation_completed']=True
 finally:
  for key,value in oldenv.items():
   if value is None:os.environ.pop(key,None)
   else:os.environ[key]=value
  sys.argv=oldargv;sys.path[:]=oldpath;os.chdir(oldcwd)
  after={p.name:sha(p)for p in cache.iterdir()if p.is_file()}
  report['all_private_TTS_cache_existing_exact']=before==after
  report['replay_RAW_exact_after']=sha(wav)==RAW
  report['source_exact_after']=sha(source_path)==source_before and sha(M/'video/scripts/48.json')==normal_source_before
  report['original_fades_and_piece_metadata_exact_after']=all(sha(p)==v for p,v in auxiliary_before.items())
  report['original_programs_exact_after']={name:sha(T/name)for name in PROGRAMS}==PROGRAMS
  dest=public_scalar_dir/'48-original-reference-report2-observation.json'
  dest.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
 assert report.get('report2_observation_completed')and report['all_private_TTS_cache_existing_exact']and report['source_exact_after']and report['replay_RAW_exact_after']
 return report
