"""Scoped source transform of the existing end-card function; never audio DSP.

The default source is returned byte-for-byte. Only user-requested article28
preview adds eighteen cloned last-body frames. The original frame/audio validators
and the original encoder/stream-copy path remain in the same function.
"""
import ast
import hashlib

BASE_MODULE_SHA256 = 'cafd2b74b2336cc371ee71ac29181bd21991059572943e5364da933192e2329e'
PREVIEW_KIND = 'preview-last-body-hold18-then-summary60'


def patch_end_card_source(body, source_id, hold_frames):
    assert isinstance(hold_frames, int) and not isinstance(hold_frames, bool)
    if hold_frames == 0:
        return body
    assert str(source_id).zfill(2) == '28' and hold_frames == 18, 'Only28 has a eighteen-frame effect preview.'
    replacements = [
        ('    transition_frame = math.ceil(speech_end * fps)\n',
         '    speech_ceiling_frame = math.ceil(speech_end * fps)\n'
         '    transition_frame = speech_ceiling_frame + 18\n'),
        ('    assert 0 <= transition - speech_end < 1/fps\n',
         '    assert 18/fps <= transition - speech_end < 19/fps\n'),
        ("    freeze_at = min(removal.get('old_card_start', transition_frame), transition_frame)\n",
         "    freeze_at = min(removal.get('old_card_start', speech_ceiling_frame), speech_ceiling_frame)\n"),
        ("    graph += f',trim=end_frame={body_tail_frames}[base];'\n",
         "    graph += f',trim=end_frame={body_tail_frames},setpts=N/(30*TB)[base];'\n"),
        ("'kind':'immediate-standalone-summary'",
         "'kind':'preview-last-body-hold18-then-summary60','preview_only':True,"
         "'preview_last_body_hold_frames':18,'preview_last_body_hold_seconds':0.6,"
         "'unheld_voice_ceiling_frame':speech_ceiling_frame,"
         "'held_body_reference_frame':speech_ceiling_frame-1"),
        ('next-frame summary; exactly 60 end-page frames.',
         'user preview: eighteen cloned last-body frames, then exactly60 summary frames.'),
    ]
    for old, new in replacements:
        assert body.count(old) == 1, 'Pinned end-card source changed: '+old[:60]
        body = body.replace(old, new)
    ast.parse(body)
    return body


def pinned_module(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == BASE_MODULE_SHA256


def selftest(body):
    for n in range(1,71):
        assert patch_end_card_source(body,str(n),0)==body
    patch_end_card_source(body,"28",18)
    for no,frames in [("27",18),("15",18),("28",9),("28",17),("28",19),("28",True)]:
        try: patch_end_card_source(body,no,frames)
        except AssertionError: pass
        else: raise AssertionError((no,frames))
    return {"all70_legacy_default_bytes_identical":True,"only28_hold18_accepted":True,"six_wrong_scopes_or_counts_rejected":True}
