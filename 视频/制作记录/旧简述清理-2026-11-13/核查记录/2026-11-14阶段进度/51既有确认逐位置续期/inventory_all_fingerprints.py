"""Inventory every51 whole-PCM fingerprint; preserve exact proof boundaries."""
from pathlib import Path
import hashlib,json,re,collections
import numpy as np
import soundfile as sf
B=Path('/workspace/work/video-audit70-20261113');O=B/'audio51-remaining-edits'
SOURCE=B/'payload/视频/脚本/51.json';WORKING=B/'ci-direct-43526354790-51/51-failed-working-source.json';STATUS=B/'ci-direct-43526354790-51/51-status.json';PROOF=B/'ci-direct-43526354790-51/51-failed-draft-proof.json';DIAG=B/'readonly-audio-replay-43528832985/51-reference-gain-diagnostic.json'
source=json.loads(SOURCE.read_text());working=json.loads(WORKING.read_text());status=json.loads(STATUS.read_text());proof=json.loads(PROOF.read_text());diag=json.loads(DIAG.read_text());fp=diag['official_abnormal_edit_scalars']['current_pcm_md5_first12']
assert hashlib.sha256(WORKING.read_bytes()).hexdigest()==proof['source_sha256']
assert proof['internal_pcm_sha256']==diag['wav_sha256']
old,sr=sf.read(B/'audio51-independent/51-accepted-decoded.wav',dtype='float64');new,sr2=sf.read(B/'audio51-independent/51-failed-decoded.wav',dtype='float64');assert sr==sr2==48000
asr=json.loads((O/'51-existing-ASR-confirmation-continuity.json').read_text());edit=json.loads((O/'51-remaining-edit-proof.json').read_text());asr_rows={r['sentence']:r for r in asr['rows']};edit_rows={r['exact_source_key']:r for r in edit['rows']}
seg=diag['public_producer_timing_metadata']['segments'];rows=[];renew={};pending=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ah(a):return hashlib.sha256(np.ascontiguousarray(a,dtype=np.float64).tobytes()).hexdigest()
def compare(lo,hi):
 a=old[round(lo*sr):round(hi*sr)];b=new[round(lo*sr):round(hi*sr)];g=float(a@b/(a@a+1e-30));r=b-g*a
 eq=bool(np.array_equal(a,b) and ah(a)==ah(b))
 return {'actual_public_seconds':[lo,hi],'decoded_sample_rate':sr,'decoded_dtype':'float64','sample_count':len(a),'whole_region_bit_identical':eq,'accepted_crop_sha256':ah(a),'actual_crop_sha256':ah(b),'different_sample_count':int(np.count_nonzero(a!=b)),'maximum_absolute_sample_difference':float(np.max(abs(a-b))),'gain_db':float(20*np.log10(abs(g)+1e-30)),'correlation':float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)+1e-30)),'residual_snr_db':None if eq else float(10*np.log10((np.mean((g*a)**2)+1e-30)/(np.mean(r*r)+1e-30)))}
