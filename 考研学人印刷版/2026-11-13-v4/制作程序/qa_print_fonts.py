"""Actual default-view font sizes and embedded visible-font audit for print."""
from pathlib import Path
import hashlib,json,re,collections
import fitz
HERE=Path(__file__).resolve().parent
def key(name):return re.sub(r'[^a-z0-9]','',re.sub(r'^[A-Z]{6}\+','',name).lower())
def main():
 book=HERE/'signed/book/PUNK-ENGLISH-70-STORIES.pdf';cache={};visible_families={};unused_unembedded={};errors=[];sizes=collections.Counter();page_count=0
 with fitz.open(book) as doc:
  for page in doc:
   page_count+=1;resources=page.get_fonts(full=True);fonts={}
   for resource in resources:
    xref,ext,kind,base,name,*rest=resource
    if xref not in cache:
     extracted=doc.extract_font(xref);cache[xref]={'basefont':base,'type':kind,'extension':ext,'embedded_font_bytes':len(extracted[3]),'embedded':bool(extracted[3])}
    fonts.setdefault(key(base),[]).append(xref)
   used=set()
   for block in page.get_text('dict')['blocks']:
    for line in block.get('lines',[]):
     for span in line.get('spans',[]):
      if not span['text'].strip():continue
      family=span['font'];name=key(family);used.add(name);sizes[round(span['size'],3)]+=len(span['text']);matches=fonts.get(name,[])
      if not matches:errors.append({'page':page.number+1,'visible_font':family,'error':'No matching page font resource'})
      elif not all(cache[x]['embedded'] for x in matches):errors.append({'page':page.number+1,'visible_font':family,'error':'Visible font is not embedded','resources':[cache[x] for x in matches]})
      visible_families.setdefault(family,{'characters':0,'sizes':set(),'embedded_resource_xrefs':set()});visible_families[family]['characters']+=len(span['text']);visible_families[family]['sizes'].add(round(span['size'],3));visible_families[family]['embedded_resource_xrefs'].update(matches)
   for family,xrefs in fonts.items():
    if family not in used:
     for x in xrefs:
      if not cache[x]['embedded']:unused_unembedded.setdefault(cache[x]['basefont'],set()).add(x)
 roles={}
 for n in range(1,71):
  rec=json.loads((HERE/'unsigned/chapters'/f'{n:02d}'/'layout-and-content-qc.json').read_text())
  for row in rec['placed_elements']:
   if 'font_size' in row:
    role=row['kind'];roles.setdefault(role,set()).add(float(row['font_size']))
 result={'pdf':str(book),'pdf_sha256':hashlib.sha256(book.read_bytes()).hexdigest(),'actual_default_view_pages_scanned':page_count,'visible_font_families':{name:{'characters':r['characters'],'visible_sizes_pt':sorted(r['sizes']),'matching_embedded_resource_count':len(r['embedded_resource_xrefs'])} for name,r in visible_families.items()},'visible_character_size_distribution_pt':dict(sorted(sizes.items())),'actual_minimum_visible_span_pt':min(sizes),'layout_roles_font_sizes_pt':{k:sorted(v) for k,v in roles.items()},'font_resources_total':len(cache),'font_resources_embedded':sum(x['embedded'] for x in cache.values()),'nonembedded_but_unused_standard_resources':{k:{'count':len(v),'not_used_by_any_visible_span':True} for k,v in unused_unembedded.items()},'all_visible_used_fonts_embedded':not errors,'errors':errors,'notes':['Actual default-hidden OCG state is used; hidden attribution font sizes are excluded.','7.8pt is auxiliary vocabulary grammatical labels; 8.1pt is the running footer, not body text.','Original approved B5 sizes: body English12.7pt/Chinese12pt; vocabulary forms11.5/10.8pt and meanings10.5/10.2pt; original short source examples9.5pt; summary11.5pt.','Compact main book prints no sentence notes, grammatical analysis, exercises or answers.','Unused standard Helvetica resources may be present in ReportLab page dictionaries; none is used by a printed visible span.'],'passed':not errors}
 (HERE/'print-font-embedding-QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'pages':page_count,'minimum_visible_span_pt':min(sizes),'all_visible_used_fonts_embedded':not errors,'errors':errors[:10]},ensure_ascii=False))
if __name__=='__main__':main()
