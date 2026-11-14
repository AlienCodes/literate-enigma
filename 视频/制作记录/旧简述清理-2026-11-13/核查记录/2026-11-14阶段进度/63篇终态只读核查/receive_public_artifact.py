"""Verify one GitHub ZIP digest; retain only public JSON/text evidence; immediately remove ZIP.

Never exports media, PCM, GT, cache bytes or raw waveform arrays. The temporary
OAI file URL is not recorded in any output. Old successful53/64 files stay intact.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import tempfile
import urllib.request
from urllib.parse import urlparse
import zipfile

HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--article',required=True)
ap.add_argument('--artifact-id',type=int,required=True)
ap.add_argument('--expected-sha256',required=True)
ap.add_argument('--expected-bytes',type=int,required=True)
ap.add_argument('--url',required=True)
args=ap.parse_args();no=args.article.zfill(2)
assert re.fullmatch(r'\d{2}',no)
assert re.fullmatch(r'[0-9a-f]{64}',args.expected_sha256)
assert urlparse(args.url).scheme=='https'
out=HERE/'public-evidence'/no;out.mkdir(parents=True,exist_ok=True)
temporary=HERE/'temporary-downloads';temporary.mkdir(exist_ok=True)
sha=lambda value:hashlib.sha256(value).hexdigest()
removed=[]


def public_json(value,path=''):
    if isinstance(value,dict):
        result={}
        for key,item in value.items():
            lower=key.lower()
            if re.fullmatch(r'(pcm|waveform|audio_data|raw_audio|audio_samples|samples|gt|ground_truth|cache_bytes|cache_data|pickled_data|base64_audio)',lower):
                removed.append(path+'/'+key);continue
            result[key]=public_json(item,path+'/'+key)
        return result
    if isinstance(value,list):
        if len(value)>64 and all(isinstance(x,(int,float)) for x in value):
            removed.append(path);return {'omitted_raw_numeric_array':True,'length':len(value)}
        return [public_json(x,path+'/'+str(i)) for i,x in enumerate(value)]
    return value


receipt={'article':no,'artifact_id':args.artifact_id,'run_id':43523430839,
         'github_declared_zip_sha256':args.expected_sha256,
         'github_declared_zip_bytes':args.expected_bytes,
         'retrieval':'GitHub connector download_workflow_artifact returned OAI file URL; urllib HTTPS read',
         'completed_utc':None,'zip_digest_verified':False,'zip_removed_after_public_extraction':False,
         'private_audio_GT_cache_or_media_extracted':False,'public_files':[],'skipped_members':[]}
path=None
try:
    with tempfile.NamedTemporaryFile(prefix=f'{no}-',suffix='.zip',dir=temporary,delete=False) as target:
        path=Path(target.name);digest=hashlib.sha256();count=0
        with urllib.request.urlopen(args.url,timeout=90) as response:
            while block:=response.read(1048576):
                target.write(block);digest.update(block);count+=len(block)
    actual=digest.hexdigest()
    assert actual==args.expected_sha256,(no,'actual ZIP digest differs from GitHub metadata',actual)
    assert count==args.expected_bytes,(no,'ZIP byte count differs',count,args.expected_bytes)
    receipt.update({'actual_zip_sha256':actual,'actual_zip_bytes':count,'zip_digest_verified':True})
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist();assert len(names)==len(set(names))
        for member in archive.infolist():
            pure=PurePosixPath(member.filename)
            assert not pure.is_absolute() and '..' not in pure.parts and '\\' not in member.filename
            if member.is_dir():continue
            name=pure.name
            public_name=(name.startswith(no+'-') and name.endswith('.json') and
                         not re.search(r'(?:private|cache[-_.](?:data|bytes|dump)|GT[-_.]|raw[-_.]|waveform|pcm|\.pkl)',name,re.I))
            safe_log=(name.startswith(no+'-') and name.endswith(('.log','.txt')) and
                      not re.search(r'(?:private|cache|GT|raw|pcm)',name,re.I))
            if not (public_name or safe_log) or member.file_size>8*1024*1024:
                receipt['skipped_members'].append({'name':member.filename,'bytes':member.file_size});continue
            raw=archive.read(member)
            if public_name:
                data=json.loads(raw);before=len(removed);clean=public_json(data,member.filename)
                payload=raw if len(removed)==before else (json.dumps(clean,ensure_ascii=False,indent=2)+'\n').encode()
                destination=out/name
                if len(removed)>before:destination=out/('sanitized-'+name)
            else:
                raw.decode('utf-8');payload=raw;destination=out/name
            assert not destination.exists(),('Never overwrite existing evidence',destination)
            destination.write_bytes(payload)
            receipt['public_files'].append({'artifact_member':member.filename,'path':str(destination),
                                           'artifact_member_sha256':sha(raw),'saved_sha256':sha(payload),
                                           'bytes':len(payload),'sanitized':payload!=raw})
    receipt['removed_private_fields']=removed
    assert any(Path(r['path']).name==no+'-status.json' for r in receipt['public_files']), 'Actual unmodified native status is required.'
finally:
    if path is not None:path.unlink(missing_ok=True)
    receipt['zip_removed_after_public_extraction']=path is None or not path.exists()
    receipt['completed_utc']=datetime.now(timezone.utc).isoformat()
    (out/'artifact-retrieval-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'article':no,'artifact_id':args.artifact_id,'zip_verified':receipt['zip_digest_verified'],
                  'zip_removed':receipt['zip_removed_after_public_extraction'],
                  'public_files':len(receipt['public_files']),'skipped_members':len(receipt['skipped_members'])}))
