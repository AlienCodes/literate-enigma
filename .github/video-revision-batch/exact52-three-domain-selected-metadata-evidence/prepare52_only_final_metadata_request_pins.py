"""Data pins only: retain original52 QC/voice/guards, select root-adopted CF pair."""
from pathlib import Path
import ast,copy,difflib,hashlib,json
H=Path(__file__).resolve().parent
B=Path('/dev/shm/source52-final19-CF-and-formal-QC-candidate-20261115/formal-files')
N=Path('/dev/shm/source52-formal43663186058-three-domain-metadata-proposal-20261115')
C=N/'candidate-payload';F=H/'formal-files';F.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());sp=lambda p:{'path':str(p),'bytes':p.stat().st_size,'SHA256':sha(p)}
decision=Path('/workspace/work/root-source52-three-domain-six-A10-plus-S10HL-S14G40-metadata-only-pair-selection-decision.json');assert sha(decision)=='cdb726056a0b94e32631c4bb3a5baa5651a39c1448afbaaa706a3c75313d5483'
src=C/'视频/脚本/52.json';gen=C/'视频/工具/初稿生成/gen52.py';assert sha(src)=='f9e3fa65ddf161a0d7b83e17fe60ac56552535566bf64512ca0f785e21e49862'and sha(gen)=='015ff440b86dac3423da4ca936f2cb91f1752c42dc485b563163285a88251177'
oldsrc=read('/dev/shm/source52-final19-CF-and-formal-QC-candidate-20261115/candidate-payload/视频/脚本/52.json');newsrc=read(src)
assert {k:v for k,v in oldsrc.items()if k!='核对确认'}=={k:v for k,v in newsrc.items()if k!='核对确认'}
assert oldsrc['核对确认']['非人声']==newsrc['核对确认']['非人声']
assert sha(B/'audio52-controlled-qc.py')=='cb04e73b69abfedd8b775e7594cb8f1d51956f2989b02860f343fb137d8b847f'
assert sha(B/'audio52-controlled-qc-reference.json')=='c76df193ca05553b119f3c039e9ce3248b708e2dbad03a74ce724c86e0e1934a'
assert sha(B/'prepare-checker-reference.py')=='1552b63956e5965fa1eeb4eb71c8182db4bf5d13c51851d1165e90988122e152'
assert sha(B/'approved-video-layouts70.json')=='ec6896889ba8594d8892398dd49e90cd37bf9b44786938516075e846af513d33'
for p in B.iterdir():
 if not p.is_file():continue
 if p.name in ['audio52-controlled-qc-reference.json','prepare-checker-reference.py','approved-video-layouts70.json']:continue
 q=F/p.name
 if not q.exists():q.symlink_to(p)
 assert sha(q)==sha(p)
