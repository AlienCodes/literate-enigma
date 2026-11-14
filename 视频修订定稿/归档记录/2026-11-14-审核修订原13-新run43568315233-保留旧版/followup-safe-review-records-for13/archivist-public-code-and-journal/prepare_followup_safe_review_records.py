"""Collect only explicit source26, disabled27 helper and mirror-cleanup manifests."""
from pathlib import Path
import hashlib
import json
import prepare_safe_user_review_records as collect

B=Path(__file__).resolve().parent
A=Path('/workspace/work/video-audit70-20261113')
OUT=B/'followup-safe-review-records-for13'

def main():
    collect.DST=OUT
    OUT.mkdir(exist_ok=True)
    groups=[
      ('source26-source-and-static',A/'article26-user-review-20261114/safe-public-evidence-manifest.json','79c634da1570fbecf24addbc943ceaa1a9820c25a68041faf85b6710ce48d360'),
      ('source27-disabled-helper-only',A/'article27-user-review-20261114/pending-controlled-helper-evidence.json','ae6fc0b448a2bc604e829c7b3c0b9e5630386dc58ef12cab8dca578f393817f5'),
      ('root-authorized-mirror-cleanup-metadata',A/'mirror-cleanup-20261114/safe-public-evidence-manifest.json','ef21492a830a4a231e1b880220bb9e43bda3bb542532de22a6444e171418e03d'),
    ]
    bindings=[]
    for label,p,sha in groups:
        assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
        manifest=json.loads(p.read_text())
        if label=='source27-disabled-helper-only':
            assert manifest['quality_acceptance'] is False and manifest['profile_enabled'] is False and manifest['true_positive_official_video_claimed'] is False
        for row in manifest['files']:
            source=Path(row['path']);assert source.suffix.lower() in ['.json','.py','.md','.log','.png','.jpg','.txt','.diff','.csv','.sh','.yaml','.yml']
            rel=row.get('safe_archive_relative_path',row.get('relative_path'));assert rel
            collect.put(source,Path(label)/rel,row['sha256'],row['bytes'])
        collect.put(p,Path(label)/p.name,sha)
        bindings.append({'label':label,'exact_manifest_path':str(p),'manifest_sha256':sha,'declared_files':len(manifest['files']),'declared_bytes':sum(r['bytes'] for r in manifest['files']),'not_new_native_video_acceptance':True})
    for name in ['prepare_followup_safe_review_records.py','prepare_safe_user_review_records.py','FINAL70-ACTIVE-REVISION-SELECTION-TODO.json']:
        collect.put(B/name,Path('archivist-public-code-and-journal')/name)
    collect.save(OUT/'EXACT-SAFE-MANIFEST-BINDINGS.json',{'groups':bindings,'no_recursive_mirror_collection':True,'no_private_PCM_GT_cache_models_or_new_media_collected':True,'source26_static_is_not_a_video_pass':True,'source27_disabled_helper_is_not_production_QC_acceptance':True,'mirror_cleanup_restore_scripts_are_saved_not_executed_by_archivist':True})
    print(json.dumps({'snapshot_dir':str(OUT),'groups':bindings},ensure_ascii=False))

if __name__=='__main__':main()
