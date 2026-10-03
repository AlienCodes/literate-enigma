"""一键全部文字校正说「母本证明没错」把自动查错字的标红去掉了；再点「🔍 自动查找」又标红回来？"""
from common import *
m = [x for _, x in tf.builtin_mother() if "whose" in x or "why" in x]
texts = [m[0], m[0].replace("其实", "那其实", 1) if "其实" in m[0] else m[0] + "啊", m[1]]
cfg, project = voice(texts)
fake_engine({r["id"]: r["text"] for r in project.load_manifest()})  # 第二个引擎听到的完全一样
pc.find_suspects(project, cfg)
for r in project.load_manifest(): show(project, r["id"], "auto (before one-click)")
res = wf.run_transcript_fix(cfg, "v", once=True)
print("one-click cleared:", res.get("cleared"))
for r in project.load_manifest(): show(project, r["id"], "after one-click")
pc.find_suspects(project, cfg)
for r in project.load_manifest(): show(project, r["id"], "auto again")
