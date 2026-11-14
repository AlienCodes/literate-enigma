#!/usr/bin/env python3
"""One new original full certificate for the same five programs, new shell mode."""
import ast
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

O = Path(__file__).resolve().parent
OLD = O.parent / 'reviewed-five-core'
PKG = O / 'native-ready/.github/reviewed-cuts-certification'
if PKG.exists():
    shutil.rmtree(PKG)
shutil.copytree(OLD / 'native-ready/.github/reviewed-five-core-certification', PKG)
B = Path('/workspace/work/video-audit70-20261113/audio02-S14-readonly/keep-reviewed-cuts-candidate')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
candidate = B / '草稿声音.sh'
assert sha(candidate) == '43fc6a1acdae6bb1c2252178bf034407400bbbe92eb1752053f3047da9760491'
assert sha(B / 'original-5core-草稿声音.sh') == 'c45c66e3cf68a380f5c829600cf6b0ed69f49f24c65e91c0330ed17d1a85475e'
shutil.copyfile(candidate, PKG / 'patch/视频/工具/草稿声音.sh')
shutil.copyfile(B / 'original-5core-草稿声音.sh', PKG / 'original-source/视频/工具/草稿声音.sh')
shutil.copyfile(B / '草稿声音-minimal.diff', PKG / 'diff/草稿声音-cuts-mode.diff')
shutil.copyfile('/workspace/work/video-audit70-20261113/payload/视频/脚本/02.json', PKG / 'request-fixtures/02.json')
shutil.copyfile(O / 'native-cuts-tests.py', PKG / 'native-cuts-tests.py')
manifest = json.loads((PKG / 'overlay-manifest.json').read_text())
shell = next(x for x in manifest['files'] if x['path'] == '视频/工具/草稿声音.sh')
shell['patch_SHA256'] = sha(candidate)
shell['certified_before_SHA256'] = sha(B / 'original-5core-草稿声音.sh')
shell['cuts_mode_scope'] = 'Explicit readonly automatic-cut suggestions; original default arguments and actual auto algorithm unchanged; all original quality checks retained'
manifest['scope'] = 'Same five unique programs as prior successful certificate; only shell adds explicit preservation of already reviewed physical NV intervals. New full certificate/stamp required.'
(PKG / 'overlay-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
code = (PKG / 'native-certify.py').read_text().replace('.github/reviewed-five-core-certification', '.github/reviewed-cuts-certification').replace('reviewed-five-core', 'keep-reviewed-cuts')
code = code.replace("'XG_KEEP_REVIEWED_ENDING':'1' if a.variant=='keep-reviewed-cuts' else '0'", "'XG_KEEP_REVIEWED_ENDING':'1' if a.variant=='keep-reviewed-cuts' else '0','XG_KEEP_REVIEWED_CUTS':'1' if a.variant=='keep-reviewed-cuts' else '0'")
anchor = " r=run([sys.executable,PKG/'native-pronunciation-tests.py'"
extra = " r=run([sys.executable,PKG/'native-cuts-tests.py','--tools',T,'--requests',PKG/'request-fixtures','--original-shell',PKG/'original-source/视频/工具/草稿声音.sh','--output',OUT/'real-cuts-mode-tests.json'],'new-cuts-mode-real-tests',cwd=W);assert r.returncode==0\n"
assert anchor in code
code = code.replace(anchor, extra + anchor)
# Restore every actual02 original raw/timed mother needed by the genuine
# complete pipeline. They remain private cache resources, never in artifacts.
resources = json.loads((PKG / 'ending-cache-resources.json').read_text())
proof = json.loads(Path('/workspace/work/video-audit70-20261113/audio02-S14-readonly/02-whole-original-source-counterfactual-proof.json').read_text())
oldmap = json.loads(subprocess.check_output(['git', 'show', 'fc0b56af9a0ac0e97015548b756d4e51d66dc2ea:视频/配音缓存/老条目指纹.json'], cwd='/workspace/work/github-publication/target'))['条目']
seen = {x['repository_path'] for x in resources['files']}
for f in proof['G72_mother_cache_scalar_provenance']:
    assert oldmap[f['key']] == f['pkl_full_sha256'][:16]
    rel = '视频/配音缓存/' + f['key']
    if rel not in seen:
        resources['files'].append({'repository_path': rel, 'SHA256': f['pkl_full_sha256']})
        seen.add(rel)
(PKG / 'ending-cache-resources.json').write_text(json.dumps(resources, ensure_ascii=False, indent=2) + '\n')
ast.parse(code)
(PKG / 'native-certify.py').write_text(code)
workflow = (OLD / 'native-ready/.github/workflows/reviewed-five-core-certification.yml').read_text().replace('已审声音与读音自检五程序完整快测', '已审切点保留与五程序完整快测').replace('reviewed-five-core-certification', 'reviewed-cuts-certification').replace('reviewed-five-core', 'keep-reviewed-cuts').replace('core-five-certification-', 'core-cuts-certification-')
start = workflow.index('          sparse-checkout: |\n', workflow.index('          path: ending-reference-resources'))
end = workflow.index('      - uses: actions/setup-python', start)
workflow = workflow[:start] + '          sparse-checkout: |\n' + ''.join('            /' + x['repository_path'] + '\n' for x in resources['files']) + workflow[end:]
path = O / 'native-ready/.github/workflows/reviewed-cuts-certification.yml'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(workflow)
launch = (OLD / 'launch-native-certification.py').read_text().replace('.github/reviewed-five-core-certification/', '.github/reviewed-cuts-certification/').replace('.github/workflows/reviewed-five-core-certification.yml', '.github/workflows/reviewed-cuts-certification.yml').replace('Independently certify five-program repair with real pronunciation negative controls and original complete fastcheck', 'Independently certify reviewed cuts preservation with real02 read-write controls and original complete fastcheck')
ast.parse(launch)
(O / 'launch-native-certification.py').write_text(launch)
report = {'status': 'isolated_unique_cuts_mode_full_package_ready_not_launched', 'unique_programs': len(manifest['files']),
          'shell_previous_SHA256': sha(B / 'original-5core-草稿声音.sh'), 'shell_candidate_SHA256': sha(candidate),
          'unchanged_auto_algorithm_SHA256': 'c3d2e6a911a33e57fbe629bc97ca332cbb2cce73d6aec9f3dbebd731aa1e6562',
          'exact_old_G72_cache_resources_private_count': len(resources['files']),
          'prior5core_bundle_unchanged': True, 'production_source_or_core_written': False}
(O / 'native-package-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False))
