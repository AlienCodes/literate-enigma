"""Install one root-adopted pronunciation-context data row; no audio execution."""
from pathlib import Path
import argparse,hashlib,json,os
OLD='4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
NEW='db04a700c9778e45db7c934ce0f4cf8f44349ff3a924599d4194aa90a363440f'
ADOPTION='a2cb835b5dfd64098e439cafb7e9239562ab3d410dd3001d2b13ebf473fc51e4'
MAKER='1b87c1d4d1685bdd59325587184cca35f853354a015e6fe89c11f150cd2a6239'
STAMP='9aa653ec47c686d9bb0b6c4393444bb50c3c8d2d249fe10a843b0959854f7ea6'
WORDS='5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
SENTENCE="The compromise struck without Wallace, may have kept rivalry over precedence at bay."
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def apply(tools,work,context,adoption,output):
    tools,work,context,adoption,output=map(Path,(tools,work,context,adoption,output))
    assert digest(adoption)==ADOPTION and digest(context)==NEW, 'Wrong actual root context data binding'
    root=json.loads(adoption.read_text())
    assert root['selected_context']['sha256']==NEW and root['exact_full_sentence']==SENTENCE
    assert root['future_producer_and_independent_checkers_must_share_same_declared_context_binding']is True
    assert root['existing_native_whole_input_phonemes_SHA256']=='7ab4087b2c5293e715b5a63769102df98c294a405f7d0e5368c328f51388492a'
    assert digest(tools/'make_video.py')==digest(work/'make_video.py')==MAKER
    assert digest(tools/'新管/快测通过.json')==STAMP
    assert digest(tools/'发音词典/读音改正.json')==digest(work/'读音改正.json')==WORDS
    paths=[tools/'发音词典/按语境读音.json',work/'按语境读音.json']
    assert all(p.is_file()and digest(p)==OLD for p in paths), 'Original context must be observed before installing this exact data row'
    raw=paths[0].read_bytes();assert paths[1].read_bytes()==raw
    data=context.read_bytes();old,new=json.loads(raw),json.loads(data)
    assert SENTENCE not in old and len(new)==len(old)+1
    assert list(new)[:-1]==list(old)and all(new[k]==v for k,v in old.items())
    assert new[SENTENCE]['词']=='Wallace' and new[SENTENCE]['读音']=='wˈɔːlɪs'
    assert hashlib.sha256(raw).hexdigest()==OLD and hashlib.sha256(data).hexdigest()==NEW and data==(json.dumps(new,ensure_ascii=False,indent=2)+'\n').encode(), 'Only exact approved old4d890 and canonical-indented db04 bytes are declared'
    # Both declared producer/checker locations receive exactly the same bytes.
    for p in paths:
        temporary=p.with_name(p.name+'.exact-context-data-'+str(os.getpid()))
        assert not temporary.exists()
        temporary.write_bytes(data);assert digest(temporary)==NEW
        os.replace(temporary,p)
    assert all(digest(p)==NEW for p in paths)
    assert digest(tools/'发音词典/读音改正.json')==digest(work/'读音改正.json')==WORDS
    assert digest(tools/'make_video.py')==digest(work/'make_video.py')==MAKER
    assert digest(tools/'新管/快测通过.json')==STAMP
    receipt={'source_id':'56','target_sentence_actual_new_CMU2_voice_context':'S11',
      'root_context_data_adoption_SHA256':ADOPTION,'historical_codecert_original_context_SHA256':OLD,
      'actual_shared_producer_and_checker_context_SHA256':NEW,'existing24_typed_rows_order_and_values_unchanged':True,
      'raw_prefix_suffix_unchanged':False,'format_is_exact_approved_indent2_LF':True,
      'existing_native_raw_key':'a387fbeb6dd6337c40167612b2f8f3c56170122f.pkl',
      'existing_native_timed_key':'42d32206d7fda7443c0e489a1ee1ac1b11d9e3fa.pkl',
      'actual_code22_programs_and_real110_stamp_bytes_unchanged':True,
      'not_claiming_old_codecert_unconditionally_covers_new_data':True,
      'no_model_or_cache_alias_or_new_audio_or_whole_quality_acceptance':True}
    assert not output.exists();output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ['tools','work','context','adoption','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();apply(a.tools,a.work,a.context,a.adoption,a.output)
