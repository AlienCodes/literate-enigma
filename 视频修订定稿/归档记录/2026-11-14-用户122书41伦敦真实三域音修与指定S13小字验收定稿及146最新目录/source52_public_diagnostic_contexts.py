"""Only four explicitly whitelisted old public MP4 diagnostic contexts for52/41."""
from pathlib import Path
import hashlib,json
MANIFEST=Path('/dev/shm/article52-user120124-final-20261114/safe-source52-user122124-certified17-text-static-audio-evidence-whitelist.json')
MANIFEST_SHA='71b38256c4979332083f615e7aaa8d4b6ef496780c185c488224a69973e64106'
ROOT=Path('/dev/shm/source52-user117119-audio-audit-20261114/public-evidence')
EXPECTED={'52-S1-actual-accepted-public-context.wav':(323598,'b4cbb6a301e56fb2d6b60d69e2ce05859d576e3ef51f4c598fef83f7a3d860d8'),'52-S4-actual-accepted-public-context.wav':(395838,'54cbd9d80c0ab3a5726f74f78196e6d09a4f9d1663e63cc0e64666f1c8488d3a'),'52-S5-actual-accepted-public-context.wav':(432798,'3fb73b18d4bfaf6787c41be669a7289be27ec2f372abeeaddfe3364d9203afc8'),'52-S18-actual-accepted-public-context.wav':(336078,'61bbdd9ebc3005a933a51f1796facf08c994dc35f61234c4a6f3a89fe991c312')}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def allowed(sid,nid):
 assert(sid,nid)==('52','41')and digest(MANIFEST)==MANIFEST_SHA
 assert REPORT.stat().st_size==5464 and digest(REPORT)==REPORT_SHA
 m=json.loads(MANIFEST.read_text());assert m['actual_old_public_MP4_decoded_diagnostics_only_from_explicit_child_safe_handoff']is True and m['private_mothers_WAV_PKL_GT_cache_tensor_and_full_private_candidate_reports_excluded']is True
 rows={Path(x['path']).name:x for x in m['files']if Path(x['path']).suffix.lower()=='.wav'};assert set(rows)==set(EXPECTED)
 for name,(n,sha)in EXPECTED.items():
  r=rows[name];assert Path(r['path'])==ROOT/name and r['bytes']==n and r['sha256']==sha and r['role']=='actual_public_MP4_decoded_diagnostic'
 return rows
def check_spec(path,n,sha):
 p=Path(path);assert p.parent==ROOT and p.name in EXPECTED and EXPECTED[p.name]==(n,sha)
def check(path,rows):
 p=Path(path);assert p.parent==ROOT and p.name in EXPECTED
 check_spec(p,p.stat().st_size,digest(p));assert p.stat().st_size==rows[p.name]['bytes']and digest(p)==rows[p.name]['sha256']

REPORT=Path('/dev/shm/source52-user117119-audio-audit-20261114/52-user117119122-readonly-audio-safe-handoff.json')
REPORT_SHA='3f03869b4fc7ec6246ae75a6c59d28901940aaef6e93f57d3201843417634664'
