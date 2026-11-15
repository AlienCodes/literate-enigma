"""Pure exact56/S11 contract tests; no model import or source/mother write."""
from pathlib import Path
import argparse,ast,copy,json,re,unittest
DISPLAY='The compromise, struck without Wallace, may have kept rivalry over precedence at bay.'
PROJECTED='The compromise struck without Wallace, may have kept rivalry over precedence at bay.'

def pure(path):
 names={'_speech_comma_spec','_speech_comma_display_for_data','_speech_source_context','_speech_rule','_speech_mother_guard'}
 nodes=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names or isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_SPOKEN_COMMA_ALLOWED'for t in n.targets)]
 env={'re':re,'SPOKEN_COMMA':{},'_SPOKEN_SOURCE_NO':None};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env);return env
def data56():
 d=json.loads(A.baseline56.read_text());d['朗读删逗号']={'S11':{'篇号':56,'原文':DISPLAY,'逗号序号':[1]}};return d
def simple(no,label,text):
 s=[{'chunks':[{'en':'Unchanged context.'}]}for _ in range(int(label[1:]))];s[-1]={'chunks':[{'en':text}]};return{'no':no,'sentences':s,'朗读删逗号':{label:{'篇号':int(no),'原文':text,'逗号序号':[1]}}}

class Exact56Tests(unittest.TestCase):
 def test_prior21_rejects_new56(self):
  with self.assertRaises(SystemExit):pure(A.prior21)['_speech_comma_spec'](data56(),'S11')
 def test_exact_first_compromise_comma_only_without_and_second_comma_retained(self):
  d=data56();before=copy.deepcopy(d);p=pure(A.candidate)['_speech_comma_spec'](d,'S11');self.assertEqual(p['original'],DISPLAY);self.assertEqual(p['projected'],PROJECTED);self.assertEqual(p['projected'].count(','),1);self.assertIn('without Wallace, may',p['projected']);self.assertEqual(d,before);self.assertTrue(p['needs_mother_binding'])
 def test_all_seven_prior_case_parser_outputs_exact_to21(self):
  cases=[(json.loads(A.fixture43.read_text()),['S16']),(json.loads(A.fixture52.read_text()),['S4','S18']),(json.loads(A.fixture24.read_text()),['S18']),(simple('68','S2','Its amenities included a lounge and, that year, a grand piano.'),['S2']),(simple('35','S15','In 2014 came an eerie, man-made twist.'),['S15']),(json.loads(A.fixture23.read_text()),['S13'])]
  for d,labels in cases:
   for label in labels:
    with self.subTest(no=d['no'],label=label):self.assertEqual(pure(A.prior21)['_speech_comma_spec'](d,label),pure(A.candidate)['_speech_comma_spec'](d,label))
 def test_wrong_source_sentence_ordinal_type_or_extra_field_rejected(self):
  for field,value in [('no','55'),('no','65'),('label','S10'),('label','S12'),('ordinal',[0]),('ordinal',[2]),('ordinal',[1,2]),('ordinal',[]),('ordinal',[True]),('ordinal',['1']),('type','56'),('extra',True)]:
   d=data56();s=d['朗读删逗号']['S11'];label='S11'
   if field=='no':d['no']=value;s['篇号']=int(value)
   elif field=='label':label=value;d['朗读删逗号'][label]=d['朗读删逗号'].pop('S11')
   elif field=='ordinal':s['逗号序号']=value
   elif field=='type':s['篇号']=value
   else:s['extra']=value
   with self.subTest(field=field,value=value),self.assertRaises(SystemExit):pure(A.candidate)['_speech_comma_spec'](d,label)
 def test_changed_full_display_with_instead_of_without_or_second_comma_rejected(self):
  for text in [DISPLAY.replace('without','with'),DISPLAY.replace('compromise','agreement'),DISPLAY.replace('Wallace,','Wallace;'),DISPLAY.replace('compromise,','compromise;')]:
   d=data56();d['sentences'][10]={'chunks':[{'en':text}]};d['朗读删逗号']['S11']['原文']=text
   with self.subTest(text=text),self.assertRaises(SystemExit):pure(A.candidate)['_speech_comma_spec'](d,'S11')
  with self.assertRaises(SystemExit):pure(A.candidate)['_speech_comma_display_for_data'](data56(),'S11',DISPLAY+' extra')
 def test_target_ending_or_synth_conflict_rejected(self):
  for field in ['结尾句','合成标点']:
   d=data56();d.setdefault(field,{})['S11']={'old':True}
   with self.subTest(field=field),self.assertRaises(SystemExit):pure(A.candidate)['_speech_comma_spec'](d,'S11')
 def test_stale_mother_missing_context_and_other_source_not_authorized(self):
  d=data56();e=pure(A.candidate);r=e['_speech_comma_spec'](d,'S11');e['SPOKEN_COMMA']={('56','S11'):r}
  with self.assertRaises(SystemExit):e['_speech_rule'](DISPLAY)
  e['_SPOKEN_SOURCE_NO']='23';self.assertIsNone(e['_speech_rule'](DISPLAY));e['_SPOKEN_SOURCE_NO']='56'
  for old in [{},{DISPLAY:'3920886d5bff'}]:
   e['VFP']=old
   with self.subTest(old=old),self.assertRaises(SystemExit):e['_speech_mother_guard'](DISPLAY,'pure-test-not-a-real-new-mother')

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ['candidate','prior21','baseline56','fixture23','fixture24','fixture43','fixture52']:p.add_argument('--'+name,type=Path,required=True)
 A,rest=p.parse_known_args();unittest.main(argv=[__file__]+rest,verbosity=2)
