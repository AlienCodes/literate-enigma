#!/usr/bin/env python3
"""Run the original per-article importer with actually acquired connector API data.

No API success/status fields are manufactured. This exact single native ZIP and
the original observed-source roles remain the evidence; no media is generated.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import delivery as D
import ingest_inline_article as V

B = Path(__file__).resolve().parent
P = json.loads((B / 'actual30-bound-source-profile.json').read_text())

def checked(row):
    p = Path(row['path'])
    D.require(p.is_file() and p.stat().st_size == row['bytes'] and D.digest(p) == row['sha256'], 'Exact source30 input file differs: ' + str(p))
    return p

class ActualConnectorEvidence:
    def __init__(self):
        self.run = D.load(checked(P['api_run']))
        self.job = D.load(checked(P['api_job']))
        self.artifact = D.load(checked(P['api_artifact']))
        D.require(self.run['id'] == self.job['run_id'] == self.artifact['workflow_run']['id'] == P['run_id'] and
                  self.run['head_sha'] == self.job['head_sha'] == self.artifact['workflow_run']['head_sha'] == P['head_sha'], 'Actual API identity differs')
        D.require(self.run['status'] == self.job['status'] == 'completed' and self.run['conclusion'] == self.job['conclusion'] == 'success' and
                  self.job['id'] == P['job_id'] and self.artifact['id'] == P['artifact_id'] and self.job['run_attempt'] == self.run['run_attempt'], 'Actual source30 native is not a genuine completed success')
    def api(self, repo, route):
        D.require(repo == 'AlienCodes/literate-enigma' == D.BACKUP[0], 'Exact connector repository differs')
        routes = {
            f'actions/runs/{P["run_id"]}/attempts/{self.job["run_attempt"]}': self.run,
            f'actions/jobs/{P["job_id"]}': self.job,
            f'actions/artifacts/{P["artifact_id"]}': self.artifact,
        }
        D.require(route in routes, 'Unacquired or unrelated API route: ' + route)
        return routes[route]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'finalize'])
    parser.add_argument('--boundary-review')
    a = parser.parse_args()
    D.require(P['article'] == '30' and P['book_order'] == '55' and P['profile_frozen'] is True, 'Only exact actual30 profile can run')
    for row in P['mandatory_evidence']:
        checked(row)
    artifact = checked(P['zip'])
    status = D.load(checked(P['actual_status']))
    D.require(status['article'] == '30' and status['passed'] is True and status['canonical_pipeline_passed'] is True and
              status['stage'] == 'final4K-passed' and status['request_source_sha256'] == P['request_source_sha256'], 'Actual native source tuple/gates differ')
    for row in P['observed_source_files'].values():
        checked(row)
    D.GitHub = ActualConnectorEvidence
    args = argparse.Namespace(article='30', native_root=P['native_root'], output_root=P['output_root'], zip=str(artifact),
                              run_id=P['run_id'], job_id=P['job_id'], artifact_id=P['artifact_id'], boundary_review=a.boundary_review)
    if a.phase == 'prepare':
        V.prepare(args)
        context_path = Path(P['native_root']) / 'inline-adapter-context.json'
        context = D.load(context_path)
        context['explicit_approved_video_layout'] = P['approved_video_layout']
        context['extra_evidence_local_files'] += [row['path'] for row in P['mandatory_evidence']]
        context['actual_connector_evidence_entry'] = str(Path(__file__).resolve())
        D.write(context_path, context)
    else:
        D.require(a.boundary_review, 'Actual five native boundary images must be viewed')
        dest = Path(P['output_root']) / 'actual30-intake-code-and-api-evidence'
        dest.mkdir(parents=True, exist_ok=False)
        rows = [P['api_run'], P['api_job'], P['api_artifact'], *P['mandatory_evidence']]
        rows += [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': D.digest(p)} for p in (Path(__file__).resolve(), B/'actual30-bound-source-profile.json', B/'only-current-layout-data.diff')]
        for i, row in enumerate(rows):
            source = checked(row)
            V.link_exact(source, dest / (str(i).zfill(2) + '-' + source.name))
        V.finalize(args)

if __name__ == '__main__':
    main()
