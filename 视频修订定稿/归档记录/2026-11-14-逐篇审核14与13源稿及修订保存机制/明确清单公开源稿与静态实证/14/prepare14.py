"""Authorized article14 data proposal; no audio/core/published bundle writes."""
from pathlib import Path
import copy, hashlib, importlib.util, json, re, shutil
B=Path('/workspace/work/video-audit70-20261113');HERE=Path(__file__).parent
PAY=B/'payload';RELMD=Path('新版定稿/14-the-fungus-that-turns-ants-into-zombies.md')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=module('article14_data_encoder',B/'generator_text_preflight.py')
before=HERE/'before';before.mkdir(parents=True,exist_ok=True)
for rel in [Path('视频/脚本/14.json'),Path('视频/工具/初稿生成/gen14.py'),RELMD]:
    p=before/rel;p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():shutil.copyfile(PAY/rel,p)
p=before/'gen-sources-gen14.py'
if not p.exists():shutil.copyfile(B/'gen-sources/gen14.py',p)
old=json.loads((before/'视频/脚本/14.json').read_text());new=copy.deepcopy(old)
def change(si,ci,replacements):
    c=new['sentences'][si-1]['chunks'][ci-1]
    for a,b in replacements:
        count=0
        for k in ['en','zh']:
            count+=c[k].count(a);c[k]=c[k].replace(a,b)
        c['align']=[[x.replace(a,b),y.replace(a,b)]for x,y in c['align']]
        assert count>0,(si,ci,a)
    assert c['en']==' '.join(x for x,y in c['align']if x!='\n')
    assert c['zh']==''.join(y for x,y in c['align'])
