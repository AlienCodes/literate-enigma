"""Exact already-exported source41/book66 public master IO; no audio production."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat

PINS = {'final_H': {'path': '/workspace/work/review41-finalV3/43723634020-normal18/archive-handoff.json', 'bytes': 64107, 'sha256': 'aef997eb1826fcbf36472cf361392c681420c58cd15c8c39627779918618663f'}, 'sourceQA_H': {'path': '/workspace/work/review41-sourceQA/43723634020/archive-handoff.json', 'bytes': 48606, 'sha256': 'cc6ac1b1fde58cd9b54dba8d00d0863a1579e9e38bd0b6d33dbf2ee5ece21555'}, 'master_WAV': {'path': '/workspace/work/review41-sourceQA/43723634020/actual-original-program-master-export/41-original-program-master-pre-video-AF.wav', 'bytes': 7391084, 'sha256': 'd6d6a3e63a819ee552f3920b702f9da67a5a5ecae1a0899de76715237174f272'}, 'export_evidence': {'path': '/workspace/work/review41-sourceQA/43723634020/actual-original-program-master-export/41-original-program-master-export.json', 'bytes': 1606, 'sha256': 'a42688d71f3ce688a8371dea1d585863ad447ff5a2ad7c6c020e81efc4448915'}, 'native_status': {'path': '/workspace/work/review41-sourceQA/43723634020/actual-original-program-master-export/41-status.json', 'bytes': 187048, 'sha256': '6cf951231c5f40016f917c8d79229b154cdf8a0a9d3f365f09140fb9f302eda6'}, 'HOST_binding': {'path': '/workspace/work/review41-sourceQA/43723634020/actual-original-program-master-export/actual-HOST-master-role-binding.json', 'bytes': 3450, 'sha256': 'ce44c4f0d2f5be803145a5bfe11ac17c93c88a72e4b99fa89716c85f4a596eb9'}, 'standalone_H': {'path': '/workspace/work/book66-source41-actual43723634020-original-HOST-preparation-20261115/BOOK66-SOURCE41-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json', 'bytes': 7622, 'sha256': 'ab28e3321c7cdd47565d34d327bd59cdf152bafdc20a63873d2f4a8054fd3b94'}, 'b00_authority': {'path': '/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json', 'bytes': 2088, 'sha256': 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}, 'original_PCM_reader': {'path': '/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py', 'bytes': 9748, 'sha256': 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'}, 'approved_IO_binder': {'path': '/workspace/work/actual-exported-master-WAV-sourceQA-role-binding-CODE-ONLY-20261115/bind_actual_exported_master.py', 'bytes': 7389, 'sha256': 'ae19dae189e42f1787ef214a26d7baa5f329e21d9eea0f2513f469eb9fb50679'}}
SID, NID, RUN = '41', '66', 43723634020
RAW = 'd6d6a3e63a819ee552f3920b702f9da67a5a5ecae1a0899de76715237174f272'
NATIVE_VIDEO = '2cc646bb60006d43e95ab72caeb6f0fe32c741bccaade1ef588106aa77870eac'
FINAL_VIDEO = 'd4464f198bba04449b0e6b3065ec33308e8428fb658e90b56539ad210c88f17a'
FORMAT = {'container':'WAV','encoding':'PCM','sample_width_bytes':2,
          'bits_per_sample':16,'channels':1,'sample_rate':24000,
          'frames':3695520,'duration_seconds':153.98}
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
    original = module_from_pin('source41_original_PCM_reader', 'original_PCM_reader')
    original._regular(path)
    with Path(path).open('rb') as stream:
        actual = original._pcm_format(stream)
    assert actual == FORMAT
    return actual


def validate_records(native, evidence):
    original = module_from_pin('source41_approved_export_IO_binder', 'approved_IO_binder')
    master = original.validate_records(SID, RUN, native, evidence)
    assert native['final_wav_sha256'] == master['sha256'] == RAW
    assert master['bytes'] == 7391084 and master['format'] == FORMAT
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
        assert row['bytes'] == 7391084 and row['sha256'] == RAW
        result[str(Path(row['path']).resolve())] = {key:row[key] for key in ('path','bytes','sha256')}
    return result


def check(path, approved):
    p = Path(path)
    assert not p.is_symlink() and p.suffix.lower() == '.wav'
    assert str(p.resolve()) in approved
    row = approved[str(p.resolve())]
    assert row['bytes'] == 7391084 and row['sha256'] == RAW
    assert checked(row) == p.resolve()
    validated_actual_master()


def standalone_assets():
    validated_actual_master()
    return [PINS[key] for key in ('master_WAV','export_evidence','HOST_binding','b00_authority')]
