"""Article28 hold18 ABI and actual small-media decoder tests, never delivery claims."""
from pathlib import Path
from types import SimpleNamespace
import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys

H = Path(__file__).parent
OLD = H.parent / 'hold9-integrator/illustrated_tail.py'
P = H / 'illustrated_tail.py'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location('hold18_isolated', P)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
rows = []

def check(name, args, timing, frames, expected):
    try:
        result = M.preview_hold_contract(SimpleNamespace(source_id=args[0], preview_last_body_hold_frames=args[1], validation_fixture=args[2]), timing, frames)
        accepted, error = True, None
    except Exception as exc:
        result, accepted, error = None, False, str(exc)
    assert accepted is expected, (name, accepted, error)
    rows.append(dict(name=name, expected_accept=expected, actual_accept=accepted, return_value=result, error=error, kind='unit_contract_not_native_media'))

t = dict(kind='preview-last-body-hold18-then-summary60', preview_only=True, preview_last_body_hold_frames=18, source_voice_endpoint_seconds=157.33)
check('actual_28_voice157_33_ceil4720_plus18', ('28',18,False), t, 4738, True)
for sid in ['01','14','17','27','29','70']:
    check('wrong_source_'+sid, (sid,18,False), t,4738,False)
for hold in [9,17,19,8,10,-1,.6,'18',True]:
    check('invalid_hold_'+repr(hold), ('28',hold,False),t,4738,False)
for key,value in [('kind','preview-last-body-hold9-then-summary60'),('kind','immediate-standalone-summary'),('preview_only',False),('preview_only',1),('preview_last_body_hold_frames',9),('preview_last_body_hold_frames',17),('preview_last_body_hold_frames',True)]:
    q=copy.deepcopy(t);q[key]=value
    check('wrong_declaration_'+key+'_'+str(value),('28',18,False),q,4738,False)
check('synthetic_cannot_be_delivery',('28',18,True),t,4738,False)
for frames in [4729,4737,4739,4747]:
    check('wrong_actual_boundary_'+str(frames),('28',18,False),t,frames,False)
check('preview_requires_explicit_cli',('28',0,False),t,4738,False)
for gap in [0,.005,1/30-.0000001]:
    check('legacy_default_immediate_'+str(gap),('53',0,False),dict(kind='immediate-standalone-summary',source_voice_endpoint_seconds=.4-gap),12,True)
check('legacy_default_reject_hold',('53',0,False),dict(kind='immediate-standalone-summary',source_voice_endpoint_seconds=.1),12,False)
check('legacy_synthetic_unchanged',('01',0,True),dict(source_voice_endpoint_seconds=.395),12,True)
old_tree=ast.parse(OLD.read_text());new_tree=ast.parse(P.read_text())
oldf={n.name:n for n in old_tree.body if isinstance(n,ast.FunctionDef)}
newf={n.name:n for n in new_tree.body if isinstance(n,ast.FunctionDef)}
assert oldf.keys()==newf.keys()
changed=[name for name in oldf if ast.dump(oldf[name])!=ast.dump(newf[name])]
assert set(changed)=={'preview_hold_contract','verify_preview_hold','provenance','main'},changed
unchanged=[name for name in oldf if name not in changed]
assert sha(OLD)=='f90e399b59ec5d1c7bc83a9d8c4c0134b7ba4dbe1627a2bde6ab91daa6c06562'

# Tiny encoded files exercise the real ffmpeg decode/count/pixel path.
# These contain diagnostic solid frames, never source28 production evidence.
w,h=M.THUMB
blue=bytes([12,45,78])*(w*h)
red=bytes([240,35,40])*(w*h)
media=[]
def encoded(name, frames):
    p=H/(name+'.mp4')
    subprocess.run(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r','30','-i','pipe:0','-an','-c:v','libx264','-threads','1','-crf','10','-pix_fmt','yuv420p',str(p)],input=b''.join(frames),check=True)
    return p
for name,frames,expected in [
    ('decoder19_actual_same_page',[blue]*19,True),
    ('decoder19_actual_last_hold_changed',[blue]*18+[red],False),
    ('decoder19_actual_first_hold_changed',[blue,red]+[blue]*17,False),
    ('decoder18_actual_missing_hold',[blue]*18,False),
]:
    p=encoded(name,frames)
    try:
        result=M.verify_preview_hold(p,19)
        accepted,error=True,None
    except Exception as exc:
        result,accepted,error=None,False,str(exc)
    assert accepted is expected,(name,accepted,error)
    media.append(dict(name=name,kind='actual_small_encoded_decoder_diagnostic_not_native',expected_accept=expected,actual_accept=accepted,error=error,actual_decoded_test_frame_count=len(frames),test_video_sha256=sha(p),path=str(p),result=result))

report=dict(passed=True,kind='isolated_article28_hold18_contract_and_real_decoder_diagnostics',program_sha256=sha(P),old_hold9_program_sha256=sha(OLD),old_hold9_unchanged=True,only_function_changes=changed,unchanged_functions_AST_exact=unchanged,unit_and_scope_tests=rows,actual_encoded_decoder_tests=media,test_count=len(rows)+len(media),exact_held_frames=18,exact_reference_plus_hold_decode_count=19,actual_28_endpoint_seconds=157.33,actual_28_speech_ceiling_frame=4720,authorized_target_body_frames=4738,default0_contract_and_original_body_AAC_clock_checks_unchanged=True,preview_only=True,production_delivery_eligible=False,real_new_native_preview_positive_pending=True,no_formal_production_pass_claimed=True)
out=H/'hold18-contract-and-actual-decoder-tests.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=True,tests=report['test_count'],program_sha256=sha(P),report=str(out),report_sha256=sha(out))))
