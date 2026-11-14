"""Pin exact approved source requests, then start only the selected official jobs."""
import argparse
import base64
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAY = Path('/workspace/work/video-audit70-20261113/payload')
LOCAL = Path('/workspace/work/github-publication/target')
TASK = ROOT / '.github/video-revision-batch'
REPO = 'AlienCodes/literate-enigma'
BRANCH = 'codex/finish-05-and-summaries-20261112'


def api(path, data=None, method='GET'):
    args = ['gh', 'api', 'repos/' + REPO + '/' + path]
    if method != 'GET':
        args += ['-X', method]
    if data is not None:
        args += ['--input', '-']
    p = subprocess.run(args, input=None if data is None else json.dumps(data).encode(),
                       capture_output=True, check=True)
    return json.loads(p.stdout)


def read(path):
    for folder in (PAY, LOCAL):
        if (folder / path).is_file():
            return (folder / path).read_bytes()
    return subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=LOCAL)


parser = argparse.ArgumentParser()
parser.add_argument('articles', nargs='+')
parser.add_argument('--bulk-upload', action='store_true', help='Transfer request blobs in one isolated git push.')
args = parser.parse_args()
selected = [s.zfill(2) for s in args.articles]
assert len(selected) == len(set(selected)) and all(s.isdigit() and 1 <= int(s) <= 70 for s in selected)
(TASK / 'articles.json').write_text(json.dumps(selected, indent=2) + '\n')
manuscripts = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD', '--', '新版定稿'], cwd=LOCAL).decode().split('\0')
hashes = {}
for no in selected:
    request = TASK / 'request' / no
    md = next(path for path in manuscripts if path.startswith('新版定稿/' + no + '-'))
    paths = [f'视频/脚本/{no}.json', f'视频/工具/初稿生成/gen{no}.py', md]
    pending = f'视频/制作记录/{no}_待改清单.md'
    if (PAY / pending).is_file():
        paths.append(pending)
    confirmations = f'视频/制作记录/逐句确认/{no}.json'
    if (PAY / confirmations).is_file():
        paths.append(confirmations)
    for path in paths:
        destination = request / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = read(path)
        destination.write_bytes(data)
        hashes[path] = hashlib.sha256(data).hexdigest()
    quote = '然后你根据这些意见重新生成这个4k视频。' if no == '11' else '所有的这些东西改完之后，我们要重新生成视频定稿的呀。'
    authorization = {'篇': no, '日期': '2026-11-13', '原话': quote,
                     '用于': f'定稿{no}：按本轮批准的重点词、小字、旧简述清理、清晰简述和排版要求生成4K；逐篇核验并保存完整MP4到GitHub及Release。',
                     '来源': '2026-11-13本会话，用户统一要求全部修订视频重出4K并定稿；第37手另有本篇明确重出指令。'}
    (request / 'user-authorization.json').write_text(json.dumps(authorization, ensure_ascii=False, indent=2) + '\n')

# Cross-article vocabulary checks must read the same reviewed70-article data
# that passed locally, including explicitly permitted repeated focus phrases.
# The production target still uses its own immutable request above.
context = TASK / 'context'
context_hashes = {}
for n in range(1, 71):
    no = f'{n:02d}'
    md = next(path for path in manuscripts if path.startswith('新版定稿/' + no + '-'))
    for path in [f'视频/脚本/{no}.json', md]:
        data = read(path)
        destination = context / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        context_hashes[path] = hashlib.sha256(data).hexdigest()
(context / 'manifest.json').write_text(json.dumps({
    'kind': 'exact_reviewed_cross_article_source_context',
    'article_ids': [f'{n:02d}' for n in range(1, 71)],
    'files_sha256': context_hashes,
}, ensure_ascii=False, indent=2) + '\n')
updates = []
if args.bulk_upload:
    assets=ROOT/'request-assets'
    assets.mkdir(exist_ok=True)
    def command(argv):
        return subprocess.check_output(['git',*argv],cwd=assets,text=True).strip()
    asset_branch='codex/rebuild-requests-assets-ready41-20261114'
    if not (assets/'.git').is_dir():
        command(['init','-q','-b',asset_branch])
        command(['config','user.name','Codex'])
        command(['config','user.email','codex@users.noreply.github.com'])
        command(['config','credential.helper','!gh auth git-credential'])
    for path in sorted((ROOT/'.github').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            target=assets/path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
    command(['add','--all','.github'])
    command(['commit','-q','--allow-empty','-m','Freeze exact reviewed source requests for official4K rebuild [skip ci]'])
    asset_commit=command(['rev-parse','HEAD'])
    command(['push','-q','https://github.com/'+REPO+'.git',asset_commit+':refs/heads/'+asset_branch])
    records=subprocess.check_output(['git','ls-tree','-rz','HEAD','--','.github'],cwd=assets)
    for record in records.split(b'\0'):
        if not record:continue
        meta,path=record.split(b'\t',1);mode,kind,oid=meta.decode().split()
        assert kind=='blob' and mode=='100644'
        updates.append({'path':path.decode(),'mode':mode,'type':kind,'sha':oid})
else:
    for path in sorted((ROOT / '.github').rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        data = path.read_bytes()
        blob = api('git/blobs', {'content': base64.b64encode(data).decode(), 'encoding': 'base64'}, 'POST')
        assert blob['sha'] == hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        updates.append({'path': str(path.relative_to(ROOT)), 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
# Fetch the current parent after the asset transfer so an unrelated relay
# request cannot cause an avoidable stale-parent race during a long upload.
parent = api('git/ref/heads/' + BRANCH)['object']['sha']
base = api('git/commits/' + parent)['tree']['sha']
tree = api('git/trees', {'base_tree': base, 'tree': updates}, 'POST')['sha']
commit = api('git/commits', {'message': 'Rebuild revised articles in official4K: ' + ','.join(selected),
                           'tree': tree, 'parents': [parent]}, 'POST')['sha']
api('git/refs/heads/' + BRANCH, {'sha': commit, 'force': False}, 'PATCH')
state = {'repository': REPO, 'branch': BRANCH, 'commit': commit,
         'selected': selected, 'request_sha256': hashes,
         'cross_article_context_sha256': context_hashes, 'stage': 'GitHub Actions queued'}
if args.bulk_upload:
    state['request_assets_commit']=asset_commit
(ROOT / 'TASK-STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(state, ensure_ascii=False), flush=True)
