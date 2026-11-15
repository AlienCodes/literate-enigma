"""CODE-ONLY proposal: actual certified stock programs; no core repair or media pass.
ROOT must review before any real caller uses this module.
"""
from pathlib import Path
import ast,glob,hashlib,json,os,re,shutil
SOURCE_ID='58'
BOOK_ORDER=67
PROFILE_FOLDER='stock-certified58'
PROFILE_KIND='actual-original-stock109-plus-exact-single-reference-raw-cache-IO-full110-profile'
PROFILE_SHA='d53a780360169676d43b739215c1880f0e44b67f8cc07ba61398df3ffed851f2'
EXPECTED_CHANGED_PROGRAMS=('独立复核/synth.py',)
INSTALL_TARGETS=('视频/工具/独立复核/synth.py', '视频/工具/新管/回归基准_27.json', '视频/工具/新管/快测通过.json')

def require(ok,message):
    if not ok:raise ValueError(message)

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def typed(value):
    if isinstance(value,dict):return ('dict',tuple(sorted((k,typed(v))for k,v in value.items())))
    if isinstance(value,list):return ('list',tuple(typed(v)for v in value))
    return (type(value).__name__,value)

def validate_inventory(expected,observed):
    require(len(expected)==len(observed)==110,'Exact actual 110 stock program names required')
    require(typed(expected)==typed(observed),'Full actual program SHA/bytes or inventory differs')

def validate_environment(env,has_core_manifest):
    require(not has_core_manifest,'Target source stock role forbids certified-core manifest')
    require(not any(k.startswith('XG_KEEP_REVIEWED_')for k in env),'Original target source stock role forbids every KEEP flag')
    require(env.get('STRICT_CACHE')=='1','Original strict cache is required')
    require(str(env.get('ARTICLE_NO',SOURCE_ID)).zfill(2)==SOURCE_ID,'Target source-only profile')

def inventory(tools,profile):
    tools=Path(tools);verifier=tools/'新管/印章.py'
    require(digest(verifier)==profile['original_stamp_verifier_SHA256'],'Original stamp verifier differs')
    tree=ast.parse(verifier.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='程序哈希']
    require(len(nodes)==1,'Original stamp inventory function missing')
    # Execute only the unchanged original pure file-hash function. No module main,
    # models, voice, quickcheck, stamp writer or source processing is executed.
    namespace={'T':str(tools),'H':str(tools/'新管'),'os':os,'glob':glob,'hashlib':hashlib,'re':re}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(verifier),'exec'),namespace)
    names=namespace['程序哈希']()
    result={}
    for name in names:
        rel=Path(name);require(not rel.is_absolute()and '..'not in rel.parts,'Invalid original program path')
        f=tools/rel;result[name]={'bytes':f.stat().st_size,'sha256':digest(f)}
    return result

def read_contract(task):
    folder=Path(task)/PROFILE_FOLDER;p=folder/'profile.json'
    require(digest(p)==PROFILE_SHA,'Exact ROOT-reviewed stock-role code profile differs')
    profile=json.loads(p.read_text())
    require(profile['kind']==PROFILE_KIND and profile['source_id']==SOURCE_ID and profile['book_order']==BOOK_ORDER,'Wrong stock profile role')
    require(profile['mode_environment']=={}and profile['certified_core_overlay_permitted']is False,'No core/KEEP overlays permitted')
    for item in profile['files'].values():
        f=folder/item['file'];require(f.stat().st_size==item['bytes']and digest(f)==item['sha256'],'Actual certified input bytes differ: '+item['file'])
    cert=json.loads((folder/'files/certification.json').read_text())
    for field,want in profile['certificate_requirements']:
        actual=cert
        for part in field.split('/'):
            actual=actual[part]
        require(typed(actual)==typed(want),'Actual native certificate field differs: '+field)
    inv=json.loads((folder/'files/full110-inventory.json').read_text())
    before={r['path']:{'bytes':r['bytes'],'sha256':r['sha256']}for r in inv['stock_files']}
    after={r['path']:{'bytes':r['bytes'],'sha256':r['sha256']}for r in inv['expected_after_only_renderer']}
    require(set(before)==set(after)and len(before)==110,'Actual110 inventory names differ')
    require(tuple(k for k in before if before[k]!=after[k])==EXPECTED_CHANGED_PROGRAMS,'Only explicitly adopted program bytes may differ from stock')
    stamp=json.loads((folder/'files/real-fastcheck-stamp.json').read_text())
    require(stamp['程序']=={k:v['sha256'][:16]for k,v in after.items()},'Real stamp must match full110 exact hashes')
    require(cert['real_fastcheck_stamp_SHA256']==digest(folder/'files/real-fastcheck-stamp.json'),'Actual native stamp hash mismatch')
    return folder,profile,before,after

def verify_installed(root,task,env):
    root=Path(root);folder,profile,before,after=read_contract(task)
    validate_environment(env,(Path(task)/'certified-core/manifest.json').exists())
    observed=inventory(root/'视频/工具',profile);validate_inventory(after,observed)
    require(digest(root/'视频/工具/新管/快测通过.json')==profile['files']['real-fastcheck-stamp.json']['sha256'],'Installed actual stamp differs')
    require(digest(root/'视频/工具/新管/回归基准_27.json')==profile['files']['regression27.json']['sha256'],'Original reviewed regression27 differs')
    data=json.dumps(observed,sort_keys=True,separators=(',',':')).encode()
    return {'stock_code_profile_SHA256':PROFILE_SHA,'actual_complete_program_inventory_SHA256':hashlib.sha256(data).hexdigest(),'actual_program_count':110,'actual_native_stock_code_certification':profile['actual_native_certification'],'stock_mode_environment':{},'core_repairs_applied':False,'original_maker_unchanged':True,'production_audio_or_video_acceptance':False}

def install(root,task,env,status,checked,save):
    root=Path(root);task=Path(task);folder,profile,before,after=read_contract(task)
    validate_environment(env,(task/'certified-core/manifest.json').exists())
    validate_inventory(before,inventory(root/'视频/工具',profile))
    request=task/'request'/SOURCE_ID
    for rel,want in profile['source_file_specs'].items():
        f=request/rel;require(f.stat().st_size==want['bytes']and digest(f)==want['sha256'],'Exact adopted64 source inputs differ: '+rel)
    require({i['target']for i in profile['install_only']}==set(INSTALL_TARGETS),'Only explicitly reviewed certified resource targets may be copied')
    for item in profile['install_only']:
        source=folder/item['file'];target=root/item['target']
        require(digest(source)==item['sha256'],'Exact install payload differs')
        shutil.copyfile(source,target)
    record=verify_installed(root,task,env)
    # No --自动 or --盖: use the unchanged original read-only stamp checker.
    checked(['python3',root/'视频/工具/新管/印章.py'],'stock'+SOURCE_ID+'-original-real-stamp-verification.log')
    status['stock_code_profile']=record
    status['actual_native_stock_code_certification']=profile['actual_native_certification']
    status['actual_native_fastcheck_stamp']={'target':'视频/工具/新管/快测通过.json','sha256':profile['files']['real-fastcheck-stamp.json']['sha256'],'origin':'actual original stock full110 run'+str(profile['actual_native_certification']['run_id'])}
    status['reviewed_regression_resource']={'target':'视频/工具/新管/回归基准_27.json','sha256':profile['files']['regression27.json']['sha256'],'origin':'actual certified original regression27 resource'}
    save()
    return record
