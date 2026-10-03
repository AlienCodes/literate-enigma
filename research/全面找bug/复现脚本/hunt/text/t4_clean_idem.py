import random
from h import *
from voicetwin.utils.textutil import clean_transcript as C
rng = random.Random(1)
alpha = list("中文a b,.?!;:()（）。，  1\t") + ["as", "我们", "the", "　", "．", "︰"]
found = {}
for _ in range(200000):
    s = "".join(rng.choice(alpha) for _ in range(rng.randrange(1, 9)))
    a = C(s); b = C(a)
    if a != b:
        key = (len(s))
        if len(found) < 12 and s not in found: found[s] = (a, b)
for s, (a, b) in sorted(found.items(), key=lambda x: len(x[0]))[:12]: print(repr(s), "->", repr(a), "->", repr(b))
