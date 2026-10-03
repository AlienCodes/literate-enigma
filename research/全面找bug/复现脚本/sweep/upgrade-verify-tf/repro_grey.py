"""Grey rows (程序判断不能用的, e.g. 语速异常（文字可能不对）) are skipped by the one-click but still marked as used."""
import sys, json
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf
from voicetwin.webui import app as A
WS = Path(sys.argv[1]); V = "我的声音"
cfg = make_cfg(WS); p = wf.open_project(cfg, V, must_exist=True)
ui = A.WebUI(cfg)
grey = [r for r in p.load_manifest() if not r.get("deleted") and not r.get("keep")]
print("grey rows:", [(r["id"], r.get("drop_reason"), r["text"]) for r in grey])
gid = grey[0]["id"]
list(ui.do_textfix(V))
r = {x["id"]: x for x in p.load_manifest()}[gid]
print("after one-click grey row:", review.current_values(r, review.load_draft(p).get(gid))["text"])
print("grey row marked used:", gid in json.loads((p.root / tf.USED_FILE).read_text(encoding="utf-8"))["ids"])
ui.do_save(V)
msg = ui.do_clip_action(V, json.dumps({"action": "use", "id": gid, "no": "1"}))[0]
print("use:", msg[:80])
ui.do_save(V); ui.do_confirm(V)
r = {x["id"]: x for x in p.load_manifest()}[gid]
print("now training material:", review.is_material(r), r["text"])
print("button:", ui.textfix_btn(V)["interactive"])
