#!/usr/bin/env python3
"""One new complete five-program certificate; keep successful four-core immutable."""
import ast
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

O = Path(__file__).resolve().parent
OLD = O.parent / 'keep-reviewed-ending'
PKG = O / 'native-ready/.github/reviewed-five-core-certification'
if PKG.exists():
    shutil.rmtree(PKG)
shutil.copytree(OLD / 'native-ready/.github/reviewed-ending-certification', PKG)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
candidate = Path('/workspace/work/video-audit70-20261113/audio16-A23-readonly/读音核对-selftest-candidate.py')
assert sha(candidate) == '50f4363bb2fc2930be59904cdccfa44fd46f14393a0385c7846028ee25b4e84c'
raw = subprocess.check_output(['git', 'show', 'fc0b56af9a0ac0e97015548b756d4e51d66dc2ea:视频/工具/读音核对.py'], cwd='/workspace/work/github-publication/target')
assert hashlib.sha256(raw).hexdigest() == '0a3b97e1179e47c0593f69286f4206eecc123cc7ec5d5adf4f5e62457c228a41'
dest = PKG / 'original-source/视频/工具/读音核对.py'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_bytes(raw)
shutil.copyfile(candidate, PKG / 'patch/视频/工具/读音核对.py')
shutil.copyfile('/workspace/work/video-audit70-20261113/audio16-A23-readonly/selftest-candidate.diff', PKG / 'diff/读音核对.py.diff')
shutil.copyfile('/workspace/work/video-audit70-20261113/payload/视频/脚本/16.json', PKG / 'request-fixtures/16.json')
shutil.copyfile(O / 'native-pronunciation-tests.py', PKG / 'native-pronunciation-tests.py')
manifest = json.loads((PKG / 'overlay-manifest.json').read_text())
manifest['files'].append({'path': '视频/工具/读音核对.py', 'main_SHA256': hashlib.sha256(raw).hexdigest(), 'patch_SHA256': sha(candidate),
                          'scope': 'selftest fault injection only; keep compound registry and inject actual uncorrected espeak IPA, finally restore; all normal checker AST unchanged'})
manifest['scope'] = 'Previously certified four-program repair plus real pronunciation selftest fault-injection repair. Original normal checker, producer, audit, thresholds and dictionaries unchanged.'
(PKG / 'overlay-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
code = (PKG / 'native-certify.py').read_text().replace('.github/reviewed-ending-certification', '.github/reviewed-five-core-certification').replace('keep-reviewed-ending', 'reviewed-five-core')
anchor = " r=run([sys.executable,PKG/'native-ending-tests.py'"
assert anchor in code
additional = " r=run([sys.executable,PKG/'native-pronunciation-tests.py','--tools',T,'--requests',PKG/'request-fixtures','--original-tool',PKG/'original-source/视频/工具/读音核对.py','--output',OUT/'real-pronunciation-selftest-tests.json'],'new-pronunciation-selftest-real-tests',cwd=W);assert r.returncode==0\n"
code = code.replace(anchor, additional + anchor)
ast.parse(code)
(PKG / 'native-certify.py').write_text(code)
workflow = (OLD / 'native-ready/.github/workflows/reviewed-ending-certification.yml').read_text()
workflow = workflow.replace('已审结尾接点保留与四程序完整快测', '已审声音与读音自检五程序完整快测').replace('reviewed-ending-certification', 'reviewed-five-core-certification').replace('keep-reviewed-ending', 'reviewed-five-core').replace('core-ending-certification-', 'core-five-certification-')
path = O / 'native-ready/.github/workflows/reviewed-five-core-certification.yml'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(workflow)
launch = (OLD / 'launch-native-certification.py').read_text().replace('.github/reviewed-ending-certification/', '.github/reviewed-five-core-certification/').replace('.github/workflows/reviewed-ending-certification.yml', '.github/workflows/reviewed-five-core-certification.yml').replace('Independently certify valid reviewed ending-point preservation with original complete fastcheck', 'Independently certify five-program repair with real pronunciation negative controls and original complete fastcheck')
ast.parse(launch)
(O / 'launch-native-certification.py').write_text(launch)
print(json.dumps({'status': 'isolated_five_core_unique_full_package_ready_not_launched', 'program_count': len(manifest['files']),
                  'original_pronunciation_SHA256': hashlib.sha256(raw).hexdigest(), 'candidate_pronunciation_SHA256': sha(candidate),
                  'prior_core4_immutable_unchanged': True, 'private_PCM_uploaded': False}, ensure_ascii=False))
