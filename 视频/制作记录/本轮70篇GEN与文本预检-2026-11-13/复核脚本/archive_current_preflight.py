from pathlib import Path
import json,hashlib,datetime,shutil,sys
B=Path(__file__).resolve().parent;P=B/'payload';D=P/'视频/制作记录/本轮70篇GEN与文本预检-2026-11-13';D.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(B/'preflight-frozen66-v2-part1/mirror/视频/工具'));from 译文核查 import 去标
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();proof=json.loads((B/'actual-payload-gen-proof/report.json').read_text());pr={r['id']:r for r in proof['articles']};glob=json.loads((B/'final-global-readonly-text-checks.json').read_text());gr={r['id']:r for r in glob['articles']};candidates={}
for rp in B.glob('resumed-preflight-*/report.json'):
 report=json.loads(rp.read_text())
 for row in report['articles']:
  no=row['article'];src=P/f'视频/脚本/{no}.json'
  if row.get('text_exit')==0 and row.get('source_sha256')==sha(src):candidates.setdefault(no,[]).append((rp.stat().st_mtime,rp,report,row))
rows=[];overlay=(D/'原机械修后JSON供审阅');overlay.mkdir(exist_ok=True)
for i in range(1,71):
 no=f'{i:02}';assert no in candidates,no;_,rp,report,row=max(candidates[no],key=lambda x:x[0]);assert pr[no]['whole_JSON_exact']and pr[no]['source_sha256']==row['source_sha256'];assert not row['hard_errors']and not row['pending'];m=B/f'preflight-frozen66-v2-part{report["part"]}/mirror';assert all(sha(m/rel)==h for rel,h in report['core_hashes'].items())
 src=P/f'视频/脚本/{no}.json';repaired=rp.parent/f'auto-repaired-sources/{no}.json';assert repaired.exists();before=json.loads(src.read_text());after=json.loads(repaired.read_text());visible=[]
 for si,(sa,sb)in enumerate(zip(before['sentences'],after['sentences']),1):
  for ci,(ca,cb)in enumerate(zip(sa['chunks'],sb['chunks']),1):
   for field in ['en','zh','note']:
    if 去标(ca.get(field,''))!=去标(cb.get(field,'')):visible.append({'sentence':si,'chunk':ci,'field':field,'before':ca.get(field,''),'after':cb.get(field,'')})
 target=overlay/f'{no}.json';shutil.copyfile(repaired,target);rec=P/f'视频/制作记录/逐句确认/{no}.json'
 rows.append({'id':no,'current_source_sha256':sha(src),'current_actual_generator_sha256':sha(P/f'视频/工具/初稿生成/gen{no}.py'),'actual_existing_generator_whole_JSON_exact':True,'text_gate_exit':0,'hard_errors':[],'pending_confirmations':[],'full_original_text_gate_report':str(rp.relative_to(B)),'original_mechanical_repair_exit':row['repair_exit'],'mechanical_repair_differences':row['repair_differences'],'mechanical_repair_visible_word_differences':visible,'mechanically_repaired_overlay':str(target.relative_to(P)),'mechanically_repaired_sha256':sha(target),'confirmation_file_sha256':sha(rec)if rec.exists()else None,'current_manuscript_sha256':gr[no]['current_manuscript_sha256'],'current_pending_sha256':sha(P/f'视频/制作记录/{no}_待改清单.md')})
report={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'all70 frozen current PAY source hashes matched to actual original GEN/fullJSON proof, original 修.py and original 踩坑核查 CLI; extra final all70 current source/focus/T25 crosscheck','status':'passed','source_and_generators_frozen':True,'source_or_checker_changed_during_archive':False,'actual_existing_PAY_generators_exact_count':sum(r['whole_JSON_exact']for r in proof['articles']),'actual_original_text_gate_pass_count':len(rows),'global_current_readonly_checks_status':glob['status'],'helper_plain_English_diagnostics':{'count':proof['original_helper_diagnostic_count'],'cause':'old helper strips bold only; inline display/grammar gloss markers remain in JSON','official_render_strip_gloss_recheck':'all paragraphs equal after unchanged display-gloss removal and whitespace canonicalization; raw original helper logs preserved','real_visible_English_mismatches':0},'checker_changes':False,'repaired_JSONs_not_copied_into_production_source_by_preflight':True,'mechanical_overlays_need_parent_review_before_merging':True,'audio_video_or_PDF_produced_by_this_preflight':False,'pushed_or_dispatched':False,'confirmed_sentence_method':'Existing detailed body confirmations carried forward only where issued-body semantics unchanged; new keywords/notes reviewed specifically; all21–70 tails and parent-requested02 tail have actual detailed seven-item reviews including current T33. Fingerprints computed from actual original-repaired JSON, not stale request bytes.','articles':rows}
assert glob['status']=='passed';assert not any(r['mechanical_repair_visible_word_differences']for r in rows),[r['id']for r in rows if r['mechanical_repair_visible_word_differences']]
(B/'current70-final-preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');shutil.copyfile(B/'current70-final-preflight.json',D/'current70-final-preflight.json')
# Detailed historical attempts stay separated; final report above is the only current SHA verdict.
for folder in sorted(B.glob('resumed-preflight-*')):
 if not(folder/'report.json').exists():continue
 dest=D/'实际原程序运行记录'/folder.name;dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(folder/'report.json',dest/'report.json')
 if(folder/'logs').exists():shutil.copytree(folder/'logs',dest/'logs',dirs_exist_ok=True)
for folder in ['actual-payload-gen-proof','preflight20-alignment-overlay-review','preflight22-width-overlay-review']:
 src=B/folder;dest=D/'独立实测证据'/folder;dest.mkdir(parents=True,exist_ok=True)
 for pat in ['*.json','*.log','*.png']:
  for item in src.glob(pat):shutil.copyfile(item,dest/item.name)
 if(src/'logs').exists():shutil.copytree(src/'logs',dest/'logs',dirs_exist_ok=True)
for pattern in ['confirmation-tail-review-*.json','sentence-review-*.json','preflight-authorized*.json','preflight-actual-grammar-confirmations*.json','preflight-stale-summary-anchors.json','preflight-t25-minimal-data-proposals.json','preflight-latest-note-authorization-addendum.json','preflight20-*.json','preflight22-*.json','priority-five-frozen-source-manifest.json','final-global-readonly-text-checks.json']:
 for item in B.glob(pattern):shutil.copyfile(item,D/item.name)
for name in ['resume_actual_preflight.py','generator_text_preflight.py','prove_actual_payload_generators.py','final_global_readonly_checks.py','probe20_alignment_overlay.py','probe22_width_overlay.py','review_tail49_70.py','archive_current_preflight.py']:
 dst=D/'复核脚本'/name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(B/name,dst)
manifest={str(f.relative_to(D)):sha(f)for f in D.rglob('*')if f.is_file() and f.name!='archive-manifest.json'};(D/'archive-manifest.json').write_text(json.dumps({'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'file_count':len(manifest),'files':manifest},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'passed','all70_gen_exact':True,'all70_actual_text_gate_passed':True,'all70_final_source_focus_T25_passed':True,'mechanical_overlays_visible_word_changes':0,'archive':str(D.resolve()),'archived_files':len(manifest)},ensure_ascii=False))
