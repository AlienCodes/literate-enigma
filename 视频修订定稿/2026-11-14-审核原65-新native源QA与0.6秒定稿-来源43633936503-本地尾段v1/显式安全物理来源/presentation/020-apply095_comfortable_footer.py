"""Use source65's existing per-sentence font cap for user095's comfortable centered last page."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
H=Path(__file__).resolve().parent;B=Path('/workspace/work/video-audit70-20261113');C=H/'candidate-payload';hist=H/'history094-before095-footer';hist.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for rel,name in [('视频/脚本/65.json','source.json'),('视频/工具/初稿生成/gen65.py','GEN.py')]:assert not(hist/name).exists();shutil.copyfile(C/rel,hist/name)
old=json.loads((hist/'source.json').read_text());new=copy.deepcopy(old);assert '字号上限'not in new;new['字号上限']={'S17':88}
assert {k:v for k,v in old.items()}=={k:v for k,v in new.items()if k!='字号上限'}
p=C/'视频/脚本/65.json';p.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');s=importlib.util.spec_from_file_location('original65encoder095',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P);code,issues=P.pure_generator(new);assert code and not issues;(C/'视频/工具/初稿生成/gen65.py').write_text(code)
r={'article':'65','book_order':'37','kind':'user095_last_page_comfortable_font_and_centering','actual_original_renderer_centers_total_content':True,'original_MAXH2_per_1080':1020,'old_natural_body_font_px_per_1080':96,'old_total_height_px_per_1080':1020,'new_original_native_font_cap_S17_per_1080':88,'other_sentences_no_font_change':True,'only_add_source_font_cap_using_existing_original_maker_support':True,'all_body_align_notes_summary_and_audio_controls_exact':True,'no_new_inline_summary_or_removed_grammar':True,'source_before_sha256':sha(hist/'source.json'),'source_after_sha256':sha(p),'GEN_after_sha256':sha(C/'视频/工具/初稿生成/gen65.py'),'MD_unchanged_sha256':sha(C/'新版定稿/65-the-day-the-doomsday-vault-opened.md'),'source_delta':P.differences(old,new),'PDF_native_audio_video_PAY_CI_unmodified':True}
(H/'user095-footer-implementation-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='source_delta'},ensure_ascii=False))
