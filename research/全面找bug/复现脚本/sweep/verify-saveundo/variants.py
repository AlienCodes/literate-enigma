"""Variants around the reported problem.  usage: ROOT=<code root> python variants.py <tag> [v1 v2 v3 v4]"""
import json, os, re, shutil, sys, tempfile
from pathlib import Path

ROOT = os.environ.get("ROOT", "/home/user/literate-enigma")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
TAG = sys.argv[1]
WHICH = sys.argv[2:] or ["v1", "v2", "v3", "v4"]
BASE = HERE / f"base_{TAG}"
TMP = HERE / f"tmp_{TAG}"
TMP.mkdir(exist_ok=True)

import conftest  # noqa
from conftest import make_cfg, make_lecture  # noqa
from voicetwin import workflows as wf  # noqa
from voicetwin.data import review, transcript_fix as tf, proofcheck as pc  # noqa
from voicetwin.webui import app as A  # noqa

assert wf.__file__.startswith(ROOT), wf.__file__
VOICE = "测试声音"
strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))
ORIG_REC = pc._EngineRunner.recognize


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
    return cfg, wf.Project(cfg, VOICE), A.WebUI(cfg), d


def cur(p, rid):
    rec = {r["id"]: r for r in p.load_manifest()}[rid]
    return review.current_values(rec, review.load_draft(p).get(rid))


def show(label, cfg, p, rid):
    r = [x for x in A._clips_table(cfg, VOICE) if x[1] == rid][0]
    rec = {x["id"]: x for x in p.load_manifest()}[rid]
    sus = rec.get("suspect") or {}
    info = review.analyze(rec, cur(p, rid)["text"])
    print(f"  [{label}] text={cur(p, rid)['text']!r} dirty={review.is_dirty(rec, review.load_draft(p).get(rid))}"
          f" src={sus.get('src')!r} undo={info['undo']} red={info['red']} edits={info['edits']}")
    print(f"      修改建议={strip(r[6])!r}")
    return strip(r[6]), info


def try_undo(p, rid):
    try:
        review.unadopt_suggestion(p, rid)
        return cur(p, rid)["text"]
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def oneclick(name, text):
    cfg, p, ui, d = fresh(name)
    rs = p.load_manifest()
    a = rs[1]["id"]
    for r in rs:
        r.pop("suspect", None)
    rs[1]["text"] = text
    p.save_manifest(rs)
    list(ui.do_textfix(VOICE))
    show("after 一键", cfg, p, a)
    ui.do_save(VOICE)
    show("after 保存", cfg, p, a)
    return cfg, p, ui, d, a


out = {}
if "v1" in WHICH:  # 2nd engine flags ANOTHER word in the same saved one-click row
    print(f"== v1 ({TAG}): saved one-click + 🔍 flags another word ==")
    cfg, p, ui, d, a = oneclick("v1", "我们先来看艾子引导的定语从句。")

    def rec2(self, rec, lang):
        t = str(rec.get("text") or "")
        return (t.replace("从句", "从具") if rec["id"] == a else t), None, "funasr"

    pc._EngineRunner.recognize = rec2
    list(ui.do_proofcheck(VOICE, False))
    s, info = show("after 🔍", cfg, p, a)
    out["v1"] = dict(cell=s, undo=bool(info["undo"]), undo_result=try_undo(p, a))
    print("  undo ->", out["v1"]["undo_result"])
    pc._EngineRunner.recognize = ORIG_REC
    shutil.rmtree(d, ignore_errors=True)

