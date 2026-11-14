"""Article12 accepted/canonical title measurement using original A21 pure functions."""
import ast
import json
from pathlib import Path
import subprocess
import numpy as np
import scipy.signal as ss

SR = 24000
F5 = 120

def original_a21(tools):
    source = Path(tools) / '词尾辅音核对.py'
    ns = {'np': np, 'ss': ss, 'SR': SR, 'AUD_DB': -55.0}
    assignments = {'F5','HP','TH_HF','TH_P','CEN_MIN','DUR_MAX','LP8','LF_MAX','PER_MAX'}
    functions = {'frames_back','release','centroid','lf_peak','periodicity','双爆破','judge'}
    for node in ast.parse(source.read_text()).body:
        use = isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in node.targets)
        use = use or isinstance(node,ast.FunctionDef) and node.name in functions
        if use:
            exec(compile(ast.Module(body=[node],type_ignores=[]),str(source)+'#pure-waveform-functions','exec'),ns)
    return ns

def measure_title(video, tools):
    """Return measured accepted/canonical Coke release intervals and original A21 verdicts.

    Reads existing MP4 audio only. Does not execute producer, synthesize voice,
    change source/checkers, or create a pass record for simulated candidates.
    """
    ns = original_a21(tools)
    raw = subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-map','0:a:0',
                                  '-t','3.0','-ac','1','-ar',str(SR),'-f','f32le','-'])
    x = np.frombuffer(raw,dtype='<f4').astype(np.float64)
    title_start = .4
    a = x[round(title_start*SR):round(2.9*SR)]
    m = len(a)//F5
    ref = np.sqrt(np.mean(a[:m*F5].reshape(m,F5)**2,axis=1)).max()
    n = len(x)//F5
    rms = np.sqrt(np.mean(x[:n*F5].reshape(n,F5)**2,axis=1))
    db = 20*np.log10(rms/ref+1e-12)
    audible = [i for i,d in enumerate(db) if 1.5 < i*.005 < 2.9 and d > -55]
    assert audible, 'No audible final title consonant found.'
    end = (audible[-1]+1)*.005
    hp = ss.sosfiltfilt(ns['HP'],a)
    def metric(z):
        if not z:
            return None
        return {'full_peak_db':z[0],'hf_above2k_peak_db':z[1],'duration_ms':z[2],
                'interval_in_video_seconds':[title_start+p/SR for p in z[3]],
                'closure_min_db':z[4],'spectral_centroid_hz':ns['centroid'](a,*z[3]),
                'periodicity':ns['periodicity'](a,*z[3]),'below800hz_peak_db':ns['lf_peak'](a,*z[3])}
    rows=[]
    for offset in (0,.0025,.005,.0075,.01,.015,.02,.025,.03):
        p=round((end-title_start+offset)*SR)
        z=ns['release'](a,hp,p,ref)
        z2=ns['release'](a,hp,z[3][0],ref) if z else None
        double=ns['双爆破'](a,hp,z,ref)
        rows.append({'analysis_end_video_seconds':p/SR+title_start,
                     'last_release':metric(z),'previous_release':metric(z2),
                     'double_release':list(double) if double else None,
                     'release_meets_original_A21':bool(ns['judge'](a,z,'k'))})
    return {'title_start_seconds':title_start,'last_audible_5ms_window_end_seconds':end,
            'method':'existing MP4 AAC decoded24kHz; unchanged original A21 pure functions;9 endpoint/frame-phase settings',
            'settings':rows,'has_double_release_all_settings':all(r['double_release'] for r in rows),
            'has_double_release_any_setting':any(r['double_release'] for r in rows),
            'release_passes_all_settings':all(r['release_meets_original_A21'] for r in rows)}

def verify_title_correction(accepted, canonical, tools):
    """Call only with actual official canonical output; outside-region QC is the caller's job."""
    before=measure_title(accepted,tools)
    after=measure_title(canonical,tools)
    assert before['has_double_release_all_settings'], 'Accepted reference no longer exhibits the measured legacy duplicate.'
    assert not after['has_double_release_any_setting'], 'Canonical title still has a duplicate /k/ release.'
    assert after['release_passes_all_settings'], 'Canonical natural /k/ release fails unchanged A21 thresholds.'
    return {'accepted':before,'canonical':after,
            'title_voice_endpoint_change_seconds':after['last_audible_5ms_window_end_seconds']-before['last_audible_5ms_window_end_seconds'],
            'warning':'Removing the duplicate may shorten the title; align following body by the measured constant endpoint shift and still verify all body samples.'}
