"""Default-hidden PDF attribution. Does not assert independent proof of authorship."""
from pathlib import Path
import hashlib, json, string, shutil, datetime
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import fitz

ROOT = Path(__file__).resolve().parent
LAYER_NAME = '来源署名｜朋克英语'
OWNER = '朋克英语'
FONT = ROOT / '字体/PKEN-Attribution.ttf'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def make_font(original):
    from fontTools import subset
    FONT.parent.mkdir(parents=True, exist_ok=True)
    opts = subset.Options()
    font = subset.load_font(str(original), opts)
    sub = subset.Subsetter(options=opts)
    sub.populate(text=string.printable + '朋克英语B站UP主来源署名考研学人文档编号：｜·（默认隐藏）')
    sub.subset(font)
    subset.save_font(font, str(FONT), opts)
    return FONT

def layer_xref(doc):
    found = [x for x,v in doc.get_ocgs().items() if v['name'] == LAYER_NAME]
    if len(found) != 1:
        raise ValueError(f'Expected one attribution layer, found {len(found)}')
    return found[0]

def show_copy(source, output):
    if Path(source).resolve() == Path(output).resolve():
        raise ValueError('Use a separate output file; keep the original download intact.')
    with fitz.open(source) as doc:
        ocg = layer_xref(doc)
        conf = doc.get_layer(-1)
        on = list(dict.fromkeys(conf.get('on', []) + [ocg]))
        off = [x for x in conf.get('off', []) if x != ocg]
        doc.set_layer(-1, on=on, off=off)
        doc.save(output, garbage=4, deflate=True)

def inspect_pdf(path):
    with fitz.open(path) as doc:
        ocg = layer_xref(doc)
        conf = doc.get_layer(-1)
        assert ocg in conf.get('off', []) and not doc.get_ocgs()[ocg]['on']
        pages_with_layer = 0
        for p in doc:
            items = p.get_oc_items()
            assert any(ocg in item for item in items), (p.number, items, ocg)
            pages_with_layer += 1
        assert OWNER in doc.metadata.get('creator', '')
        assert OWNER in doc.get_xml_metadata()
        return {'pages':len(doc), 'pages_with_attribution':pages_with_layer,
                'layer_name':LAYER_NAME, 'default_hidden':True,
                'metadata_author':doc.metadata.get('author',''),
                'metadata_creator':doc.metadata.get('creator','')}

