"""Keep exactly the measured source24/S18 missing ending entry; never edit source/audio.

This external constructor helper is outside the original tools-tree110 enumeration.
Its complete SHA256 is embedded in the stamped shell and declared in certification.
The presence of a case file opts only this one request into strict validation; any
bad opted-in case fails. Other requests stay on the unchanged original constructor.
"""
from pathlib import Path
import ast,hashlib,json,re

MAKER_SHA256='0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
MEASURED_REPORT_SHA256='8b86e718b7ee54f4d0ad20bc658f9dba7f2973090df834d9555fff20473ae54e'
MEASURED_INTAKE_SHA256='b4c730b97083ca577b5d4299ebdfd098fd74726f30d032798908b5bfec493a93'
MEASURED_WAV_SHA256='0bfc44bac414b289ee12dae0fa74a7db64a8b2a33d5d6d2a19ac6161a635aa40'
RAW_FP='e43769675c69'
GAIN=-1.109697858091752
DISPLAY='Precision put six ashore within reach of help and, a century on, brought their ship back into view.'
PROFILE_NAME='reviewed-none-ending24-case.json'
HELPER_NAME='reviewed_none_ending24.py'
REPORT_NAME='reviewed-none-ending24-actual-selected-whole.json'
INTAKE_NAME='reviewed-none-ending24-actual-whole-intake.json'


def require(ok,message):
    if not ok:raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def typed(value):
    if isinstance(value,dict):return('dict',tuple(sorted((k,typed(v))for k,v in value.items())))
    if isinstance(value,list):return('list',tuple(typed(v)for v in value))
    return(type(value).__name__,value)


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def regular(path,label):
    path=Path(path)
    require(path.is_file()and not path.is_symlink(),label+' must be a regular frozen file')
    return path


def no_ending_entry(data,label):
    # Explicit null/empty S18 entries or any other constructed ending are not NONE.
    value=data.get('结尾句',{})
    require(type(value)is dict and not value,label+' must have no constructed ending entry at all')


def sentence_text(sentence):
    return ' '.join(re.sub(r'\*\*','',re.sub(r'\{\{.*?\}\}','',c['en'])).strip()for c in sentence['chunks'])


def validate_source(data,label):
    require(type(data.get('no'))is str and data['no']=='24',label+' is not exact source24')
    require(type(data.get('sentences'))is list and len(data['sentences'])==18,label+' must have exactly18 sentences')
    require(sentence_text(data['sentences'][17])==DISPLAY,label+' S18 full display English differs')
    no_ending_entry(data,label)
    spec={'S18':{'篇号':24,'原文':DISPLAY,'逗号序号':[1]}}
    require(typed(data.get('朗读删逗号'))==typed(spec),label+' exact spoken first-comma case differs')
    require(typed(data.get('分段增益dB'))==typed({'S18':{'2':GAIN}}),label+' must have only measured S18 speech-piece2 gain')
    require(typed(data.get('区间声音指纹',{}).get('S18'))==typed(RAW_FP),label+' S18 measured raw fingerprint differs')
    fields=('非人声区间','词尾除阻','停顿处除阻','除阻加强','停顿删除区间','停顿插入点',
            '句子增益dB','段内渐变dB','分段包络dB','列举逗号','合成标点')
    for field in fields:
        table=data.get(field,{})
        require(type(table)is dict and 'S18'not in table,label+' retains unreviewed target control: '+field)
    require(not any(k.startswith('S18 ')for k in data.get('高亮开始',{})),label+' unreviewed target highlight time')


def original_constants(path):
    regular(path,'Original maker')
    require(digest(path)==MAKER_SHA256,'Original maker/parser/A45/gain bytes differ')
    assignments={}
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name)and target.id in {'SPEED','P_COMMA'}:
                    require(target.id not in assignments,'Ambiguous original '+target.id)
                    assignments[target.id]=ast.literal_eval(node.value)
    require(typed(assignments)==typed({'SPEED':.95,'P_COMMA':.4}),'Original speed/comma-gap constants differ')


