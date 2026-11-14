"""Read-only original confirmation migration and PV preflight of approved67.

Both complete original cached WAV/AAC hashes are forced first. Only the private
clone receives the unmodified migration tool's exact-sample changes. No CF is
invented and all remaining original PV alarms are retained.
"""
import copy,hashlib,importlib.util,json,pathlib,subprocess,sys,tempfile
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent;OUT=B/'67-original-confirmation-transfer-preflight';OUT.mkdir(exist_ok=True)
CI=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch')
T=pathlib.Path('/workspace/work/audit-repo/视频/工具')
def mod(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('actual67_two_cache_sources',B/'replay_cache_provenance.py');o=base.orig
pv=mod('unchanged_original67_PV',T/'纯人声核对.py')
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
oldfile=pathlib.Path('/workspace/work/video-audit70-20261113/layout-rebind67-20261114/67-approved-before-source.json')
newfile=pathlib.Path('/workspace/work/video-audit70-20261113/payload/视频/脚本/67.json')
assert sha(oldfile)=='8897cc1c2df1e4672eec3bbff2776d0565afb9c9fe84087a1758ebb15b2a233e'
assert sha(newfile)=='6839a46ebdb51cdcff6a65ca238efc228f1e114efd1734cee6c994ca659a29cb'
olddata=json.loads(oldfile.read_text());newdata=json.loads(newfile.read_text());unchanged_pay=newfile.read_bytes()
report=dict(article='67',quality_acceptance=False,official_native_video_produced=False,
    purpose='unchanged original exact-sample confirmation transfer then original PV scan in private approved-source clone',
    program_sha256=sha(pathlib.Path(__file__)),confirmation_migration_program_sha256=sha(T/'确认平移.py'),
    original_PV_program_sha256=sha(T/'纯人声核对.py'),baseline_source_sha256=sha(oldfile),new_source_sha256=sha(newfile),
    old_expected_PCM_MD5_first12='c34294a522a7',source_or_core_or_existing_cache_modified=False)
expected={'old':('39f7defdcfad7a4dae00c9677c7998d8f70c984247583e136e09e6efe9392bae','d5d57519d6b60e31eeb92bd1bf0b0505192b49ee9c1e34ae02b5c9ddc9532856'),
          'new':('a134119bc6caf3f1fd167cf7119f3414f44486643ee42ce17a6c9a247f3a9241','e9ea80df817aa07649361244a87ddd96bf88fc56e0a0c7b82f28389064ceec70')}
with tempfile.TemporaryDirectory(prefix='private67-original-confirmation-transfer-',dir='/dev/shm')as td:
    td=pathlib.Path(td);cache=td/'cache';cache.mkdir();work=td/'work';(work/'scripts').mkdir(parents=True);(work/'work_67').mkdir()
    wavs={};proof={}
    for label,data in [('old',olddata),('new',newdata)]:
        a,_=o.build(data,cache);wav=td/(label+'.wav');sf.write(wav,a,24000);aac=td/(label+'.m4a')
        subprocess.run([o.FF,'-y','-loglevel','error','-i',str(wav),'-af',o.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
        ash=hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest();wsh=sha(wav)
        assert (wsh,ash)==expected[label],(label,wsh,ash)
        md=hashlib.md5(wav.read_bytes()).hexdigest()[:12];proof[label]=dict(WAV_sha256=wsh,AAC_ADTS_sha256=ash,PCM_file_MD5_first12=md,samples=len(a));wavs[label]=wav
    assert proof['old']['PCM_file_MD5_first12']=='c34294a522a7'
    (work/'work_67/a.wav').write_bytes(wavs['new'].read_bytes());(work/'scripts/67.json').write_bytes(newfile.read_bytes())
    meta=json.loads((B/'67/67-reference-gain-diagnostic.json').read_text())['public_producer_timing_metadata']
    (work/'work_67/词尾除阻.json').write_text(json.dumps(meta['consonant_grafts'],ensure_ascii=False))
    report['exact_two_source_full_WAV_AAC_bindings']=proof
    before=copy.deepcopy(newdata)
    c=subprocess.run([sys.executable,str(T/'确认平移.py'),'67',str(wavs['old']),'--写入'],cwd=work,text=True,capture_output=True)
    (OUT/'original-confirmation-transfer.log').write_text(c.stdout+'\n'+c.stderr)
    report['original_transfer_exit']=c.returncode;report['original_transfer_summary']=c.stdout.strip().splitlines()[-3:]
    report['original_transfer_unmoved_lines']=[x for x in c.stdout.splitlines()if'不挪'in x]
    assert c.returncode==0
    after=json.loads((work/'scripts/67.json').read_text())
    assert{k:v for k,v in before.items()if k!='核对确认'}=={k:v for k,v in after.items()if k!='核对确认'}
    pv_run=subprocess.run([sys.executable,str(T/'纯人声核对.py'),'67'],cwd=work,text=True,capture_output=True)
    (OUT/'original-PV-after-transfer.log').write_text(pv_run.stdout+'\n'+pv_run.stderr)
    selftest=subprocess.run([sys.executable,str(T/'纯人声核对.py'),'67','--自检'],cwd=work,text=True,capture_output=True)
    (OUT/'original-PV-selftest.log').write_text(selftest.stdout+'\n'+selftest.stderr)
    report.update(original_PV_exit=pv_run.returncode,original_PV_summary=pv_run.stdout.strip().splitlines()[-1:],
        original_PV_BAD_lines=[x for x in pv_run.stdout.splitlines()if' BAD' in x],
        original_PV_selftest_exit=selftest.returncode,original_PV_selftest_summary=selftest.stdout.strip().splitlines()[-1:])
    arr,_=sf.read(work/'work_67/a.wav',dtype='int16');a=arr.astype(float)/32768;cf=after.get('核对确认',{}).get('非人声',{});fn=proof['new']['PCM_file_MD5_first12'];findings=[]
    for event in pv.scan(a):
        key=pv.key(event);item=cf.get(key);g=next((x for x in meta['consonant_grafts']if event[0]in('孤立杂音','噗声','呼吸声')and x['开始']-.005<=event[1]and event[2]<=x['结束']+.005),None)
        valid=isinstance(item,dict)and item.get('配音指纹')==fn
        why=None
        if valid:valid,why=pv.确认可收('67',event,item,a)
        if g:valid=True;why='unchanged original A21 graft interval'
        findings.append(dict(key=key,kind=event[0],start_s=event[1],end_s=event[2],original_measurements=pv.实测(event)if event[0]not in('起音前过长','收尾过长')else{'relative_dB':float(event[3]),'duration_s':float(event[4])},
            accepted_by_original_PV=bool(valid),original_reason=why,existing_confirmation_fingerprint=item.get('配音指纹')if isinstance(item,dict)else None,
            overlaps_changed_S9_part3=event[1]<68.91 and event[2]>67.345))
    report['actual_original_PV_findings']=findings
    report['actual_remaining_original_PV_bad_keys']=[x['key']for x in findings if not x['accepted_by_original_PV']]
    report['confirmation_only_changed_in_private_clone']=True;report['manual_CF_added_or_reconfirmed']=False
    report['only_original_exact_sample_mapper_mutated_private_confirmations']=True
assert newfile.read_bytes()==unchanged_pay
report['private_generated_PCM_AAC_and_source_clone_deleted']=True;report['no_raw_GT_cache_or_PCM_exported']=True
p=OUT/'report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(exact_hashes_matched=True,transfer=report['original_transfer_summary'],PV=report['original_PV_summary'],remaining=report['actual_remaining_original_PV_bad_keys'],selftest=report['original_PV_selftest_summary'],report_sha256=sha(p)),ensure_ascii=False),flush=True)
