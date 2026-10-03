"""Order dependence: grey row made usable BEFORE one-click gets corrected; AFTER one-click it never does."""
import sys
sys.argv = [sys.argv[0], "none"]
exec(open("repro.py", encoding="utf-8").read())
cfg, p, ui, A = fresh("greybefore")
ids = [r["id"] for r in p.load_manifest()]
a, b = ids[1], ids[2]
setup_rows(p, {a: {"text": "我们先来看艾子引导的定语从句。"},
               b: {"text": "关系代词that不能和借词一起提前。",
                   "asr": {"engine": "x", "avg_logprob": -1.6, "no_speech_prob": 0.1}}})
wf.apply_review(cfg, VOICE, read_csv=False)
print("[before] b keep:", cur(p, b)["keep"])
print("[before] use:", strip(act(ui, "use", b)[0])[:50]); ui.do_save(VOICE)
print("[before] b keep after use+save:", cur(p, b)["keep"])
onclick(ui)
print("[before] after one-click b:", cur(p, b)["text"])
