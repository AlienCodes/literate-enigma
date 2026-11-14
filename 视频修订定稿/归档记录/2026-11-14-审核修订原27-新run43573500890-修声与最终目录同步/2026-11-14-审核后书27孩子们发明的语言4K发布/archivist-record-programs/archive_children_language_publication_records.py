"""Reuse exact small-record collector for the successful book27 publication."""
from pathlib import Path
import archive_reviewed_publication_records as records

B=Path(__file__).resolve().parent
records.W=B/'children-language-publication-record-assets-20261114'
records.PREFIX=Path('发行记录/2026-11-14-审核后书27孩子们发明的语言4K发布')
records.ASSET_BRANCH='codex/children-language-publication-records-20261114'
records.ADDITIONAL_PROGRAMS=['archive_children_language_publication_records.py']
records.PUBLICATIONS=[('book27',Path('/workspace/work/children-language-reviewed-4k-v1'),445116128,806,'b85794780ee8ee22abdf4c92c4019f3743b3351d5583649650d13f7d1511a5d6')]

if __name__=='__main__':records.main()
