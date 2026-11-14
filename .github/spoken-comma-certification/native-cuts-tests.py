#!/usr/bin/env python3
"""Real complete02 source, original raw caches, actual shell and quality programs."""
import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--tools', type=Path, required=True)
p.add_argument('--requests', type=Path, required=True)
p.add_argument('--original-shell', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
parent_work = Path.cwd()
W = parent_work.parent / 'actual-reviewed-cuts-02'
W.mkdir(exist_ok=True)
subprocess.run([sys.executable, str(a.tools / '出片指纹.py'), '--拷', str(W)], check=True)
(W / 'scripts').mkdir(exist_ok=True)
if not (W / 'fonts').exists():
    (W / 'fonts').symlink_to(a.tools / 'fonts', target_is_directory=True)
os.chdir(W)
source = W / 'scripts/02.json'
raw = (a.requests / '02.json').read_bytes()
request = json.loads(raw)
AUTO = a.tools / '自动切点.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(AUTO) == 'c3d2e6a911a33e57fbe629bc97ca332cbb2cce73d6aec9f3dbebd731aa1e6562'
logs = []
base_env = {**os.environ, 'XG_TOOLS': str(a.tools), 'XG_WORK': str(W), 'XG_KEEP_REVIEWED_GAIN': '1', 'XG_KEEP_REVIEWED_ENDING': '1'}


def run(args, label, env=None, good=True):
    r = subprocess.run([str(x) for x in args], cwd=W, env=env or base_env, text=True, capture_output=True)
    logfile = a.output.parent / (label + '.log')
    logfile.write_text(r.stdout + '\n' + r.stderr)
    logs.append({'name': label, 'exit': r.returncode, 'log_SHA256': sha(logfile)})
    if good:
        assert r.returncode == 0, label + ': ' + (r.stdout + r.stderr)[-2200:]
    return r


def fresh():
    source.write_bytes(raw)
    work = W / 'work_02'
    if work.exists():
        shutil.rmtree(work)


def encoded_aac(label):
    code = "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"
    ff = subprocess.check_output([sys.executable, '-c', code], text=True).strip()
    af = (a.tools / '配音/AF.txt').read_text().strip()
    out = W / (label + '.m4a')
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', str(W / 'work_02/a.wav'), '-af', af,
                    '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(out)], check=True)
    adts = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(out), '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])
    out.unlink()
    return hashlib.sha256(adts).hexdigest()


cases, full_sources = [], []
# Actual original5 shell and candidate default must create the same physical
# intervals and audio. Only the new explicit mode preserves the reviewed data.
for name, shell, mode in [('original-default', a.original_shell, None),
                           ('candidate-default', a.tools / '草稿声音.sh', '0'),
                           ('candidate-preserve', a.tools / '草稿声音.sh', '1')]:
    fresh()
    env = dict(base_env)
    env.pop('XG_KEEP_REVIEWED_CUTS', None)
    if mode is not None:
        env['XG_KEEP_REVIEWED_CUTS'] = mode
    run(['bash', shell, '02'], 'real02-' + name + '-complete-shell', env)
    result = json.loads(source.read_text())
    full_sources.append(result)
    # Render directly again using the real original producer; no shadow audio.
    run([sys.executable, 'make_video.py', source, '_cuts-test02.mp4'], 'real02-' + name + '-actual-PCM', {**env, 'AUDIO_ONLY': '1'})
    row = {'case': name, 'mode': mode, 'S14_NV': result.get('非人声区间', {}).get('S14'),
           'all_NV': result.get('非人声区间', {}), 'source_SHA256': sha(source),
           'actual_PCM_SHA256': sha(W / 'work_02/a.wav'), 'actual_AAC_ADTS_SHA256': encoded_aac(name)}
    cases.append(row)
    if mode == '1':
        preserved = source.read_bytes()
        assert result['非人声区间'] == request['非人声区间']
        text = (a.output.parent / ('real02-' + name + '-complete-shell.log')).read_text()
        assert '  删 S14' in text, 'Real original automatic suggestion must remain visible and saved'
        assert row['actual_PCM_SHA256'] == 'c21872d4db894f37b1b8b5db752917f9f6ef60680834ca4cccef9b806b5c1c52'
        assert row['actual_AAC_ADTS_SHA256'] == 'c026dfff1f9591a3e11539cc40e87e3da0ed247cec3bf883d265011126e094d3'
        # Original new-noise positive controls run on actual02's audio: four
        # injected bad noises must be detected; no scanner or threshold changes.
        run([sys.executable, a.tools / '纯人声核对.py', '02', '--自检'], 'real02-original-new-noise-selftests', env)
        assert source.read_bytes() == preserved
assert cases[0]['all_NV'] == cases[1]['all_NV']
assert full_sources[0] == full_sources[1], 'Default full pipeline JSON differs from previous certified5 shell'
assert cases[0]['actual_PCM_SHA256'] == cases[1]['actual_PCM_SHA256'] == 'e1aa1d853e655f754c2515023f0c78582377d8e1f90e1d89347e0596d692a40f'
assert cases[0]['actual_AAC_ADTS_SHA256'] == cases[1]['actual_AAC_ADTS_SHA256'] == '22618683aa7cbefbac743d8aec4fec64ac6610cbb4c92329b92ba13b6412a849'
assert cases[0]['S14_NV'] == request['非人声区间']['S14'] + [[4.183958, 4.275, '紧贴词尾']]
# New mode cannot make an invalid existing physical deletion legal. This must
# still fail in the original producer's original typed interval gate.
bad = copy.deepcopy(request)
bad['非人声区间']['S14'].append([-0.1, 0.1])
source.write_text(json.dumps(bad, ensure_ascii=False, indent=1))
r = run([sys.executable, 'make_video.py', source, '_cuts-bad02.mp4'], 'real02-original-invalid-NV-rejected', {**base_env, 'XG_KEEP_REVIEWED_CUTS': '1', 'AUDIO_ONLY': '1'}, good=False)
assert r.returncode != 0 and '非人声区间不对' in r.stdout + r.stderr
source.write_bytes(raw)
report = {'status': 'passed_real_complete02_keep_reviewed_cuts_mode', 'full_actual_shell_no_routing_stubs': True,
          'all_three_actual_shell_cases': cases,
          'default_original5_vs_candidate_physical_NV_PCM_AAC_exact': True,
          'default_original5_vs_candidate_complete_JSON_deep_exact': True,
          'explicit_mode_all_original_NV_preserved': True,
          'explicit_mode_actual_PCM_and_AAC_match_accepted_original': True,
          'real_automatic_S14_proposal_still_printed_and_saved': True,
          'original_new_noise_selftests_passed_on_actual02': True,
          'existing_bad_typed_NV_still_rejected_by_original_producer': True,
          'automatic_cut_algorithm_SHA256_unchanged': sha(AUTO),
          'all_original_checker_algorithms_and_thresholds_unchanged_from_certified5core': True,
          'real_calls': logs, 'private_raw_or_processed_PCM_exported': False,
          'article_audio_or_video_accepted_here': False}
a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'real_calls'}, ensure_ascii=False, indent=2))
