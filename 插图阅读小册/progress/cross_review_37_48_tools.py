import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/workspace/work/booklet70')
import booklet_utils as b
ROOT=b.ROOT
def sign(n,notes):
 n=f'{int(n):02}';content=ROOT/'content/articles'/f'{n}.json';d=json.loads(content.read_text());b.validate_article(d)
 qc=json.loads((ROOT/'production'/n/'qc.json').read_text())
 assert qc['passed'] and qc['engine_revision']>=3
 assert not (ROOT/'production'/n/'error.json').exists()
 ch=hashlib.sha256(content.read_bytes()).hexdigest();ih=hashlib.sha256((ROOT/'illustrations'/f'{n}.png').read_bytes()).hexdigest();ph=hashlib.sha256(Path(qc['pdf']).read_bytes()).hexdigest()
 assert qc['content_sha256']==ch and qc['image_sha256']==ih and qc['pdf_sha256']==ph
 full=' '.join(d['english_paragraphs'])
 assert all(not v['core'] or (v['source_term'] in v['context_phrase'] and len(v['context_phrase'])<=38 and v['context_phrase'] in full) for v in d['vocabulary'])
 assert all(q['text_with_blank'].count('______')==1 and q['text_with_blank'].replace('______',q['answer']) in full for q in d['questions'])
 out={'id':n,'reviewer':'/root/summaries_25_36','passed':True,'content_sha256':ch,'illustration_sha256':ih,'pdf_visual_review':True,'reviewed_pdf_sha256':ph,'engine_revision':qc['engine_revision'],'notes':notes}
 b.atomic_json(ROOT/'reviews'/f'{n}.json',out)
 progress=ROOT/'progress/cross_37_48_by_25_36.json';p=json.loads(progress.read_text()) if progress.exists() else {'assigned':[f'{x:02}' for x in range(37,49)],'passed_ids':[],'pending_ids':[]}
 p['passed_ids']=sorted(set(p['passed_ids']+[n]));p['pending_ids']=[x for x in p['assigned'] if x not in p['passed_ids']];b.atomic_json(progress,p)
 print('SIGNED',n,'engine',qc['engine_revision'],'pages',qc['pages'],ph)

def snippets(n,mapping):
 path=ROOT/'content/articles'/f'{int(n):02}.json';d=json.loads(path.read_text());changed=[]
 for v in d['vocabulary']:
  if v['core'] and v['source_term'] in mapping:
   new=mapping[v['source_term']]
   if new!=v['context_phrase']:changed.append({'term':v['source_term'],'before':v['context_phrase'],'after':new});v['context_phrase']=new
 b.validate_article(d);b.atomic_json(path,d)
 return changed
