import re
STATUS='^(?:Git API (?:GET|POST) failed status |Blob POST failed status )([1-5][0-9]{2}); no ref progression$'
STATUS=re.compile(STATUS)
def safe_chain(error,guard_type):
 rows=[];seen=set()
 while error is not None and id(error)not in seen and len(rows)<8:
  seen.add(id(error));status=None
  if isinstance(error,guard_type):
   match=STATUS.fullmatch(str(error))
   if match:status=int(match.group(1))
  rows.append({'class':type(error).__name__,'HTTP_status_from_exact_owned_template':status})
  error=error.__context__
 return rows

def safe_stage(stage):
 if not isinstance(stage,dict):return None
 method=stage.get('method');endpoint=stage.get('git_endpoint');result={}
 if method in {'GET','POST'}:result['method']=method
 if isinstance(endpoint,str):
  for prefix in ['git/blobs','git/trees','git/commits','git/refs','git/ref/heads']:
   if endpoint==prefix or endpoint.startswith(prefix+'/'):
    result['Git_endpoint_category']=prefix;break
 sha=stage.get('expected_git_blob_sha')
 if isinstance(sha,str)and re.fullmatch('[0-9a-f]{40}',sha):result['expected_git_blob_sha']=sha
 return result or None
