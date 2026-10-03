"""Web UI: 开始训练 (blocked when unconfirmed; then success incl. auto selection) and 重新挑选最佳模型."""
import common
from common import fresh, wf, VOICE
from voicetwin.data import review
from voicetwin.webui import app as A
cfg, project, root, tmp = fresh("webtrain")
ui = A.WebUI(cfg)
O = ui.TRAIN_OUT
review.confirm_path(project).unlink()
outs = list(ui.do_train(VOICE, "gptsovits", 0, 0, 0, 0, "auto"))
d = dict(zip(O, outs[-1])); print("unconfirmed ->", str(d["train_log"])[:120])
print("   reports:", list(project.logs_dir.glob("问题报告_*")))
wf.review_confirm(cfg, VOICE)
outs = list(ui.do_train(VOICE, "gptsovits", 0, 0, 0, 0, "auto"))
d = dict(zip(O, outs[-1])); print("train md ->", str(d["train_md"])[:500])
m = project.load_models()["gptsovits"]
print("   selected", m["selected"]["id"], "| selection best", (m.get("selection") or {}).get("best"), "| speed", m.get("speed"))
hdr = A.header_md(cfg, VOICE) if hasattr(A, "header_md") else ""
print("   header:", str(hdr)[:200])
