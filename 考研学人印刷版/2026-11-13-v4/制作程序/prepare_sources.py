"""Freeze the current public PAY manuscripts into independently validated book data.

No old PDF is reused as content. Old content contributes only illustration IDs,
approved cover questions and exercises that still reproduce exact source text.
"""
from __future__ import annotations
import argparse, ast, copy, hashlib, json, re, shutil, subprocess, types
from pathlib import Path

HERE=Path(__file__).resolve().parent
PAY=Path('/workspace/work/video-audit70-20261113/payload')
OLD=Path('/workspace/work/booklet70')
REPO=Path('/workspace/work/github-publication/target')
TOOLS=Path('/workspace/work/audit-repo/视频/工具')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def plain_en(t):return re.sub(r'\s+',' ',re.sub(r'\{\{.*?\}\}','',t).replace('**','')).strip()
def strip_gloss(t):return re.sub(r'\{\{.*?\}\}','',t).replace('\n','')
def plain_zh(t):return re.sub(r'\*\*([^*]+)\*\*\([^)]*\)',r'\1',strip_gloss(t)).replace('**','').replace('#Y','').strip()
def atom_write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)

def checker():
 tree=ast.parse((TOOLS/'check_all.py').read_text());support={'ROOT','strip','DOCX_起','STOP','虚词','T12全篇_起','_OJ'}
 nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef)) or isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in support for t in n.targets)]
 ns={'__file__':str(TOOLS/'check_all.py'),'__name__':'book_source_original_checker'};exec(compile(ast.Module(nodes,type_ignores=[]),str(TOOLS/'check_all.py'),'exec'),ns)
 return types.SimpleNamespace(**ns)

def table_rows(md):
 rows=[]
 for line in md.split('## 速查表',1)[1].split('## ',1)[0].splitlines():
  if not line.startswith('|'):continue
  cols=[x.strip() for x in line.strip().strip('|').split('|')]
  if len(cols)>=2 and cols[0] not in ('词','---') and not set(cols[0])<={'-',':'}:rows.append((cols[0].replace('**',''),cols[1]))
 return rows

def summary(note):
 assert note.count('（简述：')==1,'Exactly one revised summary is required'
 start=note.index('（简述：');text=note[start+4:].strip();assert text.endswith('）');text=text[:-1].replace('\n','')
 parts=[]
 for p in text.split('▸'):
  p=p.strip()
  if not p:continue
  label,sep,body=p.partition('：');assert sep and body
  parts.append([label,body])
 assert len(parts)==5,parts
 return note[:start].rstrip(),parts