def verify(root,tools,work,source_id,keep_ending):
    root,tools,work=Path(root).resolve(),Path(tools).resolve(),Path(work).resolve()
    require(type(source_id)is str and source_id=='24','Only exact source24/S18 is authorized')
    require(keep_ending=='1','Reviewed NONE is only valid inside KEEP_ENDING1 constructor entry')
    require(tools==(root/'视频/工具').resolve(),'Actual ROOT/tools identity differs')
    require(work.is_dir()and(root/'视频/工具').is_dir(),'Actual root/work missing')
    request=root/'.github/video-revision-batch/request/24'
    p=regular(request/PROFILE_NAME,'Reviewed NONE case')
    profile=json.loads(p.read_text())
    require(profile.get('kind')=='source24-S18-reviewed-missing-ending-exact-data-binding','Wrong explicit NONE case kind')
    expected={'source_id':'24','target_sentence':'S18','speed':.95,'comma_gap_seconds':.4,
              'raw_fingerprint':RAW_FP,'manual_gain_dB':{'S18':{'2':GAIN}},
              'expected_ending_state':'missing-entry','actual_measured_whole_report_SHA256':MEASURED_REPORT_SHA256,
              'actual_measured_whole_intake_SHA256':MEASURED_INTAKE_SHA256}
    require(all(typed(profile.get(k))==typed(v)for k,v in expected.items()),'Exact reviewed NONE case fields differ')
    for key in ['immutable_request_SHA256','immutable_target_record_SHA256','canonical_target_record_SHA256']:
        require(type(profile.get(key))is str and re.fullmatch('[0-9a-f]{64}',profile[key]),'Missing exact '+key)
    immutable=regular(request/'视频/脚本/24.json','Immutable request')
    canonical=regular(work/'scripts/24.json','Actual canonical working source')
    require(digest(immutable)==profile['immutable_request_SHA256'],'Immutable request full bytes differ')
    original_constants(tools/'make_video.py');original_constants(work/'make_video.py')
    before=json.loads(immutable.read_text());current=json.loads(canonical.read_text())
    validate_source(before,'Immutable request');validate_source(current,'Actual canonical source')
    require(canonical_digest(before['sentences'][17])==profile['immutable_target_record_SHA256'],'Immutable full S18 record differs')
    require(canonical_digest(current['sentences'][17])==profile['canonical_target_record_SHA256'],'Actual canonical full S18 record differs')
    require(before['title_en']==current['title_en']and
            [sentence_text(s)for s in before['sentences']]==[sentence_text(s)for s in current['sentences']],
            'Canonical English source identity differs from immutable request')
    report_path=regular(request/REPORT_NAME,'Actual measured whole scalar')
    intake_path=regular(request/INTAKE_NAME,'Actual measured whole intake')
    require(digest(report_path)==MEASURED_REPORT_SHA256 and digest(intake_path)==MEASURED_INTAKE_SHA256,'Measured evidence bytes differ')
    report=json.loads(report_path.read_text());intake=json.loads(intake_path.read_text())
    require(report['source_id']=='24'and report['book_order']==49 and report['diagnostic_completed']is True and report['exact_scope_proved']is True,'Actual measured whole scope not complete')
    require(report['actual_master_coefficient_ratio_new_over_old']==1.0 and
            report['all_title_and17_non_target_actual_mastered_WAV_PCM16_exact']is True,'Actual measured master/nontarget scope differs')
    selected=report['phases']['selected_gain_shadow'];target=selected['observed_sentences']['S18']
    require(selected['actual_complete_WAV']['file_sha256']==MEASURED_WAV_SHA256,'Actual reviewed no-ending WAV identity differs')
    require(target['actual_raw_w_fingerprint']==RAW_FP and typed(target['manual_gain_dB'])==typed({'2':GAIN}) and
            target['automatic_gain_dB']=={} and target['actual_grafts']==[] and target['actual_gaps']==[.4],
            'Actual reviewed S18 raw/gain/gap metadata differs')
    require(intake['actual_selected_complete_WAV']['file_sha256']==MEASURED_WAV_SHA256 and
            intake['actual_target_raw_fingerprint']==RAW_FP,'Independent actual whole intake differs')
    return {'kind':'exact-source24-S18-reviewed-missing-ending-constructor-only',
            'source_id':'24','target_sentence':'S18','preserve_missing_ending_entry':True,
            'immutable_request_SHA256':digest(immutable),'actual_canonical_source_SHA256':digest(canonical),
            'actual_profile_SHA256':digest(p),'actual_reviewed_WAV_SHA256':MEASURED_WAV_SHA256,
            'source_or_audio_written':False,'original_speed':.95,'original_comma_gap_seconds':.4,
            'quality_acceptance':False,'all_other_original_gates_required':True}
