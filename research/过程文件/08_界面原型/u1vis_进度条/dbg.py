import sys
sys.path.insert(0, "<仓库>/.claude/worktrees/wf_08725f86-d54-3")
from voicetwin.webui import tasks
from voicetwin.utils.log import get_logger
log = get_logger("dbg")
tasks.POLL_SECONDS = 0.02
def job(a, b, progress=None):
    log.info("第一行"); log.info("第二行"); progress(0.5, "[1/2] x"); log.info("第三行"); return a + b
for i in range(200):
    with tasks._LOCK:
        tasks._CURRENT = None
    out = list(tasks.stream_task("prepare", "准备素材", "v", job, 40, 2))
    text = out[-1][0]
    bad = [ln for ln in text.splitlines() if " | " not in ln]
    if bad or "第三行" not in text:
        print(i, repr(text)); break
else:
    print("ok")
