"""Reassemble the original print PDF bytes from archived Git-safe parts."""
import argparse,hashlib,json,os
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--repo-root',type=Path);p.add_argument('--output',type=Path);args=p.parse_args();m=json.loads(args.manifest.read_text());output=args.output or args.manifest.parent/m['release_name'];root=args.repo_root
 if root is None:
  root=next((r for r in args.manifest.resolve().parents if (r/m['parts'][0]['repo_path']).is_file()),None)
 if root is None:raise SystemExit('Pass --repo-root pointing at the downloaded repository files.')
 if output.exists():
  h=hashlib.sha256()
  with output.open('rb') as f:
   for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
  if output.stat().st_size==m['bytes'] and h.hexdigest()==m['sha256']:print('Existing PDF already matches the original bytes and SHA-256.');return
  raise SystemExit('Output exists with different bytes; choose a new --output path.')
 output.parent.mkdir(parents=True,exist_ok=True);temp=output.with_name(output.name+'.joining');whole=hashlib.sha256();count=0
 try:
  with temp.open('wb') as out:
   for i,part in enumerate(m['parts'],1):
    assert part['index']==i;h=hashlib.sha256();size=0
    with (root/part['repo_path']).open('rb') as f:
     for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b);whole.update(b);size+=len(b);count+=len(b);out.write(b)
    assert size==part['bytes'] and h.hexdigest()==part['sha256'],('Bad part',part['index'])
  assert count==m['bytes'] and whole.hexdigest()==m['sha256'],'Whole PDF byte count/SHA mismatch'
  temp.replace(output)
 finally:
  if temp.exists():temp.unlink()
 print(json.dumps({'output':str(output),'bytes':count,'sha256':whole.hexdigest(),'original_bytes_preserved':True},ensure_ascii=False))
if __name__=='__main__':main()
