"""While 「③ 生成讲课音频」 runs in the background (GPT-SoVITS through the REAL api_v2.py, fake models), the teacher goes
back to the 校对表 and deletes one sentence (it happens to be a reference clip).  The edit guard only blocks the
table during prepare / proofcheck / textfix, so this is allowed.  Every review save/delete/restore/confirm runs
apply_review -> select_references(), which unlinks references/*.wav and writes a new set.  The running narration
still points at the old files.

usage: race_refs_during_generate.py [delete|save]
  delete: teacher deletes the main Chinese reference sentence  (reference set changes)
  save  : teacher only saves an edit of some other sentence     (same reference set, files rewritten)
"""
import os
import socket
import sys
import sysconfig
import threading
import time

from common import REPO, cleanup, lecture, make_cfg, workspace

sys.path.insert(0, str(REPO / "tests"))
from fake_gptsovits import build_fake_root  # noqa: E402

from voicetwin import workflows as wf  # noqa: E402
from voicetwin.backends.gptsovits import GPTSoVITSBackend  # noqa: E402
from voicetwin.data import review  # noqa: E402
from voicetwin.errors import explain  # noqa: E402

mode = sys.argv[1] if len(sys.argv) > 1 else "delete"
GPTSoVITSBackend.ensure_users_pth = lambda self: None
GPTSoVITSBackend._gpu_memory = lambda self, quick=False: (11.99, 11.2, "test")
GPTSoVITSBackend.POLL_SECONDS = 0.05
os.environ["FAKE_GSV_CLIP_SLEEP"] = "0.0"
paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
os.environ["PYTHONPATH"] = os.pathsep.join(p for p in dict.fromkeys(paths) if p)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

V = "张老师"
ws = workspace("refrace")
root = build_fake_root(ws / "GPT-SoVITS", real_api=True)
cfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
    "root": str(root), "python": sys.executable, "port": PORT, "startup_timeout": 60, "is_half": True,
    "train": {"sovits_epochs": 1, "gpt_epochs": 1, "batch_size": 2}}})
wf.run_prepare(cfg, V, [str(lecture(2))])
wf.review_confirm(cfg, V)
wf.run_train(cfg, V, "gptsovits", select=False)
p = wf.open_project(cfg, V, must_exist=True)
refs = p.load_references()
main_zh = next(r for r in refs if r["lang"] == "zh")
print("references:", [r["id"][-4:] for r in refs], "main zh:", main_zh["id"][-4:])

script = "\n\n".join(f"这是讲稿里的第{i}句话，我们一句一句地生成。" for i in range(1, 9))
progress_msgs = []
result = {}


def gen():
    try:
        r = wf.run_narrate(cfg, V, script, out=str(ws / "讲稿.wav"), backend_name="gptsovits", quality="balanced",
                           progress=lambda f, m: progress_msgs.append(m))
        result["ok"] = f"OK {r.duration:.1f}s, warnings={r.warnings[:2]}"
    except Exception as exc:
        result["ok"] = f"FAILED {type(exc).__name__}: {str(exc).splitlines()[0][:110]} | teacher sees: {explain(exc).title}"


t = threading.Thread(target=gen)
t.start()
while not any(m.startswith("[2/8]") for m in progress_msgs) and t.is_alive():
    time.sleep(0.05)
if mode == "delete":
    wf.review_delete(cfg, V, main_zh["id"])   # teacher deletes one sentence in the table
    print("teacher: deleted", main_zh["id"][-4:], "-> new references:", [r["id"][-4:] for r in p.load_references()])
else:
    other = next(r for r in p.load_manifest() if r.get("text") and r["id"] not in {x["id"] for x in refs})
    review.set_draft(p, other["id"], text=other["text"].replace("。", "！"))
    wf.review_save(cfg, V)
    print("teacher: saved an edit of", other["id"][-4:])
t.join()
print("generation:", result.get("ok"))
cleanup()
