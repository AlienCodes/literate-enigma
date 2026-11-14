"""Preserve only actual completed titanic publication records, no media."""
from pathlib import Path
import archive_reviewed_publication_records as records

B=Path(__file__).resolve().parent
records.W=B/'titanic-publication-record-assets-20261114'
records.PREFIX=Path('发行记录/2026-11-14-审核后书25永不沉没的神话4K发布')
records.ASSET_BRANCH='codex/titanic-publication-records-20261114'
records.ADDITIONAL_PROGRAMS=['archive_titanic_publication_records.py']
records.PUBLICATIONS=[('book25',Path('/workspace/work/titanic-reviewed-4k-v1'),445140014,801,'276eae3aea3dfc36bdd942b7f3e947c14bc790cebc914ad67cb2bf5867a5313e')]

if __name__=='__main__':records.main()
