#!/usr/bin/env python3
"""Read-only original ASR evidence for the three unresolved pronunciation reports."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess


TARGETS = {'46': 'S6', '49': 'S8', '55': 'S11'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--article', choices=sorted(TARGETS), required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--public-video', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = {'article': args.article, 'sentence': TARGETS[args.article],
              'diagnostic_only': True, 'acceptance': False, 'automatic_confirmation': False,
              'private_raw_PCM_GT_models_or_caches_exported': False}
    try:
        import numpy as np
        import soundfile as sf
        from scipy.signal import resample_poly
        source = args.work / f'scripts/{args.article}.json'
        private_work = args.work / f'work_{args.article}'
        raw_wav = private_work / 'a.wav'
        segmentation = private_work / '分段.json'
        proof = json.loads(args.proof.read_text())
        assert proof['official_fingerprint_matches_current_video_source_and_pcm'] is True
        assert sha(source) == proof['source_sha256'] and sha(raw_wav) == proof['internal_pcm_sha256']
        assert sha(args.public_video) == proof['video_sha256']
        data = json.loads(source.read_text())
        label = TARGETS[args.article]
        pieces = json.loads(segmentation.read_text())[label]
        lo, hi = float(pieces[0]['时刻'][0]), float(pieces[-1]['时刻'][1])
        assert 0 <= lo < hi < 1800
        reference = ' '.join(re.sub(r'\{\{.*?\}\}|\*\*', '', chunk['en'])
                             for chunk in data['sentences'][int(label[1:]) - 1]['chunks'])
        program = args.tools / '机器复听.py'
        original = runpy.run_path(str(program), run_name='original_asr_diagnostic')
        recognizers = original['识别器']()
        assert set(recognizers) == set(original['路名']) == {'small.en', 'parakeet'}
        samples, sr = sf.read(raw_wav)
        samples = samples if samples.ndim == 1 else samples.mean(axis=1)
        crop = samples[int(lo * sr):int(hi * sr)]
        x16 = resample_poly(crop, 16000, sr).astype(np.float32) if sr != 16000 else crop.astype(np.float32)
        merged = []
        transcripts, differences = original['各路'](recognizers, reference, x16, merged)
        result.update({'original_asr_program_sha256': sha(program),
                       'source_sha256': sha(source), 'internal_pcm_sha256': sha(raw_wav),
                       'public_video_sha256': sha(args.public_video), 'actual_segment_metadata_sha256': sha(segmentation),
                       'reference_text': reference,
                       'original_pipeline_input': {'native_seconds': [lo, hi], 'sample_rate': 16000,
                           'sample_count': len(x16), 'float32_sample_sha256': hashlib.sha256(x16.tobytes()).hexdigest(),
                           'full_transcripts_by_original_recognizer': transcripts,
                           'original_comparison_differences': differences,
                           'original_merged_word_observations': merged}})
        # Only the already exported public MP4 supplies a shareable sound clip.
        # Its clock can differ from private a.wav, so retain a labelled context.
        clip_lo, clip_hi = max(0., lo - .12), hi + .12
        clip = args.output.parent / f'{args.article}-{label}-public-ASR-context.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(clip_lo), '-i', str(args.public_video),
                        '-t', str(clip_hi - clip_lo), '-map', '0:a:0', '-vn', '-ac', '1',
                        '-ar', '16000', '-c:a', 'pcm_s16le', str(clip)], check=True, capture_output=True)
        public, public_sr = sf.read(clip)
        public = public.astype(np.float32)
        assert public_sr == 16000
        public_merged = []
        public_text, public_diff = original['各路'](recognizers, reference, public, public_merged)
        result['public_MP4_context'] = {'file': clip.name, 'sha256': sha(clip),
            'source_video_sha256': sha(args.public_video), 'public_mp4_seconds': [clip_lo, clip_hi],
            'clock_relation': 'native sentence bounds plus 120ms public-context padding; not a sample-identity alignment',
            'derived_from_public_mp4_only': True, 'full_transcripts_by_original_recognizer': public_text,
            'original_comparison_differences': public_diff, 'original_merged_word_observations': public_merged}
    except (Exception, SystemExit) as exc:
        message = str(exc).replace(str(args.work), '<private-work>').replace(str(args.tools), '<tools>')
        result['diagnostic_error'] = {'type': type(exc).__name__, 'message': message[:700]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'article': args.article, 'diagnostic_only': True,
                      'diagnostic_error': result.get('diagnostic_error'),
                      'original_transcripts_collected': 'original_pipeline_input' in result}, ensure_ascii=False))


if __name__ == '__main__':
    main()
