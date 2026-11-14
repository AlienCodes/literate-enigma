"""Publish one actually validated, permanently archived article without altering media."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
REPO = 'alienalgorithm/postgraduate-vocabulary'


def api(path, method='GET', data=None, missing_ok=False):
    command = ['gh', 'api', 'repos/' + REPO + '/' + path]
    if method != 'GET':
        command += ['-X', method]
    if data is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=None if data is None else json.dumps(data).encode(), capture_output=True)
    if missing_ok and result.returncode and b'(HTTP 404)' in result.stderr:
        return None
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace'))
    return json.loads(result.stdout)


def sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


EXPECTED = {'14':'21','27':'22','13':'23','15':'25','17':'26','26':'27','36':'28','33':'30','47':'32','34':'33','62':'34'}
TAG = 'reviewed-eleven-4k-hold06-v1'
ASSET = 'Reviewed-11-Articles-4K-0.6s-FINAL.zip'

def stable_zip_add(archive, name, data):
    info = zipfile.ZipInfo(name, (2026,11,14,0,0,0))
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)

def main():
    if os.environ.get('GITHUB_REPOSITORY') != REPO:
        return
    config = json.loads((HERE/'MANIFEST.json').read_text())
    specs = config['videos']
    assert config['actual_all_11_full_validation_and_dual_archive_passed'] is True
    assert config['end_reading_pause_seconds'] == 0.6 and config['tag'] == TAG
    assert len(specs) == 11 and {v['source_id']:v['book_order'] for v in specs} == EXPECTED
    assert len({v['release_name'] for v in specs}) == 11
    out = Path(os.environ['GITHUB_WORKSPACE'])/'bundle-release-output'
    out.mkdir(exist_ok=True)
    verified = []
    for spec in sorted(specs, key=lambda x:int(x['book_order'])):
        assert spec['actual_complete_validation_passed'] is True and spec['actual_dual_permanent_archive_passed'] is True
        assert spec['preview_only'] is False and spec['end_reading_pause_seconds'] == 0.6
        assert 0.6 <= spec['actual_end_reading_pause_seconds'] < 0.633334
        assert spec['release_name'].endswith('.mp4') and Path(spec['release_name']).name == spec['release_name']
        path = out/spec['release_name']
        raw_url = 'https://raw.githubusercontent.com/'+REPO+'/'+spec['archived_commit']+'/'+urllib.parse.quote(spec['repo_path'],safe='/')
        with urllib.request.urlopen(raw_url,timeout=180) as response, path.open('wb') as target:
            while chunk := response.read(1024*1024):
                target.write(chunk)
        assert path.stat().st_size == spec['bytes'] and sha(path) == spec['sha256']
        verified.append({'source_id':spec['source_id'],'book_order':spec['book_order'],'file':spec['release_name'],'bytes':spec['bytes'],'sha256':spec['sha256']})
    bundle = out/ASSET
    with zipfile.ZipFile(bundle,'w',allowZip64=True) as archive:
        for item in verified:
            stable_zip_add(archive,item['file'],(out/item['file']).read_bytes())
        metadata = {'videos':verified,'nominal_end_reading_pause_seconds':0.6,'MP4_bytes_preserved':True}
        stable_zip_add(archive,'MANIFEST.json',(json.dumps(metadata,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == 12
        for item in verified:
            payload = archive.read(item['file'])
            assert len(payload) == item['bytes'] and hashlib.sha256(payload).hexdigest() == item['sha256']
    digest = sha(bundle)
    marker = 'Reviewed11 hold06 final ZIP SHA-256: '+digest
    release = api('releases/tags/'+TAG,missing_ok=True)
    if release is None:
        matches = [x for x in api('releases?per_page=100') if x['tag_name']==TAG and marker in (x.get('body') or '')]
        assert len(matches)<=1
        release = matches[0] if matches else None
    if release is None:
        release = api('releases','POST',{'tag_name':TAG,'target_commitish':config['final_directory_commit'],'name':'考研学人｜本轮11篇审核修订4K定稿合集｜末句停留0.6秒','body':'本轮11篇已审核修订4K定稿，末句后正文保持约0.6秒再切插图。\n\n合集内MP4字节与各篇已验收文件完全一致，附文件校验清单；旧版本与修改记录保留。\n\n<!-- '+marker+' -->','draft':True,'prerelease':False})
    assert release['tag_name']==TAG and marker in (release.get('body') or '')
    assets = api('releases/'+str(release['id'])+'/assets?per_page=100')
    assert len(assets)<=1 and all(x['name']==ASSET for x in assets)
    if not assets:
        subprocess.run(['gh','release','upload',TAG,str(bundle),'--repo',REPO],check=True)
    assets = api('releases/'+str(release['id'])+'/assets?per_page=100')
    assert len(assets)==1
    asset=assets[0]
    assert asset['state']=='uploaded' and asset['size']==bundle.stat().st_size and asset['digest']=='sha256:'+digest
    if release['draft']:
        api('releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':False,'make_latest':'false'})
    tag = api('git/ref/tags/'+TAG)['object']
    assert tag['type']=='commit' and tag['sha']==config['final_directory_commit']
    downloaded=hashlib.sha256();size=0
    with urllib.request.urlopen(asset['browser_download_url'],timeout=180) as response:
        while chunk:=response.read(1024*1024):
            downloaded.update(chunk);size+=len(chunk)
    assert size==bundle.stat().st_size and downloaded.hexdigest()==digest
    release=api('releases/'+str(release['id']));assert not release['draft']
    receipt={'passed':True,'video_count':11,'end_reading_pause_seconds':0.6,'release_id':release['id'],'release_url':release['html_url'],'download_url':asset['browser_download_url'],'ZIP_bytes':size,'ZIP_sha256':digest,'every_zip_MP4_size_and_sha256_verified':True,'actual_public_entire_ZIP_download_verified':True,'videos':verified,'manifest_sha256':sha(HERE/'MANIFEST.json'),'publisher_sha256':sha(__file__),'native_actions_run_id':int(os.environ['GITHUB_RUN_ID']),'native_actions_head_sha':os.environ['GITHUB_SHA'],'other_release_or_media_deleted':False}
    (out/'RELEASE-VERIFICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False),flush=True)

if __name__=='__main__':
    main()
