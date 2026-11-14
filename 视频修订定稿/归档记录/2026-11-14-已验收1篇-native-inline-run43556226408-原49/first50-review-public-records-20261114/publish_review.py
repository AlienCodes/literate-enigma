"""User-requested interim review: one complete PDF and one ZIP with40 passed new4K videos.
This deliberately does not claim the first50 or all70 are finished. No old Release is removed.
"""
import base64, datetime, hashlib, json, mimetypes, queue, threading, urllib.error, urllib.parse, urllib.request, zipfile, sys
from pathlib import Path
from zoneinfo import ZoneInfo
HERE=Path(__file__).resolve().parent
DROOT=Path('/workspace/work/video-revision-delivery');sys.path.insert(0,str(DROOT))
import delivery as D
import release_actions as R
REPOS=('alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma')
BRANCH='codex/first50-review-v1';TAG='kaoyanxueren-first50-review-v1'
MASTER='6355a02864ebae616b693200d9d26f74f5da80e9'

def save(name,value):
 p=HERE/name;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def load(name):return json.loads((HERE/name).read_text())
def sha(path):return R.sha(path)
def regular(spec):
 p=Path(spec['path']);assert p.is_file() and not p.is_symlink() and p.stat().st_size==spec['bytes'] and sha(p)==spec['sha256'];return p

