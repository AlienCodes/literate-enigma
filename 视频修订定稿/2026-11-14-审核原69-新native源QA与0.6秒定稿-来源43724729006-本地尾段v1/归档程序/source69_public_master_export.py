"""Exact already-exported source69/book56 public master IO; no audio production."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat

PINS = {'final_H': {'path': '/workspace/work/review69-finalV3/43724729006-normal18/archive-handoff.json', 'bytes': 65040, 'sha256': 'd7bdc897ff024d80e69716e58b3c0661a396d39ee0deca788d9008d1eac62b58'}, 'sourceQA_H': {'path': '/workspace/work/review69-sourceQA/43724729006/archive-handoff.json', 'bytes': 49513, 'sha256': 'a3a1464a3144a2dc85cd52c985912f6e7433f9ebbab1e376702c6f839ac9a1e8'}, 'master_WAV': {'path': '/workspace/work/review69-sourceQA/43724729006/actual-original-program-master-export/69-original-program-master-pre-video-AF.wav', 'bytes': 7775324, 'sha256': '96363389b32a3bff18746cead710d1c1522046f1fa39c67b7fcbf44c7d80c255'}, 'export_evidence': {'path': '/workspace/work/review69-sourceQA/43724729006/actual-original-program-master-export/69-original-program-master-export.json', 'bytes': 1607, 'sha256': '36b853e4fe8bf9608362c056dca15ea778d090b706e305642096cfe32e05c691'}, 'native_status': {'path': '/workspace/work/review69-sourceQA/43724729006/actual-original-program-master-export/69-status.json', 'bytes': 145345, 'sha256': 'ca97e3f0464d2f8e1a09f72d9ab88ef1d8345d3ee74d93ea9fdb2b3ea41e896d'}, 'HOST_binding': {'path': '/workspace/work/review69-sourceQA/43724729006/actual-original-program-master-export/actual-HOST-master-role-binding.json', 'bytes': 3451, 'sha256': 'c9df317f7874284fb182b655ee84d148c3e13af928d5063e1992bdffe6886deb'}, 'standalone_H': {'path': '/workspace/work/book56-source69-actual43724729006-original-HOST-preparation-20261115/BOOK56-SOURCE69-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json', 'bytes': 16824, 'sha256': '24f50ef296e37cdff9bfa465437505bc3a350d3f5cd4e3012739061b2a2b047b'}, 'b00_authority': {'path': '/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json', 'bytes': 2088, 'sha256': 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'}, 'original_PCM_reader': {'path': '/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py', 'bytes': 9748, 'sha256': 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'}, 'approved_IO_binder': {'path': '/workspace/work/actual-exported-master-WAV-sourceQA-role-binding-CODE-ONLY-20261115/bind_actual_exported_master.py', 'bytes': 7389, 'sha256': 'ae19dae189e42f1787ef214a26d7baa5f329e21d9eea0f2513f469eb9fb50679'}}
SID, NID, RUN = '69', '56', 43724729006
RAW = '96363389b32a3bff18746cead710d1c1522046f1fa39c67b7fcbf44c7d80c255'
NATIVE_VIDEO = '96e1ef298003f08aa9e50e6d18f749e9ac561188ca84118be04a9667cd323321'
FINAL_VIDEO = '38b5b9243e3b71cc8ecb72d6367e73e316df96a3a44baa83293e257b63f7b670'
FORMAT = {'container':'WAV','encoding':'PCM','sample_width_bytes':2,
          'bits_per_sample':16,'channels':1,'sample_rate':24000,
          'frames':3887640,'duration_seconds':161.985}
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
    original = module_from_pin('source69_original_PCM_reader', 'original_PCM_reader')
    original._regular(path)
    with Path(path).open('rb') as stream:
        actual = original._pcm_format(stream)
    assert actual == FORMAT
    return actual


def validate_records(native, evidence):
    original = module_from_pin('source69_approved_export_IO_binder', 'approved_IO_binder')
    master = original.validate_records(SID, RUN, native, evidence)
    assert native['final_wav_sha256'] == master['sha256'] == RAW
    assert master['bytes'] == 7775324 and master['format'] == FORMAT
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
        assert row['bytes'] == 7775324 and row['sha256'] == RAW
        result[str(Path(row['path']).resolve())] = {key:row[key] for key in ('path','bytes','sha256')}
    return result


def check(path, approved):
    p = Path(path)
    assert not p.is_symlink() and p.suffix.lower() == '.wav'
    assert str(p.resolve()) in approved
    row = approved[str(p.resolve())]
    assert row['bytes'] == 7775324 and row['sha256'] == RAW
    assert checked(row) == p.resolve()
    validated_actual_master()


def standalone_assets():
    validated_actual_master()
    return [PINS[key] for key in ('master_WAV','export_evidence','HOST_binding','b00_authority')]