def stamp_pdf(source, output, *, preserve_original_author=False, source_commit=''):
    source, output = Path(source), Path(output)
    original_sha = sha(source)
    doc_id = 'PKEN-' + original_sha[:20].upper()
    output.parent.mkdir(parents=True, exist_ok=True)
    font = fitz.Font(fontfile=str(FONT))
    with fitz.open(source) as doc:
        if any(v['name'] == LAYER_NAME for v in doc.get_ocgs().values()):
            inspect_pdf(source)
            if source.resolve() != output.resolve(): shutil.copy2(source, output)
            return {'passed':True, 'idempotent_copy':True, 'source_sha256':original_sha,
                    'sha256':sha(output), **inspect_pdf(output)}
        bookmarks = doc.get_toc()
        previous_layer_state = doc.get_layer(-1) if doc.get_ocgs() else {}
        old_xml = doc.get_xml_metadata()
        ocg = doc.add_ocg(LAYER_NAME, on=False)
        total = len(doc)
        for page in doc:
            area = page.rect * page.derotation_matrix
            size = min(54, area.width / 8)
            width = font.text_length(OWNER, fontsize=size)
            point = fitz.Point(area.x0+(area.width-width)/2, area.y0+area.height/2+size*.35)
            page.insert_text(point, OWNER, fontsize=size, fontname='PKENAttribution',
                             fontfile=str(FONT), color=(.60,.09,.19),
                             fill_opacity=.42, overlay=True, oc=ocg)
            footer = f'B站UP主：朋克英语  |  {doc_id}  |  {page.number+1}/{total}'
            page.insert_text((area.x0+20,area.y1-8), footer, fontsize=6.2,
                             fontname='PKENAttribution',fontfile=str(FONT),
                             color=(.08,.25,.48), fill_opacity=.85, overlay=True,oc=ocg)
        meta = dict(doc.metadata)
        old_author = meta.get('author','')
        if not preserve_original_author: meta['author'] = OWNER
        meta['creator'] = 'B站UP主 朋克英语｜来源署名处理'
        meta['subject'] = (meta.get('subject','') + f'；来源署名：B站UP主朋克英语；文档编号：{doc_id}').lstrip('；')
        meta['modDate'] = datetime.datetime.now(datetime.timezone.utc).strftime('D:%Y%m%d%H%M%SZ')
        doc.set_metadata(meta)
        xml = f'''<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:RDF><rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:pken="https://github.com/alienalgorithm/postgraduate-vocabulary/ns/provenance/1.0/">
<dc:publisher><rdf:Seq><rdf:li>朋克英语</rdf:li></rdf:Seq></dc:publisher>
<dc:creator><rdf:Seq><rdf:li>{escape(old_author if preserve_original_author else OWNER)}</rdf:li></rdf:Seq></dc:creator>
<dc:identifier>{doc_id}</dc:identifier><pken:Attribution>B站UP主：朋克英语</pken:Attribution>
<pken:LayerName>{LAYER_NAME}</pken:LayerName><pken:DefaultVisibility>OFF</pken:DefaultVisibility>
<pken:SourceSHA256>{original_sha}</pken:SourceSHA256><pken:SourceCommit>{source_commit}</pken:SourceCommit>
<pken:EvidenceScope>来源署名与文件溯源信息，不单独证明原创或不可删除</pken:EvidenceScope>
</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>'''
        if old_xml:
            try:
                old_root, new_root = ET.fromstring(old_xml), ET.fromstring(xml)
                rdf_tag = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF'
                creator_tag = '{http://purl.org/dc/elements/1.1/}creator'
                publisher_tag = '{http://purl.org/dc/elements/1.1/}publisher'
                old_rdf, new_rdf = old_root.find('.//'+rdf_tag), new_root.find('.//'+rdf_tag)
                assert old_rdf is not None and new_rdf is not None
                desc = list(new_rdf)[0]
                for tag, keep_old in [(creator_tag,preserve_original_author),(publisher_tag,True)]:
                    existing = [(parent,child) for parent in old_rdf.iter() for child in parent if child.tag==tag]
                    if existing and keep_old:
                        for child in list(desc):
                            if child.tag==tag: desc.remove(child)
                    elif existing:
                        for parent,child in existing: parent.remove(child)
                old_rdf.append(desc)
                xml = ET.tostring(old_root,encoding='unicode')
            except (ET.ParseError,AssertionError):
                # Retain malformed legacy metadata as evidence without losing its contents.
                xml = xml.replace('</rdf:Description>', '<pken:OriginalXMP>'+escape(old_xml)+'</pken:OriginalXMP></rdf:Description>')
        doc.set_xml_metadata(xml)
        off = list(dict.fromkeys(previous_layer_state.get('off',[])+[ocg]))
        on = [x for x in previous_layer_state.get('on',[]) if x!=ocg]
        doc.set_layer(-1, off=off, on=on)
        doc.save(output, garbage=4, deflate=True, no_new_id=True)
    with fitz.open(output) as d: assert d.get_toc() == bookmarks
    return {'passed':True, 'document_id':doc_id, 'source_sha256':original_sha,
            'sha256':sha(output), 'bytes':output.stat().st_size,
            'original_author':old_author, 'original_author_preserved':preserve_original_author,
            **inspect_pdf(output)}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='给PDF每页加入默认隐藏的朋克英语来源署名。')
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--preserve-original-author',action='store_true')
    args=parser.parse_args()
    print(json.dumps(stamp_pdf(args.source,args.output,
          preserve_original_author=args.preserve_original_author),ensure_ascii=False,indent=2))