def convert(no,newid,C):
 sp=PAY/f'视频/脚本/{no}.json';gp=PAY/f'视频/工具/初稿生成/gen{no}.py'
 mdp=next((p for root in (PAY,REPO,Path('/workspace/work/audit-repo')) for p in (root/'新版定稿').glob(f'{no}-*.md')),None)
 assert mdp is not None,(no,'No current manuscript source')
 d=json.loads(sp.read_text());md=mdp.read_text();errors=C.查(d,md);assert not errors,(no,errors)
 assert not any('（结局：' in (c.get('note') or '') for s in d['sentences'] for c in s['chunks']),(no,'old ending remains')
 old=json.loads((OLD/f'content/articles/{no}.json').read_text());en_by={};zh_by={};en_markup_by={};zh_markup_by={};notes=[];focus=[];meanings={};occurrences=[];inline_gloss_count=0
 for si,s in enumerate(d['sentences'],1):
  para=s['para'];ens=[];zhs=[]
  for c in s['chunks']:
   ens.append(re.sub(r'\{\{.*?\}\}','',c['en']).strip());zhs.append(strip_gloss(c['zh']))
   for zh,term in re.findall(r'\*\*([^*]+)\*\*\(([^)]*)\)',c['zh']):meanings.setdefault(term.lower(),[]).append(zh)
  en=' '.join(ens);zh=''.join(zhs)
  en_markup_by.setdefault(para,[]).append(en);zh_markup_by.setdefault(para,[]).append(zh)
  en_by.setdefault(para,[]).append(plain_en(en));zh_by.setdefault(para,[]).append(plain_zh(zh))
  words=C.句重点词(s)
  words=sorted(words,key=lambda w:plain_en(en).lower().find(w.split()[0].lower()))
  for word in words:
   occurrences.append({'sentence':si,'term':word,'paragraph':para})
   if word.lower() not in {x.lower() for x in focus}:focus.append(word)
  for ci,c in enumerate(s['chunks'],1):
   glosses={}
   for visible,key in re.findall(r'\{\{(.*?)\|([^}]+)\}\}',c['zh']):glosses.setdefault(key,[]).append(visible)
   for key,parts in glosses.items():
    notes.append({'sentence':si,'chunk':ci,'source_English':plain_en(c['en']),'text':key+'：'+''.join(parts),'kind':'current inline word gloss'});inline_gloss_count+=1
   note=c.get('note') or ''
   if '（简述：' in note:note,approved_summary=summary(note)
   if note.strip():notes.append({'sentence':si,'chunk':ci,'source_English':plain_en(c['en']),'text':note.replace('#Y','').strip()})
 full=' '.join(' '.join(en_by[k]) for k in sorted(en_by));tr=table_rows(md);lookup={k.lower():v for k,v in tr};entries=[];missing=[]
 oldv={x['source_term'].lower():x for x in old['vocabulary']}
 for term in focus:
  definition=lookup.get(term.lower());table_term=term
  if definition is None:
   matches=[(k,v) for k,v in tr if C.同词(term,k)=='撞车']
   if len(matches)==1:table_term,definition=matches[0]
  definition_resolution='current manuscript exact term'
  if definition is None and term.lower() in meanings:
   components=[(k,v) for k,v in tr if k.lower() in {w.lower() for w in term.split()}]
   if components:
    definition='本文：'+'……'.join(dict.fromkeys(meanings[term.lower()]))+'；'+ '；'.join(v for k,v in components)
    definition_resolution='current Chinese phrase gloss plus component manuscript entries'
  if definition is None:missing.append(term);continue
  contextual=re.search(r'本文[:：]\s*([^；;]+)',definition)
  meaning=contextual.group(1).strip() if contextual else '……'.join(dict.fromkeys(meanings.get(term.lower(),[])))
  assert meaning,(no,term,'Missing current in-context meaning')
  pos=re.search(r'(?<![A-Za-z])(?:n\.|v\.|adj\.|adv\.|prep\.|pron\.|conj\.|num\.|art\.|interj\.|phr\.|[nv]\./[nv]\.)',definition)
  part=pos.group(0) if pos else ''
  if definition_resolution.startswith('current Chinese phrase'):part='短语'
  old_entry=oldv.get(term.lower(),{})
  if not part:part=old_entry.get('pos','表达')
  head=old_entry.get('headword',term)
  if table_term.lower()!=term.lower():head=table_term
  context=old_entry.get('context_phrase','')
  if context and context not in full:context=''
  if not old_entry:
   source_sentence=next(plain_en(' '.join(c['en'] for c in s['chunks'])) for s in d['sentences'] if term.lower() in [x.lower() for x in C.句重点词(s)])
   at=source_sentence.lower().find(term.lower())
   if at>=0:
    begin=source_sentence.rfind(' ',0,max(0,at-16))+1;end=source_sentence.find(' ',min(len(source_sentence),at+len(term)+20));end=len(source_sentence) if end<0 else end;context=source_sentence[begin:end]
   # Existing approved short source excerpts remain; new words get only a
   # short exact context, never repeated full sentences or invented examples.
   if len(context)>75:context=''
  entries.append({'source_term':term,'headword':head,'form_in_text':term,'pos':part,'meaning_zh':meaning,'current_table_definition':definition,'current_table_term':table_term,'definition_resolution':definition_resolution,'context_phrase':context})
 assert not missing,(no,'New focus absent from current vocabulary table',missing)
 assert len(entries)==len(focus)
 questions=copy.deepcopy(old['questions'])
 for q in questions:assert q['text_with_blank'].replace('______',q['answer']) in full,(no,'Old exercise no longer matches source',q)
 assert len(approved_summary)==5
 image=OLD/'illustrations'/('01-preview.png' if no=='01' else f'{no}.png');assert image.is_file()
 data={'id':f'{newid:02d}','source_id':no,'title_en':d['title_en'],'title_zh':d['title_zh'],'english_paragraphs':[' '.join(en_by[k]) for k in sorted(en_by)],'chinese_paragraphs':[''.join(zh_by[k]) for k in sorted(zh_by)],'english_markup_paragraphs':[' '.join(en_markup_by[k]) for k in sorted(en_markup_by)],'chinese_markup_paragraphs':[''.join(zh_markup_by[k]) for k in sorted(zh_markup_by)],'vocabulary':entries,'focus_occurrences':occurrences,'notes':notes,'approved_summary':approved_summary,'questions':questions,'cover_question':old['cover_question'],'illustration':str(image),'source_paths':{'JSON':str(sp),'GEN':str(gp),'MD':str(mdp)},'source_hashes':{'JSON':sha(sp),'GEN':sha(gp),'MD':sha(mdp),'illustration':sha(image)}}
 assert data['english_paragraphs']==[plain_en(x) for x in data['english_markup_paragraphs']]
 assert data['chinese_paragraphs']==[plain_zh(x) for x in data['chinese_markup_paragraphs']]
 # Preserve every source note exactly after only stripping its color directive
 # and separating the summary. No visible制作/流程文案 is invented here.
 assert sum(bool((c.get('note') or '').split('（简述：',1)[0].strip()) for s in d['sentences'] for c in s['chunks'])+inline_gloss_count==len(notes)
 for src in (sp,gp,mdp):
  dest=HERE/'source-snapshot'/no/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
 atom_write(HERE/'data'/f'{newid:02d}.json',data)
 return {'source_id':no,'new_id':data['id'],'title_zh':d['title_zh'],'focus_unique':len(focus),'focus_occurrences':len(occurrences),'notes':len(notes),'summary_points':5,'body_paragraphs':len(data['english_paragraphs']),'hashes':data['source_hashes']}

def main():
 C=checker();manifest=json.loads((HERE/'order-source.json').read_text());order=manifest['order_source_ids'];assert len(order)==70 and len(set(order))==70
 records=[];errors=[]
 for newid,no in enumerate(order,1):
  try:records.append(convert(no,newid,C))
  except Exception as exc:errors.append({'source_id':no,'new_id':f'{newid:02d}','type':type(exc).__name__,'error':str(exc)})
 result={'purpose':'Fresh book-content conversion from current PAY, not old PDF metadata substitution','source_root':str(PAY),'approved_style_root':str(OLD),'order_source_SHA256':sha(HERE/'order-source.json'),'target_repo_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'converted':records,'errors':errors,'complete':len(records)==70 and not errors,'artwork_reused_without_modification':True,'all_current_focus_terms_preserved':not errors,'all_current_notes_included':not errors,'old_source_9374187_used_for_body':False,'source_changed_since_last_build_check_required':True}
 atom_write(HERE/'conversion-report.json',result)
 print(json.dumps({'converted':len(records),'errors':errors,'complete':result['complete']},ensure_ascii=False))

if __name__=='__main__':main()
