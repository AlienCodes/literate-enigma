"""Physical test on a real previously passed28 movie; never a new final verdict."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile

H = Path(__file__).resolve().parent
ORIGINAL_H = H.parent
B = ORIGINAL_H.parent
LOCAL = Path('/workspace/work/github-publication/target')
MODULE = Path('/workspace/work/video-revision-batch-ci/.github/video-batch/run.py')
ARTIFACTS = B/'next-preview-native/43576642418/28/artifact-files'
SOURCE = ARTIFACTS/'28-4K-效果审核-末句后停9帧-简述2秒.mp4'
ORIGINAL_TIMING = json.loads((ARTIFACTS/'28-summary-verification.json').read_text())
ORIGINAL_STATUS = json.loads((ARTIFACTS/'28-canonical-summary-passed-status.json').read_text())
SOURCE_JSON = ARTIFACTS/'28-actual-working-source.json'
OUT = H/'upstream'
OUT.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


P = load('user28_scope_transform', H/'preview28_hold18.py')
P.pinned_module(MODULE)
assert sha(SOURCE) == ORIGINAL_TIMING['video_sha256'] == ORIGINAL_STATUS['video_sha256']
assert ORIGINAL_STATUS['passed'] and ORIGINAL_STATUS['canonical_pipeline_passed']
assert ORIGINAL_TIMING['kind'] == 'preview-last-body-hold9-then-summary60'
batch = load('unchanged_original_end_card_for28_physical_test', MODULE)
body = inspect.getsource(batch.end_card)
scope_test = P.selftest(body)
body = P.patch_end_card_source(body, '28', 18)
data = json.loads(SOURCE_JSON.read_text())
note = data['sentences'][-1]['chunks'][-1]['note']
text = note[note.index('（简述：'):]
assert text.count('▸') == 5
batch.summary = lambda no: text
def reuse_original_approved_summary(no, data, width, height, destination):
    assert no == '28' and (width,height) == (3840,2160)
    shutil.copyfile(ARTIFACTS/'28-简述.png', destination)
    return copy.deepcopy(ORIGINAL_TIMING['layout'])
batch.render_card = reuse_original_approved_summary
batch.BASE = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=LOCAL, text=True).strip()
batch.PICTURE_REFERENCES = {}
with tempfile.TemporaryDirectory(prefix='real28-hold18-', dir='/dev/shm') as td:
    td = Path(td)
    toy = td/'readonly-tool-root'
    tools = toy/'视频/工具'
    tools.mkdir(parents=True)
    for name in ['render.py', 'make_video.py']:
        (tools/name).symlink_to(B/'final-layout/official'/name)
    (tools/'fonts').symlink_to(B/'final-layout/fonts', target_is_directory=True)
    batch.ROOT = toy
    batch.OUT = td/'physical-output'
    batch.OUT.mkdir()
    batch.LOCAL_SOURCE = str(SOURCE)
    batch.LOCAL_SCRIPT = copy.deepcopy(data)
    lo = body.index('    paths = tree_paths()')
    hi = body.index('    info = probe(source)')
    loader = ("    originals = [f'real-previously-passed28-physical-validation:{no}']\n"
              "    source = OUT / f'{no}-original.mp4'\n"
              "    source.write_bytes(Path(LOCAL_SOURCE).read_bytes())\n"
              "    data = copy.deepcopy(LOCAL_SCRIPT)\n"
              "    changed = add_summary(data, no)\n")
    body = body[:lo] + loader + body[hi:]
    exec(compile(body, str(MODULE)+'#only28-hold18-post-only', 'exec'), batch.__dict__)
    os.environ['RUNNER_TEMP'] = str(td/'renderer-cache')
    os.chdir(LOCAL)
    batch.end_card('28')
    movies = list(batch.OUT.glob('*.mp4'))
    assert len(movies) == 1, movies
    timing = json.loads((batch.OUT/'28-verification.json').read_text())
    assert timing['source_voice_endpoint_seconds'] == 157.33
    assert timing['unheld_voice_ceiling_frame'] == 4720
    assert timing['summary_start_frame'] == 4738
    assert .6 <= timing['delay_after_voice_seconds'] < 19/30
    assert timing['preview_only'] and timing['preview_last_body_hold_frames'] == 18
    assert timing['original_audio_identical'] and timing['original_audio_packet_timings_identical']
    helper = load('original_packet_reader_for_real28', Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/illustrated_tail.py'))
    old_a = helper.packets(SOURCE, 'a:0', payload=True)
    new_a = helper.packets(movies[0], 'a:0', payload=True)
    assert old_a == new_a
    destination = OUT/'28-new-requested-preview-hold18-then-summary60.mp4'
    shutil.copyfile(movies[0], destination)
    for path in batch.OUT.glob('*.json'):
        shutil.copyfile(path, OUT/path.name)
    for path in batch.OUT.glob('*.png'):
        shutil.copyfile(path, OUT/path.name)
    record = dict(article='28', diagnostic_only=False, native_new_requested_video_generated=False,
                  production_delivery_eligible=False, active_final_replaced=False,
                  real_prior_quality_passed_run=43576642418,
                  original_source_video_sha256=sha(SOURCE), original_source_JSON_sha256=sha(SOURCE_JSON),
                  original_end_card_module_sha256=sha(MODULE), scoped_transform_program_sha256=sha(H/'preview28_hold18.py'),
                  actual_output_file=str(destination), actual_output_sha256=sha(destination),
                  actual_voice_endpoint_seconds=157.33, illustration_target_frame_after_composition=4738,
                  actual_gap_seconds=timing['delay_after_voice_seconds'], cloned_final_body_frames=18,
                  all_audio_packet_payload_side_data_absolute_clock_exact=True,
                  actual_audio_packet_count=len(old_a),
                  audio_packet_records_sha256=hashlib.sha256(json.dumps(old_a, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                  original_builtin_end_card_checks_really_passed=True, scope_and_default_tests=scope_test,
                  actual_raw_verification_file=str(OUT/'28-verification.json'))
    (OUT/'28-current-new-body-hold18-upstream-verification.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    timing.update({'source_kind':'new-canonical-4K', 'canonical_source_video_sha256':ORIGINAL_TIMING['canonical_source_video_sha256'],
                   'canonical_pipeline_passed':True,'original_audio_identical':True,'original_audio_packet_timings_identical':True,
                   'postprocessing_only':True,'inherited_true_native_full_QA_run':43576642418})
    (OUT/'28-summary-verification.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2)+'\n')
    status=copy.deepcopy(ORIGINAL_STATUS)
    status.update({'passed':True,'stage':'final4K-passed','video_sha256':sha(destination),'preview_only':True,
                   'preview_last_body_hold_frames':18,'active_final_replacement_authorized':False,
                   'production_delivery_eligible':False,'delay_after_voice_seconds':timing['delay_after_voice_seconds'],
                   'postprocessing_only':True,'original_producer_or_TTS_repeated':False,
                   'true_original_native_full_QA_run':43576642418,
                   'inherited_original_summary_status_sha256':sha(ARTIFACTS/'28-canonical-summary-passed-status.json'),
                   'prior_hold9_input_video_sha256':sha(SOURCE)})
    (OUT/'28-upstream-summary-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(record, ensure_ascii=False))
