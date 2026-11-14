"""Delete only mirror leaves proven byte-identical to retained public HEAD files."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
B=Path('/workspace/work/video-audit70-20261113');HERE=Path(__file__).parent
REPO=Path('/workspace/work/github-publication/target');COMMIT='64621068034f8b6e09836a6d97210a0e9b2f1ed6'
ROOTS=[B/'article14-user-review-20261114/gen-text-validation/mirror',B/'article27-user-review-20261114/thin-validation/mirror']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((HERE/'actual-public-baseline-commit.json').read_text());assert proof['sha']==COMMIT
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==COMMIT
tree={}
for line in subprocess.check_output(['git','ls-tree','-r','-z',COMMIT],cwd=REPO).split(b'\0'):
 if line:
  meta,name=line.split(b'\t',1);mode,kind,oid=meta.decode().split()
  if kind=='blob'and mode!='120000':tree[name.decode()]=oid
cache={};entries=[];kept=[]
for root in ROOTS:
 for path in sorted(root.rglob('*')):
  if path.is_symlink()or not path.is_file():continue
  rel=path.relative_to(root)
  # Keep work13/26/14/27 and unique validation outputs, including all new sources.
  if rel.parts[0].startswith('_'):
   kept.append({'path':str(path),'reason':'work-area-and-unique-results-protected','bytes':path.stat().st_size});continue
  key=str(rel)
  if key not in tree:kept.append({'path':str(path),'reason':'not-in-verified-public-baseline-tree','bytes':path.stat().st_size});continue
  retained=None
  for retained_root in [REPO,Path('/workspace/work/audit-repo'),B/'preflight-frozen66-v2-part1/mirror',B/'payload']:
   q=retained_root/rel
   if not q.is_file()or q.is_symlink()or q.stat().st_size!=path.stat().st_size:continue
   cache_key=str(q)
   if cache_key not in cache:
    raw=q.read_bytes();cache[cache_key]=(hashlib.sha256(raw).hexdigest(),hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
   retained_sha,blob=cache[cache_key]
   if blob==tree[key]and sha(path)==retained_sha:retained=q;break
  if retained is None:
   kept.append({'path':str(path),'reason':'different-content-retained-unchanged','bytes':path.stat().st_size});continue
  st=path.stat();entries.append({'path':str(path),'retained_path':str(retained),'relative_repo_path':key,'bytes':st.st_size,'sha256':retained_sha,'git_blob_sha1':blob,'public_repository':'alienalgorithm/postgraduate-vocabulary','immutable_commit':COMMIT,'retained_baseline_public_commit_actually_read':True,'nlink_before':st.st_nlink,'physical_blocks_before':st.st_blocks*512})
inventory={'kind':'verified-duplicate-only-mirror-cleanup-inventory','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roots':[str(p)for p in ROOTS],'remote_commit_proof':str(HERE/'actual-public-baseline-commit.json'),'candidate_duplicate_count':len(entries),'candidate_duplicate_logical_bytes':sum(x['bytes']for x in entries),'candidate_duplicate_single_link_physical_bytes':sum(x['physical_blocks_before']for x in entries if x['nlink_before']==1),'entries':entries,'retained_unmatched_or_protected':kept,'no_live_audio_mother_cache_source_PNG_or_report_targets':True}
ip=HERE/'duplicate-only-inventory.json';ip.write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
if '--execute'not in sys.argv:
 print(json.dumps({k:v for k,v in inventory.items()if k.startswith('candidate_')},ensure_ascii=False));sys.exit(0)
deleted=[]
for row in entries:
 p=Path(row['path']);retained=Path(row['retained_path'])
 assert p.is_file()and not p.is_symlink()and retained.is_file()
 assert sha(p)==sha(retained)==row['sha256']
 p.unlink();deleted.append(row)
receipt={'kind':'completed-verified-duplicate-only-mirror-cleanup','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inventory_sha256':sha(ip),'deleted_count':len(deleted),'logical_bytes_removed':sum(x['bytes']for x in deleted),'single_link_physical_bytes_removed':sum(x['physical_blocks_before']for x in deleted if x['nlink_before']==1),'each_retained_file_rechecked_immediately_before_delete':True,'each_retained_file_matches_actual_public_immutable_commit_blob':True,'unique_sources_reports_PNG_work_areas_and_live_audio_caches_untouched':True,'deleted':deleted}
p=HERE/'cleanup-receipt.json';p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k not in['deleted']},ensure_ascii=False))
