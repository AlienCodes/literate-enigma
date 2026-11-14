"""Read-only diagnostic: exact original functions and G72-verified cached mothers.

No inference, production, control changes, quality verdict, or private audio export.
Temporary reconstructed WAV/AAC exists in /dev/shm and is deleted on exit.
"""
import datetime
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import traceback

import numpy as np
import soundfile as sf

B = pathlib.Path(__file__).parent
BASE = B.parent / 'audio65-69-source-readonly/replay_original_sources.py'
spec = importlib.util.spec_from_file_location('readonly_original_audio_replay', BASE)
orig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orig)
sha = lambda x: hashlib.sha256(x).hexdigest()

def main(no):
    folder = B / no
    status = json.loads((folder / f'{no}-status.json').read_text())
    diag = json.loads((folder / f'{no}-reference-gain-diagnostic.json').read_text())
    req = pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request') / no / f'视频/脚本/{no}.json'
    raw = req.read_bytes()
    assert sha(raw) == status['request_source_sha256'][f'视频/脚本/{no}.json']
    assert sha(orig.m.source.encode()) == diag['tool_sha256']['make_video.py']
    assert sha(orig.m.clean.encode()) == diag['tool_sha256']['clean.py']
    report = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        purpose='read-only G72 cache and original-function provenance diagnostic; never audio quality acceptance',
        source_id=no, actual_native_run=43543967031, quality_acceptance=False,
        native_status_sha256=sha((folder / f'{no}-status.json').read_bytes()),
        native_reference_gain_diagnostic_sha256=sha((folder / f'{no}-reference-gain-diagnostic.json').read_bytes()),
        program_sha256=sha(pathlib.Path(__file__).read_bytes()), reused_original_replay_sha256=sha(BASE.read_bytes()),
        original_maker_sha256=sha(orig.m.source.encode()), original_clean_sha256=sha(orig.m.clean.encode()),
        current_request_source_sha256=sha(raw), expected_native_PCM_WAV_sha256=diag['wav_sha256'],
        expected_native_AAC_ADTS_sha256=status.get('canonical_aac_adts_sha256'),
        actual_old_accepted_anchor=status['accepted_source'],
        ffmpeg_version=subprocess.check_output([orig.FF,'-version'],text=True).splitlines()[0],
        modes=[])
    try:
        pinned = orig.m.git(f'视频/脚本/{no}.json')
        candidates = [('exact_current_native_request',raw)]
        if pinned != raw:
            candidates.append(('original_pinned_source',pinned))
        report['pinned_source_commit']=orig.m.PIN
        report['pinned_source_sha256']=sha(pinned)
        report['pinned_source_entire_bytes_equal_request']=pinned==raw
        with tempfile.TemporaryDirectory(prefix=f'private-{no}-cache-only-provenance-',dir='/dev/shm') as temp:
            td=pathlib.Path(temp); cache=td/'cache';cache.mkdir()
            for label,data in candidates:
                d=json.loads(data);audio,parts=orig.build(d,cache)
                wav=td/f'{label}.wav';aac=td/f'{label}.m4a'
                sf.write(wav,audio,24000)
                subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
                ash=sha(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']))
                wsh=sha(wav.read_bytes())
                row=dict(source_kind=label,source_file_sha256=sha(data),private_reconstructed_WAV_sha256=wsh,
                    private_reconstructed_AAC_ADTS_sha256=ash,
                    reconstructed_PCM_matches_actual_native_WAV=wsh==diag['wav_sha256'],
                    reconstructed_AAC_matches_actual_native=ash==status.get('canonical_aac_adts_sha256'),
                    reconstructed_AAC_matches_actual_old_accepted=ash==status['accepted_source']['aac_adts_sha256'],
                    sample_count_24k=len(audio),duration_s=len(audio)/24000,
                    parts=parts)
                report['modes'].append(row)
                print(no,label,'PCM native',row['reconstructed_PCM_matches_actual_native_WAV'],
                    'AAC native',row['reconstructed_AAC_matches_actual_native'],
                    'AAC old',row['reconstructed_AAC_matches_actual_old_accepted'],flush=True)
    except BaseException as exc:
        report['error']=dict(type=type(exc).__name__,detail=str(exc),traceback=traceback.format_exc())
        print(traceback.format_exc(),flush=True)
    report['G72_original_mother_safe_scalar_provenance']=list(orig.m.cache_rows.values())
    report['stored_level_cache_safe_scalar_provenance']=list(orig.level_rows.values())
    report['private_generated_audio_removed']=True
    report['no_existing_source_cache_core_or_control_changed']=True
    report['no_TTS_inference_or_production_run']=True
    out=folder/f'{no}-original-cache-provenance-diagnostic.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:float(x) if isinstance(x,np.floating) else int(x) if isinstance(x,np.integer) else str(x))+'\n')
    print('report',out,'sha256',sha(out.read_bytes()),flush=True)

if __name__=='__main__':
    for a in sys.argv[1:]:main(a)
