"""Own helper: temp voice + fake second recognizer (no models, no network)."""
import sys, tempfile, shutil, atexit
from pathlib import Path
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
import numpy as np, soundfile as sf
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf, proofcheck as pc
SCR = Path(__file__).resolve().parent
_tmps = []
atexit.register(lambda: [shutil.rmtree(d, ignore_errors=True) for d in _tmps])

def voice(texts, ids=None, name="v"):
    d = Path(tempfile.mkdtemp(dir=str(SCR))); _tmps.append(d)
    cfg = make_cfg(d / "ws", prepare={"asr": {"engine": "faster-whisper"}})
    project = wf.Project(cfg, name).ensure()
    ids = ids or [f"c{i:03d}" for i in range(len(texts))]
    (project.root / "clips").mkdir(parents=True, exist_ok=True)
    recs = []
    for k, (i, t) in enumerate(zip(ids, texts)):
        rel = f"clips/{i}.wav"
        sf.write(str(project.root / rel), np.zeros(1600 + k, dtype=np.float32), 16000)
        recs.append({"id": i, "path": rel, "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"})
    project.save_manifest(recs)
    return cfg, project

ANS = {}
class Fake:
    def __init__(self, name):
        self.name = name; self.label = "fake"; self.diff = name != pc.ENGINE_WHISPER_WORDS; self.model_id = "f1"
    def applies(self, rec): return True
    def load(self): pass
    def recognize(self, wav, lang):
        v = ANS.get(wav)
        return (v(wav) if callable(v) else (v or "")), None
    def close(self): pass

def install_fake():
    pc._has = lambda m: m in ("funasr", "modelscope", "torch")
    pc._make_checker = lambda name, cfg: Fake(name)
    pc._load_wav16 = lambda project, rec: rec["id"]

def state(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    text = review.current_values(rec, review.load_draft(project).get(rid))["text"]
    info = review.analyze(rec, text)
    sus = rec.get("suspect") or {}
    return dict(text=text, red=[text[s:e] for s, e in info["red"]], edits=[(text[s:e], r) for s, e, r in info["edits"]],
                undo=[(text[s:e], r) for s, e, r in info["undo"]], src=sus.get("src"), active=info["active"],
                adopted=info["adopted"])
