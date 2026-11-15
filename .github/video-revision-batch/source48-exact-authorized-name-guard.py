import hashlib,json,re
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def english(d):
    return [re.sub(r'\{\{.*?\}\}', '', ' '.join(c['en'] for c in sent['chunks'])).replace('**','').split() for sent in d['sentences']]
def validate(requested,baseline,old_file,new_file,gen_file,decision):
    assert sha(old_file)=='4f146ce6a70bb0bf5d2c6e1f6b47bd6a2bcc2f311be7a948092d7bde1a08f449'
    assert sha(new_file)=='4980ad358636619218f20a8edb618ae543432b82c2124cfac8058790be5e8361'
    assert sha(gen_file)=='3178b9610b5d49f3b7e5bbfce16cebc0839bdb429b0f5f911e692b9dce8831e3'
    assert sha(decision)=='c17a3b2b33a33fb27e17a7537fc655acb0611214749bfec1ffe8ebd29f4633b7'
    old=json.loads(Path(old_file).read_text());new=json.loads(Path(new_file).read_text())
    assert str(requested['no'])==str(old['no'])==str(new['no'])=='48'
    assert requested==new
    assert requested['title_en']==baseline['title_en']==old['title_en']
    before,after=english(old),english(new)
    assert len(before)==len(after)==17 and english(baseline)==before
    assert all(before[i]==after[i] for i in range(17) if i!=14)
    assert before[14][0]=='Yuan,' and after[14]==['Yuan','Longping,']+before[14][1:]
    return {'kind':'exact-user127-one-name-insertion-only-original-outer-EN-scope','source_id':'48','sentence':'S15','all_other16_sentence_words_and_title_exact':True,'original_all_ASR_and_voice_picture_gates_still_required':True}
