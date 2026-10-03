"""共用：临时声音 + 假的第二个识别引擎（不加载任何模型、不联网）。"""
import sys, tempfile, shutil, atexit
from pathlib import Path

ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")
import numpy as np
import soundfile as sf
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf, proofcheck as pc

SCR = Path(__file__).resolve().parent
_tmps = []


def _cleanup():
    for d in _tmps:
        shutil.rmtree(d, ignore_errors=True)


atexit.register(_cleanup)


def voice(texts, ids=None, name="v", engine="faster-whisper", write_wav=True):
    d = Path(tempfile.mkdtemp(dir=str(SCR)))
    _tmps.append(d)
    cfg = make_cfg(d / "ws", prepare={"asr": {"engine": engine}})
    project = wf.Project(cfg, name).ensure()
    ids = ids or [f"c{i:03d}" for i in range(len(texts))]
    recs = []
    for k, (i, t) in enumerate(zip(ids, texts)):
        rel = f"clips/{i}.wav"
        if write_wav:
            (project.root / "clips").mkdir(parents=True, exist_ok=True)
            sf.write(str(project.root / rel), np.zeros(1600 + k, dtype=np.float32), 16000)
        recs.append({"id": i, "path": rel, "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"})
    project.save_manifest(recs)
    return cfg, project


class FakeChecker:
    def __init__(self, name, answers, fail=(), load_error=None, log=None):
        self.name = name
        self.label = f"假的{name}"
        self.diff = name != pc.ENGINE_WHISPER_WORDS
        self.model_id = "fake-1"
        self.answers = answers
        self.fail = set(fail)
        self.load_error = load_error
        self.log = log if log is not None else []

    def applies(self, rec):
        return self.name != pc.ENGINE_FUNASR or rec.get("lang") == "zh" or pc.count_cjk(str(rec.get("text") or "")) > 0

    def load(self):
        self.log.append(("load", self.name))
        if self.load_error:
            raise self.load_error

    def recognize(self, wav, lang):
        self.log.append(("recognize", self.name, wav))
        if wav in self.fail or "*" in self.fail:
            raise RuntimeError("识别出错了")
        return self.answers.get(wav, ""), None

    def close(self):
        self.log.append(("close", self.name))


def fake_engine(answers, installed=("funasr", "modelscope", "torch"), **kw):
    """假装装了 FunASR，第二次识别的结果 = answers[片段 id]。"""
    mods = set(installed)
    pc._has = lambda m: m in mods
    log = []
    specs = {"answers": answers, **kw}
    pc._make_checker = lambda name, cfg: FakeChecker(name, log=log, **specs)
    pc._load_wav16 = lambda project, rec: rec["id"]
    return log


def cur(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    return rec, review.current_values(rec, review.load_draft(project).get(rid))["text"]


def show(project, rid, label=""):
    rec, text = cur(project, rid)
    info = review.analyze(rec, text)
    sus = rec.get("suspect") or {}
    print(f"[{label}] {rid}: text={text!r} red={[text[s:e] for s, e in info['red']]} "
          f"edits={[(text[s:e], r) for s, e, r in info['edits']]} undo={[(text[s:e], r) for s, e, r in info['undo']]} "
          f"src={sus.get('src')} active={info['active']} adopted={info['adopted']}")
    return info
