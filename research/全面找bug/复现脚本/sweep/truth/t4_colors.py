import sys, tempfile
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
p = wf.Project(cfg, "v").ensure()
texts = ["我们先来看艾子引导的定语从剧。", "现在分词作壮语的时候要注意逻辑主语。", "今天讲飞谓语动词。"]
recs = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(texts)]
recs[1]["suspect"] = {"spans": [[5, 7]], "alt": "现在分词作状语的时候要注意逻辑主语。", "reasons": ["另一个引擎听成：状语"], "score": 0.6}
recs[2]["suspect"] = {"spans": [[3, 5]], "alt": "", "reasons": ["这几个字可能识别错了"], "score": 0.6}
p.save_manifest(recs)
ui = A.WebUI(cfg)
list(ui.do_textfix("v"))
rows = A._clips_table(cfg, "v")
H = A.CLIP_HEADERS
for r in rows:
    d = dict(zip(H, r))
    print("----", d["id"])
    print(" TEXT:", d[A.COL_TEXT][:300])
    print(" SUS :", d[A.COL_SUSPECT][:300])
    print(" SUG :", d[A.COL_SUGGEST][:300])
    print(" MENU:", d[A.COL_MENU][:200])
