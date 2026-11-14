"""Two existing verified post-only stages in sequence, without native production."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

ap=argparse.ArgumentParser();ap.add_argument('article');a=ap.parse_args();sid=a.article.zfill(2);H=Path(__file__).parent
stages=[('upstream',[sys.executable,str(H/'produce_actual_normal18_upstream.py'),sid,'--output-root','/dev/shm/normal-final-hold18-upstream']),('composition',[sys.executable,str(H/'compose_actual_normal_article.py'),'--article',sid])]
for name,cmd in stages:
    log=H/f'actual-normal{sid}-{name}-orchestration.log'
    with log.open('w')as stream: rc=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT).returncode
    if rc:
        print(json.dumps(dict(article=sid,stage=name,passed=False,log=str(log),exit_code=rc)))
        print(log.read_text()[-4500:])
        raise SystemExit(rc)
report=H/f'{sid}-actual-normal18-art60-summary60-report.json';r=json.loads(report.read_text())
assert r['passed'] and r['production_delivery_eligible'] and r['preview_only'] is False
print(json.dumps({k:r.get(k)for k in ['article','passed','preview_only','production_delivery_eligible','body_frames','illustration_start_frame','summary_start_frame','output_frames','aac_packet_count','video_sha256']},ensure_ascii=False))
