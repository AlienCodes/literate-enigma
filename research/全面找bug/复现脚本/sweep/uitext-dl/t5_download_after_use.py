"""先点「一键全部文字校正」，再点「下载改好的文字」：下载的说明叫老师「再点一键全部文字校正」，可按钮已经是灰的；
而且把下载的文件当母本上传，和表格里一模一样的句子会被丢掉（什么也证明不了）。"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf
from voicetwin.webui import app as A
d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
p = wf.Project(cfg, "v").ensure()
texts = ["我们先来看艾子引导的定语从剧。", "关系代词that不能和借词一起提前。", "这个句子完全没有错。"]
p.save_manifest([{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(texts)])
ui = A.WebUI(cfg)
outs = list(ui.do_textfix("v"))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("button after textfix interactive:", last["tr_btn"]["interactive"])
dl = dict(zip(ui.DLTXT_OUT, ui.do_download_text("v")))
print("download md:\n", dl["dl_txt_md"])
path = dl["dl_txt_file"]["value"]
lines = tf.parse_mother(Path(path).name, Path(path).read_text(encoding="utf-8-sig"))
selves = tf._row_texts(p)
kept = [x for _, x in lines if tf._norm_line(x) not in selves]
print(f"downloaded lines {len(lines)}; lines that would survive as mother after upload: {len(kept)}")
outs = list(ui.do_textfix("v", [path]))
again = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("clicking again (old page) ->", A.re.sub(r'<[^>]+>', '', str(again['proof_bar']))[:200] if hasattr(A, 're') else str(again['proof_bar'])[:300])
