"""Local DATA overlay for an already accepted voice chosen by a new pure review.

No quality gate, source, media or repository mutation occurs. This preserves
the historical 70-row catalog and replaces one row with the real previously
V3-passed public MP4 actually declared as accepted by the new native status.
The unchanged V3 validator still compares all current AAC and packet clocks.
"""
import argparse, copy, hashlib, json, shutil
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def spec(path):
    p=Path(path);return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':digest(p)}

def main(a):
    n=a.article.zfill(2);root=Path(a.native_root);out=Path(a.output_root)
    status=json.loads((root/'files'/f'{n}-status.json').read_text())
    handpath=Path(a.prior_handoff);hand=json.loads(handpath.read_text())
    candidates=[r for r in hand['articles']if r['source_id']==n]
    assert len(candidates)==1 and candidates[0]['passed_per_article']is True
    prior=candidates[0]['final_mp4'];path=Path(prior['path'])
    assert digest(path)==prior['sha256'] and path.stat().st_size==prior['bytes']
    assert status['passed']is True and status['canonical_pipeline_passed']is True
    assert status['accepted_prior_aac_identical']is True
    assert status['accepted_source']['sha256']==prior['sha256']
    assert status['canonical_aac_adts_sha256']==status['accepted_source']['aac_adts_sha256']
    template=Path(a.frozen_primary);folder=out/'frozen-primary';folder.mkdir(exist_ok=True)
    for name in ('来源视频清单.json','篇号对照.json'):
        target=folder/name
        if not target.exists():shutil.copyfile(template/name,target)
    catalogpath=folder/'来源视频清单.json'
    historical=folder/('来源视频清单.historical-before-latest'+n+'-review.json')
    if not historical.exists():shutil.copyfile(catalogpath,historical)
    catalog=json.loads(historical.read_text())
    selected=[row for row in catalog['videos']if row['id']==n];assert len(selected)==1
    row=selected[0];before=copy.deepcopy(row)
    git=hashlib.sha1(b'blob '+str(path.stat().st_size).encode()+b'\0')
    with path.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):git.update(b)
    row.update(sha256=prior['sha256'],bytes=prior['bytes'],git_blob_sha=git.hexdigest())
    catalog['actual_latest_accepted_review_overlay']={
        'source_id':n,'prior_handoff_sha256':digest(handpath),'prior_run_id':hand['source_run']}
    proof={'kind':'actual_latest_previously_accepted_audio_baseline_catalog_DATA_overlay',
           'source_id':n,'original_catalog':spec(historical),'before_row':before,
           'after_row':row,'actual_previously_V3_passed_handoff':spec(handpath),
           'latest_accepted_public_MP4':prior,'new_native_status':spec(root/'files'/f'{n}-status.json'),
           'policy':'Pure user text review uses the actual latest already accepted voice. Original AAC and absolute packet timing identity validation remains unchanged; no new repair is claimed.',
           'remaining_69_rows_and_all_70_order_paths_unchanged':True,
           'audio_quality_program_or_threshold_changed':False,
           'script':spec(Path(__file__))}
    catalogpath.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    proofpath=out/f'actual-latest-accepted{n}-catalog-data-overlay.json'
    proofpath.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    contextpath=root/'inline-adapter-context.json';context=json.loads(contextpath.read_text())
    extra=context['extra_evidence_local_files']
    for p in (proofpath,historical,handpath,Path(__file__)):
        if str(p.resolve())not in extra:extra.append(str(p.resolve()))
    contextpath.write_text(json.dumps(context,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'article':n,'catalog':spec(catalogpath),'proof':spec(proofpath),
                      'new_media_quality_pass_claimed':False},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('article','native-root','output-root','prior-handoff','frozen-primary'):
        p.add_argument('--'+key,required=True)
    main(p.parse_args())
