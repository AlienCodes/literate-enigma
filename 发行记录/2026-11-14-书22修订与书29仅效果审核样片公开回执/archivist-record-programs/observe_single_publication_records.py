"""Read actual publication run/artifact/release metadata and immutable helper sources."""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import json
import subprocess
import urllib.parse
import urllib.request
import zipfile

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',required=True);parser.add_argument('--run-id',required=True,type=int);parser.add_argument('--release-id',required=True,type=int);parser.add_argument('--zip-bytes',required=True,type=int);parser.add_argument('--zip-sha256',required=True);parser.add_argument('--publisher-path',required=True);parser.add_argument('--failed-run-id',action='append',default=[],type=int);a=parser.parse_args()
    d=Path(a.directory).resolve();repo='alienalgorithm/postgraduate-vocabulary'
    token=subprocess.check_output(['gh','auth','token'],text=True).strip()
    def api(path):
        url='https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%')
        with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Codex-exact-publication-record-observation'}),timeout=30) as r:return json.loads(r.read())
    def save(name,value):(d/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    run=api('actions/runs/'+str(a.run_id));assert run['status']=='completed' and run['conclusion']=='success'
    jobs=api('actions/runs/'+str(a.run_id)+'/jobs');artifacts=api('actions/runs/'+str(a.run_id)+'/artifacts');release=api('releases/'+str(a.release_id));assert release['draft'] is False
    z=d/'native-release-verification.zip';raw=z.read_bytes();assert len(raw)==a.zip_bytes and hashlib.sha256(raw).hexdigest()==a.zip_sha256
    with zipfile.ZipFile(z) as archive:
        assert archive.testzip() is None and archive.namelist()==['RELEASE-VERIFICATION.json']
        assert archive.read('RELEASE-VERIFICATION.json')==(d/'RELEASE-VERIFICATION.json').read_bytes()
    matches=[r for r in artifacts['artifacts'] if r['size_in_bytes']==len(raw) and not r['expired']];assert len(matches)==1
    artifact=matches[0]
    if artifact.get('digest'):assert artifact['digest']=='sha256:'+a.zip_sha256
    save('RUN.json',run);save('NATIVE-JOBS.json',jobs);save('NATIVE-ARTIFACTS.json',artifacts);save('PUBLIC-RELEASE-OBSERVATION.json',release)
    sources=[]
    def source_snapshot(observed,label):
        for path,basename in [(a.publisher_path,'publish_single.py'),(observed['path'].split('@',1)[0],'workflow.yml')]:
            assert path.startswith('.github/')
            result=api('contents/'+urllib.parse.quote(path,safe='/')+'?ref='+observed['head_sha']);assert result['encoding']=='base64'
            source=base64.b64decode(result['content']);gitsha=hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest();assert gitsha==result['sha']
            local='actual-'+label+'-'+basename;(d/local).write_bytes(source)
            sources.append({'actual_run_id':observed['id'],'actual_commit':observed['head_sha'],'repository_path':path,'local_file':local,'Git_blob_SHA':gitsha,'bytes':len(source),'sha256':hashlib.sha256(source).hexdigest()})
    source_snapshot(run,'successful-native-head')
    failures=[]
    for number in a.failed_run_id:
        previous=api('actions/runs/'+str(number));assert previous['status']=='completed' and previous['conclusion']=='failure'
        save('FAILED-RUN-'+str(number)+'.json',previous);save('FAILED-JOBS-'+str(number)+'.json',api('actions/runs/'+str(number)+'/jobs'));source_snapshot(previous,'failed-'+str(number))
        failures.append({'id':number,'head_sha':previous['head_sha'],'conclusion':'failure','historical_failure_preserved':True})
    proof={'kind':'actual-single-article-publication-native-observation','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_successful_run':run['id'],'actual_successful_commit':run['head_sha'],'release_id':release['id'],'release_url':release['html_url'],'actual_native_artifact_id':artifact['id'],'exact_native_verification_ZIP_bytes':len(raw),'exact_native_verification_ZIP_sha256':a.zip_sha256,'native_ZIP_CRC_and_exact_JSON_member_passed':True,'actual_immutable_publisher_and_workflow_sources':sources,'earlier_actual_failed_runs':failures,'no_media_copied_generated_or_reclassified_by_record_collector':True}
    save('ACTUAL-NATIVE-PUBLICATION-IDENTITY.json',proof);print(json.dumps(proof,ensure_ascii=False))

if __name__=='__main__':main()
