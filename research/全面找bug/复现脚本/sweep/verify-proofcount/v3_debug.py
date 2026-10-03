import re, sys, shutil, json
exec(open(__file__.replace("v3_debug.py", "v1_repro.py")).read().split("# A: second engine")[0])


def engine(map_):
    def rec_fn(self, r, lang):
        t = str(r.get("text") or "")
        return map_.get(r["id"], t), None, "funasr"
    pc._EngineRunner.recognize = rec_fn

for order in ("save_then_proof", "proof_then_save_then_proof"):
    print("=" * 10, order)
    d, cfg, p, ui = make()
    try:
        list(ui.do_textfix(V))
        engine({"c001": "我们先来看as指导的定语从句。"})
        if order == "save_then_proof":
            ui.do_save(V)
        else:
            proof(ui, cfg, p, "proof unsaved")
            ui.do_save(V)
        rec, cur = shown(p, "c001")
        print(" before proof: suspect=", json.dumps({k: v for k, v in rec["suspect"].items() if k in ("src","spans","alt","text","fp")}, ensure_ascii=False))
        print("   undo:", review.analyze(rec, cur)["undo"], "suspect_auto:", rec.get("suspect_auto"))
        proof(ui, cfg, p, "proof")
        rec, cur = shown(p, "c001")
        print(" after proof: suspect=", json.dumps({k: v for k, v in rec["suspect"].items() if k in ("src","spans","alt","text")}, ensure_ascii=False))
        print("   suspect_auto:", rec.get("suspect_auto"))
    finally:
        shutil.rmtree(d, ignore_errors=True)
