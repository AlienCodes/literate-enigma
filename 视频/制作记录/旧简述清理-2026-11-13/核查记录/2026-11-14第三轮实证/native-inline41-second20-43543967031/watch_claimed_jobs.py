"""Metadata-only60-second observer; exits when one claimed article newly completes."""
import importlib.util,json,sys,time
from pathlib import Path
O=Path(__file__).resolve().parent
V=Path('/workspace/work/video-revision-delivery');sys.path.insert(0,str(V))
from observe_native_runs import observe
last=None
for turn in range(90):
    state=json.loads((O/'claimed-state.json').read_text())
    known=set(state['ingested_and_handed_off'])|set(state['native_failed_not_ingested'])|set(state.get('downloaded_passed_pending_ingest',[]))|set(state.get('successful_native_artifacts_awaiting_download',[]))
    claimed=set(state['claimed_source_ids'])
    result=observe([43543967031],O/'latest-native-observation.json')
    completed=result['runs'][0]['completed_producer_jobs']
    fresh=[row for row in completed if row['name'].removeprefix('produce (').removesuffix(')')in claimed-known]
    if fresh:
        print(json.dumps({'newly_completed_claimed_jobs':fresh,
            'successful_artifacts':[r for r in result['successful_job_artifacts_to_inspect']if r['article']in claimed-known]},ensure_ascii=False),flush=True)
        break
    summary=result['runs'][0]['job_state_counts']
    if summary!=last:print(json.dumps({'waiting_native_jobs':True,'whole_matrix_states':summary,'observation':str(O/'latest-native-observation.json')},ensure_ascii=False),flush=True);last=summary
    time.sleep(60)
else:print('Metadata observation period ended; no quality verdict inferred.',flush=True)
