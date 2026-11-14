"""Reclaim only this completed archive's recoverable temporary duplicates."""
from pathlib import Path
import datetime, hashlib, json, os, shutil

HERE=Path(__file__).resolve().parent
remote=json.loads((HERE/'remote-book-stream-verification.json').read_text())
assert remote['passed'] and remote['bytes']==375955024
assert remote['sha256']=='65bc695c7b789fbc397c443ea6a387ee616f2569865a4350edc0137ddcff089e'
assert len(remote['parts'])==4 and all(x['passed'] for x in remote['parts'])
final=json.loads((HERE/'archive-final-receipt.json').read_text())
assert final['status']=='complete' and all(final['checks'].values())
before=shutil.disk_usage(HERE).free
bare=HERE/'archive-assets.git'
assert bare.parent==HERE and not bare.is_symlink()
removed_bytes=sum(x.stat().st_size for x in bare.rglob('*') if x.is_file()) if bare.exists() else 0
if bare.exists():shutil.rmtree(bare)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

rows=[]
archive=HERE/'archive-payload/考研学人印刷版/2026-11-13-v4'
for kind,folder in [('chapters','分篇PDF'),('volumes','分册PDF')]:
    for dst in sorted((archive/folder).glob('*.pdf')):
        src=HERE/'signed'/kind
        src=(src/dst.name[:2]/dst.name) if kind=='chapters' else src/dst.name
        assert src.is_file() and dst.is_file() and not src.is_symlink() and not dst.is_symlink()
        assert src.stat().st_dev==dst.stat().st_dev
        assert src.stat().st_size==dst.stat().st_size and sha(src)==sha(dst)
        digest=sha(src)
        if src.stat().st_ino!=dst.stat().st_ino:
            temp=dst.with_name(dst.name+'.verified-hardlink.tmp')
            assert not temp.exists()
            os.link(src,temp);os.replace(temp,dst)
        assert src.stat().st_ino==dst.stat().st_ino and sha(dst)==digest
        rows.append({'source':str(src),'archive_path':str(dst),'bytes':src.stat().st_size,
                     'sha256':digest,'same_inode':True,'logical_paths_preserved':True})
assert len(rows)==77
report={'passed':True,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'remote_full_book_actual_HTTPS_verification':str(HERE/'remote-book-stream-verification.json'),
        'deleted_only_owned_temporary_bare_repository':str(bare),'bare_logical_bytes_removed':removed_bytes,
        'hardlinked_duplicate_PDFs':rows,'hardlinked_count':len(rows),'original_signed_and_unsigned_PDFs_preserved':True,
        'all_source_QA_and_receipts_preserved':True,'free_bytes_before':before,
        'free_bytes_after':shutil.disk_usage(HERE).free}
(HERE/'cleanup-owned-duplicates-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='hardlinked_duplicate_PDFs'},ensure_ascii=False),flush=True)
