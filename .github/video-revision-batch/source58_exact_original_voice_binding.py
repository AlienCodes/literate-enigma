"""Exact original stock voice identity only, after every original native quality check.
No repair, TTS, or quality acceptance is granted by this module.
"""
from pathlib import Path
from fractions import Fraction
import hashlib,json,subprocess,tempfile
SOURCE_ID='58'
BOOK_ORDER=67
REFERENCE_SHA='21260b56b109c4732620f319653499f8d2c994182d82dc110dfa83ea6f619792'
REFERENCE_FILE='source58_exact_original_voice_reference.json'
INSTALLER_FILE='install_source58_stock_code.py'
INSTALLER_SHA='b6ce66b13f8c977c88d427548e8fcf865454f707917b17a8c02f577d795856f4'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def command(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def actual_aac(path):
    """Hash copied ADTS plus exact rational timestamp/payload/priming projection. Never rebase PTS."""
    raw = json.loads(command(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_streams', '-show_packets', '-show_data_hash', 'sha256', '-of', 'json', str(path)]))
    require(len(raw.get('streams', [])) == 1, f'No unique actual audio stream: {path}')
    stream = raw['streams'][0]; require(stream['codec_name'] == 'aac', f'Expected copied AAC: {path}')
    timebase = Fraction(stream['time_base']); packets = []
    for pkt in raw['packets']:
        timing = []
        for key in ('pts', 'dts', 'duration'):
            require(key in pkt, f'Cannot prove exact packet {key}: {path}')
            value = int(pkt[key]) * timebase
            timing.append([value.numerator, value.denominator])
        side = [{k: s[k] for k in sorted(s) if k != 'side_data_size'} for s in pkt.get('side_data_list', [])]
        require(pkt.get('data_hash'), f'No actual packet payload hash: {path}')
        packets.append({'timing_rationals': timing, 'size': int(pkt['size']), 'payload_sha256': pkt['data_hash'], 'side_data': side})
    codec = {k: stream.get(k) for k in ('codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout')}
    projection = {'codec': codec, 'packets': packets}
    encoded = json.dumps(projection, sort_keys=True, separators=(',', ':')).encode()
    with tempfile.TemporaryDirectory(prefix='actual-aac-') as td:
        adts = Path(td) / 'audio.aac'
        command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-vn', '-c:a', 'copy', '-f', 'adts', str(adts)])
        return {'aac_adts_sha256': digest(adts), 'packet_projection_sha256': hashlib.sha256(encoded).hexdigest(),
                'packet_count': len(packets), 'projection': projection}


def typed(value):
    if isinstance(value,dict):return ('dict',tuple(sorted((k,typed(v))for k,v in value.items())))
    if isinstance(value,list):return ('list',tuple(typed(v)for v in value))
    return (type(value).__name__,value)


def validate_values(reference,observed):
    require(observed['source_id']==SOURCE_ID and observed['book_order']==BOOK_ORDER,'Exact exact source/book role required')
    require(observed['canonical_pipeline_passed']is True,'All original canonical checks must actually pass first')
    require(typed(observed['file_specs'])==typed(reference['file_specs']),'Actual selected source/GEN/MD/pending/per/authority/root input bytes differ')
    require(observed['RAW_SHA256']==reference['RAW_SHA256'],'Actual original target complete WAV differs')
    for key in ['aac_adts_sha256','packet_count','packet_projection_sha256','codec']:
        require(typed(observed[key])==typed(reference[key]),'Actual original target copied AAC/absolute timing/side data differs: '+key)
    require(observed['stock_code_profile_SHA256']==reference['stock_code_profile_SHA256']and observed['stock_code_profile_verified']is True,'Actual full110 stock profile must be installed and verified')
    require(observed['maker_SHA256']==reference['maker_SHA256']and observed['renderer_SHA256']==reference['renderer_SHA256']and observed['stamp_SHA256']==reference['stamp_SHA256'],'Exact stockmaker/adopted renderer/actual stamp required')
    return {'identity_binding_passed':True,'formal_quality_acceptance':False,
            'repair_applied':False,'source_id':SOURCE_ID,'book_order':BOOK_ORDER,
            'user_individual_finalization_authorized':True,'review_only':False,
            'specific_final_authorization_sha256':reference['final_authority_sha256'],
            'actual_root_final_input_adoption_sha256':reference['root_source_adoption_sha256'],
            'all_original_native_quality_checks_remain_required':True,
            'actual_RAW_SHA256':observed['RAW_SHA256'],'actual_AAC_SHA256':observed['aac_adts_sha256'],
            'actual_AAC_packet_count':observed['packet_count'],
            'actual_absolute_packet_projection_SHA256':observed['packet_projection_sha256'],
            'actual_codec':observed['codec'],'source_documents_publication_role':f'actual book{BOOK_ORDER} source exact final authority; stock identity adds no publication authority'}


def bind(request_dir,wav_path,canonical_video,task,tools,canonical_pipeline_passed,production_environment):
    refpath=Path(__file__).with_name(REFERENCE_FILE)
    require(digest(refpath)==REFERENCE_SHA,'Pinned source exact identity reference differs')
    reference=json.loads(refpath.read_text());request_dir=Path(request_dir)
    files={}
    for rel,want in reference['file_specs'].items():
        path=request_dir/rel
        files[rel]={'bytes':path.stat().st_size,'sha256':digest(path)}
    aac=actual_aac(canonical_video)
    import importlib.util
    installer=Path(task)/INSTALLER_FILE
    require(digest(installer)==INSTALLER_SHA,'Exact reviewed stock installer differs')
    spec=importlib.util.spec_from_file_location('stock_identity_installer',installer)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    env=dict(production_environment)
    installed=module.verify_installed(Path(tools).parents[1],task,env)
    observed={'source_id':SOURCE_ID,'book_order':BOOK_ORDER,'canonical_pipeline_passed':canonical_pipeline_passed,
              'file_specs':files,'RAW_SHA256':digest(wav_path),
              'stock_code_profile_SHA256':installed['stock_code_profile_SHA256'],
              'stock_code_profile_verified':installed['actual_program_count']==110,
              'renderer_SHA256':digest(Path(tools)/'render.py'),
              'maker_SHA256':digest(Path(tools)/'make_video.py'),
              'stamp_SHA256':digest(Path(tools)/'新管/快测通过.json'),
              **{k:aac[k]for k in ['aac_adts_sha256','packet_count','packet_projection_sha256']},
              'codec':aac['projection']['codec']}
    return validate_values(reference,observed)
