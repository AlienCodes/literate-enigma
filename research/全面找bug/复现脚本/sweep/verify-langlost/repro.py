"""Independent repro: manual 语言 toggle lost after later text change; save message lang count."""
import sys, json, tempfile, shutil, re
from pathlib import Path
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.utils.textutil import detect_lang
from voicetwin.webui import app as A

HERE = Path(__file__).resolve().parent
V = "v"
TEXTS = ["今天我们来学习定语从句。", "我们先看第一个例子。", "Next, let's look at the 定语 clause example.",
         "大家记住这个规则。", "好，下课。"]


def mk(name):
    d = Path(tempfile.mkdtemp(prefix=name + "_", dir=HERE))
    cfg = make_cfg(d / "ws")
    p = wf.Project(cfg, V).ensure()
    import numpy as np, soundfile as sf
    (Path(p.root) / "clips").mkdir(parents=True, exist_ok=True)
    sr = 32000
    t = np.arange(int(sr * 3.0)) / sr
    for i in range(len(TEXTS)):
        w = (0.2 * np.sin(2 * np.pi * (150 + 20 * i) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))).astype("float32")
        sf.write(str(Path(p.root) / "clips" / f"c{i:03d}.wav"), w, sr)
    p.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": detect_lang(t),
                      "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(TEXTS)])
    return d, cfg, p, A.WebUI(cfg)


def act(ui, action, cid, **kw):
    return ui.do_clip_action(V, json.dumps(dict(action=action, id=cid, no="3", **kw), ensure_ascii=False), False)


def saved(p, rid):
    return {r["id"]: r for r in p.load_manifest()}[rid]


def cur(p, rid):
    rec = saved(p, rid)
    return review.current_values(rec, review.load_draft(p).get(rid))


def first(md):
    return re.sub("<[^>]+>", "", str(md)).splitlines()[0]


RID = "c002"
print("detect_lang of row 3:", detect_lang(TEXTS[2]))
dirs = []

# Scenario 1: toggle lang, save; later edit one word, save
d, cfg, p, ui = mk("s1"); dirs.append(d)
print("\n== S1: toggle -> save -> edit word -> save")
print("toggle msg:", first(act(ui, "lang", RID)[0]))
print("save1:", first(ui.do_save(V)[0]))
print("saved lang after save1:", saved(p, RID)["lang"])
print("edit msg:", first(act(ui, "edit", RID, text="Next, let's look at the 定语 clause examples.")[0]))
print("draft lang after edit:", cur(p, RID)["lang"])
print("save2:", first(ui.do_save(V)[0]))
print("saved lang after save2:", saved(p, RID)["lang"], "| text:", saved(p, RID)["text"])
print("train.list line:", [l for l in __import__("voicetwin.data.exporters", fromlist=["x"]).gptsovits_list_text(p, "spk").splitlines() if "c002" in l])

# Scenario 2: toggle lang then edit before saving (same unsaved session)
d, cfg, p, ui = mk("s2"); dirs.append(d)
print("\n== S2: toggle -> edit word (no save between) -> save")
act(ui, "lang", RID)
print("draft lang after toggle:", cur(p, RID)["lang"])
act(ui, "edit", RID, text="Next, let's look at the 定语 clause examples.")
print("draft lang after edit:", cur(p, RID)["lang"])
print("save:", first(ui.do_save(V)[0]))
print("saved lang:", saved(p, RID)["lang"])

# Scenario 3: edit first then toggle (control: should keep en)
d, cfg, p, ui = mk("s3"); dirs.append(d)
print("\n== S3 (control): edit word -> toggle -> save")
act(ui, "edit", RID, text="Next, let's look at the 定语 clause examples.")
act(ui, "lang", RID)
print("save:", first(ui.do_save(V)[0]))
print("saved lang:", saved(p, RID)["lang"])

# Scenario 4: toggle+save, then 全部替换 clause->Clause
d, cfg, p, ui = mk("s4"); dirs.append(d)
print("\n== S4: toggle -> save -> 全部替换 clause->Clause -> save")
act(ui, "lang", RID); ui.do_save(V)
print("saved lang:", saved(p, RID)["lang"])
ui.do_find(V, "clause", True, False)
print("replace:", first(ui.do_replace_all(V, "clause", "Clause", True, False)[0]))
print("draft lang after replace:", cur(p, RID)["lang"])
print("save:", first(ui.do_save(V)[0]))
print("saved lang:", saved(p, RID)["lang"])
print("undo replace check:")
act(ui, "lang", RID); ui.do_save(V)
ui.do_find(V, "clause", True, False)
ui.do_replace_all(V, "Clause", "clause", True, False)
print("  draft lang after 2nd replace:", cur(p, RID)["lang"])
print("  undo:", first(ui.do_undo_replace(V, False)[0]))
print("  draft lang after undo:", cur(p, RID)["lang"], "dirty:", RID in review.load_draft(p))

# Scenario 5: toggle+save, then 采用建议 on that row (suspect with alt)
d, cfg, p, ui = mk("s5"); dirs.append(d)
print("\n== S5: toggle -> save -> 采用建议 -> save")
act(ui, "lang", RID); ui.do_save(V)
rs = p.load_manifest()
for r in rs:
    if r["id"] == RID:
        t = r["text"]
        i = t.index("example")
        r["suspect"] = {"spans": [[i, i + len("example")]], "alt": t.replace("example", "examples"), "text": t}
p.save_manifest(rs)
print("saved lang before adopt:", saved(p, RID)["lang"])
print("adopt:", first(act(ui, "adopt", RID)[0]))
print("draft:", cur(p, RID))
print("save:", first(ui.do_save(V)[0]))
print("saved lang:", saved(p, RID)["lang"])

for d in dirs:
    shutil.rmtree(d, ignore_errors=True)
