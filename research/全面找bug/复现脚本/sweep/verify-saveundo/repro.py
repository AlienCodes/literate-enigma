"""Verify: after one-click (艾子 -> as) + 保存修改, does 🔍 自动查找 / adding a new batch remove the 「已采用」 undo button?

usage: ROOT=<code root> python repro.py <tag> [proofundo] [newbatch]
"""
import json, os, re, shutil, sys, tempfile
from pathlib import Path

ROOT = os.environ.get("ROOT", "/home/user/literate-enigma")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
TAG = sys.argv[1]
WHICH = sys.argv[2:] or ["proofundo", "newbatch"]
BASE = HERE / f"base_{TAG}"
TMP = HERE / f"tmp_{TAG}"
TMP.mkdir(exist_ok=True)

import conftest  # noqa: E402  (blocks network)
from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review, transcript_fix as tf, proofcheck as pc  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402

assert wf.__file__.startswith(ROOT), wf.__file__
VOICE = "测试声音"
strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))


def ensure_base():
    if (BASE / "ok").exists():
        return
    shutil.rmtree(BASE, ignore_errors=True)
    make_lecture(BASE / "lectures" / "第1课.wav")
    cfg = make_cfg(BASE / "ws")
    wf.run_prepare(cfg, VOICE, [str(BASE / "lectures")])
    (BASE / "ok").write_text("1")


def fresh(name):
    ensure_base()
    d = Path(tempfile.mkdtemp(prefix=name + "_", dir=TMP))
    shutil.copytree(BASE / "ws" / VOICE, d / "ws" / VOICE)
    cfg = make_cfg(d / "ws")
    return cfg, wf.Project(cfg, VOICE), A.WebUI(cfg)


def cur(p, rid):
    rec = {r["id"]: r for r in p.load_manifest()}[rid]
    return review.current_values(rec, review.load_draft(p).get(rid))


def row_of(cfg, rid):
    return [r for r in A._clips_table(cfg, VOICE) if r[1] == rid][0]


def show(label, cfg, p, rid):
    r = row_of(cfg, rid)
    rec = {x["id"]: x for x in p.load_manifest()}[rid]
    sus = rec.get("suspect") or {}
    info = review.analyze(rec, cur(p, rid)["text"])
    print(f"  [{label}] text={cur(p, rid)['text']!r} saved={rec.get('text')!r} dirty={review.is_dirty(rec, review.load_draft(p).get(rid))}")
    print(f"      suspect.src={sus.get('src')!r} alt={sus.get('alt')!r} undo={info['undo']} adopted={info['adopted']}")
    print(f"      修改建议 cell={strip(r[6])!r}  | 可能有错 cell={strip(r[5])!r}")
    return strip(r[6])


def setup_oneclick(name):
    cfg, p, ui = fresh(name)
    rs = p.load_manifest()
    a = rs[1]["id"]
    for r in rs:
        r.pop("suspect", None)
    rs[1]["text"] = "我们先来看艾子引导的定语从句。"
    p.save_manifest(rs)
    outs = list(ui.do_textfix(VOICE))
    s1 = show("after 一键全部文字校正", cfg, p, a)
    ui.do_save(VOICE)
    s2 = show("after 保存修改", cfg, p, a)
    return cfg, p, ui, a, s1, s2


res = {}
if "proofundo" in WHICH:
    print(f"== proofundo ({TAG}) ==")
    cfg, p, ui, a, s1, s2 = setup_oneclick("proofundo")

    def same(self, rec, lang):  # second engine hears exactly the saved text
        return str(rec.get("text") or ""), None, "funasr"

    pc._EngineRunner.recognize = same
    outs = list(ui.do_proofcheck(VOICE, False))
    s3 = show("after 🔍 自动查找", cfg, p, a)
    print("  textfix button interactive:", ui.textfix_btn(VOICE)["interactive"])
    # try the undo button: is there still an undo action available for this row?
    rec = {x["id"]: x for x in p.load_manifest()}[a]
    info = review.analyze(rec, cur(p, a)["text"])
    if info["undo"]:
        try:
            review.unadopt_suggestion(p, a)
            print("  undo via review ->", cur(p, a)["text"])
        except Exception as exc:
            print("  undo raised:", type(exc).__name__, exc)
    res["proofundo"] = dict(after_oneclick=s1, after_save=s2, after_check=s3)
    shutil.rmtree(Path(cfg.get("workspace")).parent, ignore_errors=True)

if "newbatch" in WHICH:
    print(f"== newbatch ({TAG}) ==")
    cfg, p, ui, a, s1, s2 = setup_oneclick("newbatch")
    md, _, _ = ui.do_confirm(VOICE)
    print("  textfix button after batch 1:", ui.textfix_btn(VOICE)["interactive"])

    def second_engine(self, rec, lang):
        t = str(rec.get("text") or "")
        return t.replace("as", "a在"), None, "funasr"

    pc._EngineRunner.recognize = second_engine
    newdir = Path(cfg.get("workspace")).parent / "lectures2"
    make_lecture(newdir / "第2课.wav", repeats=1, seed=7)
    cfg_on = make_cfg(Path(cfg.get("workspace")), prepare={"asr": {"engine": "none"}, "proofcheck": "on"})
    summary = wf.run_prepare(cfg_on, VOICE, [str(newdir)])
    ui.after_prepare_clips(VOICE, False, None, {"voice": VOICE})
    print("  clips now", len(p.load_manifest()), "| prepare proofcheck:", summary.get("proofcheck"))
    s3 = show("after adding batch 2 (prepare runs 🔍)", cfg, p, a)
    print("  textfix button now:", ui.textfix_btn(VOICE)["interactive"], "| a in new ids:", a in tf.textfix_new_ids(p))
    res["newbatch"] = dict(after_oneclick=s1, after_save=s2, after_newbatch=s3)
    shutil.rmtree(Path(cfg.get("workspace")).parent, ignore_errors=True)

print("RESULT", TAG, json.dumps(res, ensure_ascii=False))
