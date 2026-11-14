"""Read the connector's temporary OAI URL and verify actual native ZIP bytes."""
import argparse,hashlib,json,os
from pathlib import Path
from urllib.request import urlopen
import zipfile

p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--article',required=True)
p.add_argument('--sha256',required=True);p.add_argument('--bytes',type=int,required=True)
p.add_argument('--output',required=True);p.add_argument('--artifact-id',type=int,required=True)
p.add_argument('--run-id',type=int,required=True);p.add_argument('--job-id',type=int,required=True);p.add_argument('--status-only',action='store_true');p.add_argument('--inspect-native',action='store_true')
a=p.parse_args();no=a.article.zfill(2);target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
temporary=target.with_suffix('.zip.partial');assert not target.exists() and not temporary.exists()
digest=hashlib.sha256();count=0
try:
    with urlopen(a.url,timeout=90) as source,temporary.open('wb') as dest:
        while block:=source.read(1048576):dest.write(block);digest.update(block);count+=len(block)
    assert digest.hexdigest()==a.sha256 and count==a.bytes,'Actual GitHub artifact digest/bytes differ.'
    with zipfile.ZipFile(temporary)as archive:
        names=[n for n in archive.namelist()if Path(n).name==no+'-status.json'];assert len(names)==1
        raw=archive.read(names[0]);status=json.loads(raw);assert status['article']==no
    receipt={'run_id':a.run_id,'article':no,'artifact_id':a.artifact_id,'job_id':a.job_id,
             'actual_zip_sha256':digest.hexdigest(),'actual_zip_bytes':count,
             'native_status_member':names[0],'native_status_sha256':hashlib.sha256(raw).hexdigest(),
             'native_status_passed':status['passed'],'native_stage':status['stage'],'quality_acceptance':False,'read_only_native_inspection':a.inspect_native}
    if a.status_only:
        output=target.parent/(no+'-status.json');output.write_bytes(raw)
        receipt['read_only_failure_metadata_only']=True;receipt['zip_removed']=True
        temporary.unlink()
    else:
        if a.inspect_native:(target.parent/(no+'-native-outer-status.json')).write_bytes(raw)
        if not a.inspect_native:assert status.get('passed')is True and status.get('stage')=='final4K-passed' and status.get('canonical_pipeline_passed')is True,'Only actual passed native jobs may be ingested.'
        os.replace(temporary,target);receipt['actual_zip_path']=str(target)
    (target.parent/'connector-download-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False))
finally:
    temporary.unlink(missing_ok=True)
