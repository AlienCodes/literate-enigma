"""Verify: script with only non-readable content -> message + problem report (independent repro)."""
import os, sys, tempfile, shutil
from pathlib import Path
ROOT = os.environ["VT_ROOT"]
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
from conftest import make_cfg
from voicetwin.eval import sv_models
sv_models.download = lambda cfg, progress=None, keys=None: []
from voicetwin import workflows as wf
from voicetwin.webui import app as A, tasks as T
import voicetwin
print("code from:", os.path.dirname(voicetwin.__file__))
print("NO_REPORT_KEYS:", sorted(T.NO_REPORT_KEYS))
d = Path(tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__))))
try:
    cfg = make_cfg(d / "ws")
    V = "测试声音"
    project = wf.Project(cfg, V).ensure()
    project.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": "你好世界。", "lang": "zh",
                            "duration": 3.0, "keep": True, "split": "train"} for i in range(3)])
    ui = A.WebUI(cfg); O = ui.GEN_OUT
    print("skip_code_blocks =", cfg.get_path("synth.skip_code_blocks", None))
    for script in ("```python\nprint(1)\n```", "[停顿]", "😀😀", "   \n  ", ""):
        before = set(d.rglob("问题报告_*.txt"))
        outs = list(ui.do_generate(V, script, None, "dummy", "fast", 0, "", "", "", "wav"))
        dd = dict(zip(O, outs[-1]))
        new = set(d.rglob("问题报告_*.txt")) - before
        md = str(dd.get("gen_md") or "")
        bar = str(dd.get("gen_bar") or "")
        print("=" * 70)
        print("SCRIPT:", repr(script))
        print("gen_md:", md.replace("\n", " / ")[:400])
        print("gen_bar:", bar.replace("\n", " / ")[:200])
        print("new problem reports:", [str(p.relative_to(d)) for p in new])
        print("mentions report in md:", "问题报告" in md or "发给帮你的人" in md)
finally:
    shutil.rmtree(d, ignore_errors=True)
