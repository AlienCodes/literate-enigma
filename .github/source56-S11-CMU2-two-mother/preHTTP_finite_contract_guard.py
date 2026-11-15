"""Finite local transport validation only, never model/HTTP entrypoint."""
from pathlib import Path
import hashlib,importlib.util,json
ROOT_SHA='a430159b2c827fcabcdf242f8407b33d546f1d5cfac336558b4537c90577efa4'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(root_file,root_sha,parent_file,parent_sha,F):
 F=Path(F);N=F/'.github/source56-S11-CMU2-two-mother'
 assert root_sha==ROOT_SHA and Path(root_file).is_file()and not Path(root_file).is_symlink()and sha(root_file)==root_sha
 assert len(parent_sha)==64 and Path(parent_file).is_file()and not Path(parent_file).is_symlink()and sha(parent_file)==parent_sha
 assert sha(N/'actual-ROOTa430-S11-two-mother-scope.json')==ROOT_SHA
 mf=json.loads((F/'program-freeze-manifest.json').read_text());seen=set()
 for row in mf['files']:
  rel=Path(row['path']);assert not rel.is_absolute()and '..'not in rel.parts and str(rel)not in seen;seen.add(str(rel))
  p=F/rel;assert p.is_file()and not p.is_symlink()and p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 actual={str(p.relative_to(F))for p in (F/'.github').rglob('*')if p.is_file()and'__pycache__'not in p.parts};assert actual==seen
 for row in json.loads((N/'transport-file-pins.json').read_text()):
  p=N/row['relative'];assert p.is_file()and not p.is_symlink()and p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 spec=importlib.util.spec_from_file_location('_only56_preHTTP_pure_helper',N/'prepare56_only_S11_CMU2_two_mothers_spoken22.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 profile=m.read(N/'source56-S11-two-mother-input-profile-spoken22.json');assert sha(N/'source56-S11-two-mother-input-profile-spoken22.json')==m.PROFILE_SHA
 m.validate_execution_adoption(m.read(N/'actual-root-two-mother-execution-adoption.json'),sha(N/'prepare56_only_S11_CMU2_two_mothers_spoken22.py'))
 for name,filename in {'request': '56-owner-source.json', 'shadow': '56-S11-private-shadow.json', 'history': '56-S11-five-old-mother-retirement-history.json', 'GEN': 'gen56.py', 'MD': '56-owner-manuscript.md', 'authority': '56-final-authority.json', 'raw_audio_authority': '56-S11-raw-audio-authority.json', 'code_adoption': 'root-actual-spoken22-code-adoption.json', 'overlay': 'actual-spoken22-runtime-contract.json', 'input_H': '56-owner-input-H.json', 'pending_text': '56-pending-text.md', 'sentence_confirmations': '56-sentence-confirmations.json', 'certification_report': 'actual22-certification43714183305.json'}.items():assert profile['file_sha256'][name]==sha(N/filename)
 m.verify_request(m.read(N/'56-owner-source.json'),m.read(N/'56-S11-private-shadow.json'),m.read(N/'56-S11-five-old-mother-retirement-history.json'))
 from types import SimpleNamespace
 m.validate_scope_and_contract(SimpleNamespace(root_execution_scope=N/'actual-ROOTa430-S11-two-mother-scope.json',contract=N/'exact-CMU2-CPU-contract.json',contract_guards=N/'exact_S11_CMU2_contract_guards.py',prior_context=N/'prior-4d890-context.json',new_context=N/'new-S11-only-CMU2-context.json',request=N/'56-owner-source.json',shadow=N/'56-S11-private-shadow.json',old_identity=N/'actual-old-S11-two-mother-identity.json',old_cache_API=N/'actual-old-S11-fourfile-cache-API.json'))
 args=json.loads((N/'native-arguments-internal-delegate-fixed.json').read_text());assert args['program']=='.github/source56-S11-CMU2-two-mother/prepare56_only_S11_CMU2_two_mothers_spoken22.py'
 for key,val in args['arguments'].items():
  if val.startswith('.github/'):
   p=F/val;assert p.is_file()and not p.is_symlink()
 assert args['arguments']['--root-execution-scope'].endswith('actual-ROOTa430-S11-two-mother-scope.json')
 return {'all_pinned_files_verified':len(seen),'no_models_or_network_called':True}
