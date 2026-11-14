"""Archive completed public source fixes, original-code certificates and truthful QA records."""
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone

B = Path(__file__).resolve().parent
PAY = B / 'payload'
REL = Path('视频/制作记录/旧简述清理-2026-11-13')
DEST = PAY / REL / '核查记录/2026-11-14第二轮实证'
CODE = PAY / REL / '核查程序/2026-11-14第二轮实证'
EXT = {'.json', '.py', '.sh', '.txt', '.md', '.log', '.csv', '.diff', '.patch', '.yml', '.yaml'}
rows = []

def copy(source, target):
    raw = source.read_bytes()
    assert not re.search(rb'https?://[^\s\x22\x27]*oaiusercontent\.com', raw), source
    assert not re.search(rb'https?://[^\s\x22\x27]*[?&]sig=', raw, re.I), source
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({'source': str(source), 'archive_path': str(target.relative_to(PAY)),
                 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})

def tree(source, destination):
    if not source.exists():
        return
    for path in sorted(source.rglob('*')):
        parts = path.relative_to(source).parts
        if (not path.is_file() or path.suffix not in EXT or
            any(p in {'.git', '__pycache__', 'models', 'tts-cache', 'cache'} or p.endswith('mirror') for p in parts)):
            continue
        copy(path, destination / path.relative_to(source))

for name in ('core-overlays/keep-reviewed-ending', 'core-overlays/reviewed-five-core',
             'audio05-restored-source-readonly', 'audio05-explicit95-equivalence',
             'audio06-ending-readonly', 'audio07-original-post-readonly', 'audio16-A23-readonly',
             'audio02-S14-readonly', 'asr49-new-evidence-readonly-20261114',
             'asr46-new-evidence-readonly-20261114', 'ready41-monitor',
             'native-observation-metadata-policy-v2', 'actual-accepted-control-reconciliations',
             'layout-rebind-five-20261114', 'canonical-final-source-backflow-plan-20261114',
             'progress-observations'):
    tree(B / name, DEST / name)
for name in ('LATEST-WORK-STATE.json', 'LATEST-SCOPE-UPDATE.json',
             'verified-old-download-cache-cleanup.json'):
    copy(B / name, DEST / name)

D = Path('/workspace/work/video-revision-delivery')
for name in ('markdown-summary-sync-proposal-20261114', 'local-gh-publisher-candidate-20261114',
             'release-readonly-plan-20261114', 'native-inline-engine-frozen-20261114-v2-observation-metadata',
             'native-inline-engine-frozen-20261114-v3-voice-and-approved-summary-sync'):
    tree(D / name, CODE / name)
for name in ('delivery.py', 'release_actions.py', 'release_contract.py'):
    copy(D / name, CODE / 'current-publication-and-validation' / name)
for name in ('prepare_source_phase7.py', 'prepare_source_phase6.py', 'refresh_work_state.py',
             'save_current_journal.py', 'publish_sources.py', 'compact_completed_mirrors.py'):
    copy(B / name, CODE / name)

# A lossless temporary-source archive. Every binary test/style resource was
# separately compared byte-for-byte with the already public original Git ref.
compact = B / 'temporary-mirror-snapshots'
receipt = json.loads((compact / 'compaction-receipt.json').read_text())
archive = Path(receipt['archive'])
assert hashlib.sha256(archive.read_bytes()).hexdigest() == receipt['archive_sha256']
copy(archive, DEST / '历史临时源码镜像原字节存档.zip')
copy(compact / 'compaction-receipt.json', DEST / '历史临时源码镜像无损去重记录.json')

manifest = {'recorded_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'local_preparation_only_not_remote_publication',
            'files': len(rows), 'bytes': sum(r['bytes'] for r in rows),
            'current_book_only_illustrations_articles_vocabulary_summaries': True,
            'book_pages': 475, 'new_release_published': False,
            'new_private_PCM_GT_TTS_cache_credentials_exported': False,
            'records': rows,
            'canonical_source_SHA256': {f'{i:02d}': hashlib.sha256((PAY / f'视频/脚本/{i:02d}.json').read_bytes()).hexdigest() for i in range(1, 71)}}
target = DEST / 'phase7-prepared-file-manifest.json'
target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'files': len(rows), 'bytes': manifest['bytes'], 'manifest': str(target)}, ensure_ascii=False))
