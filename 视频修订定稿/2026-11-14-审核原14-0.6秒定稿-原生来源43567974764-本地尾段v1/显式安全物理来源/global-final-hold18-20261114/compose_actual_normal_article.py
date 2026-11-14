"""Run the frozen integrator on an already passed article's actual hold18 stage."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ap=argparse.ArgumentParser();ap.add_argument('--article',required=True);a=ap.parse_args();sid=a.article.zfill(2)
H=Path(__file__).parent;B=H.parent;U=Path('/dev/shm/normal-final-hold18-upstream')/sid;O=Path('/dev/shm/normal-final-hold18-composed')/sid;O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H/'illustrated_tail.py')=='05011f54fc9bbfb4ef8d7325f349bfb1e17d9038cb2b5b6b3d2e3290df65dbaa'
r=json.loads((U/f'{sid}-post-only-normal18-upstream-record.json').read_text());native=Path(r['source_video']).parent;request=native/f'{sid}-request-source.json';run=str(r['source_native_run'])
status=U/f'{sid}-upstream-summary-status.json';s=json.loads(status.read_text());assert sha(request)==s['request_source_sha256'][f'视频/脚本/{sid}.json']
layout=Path('/workspace/work/video-revision-delivery/next-passed-validated')/run/sid/sid/'approved-video-layouts70-frozen.json'
if not layout.exists(): layout=H/'approved-video-layouts70-at-first-normal36.json'
manifest=Path('/workspace/work/punk-print-20261113-v3/book-illustrations70.json');im=next(x['approved_book_illustration_path']for x in json.loads(manifest.read_text())['illustrations']if x['source_id']==sid)
cmd=[sys.executable,str(H/'illustrated_tail.py'),'--source-id',sid,'--final-last-body-hold-frames','18','--final-hold-policy','/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-051.json','--input',str(U/f'{sid}-4K-末句后停0.6秒-简述2秒-private-upstream.mp4'),'--verification',str(U/f'{sid}-summary-verification.json'),'--status',str(status),'--source-script',str(request),'--illustration-manifest',str(manifest),'--order-manifest',str(B/'publication-order-manifest-readonly.json'),'--crop-review',str(B/'illustrated-tail/illustration-crop-review70.json'),'--illustration',im,'--summary-image',str(U/f'{sid}-简述.png'),'--layout-approval',str(layout),'--output',str(O/f'{sid}-4K-正文读完停留0.6秒-插图2秒-简述2秒.mp4'),'--report',str(H/f'{sid}-actual-normal18-art60-summary60-report.json'),'--work',str(O),'--preview-dir',str(H/f'actual{sid}-boundary-previews'),'--prepared-illustration-output',str(O/f'{sid}-approved-illustration-prepared4K.png')]
(H/f'actual-normal{sid}-integration-command.json').write_text(json.dumps(dict(kind='actual_passed_native_postonly_normal18_composition',source_native_run=run,args=cmd,layout_manifest_sha256=sha(layout)),ensure_ascii=False,indent=2)+'\n')
with(H/f'actual-normal{sid}-physical-integration.log').open('w')as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
if rc: print((H/f'actual-normal{sid}-physical-integration.log').read_text()[-3500:]);raise SystemExit(rc)
q=json.loads((H/f'{sid}-actual-normal18-art60-summary60-report.json').read_text());print(json.dumps({k:q.get(k)for k in ['article','passed','preview_only','production_delivery_eligible','body_frames','illustration_start_frame','summary_start_frame','output_frames','aac_packet_count','video_sha256']},ensure_ascii=False))
