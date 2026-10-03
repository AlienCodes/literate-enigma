import logging
from common import *
logging.disable(logging.CRITICAL)
for saved, fixed in [("这个这个这个 VFIXED 很重要", "这个 VFIXED 很重要"), ("这个这个这个函数 VFIXED 很重要", "这个函数 VFIXED 很重要")]:
    cfg, project = voice([saved])
    fake_engine({"c000": saved})
    pc.find_suspects(project, cfg)
    rec, t = cur(project, "c000")
    sus = rec["suspect"]
    print("spans", sus.get("spans"), [t[s:e] for s, e in sus["spans"]], sus.get("reasons"))
    ops = review._opcodes(saved, fixed)
    print("ops", ops)
    for s, e in sus["spans"]:
        print((s, e), "touched", review.touched(ops, s, e), "repeat_run", review._repeat_run(saved, s, e), "repeat_fixed", review._repeat_fixed(ops, saved, s, e))
    a = review.analyze(rec, fixed)
    print("red", [fixed[s:e] for s, e in a["red"]])
