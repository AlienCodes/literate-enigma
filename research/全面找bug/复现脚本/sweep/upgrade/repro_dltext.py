"""After the one-click was used (button gray), 下载改好的文字 still tells the teacher to upload it and click the one-click again."""
import sys
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin.webui import app as A
cfg = make_cfg(Path(sys.argv[1])); ui = A.WebUI(cfg); V = "我的声音"
list(ui.do_textfix(V))
md, f = ui.do_download_text(V)
print("button:", ui.textfix_btn(V)["interactive"])
print("message:", [l for l in md.split("\n") if "一键" in l])
