"""Independent reproduction: web 一键全部文字校正 (once-per-batch) -> 🔍 自动查找 -> count shown vs table, and where the
new second-engine finding goes. Small voice (3 rows, sine-tone wavs), second engine mocked at _EngineRunner.recognize
so build_suspect / _protect_changed / find_suspects run for real.
Run against committed HEAD:  mkdir head && git -C /home/user/literate-enigma archive HEAD voicetwin tests | tar -x -C head
                             VT_ROOT=$PWD/head /tmp/gsv39/bin/python v1_repro.py
(without VT_ROOT it runs against the working tree)."""
import re, sys, tempfile, shutil
from pathlib import Path

import os; ROOT = os.environ.get("VT_ROOT", "/home/user/literate-enigma")
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
from conftest import make_cfg  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review, proofcheck as pc  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402
import voicetwin; print("USING", voicetwin.__file__)

HERE = Path(__file__).resolve().parent
strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))
TEXTS = ["今天我们来讲定语从句。", "我们先来看艾子引导的定语从句。", "好，我们来做一下练习。"]
V = "核查声音"


def make():
    d = Path(tempfile.mkdtemp(prefix="ws_", dir=HERE))
    cfg = make_cfg(d / "ws")
    p = wf.Project(cfg, V).ensure()
    import numpy as np, soundfile as sf
    (p.root / "clips").mkdir(parents=True, exist_ok=True)
    t = np.arange(int(3.0 * 32000)) / 32000
    for i in range(len(TEXTS)):
        sf.write(str(p.root / "clips" / f"c{i:03d}.wav"), (0.2 * np.sin(2 * np.pi * 180 * t)).astype("float32"), 32000)
    p.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh", "duration": 3.0,
                      "keep": True, "split": "train"} for i, t in enumerate(TEXTS)])
    return d, cfg, p, A.WebUI(cfg)


def shown(p, rid):
    rec = {r["id"]: r for r in p.load_manifest()}[rid]
    return rec, review.current_values(rec, review.load_draft(p).get(rid))["text"]


def proof(ui, cfg, p, label):
    outs = list(ui.do_proofcheck(V, False))
    last = dict(zip(ui.PROOF_OUT, outs[-1]))
    m = re.search(r"其中 \*\*(\d+)\*\* 条可能有错", last["proof_md"] or "")
    said = int(m.group(1)) if m else 0
    h = re.search(r"\*\*(\d+)\*\* 条可能有错", last["clips_count"] or "")
    header = int(h.group(1)) if h else 0
    table = A._clips_table(cfg, V)
    red_rows = [strip(r[1]) for r in table if "vt-red" in str(r[5])]
    only = A._clips_table(cfg, V, True)
    print(f"[{label}] result says {said} rows red | header says {header} | rows with red marks: {red_rows} | "
          f"'只看可能有错的' rows: {[(strip(r[1]), strip(r[5]), strip(r[6])) for r in only]}")
    return said, header, red_rows


def scenario(engine_hears, title):
    print("=" * 20, title)
    d, cfg, p, ui = make()
    try:
        list(ui.do_textfix(V))
        rec, cur = shown(p, "c001")
        print("after web one-click: shown =", cur, "| saved =", rec["text"], "| button interactive:",
              ui.textfix_btn(V)["interactive"])

        def rec_fn(self, r, lang):
            t = str(r.get("text") or "")
            return (engine_hears if r["id"] == "c001" else t), None, "funasr"
        pc._EngineRunner.recognize = rec_fn
        proof(ui, cfg, p, "proof #1 (unsaved)")
        rec, cur = shown(p, "c001")
        print("   suspect:", {k: rec.get("suspect", {}).get(k) for k in ("src", "spans", "alt")})
        print("   suspect_auto:", rec.get("suspect_auto"))
        print("   analyze on shown:", {k: review.analyze(rec, cur)[k] for k in ("active", "red")})
        print("save:", strip(ui.do_save(V)[0])[:60])
        rec, cur = shown(p, "c001")
        print("   after save: shown =", cur, "| analyze red:", review.analyze(rec, cur)["red"],
              "| suspect_auto still parked:", bool(rec.get("suspect_auto")))
        proof(ui, cfg, p, "proof #2 (after save)")
        rec, cur = shown(p, "c001")
        print("   suspect_auto:", rec.get("suspect_auto"))
        outs = list(ui.do_textfix(V))
        print("one-click again:", strip(dict(zip(ui.TEXTFIX_OUT, outs[-1]))["proof_bar"])[:70])
    finally:
        shutil.rmtree(d, ignore_errors=True)


# A: second engine hears what the audio would say (she said "as"), but 引导 heard as 指导
scenario("我们先来看as指导的定语从句。", "A: engine hears 'as指导'")
# B: reporter's variant (engine output same as saved text except 引导->指导)
scenario("我们先来看艾子指导的定语从句。", "B: engine hears '艾子指导'")
