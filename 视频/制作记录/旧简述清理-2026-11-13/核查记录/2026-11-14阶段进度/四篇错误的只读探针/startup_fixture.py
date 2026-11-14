"""Synthetic in-memory gate only: verify opt-in startup hook, not real article audio."""
import ast,json
from pathlib import Path
import os,sys
import numpy as np
assert sys.gettrace() is not None,'Opt-in sitecustomize was not installed.'
import safe_scalar_probe as P
P._state['fixture_only']=True;P._state['synthetic_validation_fixture']=True
maker=Path(os.environ['VIDEO_SAFE_SCALAR_MAKER']);tree=ast.parse(maker.read_text())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_env5','_像吸气帧','_nonvoice'}]
space={'np':np,'SR':24000,'AUD_DB':-55}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'native-original-AST-startup-fixture','exec'),space)
d=json.loads(Path(os.environ['VIDEO_SAFE_SCALAR_SOURCE']).read_text())
label=' '.join(__import__('re').sub(r'\{\{.*?\}\}','',c['en']).replace('**','').strip() for c in d['sentences'][18]['chunks'])
x=np.zeros(24000);x[18000:18120]=1.0
try:space['_nonvoice'](x,[[.02,1.5]],label)
except SystemExit:print('Original synthetic invalid-bounds exception preserved; opt-in hook observed safe scalars.')
else:raise RuntimeError('Unchanged native failure was lost.')
assert P._state['observations'][-1]['original_failure_predicates']['invalid_interval_bounds']is True
