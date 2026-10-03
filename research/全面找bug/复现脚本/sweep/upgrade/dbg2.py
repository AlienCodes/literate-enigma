import sys, json
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf
from voicetwin.data.lexicon_fix import Lexicon
WS = Path(sys.argv[1]); V = "我的声音"
cfg = make_cfg(WS); project = wf.open_project(cfg, V, must_exist=True)
recs = project.load_manifest(); r = recs[int(sys.argv[2])]
cur = r["text"]
builtin = list(tf.builtin_mother()); lex = Lexicon.build([x for _, x in builtin])
print("cur:", cur)
print("lex.find:", [(f.start, f.end, f.rep, f.direct, f.kind) for f in lex.find(cur)])
changed = tf._changed_chars(r, cur)
print("changed:", changed)
prot = tf._protect(lex.find(cur), cur, changed, lex)
print("after protect:", [(f.start, f.end, f.rep) for f in prot])
