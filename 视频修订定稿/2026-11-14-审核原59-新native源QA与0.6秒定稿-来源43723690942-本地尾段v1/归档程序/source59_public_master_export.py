"""Exact already-exported source59/book69 public master IO; no audio production."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat

PINS = {'final_H': {'path': '/workspace/work/review59-finalV3/43723690942-normal18/archive-handoff.json', 'bytes': 64797, 'sha256': 'bbecdf45996de7fe67f23a0031a5a9c377a7f6ddf7d18b96fb14e26b52160d8c'}, 'sourceQA_H': {'path': '/workspace/work/review59-sourceQA/43723690942/archive-handoff.json', 'bytes': 49233, 'sha256': 'c86bdea99ef862b718b08e98e36956a8e6bb1b8731ffbb14a00885ec2907dff2'}, 'master_WAV': {'path': '/workspace/work/review59-sourceQA/43723690942/actual-original-program-master-export/59-original-program-master-pre-video-AF.wav', 'bytes': 7414124, 'sha256': '8f822a42adab797aeb278971afbcb260944c088a60ca241d416a9c962409daa7'}, 'export_evidence': {'path': '/workspace/work/review59-sourceQA/43723690942/actual-original-program-master-export/59-original-program-master-export.json', 'bytes': 1606, 'sha256': 'a680841f70b12a237a65a83fabc91c56959347bbb80865d89449be82902d1c4e'}, 'native_status': {'path': '/workspace/work/review59-sourceQA/43723690942/actual-original-program-master-export/59-status.json', 'bytes': 164440, 'sha256': 'd6a92bdeee5c77bb2dad5f62b39649431f563be5602d187259f312418d81bf59'}, 'HOST_binding': {'path': '/workspace/work/review59-sourceQA/43723690942/actual-original-program-master-export/actual-HOST-master-role-binding.json', 'bytes': 3450, 'sha256': '6312949f5e1624ea0ccbb3da5047e22516fcd65225ae6750ee86054a14f5d242'}, 'standalone_H': {'path': '/workspace/work/book69-source59-actual43723690942-original-HOST-preparation-20261115/BOOK69-SOURCE59-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json', 'bytes': 9183, 'sha256': '224043aaee90a7eb9dd5abf92900b7cc6c383876bf0dfc1166b49644126bcbfa'}, 'b00_authority': {'path': '/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json', 'bytes': 2088, 'sha256': 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}, 'original_PCM_reader': {'path': '/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py', 'bytes': 9748, 'sha256': 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'}, 'approved_IO_binder': {'path': '/workspace/work/actual-exported-master-WAV-sourceQA-role-binding-CODE-ONLY-20261115/bind_actual_exported_master.py', 'bytes': 7389, 'sha256': 'ae19dae189e42f1787ef214a26d7baa5f329e21d9eea0f2513f469eb9fb50679'}}
SID, NID, RUN = '59', '69', 43723690942
RAW = '8f822a42adab797aeb278971afbcb260944c088a60ca241d416a9c962409daa7'
NATIVE_VIDEO = 'a26a219fca9bd0c40131a5e4ce49aaaba20cc9c91466fdf45c0e3dc2758e3516'
FINAL_VIDEO = 'd93689a50170e11a79a397698cca75a8458506ade1ac5f6fecf02c7fc665087f'
FORMAT = {'container':'WAV','encoding':'PCM','sample_width_bytes':2,
          'bits_per_sample':16,'channels':1,'sample_rate':24000,
          'frames':3707040,'duration_seconds':154.46}
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
    original = module_from_pin('source59_original_PCM_reader', 'original_PCM_reader')
    original._regular(path)
    with Path(path).open('rb') as stream:
        actual = original._pcm_format(stream)
    assert actual == FORMAT
    return actual


def validate_records(native, evidence):
    original = module_from_pin('source59_approved_export_IO_binder', 'approved_IO_binder')
    master = original.validate_records(SID, RUN, native, evidence)
    assert native['final_wav_sha256'] == master['sha256'] == RAW
    assert master['bytes'] == 7414124 and master['format'] == FORMAT
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
        assert row['bytes'] == 7414124 and row['sha256'] == RAW
        result[str(Path(row['path']).resolve())] = {key:row[key] for key in ('path','bytes','sha256')}
    return result


def check(path, approved):
    p = Path(path)
    assert not p.is_symlink() and p.suffix.lower() == '.wav'
    assert str(p.resolve()) in approved
    row = approved[str(p.resolve())]
    assert row['bytes'] == 7414124 and row['sha256'] == RAW
    assert checked(row) == p.resolve()
    validated_actual_master()


def standalone_assets():
    validated_actual_master()
    return [PINS[key] for key in ('master_WAV','export_evidence','HOST_binding','b00_authority')]
