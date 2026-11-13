from pathlib import Path
import shutil,json,re,hashlib

BASE=Path(__file__).resolve().parent
SRC=Path('/workspace/work/booklet70')
REPO=BASE/'target';DEST=REPO/'插图阅读小册'
PRIVATE=[r'https://chatgpt\.com/space/page_[a-zA-Z0-9]+',r'library-file:[A-Za-z0-9_:/.-]+',r'page_[a-f0-9]{32}',r'user-[A-Za-z0-9]+']

def scrub(t):
    for p in PRIVATE:t=re.sub(p,'[private-reference-omitted]',t)
    return t

def copy(p,to,clean=False):
    to.parent.mkdir(parents=True,exist_ok=True)
    if clean and p.suffix.lower() in ['.json','.md','.txt','.py','.js']:
        to.write_text(scrub(p.read_text()),encoding='utf8')
    else:shutil.copy2(p,to)

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    for dirname in ['content','sources','fonts','reviews','progress']:
        for p in (SRC/dirname).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:copy(p,DEST/p.relative_to(SRC),clean=dirname in ['reviews','progress'])
    for p in (SRC/'illustrations').iterdir():
        if p.is_file() and (p.suffix=='.json' or p.name=='01-preview.png' or re.fullmatch(r'\d{2}\.png',p.name)):copy(p,DEST/p.relative_to(SRC),clean=p.suffix=='.json')
    for n in range(1,71):
        folder=SRC/f'production/{n:02}';q=json.loads((folder/'qc.json').read_text());manifest=json.loads((folder/'preview-manifest.json').read_text())
        paths=[Path(q['pdf']),folder/'qc.json',folder/'layout.json',folder/'preview-manifest.json',folder/'contact-sheet.jpg']+[Path(p['path']) for p in manifest['pages']]
        for p in paths:copy(p,DEST/p.relative_to(SRC))
    for n in range(1,8):
        folder=SRC/f'volumes/{n:02}';q=json.loads((folder/'qc.json').read_text())
        for p in [Path(q['pdf']),folder/'qc.json',folder/'contents-preview.png']:copy(p,DEST/p.relative_to(SRC))
    for p in (SRC/'output').glob('*'):
        if p.is_file() and p.suffix in ['.pdf','.json']:copy(p,DEST/p.relative_to(SRC),clean=p.suffix=='.json')
    code=['booklet_utils.py','cjk_layout.py','build_booklet01.py','build_all70.py','build_volumes.py','publication_payloads.py']
    for name in code:copy(SRC/name,DEST/name)
    for p in SRC.iterdir():
        if p.is_file():copy(p,REPO/'成果归档/小册子原始制作程序'/p.name,clean=True)
    for p in (SRC/'workers').rglob('*'):
        if p.is_file() and p.suffix in ['.py','.json','.md','.txt'] and '__pycache__' not in p.parts:copy(p,REPO/'成果归档/小册子协作记录'/p.relative_to(SRC/'workers'),clean=True)
    for p in Path('/workspace/work').glob('order70-*.json'):copy(p,REPO/'成果归档/阅读排序推敲材料'/p.name)
    order=json.loads(Path('/workspace/work/order70-recommended.json').read_text())['order']
    (DEST/'recommended-order.json').write_text(json.dumps({'original_ids_preserved':True,'order':order,'note':'编辑推荐阅读顺序；不代表经过用户实验验证的唯一最优顺序。'},ensure_ascii=False,indent=2)+'\n')
    for name in ['source-index.json','source-cleaning-audit.json','booklet-terminology-corrections.json','illustration-style-standard.txt','BATCH-SPEC.txt','CROSS-REVIEW-SPEC.txt']:
        copy(SRC/name,DEST/name,clean=True)
    for p in Path('/usr/share/fonts/truetype/liberation').glob('*.ttf'):copy(p,DEST/'fonts'/p.name)
    license=Path('/usr/share/doc/fonts-liberation/copyright')
    if license.exists():copy(license,DEST/'fonts/Liberation-LICENSE.txt')
    p=DEST/'booklet_utils.py';p.write_text(p.read_text().replace("ROOT=Path('/workspace/work/booklet70')","ROOT=Path(__file__).resolve().parent"))
    p=DEST/'build_booklet01.py';t=p.read_text().replace("SOURCE = load('/workspace/work/summary-round2/source/01.json')","SOURCE = load(ROOT / 'sources/01.json')").replace("SUMMARY = load('/workspace/work/summary-round2/final/01-12.json')['01']","SUMMARY = SOURCE['approved_summary']")
    t=re.sub(r"Path\('/usr/share/fonts/truetype/liberation/([^']+)'\)",r"ROOT / 'fonts/\1'",t);p.write_text(t)
    p=DEST/'build_volumes.py';p.write_text(p.read_text().replace("Path('/workspace/work/order70-recommended.json')","(ROOT/'recommended-order.json')"))
    p=DEST/'publication_payloads.py';t=p.read_text().replace("if sha(q['pdf'])!=q['pdf_sha256']:","q['pdf']=str(ROOT/'production'/n/Path(q['pdf']).name)\n    if sha(q['pdf'])!=q['pdf_sha256']:")
    t=t.replace("if pm['pdf_sha256']!=q['pdf_sha256']:","for page in pm['pages']:page['path']=str(ROOT/'production'/n/Path(page['path']).name)\n    if pm['pdf_sha256']!=q['pdf_sha256']:");p.write_text(t)
    (DEST/'requirements.txt').write_text('reportlab==4.4.4\nPyMuPDF==1.26.6\nPillow==12.0.0\n')
    manifest={'schema_version':1,'source_video_commit':'9374187e740fcefef39e42259a2f057ae504ebc9','chapters':[],'volumes':[],'artwork_count':70,'chapter_pages':467,'volume_pages':474,'vocabulary_entries':4158,'core_entries':1540,'recall_questions':280,'previews':467}
    for n in range(1,71):
        d=json.loads((SRC/f'content/articles/{n:02}.json').read_text());q=json.loads((SRC/f'production/{n:02}/qc.json').read_text());pm=json.loads((SRC/f'production/{n:02}/preview-manifest.json').read_text())
        image=DEST/'illustrations'/('01-preview.png' if n==1 else f'{n:02}.png')
        manifest['chapters'].append({'id':f'{n:02}','title_zh':d['title_zh'],'title_en':d['title_en'],'pages':q['pages'],'pdf':str((DEST/f'production/{n:02}'/Path(q['pdf']).name).relative_to(DEST)),'pdf_sha256':q['pdf_sha256'],'content_sha256':q['content_sha256'],'illustration':str(image.relative_to(DEST)),'illustration_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'previews':[{'path':f'production/{n:02}/'+Path(p['path']).name,'sha256':p['sha256']} for p in pm['pages']]})
    for n in range(1,8):
        q=json.loads((SRC/f'volumes/{n:02}/qc.json').read_text());manifest['volumes'].append({'volume':n,'pages':q['pages'],'pdf':f'volumes/{n:02}/'+Path(q['pdf']).name,'pdf_sha256':q['pdf_sha256'],'articles':[i['id'] for i in q['articles']]})
    (DEST/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'booklets':70,'volumes':7,'copied_files':sum(p.is_file() for p in DEST.rglob('*')),'bytes':sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file())},ensure_ascii=False))

if __name__=='__main__':main()
