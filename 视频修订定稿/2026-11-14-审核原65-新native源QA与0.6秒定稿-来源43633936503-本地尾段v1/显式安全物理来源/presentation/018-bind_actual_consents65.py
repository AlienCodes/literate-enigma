"""Replace the original splitter's generic old consent pointer with exact current user quotes."""
import copy,hashlib,importlib.util,json,shutil
from pathlib import Path
H=Path(__file__).resolve().parent;B=Path('/workspace/work/video-audit70-20261113');C=H/'candidate-payload';V=H/'thin-validation';hist=H/'history091093-original-generic-consent-v2';hist.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for rel,name in [('视频/脚本/65.json','source.json'),('视频/工具/初稿生成/gen65.py','GEN.py'),('新版定稿/65-the-day-the-doomsday-vault-opened.md','manuscript.md')]:assert not(hist/name).exists();shutil.copyfile(C/rel,hist/name)
shutil.copyfile(V/'report.json',hist/'original-text-failure-report.json');shutil.copytree(V/'logs',hist/'original-text-failure-logs')
p=C/'视频/脚本/65.json';old=json.loads(p.read_text());new=copy.deepcopy(old)
for sid,number in [('S1',91),('S11',93)]:
 rp=Path('/workspace/work/first50-review-release')/f'USER-REVIEW-2026-11-14-{number:03}.json';r=json.loads(rp.read_text());assert r['source_id']=='65'and r['book_order']=='37'
 new['换行变更已获同意'][sid]='用户 2026-11-14 原话：“'+r['user_instruction_verbatim']+'”（本次仅将用户点名的国家名标注为独立重点；原T34拆分组机械拆开同序重点的align，连续中英文和原小字均不改。实施说明不作为用户逐字话。）'
assert all(old[k]==new[k]for k in old if k!='换行变更已获同意')
p.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');s=importlib.util.spec_from_file_location('original65encoder_realconsent',B/'generator_text_preflight.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P);code,issues=P.pure_generator(new);assert code and not issues;(C/'视频/工具/初稿生成/gen65.py').write_text(code)
report={'article':'65','book_order':'37','draft_only':True,'old_generic_splitter_quote_not_in_current_consent_failure_preserved':True,'exact_user091_and093_quotes_bound':True,'only_two_consent_pointer_strings_changed':True,'bare_EN_Chinese_align_notes_summary_audio_all_exact':True,'source_before_sha256':sha(hist/'source.json'),'source_after_sha256':sha(p),'GEN_after_sha256':sha(C/'视频/工具/初稿生成/gen65.py'),'MD_unchanged_sha256':sha(C/'新版定稿/65-the-day-the-doomsday-vault-opened.md'),'delta':P.differences(old,new),'no_original_rule_or_core_change':True}
(H/'actual091093-consent-pointer-reconciliation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='delta'},ensure_ascii=False))
