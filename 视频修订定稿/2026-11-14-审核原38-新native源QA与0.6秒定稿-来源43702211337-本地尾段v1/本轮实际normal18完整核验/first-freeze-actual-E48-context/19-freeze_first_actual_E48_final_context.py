"""Attach actual execution context once, before the new handoff is announced.
Never updates source/native/producer evidence or any previously frozen handoff.
"""
from pathlib import Path
import hashlib,json,shutil
T=Path(__file__).resolve().parent; O=T/'validated'
P=Path('/dev/shm/normal18-book48-51-52-HOST-output-tmp-path-only-20261115/book51-source38')
R=Path('/workspace/work/review38-native/43702211337/38')
def spec(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
hp=O/'archive-handoff.json';h=json.loads(hp.read_text())
assert h['source_run']==43702211337 and h['production_delivery_eligible'] is True and h['preview_only'] is False
assert h['articles'][0]['source_id']=='38' and h['articles'][0]['new_id']=='51' and h['articles'][0]['passed_per_article'] is True
assert not any('first-freeze-actual-E48-context/' in r['relative_validation_path'] for r in h['validation_files'])
actualready=P/'ready-book51-source38.json';ready=json.loads(actualready.read_text())
files=[P/'ACTUAL-HOST-NORMAL18-EXECUTION-ORIGINAL-PROGRAMS-AND-BUDGET-SIDECAR.json',Path('/workspace/work/review38-sourceQA/43702211337/archive-handoff.json'),Path('/dev/shm/root-three-normal18-explicit-data-only-code-adoption-20261115.json'),Path('/dev/shm/root-normal18-three-article-HOST-output-tmp-path-only-adoption-20261115.json'),P/'actual-38-upstream-execution.log',P/'actual-38-composer-execution.log',P/'ACTUAL-SUCCESS-SOURCEQA-AND-HOST-BUDGET-BEFORE-UPSTREAM.json',P/'ACTUAL-UPSTREAM-EXIT0-AND-HOST-COMPOSER-CAPACITY.json',actualready,Path('/dev/shm/root-source38-E47-actual-API-single-layout-sourceQA-entry-adoption-20261115.json'),Path('/dev/shm/root-source38-E48-original-normal18-data-only-final-consumer-adoption-20261115.json'),T/'E48-SOURCE38-NORMAL18-DATA-ONLY-FINAL-CONSUMER-ROOT-REVIEW-HANDOFF.json',T/'E48-original-code-inverse-and-unchanged-numeric-logic-proof.json',R/'measure_actual38_all_pages.py',R/'actual-working-source38-original-dual-resolution-geometry-report.json',T/'actual-final-review/actual-final-complete-decode-proof.json',T/'actual-final-review/actual-final-full-decode.stderr.log',T/'actual-final-review/actual-final-full-decode.stdout.log',Path('/dev/shm/USER-EXPLICIT-EIGHT-FINAL-SOURCE-DOCUMENT-PUBLICATION-CONSENT-20261115.json'),Path(__file__)]
files+=list((T/'code').glob('*.diff'))
rows=[{**spec(p),'relative_validation_path':'first-freeze-actual-E48-context/'+str(i)+'-'+p.name}for i,p in enumerate(files)]
h['articles'][0]['section']['evidence'].extend(spec(p)for p in files)
h.update(first_freeze_includes_actual_original_HOST_programs_and_execution_sidecar=True,source_document_publication_authority=spec('/dev/shm/USER-EXPLICIT-EIGHT-FINAL-SOURCE-DOCUMENT-PUBLICATION-CONSENT-20261115.json'))
report=json.loads((O/'report.json').read_text());report['first_freeze_actual_execution_context']=[spec(p)for p in files];write(O/'report.json',report)
inp=json.loads((O/'actual-sample-input.json').read_text());inp['articles']=[h['articles'][0]['section']];write(O/'actual-sample-input.json',inp)
for r in h['validation_files']:
 if Path(r['path']) in (O/'report.json',O/'actual-sample-input.json'):
  r.update(bytes=Path(r['path']).stat().st_size,sha256=spec(r['path'])['sha256'])
h['validation_files']+=rows
for r in h['validation_files']:
 assert spec(r['path'])=={k:r[k]for k in ('path','bytes','sha256')},r['path']
write(hp,h);print(json.dumps({'handoff':spec(hp),'validation_count':len(h['validation_files'])},ensure_ascii=False))
