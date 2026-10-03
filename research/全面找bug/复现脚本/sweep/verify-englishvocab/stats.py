import sys, re, collections
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.data import transcript_fix as tf, proofcheck as pc
m = [x for _, x in tf.builtin_mother()]
mv = pc._mother_vocab()
print("mother sentences", len(m), "mother english vocab size", len(mv))
print("CONFUSABLE_EN not in mother vocab:", sorted(pc.CONFUSABLE_EN - mv))
print("CONFUSABLE_SOFT not in mother vocab:", sorted(pc.CONFUSABLE_SOFT - mv))
# sentences with many english words
def nlat(t): return len(re.findall(r"[A-Za-z]+", t))
many = sorted(m, key=nlat, reverse=True)[:8]
for t in many: print(nlat(t), t[:90])
print("sentences with >=3 english words:", sum(1 for t in m if nlat(t) >= 3), "with >=6:", sum(1 for t in m if nlat(t) >= 6))
