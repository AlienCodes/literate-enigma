"""Publish the four finished cover images using the native GitHub Actions token."""
from pathlib import Path
from urllib.parse import quote
import base64, concurrent.futures, hashlib, json, os, subprocess

ROOT = Path(__file__).resolve().parent
REPO = os.environ.get('GITHUB_REPOSITORY', 'alienalgorithm/postgraduate-vocabulary')
TAG = os.environ.get('COVER_RELEASE_TAG', 'bilibili-covers-2026.11.13-v2')

def run(*args):
    p = subprocess.run(['gh', *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2000:])
    return p.stdout

def api(path):
    return json.loads(run('api', path))

def send(path, body, method='POST'):
    p = subprocess.run(['gh', 'api', '--method', method, path, '--input', '-'], input=json.dumps(body), capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2000:])
    return json.loads(p.stdout)

def main():
    m = json.loads((ROOT / 'manifest.json').read_text())
    assert m['passed'] and len(m['assets']) == 4 and m['tag'] == TAG
    assert {(a['ratio'], a['format']) for a in m['assets']} == {('16:9','JPEG'),('4:3','JPEG'),('16:9','PNG'),('4:3','PNG')}
    for a in m['assets']:
        p = ROOT / a['path']
        assert p.stat().st_size == a['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == a['sha256']
        assert a['width'] * int(a['ratio'].split(':')[1]) == a['height'] * int(a['ratio'].split(':')[0])
    commit = os.environ['GITHUB_SHA']
    assert api(f'repos/{REPO}/git/ref/tags/{TAG}')['object']['sha'] == commit
    prior = [r for r in api(f'repos/{REPO}/releases?per_page=100') if r['tag_name'] == TAG]
    assert len(prior) <= 1
    notes = '考研学人 · 70篇文章搞定考研单词 · 约4200考研重点词汇。\n\n16:9为1600×900，4:3为1440×1080；两版分别安排构图。JPG可直接上传B站，PNG为无损版。附件仅含四张成品封面。\n\n文案：70篇文章搞定考研单词／考研学人／约4200考研重点词汇／科普·历史·趣闻。原始生成图、提示词及尺寸导出程序完整保存在仓库。'
    release = prior[0] if prior else send(f'repos/{REPO}/releases', {'tag_name':TAG, 'target_commitish':commit, 'draft':True, 'make_latest':'false', 'name':'考研学人｜70篇文章｜B站封面（16:9与4:3）', 'body':notes})
    rid = release['id']
    existing = {a['name']:a for a in release['assets']}
    def upload(a):
        if a['name'] not in existing:
            assert release['draft']
            run('release','upload',TAG,str(ROOT / a['path']),'--repo',REPO)
        actual = next(x for x in api(f'repos/{REPO}/releases/{rid}/assets?per_page=100') if x['name'] == a['name'])
        assert actual['size'] == a['bytes'] and actual['digest'] == 'sha256:' + a['sha256'] and actual['state'] == 'uploaded'
        return {**a, 'asset_id':actual['id'], 'download_url':actual['browser_download_url'], 'remote_SHA256_verified':True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        assets = list(pool.map(upload,m['assets']))
    assert len(api(f'repos/{REPO}/releases/{rid}/assets?per_page=100')) == 4
    if release['draft']:
        send(f'repos/{REPO}/releases/{rid}', {'draft':False, 'make_latest':'false'}, 'PATCH')
    actual = api(f'repos/{REPO}/releases/tags/{TAG}')
    assert not actual['draft']
    report = {'passed':True,'repository':REPO,'tag':TAG,'source_commit':commit,'release_url':actual['html_url'],'assets':assets,'no_existing_PDF_or_video_modified':True}
    record = 'B站封面/考研学人-70篇/2026-11-13-v2/发布核验.json'
    body = {'message':'保存B站两种比例封面的Release上传后核验 [skip ci]','branch':'main','content':base64.b64encode((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()).decode()}
    files = api(f'repos/{REPO}/contents/' + quote('B站封面/考研学人-70篇/2026-11-13-v2',safe='/'))
    old = next((x for x in files if x['name']=='发布核验.json'),None)
    if old:
        body['sha'] = old['sha']
    send(f'repos/{REPO}/contents/' + quote(record,safe='/'),body,'PUT')
    print(json.dumps({'published':True,'release_url':actual['html_url'],'assets':4,'all_remote_SHA256_verified':True},ensure_ascii=False),flush=True)

if __name__ == '__main__':
    main()
