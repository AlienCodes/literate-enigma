"""Attach actual execution context once, before the new handoff is announced.
Never updates source/native/producer evidence or any previously frozen handoff.
"""
from pathlib import Path
import hashlib,json,shutil
T=Path(__file__).resolve().parent; O=T/'validated'
P=Path('/dev/shm/normal18-book48-51-52-HOST-output-tmp-path-only-20261115/book48-source46')
R=Path('/workspace/work/review46-native/43702082473/46')
def spec(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
hp=O/'archive-handoff.json';h=json.loads(hp.read_text())
assert h['source_run']==43702082473 and h['production_delivery_eligible'] is True and h['preview_only'] is False
assert h['articles'][0]['source_id']=='46' and h['articles'][0]['new_id']=='48' and h['articles'][0]['passed_per_article'] is True
assert not any('first-freeze-actual-E52-context/' in r['relative_validation_path'] for r in h['validation_files'])
actualready=P/'ready-book48-source46.json';ready=json.loads(actualready.read_text())
files=[P/'ACTUAL-HOST-NORMAL18-EXECUTION-ORIGINAL-PROGRAMS-AND-BUDGET-SIDECAR.json',Path('/workspace/work/review46-sourceQA/43702082473-E51/archive-handoff.json'),Path('/dev/shm/root-three-normal18-explicit-data-only-code-adoption-20261115.json'),Path('/dev/shm/root-normal18-three-article-HOST-output-tmp-path-only-adoption-20261115.json'),P/'actual-46-upstream-execution.log',P/'actual-46-compose-execution.log',P/'ACTUAL-SUCCESS-SOURCEQA-AND-HOST-BUDGET-BEFORE-UPSTREAM.json',P/'ACTUAL-HOST-BUDGET-AFTER-UPSTREAM-BEFORE-COMPOSE.json',actualready,Path('/dev/shm/root-source46-E49-actual-API-and-exact-new-code-stamp-sourceQA-entry-adoption-20261115.json'),Path('/dev/shm/root-source46-E52-original-normal18-data-only-final-consumer-adoption-20261115.json'),T/'E52-SOURCE46-NORMAL18-DATA-ONLY-FINAL-CONSUMER-ROOT-REVIEW-HANDOFF.json',T/'E52-original-code-inverse-and-unchanged-numeric-logic-proof.json',R/'measure_actual46_all_pages.py',R/'actual-working-source46-original-dual-resolution-geometry-report.json',T/'actual-final-review/actual-final-complete-decode-proof.json',T/'actual-final-review/actual-final-full-decode.stderr.log',T/'actual-final-review/actual-final-full-decode.stdout.log',Path('/dev/shm/USER-EXPLICIT-EIGHT-FINAL-SOURCE-DOCUMENT-PUBLICATION-CONSENT-20261115.json'),Path(__file__)]
files+=list((T/'code').glob('*.diff'))
rows=[{**spec(p),'relative_validation_path':'first-freeze-actual-E52-context/'+str(i)+'-'+p.name}for i,p in enumerate(files)]
h['articles'][0]['section']['evidence'].extend(spec(p)for p in files)
h.update(original_maker_unchanged=False,actual_exact_format_code_certification=spec(R/'artifact-files/46-exact-user-format-original-full-fastcheck.json'),actual_new_original_fullfastcheck_stamp=spec(R/'artifact-files/source46-actual-new-format-full-fastcheck-stamp.json'),format_code_certificate_alone_claims_article_or_audio_acceptance=False,first_freeze_includes_actual_original_HOST_programs_and_execution_sidecar=True,source_document_publication_authority=spec('/dev/shm/USER-EXPLICIT-EIGHT-FINAL-SOURCE-DOCUMENT-PUBLICATION-CONSENT-20261115.json'))
report=json.loads((O/'report.json').read_text());report['first_freeze_actual_execution_context']=[spec(p)for p in files];write(O/'report.json',report)
inp=json.loads((O/'actual-sample-input.json').read_text());inp['articles']=[h['articles'][0]['section']];write(O/'actual-sample-input.json',inp)
for r in h['validation_files']:
 if Path(r['path']) in (O/'report.json',O/'actual-sample-input.json'):
  r.update(bytes=Path(r['path']).stat().st_size,sha256=spec(r['path'])['sha256'])
h['validation_files']+=rows
for r in h['validation_files']:
 assert spec(r['path'])=={k:r[k]for k in ('path','bytes','sha256')},r['path']
write(hp,h);print(json.dumps({'handoff':spec(hp),'validation_count':len(h['validation_files'])},ensure_ascii=False))
