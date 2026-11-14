"""Only two public MP4-derived 0.75-second diagnostic clips, never raw mothers."""
from pathlib import Path
import hashlib,json
PARENT=Path('/dev/shm/review18-native/43644184021/18/artifact-files')
QC=PARENT/'18-approved-audio-qc.json'
QC_SHA='aaa08951c3402b3d8b68cc008818400acf6976fb982ebd6cf50adf7855bfc18b'
SIDECAR=Path('/dev/shm/review18-hold18-intake/source18-two-explicit-public-MP4-derived-clips-provenance-sidecar.json')
SIDECAR_SHA='ab2ff6e73a22b8c8ecba23b4d3ca2a4cf03fb91277cc884099311b1e771966c8'
EXPECTED={'18-a21-controlled-word-actual.wav':'0e942aa63017ad4c4e8760d4e5f8ff1124f4a6ae59a509fbb4c9628bcfef1c9b','18-a21-controlled-word-accepted.wav':'f3fd0f712cfbcd836a76472c6424c53a1759d1831f013ea889f5f9126c855c79'}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_spec(parent,name,size,sha):
 assert Path(parent)==PARENT
 assert name in EXPECTED and size==72044 and sha==EXPECTED[name]
def check(path):
 p=Path(path);assert p.parent==PARENT and p.name in EXPECTED
 assert QC.stat().st_size==88695 and digest(QC)==QC_SHA
 q=json.loads(QC.read_text());assert q['validation_basis']=='Actual accepted/current public MP4 decoded samples and actual native timing/control metadata only.'
 assert q['private_GT_cache_or_raw_producer_PCM_read'] is False and q['subjective_listening_acceptance_claimed'] is False
 assert {r['file']:r['sha256']for r in q['public_actual_listening_clips']}==EXPECTED
 assert SIDECAR.stat().st_size==2393 and digest(SIDECAR)==SIDECAR_SHA
 check_spec(p.parent,p.name,p.stat().st_size,digest(p))
