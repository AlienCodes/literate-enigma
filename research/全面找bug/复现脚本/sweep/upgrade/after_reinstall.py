import sys
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin.webui import app as A
from voicetwin.data import transcript_fix as tf
cfg = make_cfg(Path(sys.argv[1])); ui = A.WebUI(cfg)
print("after reinstall (pypinyin now available):", tf.has_pinyin(), "button:", ui.textfix_btn("我的声音")["interactive"])
