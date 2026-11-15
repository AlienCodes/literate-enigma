"""Review-only finite raw reader. Not installed or called by any production writer."""
from pathlib import Path
import hashlib
import json

TABLE = Path(__file__).with_name('EXACT17-READONLY-AUTHORITY-PINS.json')
TABLE_SHA256 = '3205f2dc9190d86e70a7365bde943f035e13b442be65b377bc83b9d1239930cd'


def check_exact_authority(raw, sid, book):
    """Validate one of 17 already-observed immutable originals, never arbitrary prose."""
    assert type(raw) is bytes and type(sid) is str and type(book) is str
    table_raw = TABLE.read_bytes()
    assert hashlib.sha256(table_raw).hexdigest() == TABLE_SHA256
    known = json.loads(table_raw)
    assert sid in known
    item = known[sid]
    assert book == item['book_order']
    assert len(raw) == item['raw']['bytes']
    assert hashlib.sha256(raw).hexdigest() == item['raw']['sha256']
    doc = json.loads(raw)
    assert doc['source_id'] == sid and type(doc['source_id']) is str
    expected_book_type = {'str': str, 'int': int}[item['book_order_type']]
    assert type(doc['book_order']) is expected_book_type
    assert doc['book_order'] == (book if expected_book_type is str else int(book))
    assert ('kind' in doc) is item['kind_present']
    if item['kind_present']:
        assert doc['kind'] == item['kind']
    assert ('author' in doc) is item['author_present']
    if item['author_present']:
        assert doc['author'] == item['author']
    assert type(doc[item['quote_key']]) is str and doc[item['quote_key']] == item['quote']
    return {
        'kind': 'assistant-derived-exact-known-final-authority-reader-receipt-not-original-user-schema',
        'source_id': sid,
        'book_order': book,
        'actual_original_raw_sha256': item['raw']['sha256'],
        'actual_original_raw_bytes': item['raw']['bytes'],
        'actual_quote_key': item['quote_key'],
        'actual_quote_verbatim': item['quote'],
        'finalization_authority_observed': True,
        'original_missing_fields_not_added_or_fabricated': True,
        'media_or_audio_QA_pass_or_dual_archive_or_current_completion_granted': False,
    }
