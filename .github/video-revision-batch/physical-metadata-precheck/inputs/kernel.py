"""Original A21 metadata-only kernel. No original function or threshold is changed."""
from pathlib import Path
import ast,contextlib,copy,gc,hashlib,io,json,sys,types
sys.dont_write_bytecode=True
A21_SHA='e64ed781a2e27991e3ff8aa97e41e1cc1bc09515a4f61cbc943fec27e0e41508'
PHYSICAL_KEYS=('title_en','title_fx','sentences','非人声区间','词尾除阻','除阻加强','停顿处除阻','停顿删除区间','停顿插入点','分段增益dB','句子增益dB','段内渐变dB','结尾句','合成标点','列举逗号','朗读删逗号')
BOOTSTRAP=ast.parse("exec(open('make_video.py').read().split(\"if __name__\")[0])").body[0]
def require(ok,msg):
    if not ok:raise AssertionError(msg)
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def typed(x):
    if isinstance(x,dict):return('dict',tuple((k,typed(v))for k,v in x.items()))
    if isinstance(x,list):return('list',tuple(typed(v)for v in x))
    return(type(x).__name__,x)
def difference(a,b,path=''):
    if type(a)is not type(b):return[{'path':path,'before':a,'after':b,'reason':'type'}]
    if isinstance(a,dict):
        out=[]
        for k in sorted(a.keys()|b.keys()):
            if k not in a or k not in b:out.append({'path':path+'/'+str(k),'before':a.get(k),'after':b.get(k),'missing_before':k not in a,'missing_after':k not in b})
            else:out+=difference(a[k],b[k],path+'/'+str(k))
        return out
    if isinstance(a,list)and len(a)==len(b):return sum((difference(x,y,path+'/'+str(i))for i,(x,y)in enumerate(zip(a,b))),[])
    return[]if a==b else[{'path':path,'before':a,'after':b}]
def physical_delta(a,b):return difference({k:a[k]for k in PHYSICAL_KEYS if k in a},{k:b[k]for k in PHYSICAL_KEYS if k in b})
def split_original_A21(text,actual_sha):
    require(actual_sha==A21_SHA and hashlib.sha256(text.encode()).hexdigest()==A21_SHA,'Wrong exact original A21 bytes')
    tree=ast.parse(text);xs=[(i,n)for i,n in enumerate(tree.body)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='exec']
    require(len(xs)==1 and ast.dump(xs[0][1],include_attributes=False)==ast.dump(BOOTSTRAP,include_attributes=False),'Unknown or extra original maker bootstrap statement')
    i=xs[0][0];left=ast.Module(body=tree.body[:i+1],type_ignores=tree.type_ignores);right=ast.Module(body=tree.body[i+1:],type_ignores=[])
    require(ast.dump(ast.Module(body=left.body+right.body,type_ignores=tree.type_ignores),include_attributes=False)==ast.dump(tree,include_attributes=False),'Entire original AST inverse failed')
    require({'check','sentence_items','nograft_items','write_grafts'}<={n.name for n in tree.body if isinstance(n,ast.FunctionDef)},'Original CLI function ABI changed')
    return left,right

def original_cli_preview(ns,no,data):
    rows,bad,info=ns['check'](no,data)
    result={'original_rows':rows,'original_bad':bad,'original_info':info,'original_bad_count':len(bad),'original_writer_invoked':False,'original_writer_count':0,'equivalent_original_CLI_exit':0}
    if bad:
        ns['sentence_items_cache']={lab:[cuts]for lab,text,out,starts,fin,cuts in ns['sentence_items'](data)}
        result['original_writer_invoked']=True;result['original_writer_count']=ns['write_grafts'](no,data,bad);result['equivalent_original_CLI_exit']=2
    return result

