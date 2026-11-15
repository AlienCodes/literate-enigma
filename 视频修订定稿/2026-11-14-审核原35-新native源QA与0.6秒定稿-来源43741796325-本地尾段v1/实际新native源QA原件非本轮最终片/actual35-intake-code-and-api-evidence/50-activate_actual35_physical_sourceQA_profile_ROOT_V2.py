"""Late-bind only actual source35 native ZIP members to the approved V2 IO entry."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parent;C=R/'source-consumer-code'
A=Path('/workspace/work/review35-native/43741796325/35/artifact-files')
sys.path.insert(0,str(C))
import delivery as D
import exact_formal_new35 as F
def sp(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
pending=C/'actual35-bound-source-profile-PENDING.json';p=json.loads(pending.read_text())
status=A/'35-status.json';s=json.loads(status.read_text());aux=F.P['pins']['formal_main_stdout_aux_not_ART_member']
assert sp(status)['sha256']==aux['sha256'] and sp(status)['bytes']==aux['bytes']
assert s==json.loads(Path(aux['path']).read_text())
F.metadata(D.require);F.native_fields(s,'35',D.require)
assert s['accepted_prior_aac_identical']is False and s['original_maker_unchanged']is False
assert p['article']=='35'and p['book_order']=='54'and p['profile_frozen']is False
assert p['request_source_sha256']==s['request_source_sha256']==F.P['request_source_sha256']
coll=json.loads((A/'35-actual-source-collection.json').read_text())
assert coll==s['actual_source_collection']and coll['generator_execution_observed']is False
roles={}
for role,record in coll['files'].items():
 found=list(A.rglob(record['file']));assert len(found)==1
 observed=sp(found[0]);assert observed['sha256']==record['sha256'];roles[role]=observed
assert roles['request_json']['sha256']=='d54e02ff7c013821e3a86785b98867e27ab1892e4042852637ca36a2ac06bbe7'
assert roles['request_generator']['sha256']=='19e7fe869c4b2b7a8f85b04249890109504cd94d736dc723846fbf91070df121'
assert len(p['mandatory_evidence'])==44
for row in p['mandatory_evidence']:assert sp(row['path'])==row
intake=R/'ACTUAL-UNIQUE-WHOLE-SHA-CRC-SAFE-PATH-EXPANDED-BUDGET-INTAKE.json'
proof=json.loads(intake.read_text());assert proof['all_member_CRC_path_regularfile_and_duplicate_guards_passed']is True
archive=A.parent/'article35-passed-output.zip';assert proof['immutable_ZIP']==sp(archive)
assert sp(archive)['bytes']==47964978 and sp(archive)['sha256']=='12d1791d3095652e378b17cccf7cdce75ac12d6313ec36d93f84b1930ab29d29'
p.update(kind='actual-acquired-source35-ROOT-adopted-V2-native-quality-and-diagnostic-S15-scope-physical-sourceQA-profile',profile_frozen=True,actual_physical_ZIP_not_downloaded=False,zip=sp(archive),actual_status=sp(status),observed_source_files=roles)
p['mandatory_evidence']+=[sp(intake),sp(R/'PARENT-CONCRETE-ROOT-ADOPTED35-V2-ORIGINAL-HOST-LANE-CODE-ADOPTION.json'),sp(R/'PARENT-INDEPENDENT-ALL-H-FREEZE-SPECS-AND-ORIGINAL35-PURE-METADATA-REPLAY.json'),sp(Path(__file__))]
dest=C/'actual35-bound-source-profile.json';assert not dest.exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
observed={'kind':'actual35-physical-immutable-ART-to-ROOT-adopted-V2-sourceQA-profile-activation-not-new-quality-acceptance','actual_main_status':sp(status),'stdout_aux_separate_and_whole_bytes_equal':aux,'actual_source_collection_roles':roles,'selected_profile':sp(dest),'ROOT_specific_V2_adoption_SHA256':'4d8ded89f8a19b2876fe5471eb78df609c098c10b28d245c40fb15863cb46d2d','actual_native_original_quality_is_true_diagnostic_scope_and_identity_are_not_quality':True,'actual_legacyAAC_identical':False,'actual_original_maker_unchanged':False,'actual_top_book_order_key_present':'book_order'in s,'actual_top_book_order_value':s.get('book_order'),'no_runtime_book_order_added':True,'no_sourceQA_or_normal18_pass_claimed_before_original_entries':True}
h=R/'ACTUAL-SOURCE35-PHYSICAL-INTAKE-TO-ROOT-V2-SOURCEQA-PROFILE-ACTIVATION-RECORD.json';h.write_text(json.dumps(observed,ensure_ascii=False,indent=2)+'\n');print(json.dumps(sp(h)))
