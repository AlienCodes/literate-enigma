"""CODE-ONLY35 physical binding: all original quality gates remain required."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,subprocess,tempfile
REFERENCE_SHA = '6cf01b6b4a02da7c26e332930dc1ba4ee18a0f74bfda057e015f029f3eb97ed5'

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


def validate_values(reference, observed):
    require(observed['source_id'] == '35' and observed['book_order'] == 54, 'Exact source35/book54 role required')
    require(observed['canonical_pipeline_passed'] is True, 'All original native canonical quality gates must pass first')
    for key in ['file_specs', 'RAW_SHA256', 'aac_adts_sha256', 'packet_projection_sha256', 'packet_count',
                'codec', 'maker_SHA256', 'certificate_SHA256', 'stamp_SHA256', 'actual_original20_program_SHA256']:
        require(typed(observed[key]) == typed(reference[key]), 'Exact actual new S15 physical identity differs: ' + key)
    require(observed['accepted_legacy_video_SHA256'] == reference['accepted_legacy_video_SHA256'] and
            observed['accepted_legacy_AAC_SHA256'] == reference['accepted_legacy_AAC_SHA256'], 'Original accepted legacy role differs')
    require(observed['aac_adts_sha256'] != observed['accepted_legacy_AAC_SHA256'], 'Expected authorized new mother, not a legacy relabel')
    return {'identity_binding_passed': True, 'formal_quality_acceptance': False,
            'source_id': '35', 'book_order': 54, 'target_sentence': 'S15',
            'all_original_native_quality_checks_required_and_reported_passed': True,
            'actual_new_RAW_SHA256': observed['RAW_SHA256'], 'actual_new_AAC_SHA256': observed['aac_adts_sha256'],
            'actual_new_packet_count': observed['packet_count'],
            'actual_new_absolute_projection_SHA256': observed['packet_projection_sha256'],
            'accepted_legacy_AAC_SHA256': observed['accepted_legacy_AAC_SHA256'],
            'accepted_prior_aac_identical': False,
            'no_new_quality_threshold_or_confirmation_or_hearing_approval': True}


def bind(request, wav, canonical_video, accepted_video, task, tools, canonical_pipeline_passed):
    task, tools, request = Path(task), Path(tools), Path(request)
    refpath = Path(__file__).with_name('source35_exact_new_S15_physical_reference.json')
    require(digest(refpath) == REFERENCE_SHA, 'Pinned physical reference differs')
    reference = json.loads(refpath.read_text())
    aac, legacy = actual_aac(canonical_video), actual_aac(accepted_video)
    files = {rel: {'bytes': (request / rel).stat().st_size, 'sha256': digest(request / rel)}
             for rel in reference['file_specs']}
    observed = {'source_id': '35', 'book_order': 54, 'canonical_pipeline_passed': canonical_pipeline_passed,
                'file_specs': files, 'RAW_SHA256': digest(wav),
                **{k: aac[k] for k in ['aac_adts_sha256', 'packet_count', 'packet_projection_sha256']},
                'codec': aac['projection']['codec'], 'maker_SHA256': digest(tools / 'make_video.py'),
                'certificate_SHA256': digest(task / 'actual-spoken20-certification.json'),
                'stamp_SHA256': digest(tools / '新管/快测通过.json'),
                'actual_original20_program_SHA256': {p: digest(tools / p) for p in reference['actual_original20_program_SHA256']},
                'accepted_legacy_video_SHA256': digest(accepted_video), 'accepted_legacy_AAC_SHA256': legacy['aac_adts_sha256']}
    return validate_values(reference, observed)
