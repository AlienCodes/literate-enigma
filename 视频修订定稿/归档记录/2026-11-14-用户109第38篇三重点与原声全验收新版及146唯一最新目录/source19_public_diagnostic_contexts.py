"""Only five exact processed-public-MP4 contexts from the sealed105 audit."""
from pathlib import Path
import hashlib,json
REPORT=Path('/dev/shm/source19-user105-audio-audit-20261114/19-user105-completed-audio-audit-safe-handoff.json')
REPORT_SHA='def78619ecf3afb53f9f8916977ac0583934c798c9914423516ba645acd095bd'
EXPECTED={
 '19-S13-original-public-full-sentence-context.wav':(522078,'9b6eff74e10c36600a5f8052de5fb241354f953a78d12c469899664eae071113'),
 '19-S17-original-public-full-sentence-context.wav':(587598,'ee2e22605d3b8ed39b30f163d3f1c6246194ef843fbce9ddc523d5e62f734087'),
 '19-S3-original-public-full-sentence-context.wav':(367038,'0e5c04e4a0812413ef9f422cc329454f4ac9083caf8db4456400e9f16068a5d8'),
 '19-S9-original-public-full-sentence-context.wav':(384558,'e02db6c93e0be1c089809cd30be99ec23f144fd372248e8c959dba28558b3df6'),
 '19-petals-soared-AF-calibrated-public-context.wav':(96078,'967b8ecf674cda2fa9395e5c346e987b9aa43320252bb8331fab016a796ca850'),
}
def allowed(source_id,book_order):
 if(source_id,book_order)!=('19','38'):return {}
 raw=REPORT.read_bytes();assert len(raw)==5093 and hashlib.sha256(raw).hexdigest()==REPORT_SHA;q=json.loads(raw)
 assert q['source_id']=='19'and q['book_order']=='38'and q['diagnostic_audit_completed']is True
 assert q['actual_latest_public_MP4_sha256']=='fb8828bc717aedb38605b187a85d1ef6676bf8e51504f92a5154fe839c28d6e7'
 assert q['root_decision']['sha256']=='3f71278a3b5915abdc6e6a2233c63a8c8ebdd9a970c2f80852676fe4324c105d'
 assert q['human_perfect_audio_listening_or_formal_new_production_pass_not_claimed']is True
 out={}
 for row in q['safe_files']:
  p=Path(row['path'])
  if p.suffix!='.wav':continue
  assert row['role']=='actual_public_MP4_derived_diagnostic'and p.name in EXPECTED
  assert(row['bytes'],row['sha256'])==EXPECTED[p.name];data=p.read_bytes();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];out[str(p.resolve())]=row
 assert len(out)==5;return out
def check(path,contexts):
 p=Path(path);row=contexts.get(str(p.resolve()))
 if row is None:
  matches=[r for r in contexts.values()if p.name.endswith(Path(r['path']).name)]
  assert len(matches)==1,'Only exact named public context originals or their QA copies are permitted'
  row=matches[0]
 data=p.read_bytes();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];return row
