"""Prepare actual approved source27 repair records without touching PDF/media."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

B=Path(__file__).resolve().parent
H=Path('/workspace/work/video-audit70-20261113/article27-user-review-20261114')
W=B/'operations-review27-43573500890-revision1'
def main():
    out=B/'safe-source27-records-for-new-revision';out.mkdir(exist_ok=True)
    groups=[('text-static-source-history',H/'safe-public-evidence-manifest.json','6218eb110730ae607f5e6e88e222dafd54b2079c34a180baf767af12ece8a26b'),('disabled-proposal-history-not-production',H/'pending-controlled-helper-evidence.json','ae6fc0b448a2bc604e829c7b3c0b9e5630386dc58ef12cab8dca578f393817f5'),('actual-final-controlled-QC-immutable-code-positive-negatives',H/'controlled-QC-final-safe-evidence-manifest.json','85e10ad6ec60939b63507458af13aabcf7db0d37108092fa30a37272f4aff670')]
    bindings=[]
    for label,manifest,sha in groups:
        assert hashlib.sha256(manifest.read_bytes()).hexdigest()==sha;q=json.loads(manifest.read_text())
        for row in q['files']:
            src=Path(row['path']);assert src.is_absolute();rel=Path(row['safe_archive_relative_path']);assert not rel.is_absolute() and '..' not in rel.parts
            assert src.suffix.lower() in ['.json','.py','.md','.log','.png','.jpg','.txt','.csv','.diff','.sh','.yaml','.yml'];raw=src.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
            dst=out/label/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists():assert dst.read_bytes()==raw
            elif src.suffix.lower() in ['.png','.jpg']:dst.hardlink_to(src)
            else:dst.write_bytes(raw)
        (out/label/manifest.name).write_bytes(manifest.read_bytes());bindings.append({'scope':label,'manifest':str(manifest),'sha256':sha,'declared_files':len(q['files']),'bytes':sum(r['bytes'] for r in q['files'])})
    (out/'EXACT-MANIFEST-BINDINGS.json').write_text(json.dumps({'groups':bindings,'private_PCM_GT_cache_or_mother_exported':False,'proposal_history_is_not_production_acceptance':True,'raw_R_failures_and_exact_baseline_QC_evidence_kept':True},ensure_ascii=False,indent=2)+'\n')
    native=B/'run43573500890-27-review-revision1';d=B/'closure-records-for27-revision1';d.mkdir(exist_ok=True)
    records=[('previous15-final-archive-and-alias-receipt.json',B/'operations-review15-43573168894-revision1-v2/final-archive-receipt.json'),('previous15-integration-plan.json',B/'integration-plan-review15-43573168894.json'),('previous15-cleanup.json',B/'completed-bare-cleanup-review15-20261114.json'),('new27-actual-dual-blobs.json',native/'actual-dual-asset-blob-verification.json'),('new27-closed-own-media-bare.json',native/'closed-dual-asset-own-bare-cleanup-receipt.json'),('new27-download-manifest.json',B/'ready-new27-book22-exact-download-manifest.json')]
    for name in ['assets-primary.json','assets-backup.json','remote-video-byte-verification.json','prepared-archive.json']:records.append(('new27-'+name,native/name))
    for name,p in records:shutil.copyfile(p,d/name)
    shutil.copyfile(B/'CURRENT-ARCHIVE-STATE.json',d/'before27-active-and-final-alias-state.json')
    for n in range(1,36):
        p=Path('/workspace/work/first50-review-release')/f'USER-REVIEW-2026-11-14-{n:03d}.json'
        if p.exists():shutil.copyfile(p,d/p.name)
    for name in ['maintenance-pip-download-cache-20261114.json','maintenance-stale-git-transfer-cache-20261114.json']:
        p=Path('/workspace/work')/name
        if p.exists():shutil.copyfile(p,d/name)
    (d/'APPROVED-AUDIO-REPAIR-LINEAGE-NOT-NEW-QC.json').write_text(json.dumps({'kind':'facts_from_original_actualV3_not_a_new_archivist_quality_gate','source_id':'27','book_order':'22','native_run':43573500890,'handoff_sha256':'24a28525a747cd7d4b0a92ae4cf4f2224c1f9df35bee9d5f35f24a72fd1e0f84','approved_two_opening_audio_repair_applied':True,'old_accepted_AAC_claimed_identical':False,'new_canonical_to_card_to_inline_AAC_packets_preserved':7039,'actual_dedicated_report_82_checks_and_immutable_code_retained':True,'original_S12_R_false_kept_with_only_exact_approved_baseline_exception':True,'no_private_WAV_GT_or_mother_exported':True},ensure_ascii=False,indent=2)+'\n')
    args=['python',str(B/'prepare_operation.py'),'--work-dir',str(W),'--batch','2026-11-14-审核修订原27-新run43573500890-修声与最终目录同步','--asset-branch','codex/passed4k-review27-records-43573500890','--previous-inventory',str(B/'operations-review15-43573168894-revision1-v2/final-remote-cumulative-inventory.json'),'--article-work-dir',str(native),'--revision-authorization',str(B/'user-review-revisions-14-27-13-26-15-17-36-33-authorization.json')]
    for p in [d,out,B/'children-language-publication-record-assets-20261114/payload/发行记录/2026-11-14-审核后书27孩子们发明的语言4K发布']:args+=['--attach-tree',str(p)]
    for name in ['integrate_verified_batch.py','atomic-final-alias-sync-program-change-record.json','PDF-PAUSE-USER-INSTRUCTION-20261114.json','user-authorized-source28-preview-only-032.json','prepare_review27_operation.py']:args+=['--attach',str(B/name)]
    subprocess.run(args,check=True)

if __name__=='__main__':main()
