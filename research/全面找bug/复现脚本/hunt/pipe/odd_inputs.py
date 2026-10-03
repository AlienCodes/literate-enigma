"""prepare() with odd inputs: silent file, very short file, 0-byte file, corrupt 'video', only odd ones in folder."""
import numpy as np, soundfile as sf, shutil
from common import HERE, cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf
from voicetwin.errors import explain
ws = workspace("odd"); cfg = make_cfg(ws)
d = ws / "输入 文件夹（奇怪）"; d.mkdir()
sf.write(str(d / "全是静音.wav"), np.zeros(44100 * 10, dtype=np.float32), 44100)
sf.write(str(d / "很短.wav"), (0.3 * np.sin(np.arange(13230) / 10)).astype(np.float32), 44100)
(d / "空文件.wav").write_bytes(b"")
(d / "坏的视频.mp4").write_bytes(np.random.default_rng(1).bytes(50000))
sf.write(str(d / "噪声.wav"), np.random.default_rng(2).normal(0, 0.3, 44100 * 8).astype(np.float32), 44100)
def run(label, voice, inputs):
    try:
        s = wf.run_prepare(cfg, voice, inputs)
        print(label, "OK kept", s["clips_kept"], "/", s["clips_total"], "| skipped:", [(x["file"], x["reason"][:30]) for x in s.get("skipped_files", [])], "| warn:", [w[:40] for w in s["warnings"][:3]])
    except Exception as exc:
        f = explain(exc); print(label, "FAIL", type(exc).__name__, str(exc)[:120], "| teacher sees:", f.title, "|", f.advice[:40])
run("only odd files:", "怪声音", [str(d)])
run("odd + real:", "怪声音2", [str(d), str(lecture(2))])
p = wf.Project(cfg, "怪声音2")
try:
    r = wf.review_confirm(cfg, "怪声音2"); print("confirm", r["confirmed"], r["counts"])
except Exception as exc:
    print("confirm FAIL", type(exc).__name__, exc)
cleanup()
