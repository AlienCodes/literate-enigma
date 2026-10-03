"""C: no one-click involved: 采用 an auto suggestion (unsaved) then 🔍 again -> count vs table.
D: new batch of material: one-click+save on batch 1, 🔍 finds a new doubt on a batch-1 row (parked), new row added,
   button lights up, one-click again (only new rows) -> is the parked doubt ever shown?"""
import re, sys, shutil
sys.argv = sys.argv[:1]
exec(open(__file__.replace("v2_more.py", "v1_repro.py")).read().split("# A: second engine")[0])


def engine(map_):
    def rec_fn(self, r, lang):
        t = str(r.get("text") or "")
        return map_.get(r["id"], t), None, "funasr"
    pc._EngineRunner.recognize = rec_fn


print("=" * 20, "C: 采用 (unsaved) then 🔍 again, no one-click")
d, cfg, p, ui = make()
try:
    engine({"c000": "今天我们来讲定于从句。"})
    proof(ui, cfg, p, "proof #1")
    rec, cur = shown(p, "c000")
    print("   suspect alt:", rec.get("suspect", {}).get("alt"))
    print("adopt:", strip(ui.do_adopt(V, "c000")[0])[:50])
    rec, cur = shown(p, "c000")
    print("   shown:", cur, "| analyze active:", review.analyze(rec, cur)["active"], "undo:", review.analyze(rec, cur)["undo"])
    proof(ui, cfg, p, "proof #2 (adopted, unsaved)")
finally:
    shutil.rmtree(d, ignore_errors=True)

print("=" * 20, "D: new batch")
d, cfg, p, ui = make()
try:
    list(ui.do_textfix(V))
    ui.do_save(V)
    engine({"c001": "我们先来看as指导的定语从句。"})
    proof(ui, cfg, p, "proof after batch-1 one-click+save")
    rec, _ = shown(p, "c001")
    print("   c001 suspect_auto parked:", rec.get("suspect_auto", {}).get("alt"))
    # new material recognized: add a row (as prepare would)
    import numpy as np, soundfile as sf
    t = np.arange(int(3.0 * 32000)) / 32000
    sf.write(str(p.root / "clips" / "c003.wav"), (0.2 * np.sin(2 * np.pi * 200 * t)).astype("float32"), 32000)
    rs = p.load_manifest()
    rs.append({"id": "c003", "path": "clips/c003.wav", "text": "关系代词that不能和借词一起提前。", "lang": "zh",
               "duration": 3.0, "keep": True, "split": "train"})
    p.save_manifest(rs)
    proof(ui, cfg, p, "proof after new material (prepare auto-check)")
    print("button interactive now:", ui.textfix_btn(V)["interactive"])
    outs = list(ui.do_textfix(V))
    print("one-click #2:", strip(dict(zip(ui.TEXTFIX_OUT, outs[-1]))["proof_md"]).splitlines()[0])
    ui.do_save(V)
    rec, cur = shown(p, "c001")
    print("   c001 after one-click #2 + save: shown =", cur, "| red:", review.analyze(rec, cur)["red"],
          "| suspect alt:", rec.get("suspect", {}).get("alt"), "| suspect_auto:", (rec.get("suspect_auto") or {}).get("alt"))
    rec, cur = shown(p, "c003")
    print("   c003:", cur)
    print("button interactive now:", ui.textfix_btn(V)["interactive"])
    proof(ui, cfg, p, "proof again")
finally:
    shutil.rmtree(d, ignore_errors=True)
