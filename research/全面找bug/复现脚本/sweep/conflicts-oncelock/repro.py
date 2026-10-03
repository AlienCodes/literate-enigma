"""Independent reproduction of: 'one-click lock marks rows it never checked as used'.

Scenarios (run against the current working tree, read-only):
  pending  - row with no recognised text at one-click time; text arrives later (re-prepare finishes ASR)
  edit     - row double-click edited while one-click is running
  grey     - row with text but keep=False (grey, program judged unusable) at one-click time; teacher then
             clicks 「✅ 这一条也要用」 and saves
All driven through the real WebUI handlers (do_textfix, do_clip_action, do_save).
"""
import json
import re
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
BASE = HERE / "base"
TMP = HERE / "tmp"
TMP.mkdir(exist_ok=True)

from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review, transcript_fix as tf  # noqa: E402
from voicetwin.eval import sv_models  # noqa: E402

sv_models.download = lambda cfg, progress=None, keys=None: []  # no network
VOICE = "测试声音"


def base():
    if (BASE / "ok").exists():
        return
    shutil.rmtree(BASE, ignore_errors=True)
    make_lecture(BASE / "lec" / "第1课.wav")
    wf.run_prepare(make_cfg(BASE / "ws"), VOICE, [str(BASE / "lec")])
    (BASE / "ok").write_text("1")


def fresh(name):
    base()
    d = Path(tempfile.mkdtemp(prefix=name + "_", dir=TMP))
    shutil.copytree(BASE / "ws" / VOICE, d / "ws" / VOICE)
    cfg = make_cfg(d / "ws")
    from voicetwin.webui import app as A
    return cfg, wf.Project(cfg, VOICE), A.WebUI(cfg), A


def act(ui, action, cid, **extra):
    return ui.do_clip_action(VOICE, json.dumps(dict(action=action, id=cid, no="1", **extra), ensure_ascii=False), False)


def cur(p, rid):
    rec = {r["id"]: r for r in p.load_manifest()}[rid]
    return review.current_values(rec, review.load_draft(p).get(rid))


def used_ids(p):
    f = Path(p.root) / tf.USED_FILE
    return set(json.loads(f.read_text("utf-8"))["ids"]) if f.exists() else set()


def onclick(ui):
    outs = list(ui.do_textfix(VOICE))
    return dict(zip(ui.TEXTFIX_OUT, outs[-1]))


def strip(x):
    return re.sub("<[^>]+>", "", str(x))


def setup_rows(p, edits):
    rs = p.load_manifest()
    for r in rs:
        r.pop("suspect", None)
        if r["id"] in edits:
            r.update(edits[r["id"]])
            r["_stats_text"] = None
    p.save_manifest(rs)


which = sys.argv[1:] or ["pending", "edit", "grey"]
OUT = {}

if "pending" in which:
    cfg, p, ui, A = fresh("pending")
    ids = [r["id"] for r in p.load_manifest()]
    a, c = ids[1], ids[3]
    setup_rows(p, {a: {"text": "我们先来看艾子引导的定语从句。"}, c: {"text": "", "asr_done": False}})
    wf.apply_review(cfg, VOICE, read_csv=False)
    print("[pending] c text before:", repr(cur(p, c)["text"]), "keep", cur(p, c)["keep"])
    last = onclick(ui)
    print("[pending] after one-click: button interactive =", last["tr_btn"].get("interactive"))
    print("[pending] a:", cur(p, a)["text"])
    print("[pending] c marked used?", c in used_ids(p), "| a marked used?", a in used_ids(p))
    rs = p.load_manifest()
    for r in rs:
        if r["id"] == c:
            r.update(text="这里的借词后面要接宾语。", lang="zh", asr_done=True)
    p.save_manifest(rs)
    wf.apply_review(cfg, VOICE, read_csv=False)
    print("[pending] c keep now:", cur(p, c)["keep"], "| textfix_used =", wf.textfix_used(cfg, VOICE),
          "| button interactive =", ui.textfix_btn(VOICE).get("interactive"))
    last = onclick(ui)
    print("[pending] 2nd one-click -> c:", cur(p, c)["text"], "| msg:", strip(last["proof_bar"])[:80])
    OUT["pending"] = ("借词" not in cur(p, c)["text"])