def preview(T,M,source,phase_result,observer,support,profile,events):
    """Same original CLI functions, private JSON only; no whole/dossier/gain calls."""
    T,M,source=map(Path,(T,M,source));W=M/'video';no=profile['source_id'];cache=M/'tts/cache_tts';checker=T/'词尾辅音核对.py';left,right=split_original_A21(checker.read_text(),digest(checker));before=json.loads(source.read_text());require(str(before['no'])==no,'Wrong source id');require(phase_result['source_sha256']==digest(source),'Private whole phase source differs')
    require(not phase_result['actual_voice_fingerprint_table']['作废'],'A45 invalidation must be resolved first')
    actual_work=W/('work_'+no)
    require(digest(actual_work/'a.wav')==phase_result['actual_complete_WAV']['file_sha256'],'Original A21 must read the same-job selected WAV at its actual work path')
    require(json.loads((actual_work/'分段.json').read_text())==phase_result['actual_original_piece_time_table']and json.loads((actual_work/'句子声音指纹.json').read_text())==phase_result['actual_voice_fingerprint_table'],'Original A21 selected metadata role differs')
    r={'restoration':{},'quality_acceptance':False,'only_original_A21_check_and_writegrafts_executed':True};m=None;restore=None;original_methods=[];native_cells=[];level=None;saved_modules={};log=io.StringIO()
    try:
        with support.environment_and_cwd(W,r['restoration']):
            with support.source_namespace(W,source.read_bytes(),r['restoration']):
                for name in ('render','title2','clean','出片指纹'):saved_modules[name]=sys.modules.get(name);sys.modules.pop(name,None)
                name='_actual_original_A21_private_'+no;m=types.ModuleType(name);m.__file__=str(checker);sys.modules[name]=m
                # Execute the exact original imports and unique bootstrap once, then
                # insert inference guards before the original remaining definitions.
                exec(compile(left,str(checker),'exec'),m.__dict__)
                require(Path(m._CACHE).resolve()==cache.resolve(),'Wrong original cache directory')
                require(m._OLDF and digest(m._OLDF)==observer.OLD_REGISTRY_SHA256 and digest(m._CTX_PATH)==profile['context_SHA256']and digest(m._cand)==observer.DICT_SHA256,'Wrong G72/dictionary/context')
                m._SPOKEN_SOURCE_NO=no;m._REPO_CACHE=str(M/('forbid-A21-metadata-public-export-'+no));require(not Path(m._REPO_CACHE).exists(),'Private export sentinel must be absent')
                for obj,method in[(m.k,'create'),(m.k,'create_timed'),(m.KT,'create'),(m.KT,'create_timed')]:original_methods.append((obj,method,getattr(obj,method)))
                for obj,method in[(m.k,'create'),(m.KT,'create_timed')]:
                    cached=support.closure_cell(getattr(obj,method),'fn').cell_contents
                    cell=support.closure_cell(cached,'fn');native_cells.append((cell,cell.cell_contents))
                restore=observer.block_native(m,support,events);counts={'cached_model_calls':0};used={}
                for method,obj,model in[('create',m.k,'kokoro-v1.0.onnx'),('create_timed',m.KT,'kokoro-v1.0-timed.onnx')]:setattr(obj,method,observer.strict_cached_guard(m,m.np,cache,method,model,getattr(obj,method),used,counts))
                level=m._auto_level
                def forbid_G36(*a,**kw):raise AssertionError('No G36 call is part of original A21 metadata-only kernel')
                m._auto_level=forbid_G36
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                    exec(compile(right,str(checker),'exec'),m.__dict__)
                    result=original_cli_preview(m.__dict__,no,copy.deepcopy(before))
                after_raw=(W/f'scripts/{no}.json').read_bytes();after=json.loads(after_raw)
                r.update(result);r.update(full_source_JSON_delta=difference(before,after),actual_physical_audio_source_delta=physical_delta(before,after),private_after_source_JSON=after,private_after_source_SHA256=hashlib.sha256(after_raw).hexdigest(),original_preview_log=log.getvalue(),cached_model_calls=counts['cached_model_calls'],actual_used_existing_cache_entries=list(used.values()))
                for i,s in enumerate(before['sentences'],1):
                    text=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in s['chunks']);require(m.SENT_FP.get(text)==phase_result['actual_voice_fingerprint_table']['指纹'].get('S'+str(i)),'Actual cached raw fingerprint differs from just-proved phase: S'+str(i))
                require(not m.VOIDED,'A45 invalidation during original A21 preview')
                r['all_raw_fingerprints_match_actual_samejob_whole']=True
    finally:
        if m is not None and level is not None:m._auto_level=level;r['restoration']['original_level_method_restored']=m._auto_level is level
        try:
            if restore is not None:restore()
        finally:
            for obj,method,value in original_methods:setattr(obj,method,value)
            for cell,value in native_cells:cell.cell_contents=value
            r['restoration']['all_original_cached_object_methods_restored']=bool(original_methods)and all(getattr(obj,method)is value for obj,method,value in original_methods)
            r['restoration']['all_original_native_closure_cells_restored']=bool(native_cells)and all(cell.cell_contents is value for cell,value in native_cells)
        for name,value in saved_modules.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value
        if m is not None:sys.modules.pop(m.__name__,None);del m;gc.collect()
    require(all(r['restoration'].get(k)is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','original_level_method_restored','all_original_cached_object_methods_restored','all_original_native_closure_cells_restored']),'A21 private namespace/method restoration failed')
    r['physical_audio_fields_would_change']=bool(r['actual_physical_audio_source_delta']);r['original_A21_no_bad_and_physical_fields_unchanged']=not r['original_bad_count']and not r['physical_audio_fields_would_change']
    return r