def prepare():
 if (HERE/'MANIFEST.json').exists():return load('MANIFEST.json')
 hs=[DROOT/'actual53-64-validation/archive-handoff.json']
 for f in ('next-passed-validated','recovered-canonical-validated','inline-passed-validated'):hs+=sorted((DROOT/f).glob('*/*/archive-handoff.json'))
 articles={}
 for h in hs:
  if not h.exists():continue
  for a in json.loads(h.read_text())['articles']:
   if int(a['new_id'])>50:continue
   assert a['passed_per_article'] is True
   p=regular(a['final_mp4']);v=json.loads(Path(a['validated_record']).read_text());v=v.get('record',v);assert v['sha256']==a['final_mp4']['sha256'] and v['actual_probe']['width']==3840 and v['actual_probe']['height']==2160 and v['qc']['status']=='passed'
   item={'book_order':a['new_id'],'source_id':a['source_id'],'name':Path(a['book_order_archive_path']).name,'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'handoff_path':str(h),'handoff_sha256':sha(h),'actual_full_V3_passed':True}
   if a['new_id']in articles:assert articles[a['new_id']]['sha256']==item['sha256']
   articles[a['new_id']]=item
 order=json.loads((DROOT/'next-passed-validated/43556145154/02/frozen-primary/篇号对照.json').read_text())['rows']
 missing=[{'book_order':r['new_id'],'source_id':r['source_id'],'title':r['title_zh']}for r in order if int(r['new_id'])<=50 and r['new_id']not in articles]
 pdfref=json.loads((DROOT/'published-pdf-v4-frozen-primary.json').read_text());pdf={'name':'考研学人.pdf','path':'/workspace/work/punk-print-20261113-v4-compact/signed/book/PUNK-ENGLISH-70-STORIES.pdf','bytes':pdfref['bytes'],'sha256':pdfref['sha256'],'pages':475};regular(pdf);assert pdfref['pages']==475 and pdfref['sha256']=='65bc695c7b789fbc397c443ea6a387ee616f2569865a4350edc0137ddcff089e'
 assert len(articles)==40 and len(missing)==10,'Freeze this expressly requested40-video review; additional outputs belong to a subsequent recorded update'
 now=datetime.datetime.now(datetime.timezone.utc);local=now.astimezone(ZoneInfo('America/New_York'))
 m={'kind':'explicitly_requested_interim_review_release','requested_book_range':['01','50'],'requested_range_complete':False,'video_count':40,'required_within_range':50,'pending':missing,'PDF':pdf,'videos':[articles[k]for k in sorted(articles)],'recorded_utc':now.isoformat(),'zip_datetime':list(local.timetuple()[:6]),'new_release_tag':TAG,'only_uploaded_attachments':['考研学人.pdf','考研学人-前50篇已完成40篇-审核包.zip'],'full70_complete_or_released_claimed':False,'old_releases_or_tags_to_delete':[],'publisher_program_sha256':sha(__file__)}
 save('MANIFEST.json',m);return m

class HashSink:
 def __init__(self):self.count=0;self.hash=hashlib.sha256()
 def write(self,b):self.count+=len(b);self.hash.update(b);return len(b)
 def tell(self):return self.count
 def seek(self,*a):raise OSError('Streaming ZIP has no seek')
 def flush(self):pass

def write_zip(m,sink):
 members=[(m['PDF'],'考研学人.pdf')]+[(x,'4K视频/'+x['name'])for x in m['videos']]
 with zipfile.ZipFile(sink,'w',compression=zipfile.ZIP_STORED,allowZip64=True)as archive:
  for spec,name in members:
   info=zipfile.ZipInfo(name,date_time=tuple(m['zip_datetime']));info.compress_type=zipfile.ZIP_STORED;info.create_system=3;info.external_attr=0o100644<<16;info.file_size=spec['bytes'];h=hashlib.sha256();count=0
   with Path(spec['path']).open('rb')as source,archive.open(info,'w',force_zip64=False)as out:
    for b in iter(lambda:source.read(1024*1024),b''):h.update(b);count+=len(b);out.write(b)
   assert count==spec['bytes'] and h.hexdigest()==spec['sha256'],'Immutable review member changed: '+name

class ZipBody:
 def __init__(self,m,expected):
  self.q=queue.Queue(maxsize=4);self.stop=threading.Event();self.buffer=b'';self.done=False
  outer=self
  class Sink(HashSink):
   def write(self,b):
    super().write(b)
    if b:
     while not outer.stop.is_set():
      try:outer.q.put(bytes(b),timeout=.2);return len(b)
      except queue.Full:pass
     raise RuntimeError('ZIP transport cancelled')
    return 0
  def run():
   try:
    sink=Sink();write_zip(m,sink);assert sink.count==expected['bytes'] and sink.hash.hexdigest()==expected['sha256'];value=None
   except BaseException as e:value=e
   while not self.stop.is_set():
    try:self.q.put(value,timeout=.2);break
    except queue.Full:pass
  self.thread=threading.Thread(target=run,daemon=True);self.thread.start()
 def read(self,n=8192):
  if self.done:return b''
  while not self.buffer:
   v=self.q.get()
   if v is None:self.done=True;return b''
   if isinstance(v,BaseException):raise v
   self.buffer=v
  out=self.buffer[:n];self.buffer=self.buffer[n:];return out
 def close(self):self.stop.set();self.thread.join(timeout=2)

def archive_records(phase,files):
 api=D.GitHub();assert api.api(REPOS[1],'git/ref/heads/master')['object']['sha']==MASTER
 state=load('STATE.json')if(HERE/'STATE.json').exists()else{}
 expected={p:hashlib.sha256(raw).hexdigest()for p,raw in files.items()};saved=state.setdefault('record_archives',{}).setdefault(phase,{})
 for repo in REPOS:
  if repo in saved:continue
  try:parent=api.api(repo,'git/ref/heads/'+BRANCH)['object']['sha']
  except urllib.error.HTTPError as e:
   if e.code!=404:raise
   parent=None
  entries=[]
  for path,raw in files.items():
   g=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert api.api(repo,'git/blobs','POST',{'encoding':'base64','content':base64.b64encode(raw).decode()})['sha']==g;entries.append({'path':path,'mode':'100644','type':'blob','sha':g})
  body={'tree':entries}
  if parent:body['base_tree']=api.api(repo,'git/commits/'+parent)['tree']['sha']
  tree=api.api(repo,'git/trees','POST',body)['sha'];identity={'name':'Codex','email':'codex@users.noreply.github.com','date':load('MANIFEST.json')['recorded_utc']}
  commit=api.api(repo,'git/commits','POST',{'message':'保存用户先行审核40部新4K和完整PDF的精确清单与记录 [skip ci]','tree':tree,'parents':[parent]if parent else[],'author':identity,'committer':identity})['sha']
  if parent:api.api(repo,'git/refs/heads/'+BRANCH,'PATCH',{'sha':commit,'force':False})
  else:api.api(repo,'git/refs','POST',{'ref':'refs/heads/'+BRANCH,'sha':commit})
  assert api.api(repo,'git/ref/heads/'+BRANCH)['object']['sha']==commit
  for path,raw in files.items():assert base64.b64decode(api.api(repo,'contents/'+path+'?ref='+commit)['content'])==raw
  saved[repo]={'commit':commit,'branch':BRANCH,'files':expected,'actual_bytes_read_back':True};save('STATE.json',state)
 assert api.api(REPOS[1],'git/ref/heads/master')['object']['sha']==MASTER
 return saved

def upload(release,expected,body):
 url=release['upload_url'].split('{',1)[0]+'?name='+urllib.parse.quote(expected['name'],safe='')
 request=urllib.request.Request(url,data=body,method='POST',headers={'Authorization':'Bearer '+R.auth_token(),'Content-Type':mimetypes.guess_type(expected['name'])[0]or'application/octet-stream','Content-Length':str(expected['bytes']),'Accept':'application/vnd.github+json'})
 with urllib.request.urlopen(request,timeout=900)as response:return json.load(response)

def main():
 m=prepare()
 for s in [m['PDF']]+m['videos']:regular(s)
 if not(HERE/'ZIP-IDENTITY.json').exists():
  sink=HashSink();write_zip(m,sink);assert sink.count<2_000_000_000;save('ZIP-IDENTITY.json',{'name':m['only_uploaded_attachments'][1],'bytes':sink.count,'sha256':sink.hash.hexdigest(),'members':41,'compression':'ZIP_STORED; all member original bytes retained','complete_ZIP_generated_and_hashed_without_temporary_disk_copy':True})
 z=load('ZIP-IDENTITY.json');a=archive_records('initial',{'MANIFEST.json':(HERE/'MANIFEST.json').read_bytes(),'publisher.py':Path(__file__).read_bytes(),'ZIP-IDENTITY.json':(HERE/'ZIP-IDENTITY.json').read_bytes()});target=a[REPOS[0]]['commit']
 state=load('STATE.json');release=R.api('releases/tags/'+TAG,missing_ok=True);marker='Review manifest SHA-256: '+sha(HERE/'MANIFEST.json')
 body='整本《考研学人》PDF：475页。\n\n审核包包含书中第01—50篇范围内已核验的40部新4K视频及同一份PDF，视频保留书中编号。\n\n待补10篇：'+ '、'.join(x['book_order']+' '+x['title']for x in m['pending'])+'。这些篇目继续修复。\n\n附件只有整本PDF与审核ZIP，ZIP可一次下载全部内容。\n\n制作与核验记录：https://github.com/'+REPOS[0]+'/tree/'+target+'\n\n<!-- '+marker+' -->'
 if release is None:release=R.api('releases','POST',{'tag_name':TAG,'target_commitish':target,'name':'考研学人｜审核版：完整PDF与40篇新4K视频','body':body,'draft':True,'prerelease':True})
 else:assert marker in(release.get('body')or'') and R.tag_commit(TAG)==target
 state['release_id']=release['id'];state['release_url']=release['html_url'];state['preview_target_commit']=target;save('STATE.json',state)
 expected=[{k:m['PDF'][k]for k in('name','bytes','sha256')},z];rows=R.remote_assets(release['id']);assert{r['name']for r in rows}<={x['name']for x in expected};by={r['name']:r for r in rows}
 for i,spec in enumerate(expected,1):
  if spec['name']in by:remote=by[spec['name']]
  else:
   stream=Path(m['PDF']['path']).open('rb')if i==1 else ZipBody(m,z)
   try:remote=upload(release,spec,stream)
   finally:stream.close()
  proof=R.verify_asset(remote,spec);print(json.dumps({'verified_attachment':i,'of':2,'name':spec['name'],'bytes':spec['bytes'],'sha256':spec['sha256']},ensure_ascii=False),flush=True)
 rows=R.remote_assets(release['id']);assert[r['name']for r in rows]==[x['name']for x in expected]and len(rows)==2;proofs=[R.verify_asset(r,e)for r,e in zip(rows,expected)]
 if release['draft']:R.api('releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':True,'make_latest':'false'})
 final=R.api('releases/'+str(release['id']));assert not final['draft']and R.tag_commit(TAG)==target
 receipt={'scope':'User-requested interim40-video review, not first50/all70 completion','passed':True,'release_url':final['html_url'],'release_id':final['id'],'tag':TAG,'source_record_commit':target,'video_count':40,'pending_first50_count':10,'PDF_pages':475,'only_two_attachments':True,'assets':proofs,'zip_members':41,'old_release_or_tag_deleted':False,'publisher_execution':R.publisher_execution('local-gh'),'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};save('RELEASE-VERIFICATION.json',receipt)
 archives=archive_records('verification',{'RELEASE-VERIFICATION.json':(HERE/'RELEASE-VERIFICATION.json').read_bytes()});state=load('STATE.json');state.update(published=True,actual_remote_assets_verified=True,verification_archived_in_both=True);save('STATE.json',state);print(json.dumps({'PUBLIC_REVIEW_RELEASE':final['html_url'],'PDF':proofs[0]['url'],'ZIP':proofs[1]['url'],'verification_archives':archives},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
