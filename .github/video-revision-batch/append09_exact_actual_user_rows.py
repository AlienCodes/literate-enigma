"""Append only three root-reviewed, individually verbatim source09 user rows.

This is provenance/data transport. It changes no T12 or quality rule, grants no
audio confirmation, and retains the original independent final-row protocol.
"""
from pathlib import Path
import hashlib
import json

SOURCE_SHA256 = '651f4e0057c363613fbb3984fe872b190adf826b264507807c3e4ac8b14f1909'
FINAL_ROW_SHA256 = 'd15b89a8e35cb7910f8411275531dca21285e7cc03d7b939e5765bc69a4262ad'
ROWS_SHA256 = '304ae3d331925195563e01fe18798b9a6215c203ca2cbba948b8e5e925b52b7d'
PROOFS = {
 'five-feedback.json':'a0a1e01919f343e201f35f9029f13655db1847066c7881759ebfee9a2dad61db',
 'sixth-feedback.json':'8ccaf2f216a9ee4028ddf4cec362bf36c38c740ff375e095b4728ea552f2fb77',
 'actual-final-authority.json':'9519e488124361403fabf524f016c8985119c7c93d6bd1b58bbde735b371b076',
}

def _pairs(items):
    d={}
    for k,v in items:
        if k in d:raise ValueError('duplicate JSON key')
        d[k]=v
    return d

def _load(path,digest):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Exact actual-user/source pin mismatch: '+str(path))
    return json.loads(raw,object_pairs_hook=_pairs,
        parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))

def _canon(d):return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def append_exact_source09_feedback_rows(no,request,authorization,records):
    if no!='09':
        return {'applied':False,'reason':'The exact three-row transport is only source09.'}
    request=Path(request)
    if request.name!='09':raise ValueError('Actual source09 request directory required')
    if (request/'视频/工具/用户同意记录.json').exists():
        raise ValueError('Source09 uses append-only actual rows; no supplied whole registry')
    source=_load(request/'视频/脚本/09.json',SOURCE_SHA256)
    if source.get('no')!='09':raise ValueError('Source09 source identity mismatch')
    final=_load(request/'user-authorization.json',FINAL_ROW_SHA256)
    if _canon(final)!=_canon(authorization):raise ValueError('Stale final row passed to original caller')
    rows=_load(request/'supplemental-user-authorizations.json',ROWS_SHA256)
    if type(rows)is not list or len(rows)!=3:raise ValueError('Only the exact three actual-message rows are allowed')
    docs={name:_load(request/'exact-user-consent-proofs'/name,digest)for name,digest in PROOFS.items()}
    for doc in docs.values():
        if str(doc.get('source_id'))!='09' or str(doc.get('book_order'))!='52':
            raise ValueError('Wrong actual user proof source/book')
    five=docs['five-feedback.json'];sixth=docs['sixth-feedback.json'];authority=docs['actual-final-authority.json']
    by_id={x['id']:x['raw']for x in five['requests']}
    expected_quotes=[by_id['book52-drought-focus'],by_id['book52-dented-barely-focus-and-gloss'],sixth['raw_user_text_verbatim']]
    if [row.get('原话')for row in rows]!=expected_quotes:
        raise ValueError('Three quotes must remain separate and individually verbatim')
    if authorization.get('原话')!=authority['raw_user_text_verbatim']:
        raise ValueError('Independent final quote differs from actual finalization authority')
    for row in rows:
        if (set(row)!=set(('篇','日期','原话','用于','来源')) or row['篇']!='09'
                or row['日期']!='2026-11-15' or not row['原话'] or '撤回' in row['用于']):
            raise ValueError('Wrong supplemental row schema or scope')
    if type(records)is not dict or type(records.get('记录'))is not list:
        raise ValueError('Original consent registry schema mismatch')
    # Validate every input before mutating the caller's in-memory records.
    prefix=_canon(records['记录'])
    count=len(records['记录']);header=_canon({k:v for k,v in records.items()if k!='记录'})
    added=[]
    for row in rows:
        if row not in records['记录']:
            records['记录'].append(row);added.append(row)
    if _canon(records['记录'][:count])!=prefix or _canon({k:v for k,v in records.items()if k!='记录'})!=header:
        raise ValueError('Original registry prefix/header was modified')
    return {'applied':True,'source_id':'09','book_order':52,
        'exact_supplement_list_sha256':ROWS_SHA256,'actual_proof_sha256':PROOFS,
        'original_registry_prefix_and_headers_unchanged':True,
        'actual_separate_user_message_rows_added':added,
        'independent_final_row_still_appended_by_original_protocol':True,
        'new_T12_or_audio_exception_or_quality_pass_granted':False}
