"""Exact already-exported source58/book67 public master IO; no audio production."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat

PINS = {'final_H': {'path': '/workspace/work/review58-finalV3/43736478355-normal18/archive-handoff.json', 'bytes': 76510, 'sha256': '4c833c5b9581e4974fd28a92658711578219989ca9092c60b531ce215572fe82'}, 'sourceQA_H': {'path': '/workspace/work/review58-sourceQA/43736478355/archive-handoff.json', 'bytes': 60823, 'sha256': '1bd4de3cccb5939fcad09e4022f3f252d84a1c39188842f1aefea43d4e674dca'}, 'master_WAV': {'path': '/workspace/work/review58-sourceQA/43736478355/actual-original-program-master-export/58-original-program-master-pre-video-AF.wav', 'bytes': 7540124, 'sha256': '3bfba6a7aff011312ee82fca359ec69947aef371a05abc56c42dbf45918bf5d5'}, 'export_evidence': {'path': '/workspace/work/review58-sourceQA/43736478355/actual-original-program-master-export/58-original-program-master-export.json', 'bytes': 1607, 'sha256': '262a4e86c087357da858d8c40f6bb5b539ad781c443ebe3a8f20f9f380d3077b'}, 'native_status': {'path': '/workspace/work/review58-sourceQA/43736478355/actual-original-program-master-export/58-status.json', 'bytes': 173827, 'sha256': '9cf6b05bdfc29c31068806269899a63bc6b785098f5582f0dd2b8b6a72c3a423'}, 'HOST_binding': {'path': '/workspace/work/review58-sourceQA/43736478355/actual-original-program-master-export/actual-HOST-master-role-binding.json', 'bytes': 3451, 'sha256': '0bb560206c940c64809ee6b6fed651990bf63cdc0fc7708805d61206137683a7'}, 'standalone_H': {'path': '/workspace/work/book67-source58-actual43736478355-original-HOST-preparation-20261115/BOOK67-SOURCE58-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json', 'bytes': 13174, 'sha256': '2635ee14fc08912c98d77e4373f54b13b9efbd1f0a9ee3c2f11d7f539160e199'}, 'b00_authority': {'path': '/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json', 'bytes': 2088, 'sha256': 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}, 'original_PCM_reader': {'path': '/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py', 'bytes': 9748, 'sha256': 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'}, 'approved_IO_binder': {'path': '/workspace/work/book67-source58-actual43736478355-original-HOST-preparation-20261115/bind_actual_exported_master_exact58.py', 'bytes': 7408, 'sha256': '2c628080368534fae2987d1e01ddc4e4160b64807ebdc409d1afec0205fcb9b9'}}
SID, NID, RUN = '58', '67', 43736478355
RAW = '3bfba6a7aff011312ee82fca359ec69947aef371a05abc56c42dbf45918bf5d5'
NATIVE_VIDEO = '18a5016a3d9264f4908160498cac2779f81d17490934f89a66a50ac4ed6b9671'
FINAL_VIDEO = '55b0450125e66dc5d79249405aaf6bea6bc1f114b7ee689d6c9b3698b048f1ee'
FORMAT = {'container':'WAV','encoding':'PCM','sample_width_bytes':2,
          'bits_per_sample':16,'channels':1,'sample_rate':24000,
          'frames':3770040,'duration_seconds':157.085}
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
    original = module_from_pin('source58_original_PCM_reader', 'original_PCM_reader')
    original._regular(path)
    with Path(path).open('rb') as stream:
        actual = original._pcm_format(stream)
    assert actual == FORMAT
    return actual


def validate_records(native, evidence):
    original = module_from_pin('source58_approved_export_IO_binder', 'approved_IO_binder')
    master = original.validate_records(SID, RUN, native, evidence)
    assert native['final_wav_sha256'] == master['sha256'] == RAW
    assert master['bytes'] == 7540124 and master['format'] == FORMAT
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
        assert row['bytes'] == 7540124 and row['sha256'] == RAW
        result[str(Path(row['path']).resolve())] = {key:row[key] for key in ('path','bytes','sha256')}
    return result


def check(path, approved):
    p = Path(path)
    assert not p.is_symlink() and p.suffix.lower() == '.wav'
    assert str(p.resolve()) in approved
    row = approved[str(p.resolve())]
    assert row['bytes'] == 7540124 and row['sha256'] == RAW
    assert checked(row) == p.resolve()
    validated_actual_master()


def standalone_assets():
    validated_actual_master()
    return [PINS[key] for key in ('master_WAV','export_evidence','HOST_binding','b00_authority')]
