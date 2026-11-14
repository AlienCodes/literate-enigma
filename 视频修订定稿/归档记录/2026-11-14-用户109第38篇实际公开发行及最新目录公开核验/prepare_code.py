from pathlib import Path
import hashlib,json,ast
R=Path(__file__).resolve().parent
base=Path('/workspace/work/bridge-reviewed-4k-v1/publish_single.py').read_text()
prefix=base[:base.index('def validate_config(config):')]
prefix=prefix.replace('book 35', 'book 38').replace("SOURCE_ID = '53'", "SOURCE_ID = '19'").replace("BOOK_ORDER = '35'", "BOOK_ORDER = '38'").replace("TAG = 'bridge-reviewed-4k-v1'", "TAG = 'book38-tulip-mania-final-4k-hold06-v1'").replace("RELEASE_NAME = '35-The-Wind-That-Kept-No-Time-4K.mp4'", "RELEASE_NAME = '38-Tulip-Mania-The-Bubble-and-the-Legend-4K.mp4'")
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('ACCEPTED_AAC =','ACCEPTED_PACKET_CLOCK =','EXPECTED_NATIVE_RUN =')))+'\n'
custom=r'''
TITLE_ZH = '郁金香狂热：泡沫与传说'
TITLE_EN = 'Tulip Mania: The Bubble and the Legend'
REVIEW_ID = '109'
REPOS = {'alienalgorithm/postgraduate-vocabulary', 'AlienCodes/literate-enigma'}

def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()

def _hash(value):
    assert isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)
    return value

def _embedded(config, field, hash_field):
    raw = config[field].encode('utf-8')
    assert _sha256(raw) == _hash(config[hash_field])
    return json.loads(raw)

def validate_config(config):
    assert config['source_id'] == SOURCE_ID and config['book_order'] == BOOK_ORDER
    assert config['user_review_id'] == REVIEW_ID
    assert config['title_zh'] == TITLE_ZH and config['title_en'] == TITLE_EN
    assert config['actual_complete_validation_passed'] is True
    assert config['actual_dual_permanent_archive_passed'] is True
    assert config['actual_new_native_source_full_QA_verified'] is True
    assert config['preview_only'] is False and config['production_delivery_eligible'] is True
    assert type(config['actual_native_source_full_QA_run_id']) is int and config['actual_native_source_full_QA_run_id'] > 0
    assert config['end_reading_pause_seconds'] == .6 and config['nominal_extra_hold_frames_at_30fps'] == 18
    assert .6 <= config['actual_end_reading_pause_seconds'] < .633334
    assert config['tag'] == TAG
    spec = config['video']
    assert spec['release_name'] == RELEASE_NAME
    assert (spec['width'], spec['height']) == (3840, 2160)
    assert type(spec['bytes']) is int and spec['bytes'] > 0
    assert re.fullmatch('[0-9a-f]{40}', spec['archived_commit'])
    _hash(spec['sha256'])
    assert not spec['sha256'].startswith('fb88'), 'The old pending-review source19 video must never be published as user109 final.'
    assert spec['repo_path'].startswith('视频修订定稿/') and '..' not in Path(spec['repo_path']).parts
    assert Path(spec['repo_path']).suffix == '.mp4'
    probe, tail = config['validated_video_probe'], config['validated_tail']
    assert (probe['width'], probe['height'], probe['fps']) == (3840, 2160, '30/1')
    assert probe['frames'] == tail['output_frames']
    assert tail['extra_body_hold_frames'] == 18 and tail['illustration_frames'] == tail['summary_frames'] == 60
    assert tail['speech_end_frame'] == math.ceil(tail['voice_endpoint_seconds'] * 30)
    assert tail['illustration_start_frame'] == tail['speech_end_frame'] + 18 == tail['held_body_end_frame']
    assert tail['summary_start_frame'] == tail['illustration_start_frame'] + 60
    assert tail['output_frames'] == tail['summary_start_frame'] + 60
    assert abs(config['actual_end_reading_pause_seconds'] - (tail['illustration_start_frame']/30 - tail['voice_endpoint_seconds'])) < 1e-8
    _hash(config['accepted_AAC_sha256']); _hash(config['accepted_AAC_packet_projection_sha256'])
    assert type(config['accepted_AAC_packet_count']) is int and config['accepted_AAC_packet_count'] > 0
    assert config['accepted_AAC_packet_clock_preserved'] is True
    expected_roles = {'sourceQA_handoff','normal18_handoff','normal18_record','sourceQA_qc'}
    assert set(config['evidence']) == expected_roles
    for ev in config['evidence'].values():
        assert ev['repo_path'].startswith('视频修订定稿/') and '..' not in Path(ev['repo_path']).parts and ev['repo_path'].endswith('.json')
        assert type(ev['bytes']) is int and 0 < ev['bytes'] <= 2_000_000
        _hash(ev['sha256'])
    assert config['evidence']['normal18_handoff']['sha256'] == _hash(config['validation_handoff_sha256'])
    assert config['evidence']['normal18_record']['sha256'] == _hash(config['validation_record_sha256'])
    proof = _embedded(config, 'actual_dual_byte_proof_utf8', 'actual_dual_byte_proof_sha256')
    assert proof['passed'] is True and len(proof['streams']) == 2
    assert {r['repository'] for r in proof['streams']} == REPOS
    for r in proof['streams']:
        assert r['source_id'] == SOURCE_ID and r['new_id'] == BOOK_ORDER
        assert r['passed'] is True and r['http_status'] == 200
        assert (r['bytes'],r['sha256'],r['pinned_asset_commit'],r['repo_path']) == (spec['bytes'],spec['sha256'],spec['archived_commit'],spec['repo_path'])
    blobs = _embedded(config, 'actual_dual_blob_proof_utf8', 'actual_dual_blob_proof_sha256')
    assert len(blobs['archives']) == 2 and {r['repository'] for r in blobs['archives']} == REPOS
    assert type(config['archive_file_count']) is int and config['archive_file_count'] > 0
    assert blobs['actual_dual_blob_rows'] == 2 * config['archive_file_count']
    for r in blobs['archives']:
        assert r['asset_commit'] == spec['archived_commit'] and r['record_subtree'] == config['archived_video_subtree_sha']
        assert r['files'] == config['archive_file_count'] and r['all_remote_Git_blob_modes_sizes_SHA_exact'] is True
    return spec, probe

def validate_actual_documents(config, docs):
    spec, probe = validate_config(config)
    source, normal, record, qc = (docs[k] for k in ['sourceQA_handoff','normal18_handoff','normal18_record','sourceQA_qc'])
    assert source['status'] == 'passed_actual_native_inline_article_for_permanent_archive'
    assert normal['status'] == 'passed_actual_normal18_post_only_for_permanent_archive'
    assert normal['kind'] == 'actual-new-native-source-QA-then-authorized-normal18-local-tail'
    assert normal['actual_new_source_QA_then_final_normal18_verified'] is True
    assert normal['production_delivery_eligible'] is True and normal['preview_only'] is False
    assert normal['local_postprocessing_only'] is True and normal['new_native_job_or_TTS_claimed'] is False
    assert source['source_run'] == normal['source_run'] == config['actual_native_source_full_QA_run_id']
    assert normal['current_source_validation_handoff']['sha256'] == config['evidence']['sourceQA_handoff']['sha256']
    assert len(source['articles']) == len(normal['articles']) == 1
    for a in [source['articles'][0], normal['articles'][0]]:
        assert a['source_id'] == SOURCE_ID and a['new_id'] == BOOK_ORDER and a['passed_per_article'] is True
    assert source['articles'][0]['section']['qc']['sha256'] == config['evidence']['sourceQA_qc']['sha256']
    final = normal['articles'][0]['final_mp4']
    assert (final['bytes'],final['sha256']) == (spec['bytes'],spec['sha256'])
    assert record['id'] == SOURCE_ID and record['new_id'] == BOOK_ORDER
    assert record['production_delivery_eligible'] is True and record['preview_only'] is False
    assert (record['bytes'],record['sha256']) == (spec['bytes'],spec['sha256'])
    assert record['actual_probe'] == probe and record['tail'] == config['validated_tail']
    assert qc['status'] == 'passed' and type(qc['audio']['repair_applied']) is bool
    assert qc['audio']['repair_applied'] == config['source_native_audio_repair_applied']
    if qc['audio']['repair_applied']:
        assert qc['audio']['controlled_repair']['status'] == 'passed' and qc['audio']['controlled_repair']['actual_new_output'] is True
    audio, lossless = record['actual_audio_chain'], qc['audio']['lossless_copy']
    assert audio['aac_adts_sha256'] == lossless['canonical_aac_adts_sha256'] == config['accepted_AAC_sha256']
    assert audio['packet_projection_sha256'] == lossless['canonical_packet_projection_sha256'] == config['accepted_AAC_packet_projection_sha256']
    assert audio['packet_count'] == lossless['canonical_packet_count'] == config['accepted_AAC_packet_count']

def load_archived_evidence(config):
    result = {}
    for key, ev in config['evidence'].items():
        url = 'https://raw.githubusercontent.com/' + REPO + '/' + config['video']['archived_commit'] + '/' + urllib.parse.quote(ev['repo_path'], safe='/')
        with urllib.request.urlopen(url, timeout=90) as r:
            assert r.status == 200
            raw = r.read(ev['bytes'] + 1)
        assert len(raw) == ev['bytes'] and _sha256(raw) == ev['sha256']
        result[key] = json.loads(raw)
    return result

def build_actual_manifest(handoff_path, ready_path):
    # Local, explicit future operation only; there is no placeholder pass path.
    hp, rp = Path(handoff_path).resolve(), Path(ready_path).resolve()
    normal, ready = json.loads(hp.read_text()), json.loads(rp.read_text())
    assert ready['source_id'] == SOURCE_ID and ready['new_id'] == BOOK_ORDER and ready['passed_per_article'] is True
    assert ready['production_delivery_eligible'] is True and ready['preview_only'] is False
    assert ready['postprocessing_full_V3_handoff_sha256'] == sha(hp)
    assert ready['title_zh'] == TITLE_ZH and ready['title_en'] == TITLE_EN
    a = normal['articles'][0]; vp = Path(a['validated_record']); record = json.loads(vp.read_text())
    sp = Path(normal['current_source_validation_handoff']['path']); source = json.loads(sp.read_text())
    qp = Path(source['articles'][0]['section']['qc']['path']); qc = json.loads(qp.read_text())
    assert sha(sp) == normal['current_source_validation_handoff']['sha256']
    assert sha(qp) == source['articles'][0]['section']['qc']['sha256']
    media = Path(a['final_mp4']['path']); assert media.stat().st_size == ready['bytes'] and sha(media) == ready['sha256']
    metadata = {name: Path(path) for name,path in ready['metadata_files'].items()}
    prepared = json.loads(metadata['prepared-archive.json'].read_text())
    def evidence(path):
        path = Path(path).resolve(); n, h = path.stat().st_size, sha(path)
        matches = [r for r in prepared['material_source_bindings'] if Path(r['original_path']).resolve()==path and r['bytes']==n and r['sha256']==h]
        assert matches, 'Actual proof must already be in the immutable media asset tree.'
        return {'repo_path':matches[0]['repo_path'],'bytes':n,'sha256':h}
    primary = json.loads(metadata['assets-primary.json'].read_text()); backup = json.loads(metadata['assets-backup.json'].read_text())
    assert primary['asset_commit'] == backup['asset_commit'] == ready['asset_commit']
    assert primary['video_tree_sha'] == backup['video_tree_sha'] == ready['video_tree_sha']
    assert primary['files_index'] == backup['files_index']
    pp, bp = metadata['remote-video-byte-verification.json'], metadata['actual-dual-asset-blob-verification.json']
    chain = record['actual_audio_chain']
    config = {'source_id':SOURCE_ID,'book_order':BOOK_ORDER,'user_review_id':REVIEW_ID,'title_zh':TITLE_ZH,'title_en':TITLE_EN,
        'actual_complete_validation_passed':True,'actual_dual_permanent_archive_passed':True,'actual_new_native_source_full_QA_verified':True,
        'actual_native_source_full_QA_run_id':normal['source_run'],'source_native_audio_repair_applied':qc['audio']['repair_applied'],
        'video':{'release_name':RELEASE_NAME,'archived_commit':ready['asset_commit'],'repo_path':ready['video_repo_path'],'bytes':ready['bytes'],'sha256':ready['sha256'],'width':3840,'height':2160},
        'tag':TAG,'title':'考研学人｜第38篇 '+TITLE_ZH+'｜4K定稿（末句停留0.6秒）',
        'body':'第38篇《'+TITLE_ZH+'》审核定稿。最后一句朗读结束后，原正文页保留约0.6秒，再展示原书插图2秒和简述2秒。原始版本与修改、制作及核验记录保留。\n\n记录：https://github.com/'+REPO+'/tree/'+ready['asset_commit'],
        'validation_handoff_sha256':sha(hp),'validation_record_sha256':sha(vp),'validated_video_probe':record['actual_probe'],'validated_tail':record['tail'],
        'accepted_AAC_sha256':chain['aac_adts_sha256'],'accepted_AAC_packet_projection_sha256':chain['packet_projection_sha256'],'accepted_AAC_packet_count':chain['packet_count'],'accepted_AAC_packet_clock_preserved':True,
        'actual_dual_byte_proof_utf8':pp.read_text(),'actual_dual_byte_proof_sha256':sha(pp),'actual_dual_blob_proof_utf8':bp.read_text(),'actual_dual_blob_proof_sha256':sha(bp),
        'archive_file_count':len(primary['files_index']),'archived_video_subtree_sha':ready['video_tree_sha'],
        'evidence':{'sourceQA_handoff':evidence(sp),'normal18_handoff':evidence(hp),'normal18_record':evidence(vp),'sourceQA_qc':evidence(qp)},
        'preview_only':False,'production_delivery_eligible':True,'end_reading_pause_seconds':.6,'nominal_extra_hold_frames_at_30fps':18,
        'actual_end_reading_pause_seconds':record['tail']['voice_to_illustration_gap_seconds'],'old_versions_kept_unchanged':True}
    validate_actual_documents(config,{'sourceQA_handoff':source,'normal18_handoff':normal,'normal18_record':record,'sourceQA_qc':qc})
    return config

'''
main=base[base.index('def main():'):base.index("if __name__ == '__main__':")]
main=main.replace('spec, probe = validate_config(config)','spec, probe = validate_config(config)\n    validate_actual_documents(config, load_archived_evidence(config))')
main=main.replace("Article53 reviewed final hold18", "Article19 reviewed final hold18")
footer='''if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-manifest', action='store_true')
    parser.add_argument('--handoff', type=Path)
    parser.add_argument('--ready', type=Path)
    args = parser.parse_args()
    if args.build_manifest:
        assert args.handoff is not None and args.ready is not None
        config = build_actual_manifest(args.handoff, args.ready)
        output = HERE / 'MANIFEST.json'
        assert not output.exists(), 'Never overwrite a prior actual manifest.'
        output.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\\n')
        print(json.dumps({'manifest':str(output),'sha256':sha(output),'no_remote_mutations':True}))
    else:
        assert args.handoff is None and args.ready is None
        main()
'''
code=prefix+custom+main+footer
ast.parse(code);(R/'publish_single.py').write_text(code)
workflow='''name: Publish reviewed book38 Tulip Mania 4K final
on:
  push:
    branches: [codex/book38-tulip-mania-final-4k-hold06-v1]
    paths: [.github/tulip-mania-release/MANIFEST.json]
  workflow_dispatch:
permissions:
  contents: write
jobs:
  publish:
    if: github.repository == 'alienalgorithm/postgraduate-vocabulary'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Verify sourceQA, actual normal18 proofs and archived bytes; publish one MP4
        run: python -u .github/tulip-mania-release/publish_single.py
        env:
          GH_TOKEN: ${{ github.token }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: book38-tulip-mania-release-verification-${{ github.run_id }}
          path: single-release-output/RELEASE-VERIFICATION.json
          if-no-files-found: warn
          retention-days: 30
'''
(R/'publish-single.yml').write_text(workflow)
profile={'kind':'code-only-pending-user109-source19-book38-singleMP4-review-publisher','source_id':'19','book_order':'38','title_zh':'郁金香狂热：泡沫与传说','title_en':'Tulip Mania: The Bubble and the Legend','tag':'book38-tulip-mania-final-4k-hold06-v1','release_name':'38-Tulip-Mania-The-Bubble-and-the-Legend-4K.mp4','directory':str(R),'branch':'codex/book38-tulip-mania-final-4k-hold06-v1','code_repo_path':'.github/tulip-mania-release/publish_single.py','profile_repo_path':'.github/tulip-mania-release/PUBLICATION-PROFILE.json','manifest_repo_path':'.github/tulip-mania-release/MANIFEST.json','workflow_repo_path':'.github/workflows/publish-book38-tulip-mania-4k-hold06-v1.yml','prepared_code_only':True,'actual_manifest_not_yet_built':True,'actual_new_source_body_audio_and_final_QA_pending':True,'no_media_filled_or_downloaded':True,'old_video_sha_prefix_denied':'fb88','no_manifest_trigger_or_Release_authorized_by_preparation':True,'user109_single_article_download_exception_to_prior079_cloud_only':True,'future_manifest_command':'python publish_single.py --build-manifest --handoff ACTUAL_NORMAL18_H --ready ACTUAL_DUAL_READY','future_required_actual_evidence':['sourceQA_handoff','sourceQA_qc','normal18_handoff','normal18_record','dual full-MP4 HTTP proof','dual complete Git-blob proof'],'native_publish_primary_only':True,'media_transformation_permitted':False,'source_AAC_run_clock_count_not_invented_before_actual_handoff':True,'files':{name:{'bytes':(R/name).stat().st_size,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()} for name in ['publish_single.py','publish-single.yml']}}
(R/'PUBLICATION-PROFILE.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n');assert not (R/'MANIFEST.json').exists()
print(json.dumps({'source_id':'19','book_order':'38','code_only_files':{name:{'bytes':(R/name).stat().st_size,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()} for name in ['publish_single.py','PUBLICATION-PROFILE.json','publish-single.yml']},'actual_manifest_created':False},ensure_ascii=False))
