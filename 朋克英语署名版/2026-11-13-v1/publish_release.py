"""Publish the complete PDF-only collection after checking every hidden layer."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import argparse,base64,json,os,shutil,subprocess,zipfile
from provenance import ROOT,sha,inspect_pdf

REPO=os.environ.get('GITHUB_REPOSITORY','alienalgorithm/postgraduate-vocabulary')
TAG=os.environ.get('PDF_RELEASE_TAG','punk-english-pdfs-2026.11.13-v1')
OUT=Path(os.environ.get('PDF_ASSET_DIR','/tmp/punk-english-pdf-assets'))

def run(*args):
    p=subprocess.run(['gh',*args],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-2500:])
    return p.stdout
def api(path):return json.loads(run('api',path))
def send(path,data,method='POST'):
    p=subprocess.run(['gh','api','--method',method,path,'--input','-'],input=json.dumps(data),capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-2500:])
    return json.loads(p.stdout)

def verify():
    m=json.loads((ROOT/'manifest.json').read_text());assert m['passed'] and m['PDF_paths']==len(m['files'])==180
    assert m['all_normal_page_pixels_and_text_preserved'] and m['all_layers_reveal_verified'];seen=set()
    for x in m['files']:
        p=ROOT/x['pdf'];assert p.suffix.lower()=='.pdf' and p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
        assert x['normal_text_unchanged'] and x['normal_page_pixels_unchanged'] and x['layer_reveal_verified']
        if x['sha256'] not in seen:
            a=inspect_pdf(p);assert a['pages']==x['pages']==a['pages_with_attribution'];seen.add(x['sha256'])
    assert len(seen)==m['unique_PDFs']==177 and m['book']['pages']==475 and m['cover']['pages']==1
    print(json.dumps({'verified':True,'PDF_paths':180,'unique_PDFs':177,'all_pages_default_hidden':True}),flush=True);return m

def make_zip(name,entries,count):
    target=OUT/name
    with zipfile.ZipFile(target,'w',allowZip64=True) as z:
        for path,member in entries:
            assert member.endswith('.pdf') and not member.startswith('/') and '..' not in Path(member).parts
            i=zipfile.ZipInfo(member,(2026,11,13,0,0,0));i.create_system=3;i.external_attr=0o100644<<16;i.compress_type=zipfile.ZIP_STORED
            with path.open('rb') as a,z.open(i,'w',force_zip64=True) as b:shutil.copyfileobj(a,b,4*1024*1024)
    with zipfile.ZipFile(target) as z:
        assert len(z.namelist())==count and len(set(z.namelist()))==count
        assert all(n.endswith('.pdf') for n in z.namelist()) and z.testzip() is None
    assert target.stat().st_size<2_000_000_000;return target

def build(m):
    OUT.mkdir(parents=True,exist_ok=True);book=OUT/'PUNK-ENGLISH-70-STORIES.pdf';cover=OUT/'PUNK-ENGLISH-COVER.pdf'
    shutil.copy2(ROOT/m['book']['pdf'],book);shutil.copy2(ROOT/m['cover']['pdf'],cover)
    selected=sorted([x for x in m['files'] if x['original_path'].startswith('顺序重排版/分篇PDF/')],key=lambda x:Path(x['pdf']).name)
    assert len(selected)==70 and [Path(x['pdf']).name[:2] for x in selected]==[f'{n:02}' for n in range(1,71)]
    chapters=make_zip('70-PDF-BOOKLETS-PUNK-ENGLISH.zip',[(ROOT/x['pdf'],Path(x['pdf']).name) for x in selected],70)
    allfiles=make_zip('ALL-PDFS-PUNK-ENGLISH.zip',[(ROOT/x['pdf'],x['original_path']) for x in sorted(m['files'],key=lambda x:x['original_path'])],180)
    files=[book,chapters,allfiles,cover];assert {p.name for p in OUT.iterdir()}=={p.name for p in files}
    for f in files:print(json.dumps({'asset':f.name,'bytes':f.stat().st_size,'sha256':sha(f)}),flush=True)
    return files

def publish(m,files):
    commit=os.environ['GITHUB_SHA'];assert api(f'repos/{REPO}/git/ref/tags/{TAG}')['object']['sha']==commit
    prior=[r for r in api(f'repos/{REPO}/releases?per_page=100') if r['tag_name']==TAG];assert len(prior)<=1
    guide=f'https://github.com/{REPO}/blob/{commit}/朋克英语署名版/2026-11-13-v1/查看隐藏署名.md'
    notes=f'''本系列全部相关PDF统一加入默认关闭的“来源署名｜朋克英语”图层。正常阅读不显示，主动开启后每页均可显示署名与文档编号。

- 新封面70篇合订本：475页，沿用新顺序，目录页码、70处跳转和书签已顺延。
- 新顺序70份分篇PDF，文件名保持01—70及中英文标题。
- 全部相关PDF合集：178个原有PDF路径与2份新增PDF，共180份文件（177份不同文档）。
- 单页书封PDF，底部“考研重点词汇”已放大、加粗。

177份不同文档共2484页均验证默认画面与文字不变，且可主动开启署名图层。附件只含PDF或仅含PDF的ZIP。历史存档保留。

显示方法：Adobe Acrobat或支持图层的福昕阅读器→左侧“图层”→勾选“来源署名｜朋克英语”。也提供生成可见副本的脚本。[完整说明]({guide})。

署名、元数据及校验记录用于辅助溯源，不能单独证明原创或保证不能移除。'''
    r=prior[0] if prior else send(f'repos/{REPO}/releases',{'tag_name':TAG,'target_commitish':commit,'draft':True,'make_latest':'false','name':'考研学人｜全系列PDF・朋克英语隐藏署名版','body':notes})
    rid=r['id'];existing={a['name']:a for a in r['assets']}
    def upload(f):
        h=sha(f)
        if f.name not in existing:
            assert r['draft'];run('release','upload',TAG,str(f),'--repo',REPO)
        a=next(a for a in api(f'repos/{REPO}/releases/{rid}/assets?per_page=100') if a['name']==f.name)
        assert a['size']==f.stat().st_size and a['digest']=='sha256:'+h and a['state']=='uploaded'
        return {'name':f.name,'bytes':a['size'],'sha256':h,'asset_id':a['id'],'url':a['browser_download_url'],'remote_verified':True}
    with ThreadPoolExecutor(max_workers=2) as pool:assets=list(pool.map(upload,files))
    assert len(api(f'repos/{REPO}/releases/{rid}/assets?per_page=100'))==4
    if r['draft']:send(f'repos/{REPO}/releases/{rid}',{'draft':False,'make_latest':'true'},'PATCH')
    actual=api(f'repos/{REPO}/releases/tags/{TAG}');assert not actual['draft']
    report={'passed':True,'repository':REPO,'tag':TAG,'archive_commit':commit,'input_source_commit':m['source_commit'],'release_url':actual['html_url'],'PDF_paths':180,'unique_PDFs':177,'pages_verified':2484,'default_hidden':True,'layer_name':m['layer_name'],'assets':assets,'guide_url':guide}
    record='朋克英语署名版/2026-11-13-v1/核验/发布记录.json';body={'message':'保存全部PDF隐藏署名版的Release远程SHA256核验 [skip ci]','branch':'main','content':base64.b64encode((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()).decode()}
    rows=api(f'repos/{REPO}/contents/'+quote('朋克英语署名版/2026-11-13-v1/核验',safe='/'));old=next((x for x in rows if x['name']=='发布记录.json'),None)
    if old:body['sha']=old['sha']
    send(f'repos/{REPO}/contents/'+quote(record,safe='/'),body,'PUT')
    print(json.dumps({'published':True,'url':actual['html_url'],'assets':4,'all_remote_SHA256_verified':True},ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');p.add_argument('--build-only',action='store_true');a=p.parse_args();m=verify()
    if not a.verify_only:
        files=build(m)
        if not a.build_only:publish(m,files)
