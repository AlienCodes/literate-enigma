"""Exact already-exported source64/book63 public master IO; no audio production."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat

PINS = {'final_H': {'path': '/workspace/work/review64-finalV3/43728310644-normal18/archive-handoff.json', 'bytes': 64589, 'sha256': 'a573114f9deef6d042f25f53f21fd3b5c2b340bbc2758e912264fb2fce9faacb'}, 'sourceQA_H': {'path': '/workspace/work/review64-sourceQA/43728310644/archive-handoff.json', 'bytes': 49199, 'sha256': 'ea9000f12214411519bfc92a66c99fe7e6c91ee13ae95385fca5b4ce7aac3915'}, 'master_WAV': {'path': '/workspace/work/review64-sourceQA/43728310644/actual-original-program-master-export/64-original-program-master-pre-video-AF.wav', 'bytes': 7398524, 'sha256': 'c8bdfe9eebaecf45ef317d59b19572c64a2e755b5938dff1150421973b027f55'}, 'export_evidence': {'path': '/workspace/work/review64-sourceQA/43728310644/actual-original-program-master-export/64-original-program-master-export.json', 'bytes': 1607, 'sha256': 'e02a847317f93115f96f48fc5c3f0715240da96c0e22a49504b0fc993812c37a'}, 'native_status': {'path': '/workspace/work/review64-sourceQA/43728310644/actual-original-program-master-export/64-status.json', 'bytes': 178595, 'sha256': 'c010e990f4caef7d9c6a682a1cf26dd9b3d9cad2c387fda7cd6a8f85d8e2d0c0'}, 'HOST_binding': {'path': '/workspace/work/review64-sourceQA/43728310644/actual-original-program-master-export/actual-HOST-master-role-binding.json', 'bytes': 3451, 'sha256': '8e384c8159f53215a4a33174d878ac53f320b3eb772ea02d6c29e5ae1655bf2a'}, 'standalone_H': {'path': '/workspace/work/book63-source64-actual43728310644-original-HOST-preparation-20261115/BOOK63-SOURCE64-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json', 'bytes': 16030, 'sha256': 'a145cce8f9f444fec854f60342558008f987e9700c82f8f3286b7b6c9ea9c98e'}, 'b00_authority': {'path': '/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json', 'bytes': 2088, 'sha256': 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}, 'original_PCM_reader': {'path': '/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py', 'bytes': 9748, 'sha256': 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'}, 'approved_IO_binder': {'path': '/workspace/work/actual-exported-master-WAV-sourceQA-role-binding-CODE-ONLY-20261115/bind_actual_exported_master.py', 'bytes': 7389, 'sha256': 'ae19dae189e42f1787ef214a26d7baa5f329e21d9eea0f2513f469eb9fb50679'}}
SID, NID, RUN = '64', '63', 43728310644
RAW = 'c8bdfe9eebaecf45ef317d59b19572c64a2e755b5938dff1150421973b027f55'
NATIVE_VIDEO = '1f73706482e48dce65df0b31f2a098e14006f0a32c4dffebc4d5e543fd970da9'
FINAL_VIDEO = 'f0b058d5689c08f6f95d94610c26c725397e957b5f1ef170612a32b5d59d3b1f'
FORMAT = {'container':'WAV','encoding':'PCM','sample_width_bytes':2,
          'bits_per_sample':16,'channels':1,'sample_rate':24000,
          'frames':3699240,'duration_seconds':154.135}
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
    original = module_from_pin('source64_original_PCM_reader', 'original_PCM_reader')
    original._regular(path)
    with Path(path).open('rb') as stream:
        actual = original._pcm_format(stream)
    assert actual == FORMAT
    return actual


def validate_records(native, evidence):
    original = module_from_pin('source64_approved_export_IO_binder', 'approved_IO_binder')
    master = original.validate_records(SID, RUN, native, evidence)
    assert native['final_wav_sha256'] == master['sha256'] == RAW
    assert master['bytes'] == 7398524 and master['format'] == FORMAT
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
        assert row['bytes'] == 7398524 and row['sha256'] == RAW
        result[str(Path(row['path']).resolve())] = {key:row[key] for key in ('path','bytes','sha256')}
    return result


def check(path, approved):
    p = Path(path)
    assert not p.is_symlink() and p.suffix.lower() == '.wav'
    assert str(p.resolve()) in approved
    row = approved[str(p.resolve())]
    assert row['bytes'] == 7398524 and row['sha256'] == RAW
    assert checked(row) == p.resolve()
    validated_actual_master()


def standalone_assets():
    validated_actual_master()
    return [PINS[key] for key in ('master_WAV','export_evidence','HOST_binding','b00_authority')]
