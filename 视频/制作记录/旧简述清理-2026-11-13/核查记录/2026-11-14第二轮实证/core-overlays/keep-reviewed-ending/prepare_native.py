#!/usr/bin/env python3
"""Reuse the complete, already-working original full-certification resource set."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

O = Path(__file__).resolve().parent
OLD = O.parent / 'keep-reviewed-gain'
D = O / 'native-ready'
PKG = D / '.github/reviewed-ending-certification'
if PKG.exists():
    shutil.rmtree(PKG)
shutil.copytree(OLD / 'native-ready/.github/keep-reviewed-gain-certification', PKG)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((PKG / 'overlay-manifest.json').read_text())
for rel in ['视频/工具/草稿声音.sh', '视频/工具/结尾句接点.py']:
    src = O / 'patch' / rel
    dst = PKG / 'patch' / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    existing = next((f for f in manifest['files'] if f['path'] == rel), None)
    if existing:
        existing['patch_SHA256'] = sha(src)
        existing['certified_before_SHA256'] = sha(O / 'original-certified' / rel)
        existing['diff'] = str(O / 'diff' / (Path(rel).name + '.diff'))
    else:
        manifest['files'].append({'path': rel, 'main_SHA256': sha(O / 'original-pinned' / rel), 'patch_SHA256': sha(src),
                                  'certified_before_SHA256': sha(O / 'original-pinned' / rel), 'diff': str(O / 'diff' / (Path(rel).name + '.diff'))})
manifest['scope'] = 'Previously certified gain preservation and raw mother loader, plus explicit preservation of already-approved valid ending points; original producer/audit/thresholds unchanged.'
(PKG / 'overlay-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
shutil.copyfile('/workspace/work/video-audit70-20261113/payload/视频/脚本/07.json', PKG / 'request-fixtures/07.json')
dst = PKG / 'original-source/视频/工具/结尾句接点.py'
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(O / 'original-pinned/视频/工具/结尾句接点.py', dst)
shutil.copyfile(O / 'native-ending-tests.py', PKG / 'native-ending-tests.py')
for name in ['结尾句接点.py', '草稿声音.sh']:
    shutil.copyfile(O / 'diff' / (name + '.diff'), PKG / 'diff' / (name + '.diff'))
code = (PKG / 'native-certify.py').read_text()
code = code.replace('keep-reviewed-gain', 'keep-reviewed-ending').replace('.github/keep-reviewed-ending-certification', '.github/reviewed-ending-certification')
code = code.replace("'XG_KEEP_REVIEWED_GAIN':'1' if a.variant=='keep-reviewed-ending' else '0'", "'XG_KEEP_REVIEWED_GAIN':'1' if a.variant=='keep-reviewed-ending' else '0','XG_KEEP_REVIEWED_ENDING':'1' if a.variant=='keep-reviewed-ending' else '0'")
anchor = " r=run([sys.executable,T/'新管/快测.py'],'original-full-fastcheck',cwd=W)"
addition = " r=run([sys.executable,PKG/'native-ending-tests.py','--tools',T,'--requests',PKG/'request-fixtures','--original-tool',PKG/'original-source/视频/工具/结尾句接点.py','--output',OUT/'real-ending-mode-tests.json'],'new-ending-mode-real-tests',cwd=W);assert r.returncode==0\n"
assert anchor in code
code = code.replace(anchor, addition + anchor)
anchor = ' # New24 is independently tested against the current full-screen rule before legacy fixture setup.'
addition = ''' # Restore four exact pre-existing 07 raw/timed cache resources; preserve original G72 map and checks.
 ending_resources=json.loads((PKG/'ending-cache-resources.json').read_text());restored=[]
 for resource in ending_resources['files']:
  src=ROOT/'ending-reference-resources'/resource['repository_path'];dst=W.parent/'tts/cache_tts'/Path(resource['repository_path']).name
  assert sha(src)==resource['SHA256']
  assert json.loads(cachemap.read_text())['条目'][dst.name]==resource['SHA256'][:16]
  prior=sha(dst) if dst.exists() else None;shutil.copyfile(src,dst)
  restored.append({'cache_key':dst.name,'full_SHA256':sha(dst),'prior_warm_cache_SHA256':prior,'original_formal_G72_fingerprint_matches':True})
 report['restored_original_07_resources']=restored
 (OUT/'ending-cache-resources-scalar.json').write_text(json.dumps({'source_pin':ending_resources['pin'],'files':restored,'private_arrays_exported':False},ensure_ascii=False,indent=2)+'\\n')
'''
assert anchor in code
code = code.replace(anchor, addition + anchor)
(PKG / 'native-certify.py').write_text(code)
resources = {'pin': '64621068034f8b6e09836a6d97210a0e9b2f1ed6', 'files': [
    {'repository_path': '视频/配音缓存/' + key, 'SHA256': value} for key, value in [
        ('5f93aa786be55c461e644507810b77990fa6e4da.pkl', 'd92e6ab085713243e61f92fc237677e1429e4bd5dd7d7cb1e187ab29ce18547e'),
        ('37112da59e215ce16f6352f7f133828c39d090a8.pkl', '857ed318a2254d1b8971499cdc5c8d1c118957ef9978cd0653bfe7165b59fc74'),
        ('d233608ddca4ac20f4479b70e048ff0cbf2618e1.pkl', 'ffe34ea21bb7717f79d3c0c5617fe948784ef7cdb0fa0032e4899dd20686a3cc'),
        ('f001d896b4f92b9577f10482c220ac067fbb426b.pkl', '8b6b7eb96acdd38d4afbcbd122990fa5fc29fc8b64e652cb98b882686fd2fa77')]]}
(PKG / 'ending-cache-resources.json').write_text(json.dumps(resources, ensure_ascii=False, indent=2) + '\n')
workflow = (OLD / 'native-ready/.github/workflows/keep-reviewed-gain-certification.yml').read_text()
workflow = workflow.split('      - name: 独立分支保存公开认证证据', 1)[0]
workflow = workflow.replace('已审增益与原始音频参考完整快测', '已审结尾接点保留与四程序完整快测')
workflow = workflow.replace('keep-reviewed-gain-certification', 'reviewed-ending-certification').replace('keep-reviewed-gain', 'keep-reviewed-ending').replace('core-gain-certification-', 'core-ending-certification-')
workflow = workflow.replace('contents: write', 'contents: read')
anchor = '      - uses: actions/setup-python@v5'
extra = '''      - uses: actions/checkout@v4
        with:
          repository: alienalgorithm/postgraduate-vocabulary
          ref: 64621068034f8b6e09836a6d97210a0e9b2f1ed6
          path: ending-reference-resources
          filter: blob:none
          sparse-checkout-cone-mode: false
          sparse-checkout: |
'''
extra += ''.join('            /' + x['repository_path'] + '\n' for x in resources['files'])
assert anchor in workflow
workflow = workflow.replace(anchor, extra + anchor)
w = D / '.github/workflows/reviewed-ending-certification.yml'
w.parent.mkdir(parents=True, exist_ok=True)
w.write_text(workflow)
info = {'status': 'native_unique_full_certification_package_ready_not_launched', 'program_count': 4,
        'programs': manifest['files'], 'official_producer_SHA256': '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3',
        'approved_67gold_SHA256': sha(PKG / 'approved-regression/回归基准_27.json'),
        'historical_test_context_not_production_context': True, 'private_models_or_PCM_uploaded': False,
        'existing_native_resource_set_reused_full': True,
        'independent_workflow_does_not_mutate_production_workflow_or_runner': True}
(O / 'native-package-report.json').write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(info, ensure_ascii=False, indent=2))
