"""Post-only user051 tail export from each true full-QA-passed new body."""
from pathlib import Path
from fractions import Fraction
import argparse,copy,hashlib,importlib.util,inspect,json,os,shutil,subprocess,sys,tempfile
H=Path(__file__).resolve().parent;B=H.parent
LOCAL=Path('/workspace/work/github-publication/target')
MODULE=Path('/workspace/work/video-revision-batch-ci/.github/video-batch/run.py')
POLICY=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-051.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
parser=argparse.ArgumentParser();parser.add_argument('article');parser.add_argument('--output-root',type=Path,default=H/'actual-post-only');a=parser.parse_args();no=a.article.zfill(2)
P=load('normal18_source_transform',H/'final_hold18.py');assert no in P.FINAL_IDS;assert sha(POLICY)==P.POLICY_SHA256
index=json.loads(Path('/workspace/work/video-revision-delivery/hold18-intake-preparation-20261114/normal11-actual-sources-and-accepted-voice-bases.json').read_text())
row=next(x for x in index['rows'] if x['source_id']==no);hand=Path(row['latest_actual_accepted_handoff']['path']);assert sha(hand)==row['latest_actual_accepted_handoff']['sha256']
run=int(hand.parents[1].name);parent=B/f'next-passed-native/{run}/{no}'
folders=[parent/'artifact-files',parent/'files'];ART=next(x for x in folders if (x/f'{no}-canonical-summary-passed-status.json').is_file())
SOURCE=next(ART.glob(f'{no}-4K-读完即转简述2秒.mp4'))
SOURCE_JSON=ART/f'{no}-actual-working-source.json';REQUEST=ART/f'{no}-request-source.json'
T0=ART/f'{no}-summary-verification.json';S0=ART/f'{no}-canonical-summary-passed-status.json'
timing0=json.loads(T0.read_text());status0=json.loads(S0.read_text());assert sha(SOURCE)==timing0['video_sha256']==status0['video_sha256'];assert status0['passed'] and status0['canonical_pipeline_passed']
assert status0.get('preview_only',False) is False
latest=Path(row['latest_actual_accepted_mp4']['path']);assert sha(latest)==row['latest_actual_accepted_mp4']['sha256']
reader=load('existing_audio_packet_reader',Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/illustrated_tail.py'))
source_a=reader.packets(SOURCE,'a:0',payload=True);assert source_a==reader.packets(latest,'a:0',payload=True)
P.pinned_module(MODULE);batch=load('actual_normal18_endcard_'+no,MODULE);body=inspect.getsource(batch.end_card);tests=P.selftest(body);body=P.patch_end_card_source(body,no,18);batch.Fraction=Fraction
DATA=json.loads(SOURCE_JSON.read_text());note=DATA['sentences'][-1]['chunks'][-1]['note'];text=note[note.index('（简述：'):];assert text.count('▸')==5
batch.summary=lambda n:text
batch.render_card=lambda n,data,width,height,dest:(shutil.copyfile(ART/f'{no}-简述.png',dest),copy.deepcopy(timing0['layout']))[1]
batch.BASE=subprocess.check_output(['git','rev-parse','HEAD'],cwd=LOCAL,text=True).strip();batch.PICTURE_REFERENCES={}
OUT=a.output_root/no;OUT.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='normal18-'+no+'-',dir='/dev/shm') as td:
 td=Path(td);tools=td/'toolroot/视频/工具';tools.mkdir(parents=True)
 for n in ['render.py','make_video.py']:(tools/n).symlink_to(B/'final-layout/official'/n)
 (tools/'fonts').symlink_to(B/'final-layout/fonts',target_is_directory=True)
 batch.ROOT=td/'toolroot';batch.OUT=td/'output';batch.OUT.mkdir();batch.LOCAL_SOURCE=str(SOURCE);batch.LOCAL_SCRIPT=copy.deepcopy(DATA)
 lo=body.index('    paths = tree_paths()');hi=body.index('    info = probe(source)')
 loader=("    originals = [f'actual-new-canonical-body-inherited-native:{no}']\n    source = OUT / f'{no}-original.mp4'\n    source.write_bytes(Path(LOCAL_SOURCE).read_bytes())\n    data = copy.deepcopy(LOCAL_SCRIPT)\n    changed = add_summary(data, no)\n")
 body=body[:lo]+loader+body[hi:];exec(compile(body,str(MODULE)+'#user051-normal18-post-only','exec'),batch.__dict__)
 os.environ['RUNNER_TEMP']=str(td/'renderer-cache');os.chdir(LOCAL);batch.end_card(no)
 movie,=batch.OUT.glob('*.mp4');timing=json.loads((batch.OUT/f'{no}-verification.json').read_text());assert timing['source_voice_endpoint_seconds']==timing0['source_voice_endpoint_seconds'];assert timing['summary_start_frame']==timing['unheld_voice_ceiling_frame']+18
 assert timing['last_body_hold_frames']==18 and timing['preview_only'] is False
 assert timing['original_audio_identical'] and timing['original_audio_packet_timings_identical'];assert reader.packets(movie,'a:0',payload=True)==source_a
 dest=OUT/f'{no}-4K-末句后停0.6秒-简述2秒-private-upstream.mp4';shutil.copyfile(movie,dest)
 for p in batch.OUT.glob('*'):
  if p.suffix in ('.json','.png'):shutil.copyfile(p,OUT/p.name)
 timing.update(source_kind='new-canonical-4K',canonical_source_video_sha256=timing0['canonical_source_video_sha256'],canonical_pipeline_passed=True,postprocessing_only=True,inherited_true_native_full_QA_run=run,final_hold_policy_sha256=P.POLICY_SHA256)
 (OUT/f'{no}-summary-verification.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2)+'\n')
 status=copy.deepcopy(status0);status.update(passed=True,stage='final4K-passed',video_sha256=sha(dest),preview_only=False,finalization_authorized=True,last_body_hold_frames=18,last_body_hold_seconds=.6,summary_start_seconds=timing['summary_start_seconds'],summary_start_frame=timing['summary_start_frame'],delay_after_voice_seconds=timing['delay_after_voice_seconds'],postprocessing_only=True,original_producer_or_TTS_repeated=False,true_original_native_full_QA_run=run,inherited_original_summary_status_sha256=sha(S0),final_hold_policy_sha256=P.POLICY_SHA256)
 (OUT/f'{no}-upstream-summary-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
 record=dict(article=no,kind='honest-post-only-normal18-upstream',source_native_run=run,new_native_generated=False,postprocessing_only=True,source_video=str(SOURCE),source_video_sha256=sha(SOURCE),inherited_passed_handoff=str(hand),inherited_passed_handoff_sha256=sha(hand),original_status=str(S0),original_status_sha256=sha(S0),original_timing=str(T0),original_timing_sha256=sha(T0),request=str(REQUEST),actual_working_source=str(SOURCE_JSON),actual_output_file=str(dest),actual_output_sha256=sha(dest),actual_gap_seconds=timing['delay_after_voice_seconds'],all_audio_packet_payload_side_data_absolute_clock_exact=True,actual_audio_packet_count=len(source_a),policy_sha256=P.POLICY_SHA256,scope_tests=tests)
 (OUT/f'{no}-post-only-normal18-upstream-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record,ensure_ascii=False),flush=True)
