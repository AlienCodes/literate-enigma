from pathlib import Path
import json,os,subprocess,sys
sys.path.insert(0,'/dev/shm/native-inline-engine-reviewed60-v20-077-layout')
import delivery as D
from derive_final_generator import derive
O=Path(__file__).parent;W=Path('/dev/shm/book39-source29-user110-hold06-20261114');prior=Path('/workspace/work/video-revision-delivery/next-passed-validated/43532011110/29/archive-handoff.json');h=D.load(prior);cfg=D.load(h['input_path']);item=h['articles'][0]['section'];reqroot=Path(cfg['request_source_root']);finroot=Path(cfg['final_source_root']);a=item['request_source'];b=item['final_source']
for src,root in ((a,reqroot),(b,finroot)):
 for kind,s in src.items():D.checked_file(s,root)
asked=D.load(reqroot/a['json']['path']);final=D.load(finroot/b['json']['path']);invariants=D.source_invariants(asked,final,'29');md=D.markdown_prose_equivalence((reqroot/a['md']['path']).read_text(),(finroot/b['md']['path']).read_text(),asked,final,'29',D.visible_tokens,D.require)
proof=derive(finroot/b['json']['path'],reqroot/a['json']['path'],reqroot/a['gen']['path'],reqroot/a['md']['path'],'/workspace/work/video-audit70-20261113/next-passed-native/43532011110/29/files/29-status.json',cfg['source_derivation']['original_tools_root'],cfg['source_derivation']['factory']['path'],O/'fresh-source-rederivation')
D.require(proof['derived_generator_sha256']==b['gen']['sha256'] and proof['whole_JSON_roundtrip_exact'] is True,'Fresh full-JSON regeneration differs from prior exact derivedGEN')
D.write(O/'actual-current29-source-GEN-MD-full-invariance-and-roundtrip-proof.json',dict(kind='fresh-existing-source29-request-final-GEN-MD-identity-and-original-helper-roundtrip',source_id='29',book_order='39',original_native_run=43532011110,original_existing_fullV3_sha256=D.digest(prior),request_sources=a,actual_validated_final_sources=b,current_source_file_same_as_validated_final_json=D.digest('/workspace/work/video-audit70-20261113/next-passed-native/43532011110/29/files/29-source.json')==b['json']['sha256'],source_invariants=invariants,markdown_prose_equivalence=md,fresh_original_helper_derivation=proof,existing_full_original_acoustic_QA_not_rerun=True,new_native_source_GEN_execution_or_observed_MD_not_claimed=True,unchanged_actual_helper_JSON_roundtrip=True))
r=D.load(W/'ready-book39-source29.json');args=['/workspace/work/video-venv/bin/python',str(O/'code/validate_single_article_post_only.py'),'--upstream-record',str(O/'29-upstream-with-exact-existing-full-V3-reference.json'),'--tail-report',r['actual_raw_tail_report'],'--mp4',r['actual_final_MP4'],'--boundary-review',str(O/'actual-five-boundary-visual-review.json'),'--output',str(O/'validated/29')]
with (O/'finalize110.log').open('w') as log:p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(exit_code=p.returncode,source_proof=str(O/'actual-current29-source-GEN-MD-full-invariance-and-roundtrip-proof.json'),log=str(O/'finalize110.log'))));raise SystemExit(p.returncode)
