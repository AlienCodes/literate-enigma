"""Preserve actual native review publication records in both authorized repositories."""
import datetime,hashlib,json
from pathlib import Path
import publish_review as P
H=Path(__file__).resolve().parent
receipt=P.load('NATIVE-RELEASE-VERIFICATION.json')
assert receipt['passed'] and receipt['publisher_execution']['workflow_run_id']==43561024751
launch={'actual_native_attempts':[{'run_id':43560301822,'head_sha':'879960946ebd5e77336479024c07f0731f46868f','conclusion':'failure','actual_reason':'GitHub sanitized all-Chinese upload name to default.pdf; PDF bytes uploaded and verified; renamed without changing bytes.'},{'run_id':43560596586,'head_sha':'10de89f522403bdf44cfe23ea98ebfe82dae9701','conclusion':'failure','actual_reason':'Both attachments uploaded and server-digest verified. Final check incorrectly assumed REST asset listing order; no member identity or content failed.'},{'run_id':43561024751,'head_sha':'eb0ba44d7de481c2f86f86e710ebdf758700a855','conclusion':'success','actual_reason':'Order-independent exact asset inventory check; all native member hashes, CRC, asset digests, public release and frozen tag verified.'}],'actual_success_artifact':{'id':14100655012,'bytes':3151,'sha256':'b2a55aec6471683f2d02f042400d8c2fb7f9f2b192d464ca10864c9b814a239d'},'native_result':receipt,'date_recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
P.save('FINAL-NATIVE-LAUNCH-HISTORY.json',launch)
state=P.load('STATE.json');state.update(published=True,release_url=receipt['release_url'],actual_remote_assets_verified=True,actual_native_run_id=43561024751);P.save('STATE.json',state)
files={}
for name in ['MANIFEST.json','ZIP-IDENTITY.json','streaming-ZIP-transport-check.json','NATIVE-INPUT.json','NATIVE-RELEASE-VERIFICATION.json','NATIVE-DOWNLOAD-IDENTITY.json','FINAL-NATIVE-LAUNCH-HISTORY.json','first50-review-native-verification.zip','native_review.py','publish_review.py','prepare_native.py','start_native.py','archive_completed_review.py','publish-first50-review.yml','first-native-failure.log','second-native-failure.log','publication.log','native-preparation.log','native-launch.log','native-launch-retry.log','STATE.json']:
 p=H/name
 if p.exists():files['completed-review-records/'+name]=p.read_bytes()
files['.github/first50-review/native_review.py']=(H/'native_review.py').read_bytes()
files['.github/first50-review/NATIVE-INPUT.json']=(H/'NATIVE-INPUT.json').read_bytes()
files['.github/workflows/publish-first50-review.yml']=(H/'publish-first50-review.yml').read_bytes()
saved=P.archive_records('completed-native-actual-release-v1',files)
state=P.load('STATE.json');state['verification_archived_in_both']=True;P.save('STATE.json',state)
print(json.dumps({'both_actual_byte_readbacks_passed':saved,'release':receipt['release_url']},ensure_ascii=False),flush=True)
