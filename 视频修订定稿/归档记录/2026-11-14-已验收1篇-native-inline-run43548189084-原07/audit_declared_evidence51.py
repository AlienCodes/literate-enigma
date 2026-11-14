"""Read-only locate each accepted article's explicit evidence in stored Git blobs."""
import hashlib,json,pathlib,subprocess
B=pathlib.Path(__file__).resolve().parent;D=pathlib.Path('/workspace/work/video-revision-delivery');PRIMARY='alienalgorithm/postgraduate-vocabulary';HEAD='46c1c9d7887098e8ee7b2998c4f80c3445111758'
def api(path):return json.loads(subprocess.check_output(['gh','api','repos/'+PRIMARY+'/'+path]))
def tree(sha,recursive=False):
 x=api('git/trees/'+sha+('?recursive=1' if recursive else ''));assert not x.get('truncated');return {v['path']:v for v in x['tree']}
root=tree(api('git/commits/'+HEAD)['tree']['sha']);video=tree(root['视频']['sha']);records=tree(video['制作记录']['sha']);scopes=[('视频修订定稿',root['视频修订定稿']['sha']),('视频/制作记录/旧简述清理-2026-11-13',records['旧简述清理-2026-11-13']['sha'])]
blobs={}
for prefix,sha in scopes:
 for path,row in tree(sha,True).items():
  if row['type']=='blob':blobs.setdefault(row['sha'],[]).append(prefix+'/'+path)
idx=json.loads(pathlib.Path(json.loads((B/'CURRENT-ARCHIVE-STATE.json').read_text())['actual_inventory']).read_text());accepted={v['source_id'] for v in idx['articles']}
handoffs=[D/'actual53-64-validation/archive-handoff.json']
for folder in ['next-passed-validated','recovered-canonical-validated','inline-passed-validated']:handoffs+=list((D/folder).glob('*/*/archive-handoff.json'))
rows=[];seen=set()
for hp in handoffs:
 if not hp.exists():continue
 h=json.loads(hp.read_text());config=json.loads(pathlib.Path(h['input_path']).read_text());articles={a['id']:a for a in config['articles']}
 for a in h['articles']:
  sid=a['source_id']
  if sid not in accepted or sid in seen:continue
  seen.add(sid)
  for spec in articles[sid].get('evidence',[]):
   p=pathlib.Path(spec['path']);r={'source_id':sid,**spec,'input_path':h['input_path'],'actual_handoff':str(hp),'local_file_exists':p.exists()}
   if p.exists():
    raw=p.read_bytes();assert len(raw)==spec['bytes'] and hashlib.sha256(raw).hexdigest()==spec['sha256'],str(p);g=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();r.update(git_blob_sha=g,stored_record_locations=blobs.get(g,[])[:5],already_in_pinned_record_subtree=bool(blobs.get(g)))
   else:r.update(already_in_pinned_record_subtree=False,reason='Local declared file path unavailable; original archive identity needs lookup')
   rows.append(r)
assert seen==accepted,(seen^accepted)
missing=[r for r in rows if not r['already_in_pinned_record_subtree']]
out={'scope':'Only explicitly declared evidence of51 accepted handoffs; read-only record Gitblob membership, no media revalidation or old report rewrite','pinned_primary_commit':HEAD,'searched_record_scopes':[x[0] for x in scopes],'accepted_articles':len(seen),'declared_evidence_entries':len(rows),'unique_declared_evidence_sha256':len({r['sha256'] for r in rows}),'already_stored_entries':len(rows)-len(missing),'missing_record_membership_entries':len(missing),'rows':rows,'not_yet_stored':missing,'remote_mutations':False,'video_or_quality_changes':False}
p=B/'declared-evidence51-record-membership-audit.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','not_yet_stored']},ensure_ascii=False));print(json.dumps(missing,ensure_ascii=False,indent=2))
