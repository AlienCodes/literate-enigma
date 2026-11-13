import sys,json,re,hashlib,shutil
from pathlib import Path
sys.path.insert(0,'/workspace/work/booklet70')
import booklet_utils as b
ROOT=b.ROOT
STYLE=(ROOT/'illustration-style-standard.txt').read_text().strip()
PROGRESS=ROOT/'progress/group_25_36.json'
def phrase_for(n,t):
 s=b.source(n)
 for o in s['highlighted_occurrences']:
  if o['term']!=t or t not in o['english_context']:continue
  text=o['english_context'];at=text.find(t);end=at+len(t)
  spans=list(re.finditer(r'\S+',text))
  indexes=[i for i,m in enumerate(spans) if m.end()>at and m.start()<end]
  if not indexes:continue
  left=max(0,indexes[0]-1);right=min(len(spans)-1,indexes[-1]+2)
  while right>left and spans[right].end()-spans[left].start()>38:
   if right>indexes[-1]:right-=1
   elif left<indexes[0]:left+=1
   else:break
  p=text[spans[left].start():spans[right].end()].strip(' ,;:.')
  if t in p and len(p)<=38:return p
 raise ValueError((n,t,'no short phrase'))
def save(n,zh,rows,core,questions,cover,brief,note='',overrides=None):
 rows=[line.split('|') for line in rows.strip().splitlines()]
 assert all(len(x)==4 for x in rows),(n,'row fields')
 assert [x[0] for x in rows]==b.terms(n),(n,'term rows order')
 core=set(core.split('|'));assert len(core)==22,(n,len(core))
 assert core<=set(b.terms(n))
 overrides=overrides or {}
 vocab=[]
 for t,h,p,m in rows:
  assert len(m)<=26,(n,t,'meaning length')
  ph=overrides.get(t,phrase_for(n,t)) if t in core else ''
  assert not ph or t in ph,(n,t,'missing exact term')
  vocab.append({'source_term':t,'headword':h,'form_in_text':t,'pos':p,'meaning_zh':m,'core':t in core,'context_phrase':ph})
 prompt=STYLE+'\n\nARTICLE-SPECIFIC SCENE: '+brief
 obj=b.save_article(n,zh,vocab,questions,cover,reading_note=note,illustration_prompt=prompt)
 prog=json.loads(PROGRESS.read_text())
 prog['content_ready']=sorted(set(prog['content_ready']+[f'{int(n):02}']))
 prog['stage']='content and image production in progress'
 b.atomic_json(PROGRESS,prog)
 print(b.validate_article(obj))
 print('CORE PHRASES:',[(v['source_term'],v['context_phrase']) for v in vocab if v['core']])
 return obj

def save_image(n,path,notes):
 n=f'{int(n):02}';src=Path(path);dest=ROOT/'illustrations'/f'{n}.png'
 assert src.is_file(),src
 shutil.copy2(src,dest)
 content=json.loads((ROOT/'content/articles'/f'{n}.json').read_text())
 meta={'id':n,'generation_path':str(src),'image_path':str(dest),'prompt':content['illustration_prompt'],'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'review_notes':notes,'reviewed':True}
 b.atomic_json(ROOT/'illustrations'/f'{n}.json',meta)
 prog=json.loads(PROGRESS.read_text());prog['images_ready']=sorted(set(prog['images_ready']+[n]));prog['ready_ids']=sorted(set(prog['content_ready'])&set(prog['images_ready']))
 b.atomic_json(PROGRESS,prog)
 print('SAVED',dest,meta['sha256'])
