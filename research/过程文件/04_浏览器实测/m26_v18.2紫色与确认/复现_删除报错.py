import json, shutil, sys
sys.path.insert(0, "tests")
from pathlib import Path
from conftest import make_cfg, make_lecture
from voicetwin import workflows as wf
from voicetwin.webui import app as A
root = Path("./_复现")
shutil.rmtree(root, ignore_errors=True); root.mkdir()
make_lecture(root / "0006.wav", with_srt=False)
cfg = make_cfg(root / "ws", prepare={"asr": {"engine": "none"}})
try:
    wf.run_prepare(cfg, "v", [str(root)])
except Exception as e:
    print("prepare:", type(e).__name__, e)
p = wf.Project(cfg, "v")
recs = p.load_manifest()
print(len(recs), "clips; text empty:", sum(1 for r in recs if not r.get("text")), "keep:", sum(1 for r in recs if r.get("keep")))
# 老师的情况：切好了、识别没做完（manifest 里 keep 还是 True）
for r in recs:
    r["keep"] = True; r.pop("asr_done", None)
p.save_manifest(recs)
ui = A.WebUI(cfg)
out = ui.do_clip_action("v", json.dumps({"action": "delete", "id": recs[0]["id"], "no": "1"}), False)
print("delete result:", out[0][:120] if isinstance(out[0], str) else out[0])
cnt, rows = ui.load_clips("v")
print(cnt)
print(rows[0][4], "|", rows[0][7][:200])
print(rows[1][4], "|", rows[1][7][:200])
