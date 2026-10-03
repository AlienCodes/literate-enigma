"""校对表消息里还在说已经不存在的东西：「保留」列、删除的行是「灰色」、「✅ 采用建议」按钮。"""
import sys, tempfile, json
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A
from voicetwin.errors import explain
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
p = wf.Project(cfg, "v").ensure()
texts = ["我们先来看艾子引导的定语从剧。", "关系代词that不能和借词一起提前。", "这个句子完全没有错。"]
import numpy as np, soundfile as sf
sr=16000; tt=np.arange(3*sr)/sr; sig=(0.1*np.sin(2*np.pi*150*tt)).astype("float32")
for i in range(3): sf.write(str(p.clips_dir / f"c{i}.wav"), sig, sr)
p.save_manifest([{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(texts)])
ui = A.WebUI(cfg)
# 1) 保存修改的结果消息
review.set_draft(p, "c0", text="我们先来看as引导的定语从句。")
md, _, _ = ui.do_save("v")
print("1) 保存修改 ->", md.splitlines()[0])
# 2) 删除的行再改字
out = ui.do_clip_action("v", json.dumps({"action": "delete", "id": "c1", "no": "2"}))
print("2a) 删除 ->", str(out[0])[:120])
out = ui.do_clip_action("v", json.dumps({"action": "edit", "id": "c1", "no": "2", "text": "改一下"}))
print("2b) 在删除的行上改字 ->", out[0])
print("    （删除的行实际的颜色：README/快速上手/确认消息都说是紫色；FLAG_DELETED 注释：整行紫色）")
# 3) 自动查错字完成的消息（替换掉真的识别，只看消息）
wf.run_proofcheck = lambda cfg, voice, progress=None, **k: {"checked": 3, "flagged": 1}
outs = list(ui.do_proofcheck("v"))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("3) 查错字完成 ->", last["proof_md"])
# 4) errors.py no_clips 的「怎么办」
f = explain(RuntimeError("没有可用于训练的片段，请先运行素材准备并检查 transcripts.csv。"))
print("4) no_clips ->", f.title, "|", f.advice)
