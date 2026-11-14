"""Real cache-reconstruction diagnostic positive and binding/numeric negatives.

No synthetic media is claimed as official production. Private test audio is deleted.
"""
import copy,hashlib,importlib.util,json,pathlib,tempfile,types,subprocess
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent
OUT=B/'controlled67-helper-verification-v2';OUT.mkdir(exist_ok=True)
CI=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch')
def mod(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
base=mod('actual_cache_reconstruction',B/'replay_cache_provenance.py');o=base.orig
helper=mod('new_actual_controlled67_helper',CI/'audio-controlled-qc.py')
U=mod('actual_numeric_utilities',CI/'audio-qc.py')
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
ref=json.loads((CI/'audio-controlled-qc-reference.json').read_text());profile=ref['profiles']['67']
datafile=pathlib.Path('/workspace/work/video-audit70-20261113/payload/视频/脚本/67.json');data=json.loads(datafile.read_text())
results={'kind':'real-G72-cache-reconstruction-diagnostic-positive-and-adversarial-checks','quality_acceptance':False,
    'official_native_video_produced':False,'program_sha256':sha(CI/'audio-controlled-qc.py'),
    'reference_sha256':sha(CI/'audio-controlled-qc-reference.json'),'tests':[]}
with tempfile.TemporaryDirectory(prefix='private-controlled67-tests-',dir='/dev/shm')as td:
    td=pathlib.Path(td);work=td/'work';(work/'scripts').mkdir(parents=True);(work/'work_67').mkdir()
    request=td/'request';(request/'视频/脚本').mkdir(parents=True);(request/'视频/工具/初稿生成').mkdir(parents=True)
    (request/'视频/脚本/67.json').write_bytes(datafile.read_bytes())
    (request/'视频/工具/初稿生成/gen67.py').write_bytes(pathlib.Path('/workspace/work/video-audit70-20261113/payload/视频/工具/初稿生成/gen67.py').read_bytes())
    actual=work/'scripts/67.json'
    actual.write_bytes(pathlib.Path('/workspace/work/video-audit70-20261113/root-approved-audio-source-GEN-text-20261114/auto-repaired-sources/67.json').read_bytes())
    (work/'work_67/分段.json').write_text(json.dumps(profile['expected_producer_piece_metadata'],ensure_ascii=False))
    cache=td/'cache';cache.mkdir();audio,_=o.build(data,cache);wav=work/'work_67/a.wav';sf.write(wav,audio,24000)
    media=td/'67.m4a';subprocess.run([o.FF,'-y','-loglevel','error','-i',str(wav),'-af',o.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(media)],check=True)
    assert sha(wav)==profile['fingerprints']['actual_raw_WAV_sha256']
    assert helper.aac_sha(media)==profile['fingerprints']['canonical_AAC_ADTS_sha256']
    old=B/'67/67-accepted-public.mp4'
    args=types.SimpleNamespace(article='67',reference=None,diagnostic=True,request=str(request),work=str(work),actual_source=None,raw_pcm=None,
        accepted_source=str(old),canonical_video=str(media),tools='/workspace/work/audit-repo/视频/工具',output=str(OUT/'67-actual-diagnostic-positive.json'))
    positive=helper.audit(args)
    results['tests'].append({'case':'actual-current-source-G72-reconstruction-complete-diagnostic-audit',
        'passed':positive['passed']and positive['diagnostic_only']and not positive['production_delivery_eligible'],
        'actual_report':args.output,'actual_report_sha256':sha(args.output),'failed_checks':positive['failed_checks'],'error':positive.get('error')})
    olda=U.decode(old);new=U.decode(media)
    changed=new.copy();changed[round(16.0*48000):round(17.0*48000)]*=10**(6/20);checks=[]
    helper.outside_measurements(U,olda,changed,profile['allowed_audio_changes'],checks)
    results['tests'].append({'case':'actual-decoded-outside-voiced-block-plus6dB-rejected-numerically',
        'passed':any(not x['passed']for x in checks),'failed_checks':[x['name']for x in checks if not x['passed']]})
    clipped=new.copy();clipped[round(40.1*48000)]=1.1
    finite_no_clip=bool(np.isfinite(clipped).all()and np.max(abs(clipped))<1)
    results['tests'].append({'case':'real-decoded-sample-clipping-rejected-original-no-clip-rule','passed':not finite_no_clip,'sample_peak':float(np.max(abs(clipped)))})
    bad=copy.deepcopy(json.loads(actual.read_text()));bad['分段增益dB']['S9']['3']=-3.5;actual.write_text(json.dumps(bad,ensure_ascii=False))
    args.output=str(OUT/'67-wrong-effective-control-negative.json');negative=helper.audit(args)
    results['tests'].append({'case':'actual-full-source-changed-effective-gain-rejected','passed':not negative['passed']and
        'all-approved-audio-controls-exact'in negative['failed_checks'],'actual_report':args.output,'actual_report_sha256':sha(args.output),
        'failed_checks':negative['failed_checks'],'error':negative.get('error')})
    for no in ['68','70']:
        args.article=no;args.output=str(OUT/f'{no}-pending-profile-negative.json');pending=helper.audit(args)
        results['tests'].append({'case':no+'-pending-profile-fail-closed','passed':not pending['passed']and not pending['production_delivery_eligible'],
            'actual_report_sha256':sha(args.output),'error':pending.get('error')})
results['private_generated_test_audio_deleted']=True
results['no_TTS_inference_no_source_or_cache_or_official_core_changes']=True
results['all_tests_passed']=all(x['passed']for x in results['tests'])
p=OUT/'real-diagnostic-positive-and-negative-tests.json'
p.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all_tests_passed':results['all_tests_passed'],'tests':results['tests'],'report_sha256':sha(p)},ensure_ascii=False),flush=True)
