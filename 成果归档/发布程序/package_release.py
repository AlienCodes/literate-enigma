from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess

BASE=Path(__file__).resolve().parent;REPO=BASE/'target';ASSETS=BASE/'assets';ASSETS.mkdir(exist_ok=True)
TAG='reading-complete-2026.11.13-v1'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def selected_files():
    files=[REPO/p for p in ['AGENTS.md','CLAUDE.md','README.md']]
    for name in ['插图阅读小册','成果归档','最终版4K视频','简述重制核验','简述重制预览']:
        files.extend(p for p in (REPO/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith(('.lock','.tmp','.download')))
    records=json.loads((BASE/'download-records.json').read_text())
    files.extend(REPO/r['destination'] for p,r in records.items() if p.startswith('视频/'))
    return sorted(set(files))

def make_zip(name,entries):
    path=ASSETS/name;temp=path.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp,'w',allowZip64=True) as z:
        for p,arc in entries:
            comp=zipfile.ZIP_STORED if p.suffix.lower() in ['.pdf','.png','.jpg','.mp4'] else zipfile.ZIP_DEFLATED
            z.write(p,str(arc),compress_type=comp,compresslevel=None if comp==zipfile.ZIP_STORED else 6)
    with zipfile.ZipFile(temp) as z:
        assert len(z.namelist())==len({str(a) for _,a in entries})
        assert z.testzip() is None,name+' CRC failure'
    temp.replace(path)
    assert path.stat().st_size<2_000_000_000,(name,'over GitHub asset size')
    out={'name':name,'bytes':path.stat().st_size,'sha256':sha(path),'entries':len(entries)}
    print(json.dumps(out,ensure_ascii=False),flush=True);return out

def main():
    files=selected_files();manifest_path=REPO/'成果归档/文件清单.json'
    files=[p for p in files if p!=manifest_path]
    inventory=[]
    for p in files:inventory.append({'path':str(p.relative_to(REPO)),'bytes':p.stat().st_size,'sha256':sha(p)})
    inv={'schema_version':1,'release_tag':TAG,'repository':'alienalgorithm/postgraduate-vocabulary','branch':'main','intended_primary_repository':'alienalgorithm/postgraduate-vocabulary','primary_sync_status':'complete','scope':'All completed materials from this production session; pre-existing repository files are retained in Git.','videos':70,'individual_booklets':70,'combined_volumes':7,'original_illustrations':70,'PDF_page_previews':467,'video_summary_cards':70,'files':inventory,'self_excluded_from_file_hashes':True}
    manifest_path.write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n');files.append(manifest_path);files.sort()
    q=json.loads((REPO/'插图阅读小册/manifest.json').read_text())
    assets=[]
    assets.append(make_zip('ALL-MATERIALS-2026-11-13.zip',[(p,p.relative_to(REPO)) for p in files]))
    video_files=[p for p in files if p.relative_to(REPO).parts[0] in ['最终版4K视频','简述重制核验','简述重制预览'] or p.name=='视频定稿文件清单.json']
    assets.append(make_zip('videos-70-4k.zip',[(p,p.relative_to(REPO)) for p in video_files]))
    individual=[REPO/'插图阅读小册'/a['pdf'] for a in q['chapters']]
    assets.append(make_zip('booklets-70-individual-PDF.zip',[(p,p.name) for p in individual]))
    combined=[REPO/'插图阅读小册'/a['pdf'] for a in q['volumes']]
    assets.append(make_zip('booklets-7-volumes.zip',[(p,p.name) for p in combined]))
    artwork=[(REPO/'插图阅读小册'/a['illustration'],a['id']+'.png') for a in q['chapters']]
    assets.append(make_zip('illustrations-70-originals.zip',artwork))
    previews=[(REPO/'插图阅读小册'/p['path'],a['id']+'/'+Path(p['path']).name) for a in q['chapters'] for p in a['previews']]
    assets.append(make_zip('booklet-previews-467-pages.zip',previews))
    source=[p for p in files if p.suffix.lower() not in ['.pdf','.png','.jpg','.mp4']]
    assets.append(make_zip('production-source-and-audits.zip',[(p,p.relative_to(REPO)) for p in source]))
    for v,p in zip(q['volumes'],combined):
        dest=ASSETS/f'booklet-volume-{v["volume"]:02}.pdf';shutil.copy2(p,dest)
        assets.append({'name':dest.name,'bytes':dest.stat().st_size,'sha256':sha(dest),'volume':v['volume'],'pages':v['pages']})
    out={'repository':'alienalgorithm/postgraduate-vocabulary','branch':'main','intended_primary_repository':'alienalgorithm/postgraduate-vocabulary','primary_sync_status':'complete','tag':TAG,'complete':True,'assets':assets,'file_inventory_sha256':sha(manifest_path),'individual_files':len(inventory)}
    (ASSETS/'RELEASE-MANIFEST.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    m=ASSETS/'RELEASE-MANIFEST.json'
    checks=''.join(f'{a["sha256"]}  {a["name"]}\n' for a in assets)+f'{sha(m)}  RELEASE-MANIFEST.json\n'
    (ASSETS/'SHA256SUMS.txt').write_text(checks)
    (BASE/'package-result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'packages_ready':True,'assets':len(assets)+2,'total_bytes':sum(p.stat().st_size for p in ASSETS.iterdir() if p.is_file()),'files_in_full_package':len(files)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
