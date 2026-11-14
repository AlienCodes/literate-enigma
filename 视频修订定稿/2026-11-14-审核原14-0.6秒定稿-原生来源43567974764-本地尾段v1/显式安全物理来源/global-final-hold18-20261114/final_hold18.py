"""Scoped user051 final-body hold transform; no sound DSP or alternate encoder."""
import ast,hashlib
from fractions import Fraction
BASE_MODULE_SHA256='cafd2b74b2336cc371ee71ac29181bd21991059572943e5364da933192e2329e'
FINAL_KIND='last-body-hold18-then-summary60'
FINAL_IDS=frozenset(('14','27','13','26','15','17','36','33','47','34','62'))
POLICY_SHA256='4bcae46b68b9584f107966f683af580b474fa9835f101834fe55ed6968dfc36b'
def pinned_module(path):
 assert hashlib.sha256(path.read_bytes()).hexdigest()==BASE_MODULE_SHA256

def patch_end_card_source(body, source_id, hold_frames):
 assert isinstance(hold_frames,int) and not isinstance(hold_frames,bool)
 if hold_frames==0:return body
 assert str(source_id).zfill(2) in FINAL_IDS and hold_frames==18
 replacements=[
 ('    transition_frame = math.ceil(speech_end * fps)\n','    speech_ceiling_frame = math.ceil(Fraction(str(speech_end)) * fps)\n    transition_frame = speech_ceiling_frame + 18\n'),
 ('    assert 0 <= transition - speech_end < 1/fps\n','    assert Fraction(18, 1)/fps <= Fraction(transition_frame, 1)/fps-Fraction(str(speech_end)) < Fraction(19, 1)/fps\n'),
 ("    freeze_at = min(removal.get('old_card_start', transition_frame), transition_frame)\n","    freeze_at = min(removal.get('old_card_start', speech_ceiling_frame), speech_ceiling_frame)\n"),
 ("    graph += f',trim=end_frame={body_tail_frames}[base];'\n","    graph += f',trim=end_frame={body_tail_frames},setpts=N/(30*TB)[base];'\n"),
 ("'delay_after_voice_seconds':transition-speech_end","'delay_after_voice_seconds':float(Fraction(transition_frame, 1)/fps-Fraction(str(speech_end)))"),
 ("'kind':'immediate-standalone-summary'","'kind':'last-body-hold18-then-summary60','preview_only':False,'finalization_authorized':True,'last_body_hold_frames':18,'last_body_hold_seconds':0.6,'unheld_voice_ceiling_frame':speech_ceiling_frame,'held_body_reference_frame':speech_ceiling_frame-1"),
 ('next-frame summary; exactly 60 end-page frames.','user051 authorised final: eighteen cloned last-body frames, then exactly60 summary frames.')]
 for old,new in replacements:
  assert body.count(old)==1,'Pinned end-card function changed: '+old[:60]
  body=body.replace(old,new)
 ast.parse(body);return body

def selftest(body):
 for n in range(1,71):assert patch_end_card_source(body,str(n),0)==body
 for n in FINAL_IDS:patch_end_card_source(body,n,18)
 bad=[('28',18),('61',18),('02',18),('17',9),('17',17),('17',19),('17',True)]
 for no,count in bad:
  try:patch_end_card_source(body,no,count)
  except AssertionError:pass
  else:raise AssertionError((no,count))
 # Decimal endpoint at exact video frame boundary: no floating-point .59999998 false failure.
 for end in ('139.7','138.27','132.645'):
  x=Fraction(end);ceil=-(-x*30//1);gap=Fraction(ceil+18,30)-x
  assert Fraction(18,30)<=gap<Fraction(19,30)
 return {'all70_default_source_bytes_exact':True,'eleven_explicit_final_ids_only':True,'seven_bad_scope_or_count_rejected':True,'exact_decimal_boundary_geometry_passed':True}
