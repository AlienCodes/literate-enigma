"""Finite source56 onlyS11 exactcontext/real preinfer predicates; no model entrypoint."""
import copy,hashlib,json

def need(x,msg):
 if not x:raise AssertionError(msg)
def typed(x):
 if isinstance(x,dict):return('dict',tuple(sorted((k,typed(v))for k,v in x.items())))
 if isinstance(x,list):return('list',tuple(typed(v)for v in x))
 return(type(x).__name__,x)
def validate_data(source_raw,shadow_raw,prior_raw,current_raw,contract):
 need(hashlib.sha256(source_raw).hexdigest()==contract['source']['sha256'],'Wrong immutable source56dc3')
 need(hashlib.sha256(prior_raw).hexdigest()==contract['old_context']['sha256']and hashlib.sha256(current_raw).hexdigest()==contract['proposed_context']['sha256'],'Wrong immutablecontext')
 source,shadow,prior,current=map(json.loads,[source_raw,shadow_raw,prior_raw,current_raw]);expected=copy.deepcopy(source)
 need(expected['区间声音指纹'].pop('S11')=='5e39565cea68'and typed(expected)==typed(shadow),'Only currentS11 VFP may retire')
 needle=b',\n  "S11": "5e39565cea68"';need(source_raw.count(needle)==1 and source_raw.replace(needle,b'',1)==shadow_raw,'Whole raw inverse must be exact')
 need(str(source['no'])=='56'and len(source['sentences'])==17,'Only source56 17sentences')
 key=contract['projected'];need(key=='The compromise struck without Wallace, may have kept rivalry over precedence at bay.','Wrong exact projected target')
 need(key not in prior and current[key]==contract['context_entry']and current[key]['词']=='Wallace'and current[key]['读音']=='wˈɔːlɪs','Wrong fullsentenceCMU2 context')
 current=copy.deepcopy(current);current.pop(key);need(typed(prior)==typed(current),'Other globalcontext changed')
 need(source['朗读删逗号']['S11']=={'篇号':56,'原文':contract['display'],'逗号序号':[1]},'Exact original firstcomma-only schema')
 return True

def validate_preinfer_witness(witness,contract):
 need(witness['source_id']=='56'and witness['target_sentence']=='S11','Wrong actual source/target')
 need(witness['actual_original_post_pron_phones']==contract['candidate_internal_phonemes']and witness['actual_original_post_pron_phones']!=contract['old_internal_tokenizer_phones'],'Wrong/unchanged actual phones')
 calls=witness['actual_original_post_pron_calls'];need(len(calls)==2,'Exactly2 targetcontracts')
 for row,spec in zip(calls,contract['proposed_two_new_cache_keys_uncreated']):
  mid={'create':'kokoro-v1.0.onnx:7d5df8ecf7d4b187','create_timed':'kokoro-v1.0-timed.onnx:beb0d1848dee9a49'}[spec['method']]
  expected={'method':spec['method'],'portable_mid':mid,'text':contract['candidate_internal_phonemes'],'voice_sha1':contract['actual_original_voice_array_SHA1'],'speed':.95,'lang':'en-us','kwargs':spec['kwargs'],'cache_key':spec['name']}
  need(typed(row)==typed(expected),'Wrong exact method/model/voice/phone/pause/key')
 return True

def validate_old_timed_phone_string(actual_joined,actual_old_tokenizer,contract):
 need(actual_joined==actual_old_tokenizer==contract['old_internal_tokenizer_phones'],'Full existing timed phones do not match actual old internal tokenizer; zero new inference permitted')
 need(actual_joined!=contract['candidate_internal_phonemes'],'Newphones cannot be futile identicalold')
 return True
