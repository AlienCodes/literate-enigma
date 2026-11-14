from pathlib import Path
import ast
W=Path(__file__).resolve().parent;OLD=Path('/workspace/work/review35-source53-hold06-20261114')
s=(OLD/'produce_new_native061_upstream.py').read_text()
for old,new in {
"assert no == '53'":"assert no == '07'",
'b82966baa6439b194a6fa1e2c222f226517982318ef398ae631efcd5c562d588':'3ba931446468d28e2d1eea2fa57ddf1c79b24bad52be4fbd697a828c7865dede',
'cb40c9e82c60f1991c7b0f5ba2a779b4ef28886f3c87298cbe3bcc0d30529b1b':'16b6293adfc7a3c35224408ae39d831317e1932f8d47876824e129129c9115d8',
'f6a02b14660a6498691b507a327569f3a7718258b215f17764228afe668af4d2':'11edc969af0797bcd7121034f43de130d72ca9186508e64e3330aff6c4069643',
'AUTH061':'AUTH090','USER-REVIEW-2026-11-14-061.json':'USER-REVIEW-2026-11-14-090.json',
'46821260a9699626904c96f33772ce1941e021519fcc5bbbea428f14fadfac5f':'3120efc6893981436cb81458ce57f6aca7601edc5e7326cce1388b68de959001',
"expected={'53':'73393dad5d67261f2ec7819f3749a6589278900e2f214a1da06b0dbde55fe31b'}":"expected={'07':'b9b4ec0b90a4d1070b193fe42f5c30e1a3717560b03746a06d4b16388a83047f'}",
"default=Path('/dev/shm/normal-final-hold18-upstream')":"default=Path('/dev/shm/source07-user090-hold06-20261114/upstream')"}.items():s=s.replace(old,new)
ast.parse(s);(W/'produce_new_native090_upstream.py').write_text(s)
s=(OLD/'compose_new_native061.py').read_text()
for old,new in {
"RAM=Path('/dev/shm/review35-source53-hold06-20261114')":"RAM=Path('/dev/shm/source07-user090-hold06-20261114')",
"choices=['53']":"choices=['07']","book='35'":"book='03'",
'cb40c9e82c60f1991c7b0f5ba2a779b4ef28886f3c87298cbe3bcc0d30529b1b':'16b6293adfc7a3c35224408ae39d831317e1932f8d47876824e129129c9115d8',
'illustrated_tail061.py':'illustrated_tail090.py','USER-REVIEW-2026-11-14-061.json':'USER-REVIEW-2026-11-14-090.json',
'user061-only-book35-source53-actual-reviewed-text-original-voice-hold18-ready':'user090-source07-qualitybook03-videoorder01-reviewed-text-original-voice-hold18-ready',
'46821260a9699626904c96f33772ce1941e021519fcc5bbbea428f14fadfac5f':'3120efc6893981436cb81458ce57f6aca7601edc5e7326cce1388b68de959001',
'all_current_accepted53_audio_packets_and_absolute_clock_preserved_required':'all_current_first34_accepted07_audio_packets_and_absolute_clock_preserved_required',
"'book_order':book,'source_id':no":"'book_order':book,'source_id':no,'requested_video_order':'01','frozen_quality_book_order':'03'"}.items():s=s.replace(old,new)
ast.parse(s);(W/'compose_new_native090.py').write_text(s)
print('Exact user090 pure-voice source07 post-only producers prepared; qualitybook03 retained, requested video order01 is metadata only.')
