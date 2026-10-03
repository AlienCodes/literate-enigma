"""Independent repro: failed / stopped retrain silently clears the 'model trained on old text' warning.

Usage: /tmp/gsv39/bin/python repro.py [oom|stop|ok]
  oom  : retrain fails because s2 runs out of VRAM even at batch 1 (FAKE_GSV_OOM_ABOVE=0)
  stop : retrain is stopped (request_cancel, the same flag the web 停止 button sets) while s2 is running
  ok   : control: retrain succeeds -> note should disappear
"""
import os, sys, shutil, socket, sysconfig, tempfile, threading, time, json
from pathlib import Path

ROOT = os.environ.get("VT_ROOT", "/home/user/literate-enigma")
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
from conftest import make_cfg, make_lecture
from fake_gptsovits import build_fake_root
from voicetwin.eval import sv_models
sv_models.download = lambda cfg, progress=None, keys=None: []
from voicetwin import workflows as wf
from voicetwin.backends.gptsovits import GPTSoVITSBackend
from voicetwin.data import review
from voicetwin.utils.progress import request_cancel, clear_cancel, TaskCancelled

GPTSoVITSBackend.ensure_users_pth = lambda self: None
GPTSoVITSBackend._gpu_memory = lambda self, quick=False: (11.99, 11.2, "test")
GPTSoVITSBackend.POLL_SECONDS = 0.05
os.environ["FAKE_GSV_CLIP_SLEEP"] = "0.0"
paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
os.environ["PYTHONPATH"] = os.pathsep.join(p for p in dict.fromkeys(paths) if p)

