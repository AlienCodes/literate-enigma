"""Post-only user051 export from this newly produced and actually QA-passed body; no prior delivery V3 is invented."""
from pathlib import Path
from fractions import Fraction
import argparse,copy,hashlib,importlib.util,inspect,json,os,shutil,subprocess,sys,tempfile
H=Path(__file__).resolve().parent;B=Path('/workspace/work/video-audit70-20261113')
LOCAL=Path('/workspace/work/github-publication/target')
MODULE=Path('/workspace/work/video-revision-batch-ci/.github/video-batch/run.py')
POLICY=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-051.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
parser=argparse.ArgumentParser();parser.add_argument('article');parser.add_argument('--native-root',required=True,type=Path);parser.add_argument('--native-run',required=True,type=int);parser.add_argument('--native-head',required=True);parser.add_argument('--output-root',type=Path,default=Path('/dev/shm/source31-user134-hold06-20261114/upstream'));a=parser.parse_args();no=a.article.zfill(2)
P=load('normal18_new_native_transform',H/'final_hold18.py');assert no == '31';assert sha(POLICY)==P.POLICY_SHA256
assert len(a.native_head)==40 and all(c in '0123456789abcdef' for c in a.native_head)
ART=a.native_root.resolve();run=a.native_run
native_status_path=ART/f'{no}-status.json';native_status=json.loads(native_status_path.read_text())
assert native_status['article']==no and native_status['passed'] is True and native_status['canonical_pipeline_passed'] is True
assert sha(native_status_path)=='ac4d7e0ee31163b5217272b4b6100c80532ce1220be6698b22c34ebfd1b50bab'
LEGACY_H=Path('/workspace/work/video-revision-delivery/next-passed-validated/43533004625/31/archive-handoff.json')
assert sha(LEGACY_H)=='9a461a42861364201f3b8b7eedb61522b2dfceebf46287299f33ad32fed730a9'
assert json.loads(LEGACY_H.read_text())['articles'][0]['passed_per_article'] is True
assert native_status['accepted_prior_aac_identical'] is True
assert native_status['accepted_source']['sha256']=='63c4068336b757a927b9908c55ddf6944d59c171965fd29e64fa4d6b66d89a1f'
assert native_status['canonical_aac_adts_sha256']=='aa28de85e8e2468cb82087e1748f42bb86b5ad8847cb254bded66cbc5792b2f6'
assert native_status['final_wav_sha256']=='b14e0444526fe4498cab5986b261bd8556d46fa1adf06f64c0da5c145cde7bc7'
AUTH134=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-134.json')
assert sha(AUTH134)=='19458a5fe4ba5dfdb3908c2708cb3859870b6cc44914725f17478071181f661c'
SOURCE=next(ART.glob(f'{no}-4K-读完即转简述2秒.mp4'))
SOURCE_JSON=ART/f'{no}-source.json';REQUEST=SOURCE_JSON
assert sha(REQUEST)=='894d5afa8daf71a68e71c46e89679c55150f9668894f84ad2df66336ca6480fb'
expected={'31':'894d5afa8daf71a68e71c46e89679c55150f9668894f84ad2df66336ca6480fb'}
assert sha(REQUEST)==expected[no]
latest=Path('/workspace/work/video-audit70-20261113/next-passed-native/43533004625/31/31-4K-正文后插图2秒-简述2秒.mp4')
hand=H/f'{no}-actual-native-full-QA-private-input-inheritance.json'
hand.write_text(json.dumps({'kind':'actual-current-native-full-QA-private-intermediate-inheritance','article':no,'repository':'AlienCodes/literate-enigma','actual_native_run':run,'actual_native_HEAD':a.native_head,'actual_native_status_sha256':sha(native_status_path),'actual_native_source_sha256':sha(REQUEST),'original_native_all_quality_passed':True,'inherited_existing_full_V3_handoff':'/workspace/work/video-revision-delivery/next-passed-validated/43533004625/31/archive-handoff.json','full_delivery_V3_prior_to_this_new_tail_claimed':True,'user051_final_delivery_still_requires_this_hold18_and_actual_final_V3':True},ensure_ascii=False,indent=2)+'\n')
T0=ART/f'{no}-summary-verification.json';S0=ART/f'{no}-status.json'
timing0=json.loads(T0.read_text());status0=json.loads(S0.read_text());assert sha(SOURCE)==timing0['video_sha256']==status0['video_sha256'];assert status0['passed'] and status0['canonical_pipeline_passed']
assert status0.get('preview_only',False) is False
assert sha(latest)=='b2fbdd7c71e778ddb3967cd018a47a072961288b9d89003db642f4cecd73b903'
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
 record=dict(article=no,kind='honest-post-only-normal18-upstream',source_native_run=run,new_native_generated=False,postprocessing_only=True,source_video=str(SOURCE),source_video_sha256=sha(SOURCE),inherited_actual_native_QA_record=str(hand),inherited_actual_native_QA_record_sha256=sha(hand),prior_full_delivery_V3_claimed=True,actual_native_HEAD=a.native_head,original_status=str(S0),original_status_sha256=sha(S0),original_timing=str(T0),original_timing_sha256=sha(T0),request=str(REQUEST),actual_working_source=str(SOURCE_JSON),actual_output_file=str(dest),actual_output_sha256=sha(dest),actual_gap_seconds=timing['delay_after_voice_seconds'],all_audio_packet_payload_side_data_absolute_clock_exact=True,actual_audio_packet_count=len(source_a),policy_sha256=P.POLICY_SHA256,scope_tests=tests)
 (OUT/f'{no}-post-only-normal18-upstream-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record,ensure_ascii=False),flush=True)
