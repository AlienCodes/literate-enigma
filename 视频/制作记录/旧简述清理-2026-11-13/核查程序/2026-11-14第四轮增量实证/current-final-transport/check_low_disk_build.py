"""Offline transport contract check; fixtures are not actual videos or a publication."""
import io,json,tempfile
from pathlib import Path
from unittest.mock import patch
import release_actions as R
from test_v3 import Native71BuildPublish
with tempfile.TemporaryDirectory() as td:
    root=Path(td)/'root';root.mkdir();out=Path(td)/'out'
    _,pdf,raw,streams,plan=Native71BuildPublish().fixture(root)
    def open_url(url,**kw):return io.BytesIO(streams[R.urllib.parse.unquote(url).split('/'+pdf['pinned_commit']+'/',1)[1]])
    with patch.object(R,'api',return_value={'status':'ahead'}),patch.object(R,'raw_primary',side_effect=lambda p,c:raw[p]),patch.object(R.urllib.request,'urlopen',side_effect=open_url):R.build(root,out,hardlink_immutable_media=True)
    result=json.loads((out/'upload-plan.json').read_text());assert result['assets']==plan['exact_assets'];records={r['new_id']:r for r in plan['records']}
    for item in result['assets'][1:]:
        actual=out/item['name'];source=root/records[item['new_id']]['reordered_path'];assert actual.stat().st_ino==source.stat().st_ino and R.sha(actual)==item['sha256']
    report={'scope':'offline fixture transport contract; no actual media QA or remote mutation','passed':True,'exact71_inventory_and_book_order_unchanged':True,'all70_staged_MP4_inodes_reused_without_data_copy':True,'whole_asset_size_and_SHA_still_verified':True,'publisher_program_SHA256':R.sha(R.__file__)}
Path(__file__).with_name('low-disk-hardlink-build-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
