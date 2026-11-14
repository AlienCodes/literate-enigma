"""Apply user094 exact last-body translation; retain the standalone summary and voice controls."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
H=Path(__file__).resolve().parent;B=Path('/workspace/work/video-audit70-20261113');C=H/'candidate-payload';hist=H/'history091093-before094';hist.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for rel,name in [('视频/脚本/65.json','source.json'),('视频/工具/初稿生成/gen65.py','GEN.py'),('新版定稿/65-the-day-the-doomsday-vault-opened.md','manuscript.md')]:assert not(hist/name).exists();shutil.copyfile(C/rel,hist/name)
old=json.loads((hist/'source.json').read_text());new=copy.deepcopy(old);c=new['sentences'][16]['chunks'][1]
assert c['align'][1]==['and','而'];c['align'][1][1]='并且';c['zh']=''.join(b for a,b in c['align'])
assert '而建的' in new['sentences'][16]['chunks'][0]['zh']
assert all(old[k]==new[k]for k in old if k!='sentences')
for i,(a,b)in enumerate(zip(old['sentences'],new['sentences'])):
 if i!=16:assert a==b
 else:
  assert a['chunks'][0]==b['chunks'][0]
  assert a['chunks'][1]['en']==b['chunks'][1]['en']and a['chunks'][1]['note']==b['chunks'][1]['note']
p=C/'视频/脚本/65.json';p.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');s=importlib.util.spec_from_file_location('orig65encoder094',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P);code,issues=P.pure_generator(new);assert code and not issues;(C/'视频/工具/初稿生成/gen65.py').write_text(code)
md=C/'新版定稿/65-the-day-the-doomsday-vault-opened.md';t=md.read_text();a=old['sentences'][16]['chunks'][1]['zh'];b=c['zh'];assert t.count(a)==1;t=t.replace(a,b,1);md.write_text(t)
r={'article':'65','book_order':'37','kind':'user094_exact_last_body_translation_applied_pending_audio_and_final_freeze','final_authorization_received_via_root_user094095':True,'last_ordinary_and_Chinese':'而→并且','first_chunk_而建的_preserved':True,'all_bare_English_chunks_notes_summary_and_audio_controls_preserved':True,'new_inline_summary_added':False,'standalone_original_five_point_summary_preserved':True,'old_actual_summary_4K_font_px':113,'source_sha256':sha(p),'GEN_sha256':sha(C/'视频/工具/初稿生成/gen65.py'),'MD_sha256':sha(md),'exact_delta':P.differences(old,new),'production_PAY_CI_native_audio_video_PDF_unchanged':True,'user094095_exact_public_ledger_binding_pending_before_final_freeze':True}
(H/'user094-content-implementation-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='exact_delta'},ensure_ascii=False))
