"""User090 current video ordering is separate from immutable book/quality IDs."""
from copy import deepcopy
from pathlib import Path
import hashlib,json,re

USER_SHA='3120efc6893981436cb81458ce57f6aca7601edc5e7326cce1388b68de959001'
REQUEST_SHA='84e43d6e9f014deac80b86d9af38d8227f7e33ef7d668d9863ae4aee88a5a214'
CATALOG_SHA='083da8975cd2204e3f8325f48373d04987aac24c7f9b5c40c5a81282e1cdaf9c'
MAP_SHA='1061f215f195290cbee8d6f8630abbf622439b7d7f85b4bb35fc3a439db57b89'
KIND='validated-current-video-order-overlay-user090-v1'
def identity(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read(spec,expected=None):
    raw=Path(spec['path']).read_bytes();sha=hashlib.sha256(raw).hexdigest();assert len(raw)==spec['bytes'] and sha==spec['sha256']
    if expected:assert sha==expected
    return json.loads(raw)
def validate(overlay,catalog=None):
    assert overlay['kind']==KIND and overlay['authority_review_sha256']==USER_SHA
    assert overlay['request_manifest_sha256']==REQUEST_SHA and overlay['frozen_book_catalog_sha256']==CATALOG_SHA
    rows=overlay['video_order'];assert len(rows)==70 and identity(rows)==MAP_SHA
    assert len({r['source_id'] for r in rows})==len({r['frozen_book_order'] for r in rows})==len({r['video_order'] for r in rows})==70
    assert all(r['video_order']==f'{n:02d}' for n,r in enumerate(rows,1))
    assert all(r['video_order']==r['frozen_book_order'] for r in rows[13:])
    if catalog is not None:assert all(catalog[r['source_id']]['new_id']==r['frozen_book_order'] for r in rows)
    a=overlay['initial_order_activation_with_source07_revision'];assert a['source_id']=='07' and a['quality_book_order']=='03' and a['current_video_order']=='01'
    assert re.fullmatch('[0-9a-f]{40}',a['asset_commit']) and re.fullmatch('[0-9a-f]{64}',a['final_video_sha256']) and re.fullmatch('[0-9a-f]{64}',a['full_validation_handoff_sha256'])
    assert type(a['bytes']) is int and a['bytes']>0
    return {r['source_id']:r for r in rows}
def transition(previous,incoming,auth=None):
    old=previous.get('video_order_overlay')
    if old is not None:validate(old)
    request=auth['document'].get('video_order_transition') if auth else None
    if request is None:return deepcopy(old)
    assert old is None,'A later order change requires its own explicit, separately implemented user authority'
    rawuser=read(request['user_review090'],USER_SHA)
    assert rawuser['author']=='user' and rawuser['source_id']=='07' and rawuser['book_order']=='03'
    assert rawuser['execution_state']['new_regeneration_authorized_now_for_source_ids']==['07']
    doc=read(request['requested_order_manifest'],REQUEST_SHA);assert identity(doc['video_order'])==MAP_SHA
    assert doc['current_final_aliases_activated_by_this_record'] is False
    rows=[r for r in incoming if r['source_id']=='07'];assert len(rows)==1;r=rows[0];assert r['new_id']=='03'
    permits=[p for p in auth['document']['authorized_revisions'] if p['source_id']=='07'];assert len(permits)==1
    assert permits[0]['review_record']==request['user_review090']
    spec=request['actual_source07_final_handoff'];h=read(spec)
    assert spec['sha256']==r['postprocessing_full_V3_handoff_sha256']
    assert h['status']=='passed_actual_normal18_post_only_for_permanent_archive' and h['kind']=='actual-new-native-source-QA-then-authorized-normal18-local-tail'
    assert h['actual_new_source_QA_then_final_normal18_verified'] is True and h['production_delivery_eligible'] is True and h['preview_only'] is False
    assert len(h['articles'])==1;i=h['articles'][0];assert i['source_id']=='07' and i['new_id']=='03' and i['passed_per_article'] is True
    assert i['final_mp4']['bytes']==r['bytes'] and i['final_mp4']['sha256']==r['sha256']
    assert r['source_run']==h['source_run'] and r['source_run']!=permits[0]['previous_row']['source_run']
    result={'kind':KIND,'authority_review_sha256':USER_SHA,'request_manifest_sha256':REQUEST_SHA,'frozen_book_catalog_sha256':CATALOG_SHA,'video_order':deepcopy(doc['video_order']),'initial_order_activation_with_source07_revision':{'source_id':'07','quality_book_order':'03','current_video_order':'01','asset_commit':r['asset_commit'],'final_video_sha256':r['sha256'],'bytes':r['bytes'],'full_validation_handoff_sha256':spec['sha256']},'frozen_book_PDF_and_QA_mapping_unchanged':True,'all_subsequent_video_installers_must_preserve_this_order':True}
    validate(result);return result
def validate_transition(previous,current,incoming,auth=None):
    expected=transition(previous,incoming,auth)
    if expected is None:assert 'video_order_overlay' not in current
    else:assert current.get('video_order_overlay')==expected,'Current authorized video order was removed, changed or replaced without authority'
