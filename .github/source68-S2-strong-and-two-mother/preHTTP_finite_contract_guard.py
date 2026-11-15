"""Finite local transport validation only, never model/HTTP entrypoint."""
from pathlib import Path
import hashlib,importlib.util,json
ROOT_SHA='727f4eb413cdb48d215200f2260d40ba46b00867119ff2ae2842cfaa95353547'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(root_file,root_sha,parent_file,parent_sha,F):
 F=Path(F);N=F/'.github/source68-S2-strong-and-two-mother'
 assert root_sha==ROOT_SHA and Path(root_file).is_file()and not Path(root_file).is_symlink()and sha(root_file)==root_sha
 assert len(parent_sha)==64 and Path(parent_file).is_file()and not Path(parent_file).is_symlink()and sha(parent_file)==parent_sha
 assert sha(N/'actual-ROOT727f-S2-two-mother-scope.json')==ROOT_SHA
 mf=json.loads((F/'program-freeze-manifest.json').read_text());seen=set()
 for row in mf['files']:
  rel=Path(row['path']);assert not rel.is_absolute()and '..'not in rel.parts and str(rel)not in seen;seen.add(str(rel))
  p=F/rel;assert p.is_file()and not p.is_symlink()and p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 actual={str(p.relative_to(F))for p in (F/'.github').rglob('*')if p.is_file()and'__pycache__'not in p.parts};assert actual==seen
 for row in json.loads((N/'transport-file-pins.json').read_text()):
  p=N/row['relative'];assert p.is_file()and not p.is_symlink()and p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 spec=importlib.util.spec_from_file_location('_only68_preHTTP_pure_helper',N/'prepare68_only_S2_two_mothers_spoken20_internal_delegate_fixed.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 profile=m.read(N/'source68-S2-two-mother-input-profile-spoken20.json');assert sha(N/'source68-S2-two-mother-input-profile-spoken20.json')==m.PROFILE_SHA
 m.validate_execution_adoption(m.read(N/'actual-root-two-mother-execution-adoption.json'),sha(N/'prepare68_only_S2_two_mothers_spoken20_internal_delegate_fixed.py'))
 for name,filename in {'request': '68-owner-source.json', 'shadow': '68-S2-private-shadow.json', 'history': '68-S2-old-mother-retirement-history.json', 'GEN': 'gen68.py', 'MD': '68-owner-manuscript.md', 'authority': '68-final-authority.json', 'raw_audio_authority': '68-S2-raw-audio-authority.json', 'code_adoption': 'root-actual-spoken20-code-adoption.json', 'overlay': 'actual-spoken20-runtime-contract.json', 'input_H': '68-owner-input-H.json', 'pending_text': '68-pending-text.md', 'sentence_confirmations': '68-sentence-confirmations.json', 'certification_report': 'actual20-certification43693920217.json'}.items():assert profile['file_sha256'][name]==sha(N/filename)
 m.verify_request(m.read(N/'68-owner-source.json'),m.read(N/'68-S2-private-shadow.json'),m.read(N/'68-S2-old-mother-retirement-history.json'))
 from types import SimpleNamespace
 m.validate_scope_and_contract(SimpleNamespace(root_execution_scope=N/'actual-ROOT727f-S2-two-mother-scope.json',contract=N/'exact-real-CPU-contract.json',contract_guards=N/'exact_S2_context_contract_guards.py',prior_context=N/'prior-ef53-context.json',new_context=N/'new-S2-only-strong-context.json',request=N/'68-owner-source.json',shadow=N/'68-S2-private-shadow.json'))
 args=json.loads((N/'native-arguments-internal-delegate-fixed.json').read_text());assert args['program']=='.github/source68-S2-strong-and-two-mother/prepare68_only_S2_two_mothers_spoken20_internal_delegate_fixed.py'
 for key,val in args['arguments'].items():
  if val.startswith('.github/'):
   p=F/val;assert p.is_file()and not p.is_symlink()
 assert args['arguments']['--root-execution-scope'].endswith('actual-ROOT727f-S2-two-mother-scope.json')
 return {'all_pinned_files_verified':len(seen),'no_models_or_network_called':True}
