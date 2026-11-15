"""Exact208205 collector I/O only; retain every original and create regular targets."""
from pathlib import Path
import hashlib,json,os,shutil,stat
H='2082052baf9f71be9a0dcc5090234129a08e297714dc1738be8e2c1ffb099ece'
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def candidates(manifest,sid,nid,handoff_sha):
 assert (sid,nid,handoff_sha)==('48','42',H)
 m=json.loads(Path(manifest).read_text());assert m['same_content_IO_scope_handoff_sha256']==H
 target_dev=Path(manifest).stat().st_dev; result={}
 for x in m['same_content_HOST_IO_candidates']:
  p=Path(x['path']).resolve();st=p.stat();assert stat.S_ISREG(st.st_mode)and st.st_dev==target_dev
  assert st.st_size==x['bytes']and digest(p)==x['sha256']
  result[(x['bytes'],x['sha256'])]=p
 return result
def materialize(source,target,size,sha,stored,host):
 """No overwrite, deletion, source write, pathname substitution in archived provenance."""
 source=Path(source).resolve();target=Path(target)
 assert source.stat().st_size==size and digest(source)==sha
 key=(size,sha);origin=stored.get(key)
 if origin is None and source.stat().st_dev==target.parent.stat().st_dev:origin=source
 if origin is None:origin=host.get(key)
 if origin is not None:
  origin=Path(origin).resolve();st=origin.stat()
  assert stat.S_ISREG(st.st_mode)and st.st_dev==target.parent.stat().st_dev
  assert st.st_size==size and digest(origin)==sha
  os.link(origin,target)
 else:
  # The only required large copies are unique frozen RAM files crossing filesystems.
  assert os.statvfs(target.parent).f_bavail*os.statvfs(target.parent).f_frsize>size+10*1024*1024
  shutil.copyfile(source,target)
 assert target.is_file()and not target.is_symlink()and target.stat().st_size==size and digest(target)==sha
 stored[key]=target
