"""A one-line script typed/pasted into the 讲稿 box: if it contains a '.' (e.g. 'Python 3.9', 'e.g.', an English
sentence) and is longer than 255 bytes, run_narrate's "is this a file path?" probe (Path.exists) raises
OSError ENAMETOOLONG on Linux/macOS and the teacher is told the *install path* is too long."""
from common import cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf
from voicetwin.errors import explain
ws = workspace("longline"); cfg = make_cfg(ws)
wf.run_prepare(cfg, "张老师", [str(lecture(2))])
texts = {
  "zh one line with 3.9 (100 chars)": "今天我们讲 Python 3.9 里面的列表推导式，" + "它可以让代码变得更加简洁也更容易阅读，" * 4 + "好。",
  "en one paragraph": "Hello everyone. " * 20,
}
for k, t in texts.items():
    print(k, "len bytes", len(t.encode()))
    try:
        r = wf.run_narrate(cfg, "张老师", t, out=str(ws / "o.wav"), quality="fast")
        print("   OK", round(r.duration, 1), "s")
    except Exception as exc:
        f = explain(exc)
        print("   FAIL", type(exc).__name__, str(exc)[:80], "\n   teacher sees:", f.title, "|", f.advice[:70])
cleanup()
