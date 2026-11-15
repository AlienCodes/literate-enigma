#!/usr/bin/env python3
"""Proposed private-cache scalar reader; no model, GT creation or audio export.

It compares an in-memory original np.save serialization with the existing
failed GT file SHA. Different file SHA is not called a measured sample delta.
"""
from pathlib import Path
import argparse,hashlib,io,json,pickle
import numpy as np

PREP_SHA='2edd8197e6221b4262606abcf2d4cd3075384cb260c3e75096ed567b0f9809e1'
DIAG_SHA='2c14cbb761aab14b8989373f77ac098e8d21303064457a5b7f41a9e0b4094462'
KEY='0b92c947f3b30b07c1b71225382ec933c896c15c.pkl'
PKL_SHA='9a34d932db7ee80ed25a1aeb65c05d3c8928fc12ead028d32e75ea47a75ba49e'
ARRAY_SHA='0ea8b2e227d44ac577b2bc7b4c35d4d834dd59c52e51c867e25a99d788554537'
GT_SHA='5fe5c749a126a4d57df3cea2090fcbe2d6d35d7023dd039f15ba66cc5b520d58'

def sha(b):return hashlib.sha256(b).hexdigest()
def array_scalars(a):
    assert type(a) is np.ndarray and a.dtype==np.float32 and a.ndim==1 and np.isfinite(a).all()
    b=io.BytesIO();np.save(b,a);raw=b.getvalue()
    b.seek(0);r=np.load(b,allow_pickle=False);assert r.dtype==a.dtype and r.shape==a.shape and r.tobytes()==a.tobytes()
    return {'dtype':str(a.dtype),'samples':len(a),'array_SHA256':sha(np.ascontiguousarray(a).tobytes()),'original_np_save_NPY_file_SHA256':sha(raw),'original_np_save_NPY_bytes':len(raw),'FLOAT_roundtrip_bitexact':True,'numpy_version':np.__version__}

def observe(cache_dir,preparation,failed_diagnostic):
    assert sha(preparation.read_bytes())==PREP_SHA
    assert sha(failed_diagnostic.read_bytes())==DIAG_SHA
    prep=json.loads(preparation.read_text());diag=json.loads(failed_diagnostic.read_text())
    assert prep['article']=='58' and diag['article']=='58'
    row=next(r for r in prep['raw_mother_cache_scalar_manifest'] if r['exact_native_cache_key']==KEY)
    assert row['pkl_sha256']==PKL_SHA and row['unprocessed_array_sha256']==ARRAY_SHA and row['native_single_thread_marker_matches']
    assert next(t['gt_sha256']for t in diag['texts']if t['text_index']==-1)==GT_SHA
    p=cache_dir/KEY;marker=Path(str(p)+'.单线程')
    assert p.is_file() and not p.is_symlink() and marker.is_file() and not marker.is_symlink()
    before=p.read_bytes();mb=marker.read_bytes();assert sha(before)==PKL_SHA and mb.decode().strip()==PKL_SHA[:16]
    value=pickle.loads(before)
    assert type(value)is tuple and len(value)==2 and isinstance(value[1],(int,np.integer)) and value[1]==24000
    data=array_scalars(value[0]);assert data['array_SHA256']==ARRAY_SHA and data['samples']==58368
    assert p.read_bytes()==before and marker.read_bytes()==mb
    return {'kind':'existing-title-raw-PKL-vs-already-exported-failed-GT-file-SHA-scalar-only','article':'58','actual_failed_GT_NPY_file_SHA256':GT_SHA,'existing_original_raw_cache':{'key':KEY,'full_PKL_SHA256':PKL_SHA,'native_marker_exact':True,**data},'same_NPY_file_SHA256':data['original_np_save_NPY_file_SHA256']==GT_SHA,'actual_failed_GT_array_not_loaded_or_exported':True,'different_NPY_file_hash_not_claimed_as_measured_sample_delta_or_CPU_cause':True,'cache_and_marker_unchanged':True,'model_GT_whole_math_or_production_execution':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache-dir',type=Path,required=True);p.add_argument('--preparation',type=Path,required=True);p.add_argument('--failed-diagnostic',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();r=observe(a.cache_dir,a.preparation,a.failed_diagnostic);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
