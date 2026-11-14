"""Save only newly completed public evidence and current sources after phase8."""
import ast,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
B=Path(__file__).resolve().parent
# Reuse the existing signed-URL guard and explicit public-extension allowlist.
original=ast.parse((B/'prepare_source_phase8.py').read_text()); initial=[]
for node in original.body:
    if isinstance(node,ast.For):break
    initial.append(node)
ns={'__file__':str(B/'prepare_source_phase8.py')};exec(compile(ast.Module(body=initial,type_ignores=[]),str(B/'prepare_source_phase8.py'),'exec'),ns)
PAY=ns['PAY']; REL=ns['REL'];ns['DEST']=DEST=PAY/REL/'核查记录/2026-11-14第四轮增量实证';ns['CODE']=CODE=PAY/REL/'核查程序/2026-11-14第四轮增量实证';copy=ns['copy'];tree=ns['tree'];rows=ns['rows']
for folder in ('audio49-explicit95-equivalence','onset18-05-original-raw',
 'diagnosis61-native-replay-20261114','diagnosis61-public-20261114',
 'diagnosis66-public-and-raw-20261114','audio65-69-source-readonly',
 'readonly-audio48-67-68-70-43543967031','ready41-current-closeout-20261114'):
    tree(B/folder,DEST/folder)
for name in ('LATEST-WORK-STATE.json','LATEST-SCOPE-UPDATE.json','PUBLISHED-SOURCE-STATE.json',
 'phase8-actual-dual-subtree-verification.json','phase8-actual-verification.log','phase8-publication.log',
 'closed-legacy-print-identical-storage-deduplication.json','closed-print-identical-media-candidates.json',
 'local-git-auto-maintenance-observation.json'):
    copy(B/name,DEST/name)
D=Path('/workspace/work/video-revision-delivery')
for folder in ('native-inline-engine-frozen-20261114-v4-exact07-md-sync','history/low-disk-publication-before-20261114'):
    tree(D/folder,CODE/folder)
for name in ('delivery.py','release_actions.py','release_contract.py','assemble_actual_delivery.py',
 'check_low_disk_build.py','low-disk-hardlink-build-verification.json',
 'low-disk-publication-regression.log','actual06-live-artifact-reuse-observation.json'):
    copy(D/name,CODE/'current-final-transport'/name)
copy(D/'final70-assembly/collection-progress.json',DEST/'actual-passed-collection-progress.json')
owner=Path('/workspace/work/video-archive-batches-20261114')
for folder in ('operations-native43548189084-07','operations-native43554669373-46'):
    tree(owner/folder,DEST/'视频永久归档收口实证'/folder)
for name in ('CURRENT-ARCHIVE-STATE.json','completed-bare-cleanup-52-20261114.json',
 'completed-bare-cleanup-53-20261114.json','integration-plan53.json','declared-evidence51-record-membership-audit.json'):
    if (owner/name).exists():copy(owner/name,DEST/'视频永久归档收口实证'/name)
for name in ('prepare_source_phase9.py','refresh_work_state.py','save_current_journal.py','verify_source_phase8.py','publish_sources.py'):
    copy(B/name,CODE/name)
manifest={'recorded_utc':datetime.now(timezone.utc).isoformat(),'scope':'Incremental public records/current approved source; not complete70 publication',
 'files':len(rows),'bytes':sum(r['bytes']for r in rows),'new_private_PCM_GT_models_credentials_exported':False,'records':rows,
 'canonical_source_SHA256':{f'{n:02d}':hashlib.sha256((PAY/f'视频/脚本/{n:02d}.json').read_bytes()).hexdigest()for n in range(1,71)}}
(DEST/'phase9-prepared-file-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'files':len(rows),'bytes':manifest['bytes']},ensure_ascii=False))
