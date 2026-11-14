"""Remove only closed, dual-pushed temporary archive object stores; payload remains."""
import argparse,datetime,json,pathlib,shutil,subprocess
B=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--receipt',required=True);p.add_argument('--output',required=True);a=p.parse_args()
plan=json.loads(pathlib.Path(a.plan).read_text());receipt=json.loads(pathlib.Path(a.receipt).read_text());assert receipt['status']=='permanent_double_repository_archive_verified' and receipt['archived_passed_count']==plan['result_count'] and len(receipt['archives'])==2
rows=[]
for raw in plan['article_work_dirs']+[plan['operation_work_dir']]:
 w=pathlib.Path(raw).resolve();assert w.parent==B;g=w/'assets.git'
 if not g.exists():continue
 first=json.loads((w/'assets-primary.json').read_text());second=json.loads((w/'assets-backup.json').read_text());assert first['asset_commit']==second['asset_commit'] and first['video_tree_sha']==second['video_tree_sha']
 for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
  ref=json.loads(subprocess.check_output(['gh','api','repos/'+repo+'/git/ref/heads/'+first['asset_branch']]))['object']['sha'];assert ref==first['asset_commit']
 assert (w/'payload-file-index.json').is_file() and (w/'prepared-archive.json').is_file() and (w/'payload').is_dir()
 size=sum(f.stat().st_size for f in g.rglob('*') if f.is_file());shutil.rmtree(g)
 rows.append({'path':str(g),'logical_bytes':size,'asset_commit_in_both_repositories':first['asset_commit'],'all_original_media_source_payload_QA_receipts_kept':True})
out={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization':'Root explicitly authorized only closed verified own remote-restorable temporary bare object cleanup','completed_archive_receipt':a.receipt,'archived_count':receipt['archived_passed_count'],'rows':rows,'total_logical_bytes':sum(x['logical_bytes'] for x in rows),'quality_or_media_or_payload_changes':False}
pathlib.Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out))
