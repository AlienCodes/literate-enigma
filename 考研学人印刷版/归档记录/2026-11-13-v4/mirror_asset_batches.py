"""Mirror frozen original-byte V4 Git assets in bounded pushes after HTTP 503.

Writes only the dedicated asset branch; main/master are never updated here.
The already archived production payload remains immutable.
"""
from pathlib import Path
import json, subprocess

HERE = Path(__file__).resolve().parent
GITDIR = HERE / 'archive-assets.git'
REPO = 'AlienCodes/literate-enigma'
BRANCH = 'codex/punk-print-assets-20261113-v4'
URL = f'https://github.com/{REPO}.git'
OUT = HERE / 'backup-batch-mirror-journal.json'

def git(*args, allowed=False):
    r = subprocess.run(['git', '--git-dir='+str(GITDIR), *args], text=True, capture_output=True)
    if r.returncode and not allowed:
        raise RuntimeError(r.stderr[-3000:])
    return r

def remote():
    r = git('ls-remote', URL, 'refs/heads/'+BRANCH)
    return r.stdout.split()[0] if r.stdout.strip() else None

rows = [x for x in json.loads((HERE/'asset-push-journal.json').read_text())
        if x['repository']=='alienalgorithm/postgraduate-vocabulary']
commits = [x['commit'] for x in rows]
head = remote()
assert head is None or head in commits, 'Unexpected backup asset head; inspect before writing'
done = commits.index(head)+1 if head else 0
journal = json.loads(OUT.read_text()) if OUT.exists() else []
for row in rows[done:]:
    expected = head
    assert remote() == expected, 'Concurrent asset-branch update; refusing to overwrite'
    for attempt in range(1, 4):
        r = git('-c', 'http.postBuffer=209715200', 'push', '--quiet', URL,
                row['commit']+':refs/heads/'+BRANCH, allowed=True)
        actual = remote()
        if actual == row['commit']:
            break
        assert actual == expected, 'Unexpected concurrent asset head after failed push'
        print(json.dumps({'batch':row['batch'], 'attempt':attempt,
                          'error':r.stderr[-1800:]}, ensure_ascii=False), flush=True)
    else:
        raise RuntimeError('Three bounded push attempts failed: '+row['batch'])
    head = row['commit']
    saved = {**row, 'repository':REPO, 'remote_ref_verified':True}
    journal.append(saved)
    OUT.write_text(json.dumps(journal, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(saved, ensure_ascii=False), flush=True)

result = json.loads((HERE/'asset-primary.json').read_text())
assert remote() == result['asset_commit']
result['repository'] = REPO
result['transfer'] = 'bounded original primary asset commits after one HTTP503 full-mirror failure'
(HERE/'asset-backup.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False), flush=True)
