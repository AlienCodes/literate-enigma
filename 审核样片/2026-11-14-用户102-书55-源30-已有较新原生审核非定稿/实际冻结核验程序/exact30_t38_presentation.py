"""Exact parent-approved existing30 T38 presentation reconciliation only.
Never edits request/final/MD/GEN/media, and never treats fierce heat as adj.
The original unchanged function explains actual historical presentation;
every original source invariant still runs on the virtual request.
"""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
REQUEST='5b112d51b050819a46545bd33106c405df59fb476a372b4b8eccbc447b8115f5'
ACTUAL='6f8dad6491a5e33827bcd1317048b721d60242bfa44e14e5d288770ef6e0e96a'
def structure(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def virtual_original_T38_request(request,actual,article):
 from delivery import require,digest,changed_json_paths
 require(str(article).zfill(2)=='30' and structure(request)==REQUEST and structure(actual)==ACTUAL,'Exact approved30 full request/actual structure pair required')
 folder=HERE/'original-T38-frozen';pins=json.loads((HERE/'exact30-original-program-and-request-MD-pins.json').read_text())
 for name,sha in pins.items():require(digest(folder/name)==sha,'Original frozen T38 dependency/requestMD differs: '+name)
 require(pins['修.py']=='1a6662012752c2d2152d87e1690f1dbb1fd2ced583455a365c022b8b91bdd34d','Original immutable T38 program differs')
 require(digest(HERE/'root-source30-specific-T38-exact-review-decision.json')=='497b9e023d647515aa8aef89afe549fb64ae4528986ffec0b3767b01db7b70e3','Exact parent implementation decision differs')
 sys.path.insert(0,str(folder))
 spec=importlib.util.spec_from_file_location('review102_exact30_original_T38',folder/'修.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
 virtual=copy.deepcopy(request);selected=original.形容词((folder/'30-request-manuscript.md').read_text());report=original.的并进(virtual,selected)
 expected=['/sentences/0/chunks/0/align/1/1','/sentences/0/chunks/0/align/2/1','/sentences/0/chunks/0/zh']
 require(sorted(changed_json_paths(request,virtual))==expected and virtual['sentences'][0]['chunks'][0]==actual['sentences'][0]['chunks'][0],'Original exact T38 did not reproduce approved existing presentation')
 return virtual,dict(kind='specific-existing30-original-T38-virtual-request-reconciliation',request_structure_sha256=REQUEST,actual_structure_sha256=ACTUAL,original_T38_program_sha256=pins['修.py'],original_T38_report=report,only_changed_paths=expected,original_inputs_mutated=False,fierce_heat_word_class='noun phrase headed by heat; inherited historical adj. glossary tag is not endorsed',original_source_guards_required=True)
