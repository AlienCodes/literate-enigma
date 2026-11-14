"""Read-only add-on for the sole native cached source48 observer.

Not a launcher, production gate, new confirmation, or source writer. Parent must
supply the already validated original maker and hard cached-only model wrappers.
Two existing original sentences are reconstructed locally, never a whole track.
Private PCM temporary files must not be included in any public artifact.
"""
from pathlib import Path
import ast, copy, hashlib, json, math

SOURCE = '0193cbd1859525690e12a470c517cce2f120a1054b204fcfa3c0c392c92abbd7'
WHOLE = '295fd087864e9ffbd2ad63edddb2da5d10af818b960c8a030e1ccdbd5537c591'
OLD_FP = '8253a58195c8'
NEW_FP = '3bf9427c6935'
OLD_CASES = ['S1','S5','S7','S8','S9','S10','S12','S13','S16']

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def observe(m, source_path, whole_report_path, official_tools, private_scratch):
    source_path, whole_report_path = Path(source_path), Path(whole_report_path)
    T, scratch = Path(official_tools), Path(private_scratch)
    assert digest(source_path)==SOURCE and digest(whole_report_path)==WHOLE
    d=json.loads(source_path.read_text()); whole=json.loads(whole_report_path.read_text())
    assert whole['exact_scope_proved'] and whole['errors']==[]
    phase=whole['phases']['selected_new0193']
    assert phase['actual_own_17_sentence_SENT_NO']==['48']*17
    np, SR=m.np,m.SR
    assert SR==24000
    assert not scratch.exists();scratch.mkdir(parents=True)
    oldcf=d['核对确认']['删除段']
    assert len(oldcf)==11 and all(row['配音指纹']==OLD_FP for row in oldcf.values())
    report={'kind':'source48_readonly_old_confirmation_metadata_and_actual_G45_local_sentence_probe',
      'source_sha256':SOURCE,'actual_whole_report_sha256':WHOLE,
      'diagnostic_only':True,'source_or_confirmation_written':False,
      'original_old8253_voice_identity_not_proven_by_current4f_outside_identity':True,
      'old_current4f_already_failed_cut1_unconfirmed11_and_same2HL':True,
      'new_confirmation_or_native_fullQA_not_claimed':True,
      'old_delete_confirmations':[],'highlights':[]}
    for key,row in oldcf.items():
        sid,_,span=key.split(' ',2);a,b=map(float,span.split('-'))
        iv=[x for x in d.get('非人声区间',{}).get(sid,[])if x[0]<b and a<x[1]]
        report['old_delete_confirmations'].append({'raw_key':key,'old_type':row['类型'],
          'old_fingerprint':row['配音指纹'],'historical_basis':row['依据'],
          'currently_authored_overlapping_NV':iv,
          'actual_current_audit_edit_and_edge_sides_not_in_export':True,
          'fingerprint_stale_under_actual_current3bf':row['配音指纹']!=NEW_FP,
          'typed_confirmation_renewal_not_authorized_by_this_probe':True})
    # Only the original onset functions, not the script's TTS/DTW execution.
    g45path=T/'高亮同步核对.py';tree=ast.parse(g45path.read_text())
    defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ('是开口','确认可收')]
    assert len(defs)==2
    env={'np':np};code=ast.Module(body=defs,type_ignores=[]);ast.fix_missing_locations(code)
    exec(compile(code,str(g45path),'exec'),env)
    report['original_G45_program_sha256']=digest(g45path)
    report['original_G45_function_AST_sha256']={n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()for n in defs}
    state={name:copy.deepcopy(getattr(m,name))for name in ('LAST','SENT_FP','SENT_KEYS')}
    try:
        for sid in ('S10','S13'):
            index=int(sid[1:])-1
            sent=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in d['sentences'][index]['chunks'])
            assert m.SENT_NO.get(sent)=='48'
            pieces=[];gaps=[];p0=0;listing=m.list_commas(sent)
            for match in m.re.finditer(r'[,;:](?=\s)',sent):
                pieces.append((p0,match.end()));p0=match.end()+1
                gaps.append(m.P_LIST if match.start()in listing else m.P_COMMA)
            pieces.append((p0,len(sent)))
            clips,tmap=m.sentence_audio(sent,pieces,gaps)
            _,pcm,auto,manual=m.句增益(d,'48',index,sent,pieces,gaps,clips,tmap,np.concatenate(clips))
            raw_hash=hashlib.sha256(np.ascontiguousarray(pcm).tobytes()).hexdigest()
            assert raw_hash==phase['observed_sentences'][sid]['pre_master_PCM_sha256']
            assert len(pcm)==phase['observed_sentences'][sid]['samples']
            # Preserve the exact original ordered float32 normalization formula.
            fullpeak=phase['actual_original_mastering']['pre_master_absolute_peak']
            mastered=pcm/fullpeak*.89
            mastered_hash=hashlib.sha256(np.ascontiguousarray(mastered).tobytes()).hexdigest()
            clock=phase['actual_sample_clock'][sid]
            assert mastered_hash==clock['observed_post_master_float_PCM_sha256']
            privatewav=scratch/(sid+'-original-mastered-private.wav')
            m.sf.write(privatewav,mastered,SR)
            A,sr=m.sf.read(privatewav);assert sr==SR and len(A)==len(pcm)
            old=d['核对确认']['高亮'][sid+' 第2块'];t_global=float(old['开始读']);t=t_global-clock['start_s']
            assert t-2>=0 and t+2<=len(A)/SR, 'Original G45 +/-2s reference must stay completely inside this exact sentence.'
            accepted=bool(env['确认可收']('48',A,SR,t))
            F=int(.005*SR);i=int(round(t*SR));w=A[i-2*SR:i+2*SR]
            n=len(w)//(2*F);ref=float(np.sqrt(np.mean(w[:n*2*F].reshape(n,2*F)**2,axis=1)).max()+1e-12)
            frames=[]
            for x in range(i-6*F,i+8*F,F):
                v=A[x:x+F]
                frames.append({'start_global_s':clock['start_s']+x/SR,
                               'relative_5ms_RMS_dB':20*math.log10(float(np.sqrt(np.mean(v*v)))/ref+1e-12)})
            report['highlights'].append({'sentence':sid,'current_sentence_premaster_sha256':raw_hash,
              'current_sentence_postmaster_sha256':mastered_hash,'exact_to_actual295':True,
              'actual_sentence_start_s':clock['start_s'],'old_requested_onset_global_s':t_global,
              'old_requested_onset_local_s':t,'actual_original_G45_onset_acceptance':accepted,
              'original_G45_reference_peak':ref,'original_G45_5ms_frames':frames,
              'old_global_fingerprint':old['配音指纹'],'actual_current_global_fingerprint':NEW_FP,
              'historical_basis':old['依据'],'candidate_metadata_only_if_root_adopts_and_all_original_gates_pass':True})
    finally:
        for name,value in state.items():
            current=getattr(m,name);current.clear();current.update(value)
    assert digest(source_path)==SOURCE
    report['old11_actual_independent_cut1_still_unlocated']=True
    report['old11_and_cut1_require_original_report2_per_edit_not_count_substitution']=True
    report['all_source_bytes_unchanged']=True
    return report
