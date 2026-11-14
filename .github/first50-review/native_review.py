"""Actual GitHub Actions transport for the explicitly requested40-video review release."""
import concurrent.futures,datetime,hashlib,json,os,shutil,subprocess,sys,urllib.parse,urllib.request,zipfile
from pathlib import Path
REPO='alienalgorithm/postgraduate-vocabulary';HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ['GITHUB_WORKSPACE']);OUT=ROOT/'review-output';OUT.mkdir(exist_ok=True)

def api(route,method='GET',data=None):
 a=['gh','api','repos/'+REPO+'/'+route]
 if method!='GET':a+=['-X',method]
 if data is not None:a+=['--input','-']
 return json.loads(subprocess.check_output(a,input=None if data is None else json.dumps(data).encode()))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def raw(commit,path):return 'https://raw.githubusercontent.com/'+REPO+'/'+commit+'/'+urllib.parse.quote(path,safe='/')
def download(spec,path):
 h=hashlib.sha256();n=0
 with urllib.request.urlopen(raw(spec['commit'],spec['repo_path']),timeout=300)as response,path.open('wb')as out:
  for b in iter(lambda:response.read(1024*1024),b''):h.update(b);n+=len(b);out.write(b)
 assert n==spec['bytes']and h.hexdigest()==spec['sha256'],spec['repo_path'];return path

def main():
 if os.environ.get('GITHUB_REPOSITORY')!=REPO:
  print('Backup contains source records only; publication runs in the primary repository.');return
 n=json.loads((HERE/'NATIVE-INPUT.json').read_text());m=json.loads((HERE/'MANIFEST.json').read_text());z=n['ZIP'];assert hashlib.sha256((HERE/'MANIFEST.json').read_bytes()).hexdigest()==n['manifest_sha256'];assert m['video_count']==40 and len(m['videos'])==40 and len(m['pending'])==10
 pdf=OUT/n['uploaded_attachments'][0]['name'];h=hashlib.sha256();total=0
 with pdf.open('wb')as out:
  for part in n['published_pdf']['parts']:
   ph=hashlib.sha256();size=0
   with urllib.request.urlopen(raw(n['published_pdf']['pinned_commit'],part['repo_path']),timeout=300)as source:
    for b in iter(lambda:source.read(1024*1024),b''):ph.update(b);h.update(b);size+=len(b);total+=len(b);out.write(b)
   assert size==part['bytes']and ph.hexdigest()==part['sha256']
 assert total==m['PDF']['bytes']and h.hexdigest()==m['PDF']['sha256'];print('Complete475-page PDF original bytes verified',flush=True)
 sources={r['source_id']:r for r in n['video_sources']}
 def fetch(v):
  source=sources[v['source_id']];assert source['sha256']==v['sha256']and source['bytes']==v['bytes'];path=OUT/(v['source_id']+'.mp4');download(source,path);return v['source_id'],str(path)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:paths=dict(pool.map(fetch,m['videos']))
 assert len(paths)==40
 checks={'PDF':{'bytes':pdf.stat().st_size,'sha256':sha(pdf)},'videos':[{'book_order':v['book_order'],'source_id':v['source_id'],'bytes':Path(paths[v['source_id']]).stat().st_size,'sha256':sha(paths[v['source_id']])}for v in m['videos']]};(OUT/'NATIVE-DOWNLOAD-IDENTITY.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
 class NonSeek:
  def __init__(self,target):self.target=target;self.count=0
  def write(self,b):self.count+=len(b);return self.target.write(b)
  def tell(self):return self.count
  def seek(self,*a):raise OSError('Match original deterministic streaming ZIP')
  def flush(self):self.target.flush()
 bundle=OUT/n['uploaded_attachments'][1]['name']
 with bundle.open('wb')as sink,zipfile.ZipFile(NonSeek(sink),'w',compression=zipfile.ZIP_STORED,allowZip64=True)as archive:
  members=[(pdf,'考研学人.pdf',m['PDF'])]+[(Path(paths[v['source_id']]),'4K视频/'+v['name'],v)for v in m['videos']]
  for path,name,spec in members:
   info=zipfile.ZipInfo(name,date_time=tuple(m['zip_datetime']));info.compress_type=zipfile.ZIP_STORED;info.create_system=3;info.external_attr=0o100644<<16;info.file_size=spec['bytes']
   with path.open('rb')as source,archive.open(info,'w',force_zip64=False)as target:shutil.copyfileobj(source,target,1024*1024)
 assert bundle.stat().st_size==z['bytes']and sha(bundle)==z['sha256'],'Exact original review ZIP hash differs'
 with zipfile.ZipFile(bundle)as archive:
  assert len(archive.infolist())==41 and archive.testzip()is None
  for path,name,spec in members:
   with archive.open(name)as source:assert hashlib.file_digest(source,'sha256').hexdigest()==spec['sha256']
 print('40 true new4K videos + PDF: exact ZIP, all41 member SHA/CRC verified',flush=True)
 release=api('releases/'+str(n['release_id']));assert release['tag_name']==m['new_release_tag']and n['manifest_sha256']in(release.get('body')or'');expected=n['uploaded_attachments']
 for path,e in zip([pdf,bundle],expected):
  assets=api('releases/'+str(release['id'])+'/assets?per_page=100');assert{a['name']for a in assets}<={v['name']for v in expected};match=next((a for a in assets if a['name']==e['name']),None)
  if match is None:subprocess.run(['gh','release','upload',m['new_release_tag'],str(path),'--repo',REPO],check=True)
  assets=api('releases/'+str(release['id'])+'/assets?per_page=100');a=next(a for a in assets if a['name']==e['name']);assert a['state']=='uploaded'and a['size']==e['bytes']and a['digest']=='sha256:'+e['sha256'];print('Uploaded and server-digest verified: '+e['name'],flush=True)
 assets=api('releases/'+str(release['id'])+'/assets?per_page=100');assert{a['name']for a in assets}=={e['name']for e in expected}and len(assets)==2
 if release['draft']:api('releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':True,'make_latest':'false'})
 final=api('releases/'+str(release['id']));assert not final['draft'];assets=api('releases/'+str(release['id'])+'/assets?per_page=100');tag=api('git/ref/tags/'+m['new_release_tag'])['object'];assert tag['type']=='commit'and tag['sha']==n['preview_target_commit']
 receipt={'scope':'User explicitly requested interim40-video+wholePDF review; first50 incomplete/all70 not claimed','passed':True,'release_id':final['id'],'release_url':final['html_url'],'PDF_pages':475,'video_count':40,'ZIP_members':41,'manifest_sha256':n['manifest_sha256'],'ZIP_sha256':z['sha256'],'assets':[{'name':a['name'],'bytes':a['size'],'digest':a['digest'],'id':a['id'],'url':a['browser_download_url']}for a in assets],'publisher_execution':{'kind':'native_actions','workflow_run_id':int(os.environ['GITHUB_RUN_ID']),'workflow_head_sha':os.environ['GITHUB_SHA'],'repository':os.environ['GITHUB_REPOSITORY'],'program_sha256':sha(__file__)},'old_release_or_tag_deleted':False,'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(OUT/'NATIVE-RELEASE-VERIFICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'PUBLIC_REVIEW_RELEASE':final['html_url'],'assets':receipt['assets']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
