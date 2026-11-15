"""Install one root-adopted pronunciation-context data row; no audio execution."""
from pathlib import Path
import argparse,hashlib,json,os
OLD='4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
NEW='ef53a5cc5795929b5477b40550cab61ee709156112a0f2bc7a2deb071845552c'
ADOPTION='4183cd29926539889575addae04420f28a1662a6783b2cfd5ece983b0826991b'
MAKER='0e6c4ff6dd4ab4e3774bc060188de72356cd9aa37a7bc092d1f28a5508cc1c36'
STAMP='7d7ebf20b78143231992f8880f70e3cf1581c75acd2d977bc054e3ff151a1a41'
WORDS='5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
SENTENCE="A radio correspondent's eyewitness commentary was not live; audiences heard it the next day."
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def apply(tools,work,context,adoption,output):
    tools,work,context,adoption,output=map(Path,(tools,work,context,adoption,output))
    assert digest(adoption)==ADOPTION and digest(context)==NEW, 'Wrong actual root context data binding'
    root=json.loads(adoption.read_text())
    assert root['selected_context']['sha256']==NEW and root['exact_full_sentence']==SENTENCE
    assert root['future_producer_and_independent_checkers_must_share_same_declared_context_binding']is True
    assert root['existing_native_whole_input_phonemes_SHA256']=='255b963d67369660cc452459478fb69ccf08d3b9958d41ec507b61a81b14bd04'
    assert digest(tools/'make_video.py')==digest(work/'make_video.py')==MAKER
    assert digest(tools/'新管/快测通过.json')==STAMP
    assert digest(tools/'发音词典/读音改正.json')==digest(work/'读音改正.json')==WORDS
    paths=[tools/'发音词典/按语境读音.json',work/'按语境读音.json']
    assert all(p.is_file()and digest(p)==OLD for p in paths), 'Original context must be observed before installing this exact data row'
    raw=paths[0].read_bytes();assert paths[1].read_bytes()==raw
    data=context.read_bytes();old,new=json.loads(raw),json.loads(data)
    assert SENTENCE not in old and len(new)==len(old)+1
    assert list(new)[:-1]==list(old)and all(new[k]==v for k,v in old.items())
    assert new[SENTENCE]['词']=='next' and new[SENTENCE]['读音']=='nˈɛkst'
    assert raw.endswith(b'\n}')and data.startswith(raw[:-2]+b',\n')and data.endswith(raw[-2:])
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
    receipt={'source_id':'68','non_target_sentence_existing_voice_preserved':'S13',
      'root_context_data_adoption_SHA256':ADOPTION,'historical_codecert_original_context_SHA256':OLD,
      'actual_shared_producer_and_checker_context_SHA256':NEW,'existing24_rows_and_raw_prefix_suffix_unchanged':True,
      'existing_native_raw_key':'7015ff2f048856421634e6d1b7d6cce7d1771e6d.pkl',
      'existing_native_timed_key':'4c8e055804f0ae658341a7d997ae4ce8fc247360.pkl',
      'actual_code20_programs_and_real110_stamp_bytes_unchanged':True,
      'not_claiming_old_codecert_unconditionally_covers_new_data':True,
      'no_model_or_cache_alias_or_new_audio_or_whole_quality_acceptance':True}
    assert not output.exists();output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ['tools','work','context','adoption','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();apply(a.tools,a.work,a.context,a.adoption,a.output)
