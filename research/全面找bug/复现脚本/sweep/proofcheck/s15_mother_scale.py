"""老师自己的 1005 句（母本 = 正确的文字）当成一批素材：准备素材时自动查错字 → 一键全部文字校正 → 加新素材（又自动查一遍）。
数一数：一键清掉的红字，加新素材以后又回来多少。"""
import time
from common import *
pc._has = lambda m: False  # 没有第二个引擎（只用规则），不加载任何模型
m = [x for _, x in tf.builtin_mother()]
cfg, project = voice(m, write_wav=False)
def red_rows():
    d = review.load_draft(project)
    return sum(1 for r in project.load_manifest()
               if review.analyze(r, review.current_values(r, d.get(r["id"]))["text"])["active"])
t = time.time()
r1 = pc.find_suspects(project, cfg)
print("auto check at prepare:", r1["flagged"], "rows red;", red_rows(), "active", round(time.time() - t, 1), "s")
t = time.time()
res = wf.run_transcript_fix(cfg, "v", once=True)
print("one-click:", "cleared", res.get("cleared"), "fixes", res.get("fixes"), "->", red_rows(), "rows red", round(time.time() - t, 1), "s")
r2 = pc.find_suspects(project, cfg)  # 加新素材时准备素材会对所有句子再查一遍（或者老师点 🔍）
print("auto check again:", r2["flagged"], "flagged;", red_rows(), "rows red; one-click button grey:", tf.textfix_used(project))