if "v2" in WHICH:  # new batch + one-click for the new batch: old row keeps button?
    print(f"== v2 ({TAG}): saved one-click, confirm, add batch 2, one-click batch 2 ==")
    cfg, p, ui, d, a = oneclick("v2", "我们先来看艾子引导的定语从句。")
    ui.do_confirm(VOICE)

    def rec3(self, rec, lang):
        return str(rec.get("text") or "").replace("as", "a在"), None, "funasr"

    pc._EngineRunner.recognize = rec3
    newdir = d / "lectures2"
    make_lecture(newdir / "第2课.wav", repeats=1, seed=7)
    cfg_on = make_cfg(Path(cfg.get("workspace")), prepare={"asr": {"engine": "none"}, "proofcheck": "on"})
    wf.run_prepare(cfg_on, VOICE, [str(newdir)])
    ui.after_prepare_clips(VOICE, False, None, {"voice": VOICE})
    show("after batch 2 prepare", cfg, p, a)
    print("  一键 button:", ui.textfix_btn(VOICE)["interactive"])
    list(ui.do_textfix(VOICE))
    s, info = show("after 一键 for batch 2", cfg, p, a)
    print("  一键 button after:", ui.textfix_btn(VOICE)["interactive"])
    out["v2"] = dict(cell=s, undo=bool(info["undo"]), undo_result=try_undo(p, a))
    print("  undo ->", out["v2"]["undo_result"])
    pc._EngineRunner.recognize = ORIG_REC
    shutil.rmtree(d, ignore_errors=True)

if "v3" in WHICH:  # direct 母本 fix (借词 -> 介词) saved, then 🔍
    print(f"== v3 ({TAG}): saved direct fix 借词->介词 + 🔍 ==")
    cfg, p, ui, d, a = oneclick("v3", "这里的借词to后面跟名词。")

    def same(self, rec, lang):
        return str(rec.get("text") or ""), None, "funasr"

    pc._EngineRunner.recognize = same
    list(ui.do_proofcheck(VOICE, False))
    s, info = show("after 🔍", cfg, p, a)
    out["v3"] = dict(cell=s, undo=bool(info["undo"]), undo_result=try_undo(p, a))
    print("  undo ->", out["v3"]["undo_result"])
    pc._EngineRunner.recognize = ORIG_REC
    shutil.rmtree(d, ignore_errors=True)

if "v4" in WHICH:  # per-row 「采用」 of a 🔍 suggestion (not one-click), saved, then 🔍 again
    print(f"== v4 ({TAG}): per-row adopt of 🔍 suggestion, save, 🔍 again ==")
    cfg, p, ui, d = fresh("v4")
    rs = p.load_manifest()
    a = rs[2]["id"]
    for r in rs:
        r.pop("suspect", None)
    p.save_manifest(rs)
    base_text = rs[2]["text"]
    print("  row text:", base_text)

    def rec4(self, rec, lang):
        t = str(rec.get("text") or "")
        return (t.replace("例子", "栗子") if rec["id"] == a else t), None, "funasr"

    # make the saved text contain the wrong word, 2nd engine hears the right one
    rs = p.load_manifest()
    for r in rs:
        if r["id"] == a:
            r["text"] = base_text.replace("例子", "梨子")
            r.pop("orig_text", None)  # make the wrong word look like what the recogniser wrote
    p.save_manifest(rs)

    def rec4b(self, rec, lang):
        t = str(rec.get("text") or "")
        return (t.replace("梨子", "例子") if rec["id"] == a else t), None, "funasr"

    pc._EngineRunner.recognize = rec4b
    list(ui.do_proofcheck(VOICE, False))
    show("after 🔍 #1", cfg, p, a)
    try:
        review.adopt_suggestion(p, a)
    except Exception as exc:
        print("  adopt raised", exc)
    show("after 采用", cfg, p, a)
    ui.do_save(VOICE)
    show("after 保存", cfg, p, a)

    def same(self, rec, lang):
        return str(rec.get("text") or ""), None, "funasr"

    pc._EngineRunner.recognize = same
    list(ui.do_proofcheck(VOICE, False))
    s, info = show("after 🔍 #2", cfg, p, a)
    out["v4"] = dict(cell=s, undo=bool(info["undo"]), undo_result=try_undo(p, a))
    print("  undo ->", out["v4"]["undo_result"])
    pc._EngineRunner.recognize = ORIG_REC
    shutil.rmtree(d, ignore_errors=True)

print("RESULT", TAG, json.dumps(out, ensure_ascii=False))
