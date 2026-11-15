"""Exact already-exported source70/book50 public master IO; no audio production."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat

PINS = {'final_H': {'path': '/workspace/work/review70-finalV3/43728728741-normal18/archive-handoff.json', 'bytes': 74414, 'sha256': '9b7de7262eaa8dcb8f91abfb323cab92829d10a603df42eaf6c2b5fc7cf36758'}, 'sourceQA_H': {'path': '/workspace/work/review70-sourceQA/43728728741/archive-handoff.json', 'bytes': 58786, 'sha256': 'a48b67796ff5feef56575c13b163f8cddf0402fe4f8a5e9f746b73d7f44ca9d5'}, 'master_WAV': {'path': '/workspace/work/review70-sourceQA/43728728741/actual-original-program-master-export/70-original-program-master-pre-video-AF.wav', 'bytes': 6739004, 'sha256': '950829b17bedc5ac103b93bb9b488a712163800bbf5c392bf1163b381cd61f34'}, 'export_evidence': {'path': '/workspace/work/review70-sourceQA/43728728741/actual-original-program-master-export/70-original-program-master-export.json', 'bytes': 1607, 'sha256': '2d81a706c495244c8233e8f91864d7a0911b851b94122f7546c3a22f70d8bb8e'}, 'native_status': {'path': '/workspace/work/review70-sourceQA/43728728741/actual-original-program-master-export/70-status.json', 'bytes': 163405, 'sha256': 'c48ab25d24a236d8a34f527fa89a06138f9d41983c008c6f572c098421bb9f39'}, 'HOST_binding': {'path': '/workspace/work/review70-sourceQA/43728728741/actual-original-program-master-export/actual-HOST-master-role-binding.json', 'bytes': 3451, 'sha256': '46609e3155859a47667c6c54dafda599202067b47550571c3a587b0fabf13ad6'}, 'standalone_H': {'path': '/workspace/work/book50-source70-actual43728728741-original-HOST-preparation-20261115/BOOK50-SOURCE70-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json', 'bytes': 15143, 'sha256': '400549705274869b3ec1fb883c376b39d4759d7971bc108bde6af3841cb6e28c'}, 'b00_authority': {'path': '/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json', 'bytes': 2088, 'sha256': 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}, 'original_PCM_reader': {'path': '/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py', 'bytes': 9748, 'sha256': 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'}, 'approved_IO_binder': {'path': '/workspace/work/actual-exported-master-WAV-sourceQA-role-binding-CODE-ONLY-20261115/bind_actual_exported_master.py', 'bytes': 7389, 'sha256': 'ae19dae189e42f1787ef214a26d7baa5f329e21d9eea0f2513f469eb9fb50679'}}
SID, NID, RUN = '70', '50', 43728728741
RAW = '950829b17bedc5ac103b93bb9b488a712163800bbf5c392bf1163b381cd61f34'
NATIVE_VIDEO = 'ea6464fe8769af8758e7c4956ef0361ff07c0c2f46e59d353c5cd9ab7d5a24d5'
FINAL_VIDEO = 'b4f8f6123e100ebbc1252de834f8d18f1e85db4719de89415d596b81614c0f79'
FORMAT = {'container':'WAV','encoding':'PCM','sample_width_bytes':2,
          'bits_per_sample':16,'channels':1,'sample_rate':24000,
          'frames':3369480,'duration_seconds':140.395}
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
    original = module_from_pin('source70_original_PCM_reader', 'original_PCM_reader')
    original._regular(path)
    with Path(path).open('rb') as stream:
        actual = original._pcm_format(stream)
    assert actual == FORMAT
    return actual


def validate_records(native, evidence):
    original = module_from_pin('source70_approved_export_IO_binder', 'approved_IO_binder')
    master = original.validate_records(SID, RUN, native, evidence)
    assert native['final_wav_sha256'] == master['sha256'] == RAW
    assert master['bytes'] == 6739004 and master['format'] == FORMAT
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
        assert row['bytes'] == 6739004 and row['sha256'] == RAW
        result[str(Path(row['path']).resolve())] = {key:row[key] for key in ('path','bytes','sha256')}
    return result


def check(path, approved):
    p = Path(path)
    assert not p.is_symlink() and p.suffix.lower() == '.wav'
    assert str(p.resolve()) in approved
    row = approved[str(p.resolve())]
    assert row['bytes'] == 6739004 and row['sha256'] == RAW
    assert checked(row) == p.resolve()
    validated_actual_master()


def standalone_assets():
    validated_actual_master()
    return [PINS[key] for key in ('master_WAV','export_evidence','HOST_binding','b00_authority')]