change(5,1,[('fungus','**fungus**'),('真菌','**真菌**(fungus)')])
change(6,1,[('**真菌**(fungal)','**真菌的**(fungal)')])
change(6,2,[('**infectious** spores','**infectious** **spores**'),('孢子','**孢子**(spores)')])
c=new['sentences'][5]['chunks'][1]
assert c['align'][0]==['and releases **infectious** **spores**','将**具有传染性的**(infectious)**孢子**(spores)释放']
c['align'][0:1]=[['and releases','将'],['**infectious**','**具有传染性的**(infectious)'],['**spores**','**孢子**(spores)释放']]
assert c['en']==' '.join(x for x,y in c['align']) and c['zh']==''.join(y for x,y in c['align'])
change(6,3,[('foraging','**foraging**'),('觅食的','**觅食的**(foraging)')])
change(11,2,[('imaging.','**imaging**.'),('成像。','**成像**(imaging)。')])
change(12,2,[('muscle fibres','**muscle fibres**'),('肌肉纤维','**肌肉纤维**(muscle fibres)')])
change(14,1,[('Earth episode,','Earth **episode**,'),('的一集，','的**一集**(episode)，')])
change(15,2,[('the parasite','the **parasite**'),('这种寄生菌','这种**寄生菌**(parasite)')])
change(17,1,[("parasite's","**parasite**'s"),('寄生菌','**寄生菌**(parasite)')])
explain='（parasite：泛指寄生生物，包括寄生虫、寄生菌和寄生植物；\n本文特指寄生真菌，所以译为寄生菌。）'
new['sentences'][14]['chunks'][1]['note']+='\n'+explain
named=['fungus','spores','foraging','imaging','muscle fibres','episode','parasite']
new['allow_clash']=list(dict.fromkeys(new.get('allow_clash',[])+named))
assert {k:v for k,v in old.items()if k not in['sentences','allow_clash']}=={k:v for k,v in new.items()if k not in['sentences','allow_clash']}
plain=lambda s:s.replace('**','')
assert [[plain(c['en'])for c in s['chunks']]for s in old['sentences']]==[[plain(c['en'])for c in s['chunks']]for s in new['sentences']]
summary=lambda d:d['sentences'][-1]['chunks'][-1]['note'].split('（简述：',1)[1]
assert summary(old)==summary(new)
text,issues=P.pure_generator(new);assert text and not issues,issues
candidate=HERE/'candidate-payload';(candidate/'视频/脚本').mkdir(parents=True,exist_ok=True);(candidate/'视频/工具/初稿生成').mkdir(parents=True,exist_ok=True);(candidate/'新版定稿').mkdir(exist_ok=True)
(candidate/'视频/脚本/14.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
(candidate/'视频/工具/初稿生成/gen14.py').write_text(text)
md=(before/RELMD).read_text()
md,md_table_and_facts=md.split('## 速查表',1)
replacements=[('A fungus has','A **fungus** has'),('**infectious** spores','**infectious** **spores**'),('where foraging ants','where **foraging** ants'),('**microscope** imaging.','**microscope** **imaging**.'),('around muscle fibres','around **muscle fibres**'),('Earth episode,','Earth **episode**,'),('the parasite jumping','the **parasite** jumping'),("real parasite's","real **parasite**'s"),('一种真菌摧毁','一种**真菌**(fungus)摧毁'),('**真菌**(fungal)','**真菌的**(fungal)'),('**具有传染性的**(infectious)孢子','**具有传染性的**(infectious)**孢子**(spores)'),('那里有觅食的蚂蚁','那里有**觅食的**(foraging)蚂蚁'),('**显微镜**(microscope)成像。','**显微镜**(microscope)**成像**(imaging)。'),('的肌肉纤维周围','的**肌肉纤维**(muscle fibres)周围'),('《地球脉动》的一集，','《地球脉动》的**一集**(episode)，'),('这种寄生菌跳到了','这种**寄生菌**(parasite)跳到了'),('现实中的寄生菌，','现实中的**寄生菌**(parasite)，'),('envision sb/sth doing：设想……做某事）','envision sb/sth doing：设想……做某事）'+explain.replace('\n',''))]
for a,b in replacements:assert md.count(a)==1,(a,md.count(a));md=md.replace(a,b)
md+='## 速查表'+md_table_and_facts
oldrow='| fungal | 本文：真菌；adj. 真菌的（a fungal infection） | 2 |';assert oldrow in md
md=md.replace(oldrow,'| fungal | 本文：真菌的；adj. 真菌的（a fungal infection） | 2 |')
rows=[('| muscles |','| fungus | 本文：真菌；n. 真菌（a fungus） | 2 |'),('| tread |','| spores | 本文：孢子；n. (spore) 孢子（fungal spores） | 2 |\n| foraging | 本文：觅食的；v. (forage) 觅食；此处为现在分词作定语（foraging ants） | 2 |'),('| intertwined |','| imaging | 本文：成像；n. 成像（microscope imaging） | 4 |'),('| evokes |','| muscle fibres | 本文：肌肉纤维；n. pl. 肌肉纤维（muscle fibre 的复数） | 4 |'),('| narration |','| episode | 本文：一集；n. （电视剧、纪录片等的）一集（a Planet Earth episode） | 5 |'),('| hypothetical |','| parasite | 本文：寄生菌；n. 寄生生物，包括寄生虫、寄生菌和寄生植物；本文特指寄生真菌 | 5 |')]
for start,row in rows:
    lines=md.splitlines();hits=[i for i,l in enumerate(lines)if l.startswith(start)];assert len(hits)==1
    lines.insert(hits[0],row);md='\n'.join(lines)+'\n'
(candidate/RELMD).write_text(md)
diff=P.differences(old,new);(HERE/'exact-source-diff.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2)+'\n')
report={'article':'14','book_order':'21','scope':'Eight latest user instructions only; presentation, meaning, focus and requested explanatory note','before_source_sha256':sha(before/'视频/脚本/14.json'),'candidate_source_sha256':sha(candidate/'视频/脚本/14.json'),'candidate_generator_sha256':sha(candidate/'视频/工具/初稿生成/gen14.py'),'candidate_manuscript_sha256':sha(candidate/RELMD),'all_spoken_English_and_chunk_boundaries_exact':True,'all_original_non_sentence_audio_render_metadata_exact':True,'original_five_point_summary_exact':True,'named_focus_clash_exemption_only':named,'unrelated_fungus_or_Fungal_occurrences_newly_highlighted':False,'changes':diff,'source_publish_executed':False,'native_video_render_or_dispatch_executed':False}
(HERE/'proposal-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='changes'},ensure_ascii=False))