import voicetwin.backends.gptsovits as _g; print("code from:", _g.__file__, "| has list_sha1 fix:", "list_sha1" in open(_g.__file__, encoding="utf-8").read())
mode = sys.argv[1] if len(sys.argv) > 1 else "oom"
VOICE = "测试声音"
tmp = Path(tempfile.mkdtemp(prefix=f"rf_{mode}_", dir=str(HERE)))
try:
    # 1. prepare a voice with the dummy pipeline (same as the `prepared` fixture), confirm material
    lec = tmp / "lectures"; make_lecture(lec / "第1课.wav")
    ws = tmp / "ws"
    wf.run_prepare(make_cfg(ws), VOICE, [str(lec)])
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    root = build_fake_root(tmp / "GPT-SoVITS", real_api=False)
    cfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": port, "is_half": True,
        "train": {"sovits_epochs": 2, "gpt_epochs": 2, "batch_size": 1}}})
    project = wf.open_project(cfg, VOICE, must_exist=True)
    wf.review_confirm(cfg, VOICE)

    # 2. first training (old text)
    info1 = wf.run_train(cfg, VOICE, "gptsovits", select=False)
    sel_before = dict(project.load_models()["gptsovits"]["selected"])
    print("A) first train ok, selected:", sel_before["id"])
    print("B) note right after first train:", repr(wf.material_changed_note(cfg, VOICE, "gptsovits")[:30]))

    if mode == "legacy":  # simulate a model trained by an older version (no list_sha1 in models.json)
        ms = project.load_models(); ms["gptsovits"].pop("list_sha1", None); project.write_json(project.models_path, ms)
        print("   legacy: list_sha1 removed ->", "list_sha1" not in project.load_models()["gptsovits"])
    # 3. teacher fixes a training sentence, saves, confirms
    rec = next(r for r in project.load_manifest() if r.get("keep") and r.get("split", "train") == "train" and r.get("text"))
    review.set_draft(project, rec["id"], text="老师后来改好的一句话。")
    wf.review_save(cfg, VOICE, ids=[rec["id"]])
    wf.review_confirm(cfg, VOICE)
    n1 = wf.material_changed_note(cfg, VOICE, "gptsovits")
    print("C) note after edit+save+confirm (before retrain):", bool(n1), repr(n1[:40]))
    print("   training_blocker:", repr(wf.training_blocker_for(cfg, VOICE)))

    # 4. retrain
    err = None
    if mode in ("oom", "legacy"):
        os.environ["FAKE_GSV_OOM_ABOVE"] = "0"
        try:
            wf.run_train(cfg, VOICE, "gptsovits", select=False)
        except BaseException as exc:
            err = exc
        os.environ.pop("FAKE_GSV_OOM_ABOVE", None)
    elif mode == "stop":
        os.environ["FAKE_GSV_HANG"] = "1"
        box = {}
        def run():
            try:
                wf.run_train(cfg, VOICE, "gptsovits", select=False, progress=lambda f, m="": None)
            except BaseException as exc:
                box["err"] = exc
        t = threading.Thread(target=run); t.start()
        opt = root / "logs" / info1["exp_name"]
        # wait until s2 is running (the fake writes fake_child.pid)
        for _ in range(600):
            if (opt / "fake_child.pid").exists():
                break
            time.sleep(0.1)
        time.sleep(1.0)
        print("   s2 is running; stamp already rewritten? ->",
              (opt / "voicetwin_list.sha1").stat().st_mtime > time.time() - 60)
        request_cancel()
        t.join(60)
        clear_cancel()
        os.environ.pop("FAKE_GSV_HANG", None)
        err = box.get("err")
        try:  # kill the fake child the hang mode spawned, if still alive
            pid = int((opt / "fake_child.pid").read_text()); os.kill(pid, 9)
        except Exception:
            pass
    else:  # ok: control, the retrain succeeds
        try:
            wf.run_train(cfg, VOICE, "gptsovits", select=False)
        except BaseException as exc:
            err = exc
    print("D) retrain result:", "OK" if err is None else f"{type(err).__name__}: {str(err).splitlines()[0][:80]}")

    m = project.load_models()["gptsovits"]
    print("E) selected after retrain:", m["selected"]["id"], "| trained_at:", m.get("trained_at"),
          "| same model files as before (by name):",
          Path(m["selected"]["sovits"]).name == Path(sel_before["sovits"]).name,
          "| exists:", os.path.exists(m["selected"]["sovits"]), "| path:", m["selected"]["sovits"].replace(str(tmp), "<tmp>"))
    be = __import__("voicetwin.backends.base", fromlist=["get_backend"]).get_backend("gptsovits", cfg, project)
    print("   backend weights used for generation:", {k: v.replace(str(tmp), "<tmp>") for k, v in be._current_weights().items()})
    import hashlib
    opt = root / "logs" / info1["exp_name"]
    lst = project.exports_dir / "gptsovits" / "train.list"
    print("   DEBUG stamp:", (opt / "voicetwin_list.sha1").read_text().strip()[:12],
          "| sha1(train.list):", hashlib.sha1(lst.read_bytes() + be.version.encode()).hexdigest()[:12],
          "| models.json list_sha1:", str(m.get("list_sha1"))[:12])
    from voicetwin.data.exporters import gptsovits_list_text, train_records
    cur = gptsovits_list_text(project, be.exp_name, train_records(project))
    print("   DEBUG note-digest:", hashlib.sha1(cur.encode() + be.version.encode()).hexdigest()[:12],
          "| exp_name be/info1:", be.exp_name, info1["exp_name"], "| same text as train.list:", cur == lst.read_text(encoding="utf-8"))
    if cur != lst.read_text(encoding="utf-8"):
        import difflib
        print("".join(list(difflib.unified_diff(lst.read_text(encoding="utf-8").splitlines(True), cur.splitlines(True)))[:12]))
    n2 = wf.material_changed_note(cfg, VOICE, "gptsovits")
    print("F) note after retrain:", bool(n2), repr(n2[:40]))
    from voicetwin.webui import app as A
    pv = A.WebUI(cfg).train_plan_preview(VOICE, "gptsovits")
    print("G) train tab preview mentions old material:", "上次训练以后改过" in pv)
    print("   train tab preview head:", pv[:160].replace("\n", " "))
    print("   training_blocker after:", repr(wf.training_blocker_for(cfg, VOICE)))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
