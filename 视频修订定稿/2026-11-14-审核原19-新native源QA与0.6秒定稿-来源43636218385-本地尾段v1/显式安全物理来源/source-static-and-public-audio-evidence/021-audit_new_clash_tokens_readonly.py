from pathlib import Path
import ast,copy,hashlib,json,re
O=Path(__file__).parent;B=Path('/workspace/work/video-audit70-20261113');T=Path('/dev/shm/article07-user-review-draft-20261114/thin-validation-v1/mirror/视频/工具/check_all.py');tree=ast.parse(T.read_text());functions={'stem','旧键','单CVC','词基','_同','词','实词','_小品','原有','同词','ckey','_加粗','句重点词'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in functions];ns={'re':re}
for name in['STOP','虚词']:
 n=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets));ns[name]=ast.literal_eval(n.value)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(T)+'#original-functions-only','exec'),ns)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();context={};origins=[]
for no in range(1,71):
 k=f'{no:02}';p=B/'payload/视频/脚本'/f'{k}.json'
 if not p.exists():p=B/'preflight-frozen66-v2-part1/mirror/视频/脚本'/f'{k}.json'
 d=json.loads(p.read_text());context[k]=d;origins.append({'source_id':k,'path':str(p),'sha256':sha(p)})
# Supplement the two later exact frozen RAM manuscripts, without touching PAY or the originals.
for k,p in [('07',Path('/dev/shm/article07-user-review-draft-20261114/candidate-payload/视频/脚本/07.json')),('60',B/'payload/视频/脚本/60.json')]:
 if p.exists():context[k]=json.loads(p.read_text());next(x for x in origins if x['source_id']==k).update(path=str(p),sha256=sha(p))
a=json.loads((O/'candidate-payload/视频/脚本/19.json').read_text());units=list(dict.fromkeys(x for s in a['sentences']for x in ns['句重点词'](s)));newunits=['skilled','craftsman','Scottish','casting as'];rows=[]
for token in['skilled','craftsman','Scottish','casting as','casting','as']:
 raw=[];gate=[]
 for k,d in context.items():
  if k=='19':continue
  terms=list(dict.fromkeys(x for s in d['sentences']for x in ns['句重点词'](s)));excluded={x.lower()for x in d.get('allow_clash',[])}
  for term in terms:
   legacy=ns['旧键'](token)and ns['旧键'](token)==ns['旧键'](term);current=ns['同词'](token,term)
   if legacy or current:
    x={'source_id':k,'other_term':term,'legacy_source19_gate_match':bool(legacy),'current_inflection_comparison':current,'other_article_original_allow_clash_excludes_it_from_gate':term.lower()in excluded};raw.append(x)
    if legacy and term.lower()not in excluded and token in newunits:gate.append(x)
 rows.append({'token':token,'recognized_as_independent_final_focus_unit':token in units,'part_of_complete_phrase_only':token in['casting','as'],'actual_raw_focused_duplicates_across_other69':raw,'actual_legacy_source19_guard_hits_without_new_allow':gate})
r={'source_id':'19','kind':'read-only-actual-original-G32-new-token-minimum-allowance-audit','original_check_all_path':str(T),'original_program_sha256':sha(T),'all70_context_count':len(context),'context':origins,'actual_new_units_recognized_by_original_K119_phrase_merger':[x for x in units if x in newunits],'candidate_new_allow6':a.get('allow_clash'), 'per_token':rows,'minimum_new_allow_required_by_original_source19_gate':[x['token']for x in rows if x['actual_legacy_source19_guard_hits_without_new_allow']],'allow_clash_not_a_color_override':True,'all_existing_other_article_focus_and_allow_metadata_untouched':True}
p=O/'actual-new-focus-clash-audit.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':sha(p),'minimum':r['minimum_new_allow_required_by_original_source19_gate'],'newunits':r['actual_new_units_recognized_by_original_K119_phrase_merger'],'rows':rows},ensure_ascii=False))
