"""Exact existing issued-reference and genuine consent data. No quality rule changes."""
from pathlib import Path
import json,hashlib,copy
CONTRACT = {'source_id': '24', 'request_source_SHA256': '34afbcb1e517c10db4ebb963bbf59615b1c5cf439fee5156e85b14717f7edb13', 'actual_current_final_authorization_SHA256': '0925d1dfa243b9a37b6e9fdfe9855836f1c22fdcdffdf2196d3387e7bb7c34a4', 'original_fc0b_issued_SHA256': '186698a05b8eb2914eef1998e54ee3a39c897c1a47afc35ca2dafe4563d7f0d7', 'actual_accepted_reference_SHA256': 'c8903792176bbbe068af89d4826bfe19376f71bc61a121b065539644caafd834', 'feedback_SHA256': None, 'feedback_count': 0}
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def install(request, root, tools, actual_source_id):
    request, root, tools = Path(request), Path(root), Path(tools)
    assert actual_source_id == CONTRACT['source_id'], 'Wrong original text-role source'
    assert root.is_dir() and tools.resolve() == (root/'视频/工具').resolve(), 'Wrong actual ROOT/tools role'
    no = CONTRACT['source_id']
    assert (request/f'视频/脚本/{no}.json').is_file()
    assert digest(request/f'视频/脚本/{no}.json') == CONTRACT['request_source_SHA256'], 'Wrong selected request source'
    assert digest(root/f'视频/脚本/{no}.json') == CONTRACT['request_source_SHA256'], 'Runtime body differs from installed request'
    assert digest(request/'user-authorization.json') == CONTRACT['actual_current_final_authorization_SHA256'], 'Wrong actual final row'
    authorization = json.loads((request/'user-authorization.json').read_text())
    assert authorization['篇'] == no and authorization['原话'].strip()
    source = request/f'checker-reference/视频/脚本/已发版本/{no}.json'
    assert source.is_file() and not source.is_symlink(), 'Missing regular accepted issued-reference input'
    assert digest(source) == CONTRACT['actual_accepted_reference_SHA256'], 'Wrong accepted issued-reference data'
    accepted = json.loads(source.read_text())
    assert str(accepted['no']) == no
    destination = root/f'视频/脚本/已发版本/{no}.json'
    assert destination.is_file() and not destination.is_symlink(), 'Original issued-reference role must exist'
    assert destination.resolve().is_relative_to(root.resolve()), 'Issued reference escapes actual ROOT'
    previous = digest(destination)
    assert previous in [CONTRACT['original_fc0b_issued_SHA256'], CONTRACT['actual_accepted_reference_SHA256']], 'Unreviewed issued-reference bytes'
    agreement = tools/'用户同意记录.json'
    records = json.loads(agreement.read_text())
    before = copy.deepcopy(records)
    assert type(records.get('记录')) is list and authorization in records['记录'], 'Original final-row ABI must run first'
    appended = []
    if CONTRACT['feedback_count']:
        feedback = request/'user-feedback-authority-rows.json'
        assert feedback.is_file() and digest(feedback) == CONTRACT['feedback_SHA256'], 'Wrong actual feedback row list'
        rows = json.loads(feedback.read_text())
        assert type(rows) is dict and set(rows) == {'记录', 'role'} and type(rows['role']) is str and type(rows['记录']) is list
        assert len(rows['记录']) == CONTRACT['feedback_count']
        for row in rows['记录']:
            assert type(row) is dict and row.get('篇') == no and row.get('原话','').strip() and row != authorization
            if row not in records['记录']:
                records['记录'].append(copy.deepcopy(row)); appended.append(row)
    assert {k:v for k,v in before.items() if k!='记录'} == {k:v for k,v in records.items() if k!='记录'}
    assert records['记录'][:len(before['记录'])] == before['记录'], 'Original registry rows/order must remain'
    # All input and prior-role validations finish before these two data writes.
    if appended:
        agreement.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    destination.write_bytes(source.read_bytes())
    assert digest(destination) == CONTRACT['actual_accepted_reference_SHA256']
    after = json.loads(agreement.read_text())
    assert after == records
    return {'source_id':no,'only_existing_checker_data_roles_prepared':True,
            'previous_issued_source_SHA256':previous,'actual_accepted_issued_source_SHA256':digest(destination),
            'actual_selected_source_SHA256':CONTRACT['request_source_SHA256'],
            'appended_exact_actual_feedback_rows':len(appended),'all_prior_registry_rows_and_top_fields_exact':True,
            'original_current_final_row_preserved':True,'audio_or_video_quality_acceptance':False,
            'quality_checker_maker_threshold_or_model_changed':False}
