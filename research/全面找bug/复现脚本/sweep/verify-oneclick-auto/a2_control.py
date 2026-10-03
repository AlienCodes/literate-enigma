from common import *
install_fake()
texts = ["我们今天天气很好", "下面我们来看第二个例子", "那么到底什么是定语从句呢"]
ids = ["k1", "k2", "k3"]
cfg, project = voice(texts, ids=ids)
ANS.update({"k1": "我们今天天汽很好", "k2": "下面我们来看第二个列子", "k3": "那么到底什么是定语从局呢"})
r = wf.run_proofcheck(cfg, "v")
print("control (no one-click): flagged", r["flagged"])
for i in ids: print(" ", i, state(project, i))
# now same voice: one-click (button) then 🔍 again
res = wf.run_transcript_fix(cfg, "v", once=True)
print("one-click cleared", res.get("cleared"), "found", res.get("found"))
for i in ids: print(" after one-click", i, state(project, i))
r = wf.run_proofcheck(cfg, "v")
print("🔍 again flagged", r["flagged"])
for i in ids:
    rec = {x["id"]: x for x in project.load_manifest()}[i]
    print(" after 🔍", i, state(project, i), "| suspect_auto:", rec.get("suspect_auto"))
