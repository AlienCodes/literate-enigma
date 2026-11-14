"""Transparent old effective gains under untouched current K134/native caches.

Only source data candidate in this directory changes. Gains are exact differences
of archived original gain controls, not fitted from audio. No cache data is aliased,
overwritten, or renamed. No production/quality-acceptance claim is made.
"""
import copy,datetime,hashlib,importlib.util,json,pathlib,subprocess,tempfile,traceback
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent;f=B/'68';P=B/'replay_cache_provenance.py';s=importlib.util.spec_from_file_location('readonly68_transparent',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
orig=m.orig;sha=lambda x:hashlib.sha256(x).hexdigest()
req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request/68/视频/脚本/68.json');raw=req.read_bytes();data=json.loads(raw)
native=json.loads((f/'68-original-cache-provenance-diagnostic.json').read_text())['modes'][0]
old=json.loads((f/'68-actual-historical-original-reconstruction.json').read_text());assert old['exact_reconstruction_AAC_matches_old_accepted']
candidate=copy.deepcopy(data);manual=candidate.setdefault('分段增益dB',{});changes=[]
np0={x['sentence']:x for x in native['parts']};op0={x['sentence']:x for x in old['parts']}
for label,part in op0.items():
    if label=='title':continue
    n=np0[label];oauto={int(k):float(v)for k,v in part['automatic_level'].items()};oman={int(k):float(v)for k,v in (part['manual_segment_level']or{}).items()}
    nauto={int(k):float(v)for k,v in n['automatic_level'].items()};nmanual={int(k):float(v)for k,v in (n['manual_segment_level']or{}).items()}
    for k in sorted(set(oauto)|set(oman)|set(nauto)|set(nmanual)):
        total=oauto.get(k,0)+oman.get(k,0);wanted=total-nauto.get(k,0)
        if wanted!=nmanual.get(k,0):
            manual.setdefault(label,{})[str(k)]=wanted
            changes.append(dict(sentence=label,segment=k,actual_current_auto_dB=nauto.get(k,0),actual_archived_old_auto_dB=oauto.get(k,0),
                actual_archived_old_manual_dB=oman.get(k,0),old_effective_target_dB=total,current_manual_before_dB=nmanual.get(k,0),transparent_new_manual_dB=wanted))
cp=f/'68-proposed-transparent-effective-gains-source.json';cp.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
assert candidate['sentences']==data['sentences']
rep=dict(source_id='68',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),quality_acceptance=False,
    purpose='literal exact historical effective gain differences with normal unchanged current K134 cache',program_sha256=sha(pathlib.Path(__file__).read_bytes()),
    current_maker_sha256=sha(orig.m.source.encode()),current_source_sha256=sha(raw),candidate_source_sha256=sha(cp.read_bytes()),candidate_source_path=str(cp),
    exact_archived_gain_arithmetic=changes,all_visual_body_translation_notes_summary_unchanged=True,
    no_auto_algorithm_or_threshold_change=True,no_cache_alias_renaming_or_modification=True)
try:
    with tempfile.TemporaryDirectory(prefix='private68-transparent-source-only-',dir='/dev/shm')as td:
        td=pathlib.Path(td);cache=td/'cache';cache.mkdir();a,parts=orig.build(candidate,cache)
        wav=td/'candidate.wav';aac=td/'candidate.m4a';sf.write(wav,a,24000)
        subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
        ash=sha(subprocess.check_output(['ffmpeg','-v','error','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']));wsh=sha(wav.read_bytes())
        rep.update(candidate_WAV_sha256=wsh,historical_old_WAV_sha256=old['reconstructed_historical_WAV_sha256'],
            WAV_exact_old=wsh==old['reconstructed_historical_WAV_sha256'],candidate_AAC_ADTS_sha256=ash,accepted_old_AAC_ADTS_sha256=old['old_accepted_anchor']['aac_adts_sha256'],
            AAC_exact_old=ash==old['old_accepted_anchor']['aac_adts_sha256'],duration_s=len(a)/24000,parts=parts)
except BaseException as ex:
    rep['error']=dict(type=type(ex).__name__,detail=str(ex),traceback=traceback.format_exc());print(traceback.format_exc(),flush=True)
rep['actual_native_K134_cache_safe_scalar_provenance']=list(orig.level_rows.values())
rep['no_TTS_no_production_no_existing_source_or_cache_or_core_modified']=True;rep['private_diagnostic_audio_deleted']=True
out=f/'68-transparent-effective-gains-candidate-report.json';out.write_text(json.dumps(rep,ensure_ascii=False,indent=2,default=lambda x:float(x)if isinstance(x,np.floating)else int(x)if isinstance(x,np.integer)else str(x))+'\n')
print('68 transparent normalK134 WAVexact',rep.get('WAV_exact_old'),'AACexact',rep.get('AAC_exact_old'),'reportSHA',sha(out.read_bytes()),flush=True)
