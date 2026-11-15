"""Exact already-exported source35/book54 public master IO; no audio production."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat

PINS = {'final_H': {'path': '/workspace/work/review35-finalV3/43741796325-normal18/archive-handoff.json', 'bytes': 96811, 'sha256': '478962d68b9959caea78f72ab053e31590f3d7cb9a5fe4c4db2f91827fb09873'}, 'sourceQA_H': {'path': '/workspace/work/review35-sourceQA/43741796325/archive-handoff.json', 'bytes': 80707, 'sha256': '6cfc749c60ea7fb680cd0f3f712810a7b7b5eab3349fb54f850501cfa2b2e0f3'}, 'master_WAV': {'path': '/workspace/work/review35-sourceQA/43741796325/actual-original-program-master-export/35-original-program-master-pre-video-AF.wav', 'bytes': 6882284, 'sha256': '8de7327875c72f9cb5f91ec94a08a88af8c2e881ea6046bda57c8a3f0c53cd90'}, 'export_evidence': {'path': '/workspace/work/review35-sourceQA/43741796325/actual-original-program-master-export/35-original-program-master-export.json', 'bytes': 1606, 'sha256': '1f4a6477143cfb9f00faff010091089560a1f6b0c0f6f217edda8a8825616abf'}, 'native_status': {'path': '/workspace/work/review35-sourceQA/43741796325/actual-original-program-master-export/35-status.json', 'bytes': 162367, 'sha256': 'aeb7525266d6203958296966f3cf4104b9177d7a814a687eee54a1b058c4dc4f'}, 'HOST_binding': {'path': '/workspace/work/review35-sourceQA/43741796325/actual-original-program-master-export/actual-HOST-master-role-binding.json', 'bytes': 3439, 'sha256': '17866719d523b38f89c7cc0e15816fb9b32437fd607e34d1f9f144d2c35e05be'}, 'standalone_H': {'path': '/workspace/work/book54-source35-actual43741796325-original-HOST-preparation-20261115/BOOK54-SOURCE35-ACTUAL-NATIVE-SOURCEQA-AND-ORIGINAL-NORMAL18-FINALV3-ROOT-AND-SOLE-WRITER-HANDOFF.json', 'bytes': 22550, 'sha256': 'd011453c5cc5e9cfd31a0b9c2d919a72e47f2992a86d1874e2ce56d95b76ad8d'}, 'b00_authority': {'path': '/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json', 'bytes': 2088, 'sha256': 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}, 'original_PCM_reader': {'path': '/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py', 'bytes': 9748, 'sha256': 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'}, 'approved_IO_binder': {'path': '/workspace/work/book54-source35-actual43741796325-original-HOST-preparation-20261115/master-IO-code/bind_actual_exported_master.py', 'bytes': 7408, 'sha256': 'b808e278c1b17cf64c8851e36c545095d5a84d91d6881dfdb309a92cf16c21e1'}}
SID, NID, RUN = '35', '54', 43741796325
RAW = '8de7327875c72f9cb5f91ec94a08a88af8c2e881ea6046bda57c8a3f0c53cd90'
NATIVE_VIDEO = '0cb758923f2660274b8a18f5228c9bec8d985e59d285122acf88f79b37452b36'
FINAL_VIDEO = 'b44489f1bd20cdcdd6bfd1484ca1676f088577567aa0fbe1eca8f8f3bf38bf0d'
FORMAT = {'container':'WAV','encoding':'PCM','sample_width_bytes':2,
          'bits_per_sample':16,'channels':1,'sample_rate':24000,
          'frames':3441120,'duration_seconds':143.38}
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
    original = module_from_pin('source35_original_PCM_reader', 'original_PCM_reader')
    original._regular(path)
    with Path(path).open('rb') as stream:
        actual = original._pcm_format(stream)
    assert actual == FORMAT
    return actual


def validate_records(native, evidence):
    original = module_from_pin('source35_approved_export_IO_binder', 'approved_IO_binder')
    master = original.validate_records(SID, RUN, native, evidence)
    assert native['final_wav_sha256'] == master['sha256'] == RAW
    assert master['bytes'] == 6882284 and master['format'] == FORMAT
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
        assert row['bytes'] == 6882284 and row['sha256'] == RAW
        result[str(Path(row['path']).resolve())] = {key:row[key] for key in ('path','bytes','sha256')}
    return result


def check(path, approved):
    p = Path(path)
    assert not p.is_symlink() and p.suffix.lower() == '.wav'
    assert str(p.resolve()) in approved
    row = approved[str(p.resolve())]
    assert row['bytes'] == 6882284 and row['sha256'] == RAW
    assert checked(row) == p.resolve()
    validated_actual_master()


def standalone_assets():
    validated_actual_master()
    return [PINS[key] for key in ('master_WAV','export_evidence','HOST_binding','b00_authority')]
