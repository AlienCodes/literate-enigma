"""Independent repro: after training, change+save one sentence; does the ③ 生成 result summary (gen_md)
and the 「重新挑选」 result (train_md) carry the 'material changed after training' warning?

Usage: python repro.py <code_root>   (code_root = repo working tree or a `git archive HEAD` copy)
"""
import os, sys, shutil, socket, sysconfig, tempfile, time
from pathlib import Path

ROOT = sys.argv[1]
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
from conftest import make_cfg, make_lecture
from fake_gptsovits import build_fake_root
from voicetwin.eval import sv_models
sv_models.download = lambda cfg, progress=None, keys=None: []
from voicetwin import workflows as wf
import voicetwin
assert str(Path(voicetwin.__file__).resolve()).startswith(str(Path(ROOT).resolve())), voicetwin.__file__
from voicetwin.backends.gptsovits import GPTSoVITSBackend
from voicetwin.data import review
from voicetwin.webui import app as A

GPTSoVITSBackend.ensure_users_pth = lambda self: None
GPTSoVITSBackend._gpu_memory = lambda self, quick=False: (11.99, 11.2, "test")
GPTSoVITSBackend.POLL_SECONDS = 0.05
GPTSoVITSBackend.STARTUP_NOTE_SECONDS = 0.4
os.environ["FAKE_GSV_CLIP_SLEEP"] = "0.0"
paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
os.environ["PYTHONPATH"] = os.pathsep.join(p for p in dict.fromkeys(paths) if p)
VOICE = "测试声音"
KEY = "上次训练以后改过"


def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


(HERE / "tmp").mkdir(exist_ok=True)
tmp = Path(tempfile.mkdtemp(prefix="cn_", dir=str(HERE / "tmp")))
try:
    lec = tmp / "lectures"
    make_lecture(lec / "第1课.wav")
    root = build_fake_root(tmp / "GPT-SoVITS", real_api=True)
    b = {"root": str(root), "python": sys.executable, "port": port(), "startup_timeout": 60, "is_half": True,
         "train": {"sovits_epochs": 2, "gpt_epochs": 2, "batch_size": 2}}
    cfg = make_cfg(tmp / "ws", backend="gptsovits", backends={"gptsovits": b})
    s = wf.run_prepare(cfg, VOICE, [str(lec)])
    print("prepared", s["clips_kept"])
    wf.review_confirm(cfg, VOICE)
    project = wf.open_project(cfg, VOICE, must_exist=True)
    wf.run_train(cfg, VOICE, "gptsovits", select=True, sovits_save_every=1, gpt_save_every=1)
    ui = A.WebUI(cfg)
    O = ui.GEN_OUT

    def gen(label):
        outs = list(ui.do_generate(VOICE, "大家好，今天我们讲第一课。", None, "gptsovits", "fast", 0, "", "", "", "wav"))
        last = dict(zip(O, outs[-1]))
        md, lg = str(last.get("gen_md")), str(last.get("gen_log"))
        print(f"[{label}] gen_md has note: {KEY in md} | gen_log has note: {KEY in lg} | "
              f"audio: {bool(last.get('out_audio'))}")
        return md

    def sel(label):
        outs = list(ui.do_select(VOICE, "gptsovits"))
        TO = ui.TRAIN_OUT if hasattr(ui, "TRAIN_OUT") else None
        last = dict(zip(TO, outs[-1])) if TO else {}
        md = str(last.get("train_md"))
        print(f"[{label}] select train_md has note: {KEY in md}")
        return md

    # 1) unchanged material: no note anywhere (no false positive)
    print("note before edit:", repr(wf.material_changed_note(cfg, VOICE, "gptsovits")[:30]))
    gen("unchanged")
    # 2) change + save one training sentence
    rec = next(r for r in project.load_manifest() if r.get("keep") and r.get("split", "train") == "train")
    review.set_draft(project, rec["id"], text="训练以后又改过的一句话。")
    wf.review_save(cfg, VOICE, ids=[rec["id"]])
    print("note after edit:", repr(wf.material_changed_note(cfg, VOICE, "gptsovits")[:40]))
    md = gen("changed")
    print("--- gen_md (changed) ---\n" + md[:900])
    smd = sel("changed")
    print("--- select md (changed) ---\n" + smd[:600])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
