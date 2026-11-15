"""Stage only three exact existing tool JSON inputs before strict private prechecks.
No pronunciation/context/source values, runtime programs, models or quality gates
are changed. All three source/destination checks finish before any new write.
"""
from pathlib import Path
import hashlib,os
SOURCE_IDS=frozenset({'23','56','68'})
FILES=(
 ('环境/模型校验码.json','环境/模型校验码.json','dfde6c065a3558b74923ce82865a3b01dae1f839af4456b74de55dc3ff492312'),
 ('发音词典/读音改正.json','读音改正.json','5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'),
 ('发音词典/按语境读音.json','按语境读音.json','4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'),
)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def stage(tools,work,source_id):
 tools,work=Path(tools),Path(work)
 require(type(source_id)is str and source_id in SOURCE_IDS,'Only finite reviewed23/56/68 staging is declared')
 require(tools.is_dir()and not tools.is_symlink()and work.is_dir()and not work.is_symlink(),'Actual tools/work directories must already be real')
 inputs=[]
 for source_role,destination_role,expected in FILES:
  source,destination=tools/source_role,work/destination_role
  require(source.is_file()and not source.is_symlink()and source.resolve().is_relative_to(tools.resolve())and digest(source)==expected,'Original tool data SHA/path differs: '+source_role)
  require(destination.resolve().is_relative_to(work.resolve()),'Working data destination escapes actual work: '+destination_role)
  require(not destination.parent.is_symlink()and(not destination.parent.exists()or destination.parent.is_dir()),'Working data parent is not a real directory: '+destination_role)
  require(not destination.is_symlink()and(not destination.exists()or(destination.is_file()and digest(destination)==expected)),'Conflicting existing working data; do not overwrite: '+destination_role)
  temporary=destination.with_name(destination.name+'.original-data-stage-'+str(os.getpid())+'.tmp')
  if not destination.exists():require(not os.path.lexists(temporary),'Private staging temporary already exists')
  inputs.append((source,destination,source_role,destination_role,expected,destination.exists(),temporary))
 # Prevalidation above prevents a second-file conflict from leaving a first-file copy.
 result=[]
 for source,destination,source_role,destination_role,expected,existed,temporary in inputs:
  if not existed:
   destination.parent.mkdir(parents=True,exist_ok=True)
   require(not os.path.lexists(temporary),'Private staging temporary changed after prevalidation')
   raw=source.read_bytes();require(hashlib.sha256(raw).hexdigest()==expected,'Original tool data changed during staging')
   with temporary.open('xb')as f:f.write(raw)
   require(digest(temporary)==expected and not os.path.lexists(destination),'Staging copy or destination changed')
   os.replace(temporary,destination)
  require(destination.read_bytes()==source.read_bytes()and digest(destination)==expected,'Working staged data differs from original tool input')
  result.append({'tool_relative_path':source_role,'working_relative_path':destination_role,'full_SHA256':expected,'bytes':destination.stat().st_size,'already_present_same_bytes':existed,'copied_missing_same_bytes':not existed})
 return {'kind':'early_finite_original_tool_data_to_work_same_bytes_only','source_id':source_id,'files':result,'all_inputs_prevalidated_before_any_write':True,'conflicting_or_symlink_data_never_replaced':True,'original_context_remains_4d89_until_original_source68_CTX_installer':True,'runtime_program_model_cache_source_quality_threshold_or_approval_changed':False,'quality_acceptance':False}
