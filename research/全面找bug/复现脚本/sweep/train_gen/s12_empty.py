"""Script box contains only things that are not read aloud (a code block / a pause mark / emoji)."""
import common
from common import fresh, wf, VOICE
from voicetwin.webui import app as A
cfg, project, _, tmp = fresh("empty", gsv=False)
ui = A.WebUI(cfg); O = ui.GEN_OUT
for script in ("```python\nprint(1)\n```", "[停顿]", "😀😀"):
    before = set(project.logs_dir.glob("问题报告_*.txt"))
    outs = list(ui.do_generate(VOICE, script, None, "dummy", "fast", 0, "", "", "", "wav"))
    d = dict(zip(O, outs[-1]))
    new = set(project.logs_dir.glob("问题报告_*.txt")) - before
    print(repr(script), "->", str(d["gen_md"]).splitlines()[0][:80], "| new problem report files:", len(new))
