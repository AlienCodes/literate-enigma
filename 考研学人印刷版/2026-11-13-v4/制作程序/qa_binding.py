"""Read the actual final book's continuous page numbers and TOC destinations."""
from pathlib import Path
import json,re,hashlib
import fitz
HERE=Path(__file__).resolve().parent
def main():
 rec=json.loads((HERE/'assembly-report.json').read_text());p=Path(rec['signed_pdf']);errors=[];numbers=[];links=[]
 with fitz.open(p) as d:
  assert len(d)==rec['pages']
  for i in range(1,len(d)-1):
   page=d[i];value=page.get_textbox(fitz.Rect(page.rect.width-37-47,page.rect.height-33,page.rect.width-37+2,page.rect.height-13)).strip();numbers.append({'physical_page':i+1,'printed_number':value})
   if value!=str(i+1):errors.append({'physical_page':i+1,'printed_number':value})
  assert '前言' in d[1].get_text()
  for page in range(2,9):
   for link in d[page].get_links():
    assert link['kind']==fitz.LINK_GOTO;target=link['page'];links.append({'contents_page':page+1,'target_physical_page':target+1})
  assert len(links)==70
  assert [x['target_physical_page'] for x in links]==[x['start_page'] for x in rec['chapters']]
  for item in rec['chapters']:
   title=d[item['start_page']-1].get_text();data=json.loads((HERE/'data'/f'{item["new_id"]}.json').read_text());assert re.sub(r'\s+','',data['title_zh']) in re.sub(r'\s+','',title)
 result={'pdf':str(p),'pdf_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'printed_page_numbers_checked':len(numbers),'printed_page_number_errors':errors,'contents_links':links,'contents_and_actual_chapter_titles_match':True,'physical_page_2_is_preface':True,'passed':not errors};(HERE/'actual-binding-QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'printed_pages_checked':len(numbers),'errors':errors,'TOC_links':len(links),'passed':result['passed']},ensure_ascii=False))
if __name__=='__main__':main()
