"""撤销删除的消息说「又算训练素材了」：删除前本来就是灰色（不能用）的行，撤销删除以后还是不能用。"""
import sys, tempfile, json
from pathlib import Path
import numpy as np, soundfile as sf
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
p = wf.Project(cfg, "v").ensure()
sr = 16000; tt = np.arange(3 * sr) / sr; sig = (0.1 * np.sin(2 * np.pi * 150 * tt)).astype("float32")
texts = ["这个句子完全没有错。", "", "第三句话也没有问题。"]
for i in range(3): sf.write(str(p.clips_dir / f"c{i}.wav"), sig, sr)
p.save_manifest([{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "voiced": 2.8,
                  "keep": True, "split": "train", "asr_done": bool(t)} for i, t in enumerate(texts)])
ui = A.WebUI(cfg)
rec = {r["id"]: r for r in p.load_manifest()}["c1"]
print("c1 is material before delete:", review.is_material(rec))
ui.do_clip_action("v", json.dumps({"action": "delete", "id": "c1", "no": "2"}))
out = ui.do_clip_action("v", json.dumps({"action": "restore", "id": "c1", "no": "2"}))
print("restore msg:", out[0])
rec = {r["id"]: r for r in p.load_manifest()}["c1"]
print("c1 is material after restore:", review.is_material(rec), "| keep:", rec.get("keep"), "| deleted:", rec.get("deleted"))
print("counts:", review.material_counts(p.load_manifest()))
