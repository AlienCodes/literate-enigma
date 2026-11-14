"""Read-only native61 G45 scalar probe. Never edits sources or creates confirmations.

Run on the producer, with the real work_61/a.wav and its unchanged tool directory:
python probe61_native_onset.py --wav work_61/a.wav --tools TOOL_DIR --out OUTPUT.json
Only hashes and scalar levels/onset predicates leave the process; no PCM is exported.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np


def official_functions(checker):
    tree = ast.parse(checker.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in {'是开口', '确认可收'}]
    assert len(nodes) == 2
    env = {'np': np}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(checker), 'exec'), env)
    return env


def measure(a, sr, checker):
    assert a.ndim == 1 and len(a) > int(13.2 * sr)
    env = official_functions(checker)
    times = sorted(set(range(10600, 11201, 5)) | set(range(10800, 11021)))
    rows = []
    for tick in times:
        t = tick / 1000
        F = int(.005 * sr)
        i = int(round(t * sr))
        w = a[max(0, i - 2 * sr):i + 2 * sr]
        n = len(w) // (2 * F)
        ref = np.sqrt(np.mean(w[:n * 2 * F].reshape(n, 2 * F) ** 2, axis=1)).max() + 1e-12
        level = lambda j: float(20 * np.log10(np.sqrt(np.mean(a[j:j + F] ** 2)) / ref + 1e-12))
        pre = max(level(j) for j in range(i - 6 * F, i, F))
        post = max(level(j) for j in range(i, i + 8 * F, F))
        rows.append({'time_s': t, 'pre30ms_max_dB': pre, 'post40ms_max_dB': post,
                     'this5ms_dB': level(i),
                     'unchanged_original_G45_accepts': bool(env['确认可收']('61', a, sr, t))})
    return rows


def main():
    import soundfile as sf
    ap = argparse.ArgumentParser()
    ap.add_argument('--wav', type=Path, required=True)
    ap.add_argument('--tools', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    checker = args.tools / '高亮同步核对.py'
    a, sr = sf.read(args.wav)
    a = np.asarray(a, float)
    raw = args.wav.read_bytes()
    report = {'article': '61', 'purpose': 'actual native a.wav scalar diagnostic only',
              'quality_acceptance': False, 'confirmation_created': False,
              'source_audio_or_checker_modified': False,
              'actual_WAV_sha256': hashlib.sha256(raw).hexdigest(),
              'actual_WAV_md5_first12': hashlib.md5(raw).hexdigest()[:12],
              'actual_WAV_sample_rate': sr,
              'checker_sha256': hashlib.sha256(checker.read_bytes()).hexdigest(),
              'clock': 'actual supplied work_61/a.wav clock; not public AAC clock',
              'window_s': [10.6, 11.2], 'fine_window_s': [10.8, 11.02],
              'rows': measure(a, sr, checker)}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
