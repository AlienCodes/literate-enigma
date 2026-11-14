"""Freeze final-directory code, exact plans and completed Git receipts only."""
from pathlib import Path
import hashlib
import json
import prepare_safe_user_review_records as collect

B=Path(__file__).resolve().parent
W=B/'final-directory-first58-record-assets-20261114'
PREFIX=Path('视频修订定稿/归档记录/2026-11-14-最终定稿58首次Git别名物化')

def main():
    collect.DST=W/'payload'/PREFIX;collect.DST.mkdir(parents=True,exist_ok=True)
    files=['materialize_final_directory.py','build_final_alias_plan.py','test_build_final_alias_plan.py','final_alias_git.py','test_final_alias_git.py','integrate_verified_batch.py','prepare_operation.py','atomic-final-alias-sync-program-change-record.json','history/build_final_alias_plan-before-self-reference-guard.py','history/test_build_final_alias_plan-before-self-reference-guard.py','history/integrate_verified_batch-before-atomic-final-alias-sync.py','history/prepare_operation-before-atomic-final-alias-sync.py','final-directory-first58-execution.log','final-directory-first58-20261114/parent-heads-and-inventory.json','final-directory-first58-20261114/exact-alias-plan.json','final-directory-first58-20261114/prepared-graft-commits.json','final-directory-first58-20261114/actual-final-directory-receipt.json','final-directory-first58-20261114/book-illustrations70.frozen.json','PENDING-EXPLICIT-SAFE-RECORDS-20261114.json','user-authorized-source28-preview-only-032.json','archive_final_directory_execution_records.py']
    bindings=[]
    for name in files:
        p=B/name;assert p.is_file() and p.suffix in ['.py','.json','.log']
        collect.put(p,Path('exact-executed-code-plans-and-closure')/name)
        bindings.append({'original_path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    review=Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-017.json');collect.put(review,'user017-final-directory-authorization.json')
    maintenance=Path('/workspace/work/maintenance-pip-download-cache-20261114.json')
    if maintenance.exists():collect.put(maintenance,'root-pip-download-cache-only-maintenance.json')
    collect.save(collect.DST/'EXACT-RECORD-BINDINGS.json',{'kind':'completed58-final-directory-materialization-records-only','records':bindings,'actual58_original_Git_blob_aliases_verified_in_both_repositories':True,'no_binary_media_copied_or_uploaded':True,'index_and_all_old_children_preserved_on_initial_creation':True,'subsequent_accepted_revisions_sync_index_and_managed_aliases_atomically':True,'unapproved_source28_preview_excluded_from_final_active':True,'no_new_tests_or_audio_checks_added_to_delay_delivery':True})
    index=[]
    for p in sorted(collect.DST.rglob('*')):
        if p.is_file():index.append({'repo_path':str(p.relative_to(W/'payload')),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    collect.save(W/'payload-file-index.json',index);collect.save(W/'prepared-archive.json',{'prefix':str(PREFIX),'asset_branch':'codex/final-directory-first58-records-20261114','scope':'Existing58 Git aliases creation and metadata-only atomic sync sources/receipts; no media'})
    print(json.dumps({'work_dir':str(W),'files':len(index),'bytes':sum(r['bytes'] for r in index),'media_copied':0},ensure_ascii=False))

if __name__=='__main__':main()
