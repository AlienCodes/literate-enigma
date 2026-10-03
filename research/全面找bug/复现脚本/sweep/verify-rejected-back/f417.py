import fuzz_auto as F
from common import review
orig_voice = F.voice
holder = {}
def v(*a, **k):
    cfg, p = orig_voice(*a, **k); holder["p"] = p; return cfg, p
F.voice = v
F.run(417)
p = holder["p"]
print("violations", dict(F.viol))
print("rejected c003:", review.load_rejected(p).get("c003"))
