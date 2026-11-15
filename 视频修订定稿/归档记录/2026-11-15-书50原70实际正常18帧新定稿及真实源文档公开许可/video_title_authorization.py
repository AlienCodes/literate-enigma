"""Exact user077 video-only Chinese title authority; no book/catalog/PDF edits."""
from pathlib import Path
import hashlib,json,re

USER_SHA='b773f84cd2f93eb38b312869cf0696ee9382d427f8965c3c4ed9875f5db1556a'
OLD='改变世界的科学巨匠'
NEW='爱因斯坦的诺奖之路'
EN='The Scientific Giant Who Changed the World'
KIND='explicit-user077-source60-book36-video-only-title'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(spec):
    raw=Path(spec['path']).read_bytes();assert len(raw)==spec['bytes'] and digest(raw)==spec['sha256'];return raw
def user(spec):
    raw=read(spec);assert digest(raw)==USER_SHA;d=json.loads(raw)
    assert d['author']=='user' and d['source_id']=='60' and d['book_order']=='36'
    assert d['approved_Chinese_title']==NEW and d['title_en']==EN
    assert d['execution_state']['review_collection_complete_for_this_article'] is True
    assert d['execution_state']['new_regeneration_authorized_now_for_source_ids']==['60']
    return d
def actual_file(spec,source_h):
    rows=[r for r in source_h['validation_files'] if r.get('bytes')==spec['bytes'] and r.get('sha256')==spec['sha256']]
    assert rows,'Actual native working source must be retained in the real source QA handoff'
    return read(rows[0])
def build(h,book,user_spec):
    user(user_spec)
    assert book['source_id']=='60' and book['new_id']=='36' and book['title_zh']==OLD and book['title_en']==EN
    assert h['status']=='passed_actual_normal18_post_only_for_permanent_archive' and h['kind']=='actual-new-native-source-QA-then-authorized-normal18-local-tail'
    assert h['actual_new_source_QA_then_final_normal18_verified'] is True and h['production_delivery_eligible'] is True and h['preview_only'] is False
    source_spec=h['current_source_validation_handoff'];source=json.loads(read(source_spec))
    assert source['status']=='passed_actual_native_inline_article_for_permanent_archive' and source['source_run']==h['source_run']
    assert len(source['articles'])==1;item=source['articles'][0]
    assert item['source_id']=='60' and item['new_id']=='36' and item['passed_per_article'] is True
    pair=item['section']['final_source'];data=json.loads(actual_file(pair['json'],source));md=actual_file(pair['md'],source).decode()
    assert data['title_zh']==NEW and data['title_en']==EN
    assert md.splitlines()[:2]==['# EN: '+EN,'# ZH: '+NEW]
    return {'kind':KIND,'source_id':'60','new_id':'36','original_book_catalog_title_zh':OLD,'approved_video_title_zh':NEW,'unchanged_title_en':EN,'user_review077_sha256':USER_SHA,'actual_source_QA_handoff_sha256':source_spec['sha256'],'actual_source_JSON_sha256':pair['json']['sha256'],'actual_working_MD_sha256':pair['md']['sha256'],'actual_titles_verified_from_passed_native_sources':True,'frozen_book_catalog_or_PDF_changed':False}
def accepted(row,catalog):
    assert catalog=={'new_id':'36','title_zh':OLD}
    assert row['source_id']=='60' and row['new_id']=='36' and row['title_zh']==NEW and row['title_en']==EN
    assert row['passed_per_article'] is True and row['production_delivery_eligible'] is True and row['preview_only'] is False
    a=row['video_title_authorization']
    assert a['kind']==KIND and a['source_id']=='60' and a['new_id']=='36'
    assert a['original_book_catalog_title_zh']==OLD and a['approved_video_title_zh']==NEW and a['unchanged_title_en']==EN
    assert a['user_review077_sha256']==USER_SHA and a['actual_titles_verified_from_passed_native_sources'] is True and a['frozen_book_catalog_or_PDF_changed'] is False
    assert a['actual_source_QA_handoff_sha256']==row['actual_new_native_source_QA_handoff']['sha256']
    assert a['actual_source_JSON_sha256']==row['actual_native_working_source_JSON_sha256'] and a['actual_working_MD_sha256']==row['actual_native_working_MD_sha256']
    assert all(re.fullmatch('[0-9a-f]{64}',a[k]) for k in ['actual_source_QA_handoff_sha256','actual_source_JSON_sha256','actual_working_MD_sha256'])
    return True
def check_revision(old,current,permit):
    assert old['source_id']=='60' and old['new_id']=='36' and old['title_zh']==OLD
    user(permit['review_record']);spec=permit['actual_new_title_handoff'];h=json.loads(read(spec))
    assert spec['sha256']==current['postprocessing_full_V3_handoff_sha256']
    assert current['video_title_authorization']==build(h,{'source_id':'60','new_id':'36','title_zh':OLD,'title_en':EN},permit['review_record'])
    return accepted(current,{'new_id':'36','title_zh':OLD})
