import re, sys
sys.path.insert(0, "/home/user/postgraduate-vocabulary/scripts")
from core import count_words
t = open(sys.argv[1], encoding="utf-8").read()
body = re.sub(r"^#.*$", "", t, flags=re.M)
paras = [p.strip() for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
tot = 0
for i, p in enumerate(paras, 1):
    b = re.findall(r"\*\*([^*]+)\*\*", p)
    wc = count_words(p); tot += wc
    print("P%d words=%d bold=%d" % (i, wc, len(b)))
    for s in re.split(r"(?<=[a-z0-9'\)])[.](?=\s+[A-Z])", re.sub(r"\*\*", "", p)):
        print("   [%d] %s" % (count_words(s), s.strip()[:90]))
print("total", tot)
