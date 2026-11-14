"""Read-only27 exact G72 mother/source replay and safe raw/native timing metadata."""
from pathlib import Path
import hashlib, json, re, subprocess, tempfile
import numpy as np
import soundfile as sf

B = Path(__file__).resolve().parents[1]
helper = B / 'audio-a21-actual-first-4K-20261114/probe_minimal_encoded_boost.py'
ns = {'__file__': str(helper), '__name__': 'article27_original_function_readonly'}
exec(compile(helper.read_text().split('for no in sys.argv')[0], str(helper), 'exec'), ns)
r = ns['r']
source = Path('/workspace/work/video-revision-delivery/next-passed-validated/43532011110/27/final-source/视频/脚本/27.json')
review = B / 'next-passed-native/43532011110/27/27-4K-正文后插图2秒-简述2秒.mp4'
data = json.loads(source.read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(review) == '7f4114ea047285964548f4344abd3b9a307893fc3228ad43304d37a5343d068a'
report = {'article': '27', 'purpose': 'only27 user-review raw/native/public clock diagnosis',
          'quality_acceptance': False, 'source_sha256': sha(source), 'review_MP4_sha256': sha(review),
          'no_TTS_no_source_or_existing_cache_or_program_change': True,
          'original_maker_sha256': hashlib.sha256(r.m.source.encode()).hexdigest()}
try:
    with tempfile.TemporaryDirectory(prefix='private27-user-review-', dir='/dev/shm') as tmp:
        tmp = Path(tmp)
        cache = tmp / 'cache'
        cache.mkdir()
        audio, parts = r.build(data, cache)
        wav, enc = tmp / 'a.wav', tmp / 'voice.m4a'
        sf.write(wav, audio, 24000)
        subprocess.run([r.FF, '-y', '-v', 'error', '-i', str(wav), '-af', r.AF,
            '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(enc)], check=True)
        aac = lambda p: hashlib.sha256(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(p),
            '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])).hexdigest()
        report['reconstructed_WAV_sha256'] = sha(wav)
        report['reconstructed_AAC_ADTS_sha256'] = aac(enc)
        report['actual_review_AAC_ADTS_sha256'] = aac(review)
        assert sha(wav) == 'e15a2d05428e3219216ac8d10780669007f903071b0fcfc3c6bf377c517b8d7f'
        assert aac(enc) == aac(review) == '14bc91c62e66921fb55a215a42ce2db6a5544316600687b535a468770ae28252'
        report['entire_actual_native_PCM_and_public_AAC_exact'] = True
        targets = []
        for index in (13, 14):
            m, text = r.scope(data, index, cache)
            prior, pieces, gaps = 0, [], []
            listed = m['list_commas'](text)
            for match in re.finditer(r'[,;:](?=\s)', text):
                pieces.append((prior, match.end()))
                prior = match.end() + 1
                gaps.append(m['P_LIST'] if match.start() in listed else m['P_COMMA'])
            pieces.append((prior, len(text)))
            clips, tmap = m['sentence_audio'](text, pieces, gaps)
            record = next(p for p in parts if p['sentence'] == f'S{index}')
            before, last = record['start_s'], m['LAST']
            def mapped(token_seconds):
                raw_sample = round(token_seconds * last['scale'] * 24000)
                w_sample = raw_sample - last['head']
                for a, b, start, removed in last['segs']:
                    if a <= w_sample < b:
                        pos = w_sample - a
                        pos -= sum(min(pos, hi) - lo for lo, hi in removed if lo < pos)
                        return before + start + pos / 24000
                return None
            tokens = [{'phoneme': x.phoneme, 'original_model_start_s': x.start, 'original_model_end_s': x.end,
                       'original_raw_start_s': x.start * last['scale'], 'original_raw_end_s': x.end * last['scale'],
                       'mapped_native_start_s': mapped(x.start), 'mapped_native_end_s': mapped(x.end)}
                      for x in last['toks'] if x.start * last['scale'] <= 2.1]
            targets.append({'sentence': f'S{index}', 'plain_source_English': text,
                'native_sentence_span_s': [record['start_s'], record['end_s']],
                'native_piece_times_s': [{'piece': i + 1, 'text': text[a:b],
                    'native_span_s': [before + start, before + end]} for i, (a, b, start, end) in enumerate(tmap)],
                'effective_stored_auto_gain_db': record['automatic_level'],
                'manual_gain_db': record['manual_segment_level'],
                'raw_head_trim_samples': last['head'], 'raw_timing_scale': last['scale'],
                'raw_first_2100ms_phoneme_timing': tokens,
                'LAST_safe_timing': record['LAST_scalar_timing']})
        report['targets'] = targets
except Exception as exc:
    import traceback
    report['error'] = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
report['all_private_generated_audio_removed'] = True
report['G72_mother_scalar_manifest'] = list(r.m.cache_rows.values())
out = Path(__file__).with_name('27-exact-native-raw-opening-timing.json')
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(out, sha(out))
print(json.dumps({k: report[k] for k in ('reconstructed_WAV_sha256', 'entire_actual_native_PCM_and_public_AAC_exact', 'targets', 'error') if k in report}, ensure_ascii=False)[:3500])