oldref=read(B/'audio52-controlled-qc-reference.json');newref=copy.deepcopy(oldref)
newref['fingerprints']['request_source_sha256']=sha(src);newref['fingerprints']['request_generator_sha256']=sha(gen)
newref['bridge_role_notes']['metadata_request']='Root adopted actual19 lexicalCF97152/GEN6459, then specifically adopted six typed A10 confirmations, S10 onset confirmation and S14 G40 mapped record under cdb726. Final f9e3/015f changes only acoustic-review metadata; all physical controls and voice equal2e49. CurrentGT bytes were not replayed or falsely compared.'
ref=F/'audio52-controlled-qc-reference.json';ref.write_text(json.dumps(newref,ensure_ascii=False,indent=2)+'\n')
strip=copy.deepcopy(newref);strip['fingerprints']['request_source_sha256']=oldref['fingerprints']['request_source_sha256'];strip['fingerprints']['request_generator_sha256']=oldref['fingerprints']['request_generator_sha256'];strip['bridge_role_notes']['metadata_request']=oldref['bridge_role_notes']['metadata_request'];assert strip==oldref
auxold=(B/'prepare-checker-reference.py').read_text();oldpin="'52': '97152c3408e320ddec7acb1cedb426c1ec44e2a3a796ad90aedb4229735f1764'";newpin="'52': '"+sha(src)+"'";assert auxold.count(oldpin)==1
aux=F/'prepare-checker-reference.py';aux.write_text(auxold.replace(oldpin,newpin,1));assert aux.read_text().replace(newpin,oldpin,1)==auxold
manifest=read(B/'approved-video-layouts70.json');nextmanifest=copy.deepcopy(manifest);row=next(q for q in nextmanifest['articles']if q['source_id']=='52');assert row['source_json_sha256']==oldref['fingerprints']['request_source_sha256'];row['source_json_sha256']=sha(src)
# Use the original ordered digest AST. Both review-only keys are excluded by
# the frozen renderer-input contract; no rendering or new visual claim here.
tail=Path('/workspace/work/video-official52-final99d-selected19CF-original-full-native-20261115/.github/video-revision-batch/illustrated_tail.py');tree=ast.parse(tail.read_text());functions=[q for q in tree.body if isinstance(q,ast.FunctionDef)and q.name in ['source_layout_digest','digest_bytes']];ns={'hashlib':hashlib,'json':json,'REVIEW_ONLY_TOP_LEVEL_KEYS':('核对确认','区间声音指纹')};exec(compile(ast.Module(body=functions,type_ignores=[]),'original-layout-digest-AST','exec'),ns)
assert ns['source_layout_digest'](oldsrc)==ns['source_layout_digest'](newsrc)==row['source_layout_structural_sha256']=='5cdb4f3790d336f18673fc12e210899191abcaa0c318c78f7ac924349e1be916'
layout=F/'approved-video-layouts70.json';layout.write_text(json.dumps(nextmanifest,ensure_ascii=False,indent=2)+'\n')
x=copy.deepcopy(nextmanifest);next(q for q in x['articles']if q['source_id']=='52')['source_json_sha256']=oldref['fingerprints']['request_source_sha256'];assert x==manifest
diffs=[]
for name in ['audio52-controlled-qc-reference.json','prepare-checker-reference.py','approved-video-layouts70.json']:
 q=H/('exact-'+name+'.diff');q.write_text(''.join(difflib.unified_diff((B/name).read_text().splitlines(True),(F/name).read_text().splitlines(True),fromfile='root-adopted97152/'+name,tofile='root-selected-f9e3/'+name)));diffs.append(sp(q))
evidence_unchanged=[sp(F/p.name)for p in B.iterdir()if p.name not in ['audio52-controlled-qc-reference.json','prepare-checker-reference.py','approved-video-layouts70.json']and p.is_file()]
proof={'kind':'source52-root-adopted-three-domain-request-data-pins-only-verification','root_selection':sp(decision),'request_source':sp(src),'request_GEN':sp(gen),'MD':sp(C/'新版定稿/52-the-killer-smog-of-1952.md'),'new_reference':sp(ref),'new_aux':sp(aux),'new_layout':sp(layout),'QC_program_unchanged':sp(F/'audio52-controlled-qc.py'),'reference_only_changed_paths':['/fingerprints/request_source_sha256','/fingerprints/request_generator_sha256','/bridge_role_notes/metadata_request'],'aux_only_changed_literal':'sources[52] 97152→f9e3','layout_only_changed_leaf':'articles[source_id52].source_json_sha256 97152→f9e3','source_layout_structural_digest_original_AST_equal':row['source_layout_structural_sha256'],'all_other69_layout_rows_and_all_fonts_RGB_fields_exact':True,'all_other_profile_fields_exact_including_whole_RAW_AAC_FP_15cache_controls_numeric_thresholds':True,'all_legacy_source43_aux_bacc_and_sharedplan_body_exact':True,'all_QC_code_and_numeric_utility_bytes_exact':True,'all_stage0_555_5edf_acb4_physical2e49_evidence_unchanged':evidence_unchanged,'new_audio_GT_whole_model_cache_or_native_executed':False,'new_source_GEN_voice_DSP_or_checker_threshold_mutated':False,'GEN_fullJSON_original_text_0_repair0_after0_report':sp(N/'validation/report.json'),'exact_diffs':diffs}
p=H/'actual-minimal-final-request-pin-verification.json';p.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
payload=H/'candidate-payload'
if not payload.exists():payload.symlink_to(C,target_is_directory=True)
assert sha(payload/'视频/脚本/52.json')==sha(src)
print(json.dumps({'proof':sp(p),'QC':sp(F/'audio52-controlled-qc.py'),'reference':sp(ref),'aux':sp(aux),'layout':sp(layout)}))
