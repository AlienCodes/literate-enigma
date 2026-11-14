"""Optional exact reconstruction from the retained files; no network needed."""
from pathlib import Path
import argparse,hashlib,json,shutil
HERE=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--root',help='Restore only paths below this original mirror root');args=p.parse_args()
receipt=json.loads((HERE/'cleanup-receipt.json').read_text());selected=[]
for row in receipt['deleted']:
 target=Path(row['path']);retained=Path(row['retained_path'])
 if args.root and not target.is_relative_to(Path(args.root).resolve()):continue
 assert retained.is_file()and sha(retained)==row['sha256']
 if target.exists():assert sha(target)==row['sha256'];continue
 selected.append(row)
 if args.execute:
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(retained,target);assert sha(target)==row['sha256']
print(json.dumps({'restore_executed':args.execute,'selected_leaves':len(selected),'logical_bytes':sum(x['bytes']for x in selected)},ensure_ascii=False))
