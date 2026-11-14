"""Deliver three already validated, dual-archived original MP4s; never re-encode."""
import datetime,hashlib,json,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;REPO='alienalgorithm/postgraduate-vocabulary'
def api(route,method='GET',data=None,missing=False):
 a=['gh','api','repos/'+REPO+'/'+route]
 if method!='GET':a+=['-X',method]
 if data is not None:a+=['--input','-']
 p=subprocess.run(a,input=None if data is None else json.dumps(data).encode(),capture_output=True)
 if missing and p.returncode and b'(HTTP 404)'in p.stderr:return None
 if p.returncode:raise RuntimeError(p.stderr.decode())
 return json.loads(p.stdout)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 m=json.loads((H/'MANIFEST.json').read_text());assert [a['new_id']for a in m['articles']]==['24','25','26'];assert [a['source_id']for a in m['articles']]==['61','15','17'];assert m['complete_validation_and_dual_archive_previously_passed']
 for a in m['articles']:
  p=Path(a['local_release_file']);assert p.stat().st_size==a['bytes']and sha(p)==a['sha256']
 tag=m['tag'];marker='Book24-26 delivery manifest SHA-256: '+sha(H/'MANIFEST.json');r=api('releases/tags/'+tag,missing=True)
 if r is None:r=api('releases','POST',{'tag_name':tag,'target_commitish':m['target_commit'],'name':'考研学人｜第24—26篇 4K定稿视频','body':(H/'RELEASE-NOTES.md').read_text()+'\n<!-- '+marker+' -->','draft':True,'prerelease':False})
 assert marker in(r.get('body')or'');expected={a['release_ASCII_transport_alias']:a for a in m['articles']}
 for name,a in expected.items():
  assets=api('releases/'+str(r['id'])+'/assets?per_page=100');assert set(x['name']for x in assets)<=set(expected)
  if not any(x['name']==name for x in assets):subprocess.run(['gh','release','upload',tag,a['local_release_file'],'--repo',REPO],check=True)
  x=next(x for x in api('releases/'+str(r['id'])+'/assets?per_page=100')if x['name']==name);assert x['state']=='uploaded'and x['size']==a['bytes']and x['digest']=='sha256:'+a['sha256'];print('Uploaded and server-digest verified: '+name,flush=True)
 assets=api('releases/'+str(r['id'])+'/assets?per_page=100');assert len(assets)==3 and set(x['name']for x in assets)==set(expected)
 if r['draft']:api('releases/'+str(r['id']),'PATCH',{'draft':False,'prerelease':False,'make_latest':'false'})
 r=api('releases/'+str(r['id']));assert not r['draft'];t=api('git/ref/tags/'+tag)['object'];assert t['type']=='commit'and t['sha']==m['target_commit']
 proof=[]
 for x in api('releases/'+str(r['id'])+'/assets?per_page=100'):
  a=expected[x['name']];d=hashlib.sha256();n=0
  with urllib.request.urlopen(x['browser_download_url'],timeout=120)as f:
   for b in iter(lambda:f.read(1024*1024),b''):d.update(b);n+=len(b)
  assert n==a['bytes']and d.hexdigest()==a['sha256'];proof.append({'book_order':a['new_id'],'source_id':a['source_id'],'name':x['name'],'bytes':n,'sha256':d.hexdigest(),'url':x['browser_download_url'],'actual_public_entire_attachment_readback_passed':True})
 receipt={'passed':True,'release_id':r['id'],'release_url':r['html_url'],'assets':sorted(proof,key=lambda a:a['book_order']),'only_three_MP4s':True,'other_releases_or_tags_deleted':False,'manifest_sha256':sha(H/'MANIFEST.json'),'publisher_sha256':sha(__file__),'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(H/'RELEASE-VERIFICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
