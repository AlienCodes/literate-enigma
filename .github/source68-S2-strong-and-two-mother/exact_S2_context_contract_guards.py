"""Pure proposal data/witness assertions only; no tokenizer/model/cache writer entrypoint."""
import copy,hashlib,json,re

def need(ok,message):
    if not ok:raise ValueError(message)

def typed(x):
    if isinstance(x,dict):return('dict',tuple(sorted((k,typed(v))for k,v in x.items())))
    if isinstance(x,list):return('list',tuple(typed(v)for v in x))
    return(type(x).__name__,x)

def validate_data(source_raw,shadow_raw,prior_context_raw,new_context_raw,contract):
    need(contract['source_id']=='68'and contract['target_sentence']=='S2'and contract['book_order']==53,'Exact source68/S2 only')
    for raw,key in [(source_raw,'current_source'),(shadow_raw,'private_shadow'),(prior_context_raw,'old_context'),(new_context_raw,'proposed_context')]:
        need(hashlib.sha256(raw).hexdigest()==contract[key]['sha256']and len(raw)==contract[key]['bytes'],'Wrong frozen role '+key)
    source,shadow,prior,current=map(json.loads,[source_raw,shadow_raw,prior_context_raw,new_context_raw])
    expected=copy.deepcopy(source);need(expected['区间声音指纹'].pop('S2')=='7590b17b3cb1','Wrong current mother retirement');need(typed(expected)==typed(shadow),'Only current S2 mother binding can retire')
    key=contract['projected'];need(key=='Its amenities included a lounge and that year, a grand piano.','Only full projected sentence context allowed')
    need(key not in prior and current[key]==contract['context_row']and contract['context_row']['词']=='and'and contract['context_row']['读音']=='ˈænd','Wrong exact context row')
    rest=copy.deepcopy(current);rest.pop(key);need(typed(rest)==typed(prior),'Old S13 or another context changed')
    at=contract['old_context_insertion_offset'];entry=bytes.fromhex(contract['added_context_bytes_hex']);need(new_context_raw[at:at+len(entry)]==entry and new_context_raw[:at]+new_context_raw[at+len(entry):]==prior_context_raw,'Entire context raw inverse changed')
    display=' '.join(re.sub(r'\*\*|\{\{.*?\}\}','',c['en']).strip()for c in source['sentences'][1]['chunks'])
    need(display==contract['display']=='Its amenities included a lounge and, that year, a grand piano.','Display must keep both commas')
    need(source['朗读删逗号']['S2']=={'篇号':68,'原文':display,'逗号序号':[1]},'Only original firstcomma spoken schema')
    need('and'not in current and current[contract['actual_original_S13_context_key']]==contract['actual_S13_original_context_row'],'No globaland or S13 mutation')
    return {'data_scope_passed':True,'audio_or_quality_acceptance':False}

def validate_preinfer_witness(witness,contract):
    """Future CI must produce this witness directly from real original callbacks before inference."""
    need(witness['source_id']=='68'and witness['target_sentence']=='S2','Wrong actual witness source')
    need(witness['actual_original_post_pron_phones']==contract['expected_phones'],'Actual original phonemes_of did not match; zero model calls permitted')
    rows=witness['actual_original_post_pron_calls'];need(len(rows)==2,'Exactly two original target methods')
    for row,spec in zip(rows,contract['proposed_two_call_contracts']):
        expected={'method':spec['method'],'portable_mid':spec['portable_mid'],'text':spec['expected_post_pron_input'],'voice_sha1':spec['voice_sha1'],'speed':.95,'lang':'en-us','kwargs':spec['kwargs'],'cache_key':spec['deterministic_proposed_key_pending_true_CI_preinfer']}
        need(typed(row)==typed(expected),'Wrong actual phones/model/voice/settings/key witness')
    return {'preinfer_witness_matched':True,'new_mother_or_audio_quality_accepted':False}
