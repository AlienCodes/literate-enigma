#!/usr/bin/env python3
"""Read-only MP4 audio audit. Historical production QC and current measurements stay separate."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
import urllib.request
import numpy as np

BASE = 'c9d52b26fe981ef8e4c412189ca289716ab8bf00'
ROOT = Path(__file__).resolve().parents[2]
FOCUS = {'65': ('S8', 'ICARDA'), '66': ('S5', 'In Lyon'), '67': ('S1', 'Marcel Ravidat')}
LIMITATIONS = [
    'This is a read-only audit of the delivered AAC/MP4, not a rerun of the entire production pipeline.',
    'Production edit-boundary and non-speech confirmations depend on original a.wav and work_NN evidence; they are historical, not newly certified here.',
    'Speech boundaries below are independently measured from the MP4 and accepted only when title plus every script sentence maps one-to-one.',
    'ASR disagreements are retained for review; no new human-listening confirmation is fabricated.',
]

def run(args, **kw):
    return subprocess.run([str(x) for x in args], check=True, **kw)

def capture(args):
    return run(args, capture_output=True).stdout

def git_bytes(path):
    return capture(['git', 'show', f'{BASE}:{path}'])

def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'

def canonical_files(td, no, data, asr):
    tools = td / '视频/工具'
    tools.mkdir(parents=True)
    files = ['响度一致性核对.py', '音频体检.py', '音频体检基准.json']
    if asr:
        files += ['机器复听.py', '环境/模型校验码.json',
                  '发音词典/已核实读音.json', '发音词典/读音改正.json']
    hashes = {}
    for f in files:
        raw = git_bytes('视频/工具/' + f)
        p = tools / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        hashes[f] = hashlib.sha256(raw).hexdigest()
    script = tools.parent / '脚本' / (no + '.json')
    script.parent.mkdir()
    script.write_text(json_text(data))
    sys.path.insert(0, str(tools))
    def load(name, filename):
        spec = importlib.util.spec_from_file_location(name, tools / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    R = load('响度一致性核对', '响度一致性核对.py')
    R.FF = 'ffmpeg'
    Q = load('current_audio_health', '音频体检.py')
    return tools, R, Q, hashes, load

def hashes(path):
    pcm = capture(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a:0', '-vn',
                   '-c:a', 'pcm_f32le', '-f', 'hash', '-hash', 'sha256', '-']).decode().strip()
    pcm_s16 = capture(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a:0', '-vn',
                       '-c:a', 'pcm_s16le', '-f', 'hash', '-hash', 'sha256', '-']).decode().strip().removeprefix('SHA256=')
    packets = json.loads(capture(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                                 '-show_packets', '-show_data_hash', 'sha256',
                                 '-show_entries', 'packet=pts_time,dts_time,duration_time,data_hash,side_data_list',
                                 '-of', 'json', path]))['packets']
    return {'decoded_float32': pcm, 'decoded_pcm_s16le_sha256': pcm_s16,
            'encoded_packets_and_timing_sha256': hashlib.sha256(
                json.dumps(packets, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'audio_packet_count': len(packets)}

def measured_spans(a, sr=48000):
    h = int(.01 * sr)
    rms = np.sqrt(np.mean(a[:len(a)//h*h].reshape(-1, h)**2, axis=1))
    quiet = 20*np.log10(rms / (rms.max() + 1e-12) + 1e-12) < -50
    spans, start, last, q = [], None, None, 0
    for i, silent in enumerate(quiet):
        if not silent:
            if start is None:
                start = i
            last, q = i, 0
        else:
            q += 1
            if start is not None and q >= 70:
                spans.append((start*.01, (last+1)*.01))
                start = None
    if start is not None:
        spans.append((start*.01, (last+1)*.01))
    return [(s, e) for s, e in spans if e-s >= .25]

def prepare_models(tools):
    model_home = Path(os.environ.get('RUNNER_TEMP', str(ROOT / 'work'))) / 'audio-audit-models'
    model_home.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((tools / '环境/模型校验码.json').read_text())
    specs = [
        ('sherpa-onnx-whisper-small.en', [
            ('small.en-encoder.int8.onnx', 'small.en-encoder.int8.onnx'),
            ('small.en-decoder.int8.onnx', 'small.en-decoder.int8.onnx')]),
        ('sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8', [
            (f, 'parakeet/'+f) for f in ('encoder.int8.onnx', 'decoder.int8.onnx', 'joiner.int8.onnx', 'tokens.txt')])]
    verified = {}
    for directory, required in specs:
        target = model_home / directory
        def valid():
            return all((target/f).is_file() and hashlib.sha256((target/f).read_bytes()).hexdigest()[:16]
                       == manifest[key].split(':')[1] for f, key in required)
        if not valid():
            archive = model_home / (directory + '.tar.bz2')
            url = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/' + directory + '.tar.bz2'
            urllib.request.urlretrieve(url, archive)
            with tarfile.open(archive) as tf:
                tf.extractall(model_home, filter='data')
            archive.unlink()
        if not valid():
            raise RuntimeError('ASR model integrity check failed: ' + directory)
        verified[directory] = {f: hashlib.sha256((target/f).read_bytes()).hexdigest() for f, _ in required}
    return model_home, verified

def audit(no, video=None, out_dir=None, asr=False, baseline_only=False):
    no = str(no).zfill(2)
    if no not in [str(x) for x in range(65, 71)]:
        raise ValueError('This supplementary audit is scoped to 65–70.')
    out = Path(out_dir or ROOT / 'completion-output')
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / f'{no}-audio-audit.json'
    report = {
        'schema': 1, 'article': no, 'source_commit': BASE,
        'measured_at_utc': datetime.now(timezone.utc).isoformat(),
        'workflow_run': os.environ.get('GITHUB_RUN_ID'),
        'workflow_url': ('https://github.com/AlienCodes/literate-enigma/actions/runs/' + os.environ['GITHUB_RUN_ID'])
                        if os.environ.get('GITHUB_RUN_ID') else None,
        'limitations': LIMITATIONS, 'failures': [], 'preservation_failures': [], 'asr': {'performed': False},
        'historical_qc': {'commit': BASE, 'path': f'视频/音频核对/交付核查_{no}_4K定稿.txt',
                          'status': 'historical_only_not_a_new_pass'},
    }
    try:
        with tempfile.TemporaryDirectory(prefix=f'mp4_audio_audit_{no}_') as tmp:
            td = Path(tmp)
            paths = capture(['git', '-c', 'core.quotepath=off', 'ls-tree', '-rz', '--name-only', BASE]).decode().split('\0')
            candidates = [p for p in paths if p.startswith('最终版4K视频/' + no + ' - ') and p.endswith('.mp4')]
            if len(candidates) != 1:
                raise RuntimeError(f'Expected one original MP4: {candidates}')
            original = td / (no + '.mp4')
            original.write_bytes(git_bytes(candidates[0]))
            data = json.loads(git_bytes(f'视频/脚本/{no}.json'))
            inspected = original if baseline_only else Path(video).resolve()
            if not inspected.is_file():
                raise FileNotFoundError(inspected)
            alias_dir = td / 'inspected'
            alias_dir.mkdir()
            alias = alias_dir / (no + '.mp4')
            alias.symlink_to(inspected)
            report['source_video_path'] = candidates[0]
            report['mode'] = 'baseline_only_no_rendered_output_supplied' if baseline_only else 'rendered_output_compared_with_source'
            source_hashes = hashes(original)
            report['source_audio_hashes'] = source_hashes
            inspected_hashes = source_hashes if baseline_only else hashes(inspected)
            report['inspected_audio_hashes'] = inspected_hashes
            if baseline_only:
                report['original_audio_preserved'] = None
            else:
                report['original_audio_preserved'] = source_hashes == inspected_hashes
                if source_hashes != inspected_hashes:
                    report['preservation_failures'].append('Decoded audio or encoded AAC packets/timing changed from immutable BASE.')
            use_asr = asr and no in FOCUS
            tools, R, Q, file_hashes, load = canonical_files(td, no, data, use_asr)
            report['canonical_tool_sha256'] = file_hashes
            a = R.pcm(str(alias))
            TM = R.momentary(str(alias))
            metrics = Q.指标(a, no)
            base = json.loads((tools / '音频体检基准.json').read_text())
            health_notes = []
            health_bad = Q.超限(metrics, base, Q.确认(no), health_notes)
            report['current_audio_health'] = {
                'metrics': metrics, 'reference': base, 'failures': health_bad,
                'source_script_start_transient_confirmations_applied': health_notes}
            report['failures'] += health_bad
            I0, segs0, levels0, bad0, summary0 = R.check(str(alias), a)
            report['canonical_mp4_loudness_check'] = {
                'summary': summary0, 'global_lufs': I0, 'failures': bad0,
                'note': 'Unmodified canonical check skips the first 9 seconds; the independent mapping below also inspects S1.'}
            report['failures'] += [msg for _, msg in bad0]
            report['relative_threshold_voice_spans'] = measured_spans(a)
            # Use the canonical health check's absolute near-zero pauses. A relative
            # -50 dB threshold can add a false break around a quiet phrase (66 S18,
            # 67 S18); never merge or discard parts just to force the count.
            spans = [(s / R.SR, e / R.SR) for s, e in Q.句段(a)]
            report['sentence_mapping_method'] = 'Canonical audio-health 句段: >=0.7s at abs(sample)<1e-6'
            report['measured_voice_spans'] = spans
            report['expected_title_plus_sentences'] = len(data['sentences']) + 1
            report['sentence_mapping_valid'] = len(spans) == len(data['sentences']) + 1
            if not report['sentence_mapping_valid']:
                raise RuntimeError(f'Sentence mapping is uncertain: {len(spans)} voice spans for '
                                   f'{len(data["sentences"])+1} expected title/body spans.')
            body = spans[1:]
            sj = td / f'work_{no}/分段.json'
            sj.parent.mkdir()
            # This is independently measured MP4 mapping, explicitly NOT production 分段.json.
            sj.write_text(json_text({f'S{i}': [{'时刻': [x, y]}] for i, (x, y) in enumerate(body, 1)}))
            comparisons = R.句内(str(alias), a, TM, str(sj))
            internal_bad = R.句内报(comparisons)
            dipped = R.压小(str(alias), a, TM, str(sj))
            report['current_within_sentence_loudness'] = {
                'comparisons': comparisons, 'failures': internal_bad, 'suppressed_segment_candidates': dipped,
                'short_segment_effective_adjustment_lu': 2.0}
            report['failures'] += ['Within-sentence loudness exceeds 2.5 LU: ' + str(x) for x in internal_bad]
            report['failures'] += ['Segment suppression candidate: ' + str(x) for x in dipped]
            groups = R.分段(a, body)
            sentence_rows = []
            global_all = R.gated(TM[(TM[:, 0] >= body[0][0]+.4) & (TM[:, 0] <= body[-1][1]+.05), 1])
            for i, ((x, y), parts) in enumerate(zip(body, groups), 1):
                raw = R.段响度(TM, x, y)
                effective = R.等效(raw, x, y, True)
                values = []
                for j, (u, v) in enumerate(parts, 1):
                    raw_lufs, peak_m = R.段量(TM, u, v)
                    values.append({'part': j, 'start': u, 'end': v, 'raw_lufs': raw_lufs,
                                   'effective_lufs': R.等效(raw_lufs, u, v, True), 'peak_momentary_lufs': peak_m})
                sentence_rows.append({'sentence': f'S{i}', 'start': x, 'end': y, 'raw_lufs': raw,
                                      'effective_lufs': effective, 'parts': values})
            report['all_body_sentences_including_S1'] = {'global_lufs': global_all, 'sentences': sentence_rows}
            if no in FOCUS:
                name, phrase = FOCUS[no]
                row = sentence_rows[int(name[1:])-1]
                first = row['parts'][0]
                neighbours = row['parts'][1:3]
                report['historically_reported_focus'] = {
                    'sentence': name, 'phrase': phrase,
                    'measured_first_part': first, 'next_parts': neighbours,
                    'effective_differences_lu': [n['effective_lufs']-first['effective_lufs'] for n in neighbours],
                    'peak_differences_lu': [n['peak_momentary_lufs']-first['peak_momentary_lufs'] for n in neighbours],
                    'method': 'Measured first acoustical group of the mapped sentence, not a claim to forced word-level alignment.'}
                if use_asr:
                    home, verified = prepare_models(tools)
                    M = load('current_machine_relisten', '机器复听.py')
                    M.MD = str(home / 'sherpa-onnx-whisper-small.en')
                    M.PD = str(home / 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8')
                    recs = M.识别器()
                    x, y = row['start'], row['end']
                    x16 = np.frombuffer(capture(['ffmpeg', '-v', 'error', '-ss', f'{max(0,x-.08):.6f}',
                                                '-i', inspected, '-t', f'{y-x+.16:.6f}', '-vn', '-ac', '1',
                                                '-ar', '16000', '-f', 'f32le', '-']), np.float32)
                    ref = ' '.join(re.sub(r'\{\{.*?\}\}|\*\*', '', c['en']) for c in data['sentences'][int(name[1:])-1]['chunks'])
                    heard, discrepancies = M.各路(recs, ref, x16)
                    report['asr'] = {'performed': True, 'scope': name, 'reference': ref,
                                     'transcripts': heard, 'unreviewed_discrepancies': discrepancies,
                                     'verified_models': verified,
                                     'note': 'Fresh two-engine recognition; discrepancies are retained and require review, not silently waived.'}
                    # Small diagnostic excerpt; never changes the source voice.
                    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0,x-.1):.6f}', '-i', inspected,
                         '-t', f'{y-x+.2:.6f}', '-vn', '-c:a', 'pcm_s16le', out / f'{no}-{name}-focus.wav'])
            if not report['asr']['performed']:
                report['asr']['reason'] = 'No new ASR requested for this run; numerical and preservation checks only.'
            report['numerical_audio_checks_passed'] = not (health_bad or bad0 or internal_bad or dipped)
            report['waveform_checks_passed'] = not report['failures']
            report['status'] = ('needs_audio_repair_or_investigation' if report['failures'] else
                                'numerical_pass_audio_changed_requires_repair_evidence' if report['preservation_failures'] else
                                'waveform_pass_asr_review_needed' if report['asr'].get('unreviewed_discrepancies') else
                                'measured_checks_passed_with_stated_scope')
    except Exception as exc:
        report['status'] = 'audit_incomplete'
        report['failures'].append(f'{type(exc).__name__}: {exc}')
        report['waveform_checks_passed'] = False
        raise
    finally:
        report_path.write_text(json_text(report))
        (out / f'{no}-audio-audit.md').write_text(
            f'# 第{no}篇 MP4 音频实测\n\n状态：{report.get("status")}\n\n'
            + '历史制作核查仅作历史证据；本次实测范围和未覆盖项目见 JSON。\n\n'
            + ('本次发现：\n' + '\n'.join('- '+str(x) for x in report['failures']) if report['failures'] else '本次数值项未发现超限。')
            + '\n\n原配音保全：' + str(report.get('original_audio_preserved'))
            + '\n\n完整数据：' + report_path.name + '\n')
    return report

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('article')
    p.add_argument('video', nargs='?')
    p.add_argument('--out')
    p.add_argument('--asr', action='store_true')
    p.add_argument('--baseline-only', action='store_true')
    args = p.parse_args()
    if not args.baseline_only and not args.video:
        p.error('Supply the rendered MP4, or explicitly request --baseline-only.')
    result = audit(args.article, args.video, args.out, args.asr, args.baseline_only)
    print(json.dumps({'article': args.article, 'status': result['status'],
                      'focus': result.get('historically_reported_focus'),
                      'asr': {k: v for k, v in result['asr'].items() if k != 'verified_models'},
                      'failures': result['failures']}, ensure_ascii=False))
    # Default end-page audit remains strict: changed source audio is an error.
    # An authorized repair workflow may call audit() and assess its explicit
    # numerical and preservation fields together with separate repair evidence.
    sys.exit(0 if result['waveform_checks_passed'] and
             (args.baseline_only or result.get('original_audio_preserved') is True) else 1)