actual_purevoice_lines=[line for lines in status.get('failure_details',{}).get('public_checker_diagnostics',{}).values() if isinstance(lines,list) for line in lines if isinstance(line,str) and line.startswith('✔ 纯人声核对') and '问题数 0' in line]
assert actual_purevoice_lines
for category,items in source['核对确认'].items():
 if not isinstance(items,dict):continue
 for key,entry in items.items():
  if not isinstance(entry,dict) or '配音指纹' not in entry:
   if category=='删除段' and isinstance(entry,str):rows.append({'category':category,'key':key,'status':'legacy_untyped_no_fingerprint_preserve_unchanged','original_basis':entry})
   continue
  row={'category':category,'key':key,'source_fingerprint':entry['配音指纹'],'current_fingerprint':fp,'already_current':entry['配音指纹']==fp,'original_entry':entry,'safe_to_renew':False}
  if category=='非人声':
   native=working['核对确认'][category][key]
   assert native['配音指纹']==fp
   assert {k:v for k,v in native.items() if k!='配音指纹'}=={k:v for k,v in entry.items() if k!='配音指纹'}
   m=re.fullmatch(r'([\d.]+)–([\d.]+)s',key);assert m
   lo,hi=map(float,m.groups());row['public_local_comparison_with_150ms_each_side']=compare(lo-.15,hi+.15)
   row.update({'status':'already_current_native_G43_pass' if row['already_current'] else 'safe_exact_native_confirmation_migration_observed_and_G43_passed','safe_to_renew':True,'actual_native_working_entry':native,'actual_native_entry_differs_only_in_fingerprint':True,'actual_original_G43_pass_status_lines':actual_purevoice_lines,'evidence_kind':'Actual435263 working JSON/MP4-proof/sourceSHA/currentPCM binding plus original formal migration and original purevoice check, not a guessed new exemption.'})
   if not row['already_current']:renew.setdefault(category,{})[key]=native
  elif category=='删除段':
   if key in edit_rows:
    row.update({'status':'already_renewed_exact_reported_edit' if row['already_current'] else 'safe_exact_reported_edit_continuity','safe_to_renew':True,'specific_proof':edit_rows[key]})
    if not row['already_current']:renew.setdefault(category,{})[key]=edit['minimal_proposal']['metadata_updates']['核对确认'][category][key]
   else:
    label=key.split()[0];parts=seg[label];lo=parts[0]['时刻'][0]-.1;hi=parts[-1]['时刻'][1]+.1;cmp=compare(lo,hi);assert cmp['whole_region_bit_identical']
    row.update({'status':'safe_whole_sentence_exact_continuity_existing_dormant_edit_only','safe_to_renew':True,'proof_scope':'This raw edit is not one of the current9 abnormal edits; exact old/new whole sentence identity is a conservative continuity proof, not a new raw-to-actual location claim.','whole_sentence_comparison':cmp})
    suffix=f"2026-11-14 本轮连续性复核：当前配音指纹{fp}；此已有raw位置所属{label}整句及前后100 ms（实际成片{lo:.3f}–{hi:.3f} s）与旧已验MP4的{cmp['sample_count']}个48 kHz float64样本逐字节完全相同，SHA256 {cmp['accepted_crop_sha256']}。该键不是本轮9处异常之一，不声称新增raw位置映射；保留既有删除类型和原依据，只续同声音的当前指纹。详见51-all-whole-fingerprint-inventory.json。"
    if not row['already_current']:renew.setdefault(category,{})[key]={**entry,'配音指纹':fp,'依据':entry['依据']+'；'+suffix}
  elif category=='机器复听':
   assert key in asr_rows
   row.update({'status':'safe_existing_ASR_basis_continuity_only','safe_to_renew':True,'specific_proof':asr_rows[key]})
   if not row['already_current']:renew.setdefault(category,{})[key]=asr['minimal_proposal']['metadata_updates']['核对确认'][category][key]
  elif category=='响度骤降':
   m=re.fullmatch(r'([\d.]+)–([\d.]+)s',key);assert m
   lo,hi=map(float,m.groups());cmp=compare(lo,hi);row['exact_original_confirmation_window_comparison']=cmp
   if cmp['whole_region_bit_identical']:
    row.update({'status':'safe_strict_same_samples_level_confirmation_continuity','safe_to_renew':True})
    if not row['already_current']:renew.setdefault(category,{})[key]={**entry,'配音指纹':fp,'依据':entry['依据']+f"；2026-11-14 当前实际公开成片此精确时段逐样本完全相同，SHA256 {cmp['actual_crop_sha256']}；仅续当前指纹{fp}。"}
   else:
    row.update({'status':'pending_strict_sample_identity_not_proven','safe_to_renew':False,'reason':'The original confirmation migration rule requires exact samples. Decoded AAC is not identical; NCC or near-zero gain is insufficient and is not used to renew this fingerprint. No old raw producer PCM is available locally; native preparation explicitly recorded no preexisting work51/a.wav.','next_safe_options':['Read-only native reconstruction from the exact accepted old source and original unprocessed mother caches; bind reconstructed full oldPCM MD5 ff0728857c2d before comparing this window against current rawPCM.','Perform a new specific actual-voice measurement/confirmation under the unchanged original loudness policy, with root review, instead of falsely calling this an identical-sample migration.']})
    pending.append({'category':category,'key':key,'reason':row['reason']})
  else:
   row.update({'status':'pending_unexpected_fingerprint_category','reason':'No continuity rule was invented for a new category.'});pending.append({'category':category,'key':key,'reason':row['reason']})
  rows.append(row)
counts=collections.Counter(r['category'] for r in rows if 'source_fingerprint' in r)
report={'article':'51','purpose':'One-pass inventory of every existing whole-PCM-bound confirmation; exact safe/pending scope','quality_acceptance':False,'source_audio_programs_or_thresholds_modified':False,'base_payload_source_sha256':sha(SOURCE),'current_pcm_sha256':diag['wav_sha256'],'current_pcm_md5_first12':fp,'actual_native_working_source_sha256':sha(WORKING),'actual_native_proof_sha256':sha(PROOF),'summary':{'fingerprinted_record_count':sum(counts.values()),'fingerprinted_records_by_category':dict(counts),'legacy_untyped_delete_record_count':sum(r['status']=='legacy_untyped_no_fingerprint_preserve_unchanged' for r in rows),'already_current_count':sum(r.get('already_current',False) for r in rows),'safe_to_renew_count':sum(r.get('safe_to_renew',False) for r in rows),'safe_stale_record_count':sum(r.get('safe_to_renew',False) and not r.get('already_current',False) for r in rows),'pending_count':len(pending)},'inputs':{str(p):sha(p) for p in [SOURCE,WORKING,STATUS,PROOF,DIAG,O/'51-existing-ASR-confirmation-continuity.json',O/'51-remaining-edit-proof.json']},'rows':rows,'safe_existing_only_metadata_update_proposal':{'核对确认':renew},'pending_records_do_not_renew':pending,'original_checker_source_hashes':{name:sha(B.parent/'audit-repo/视频/工具'/name) for name in ['确认按位置迁移.py','纯人声核对.py','机器复听.py','交付核查.py']},'limits':['Safe is a scoped source-confirmation continuity proposal, not final video acceptance. Original checks and all selftests remain mandatory.','Nonvoice27 current native confirmations already passed the original G43 on the exact current PCM. Their binding is real formal working-source evidence, not a blanket hand-stamped exemption.','Loudness9.2–9.7s is explicitly pending because decoded samples differ; no NCC/gain substitute is used.','Six dormant raw deletion entries are supported by whole-sentence exact identity only; no new actual edit mapping or new exception is claimed.']}
(O/'51-all-whole-fingerprint-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(O/'51-all-whole-fingerprint-inventory.json'),'summary':report['summary'],'pending':pending},ensure_ascii=False))
