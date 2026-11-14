"""Save actual book22 release and book29 review-only prerelease records."""
from pathlib import Path
import archive_reviewed_publication_records as records

B=Path(__file__).resolve().parent
records.W=B/'book22-preview29-publication-record-assets-20261114'
records.PREFIX=Path('发行记录/2026-11-14-书22修订与书29仅效果审核样片公开回执')
records.ASSET_BRANCH='codex/book22-preview29-publication-records-20261114'
records.ADDITIONAL_PROGRAMS=['archive_book22_and_preview29_publication_records.py']
records.PUBLICATIONS=[
    ('book22-reviewed-final',Path('/workspace/work/forbidden-zone-reviewed-4k-v1'),445147830,804,'912feee4b5a661fb35a3d851ad46bf5c774d33141855ba02602eec1487dcb689'),
    ('book29-user032-review-only-preview',Path('/workspace/work/tu-youyou-pause-preview-4k-v1'),445165398,853,'6c1fc8eac890123ac8f1ca99bcbb798d8e427c520b1a1310eec99daa7d785068'),
]

if __name__=='__main__':records.main()
