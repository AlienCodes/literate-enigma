#!/usr/bin/env python3
"""Two authorized local gain repairs; preserve the reviewed 4K picture stream."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import traceback

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / '.github/audio-fix'
BASE = 'c9d52b26fe981ef8e4c412189ca289716ab8bf00'
FINAL = ROOT / 'audio-repair-final'
PRIVATE = ROOT / 'audio-repair-work'
SPECS = {
    '67': dict(sentence='S15', phrase='and Lascaux II', part=2,
               core_start=116.58, core_end=117.78, start=116.35,
               attack_end=116.40, release_start=117.95, end=118.00,
               prior_end=116.15, next_start=118.19),
    '70': dict(sentence='S12', phrase='Mailings doubled', part=1,
               core_start=84.17, core_end=85.30, start=84.00,
               attack_end=84.05, release_start=85.48, end=85.53,
               prior_end=83.044, next_start=85.72),
}

def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)

def capture(args):
    return run(args, capture_output=True).stdout

def load_module(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m

def sha_bytes(x):
    return hashlib.sha256(x).hexdigest()

def sha_file(p):
    return sha_bytes(Path(p).read_bytes())

def json_bytes(x):
    return json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False).encode() + b'\n'

def save(p, x):
    Path(p).write_bytes(json_bytes(x))

def probe(p):
    return json.loads(capture(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p]))

def pcm(p, sr, channels):
    raw = capture(['ffmpeg', '-v', 'error', '-i', p, '-map', '0:a:0', '-vn',
                   '-ac', channels, '-ar', sr, '-c:a', 'pcm_f32le', '-f', 'f32le', '-'])
    return np.frombuffer(raw, '<f4').reshape(-1, channels).copy()

def pcm_hash(a):
    return sha_bytes(np.asarray(a, dtype='<f4').tobytes())

def timing_hash(packets):
    return sha_bytes(json.dumps(packets, sort_keys=True, separators=(',', ':')).encode())

def db_peak(x):
    return float(20 * np.log10(max(float(np.max(np.abs(x))), 1e-15)))

def fade_metrics(a, sr, start, end):
    rows=[]
    for ms in (5,10):
        h=round(sr*ms/1000)
        for p in range(round(start*sr),round(end*sr),h):
            q=min(round(end*sr),p+h)
            z=a[p:q]
            rows.append(dict(window_ms=ms,start=p/sr,end=q/sr,
                             rms_dbfs=float(20*np.log10(max(rms(z),1e-15))),
                             peak_dbfs=db_peak(z)))
    return rows

def rms(x):
    return float(np.sqrt(np.mean(x.astype(np.float64)**2)))

def corr(a, b):
    av, bv = a.reshape(-1).astype(np.float64), b.reshape(-1).astype(np.float64)
    return float(np.dot(av, bv) / math.sqrt(np.dot(av, av)*np.dot(bv, bv)))

def sentence_row(report, sentence):
    return next(x for x in report['all_body_sentences_including_S1']['sentences']
                if x['sentence'] == sentence)

def sensitivity(R, TM, parts, part_no):
    j = part_no - 1
    rows = []
    neighbours = [k for k in (j-1, j+1) if 0 <= k < len(parts)]
    for ds in (-.04, -.02, 0, .02, .04):
        for de in (-.04, -.02, 0, .02, .04):
            x, y = parts[j]['start']+ds, parts[j]['end']+de
            raw, pk = R.段量(TM, x, y)
            effective = R.等效(raw, x, y, True)
            comparisons = []
            for k in neighbours:
                n = parts[k]
                nr, npk = R.段量(TM, n['start'], n['end'])
                ne = R.等效(nr, n['start'], n['end'], True)
                dg, dp = float(ne-effective), float(npk-pk)
                comparisons.append(dict(neighbour_part=k+1, effective_difference_lu=dg,
                                        peak_difference_lu=dp,
                                        suppressed=(dg > R.IN_DIP_G and dp > R.IN_DIP_PK),
                                        adjacent_difference_exceeds=abs(dg) > R.IN_ADJ))
            rows.append(dict(start=x, end=y, raw_lufs=float(raw),
                             effective_lufs=float(effective), peak_momentary_lufs=float(pk),
                             comparisons=comparisons))
    return rows

def full_asr(A, no, data, before, after, row, directory, sentence=None):
    sentence = sentence or SPECS[no]["sentence"]
    suffix = "target" if sentence == SPECS[no]["sentence"] else sentence
    with tempfile.TemporaryDirectory(prefix='repair_asr_') as td:
        tools, _, _, _, load = A.canonical_files(Path(td), no, data, True)
        home, verified = A.prepare_models(tools)
        M = load('repair_target_machine_relisten', '机器复听.py')
        M.MD = str(home / 'sherpa-onnx-whisper-small.en')
        M.PD = str(home / 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8')
        recs = M.识别器()
        idx = int(sentence[1:])-1
        ref = ' '.join(re.sub(r'\{\{.*?\}\}|\*\*', '', c['en']) for c in data['sentences'][idx]['chunks'])
        results = {}
        for key, file in [('source', before), ('repaired', after)]:
            x, y = row['start'], row['end']
            audio16 = np.frombuffer(capture(['ffmpeg', '-v', 'error', '-ss', f'{max(0,x-.08):.6f}',
                                            '-i', file, '-t', f'{y-x+.16:.6f}', '-vn', '-ac', '1',
                                            '-ar', '16000', '-f', 'f32le', '-']), np.float32)
            heard, discrepancies = M.各路(recs, ref, audio16)
            results[key] = dict(transcripts=heard, unreviewed_discrepancies=discrepancies)
        before_errors = {json.dumps(x, ensure_ascii=False) for x in results['source']['unreviewed_discrepancies']}
        after_errors = {json.dumps(x, ensure_ascii=False) for x in results['repaired']['unreviewed_discrepancies']}
        result = dict(sentence=sentence, reference=ref,
                      models_verified=True, model_sha256=verified, **results,
                      new_discrepancies=sorted(after_errors-before_errors),
                      note='Fresh recognition is retained without inventing listening confirmations. '
                           'Positive local gain and waveform checks separately prove no samples were cut.')
        save(directory/f'{no}-{suffix}-speech-check.json', result)
        assert not result['new_discrepancies'], 'New ASR discrepancy after repair; review rather than silently waive.'
        return result

def repair(no, P, A, profile='single'):
    spec = dict(SPECS[no])
    directory = FINAL/(no if profile == 'single' else f'{no}-{profile}')
    work = PRIVATE/(no if profile == 'single' else f'{no}-{profile}')
    directory.mkdir(parents=True)
    work.mkdir(parents=True)
    P.OUT = PRIVATE/no/'rendered'
    P.OUT.mkdir(parents=True,exist_ok=True)
    if not list(P.OUT.glob('*.mp4')):
        P.end_card(no)
    inputs = list(P.OUT.glob('*.mp4'))
    assert len(inputs) == 1
    reviewed = inputs[0]
    verification = json.loads((P.OUT/f'{no}-verification.json').read_text())
    assert verification['original_audio_identical'] is True
    assert verification['end_page_frames'] == 60 and verification['end_page_seconds'] == 2
    source = work/f'{no}-source.mp4'
    source.write_bytes(capture(['git', 'show', BASE+':'+verification['source']]))
    data = json.loads(capture(['git', 'show', BASE+f':视频/脚本/{no}.json']))
    info = probe(source)
    stream = next(x for x in info['streams'] if x['codec_type'] == 'audio')
    sr, channels = int(stream['sample_rate']), int(stream['channels'])
    source_pcm = pcm(source, sr, channels)
    assert pcm_hash(pcm(reviewed, sr, channels)) == pcm_hash(source_pcm)
    before_report = A.audit(no, video=source, out_dir=work/'before-audit', asr=False)
    assert before_report['sentence_mapping_valid']
    before_parts = sentence_row(before_report, spec['sentence'])['parts']
    target = before_parts[spec['part']-1]
    assert abs(target['start']-spec['core_start']) < .03
    assert abs(target['end']-spec['core_end']) < .03
    candidates = before_report['current_within_sentence_loudness']['suppressed_segment_candidates']
    assert len(candidates) == 1 and candidates[0][0] == spec['sentence']
    # Reuse the exact unchanged canonical functions used by the independent audit.
    with tempfile.TemporaryDirectory(prefix='repair_meter_') as td:
        _, R, _, tool_hashes, _ = A.canonical_files(Path(td), no, data, False)
        TM = R.momentary(str(source))
        before_sensitive = sensitivity(R, TM, before_parts, spec['part'])
        stable_before = all(any(n['suppressed'] for n in z['comparisons']) for z in before_sensitive)
        save(work/f'{no}-before-boundary-sensitivity.json', before_sensitive)
        assert stable_before, 'Suppression finding changes under 20/40ms boundary perturbation; needs investigation.'
        neighbour_values = [before_parts[k]['effective_lufs']
                            for k in (spec['part']-2, spec['part'])
                            if 0 <= k < len(before_parts)]
        gain_db = round(float(np.mean(neighbour_values)-target['effective_lufs']), 1)
        assert 0 < gain_db <= 3, 'Unexpected required gain; do not over-amplify.'
        spec['gain_db'] = gain_db
        spec['smoothing'] = 'raised-cosine'
        spec['role'] = 'suppressed-phrase-repair'
        gain_windows = [spec]
        nframes = len(source_pcm)
        s, a, b, e = [round(spec[x]*sr) for x in ('start', 'attack_end', 'release_start', 'end')]
        assert 0 <= s < a < round(spec['core_start']*sr) < round(spec['core_end']*sr) < b < e < nframes
        # Fade windows must be in genuinely quiet audio, well outside spoken words.
        fade_peaks = dict(attack_dbfs=db_peak(source_pcm[s:a]), release_dbfs=db_peak(source_pcm[b:e]))
        assert max(fade_peaks.values()) < -70, 'Chosen ramp touches audible material; inspect actual waveform.'
        envelope = np.ones(e-s, dtype=np.float64)
        up = .5-.5*np.cos(np.linspace(0, np.pi, a-s))
        down = .5+.5*np.cos(np.linspace(0, np.pi, e-b))
        envelope[:a-s] = up
        envelope[b-s:] = down
        amplitude = 1+(10**(gain_db/20)-1)*envelope
        processed = source_pcm.copy()
        processed[s:e] = (processed[s:e].astype(np.float64)*amplitude[:,None]).astype(np.float32)
        outside = np.ones(nframes, dtype=bool)
        outside[s:e] = False
        expected_core_gain_db = gain_db
        if no == '70':
            if profile == 'A':
                extra = dict(sentence='S12',phrase='Mailings doubled, from about 80 million items in 1839 to over 169 million in 1840.',
                             core_start=84.1661666667,core_end=92.8323541667,start=84.00,attack_end=84.05,
                             release_start=93.02,end=93.07,gain_db=-.314,smoothing='raised-cosine',
                             role='sentence-integrated-loudness-compensation')
                expected_core_gain_db += extra['gain_db']
            elif profile == 'B':
                extra = dict(sentence='S13',phrase='The design had a drawback.',core_start=93.81,core_end=95.34,
                             start=93.60,attack_end=93.65,release_start=95.50,end=95.55,
                             gain_db=.4,smoothing='raised-cosine',role='adjacent-short-sentence-balance')
            else:
                raise ValueError('Article70 requires explicit A/B candidate comparison.')
            xs,xa,xb,xe = [round(extra[x]*sr) for x in ('start','attack_end','release_start','end')]
            assert 0 <= xs < xa < round(extra['core_start']*sr) < round(extra['core_end']*sr) < xb < xe < nframes
            fade_peaks.update(extra_attack_dbfs=db_peak(source_pcm[xs:xa]),extra_release_dbfs=db_peak(source_pcm[xb:xe]))
            assert max(fade_peaks.values()) < -70, 'Extra compensation ramp touches audible material.'
            env=np.ones(xe-xs,dtype=np.float64)
            env[:xa-xs]=.5-.5*np.cos(np.linspace(0,np.pi,xa-xs))
            env[xb-xs:]=.5+.5*np.cos(np.linspace(0,np.pi,xe-xb))
            scale=1+(10**(extra['gain_db']/20)-1)*env
            processed[xs:xe]=(processed[xs:xe].astype(np.float64)*scale[:,None]).astype(np.float32)
            outside[xs:xe]=False
            gain_windows.append(extra)
        outside_source_hash = pcm_hash(source_pcm[outside])
        outside_processed_hash = pcm_hash(processed[outside])
        assert outside_source_hash == outside_processed_hash
        assert np.array_equal(source_pcm[outside], processed[outside])
        assert np.array_equal(np.signbit(source_pcm), np.signbit(processed))
        assert np.max(np.abs(processed)) < .98
        wav = work/f'{no}-processed.wav'
        sf.write(wav, processed, sr, subtype='FLOAT')
        check, rate = sf.read(wav, dtype='float32', always_2d=True)
        assert rate == sr and np.array_equal(check, processed)
        requested_bitrate = max(256000, int(stream.get('bit_rate') or 0))
        bitrate = min(requested_bitrate, 6*sr*channels)
        m4a = work/f'{no}-repaired.m4a'
        run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-map', '0:a:0',
             '-c:a', 'aac', '-b:a', bitrate, '-ar', sr, '-ac', channels,
             '-t', stream['duration'], '-avoid_negative_ts', 'disabled', m4a])
        final = directory/reviewed.name
        run(['ffmpeg', '-v', 'error', '-y', '-copyts', '-i', reviewed, '-i', m4a,
             '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy',
             '-avoid_negative_ts', 'disabled', '-movflags', '+faststart', final])
        video_before = P.packet_times(reviewed, 'v:0')
        video_after = P.packet_times(final, 'v:0')
        assert video_before == video_after, 'Repair changed picture timing.'
        pictures_before = P.coded_frames_hash(reviewed, verification['output_frames'])
        pictures_after = P.coded_frames_hash(final, verification['output_frames'])
        assert pictures_before == pictures_after, 'Repair changed coded pictures.'
        decoded = pcm(final, sr, channels)
        common = min(len(decoded), nframes)
        tail_delta = len(decoded)-nframes
        assert abs(tail_delta) <= 1024
        speech_end = verification['source_voice_endpoint_seconds']
        assert speech_end+.8 < common/sr
        mask = outside[:common]
        reference = source_pcm[:common][mask].astype(np.float64)
        observed = decoded[:common][mask].astype(np.float64)
        noise = observed-reference
        outside_snr = float(10*np.log10(np.sum(reference**2)/max(np.sum(noise**2),1e-30)))
        outside_correlation = corr(reference, observed)
        assert outside_snr >= 38 and outside_correlation >= .9999
        # Look for sub-frame speech drift independently of AAC packet padding.
        mono = source_pcm[:common].mean(axis=1)
        positions = np.flatnonzero(mask & (np.abs(mono)>.005))
        positions = positions[(positions>8) & (positions<common-8)][::10]
        assert len(positions)>1000
        lag_scores = {}
        for lag in range(-8,9):
            lag_scores[str(lag)] = corr(source_pcm[positions], decoded[positions+lag])
        best_lag = int(max(lag_scores, key=lag_scores.get))
        assert best_lag == 0, ('Audio offset detected.', lag_scores)
        core0, core1 = round(spec['core_start']*sr), round(spec['core_end']*sr)
        core_correlation = corr(processed[core0:core1], decoded[core0:core1])
        achieved_gain = float(20*np.log10(rms(decoded[core0:core1])/rms(source_pcm[core0:core1])))
        assert core_correlation>.999 and abs(achieved_gain-expected_core_gain_db)<.2
        after_report = A.audit(no, video=final, out_dir=directory, asr=False)
        print(json.dumps({'article':no,'candidate':profile,'after_failures':after_report['failures'],'whole':after_report['canonical_mp4_loudness_check']},ensure_ascii=False),flush=True)
        assert after_report['numerical_audio_checks_passed']
        assert not after_report['failures']
        assert after_report['original_audio_preserved'] is False
        assert after_report['preservation_failures']
        after_parts = sentence_row(after_report, spec['sentence'])['parts']
        TM_after = R.momentary(str(final))
        after_sensitive = sensitivity(R, TM_after, after_parts, spec['part'])
        stable_after = all(not any(n['suppressed'] or n['adjacent_difference_exceeds']
                                  for n in z['comparisons']) for z in after_sensitive)
        assert stable_after, 'Repaired segment remains unstable under boundary perturbation.'
        asr = full_asr(A, no, data, source, final, sentence_row(before_report,spec['sentence']), directory)
        extra_asr = None
        if no == '70' and profile == 'B':
            extra_asr = full_asr(A,no,data,source,final,sentence_row(before_report,'S13'),directory,sentence='S13')
        for kind in ('script.json', '简述.png'):
            shutil.copy2(P.OUT/f'{no}-{kind}', directory/f'{no}-{kind}')
        before_health = before_report['current_audio_health']
        repair_report = {
            'schema':1, 'kind':'authorized_intentional_gain_repair', 'article':no,
            'source_commit':BASE, 'source_video_path':verification['source'],
            'source_decoded_float32_sha256':pcm_hash(source_pcm),
            'processed_float32_sha256':pcm_hash(processed),
            'final_decoded_float32_sha256':pcm_hash(decoded),
            'sample_rate':sr, 'channels':channels,
            'source_sample_frames':nframes, 'processed_sample_frames':len(processed),
            'final_sample_frames':len(decoded), 'gain_windows':gain_windows,
            'selected_strategy':profile, 'target_expected_net_core_gain_db':expected_core_gain_db,
            'outside_mask_definition':'Union of every listed raised-cosine gain window, including overlaps.',
            'pre_encoding_outside_windows_identical':True,
            'outside_source_float32_sha256':outside_source_hash,
            'outside_processed_float32_sha256':outside_processed_hash,
            'fade_window_peak_dbfs':fade_peaks,
            'source_fade_5_10ms_measurements':{
                'attack':fade_metrics(source_pcm,sr,spec['start'],spec['attack_end']),
                'release':fade_metrics(source_pcm,sr,spec['release_start'],spec['end'])},
            'all_windows_fade_5_10ms_measurements':[dict(sentence=w['sentence'],role=w['role'],attack=fade_metrics(source_pcm,sr,w['start'],w['attack_end']),release=fade_metrics(source_pcm,sr,w['release_start'],w['end'])) for w in gain_windows],
            'source_global_peak_dbfs':db_peak(source_pcm),
            'processed_global_peak_dbfs':db_peak(processed),
            'final_global_peak_dbfs':db_peak(decoded),
            'source_core_peak_dbfs':db_peak(source_pcm[core0:core1]),
            'final_core_peak_dbfs':db_peak(decoded[core0:core1]),
            'achieved_core_gain_db':achieved_gain, 'core_waveform_correlation':core_correlation,
            'before_target_sentence':sentence_row(before_report,spec['sentence']),
            'after_target_sentence':sentence_row(after_report,spec['sentence']),
            'boundary_sensitivity':dict(offset_seconds=[-.04,-.02,0,.02,.04],
                                        before=before_sensitive,after=after_sensitive,
                                        before_finding_stable=stable_before,after_pass_stable=stable_after),
            'aac':dict(codec='aac',bitrate=bitrate,requested_bitrate=requested_bitrate,
                       original_bitrate=int(stream.get('bit_rate') or 0),
                       packet_timings_identical=P.packet_times(source,'a:0')==P.packet_times(final,'a:0'),
                       aligned_lag_samples=best_lag,lag_correlation=lag_scores,
                       outside_windows_snr_db=outside_snr,
                       outside_windows_correlation=outside_correlation,
                       outside_windows_quality_passed=True,sample_alignment_passed=True,
                       decoded_tail_sample_delta=tail_delta,
                       tail_delta_note='At most one AAC padding frame after >0.8s silence; no spoken samples removed.',
                       outside_final_pcm_identical=np.array_equal(source_pcm[:common][mask],decoded[:common][mask]),
                       note='Only pre-encoding PCM outside the gain window is bit-identical. '
                            'Final AAC is re-encoded; its outside-window quantization differences are measured, not hidden.'),
            'video':dict(all_coded_pictures_identical=True,packet_timings_identical=True,
                         input_coded_sha256=pictures_before,final_coded_sha256=pictures_after,
                         input_packet_timing_sha256=timing_hash(video_before),
                         final_packet_timing_sha256=timing_hash(video_after),
                         input_rendered_video_sha256=sha_file(reviewed)),
            'numerical_audio_checks_passed':True,
            'before_health_metrics':before_health['metrics'],
            'after_health_metrics':after_report['current_audio_health']['metrics'],
            'canonical_tool_sha256':tool_hashes,
            'audio_audit_report_sha256':sha_file(directory/f'{no}-audio-audit.json'),
            'target_speech_check_sha256':sha_file(directory/f'{no}-target-speech-check.json'),
            'asr_new_discrepancies':asr['new_discrepancies'],
            'additional_speech_checks':([] if extra_asr is None else [dict(sentence='S13',report=f'{no}-S13-speech-check.json',sha256=sha_file(directory/f'{no}-S13-speech-check.json'),new_discrepancies=extra_asr['new_discrepancies'])]),
            'final_video_sha256':sha_file(final),
            'no_clipped_samples':bool(np.max(np.abs(decoded))<=.99),
        }
        assert repair_report['no_clipped_samples']
        save(directory/f'{no}-audio-repair.json',repair_report)
        verification.update(
            original_audio_identical=False,
            original_audio_packet_timings_identical=repair_report['aac']['packet_timings_identical'],
            audio_sha256=P.audio_hash(final),
            video_sha256=sha_file(final),
            audio_repair={
                'kind':'authorized_intentional_gain_repair',
                'report':f'{no}-audio-repair.json',
                'report_sha256':sha_file(directory/f'{no}-audio-repair.json'),
                'source_decoded_float32_sha256':repair_report['source_decoded_float32_sha256'],
                'final_decoded_float32_sha256':repair_report['final_decoded_float32_sha256'],
                'numerical_audio_checks_passed':True,
                'reason':'Repair independently measured suppressed short phrase; no cuts, TTS or global compression.'})
        save(directory/f'{no}-verification.json',verification)
        text = (
            f'# 第{no}篇授权局部补响核验\n\n'
            f'{spec["sentence"]}「{spec["phrase"]}」：{spec["core_start"]:.2f}–{spec["core_end"]:.2f}秒，'
            f'补响{gain_db:+.1f}dB。渐入{spec["start"]:.2f}–{spec["attack_end"]:.2f}秒，'
            f'渐出{spec["release_start"]:.2f}–{spec["end"]:.2f}秒，均在实测安静区。\n\n'
            '相同规范的8项体检、整句/句内响度与短段压小核对通过；前后各25组边界扰动已记录。'
            '目标句重新做双引擎识别，没有新增差异；原有识别歧义保留在报告中。\n\n'
            '增益处理阶段窗口外PCM逐样本相同。为保持AAC播放兼容，最终音轨重新编码，'
            f'窗口外实测SNR {outside_snr:.2f}dB、相关系数{outside_correlation:.8f}，'
            f'样本对齐偏移{best_lag}；最终PCM不声称原样。\n\n'
            '全条4K视频的H264图像数据和packet时序与补响前完全相同；简述仍为读完即转、显示2秒。'
            '未裁词、未重新合成、未作全局压缩。\n'
            + ('为避免S12补响后与下一短句产生新落差，S13另补+0.4dB。全部实际增益区间及不变区按并集核验。\n' if profile=='B' else '整句综合响度补偿策略及全部实际增益区间详见JSON。\n' if profile=='A' else ''))
        (directory/f'{no}-audio-repair.md').write_text(text)
        # Only reviewed final MP4, script, card and text QC are published.
        save(directory/f'{no}-before-audio-audit.json',before_report)
        print(f'{no}: authorized local gain {gain_db:+.1f}dB; numerical checks passed; '
              f'outside AAC SNR {outside_snr:.2f}dB; lag {best_lag}; pictures identical.',flush=True)
        return dict(profile=profile,directory=str(directory),accepted=True,numerical_audio_checks_passed=True,source_hash=pcm_hash(source_pcm),gain_windows=gain_windows,whole=after_report['canonical_mp4_loudness_check'],after_target=sentence_row(after_report,spec['sentence']))

if __name__ == '__main__':
    os.chdir(ROOT)
    FINAL.mkdir(exist_ok=True)
    PRIVATE.mkdir(exist_ok=True)
    P=load_module('reviewed_summary_renderer',ROOT/'.github/video-batch/run.py')
    A=load_module('unchanged_independent_audio_audit',HERE/'audit_audio.py')
    for no in (sys.argv[1:] or ['67','70']):
        assert no in SPECS
        if no == '67':
            repair(no,P,A)
            continue
        comparisons=[]
        for profile in ('A','B'):
            try:
                comparisons.append(repair(no,P,A,profile))
            except Exception as exc:
                traceback.print_exc()
                audit_path=FINAL/f'70-{profile}'/'70-audio-audit.json'
                audit=json.loads(audit_path.read_text()) if audit_path.exists() else {}
                comparisons.append(dict(profile=profile,accepted=False,numerical_audio_checks_passed=audit.get('numerical_audio_checks_passed',False),failures=audit.get('failures'),error=repr(exc)))
        save(PRIVATE/'70-candidate-comparison.json',comparisons)
        accepted={x['profile']:x for x in comparisons if x.get('accepted')}
        assert accepted, 'Neither real full-track candidate passed; do not publish.'
        selected=accepted.get('B',accepted.get('A'))
        assert selected['profile']=='B' or 'B' not in accepted
        destination=FINAL/'70'
        shutil.copytree(Path(selected['directory']),destination)
        save(destination/'70-candidate-comparison.json',dict(selected=selected['profile'],selection_reason='Prefer B when it passes: fewer changed seconds and greater adjacent-sentence margin; both tested from BASE without cumulative encoding.',candidates=comparisons))
        print('Article70 selected full-track measured candidate:',selected['profile'],flush=True)
