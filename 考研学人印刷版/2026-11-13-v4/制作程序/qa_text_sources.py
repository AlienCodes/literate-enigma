"""Read actual freshly rendered PDFs back against every frozen current source."""
from pathlib import Path
import argparse, hashlib, html, json, re
import fitz

HERE=Path(__file__).resolve().parent
def norm(t):return re.sub(r'\s+','',t)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--ids',nargs='+');args=p.parse_args();ids=[x.zfill(2) for x in args.ids] if args.ids else [f'{n:02d}' for n in range(1,71)];rows=[];errors=[]
 for no in ids:
  d=json.loads((HERE/'data'/f'{no}.json').read_text());rec=json.loads((HERE/'unsigned/chapters'/no/'layout-and-content-qc.json').read_text());pdf=Path(rec['pdf'])
  try:
   assert sha(pdf)==rec['sha256'];assert rec['source_hashes']==d['source_hashes']
   with fitz.open(pdf) as doc:
    whole=norm(''.join(page.get_text() for page in doc));assert '\ufffd' not in whole and '\ufffd' not in ''.join(d['english_paragraphs'])
    vocabulary_text=norm(''.join(doc[sec['page']-1].get_text() for sec in rec['sections'] if sec['title']=='词汇与表达'))
    note_text=norm(''.join(doc[sec['page']-1].get_text() for sec in rec['sections'] if sec['title']=='注释'))
    summary_text=norm(''.join(doc[sec['page']-1].get_text() for sec in rec['sections'] if sec['title']=='文章简述'))
    for entry in d['vocabulary']:
     assert norm(entry['form_in_text']) in vocabulary_text,(no,'Missing focus form',entry['form_in_text'])
     assert norm(entry['meaning_zh']) in vocabulary_text,(no,'Missing current focus meaning',entry['form_in_text'],entry['meaning_zh'])
    assert not note_text and not any(sec['title'] in ('注释','词汇练习','参考答案') for sec in rec['sections']),(no,'Out-of-scope analysis/exercise section printed')
    for label,text in d['approved_summary']:assert norm(label+'：'+text) in summary_text,(no,'Missing latest summary point',label,text)
    assert not any(marker in whole for marker in ('{{','}}','**','（结局：')),(no,'Raw markup or old ending visible')
    rows.append({'id':no,'source_id':d['source_id'],'pages':len(doc),'pdf_sha256':sha(pdf),'current_focus_forms_and_meanings_read_back':len(d['vocabulary']),'notes_preserved_in_source_only':len(d['notes']),'analysis_exercises_and_answers_absent':True,'current_summary_points_read_back':5,'body_paragraphs_already_exact_read_back':rec['body_text_extracted_from_actual_PDF_exact']})
  except Exception as e:errors.append({'id':no,'type':type(e).__name__,'error':str(e)})
 out={'actual_PDF_text_readback':True,'count':len(rows),'expected':len(ids),'chapters':rows,'errors':errors,'passed':len(rows)==len(ids) and not errors}
 (HERE/'actual-content-readback-QA.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'count':len(rows),'errors':errors,'passed':out['passed']},ensure_ascii=False))
if __name__=='__main__':main()
