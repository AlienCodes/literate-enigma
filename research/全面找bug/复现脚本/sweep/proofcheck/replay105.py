from common import *
import fuzz_auto as F, random
rnd = random.Random(105)
texts = [rnd.choice(F.BASE) for _ in range(6)]
print(texts)
cfg, project = voice(texts)
ids = [r["id"] for r in project.load_manifest()]
fake_engine({i: F.HEARD[F.BASE.index(t)] for i, t in zip(ids, texts)})
wf.run_transcript_fix(cfg, "v", once=True)
pc.dismiss_suspect(project, "c002")
for rid, fn in (("c001", review.unadopt_suggestion), ("c005", review.adopt_suggestion)):
    try: fn(project, rid)
    except ValueError as e: print(rid, "skip:", str(e)[:30])
for i in ids: show(project, i, "before auto")
res = pc.find_suspects(project, cfg)
print("flagged:", res["flagged"])
for i in ids: show(project, i, "after auto")
