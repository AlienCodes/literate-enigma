"""查错字查到一半点「停止」（网页的处理函数 + 后台任务）：已经查完的存好了吗？说明是中文吗？再点一次能接着用吗？"""
from common import *
from voicetwin.webui import app as A
from voicetwin.utils import progress as P
texts = [f"我们今天讲第{i}个函数" for i in range(30)]
cfg, project = voice(texts)
heard = {f"c{i:03d}": f"我们今天讲第{i}个变量" for i in range(30)}
log = fake_engine(heard)
orig = FakeChecker.recognize
def rec(self, wav, lang):
    if wav == "c012":
        P.request_cancel()  # 老师点了停止
    return orig(self, wav, lang)
FakeChecker.recognize = rec
ui = A.WebUI(cfg)
outs = list(ui.do_proofcheck("v", False)); print("recognize calls so far:", sum(1 for e in log if e[0] == "recognize"))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
import re
print("final md:", re.sub(r"\s+", " ", str(last["proof_md"]))[:300])
recs = project.load_manifest()
done = [r["id"] for r in recs if r.get("suspect")]
print("rows with result saved:", len(done), done[:3], "...", done[-2:])
print("cancel flag still set:", P.CANCEL.is_set())
FakeChecker.recognize = orig
outs = list(ui.do_proofcheck("v", False)); print("recognize calls so far:", sum(1 for e in log if e[0] == "recognize"))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("rerun md:", re.sub(r"\s+", " ", str(last["proof_md"]))[:120])
print("recognize calls total (both runs):", sum(1 for e in log if e[0] == "recognize"))
