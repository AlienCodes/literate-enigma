"""Only two sealed public-MP4 contexts from the129/130 audio diagnosis."""
from pathlib import Path
import hashlib,json
REPORT=Path('/dev/shm/source37-user129130-audio-audit-20261114/37-user129130133-readonly-audio-safe-handoff.json')
REPORT_SHA='7600ac4807ebc4edb26ce9918b84198dd3b663339348f89ae103ed084e249152'
EXPECTED={'37-S10-actual-accepted-public-full-context.wav':(317118,'514c31a5da6877fd0fae60fa3efb148a5cfd34784cbd86c6d84c7b1a91bf841a'),'37-S13-actual-accepted-public-full-context.wav':(383118,'0c0405a2dc70c449af28fc10df7a2b6866a2393c27f611c1b51b8270671d0f09')}
def allowed(source_id,book_order):
 if(source_id,book_order)!=('37','43'):return {}
 raw=REPORT.read_bytes();assert len(raw)==5560 and hashlib.sha256(raw).hexdigest()==REPORT_SHA;q=json.loads(raw)
 assert q['kind']=='source37-user129130133-readonly-audio-audit-safe-handoff'and q['source_id']=='37'and q['frozen_book_order']=='43'
 assert q['diagnostic_audio_audit_completed']is True and q['human_listening_and_formal_new_production_pass_not_claimed']is True
 out={}
 for row in q['safe_files']:
  p=Path(row['path'])
  if p.suffix!='.wav':continue
  assert row['role']=='actual_public_MP4_decoded_evidence'and p.name in EXPECTED
  assert(row['bytes'],row['sha256'])==EXPECTED[p.name];data=p.read_bytes();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];out[str(p.resolve())]=row
 assert len(out)==2;return out
def check(path,contexts):
 p=Path(path);row=contexts.get(str(p.resolve()))
 if row is None:
  rows=[x for x in contexts.values()if p.name.endswith(Path(x['path']).name)];assert len(rows)==1;row=rows[0]
 raw=p.read_bytes();assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256'];return row
