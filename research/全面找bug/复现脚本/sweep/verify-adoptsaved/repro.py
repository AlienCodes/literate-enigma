"""独立复现：行按钮「采用」→ 保存 → 再「🔍 自动查找」/ 加新素材，「已采用」按钮（undo）还在不在？
用法：ROOT=<代码目录> python repro.py
"""
import os, sys, tempfile, shutil, atexit
from pathlib import Path

ROOT = os.environ.get("ROOT", "/home/user/literate-enigma")
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")
import numpy as np
import soundfile as sf
from conftest import make_cfg, make_lecture
from voicetwin import workflows as wf
from voicetwin.data import review, proofcheck as pc

HERE = Path(__file__).resolve().parent
TMP = []
atexit.register(lambda: [shutil.rmtree(d, ignore_errors=True) for d in TMP])
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name + (("  | " + detail) if detail else ""))


class Fake:
    def __init__(self, name, answers):
        self.name, self.label, self.model_id = name, "假" + name, "fake"
        self.diff = name != pc.ENGINE_WHISPER_WORDS
        self.answers = answers

    def applies(self, rec):
        return True

    def load(self):
        pass

    def recognize(self, wav, lang):
        return self.answers.get(wav, ""), None

    def close(self):
        pass


def fake_engine(answers):
    pc._has = lambda m: m in ("funasr", "modelscope", "torch")
    pc._make_checker = lambda name, cfg: Fake(name, answers)
    pc._load_wav16 = lambda project, rec: rec["id"]


def voice(texts):
    d = Path(tempfile.mkdtemp(dir=str(HERE)))
    TMP.append(d)
    cfg = make_cfg(d / "ws", prepare={"asr": {"engine": "faster-whisper"}})
    project = wf.Project(cfg, "v").ensure()
    recs = []
    (project.root / "clips").mkdir(parents=True, exist_ok=True)
    for k, t in enumerate(texts):
        i = f"c{k:03d}"
        sf.write(str(project.root / f"clips/{i}.wav"), np.zeros(1600 + k, dtype=np.float32), 16000)
        recs.append({"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True,
                     "split": "train"})
    project.save_manifest(recs)
    return cfg, project


def state(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    t = review.current_values(rec, review.load_draft(project).get(rid))["text"]
    return rec, t, review.analyze(rec, t)


def button(project, rid):
    try:
        from voicetwin.webui.app import _suggest_cell
    except Exception as e:  # noqa
        return f"(no app: {e})"
    rec, t, info = state(project, rid)
    return "已采用" in _suggest_cell(info)


def undo_list(project, rid):
    rec, t, info = state(project, rid)
    return [(t[s:e], r) for s, e, r in info["undo"]]


def scenario(label, save_fn, texts, heard, rid="c000", recheck=2):
    cfg, project = voice(texts)
    fake_engine(heard)
    pc.find_suspects(project, cfg)
    _, t0, info0 = state(project, rid)
    check(f"[{label}] suggestion exists before adopt", bool(info0["edits"]), f"edits={info0['edits']} text={t0}")
    review.adopt_suggestion(project, rid)
    save_fn(project, rid)
    rec, t1, info1 = state(project, rid)
    u1 = undo_list(project, rid)
    check(f"[{label}] after adopt+save: undo present + button", bool(u1) and button(project, rid) is True,
          f"text={t1} undo={u1} dirty={review.is_dirty(rec, review.load_draft(project).get(rid))}")
    for k in range(recheck):
        pc.find_suspects(project, cfg)
        u2 = undo_list(project, rid)
        check(f"[{label}] after auto check #{k + 1}: undo kept + button", u2 == u1 and button(project, rid) is True,
              f"undo={u2} src={(state(project, rid)[0].get('suspect') or {}).get('src')}")
    try:
        review.unadopt_suggestion(project, rid)
        rec, t3, info3 = state(project, rid)
        check(f"[{label}] unadopt works after recheck", t3 == texts[int(rid[1:])], f"text back to {t3!r}")
    except ValueError as e:
        check(f"[{label}] unadopt works after recheck", False, str(e))
    return cfg, project


def save_all(project, rid):
    review.save_rows(project)


def save_row(project, rid):
    review.save_rows(project, [rid])


def nosave(project, rid):
    pass


T = ["我们今天讲十个函数", "下面我们来看第二个列子"]
H = {"c000": "我们今天讲是个函数", "c001": "下面我们来看第二个例子"}
if not os.environ.get("ONLY_NEW"):
    scenario("save all", save_all, T, H)
    scenario("save row", save_row, T, H)
    scenario("unsaved", nosave, T, H)
T2 = ["这个主剧的结构也很完整，十个函数", "今天天气很好"]
H2 = {"c000": "这个主句的结构也很完成，是个函数", "c001": "今天天气很好"}
scenario("multi-edit save all", save_all, T2, H2)


# ---------- 加新素材（run_prepare 结尾自动查错字） ----------
def new_material():
    d = Path(tempfile.mkdtemp(dir=str(HERE)))
    TMP.append(d)
    lect1 = d / "in1"
    make_lecture(lect1 / "第1课.wav", repeats=1, seed=1)
    cfg = make_cfg(d / "ws")  # asr engine none（用旁边的字幕），查错字用假的 FunASR
    class Heard(dict):  # 第二个引擎"听到的"：按原文算（这一句多听到一个「是」，别的句子一样）
        def get(self, text, default=None):
            return str(text).replace("最简单的例子", "最简单的是例子")
    answers = Heard()
    fake_engine(answers)
    pc._load_wav16 = lambda project, rec: rec["text"]
    do_proof, eng, why = wf.proofcheck_plan(cfg)
    check("[new material] proofcheck runs at end of prepare", do_proof, f"engine={eng} {why}")
    wf.run_prepare(cfg, "v", [str(lect1)])
    project = wf.open_project(cfg, "v", must_exist=True)
    recs = project.load_manifest()
    zh = [r for r in recs if "最简单的例子" in str(r.get("text"))]
    if not zh:
        check("[new material] found a clip to work with", False, str([r["text"] for r in recs]))
        return
    rid = zh[0]["id"]
    orig = zh[0]["text"]
    _, t0, info0 = state(project, rid)
    check("[new material] suggestion exists", bool(info0["edits"]), f"{t0} edits={info0['edits']}")
    review.adopt_suggestion(project, rid)
    review.save_rows(project)
    u1 = undo_list(project, rid)
    check("[new material] after adopt+save undo present + button", bool(u1) and button(project, rid) is True, f"undo={u1}")
    lect2 = d / "in2"
    make_lecture(lect2 / "第2课.wav", repeats=1, seed=2)
    before_ids = {r["id"] for r in project.load_manifest()}
    s = wf.run_prepare(cfg, "v", [str(lect1), str(lect2)])
    after = project.load_manifest()
    added = [r["id"] for r in after if r["id"] not in before_ids]
    check("[new material] new clips added + proofcheck ran", bool(added) and "proofcheck" in s,
          f"added={len(added)} proof={s.get('proofcheck', {}).get('checked')}")
    u2 = undo_list(project, rid)
    check("[new material] after new material: undo kept + button", u2 == u1 and button(project, rid) is True,
          f"undo={u2} text={state(project, rid)[1]}")
    try:
        review.unadopt_suggestion(project, rid)
        check("[new material] unadopt works", state(project, rid)[1] == orig, state(project, rid)[1])
    except ValueError as e:
        check("[new material] unadopt works", False, str(e))


new_material()
print("SUMMARY:", sum(ok for _, ok in RESULTS), "/", len(RESULTS), "passed")
