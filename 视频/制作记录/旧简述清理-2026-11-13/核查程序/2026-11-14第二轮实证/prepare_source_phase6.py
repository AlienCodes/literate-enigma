"""Copy completed public-source fixes and scalar QA evidence into the existing repository archive.

No private PCM, reference arrays, TTS cache, credentials, rendered media, or remote changes.
"""
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

B = Path(__file__).resolve().parent
PAY = B / 'payload'
REL = Path('视频/制作记录/旧简述清理-2026-11-13')
DEST = PAY / REL / '核查记录/2026-11-14阶段进度'
EXTENSIONS = {'.json', '.py', '.sh', '.md', '.txt', '.csv', '.yaml', '.yml', '.log'}
EXCLUDE_PARTS = {'.git', 'mirror', '__pycache__', 'publication', 'node_modules', 'venv', '.venv'}
rows = []

def copy_file(source, target):
    raw = source.read_bytes()
    # Retrieval reports must not accidentally retain an expiring signed capability URL.
    assert not re.search(rb'https?://[^\s\x22\x27]*oaiusercontent\.com', raw), source
    assert not re.search(rb'https?://[^\s\x22\x27]*[?&]sig=', raw, re.I), source
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({'source': str(source), 'archive_path': str(target.relative_to(PAY)),
                 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})

for name in (
    'readonly-audio-replay-43536744065',
    'first3core7-failure-triage',
    'audio07-original-post-readonly',
    'A21-specific-repair-text-preflight',
    '44-raw-clock-text-preflight',
    'audio-a21-15-17-18-30-readonly',
    'canonical-final-source-backflow-plan-20261114',
    'pending-production-status-20261114',
    'progress-observations',
):
    source = B / name
    if not source.exists():
        continue
    for file in sorted(source.rglob('*')):
        parts = file.relative_to(source).parts
        if not file.is_file() or file.suffix not in EXTENSIONS or set(parts) & EXCLUDE_PARTS:
            continue
        copy_file(file, DEST / name / file.relative_to(source))

for name in ('44-actual-raw-G45-specific-clock-correction-proposal.json',
             '44-raw-clock-specific-application.json'):
    source = B / 'public-audio-inspection' / name
    if source.exists():
        copy_file(source, DEST / 'public-audio-inspection' / name)

for name in ('LATEST-WORK-STATE.json', 'LATEST-SCOPE-UPDATE.json',
             'recovered-canonical-native/43538347790/recovery10-11-metadata-diagnostic.json'):
    source = B / name
    if source.exists():
        copy_file(source, DEST / name)

DELIVERY = Path('/workspace/work/video-revision-delivery')
for name in ('recovered-canonical-3-status.json', 'recovered-canonical-5-status.json'):
    source = DELIVERY / name
    if source.exists():
        copy_file(source, DEST / name)
source = DELIVERY / 'recovered-canonical-10-11-status.json'
if source.exists():
    copy_file(source, DEST / source.name)

CODE_DEST = PAY / REL / '核查程序/2026-11-14实际修订与恢复'
for name in ('publish_sources.py', 'save_current_journal.py', 'refresh_work_state.py', 'prepare_source_phase6.py'):
    copy_file(B / name, CODE_DEST / name)
for folder in ('recovery-engine-frozen-20261114-v1', 'recovery-engine-frozen-20261114-v2-five',
               'recovery-engine-frozen-20261114-v3-exact10-11'):
    source = DELIVERY / folder
    if not source.exists():
        continue
    for file in sorted(source.rglob('*')):
        parts = file.relative_to(source).parts
        if file.is_file() and file.suffix in EXTENSIONS and not set(parts) & EXCLUDE_PARTS:
            copy_file(file, CODE_DEST / folder / file.relative_to(source))

CI = Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch')
for name in ('audio-a21-qc.py', 'audio-a21-qc-reference.json', 'approved_illustration_resource.py'):
    source = CI / name
    if source.exists():
        copy_file(source, CODE_DEST / 'ci-specific-audio-and-image-candidates' / name)

FROZEN = Path('/workspace/work/video-official-ready41-core3-frozen-20261114')
if FROZEN.exists():
    programs = json.loads((FROZEN / 'program-freeze-manifest.json').read_text())['program_sha256']
    for name, expected in programs.items():
        source = FROZEN / name
        observed = hashlib.sha256(source.read_bytes()).hexdigest()
        if observed != expected:
            binding = json.loads((FROZEN / 'after-start-articles-binding.json').read_text())
            assert name == binding['path'] and observed == binding['actual_sha256']
            assert binding['matches_immutable_launched_commit_bytes'] is True
        copy_file(source, CODE_DEST / 'ready41-actual-frozen-production' / name)
    for name in ('TASK-STATE.json', 'program-freeze-manifest.json', 'after-start-articles-binding.json', 'launch.log', 'start.py'):
        source = FROZEN / name
        copy_file(source, CODE_DEST / 'ready41-actual-frozen-production' / name)

manifest = {
    'recorded_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'local_preparation_only_not_remote_publication',
    'public_records_copied': len(rows), 'bytes': sum(x['bytes'] for x in rows),
    'latest_book_scope': '475页正式总册，仅原批准插图、中英文章、词汇及篇末简述，保留批准封面序言目录封底；无句析语法练习新章节',
    'new_4K_acceptance_claims_only_from_actual_passed_handoffs': True,
    'private_PCM_GT_TTS_cache_credentials_exported': False,
    'records': rows,
    'source_scripts_SHA256': {f'{n:02d}': hashlib.sha256((PAY / f'视频/脚本/{n:02d}.json').read_bytes()).hexdigest() for n in range(1, 71)},
    'GEN_SHA256': {f'{n:02d}': hashlib.sha256((PAY / f'视频/工具/初稿生成/gen{n:02d}.py').read_bytes()).hexdigest() for n in range(1, 71)},
}
target = DEST / 'phase6-prepared-file-manifest.json'
target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'files': len(rows), 'bytes': manifest['bytes'], 'manifest': str(target),
                  'remote_write_executed': False}, ensure_ascii=False))
