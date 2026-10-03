"""Probe: which transcript_fix fixes survive _protect next to a teacher-changed char, and what spans they produce."""
import sys
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.data import transcript_fix as tf
from voicetwin.data.lexicon_fix import Lexicon, resolve

orig = "首先我们看一个主语从句的例子。"
cur = "首先我们看一个宾语从句的例子。"
rec = {"id": "x", "text": cur, "orig_text": orig}
changed = tf._changed_chars(rec, cur)
print("changed:", changed)
mothers = ["首先我们看一个双宾语从句的例子。", "首先我们来看一个双宾语从句的例子。", "首先我们看一下双宾语从句的例子。",
           "首先我们看一个间接宾语从句的例子。", "首先我们看几个宾语从句的例子。", "首先我们看一个个宾语从句的例子。",
           "首先我们看一个双宾语从句的简单例子。"]
builtin = list(tf.builtin_mother())
for m in mothers:
    lines = builtin + [("", m)]
    ref = tf.Reference(lines, own_from=len(builtin))
    lex = Lexicon.build([x for _, x in lines])
    res = tf.check_text(cur, ref, exclude_id="x", exclude_texts=(cur, orig))
    fixes = lex.find(cur) + tf.props_to_fixes(cur, res, lex)
    kept = tf._protect(fixes, cur, changed, lex)
    sus, what, direct = tf.merge_with_auto(cur, kept, res.confirmed_chars, None, rec, res.ref_text, lex,
                                           rejected=None, changed=changed)
    print("\nmother:", m)
    print("  props:", [(p.i1, p.i2, p.rep, p.kind, p.strong) for p in res.props])
    print("  fixes:", [(f.start, f.end, f.rep, f.kind, f.direct) for f in fixes])
    print("  kept :", [(f.start, f.end, f.rep) for f in kept])
    print("  core :", [(g.start, g.end, g.rep) for g in (tf._core_fix(cur, f) for f in resolve(list(kept)))])
    print("  sus  :", sus and {k: sus.get(k) for k in ("spans", "alt", "direct_alt", "sure_alt")}, what)
