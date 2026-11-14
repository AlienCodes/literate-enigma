#!/usr/bin/env python3
"""Freeze an honestly derived GEN from actual final JSON using the unchanged helper.

This does not claim that this new GEN was executed in the original render job.
It never writes the repository or the original working JSON.
"""
import argparse, importlib.util, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from delivery import digest, write, require, source_invariants, changed_json_paths
import preview28_contract as P28


def derive(final_json, request_json, request_gen, request_md, native_status, tools_root, factory, output):
    paths=[Path(v).resolve()for v in (final_json,request_json,request_gen,request_md,native_status,tools_root,factory)]
    actual,request,old_gen,manuscript,status_path,tools,factory=paths
    out=Path(output).resolve();require(not out.exists(),'Derived output directory must be fresh')
    before={str(p):digest(p)for p in paths if p.is_file()}
    final=json.loads(actual.read_text());asked=json.loads(request.read_text());native=json.loads(status_path.read_text());n=str(final['no']).zfill(2)
    if P28.is_preview(native):
        P28.main_status(native,n)
    else:
        require(native['passed']is True and native['stage']=='final4K-passed'and native['article']==n,'Only actual successful producer source may be frozen')
    expected=native['request_source_sha256']
    require(expected[f'视频/脚本/{n}.json']==digest(request)and expected[f'视频/工具/初稿生成/gen{n}.py']==digest(old_gen)and expected['新版定稿/'+manuscript.name]==digest(manuscript),'Request JSON/GEN/MD differ from immutable producer-request fingerprints')
    semantic=source_invariants(asked,final,n)
    module=importlib.util.spec_from_file_location('original_pure_data_encoder',factory);encoder=importlib.util.module_from_spec(module);module.loader.exec_module(encoder)
    text,issues=encoder.pure_generator(final);require(text is not None and not issues,'Original helper cannot represent actual final JSON exactly: '+str(issues))
    out.mkdir(parents=True)
    helpers={}
    with tempfile.TemporaryDirectory(prefix='derived-gen-exact-')as temp:
        root=Path(temp)/'mirror';g=root/'视频/工具/初稿生成';g.mkdir(parents=True)
        for rel in ('初稿生成/核对.py','重点词被去掉.py'):
            src=tools/rel;dest=root/'视频/工具'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);helpers[rel]=digest(src)
        md=root/'新版定稿'/manuscript.name;md.parent.mkdir(parents=True);shutil.copyfile(manuscript,md)
        # Preserve the unchanged helper's real focus-removal advisory if present.
        removal=tools.parent/'制作记录/重点词被去掉.json'
        if removal.exists():
            dst=root/'视频/制作记录/重点词被去掉.json';dst.parent.mkdir(parents=True);shutil.copyfile(removal,dst)
        candidate=g/f'gen{n}.py';candidate.write_text(text)
        work=Path(temp)/'work';(work/'scripts').mkdir(parents=True)
        process=subprocess.run([sys.executable,str(candidate)],cwd=work,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
        (out/'original-helper-roundtrip.log').write_text(process.stdout+process.stderr)
        generated=work/f'scripts/{n}.json'
        require(process.returncode==0 and generated.is_file()and json.loads(generated.read_text())==final,'Actual unchanged-helper complete JSON roundtrip failed')
        require(all(digest(tools/rel)==sha for rel,sha in helpers.items()),'Original helpers changed during derivation')
        shutil.copyfile(candidate,out/f'gen{n}.py');shutil.copyfile(generated,out/f'{n}-roundtrip.json')
    require(all(digest(Path(p))==sha for p,sha in before.items()),'Original input changed during derivation')
    proof={'status':'passed','article':n,'origin':'derived_after_final_QC','actual_original_job_execution_claimed':False,'used_generator_observation':'not_exported_by_original_producer','source_json_sha256':digest(actual),'derived_generator_sha256':digest(out/f'gen{n}.py'),'request_json_sha256':digest(request),'request_generator_sha256':digest(old_gen),'request_manuscript_sha256':digest(manuscript),'immutable_native_status_sha256':digest(status_path),'factory_program_sha256':digest(factory),'original_helper_sha256':helpers,'original_helper_exit':process.returncode,'whole_JSON_roundtrip_exact':True,'semantic_control_invariants':semantic,'changed_paths':changed_json_paths(asked,final),'original_inputs_unchanged':True,'manuscript_origin':'request_manuscript_with_verified_final_source_equivalence','manuscript_runtime_observed':False,'no_repository_or_remote_write':True,'scope':'data fidelity and regeneration only; final JSON artifact-member origin must additionally be checked by delivery validation/archive','final_JSON_artifact_origin_checked_here':False}
    collection=native.get('actual_source_collection')
    if collection:
        proof.update({'used_generator_observation':'exported_actual_production_file; execution observation is a separate original fact','observed_used_generator':collection['files']['used_generator'],'original_production_generator_execution_observed':collection['generator_execution_observed'],'original_production_generator_execution_evidence':collection['generator_execution_evidence'],'actual_production_manuscript':collection['files']['actual_working_manuscript'],'manuscript_runtime_observed':True,'manuscript_origin':'immutable request used for roundtrip; actual exported production manuscript recorded separately','derived_generator_original_job_execution_claimed':False})
    if P28.is_preview(native):
        proof.update(preview_only=True,production_delivery_eligible=False,final_user_acceptance=False)
    write(out/'derived-source-proof.json',proof)
    return proof


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('final-json','request-json','request-gen','request-md','native-status','tools-root','factory','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(derive(a.final_json,a.request_json,a.request_gen,a.request_md,a.native_status,a.tools_root,a.factory,a.output),ensure_ascii=False))