if "edit" in which:
    cfg, p, ui, A = fresh("edit")
    ids = [r["id"] for r in p.load_manifest()]
    a, b = ids[1], ids[2]
    setup_rows(p, {a: {"text": "我们先来看艾子引导的定语从句。"}, b: {"text": "关系代词that不能和借词一起提前。"}})
    real = tf.check_text
    started = threading.Event()

    def slow(*x, **k):
        started.set()
        time.sleep(0.15)
        return real(*x, **k)

    tf.check_text = slow
    res = {}
    th = threading.Thread(target=lambda: res.setdefault("o", list(ui.do_textfix(VOICE))))
    th.start()
    started.wait(60)
    time.sleep(0.05)
    msg = act(ui, "edit", b, text="关系代词that不能和借词一起提前呢。")[0]
    print("[edit] edit during run:", strip(msg)[:80])
    th.join()
    tf.check_text = real
    last = dict(zip(ui.TEXTFIX_OUT, res["o"][-1]))
    print("[edit] a:", cur(p, a)["text"], "| b:", cur(p, b)["text"])
    print("[edit] b marked used?", b in used_ids(p), "| textfix_used =", wf.textfix_used(cfg, VOICE),
          "| button:", ui.textfix_btn(VOICE).get("interactive"))
    last = onclick(ui)
    print("[edit] 2nd one-click -> b:", cur(p, b)["text"], "| a:", cur(p, a)["text"])
    OUT["edit"] = ("借词" not in cur(p, b)["text"])

if "grey" in which:
    cfg, p, ui, A = fresh("grey")
    ids = [r["id"] for r in p.load_manifest()]
    a, b = ids[1], ids[2]
    setup_rows(p, {a: {"text": "我们先来看艾子引导的定语从句。"},
                   b: {"text": "关系代词that不能和借词一起提前。",
                       "asr": {"engine": "x", "avg_logprob": -1.6, "no_speech_prob": 0.1}}})
    wf.apply_review(cfg, VOICE, read_csv=False)
    rb = {r["id"]: r for r in p.load_manifest()}[b]
    print("[grey] b keep:", rb["keep"], "drop_reason:", rb.get("drop_reason"))
    last = onclick(ui)
    print("[grey] after one-click: button =", last["tr_btn"].get("interactive"), "| a:", cur(p, a)["text"])
    print("[grey] b marked used?", b in used_ids(p))
    print("[grey] b suspect / suggestion after one-click:", {r["id"]: r for r in p.load_manifest()}[b].get("suspect"))
    print("[grey] use:", strip(act(ui, "use", b)[0])[:60])
    md = ui.do_save(VOICE)[0]
    print("[grey] save:", strip(md).splitlines()[0][:80])
    print("[grey] b keep now:", cur(p, b)["keep"], "| textfix_used =", wf.textfix_used(cfg, VOICE),
          "| button:", ui.textfix_btn(VOICE).get("interactive"))
    rec = {r["id"]: r for r in p.load_manifest()}[b]
    print("[grey] b row suggestion (suspect) now:", rec.get("suspect"))
    info = review.analyze(rec, cur(p, b)["text"])
    print("[grey] analyze(b): edits/suggest", {k: v for k, v in info.items() if k in ("edits", "red", "undo")})
    last = onclick(ui)
    print("[grey] clicking anyway ->", strip(last["proof_bar"])[:90])
    print("[grey] b text:", cur(p, b)["text"])
    print("[grey] info text:", strip(ui.textfix_info(VOICE))[:200])
    OUT["grey"] = ("借词" not in cur(p, b)["text"])

print("RESULT (True = row got corrected):", OUT)
