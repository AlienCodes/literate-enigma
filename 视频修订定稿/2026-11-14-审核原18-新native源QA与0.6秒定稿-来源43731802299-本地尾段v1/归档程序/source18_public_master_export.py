"""Exact already-exported source18/book64 public master IO; no audio production."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat

PINS = {'final_H': {'path': '/workspace/work/review18-finalV3/43731802299-normal18/archive-handoff.json', 'bytes': 75173, 'sha256': '1146e58a20d50f0496291064fbe0574fada14a7e52e774adb264d7a0879a9996'}, 'sourceQA_H': {'path': '/workspace/work/review18-sourceQA/43731802299/archive-handoff.json', 'bytes': 59458, 'sha256': '84f44dd8feccb1eb8a7dfd8adbb6b06371721f5781d31eda3b08144e89d8fa68'}, 'master_WAV': {'path': '/workspace/work/review18-sourceQA/43731802299/actual-original-program-master-export/18-original-program-master-pre-video-AF.wav', 'bytes': 7275164, 'sha256': '916e594a32542618c6d5321f88fadc482adb4d3a6dabf3472cebc53f55c0d088'}, 'export_evidence': {'path': '/workspace/work/review18-sourceQA/43731802299/actual-original-program-master-export/18-original-program-master-export.json', 'bytes': 1607, 'sha256': 'd10b9713918ae092431a2027f7d2598139f08a3ac2016ca64baf6d104598a4d3'}, 'native_status': {'path': '/workspace/work/review18-sourceQA/43731802299/actual-original-program-master-export/18-status.json', 'bytes': 269072, 'sha256': 'd81371cc37633dab8fa0df984d2bd732ea969efb87edc95b218daf2d71a7cef7'}, 'HOST_binding': {'path': '/workspace/work/review18-sourceQA/43731802299/actual-original-program-master-export/actual-HOST-master-role-binding.json', 'bytes': 3451, 'sha256': '6ecb224ffddfb5817f761b0efbaf7ee3103b02ff824be9a6737469be5d4a5cb9'}, 'standalone_H': {'path': '/workspace/work/book64-source18-actual43731802299-original-HOST-preparation-20261115/BOOK64-SOURCE18-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json', 'bytes': 15158, 'sha256': '1749def2b6ab466859c195c514f7e0ceb8663cee2775df242d095f3a5523b250'}, 'b00_authority': {'path': '/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json', 'bytes': 2088, 'sha256': 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}, 'original_PCM_reader': {'path': '/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py', 'bytes': 9748, 'sha256': 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'}, 'approved_IO_binder': {'path': '/workspace/work/book64-source18-actual43731802299-original-HOST-preparation-20261115/bind_actual_exported_master_exact18.py', 'bytes': 7408, 'sha256': 'dcbca51d9ad19f8f84dd3099c5cba7fbb6f328c317a052e70bb7cc98785dfbdd'}}
SID, NID, RUN = '18', '64', 43731802299
RAW = '916e594a32542618c6d5321f88fadc482adb4d3a6dabf3472cebc53f55c0d088'
NATIVE_VIDEO = '6b4320c290e5d82112ab379434aee883fc1d637b83ae1b0062bbe91ece8873f0'
FINAL_VIDEO = 'b30f64bdddac235acb6676ee118a0f55e99678a100190d08f7e48a4d2e1a2e34'
FORMAT = {'container':'WAV','encoding':'PCM','sample_width_bytes':2,
          'bits_per_sample':16,'channels':1,'sample_rate':24000,
          'frames':3637560,'duration_seconds':151.565}
REPORT = Path(PINS['HOST_binding']['path'])
REPORT_SHA = PINS['HOST_binding']['sha256']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def checked(row):
    p = Path(row['path'])
    assert p.resolve(strict=True) == p and not p.is_symlink()
    assert stat.S_ISREG(p.lstat().st_mode) and p.stat().st_size == row['bytes']
    assert digest(p) == row['sha256']
    return p


def module_from_pin(name, key):
    p = checked(PINS[key])
    definition = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    return module


def exact_format(path):
    original = module_from_pin('source18_original_PCM_reader', 'original_PCM_reader')
    original._regular(path)
    with Path(path).open('rb') as stream:
        actual = original._pcm_format(stream)
    assert actual == FORMAT
    return actual


def validate_records(native, evidence):
    original = module_from_pin('source18_approved_export_IO_binder', 'approved_IO_binder')
    master = original.validate_records(SID, RUN, native, evidence)
    assert native['final_wav_sha256'] == master['sha256'] == RAW
    assert master['bytes'] == 7275164 and master['format'] == FORMAT
    assert master['final_video_sha256'] == native['video_sha256'] == NATIVE_VIDEO
    assert master['authority']['sha256'] == PINS['b00_authority']['sha256']
    return master


def validated_actual_master():
    native = json.loads(checked(PINS['native_status']).read_text())
    evidence = json.loads(checked(PINS['export_evidence']).read_text())
    validate_records(native, evidence)
    auth = json.loads(checked(PINS['b00_authority']).read_text())
    assert auth['author'] == 'user'
    assert 'project_master_WAV_MP3_and_actual_target_mother_audio' in auth['authorized_project_output_roles']
    wav = checked(PINS['master_WAV'])
    assert wav.name == SID + '-original-program-master-pre-video-AF.wav'
    assert digest(wav) == RAW and exact_format(wav) == FORMAT
    checked(PINS['HOST_binding'])
    checked(PINS['standalone_H'])


def allowed(sid, nid, handoff, handoff_path):
    assert (sid, nid) == (SID, NID)
    assert Path(handoff_path).resolve() == Path(PINS['final_H']['path'])
    assert checked(PINS['final_H']) == Path(handoff_path).resolve()
    assert handoff == json.loads(Path(handoff_path).read_text())
    assert handoff['source_run'] == RUN
    assert handoff['current_source_validation_handoff'] == PINS['sourceQA_H']
    source = json.loads(checked(PINS['sourceQA_H']).read_text())
    assert source['source_run'] == RUN and len(source['articles']) == 1
    assert source['articles'][0]['source_id'] == SID and source['articles'][0]['passed_per_article'] is True
    assert len(handoff['articles']) == 1
    assert handoff['articles'][0]['source_id'] == SID and handoff['articles'][0]['new_id'] == NID
    assert handoff['articles'][0]['final_mp4']['sha256'] == FINAL_VIDEO
    validated_actual_master()
    result = {PINS['master_WAV']['path']: PINS['master_WAV']}
    for row in source['validation_files'] + handoff['validation_files']:
        if Path(row['path']).suffix.lower() != '.wav':
            continue
        assert Path(row['path']).name == SID + '-original-program-master-pre-video-AF.wav'
        assert row['bytes'] == 7275164 and row['sha256'] == RAW
        result[str(Path(row['path']).resolve())] = {key:row[key] for key in ('path','bytes','sha256')}
    return result


def check(path, approved):
    p = Path(path)
    assert not p.is_symlink() and p.suffix.lower() == '.wav'
    assert str(p.resolve()) in approved
    row = approved[str(p.resolve())]
    assert row['bytes'] == 7275164 and row['sha256'] == RAW
    assert checked(row) == p.resolve()
    validated_actual_master()


def standalone_assets():
    validated_actual_master()
    return [PINS[key] for key in ('master_WAV','export_evidence','HOST_binding','b00_authority')]
