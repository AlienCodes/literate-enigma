"""Full flow with the GPT-SoVITS backend driven through the REAL api_v2.py (fake models), with an awkward voice
name and spaces / Chinese / brackets in every path: prepare -> edit -> delete -> confirm -> train(+select) ->
narrate (balanced) -> digital-silence check between sentences."""
import json
import os
import socket
import sys
import sysconfig
import time

import numpy as np
import soundfile as sf

from common import REPO, cleanup, lecture, make_cfg, workspace

sys.path.insert(0, str(REPO / "tests"))
from fake_gptsovits import build_fake_root  # noqa: E402

from voicetwin import workflows as wf  # noqa: E402
from voicetwin.backends.gptsovits import GPTSoVITSBackend  # noqa: E402
from voicetwin.data import review  # noqa: E402

GPTSoVITSBackend.ensure_users_pth = lambda self: None
GPTSoVITSBackend._gpu_memory = lambda self, quick=False: (11.99, 11.2, "test")
GPTSoVITSBackend.POLL_SECONDS = 0.05
GPTSoVITSBackend.STARTUP_NOTE_SECONDS = 0.4
os.environ["FAKE_GSV_CLIP_SLEEP"] = "0.0"
paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
os.environ["PYTHONPATH"] = os.pathsep.join(p for p in dict.fromkeys(paths) if p)


def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


VOICE = "王老师 的声音（第2版）& #1"
ws = workspace("gsv")
root = build_fake_root(ws / "GPT SoVITS 整合包（测试）", real_api=True)
cfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
    "root": str(root), "python": sys.executable, "port": port(), "startup_timeout": 60, "is_half": True,
    "train": {"sovits_epochs": 2, "gpt_epochs": 2, "batch_size": 2}}})
wf.run_prepare(cfg, VOICE, [str(lecture(2))])
p = wf.open_project(cfg, VOICE, must_exist=True)
kept = [r for r in p.load_manifest() if r.get("keep") and r.get("text") and r.get("split") == "train"]
review.set_draft(p, kept[0]["id"], text="老师改好的第一句话，用来训练。")
wf.review_delete(cfg, VOICE, kept[1]["id"])
print("confirm:", wf.review_confirm(cfg, VOICE)["confirmed"])
t0 = time.time()
info = wf.run_train(cfg, VOICE, "gptsovits", select=True, sovits_save_every=1, gpt_save_every=1)
print("train+select", round(time.time() - t0, 1), "s; selection_error:", info.get("selection_error"),
      "selected:", (info.get("selected") or {}).get("id"))
lines = (p.exports_dir / "gptsovits" / "train.list").read_text(encoding="utf-8").splitlines()
print("train.list rows", len(lines), "| corrected text present:", any(l.endswith("|老师改好的第一句话，用来训练。") for l in lines),
      "| deleted clip present:", any(l.startswith(kept[1]["id"] + ".wav|") for l in lines))
print("material note:", repr(wf.material_changed_note(cfg, VOICE, "gptsovits")))
print("badge:", wf.model_badge(cfg, VOICE)["text"])
script = "大家好，这是第一句话。\n\n这是第二句话，我们来看看。\n\nHello everyone, this is English.\n\n最后一句。"
r = wf.run_narrate(cfg, VOICE, script, out=str(ws / "输出 文件夹" / "讲稿（一）.wav"), backend_name="gptsovits",
                   quality="balanced")
wav, sr = sf.read(str(r.audio_path), dtype="int16")
rep = json.loads(r.report_path.read_text(encoding="utf-8"))
prev = 0.0
bad = 0
for s in rep["segments"]:
    a, b = int(round(prev * sr)) + 30, int(round(s["start"] * sr)) - 30  # 30 samples margin for 3-decimal rounding
    nz = int(np.count_nonzero(wav[a:b]))
    bad += nz
    print(f"  gap before {s['index']}: {prev:.3f}->{s['start']:.3f} nonzero samples {nz}")
    prev = s["end"]
print("  tail nonzero", int(np.count_nonzero(wav[int(round(prev * sr)) + 30:])), "| narrate warnings:", r.warnings[:3])
if "--keep" not in sys.argv:
    cleanup()
