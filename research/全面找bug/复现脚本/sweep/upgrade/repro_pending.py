"""Upgrade scenario: the teacher's old workspace has clips whose speech recognition never finished
(text empty, no asr_done -- v18.2 shows 「还没有识别出文字」 and tells her to click 开始准备素材 again).

After upgrading she clicks 📝 一键全部文字校正 first, then (as the page tells her) 开始准备素材 again, which
recognises the missing clips.  Expected: the newly recognised sentences can still get the one-time correction
(the help text says the button lights up again for 识别完 new sentences).  Observed: they were already marked as used.

usage: python repro_pending.py <copy of an old workspace dir>
"""
import json
import sys
from pathlib import Path

REPO = "/home/user/literate-enigma"
sys.path.insert(0, REPO)
sys.path.insert(0, REPO + "/tests")
from conftest import make_cfg  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import prepare as prep, transcript_fix as tf  # noqa: E402
from voicetwin.data.asr import ASRResult  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402

WS = Path(sys.argv[1])
V = "我的声音"
cfg = make_cfg(WS)
project = wf.open_project(cfg, V, must_exist=True)
recs = project.load_manifest()
# two clips whose recognition was interrupted in the old version
pending = [recs[10]["id"], recs[11]["id"]]
ASR_TEXT = {pending[0]: "这里的借词后面要接宾语，艾子引导的定语从剧。", pending[1]: "所以这个现行词就是整个主剧。"}
for r in recs:
    if r["id"] in pending:
        r["text"] = ""
        r.pop("asr_done", None)
        r["keep"] = False
        r["drop_reason"] = "没有识别出文字"
project.save_manifest(recs)
ui = A.WebUI(cfg)
print("count note:", [x for x in A._clips_count_md(cfg, V).split("\n") if "识别" in x])
print("button before:", ui.textfix_btn(V)["interactive"])
outs = list(ui.do_textfix(V))
print("button after one-click:", ui.textfix_btn(V)["interactive"])
used = json.loads((project.root / tf.USED_FILE).read_text(encoding="utf-8"))["ids"]
print("pending clips already marked as used:", [p in used for p in pending])


class FakeTranscriber:  # stands in for faster-whisper finishing the interrupted recognition
    def __init__(self, cfg):
        self.progress = None
        self.progress_range = (0, 1)

    def _load(self):
        pass

    def transcribe(self, wav):
        rid = next(p for p in pending if not any(r["id"] == p and r.get("text") for r in project.load_manifest()))
        FakeTranscriber.n = getattr(FakeTranscriber, "n", 0) + 1
        return ASRResult(text=ASR_TEXT[pending[FakeTranscriber.n - 1]], lang="zh", avg_logprob=-0.2,
                         no_speech_prob=0.01, engine="fake")


prep.Transcriber = FakeTranscriber
wf._precheck_prepare = lambda *a, **k: []  # the faster-whisper package is not installed on this dev machine
cfg2 = make_cfg(WS, prepare={"asr": {"engine": "faster-whisper"}})
lec = WS.parent / "lectures"
wf.run_prepare(cfg2, V, [str(lec)])  # 「再点一次开始准备素材」
recs = {r["id"]: r for r in project.load_manifest()}
print("recognised now:", [(recs[p]["text"], recs[p].get("keep")) for p in pending])
print("textfix_new_ids:", tf.textfix_new_ids(project))
print("button after recognition finished:", ui.textfix_btn(V)["interactive"])
print("info first line:", ui.textfix_info(V).split("\n")[0][:120])
