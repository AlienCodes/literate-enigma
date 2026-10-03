"""Verify: changing a sentence's language after 确认训练素材 does not invalidate the confirmation."""
import sys, json, os, re, shutil, tempfile
from pathlib import Path
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
# no network: stub sv download like conftest's autouse fixture
from voicetwin.eval import sv_models
sv_models.download = lambda cfg, progress=None, keys=None: []
from conftest import make_cfg, make_lecture
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.data.exporters import gptsovits_list_text, train_records
from voicetwin.webui import app as A

tmp = Path(tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__))))
try:
    make_lecture(tmp / "lec" / "第1课.wav", repeats=1)
    cfg = make_cfg(tmp / "ws")
    V = "测试声音"
    wf.run_prepare(cfg, V, [str(tmp / "lec")])
    ui = A.WebUI(cfg)
    md, _, _ = ui.do_confirm(V)
    print("CONFIRM:", md.splitlines()[0])
    project = wf.open_project(cfg, V, must_exist=True)
    print("blocker after confirm:", repr(wf.training_blocker(project)))
    recs = project.load_manifest()
    mat = [r for r in recs if review.is_material(r)]
    target = next(r for r in mat if r["lang"] == "zh")
    no = next(i for i, r in enumerate(recs, 1) if r["id"] == target["id"])
    print("target:", no, target["id"], target["lang"], target["text"])
    sig_before = review.material_signature(recs)
    list_before = gptsovits_list_text(project, "spk", train_records(project, include_val=True))

    # double-click 语言 cell -> hidden payload action 'lang'
    out = ui.do_clip_action(V, json.dumps({"action": "lang", "id": target["id"], "no": no}))
    print("LANG CLICK:", out[0])
    print("blocker with unsaved:", repr(wf.training_blocker(project))[:80])
    # 保存修改
    md, count_md, _ = ui.do_save(V)
    print("SAVE:", md.splitlines()[0])
    project = wf.open_project(cfg, V, must_exist=True)
    recs2 = project.load_manifest()
    t2 = next(r for r in recs2 if r["id"] == target["id"])
    print("after save lang:", t2["lang"], "keep:", t2.get("keep"), "material:", review.is_material(t2))
    sig_after = review.material_signature(recs2)
    print("signature changed:", sig_before != sig_after)
    print("blocker after lang save:", repr(wf.training_blocker(project)))
    hdr = [l for l in count_md.split("\n") if "确认" in l]
    print("HEADER confirm lines:", hdr)
    list_after = gptsovits_list_text(project, "spk", train_records(project, include_val=True))
    diff = [(a, b) for a, b in zip(list_before.splitlines(), list_after.splitlines()) if a != b]
    print("train.list lines changed:", len(diff))
    for a, b in diff:
        print("  before:", a); print("  after: ", b)

    # control: text change after confirm DOES block
    ui.do_confirm(V)
    print("re-confirm blocker:", repr(wf.training_blocker(project)))
    ui.do_clip_action(V, json.dumps({"action": "edit", "id": target["id"], "no": no, "text": target["text"] + "啊"}))
    ui.do_save(V)
    print("control (text edit) blocker:", repr(wf.training_blocker(project))[:60])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
