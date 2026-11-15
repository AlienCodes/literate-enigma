"""Exact23 parser/guards only. No model import, new mothers or native certificate."""
from pathlib import Path
import argparse,ast,copy,json,re,unittest
DISPLAY='He forfeited his security clearance and, to avert imprisonment, submitted to hormone injections.'
PROJECTED='He forfeited his security clearance and to avert imprisonment, submitted to hormone injections.'

def pure(path):
 names={'_speech_comma_spec','_speech_comma_display_for_data','_speech_source_context','_speech_rule','_speech_mother_guard'}
 nodes=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names or isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_SPOKEN_COMMA_ALLOWED'for t in n.targets)]
 env={'re':re,'SPOKEN_COMMA':{},'_SPOKEN_SOURCE_NO':None}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env);return env

def source23():return json.loads(A.fixture23.read_text())
def simple(no,label,text):
 sentences=[{'chunks':[{'en':'Unchanged context.'}]}for _ in range(int(label[1:]))];sentences[-1]={'chunks':[{'en':text}]}
 return{'no':no,'sentences':sentences,'朗读删逗号':{label:{'篇号':int(no),'原文':text,'逗号序号':[1]}}}

class Exact23Tests(unittest.TestCase):
 def test_prior20_rejects_new23(self):
  with self.assertRaises(SystemExit):pure(A.prior20)['_speech_comma_spec'](source23(),'S13')
 def test_exact_first_comma_removed_display_S19_and_all_source_fields_unchanged(self):
  d=source23();before=copy.deepcopy(d);p=pure(A.candidate)['_speech_comma_spec'](d,'S13')
  self.assertEqual(p['original'],DISPLAY);self.assertEqual(p['projected'],PROJECTED);self.assertEqual(p['projected'].count(','),1);self.assertIn('imprisonment, submitted',p['projected']);self.assertEqual(d,before)
  self.assertEqual(d['结尾句']['S19']['整句语速'],.8);self.assertTrue(p['needs_mother_binding'])
  s=json.loads(A.shadow23.read_text());q=pure(A.candidate)['_speech_comma_spec'](s,'S13');self.assertFalse(q['needs_mother_binding']);self.assertEqual(q['projected'],PROJECTED);self.assertEqual(s['结尾句'],d['结尾句'])
 def test_all_six_old_case_parser_outputs_exact_to_actual20(self):
  cases=[(json.loads(A.fixture43.read_text()),['S16']),(json.loads(A.fixture52.read_text()),['S4','S18']),(json.loads(A.fixture24.read_text()),['S18']),
         (simple('68','S2','Its amenities included a lounge and, that year, a grand piano.'),['S2']),(simple('35','S15','In 2014 came an eerie, man-made twist.'),['S15'])]
  for d,labels in cases:
   for label in labels:
    with self.subTest(no=d['no'],label=label):self.assertEqual(pure(A.prior20)['_speech_comma_spec'](d,label),pure(A.candidate)['_speech_comma_spec'](d,label))
 def test_wrong_source_sentence_ordinal_and_types_rejected(self):
  for field,value in [('no','22'),('no','24'),('label','S12'),('label','S14'),('ordinal',[2]),('ordinal',[1,2]),('ordinal',[]),('ordinal',[True]),('ordinal',['1']),('type','23'),('extra',True)]:
   d=source23();s=d['朗读删逗号']['S13'];label='S13'
   if field=='no':d['no']=value;s['篇号']=int(value)
   elif field=='label':label=value;d['朗读删逗号'][label]=d['朗读删逗号'].pop('S13')
   elif field=='ordinal':s['逗号序号']=value
   elif field=='type':s['篇号']=value
   else:s['extra']=value
   with self.subTest(field=field,value=value),self.assertRaises(SystemExit):pure(A.candidate)['_speech_comma_spec'](d,label)
 def test_changed_full_display_or_mismatched_reference_rejected(self):
  for text in [DISPLAY.replace('forfeited','lost'),DISPLAY.replace('hormone','hormonal'),DISPLAY.replace('and,','and;'),DISPLAY.replace('imprisonment,','imprisonment;')]:
   d=source23();d['sentences'][12]={'chunks':[{'en':text}]};d['朗读删逗号']['S13']['原文']=text
   with self.subTest(text=text),self.assertRaises(SystemExit):pure(A.candidate)['_speech_comma_spec'](d,'S13')
  with self.assertRaises(SystemExit):pure(A.candidate)['_speech_comma_display_for_data'](source23(),'S13',DISPLAY+' extra')
 def test_target_ending_or_synth_conflict_rejected_non_target_ending_preserved(self):
  for field in ['结尾句','合成标点']:
   d=source23();d.setdefault(field,{})['S13']={'old':True}
   with self.subTest(field=field),self.assertRaises(SystemExit):pure(A.candidate)['_speech_comma_spec'](d,'S13')
  self.assertIsNotNone(pure(A.candidate)['_speech_comma_spec'](source23(),'S13'))
 def test_old_mother_missing_context_and_opposite_source_not_authorized(self):
  d=source23();e=pure(A.candidate);rule=e['_speech_comma_spec'](d,'S13');e['SPOKEN_COMMA']={('23','S13'):rule}
  with self.assertRaises(SystemExit):e['_speech_rule'](DISPLAY)
  e['_SPOKEN_SOURCE_NO']='24';self.assertIsNone(e['_speech_rule'](DISPLAY))
  e['_SPOKEN_SOURCE_NO']='23'
  for old in [{},{DISPLAY:'662daf5f3713'}]:
   e['VFP']=old
   with self.subTest(old=old),self.assertRaises(SystemExit):e['_speech_mother_guard'](DISPLAY,'pure-test-not-new-real-mother')

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ['candidate','prior20','fixture23','shadow23','fixture24','fixture43','fixture52']:p.add_argument('--'+name,type=Path,required=True)
 A,rest=p.parse_known_args();unittest.main(argv=[__file__]+rest,verbosity=2)
